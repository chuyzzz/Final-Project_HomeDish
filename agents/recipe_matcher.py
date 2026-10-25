"""Ingredient-aware retrieval and reranking for the photo workflow.

The catalog search is deterministic first: the language model only sees a
small set of recipes that already share ingredients with the user's dish.
That keeps the recommendation grounded in the local recipe database and
makes a model response unable to invent a recipe or a source URL.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable

from pydantic import ValidationError

from llm import chat
from schemas import RecipeRecommendation, RecipeRecommendationResponse


_STOP_WORDS = {
    "a", "an", "and", "as", "at", "by", "for", "from", "in", "into", "of",
    "on", "or", "the", "to", "with", "large", "small", "fresh", "ground",
    "chopped", "diced", "minced", "sliced", "roughly", "optional", "taste",
    "serving", "servings", "plus", "more", "pinch", "clove", "cloves",
}
_QUANTITY_WORDS = {
    "cup", "cups", "tablespoon", "tablespoons", "tbsp", "teaspoon", "teaspoons",
    "tsp", "gram", "grams", "g", "kg", "ml", "liter", "liters", "lb", "lbs",
    "oz", "ounce", "ounces", "piece", "pieces", "can", "cans", "bunch", "bunches",
}
_ALIASES = {
    "aubergine": "eggplant", "brinjal": "eggplant", "capsicum": "pepper",
    "bell pepper": "pepper", "green pepper": "pepper", "red pepper": "pepper",
    "chickpeas": "chickpea", "garbanzo": "chickpea", "garbanzo beans": "chickpea",
    "coriander": "cilantro", "green onion": "scallion", "green onions": "scallion",
    "spring onion": "scallion", "spring onions": "scallion", "prawns": "shrimp",
    "yoghurt": "yogurt", "courgette": "zucchini", "sweetcorn": "corn",
    "sweet potato": "potato", "coconut cream": "coconut milk",
}
_HEALTH_SIGNALS = {
    "vegetable", "vegetables", "greens", "spinach", "broccoli", "salad", "salsa",
    "lentil", "lentils", "bean", "beans", "chickpea", "tofu", "fish", "salmon",
    "whole", "brown rice", "bowl", "roasted", "steamed", "grilled", "baked",
    "vegan", "vegetarian", "plant-based", "high protein", "healthy", "light",
}
_HEAVY_SIGNALS = {
    "deep fried", "fried", "frying", "bacon", "cream", "creamy", "butter",
    "sugar", "shortening", "lard",
}


def _as_text(value) -> str:
    if isinstance(value, (list, tuple, set)):
        return " ".join(_as_text(item) for item in value)
    if isinstance(value, dict):
        return _as_text(value.get("name", value.get("url", "")))
    return str(value or "")


def _canonical_phrase(value: str) -> str:
    phrase = re.sub(r"\([^)]*\)", " ", value.casefold())
    phrase = phrase.replace("&", " and ")
    phrase = re.sub(r"\b\d+(?:[./]\d+)?\b", " ", phrase)
    phrase = re.sub(r"\b(?:\d+\s*)?(?:g|kg|ml|lb|lbs|oz|cups?|tbsp|tsp)\b", " ", phrase)
    phrase = re.sub(r"[^a-z\s-]", " ", phrase)
    phrase = re.sub(r"\s+", " ", phrase).strip()
    for alias, canonical in sorted(_ALIASES.items(), key=lambda item: len(item[0]), reverse=True):
        phrase = re.sub(rf"\b{re.escape(alias)}\b", canonical, phrase)
    return phrase


def ingredient_tokens(value: str) -> set[str]:
    phrase = _canonical_phrase(value)
    return {
        token.rstrip("s") if len(token) > 4 and token.endswith("s") else token
        for token in phrase.split()
        if token not in _STOP_WORDS and token not in _QUANTITY_WORDS and len(token) > 2
    }


def _ingredient_values(recipe: dict) -> list[str]:
    values = recipe.get("ingredients", [])
    if isinstance(values, str):
        values = re.split(r",|;|\n", values)
    return [str(value) for value in values if str(value).strip()]


def _recipe_id(recipe: dict, index: int) -> str:
    return str(recipe.get("id") or f"recipe:{index}:{re.sub(r'[^a-z0-9]+', '-', str(recipe.get('name', 'recipe')).casefold()).strip('-')}")


def _cuisine_text(recipe: dict) -> str:
    return _as_text(recipe.get("cuisine", "")).casefold()


def _compact(value: str) -> str:
    return re.sub(r"[^a-z]", "", _canonical_phrase(value))


def _health_score(recipe: dict) -> float:
    text = _canonical_phrase(" ".join([
        _as_text(recipe.get("name")), _as_text(recipe.get("description")),
        _as_text(recipe.get("tags")), _as_text(recipe.get("diet")),
        _as_text(recipe.get("category")), _as_text(_ingredient_values(recipe)),
    ]))
    tokens = ingredient_tokens(text)
    positive = len(tokens & {x.replace("-", " ") for x in _HEALTH_SIGNALS})
    negative = sum(1 for signal in _HEAVY_SIGNALS if signal in text)
    return min(4.0, positive * 0.35) - min(2.0, negative * 0.45)


def _overlap(user_ingredients: Iterable, recipe: dict) -> tuple[float, list[str]]:
    recipe_values = _ingredient_values(recipe)
    recipe_tokens = set().union(*(ingredient_tokens(value) for value in recipe_values)) if recipe_values else set()
    matched_names: list[str] = []
    points = 0.0
    for item in user_ingredients:
        name = _as_text(item.get("ingredient_name") if isinstance(item, dict) else getattr(item, "ingredient_name", ""))
        tokens = ingredient_tokens(name)
        overlap = tokens & recipe_tokens
        if overlap:
            matched_names.append(name)
            points += min(2.0, 0.75 + (0.4 * len(overlap)))
    return points, matched_names[:6]


def retrieve_candidates(recipes: list[dict], user_ingredients: Iterable, dish: str = "", cuisine: str = "", limit: int = 10) -> list[dict]:
    """Return only linkable recipes with meaningful ingredient overlap."""
    user_ingredients = list(user_ingredients)
    ranked: list[dict] = []
    dish_tokens = ingredient_tokens(dish)
    dish_compact = _compact(dish)
    cuisine_text = str(cuisine or "").casefold()
    for index, recipe in enumerate(recipes):
        if not recipe.get("url"):
            continue
        recipe_name = _as_text(recipe.get("name", ""))
        recipe_name_tokens = ingredient_tokens(recipe_name)
        if dish_compact and dish_compact == _compact(recipe_name):
            continue
        if len(dish_tokens) >= 2 and len(dish_tokens & recipe_name_tokens) / len(dish_tokens) >= 0.9:
            continue
        overlap_score, shared = _overlap(user_ingredients, recipe)
        if not shared:
            continue
        recipe_cuisine = _cuisine_text(recipe)
        cuisine_score = 1.25 if cuisine_text and cuisine_text in recipe_cuisine else 0.0
        title_score = 0.35 if dish_tokens & recipe_name_tokens else 0.0
        score = overlap_score + cuisine_score + title_score + _health_score(recipe)
        ranked.append({
            "recipe_id": _recipe_id(recipe, index),
            "recipe": recipe,
            "shared_ingredients": shared,
            "retrieval_score": round(score, 3),
        })
    ranked.sort(key=lambda item: (-item["retrieval_score"], item["recipe"].get("name", "")))
    return ranked[:limit]


SYSTEM = (
    "Select exactly three recipes from the supplied candidate list for a food-photo user. "
    "Use only candidate recipe_id values; never invent a recipe, ingredient, URL, or nutrition claim. "
    "Each choice must have meaningful ingredient overlap, should be a more vegetable-forward, "
    "plant-based, high-protein, or otherwise lighter direction when the catalog supports it, "
    "and should feel like an interesting new direction rather than a generic salad. "
    "Explain the overlap and the lighter direction without claiming medical or weight-loss outcomes. "
    "Return JSON only: {recommendations:[{recipe_id,reason,shared_ingredients,health_angle,interest_angle}]}"
)


def _fallback(shortlist: list[dict]) -> list[RecipeRecommendation]:
    recommendations: list[RecipeRecommendation] = []
    for candidate in shortlist[:3]:
        recipe = candidate["recipe"]
        shared = candidate["shared_ingredients"]
        name = recipe.get("name", "this recipe")
        recommendations.append(RecipeRecommendation(
            recipe_id=candidate["recipe_id"],
            reason=f"{name} keeps {', '.join(shared[:3])} in the ingredient orbit while opening a new direction.",
            shared_ingredients=shared,
            health_angle="A lighter direction built around the recipe's existing ingredients and preparation style.",
            interest_angle="A fresh way to use familiar ingredients without asking you to abandon the dish's identity.",
        ))
    return recommendations


def recommend_recipes(recipes: list[dict], user_ingredients: Iterable, dish: str, cuisine: str, goal: str, constraints: str, budget, limit: int = 10) -> list[RecipeRecommendation]:
    user_ingredients = list(user_ingredients)
    shortlist = retrieve_candidates(recipes, user_ingredients, dish, cuisine, limit)
    if len(shortlist) < 3:
        return _fallback(shortlist)

    candidate_payload = []
    for item in shortlist:
        recipe = item["recipe"]
        candidate_payload.append({
            "recipe_id": item["recipe_id"],
            "name": recipe.get("name", "Recipe"),
            "description": recipe.get("description", ""),
            "cuisine": recipe.get("cuisine", ""),
            "diet": recipe.get("diet", ""),
            "tags": recipe.get("tags", []),
            "ingredients": _ingredient_values(recipe)[:30],
            "shared_ingredients_verified": item["shared_ingredients"],
            "source": recipe.get("source", ""),
        })
    prompt = json.dumps({
        "dish": dish, "cuisine": cuisine, "goal": goal, "constraints": constraints,
        "confirmed_ingredients": list(user_ingredients), "candidates": candidate_payload,
    }, ensure_ascii=False)
    try:
        raw = chat([{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}], "recipe_matcher", budget, {"type": "json_object"})
        parsed = RecipeRecommendationResponse.model_validate(json.loads(raw))
    except Exception:
        return _fallback(shortlist)

    by_id = {item["recipe_id"]: item for item in shortlist}
    output: list[RecipeRecommendation] = []
    seen: set[str] = set()
    for recommendation in parsed.recommendations:
        item = by_id.get(recommendation.recipe_id)
        if not item or recommendation.recipe_id in seen:
            continue
        seen.add(recommendation.recipe_id)
        verified_shared = item["shared_ingredients"]
        actual_shared = [name for name in recommendation.shared_ingredients if any(name.casefold() == value.casefold() for value in verified_shared)]
        output.append(recommendation.model_copy(update={"shared_ingredients": actual_shared or verified_shared}))
        if len(output) == 3:
            break
    if len(output) < 3:
        existing = {recommendation.recipe_id for recommendation in output}
        for recommendation in _fallback(shortlist):
            if recommendation.recipe_id not in existing:
                output.append(recommendation)
            if len(output) == 3:
                break
    return output
