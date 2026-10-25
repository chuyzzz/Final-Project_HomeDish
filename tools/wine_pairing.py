"""Deterministic dish profiling and X-Wines pairing retrieval."""

from __future__ import annotations

import math
import re
from pathlib import Path

from schemas import DishWineProfile


WINE_CATALOG_PATH = Path(__file__).resolve().parents[1] / "data" / "wine_catalog.json"

_HEAT = {"chili", "chilli", "jalapeno", "serrano", "cayenne", "pepper", "spicy", "hot", "harissa", "gochujang", "doubanjiang", "sambal", "sichuan", "curry", "paprika"}
_RICH = {"oil", "butter", "cream", "coconut", "cheese", "feta", "parmesan", "avocado", "nuts", "fried", "thigh", "bacon", "ghee", "sesame"}
_SWEET = {"sugar", "honey", "maple", "sweet", "fruit", "mango", "pineapple", "plantain", "teriyaki", "dessert"}
_ACID = {"lemon", "lime", "vinegar", "tomato", "tamarind", "yogurt", "yoghurt", "citrus", "pickled"}
_UMAMI = {"soy", "miso", "mushroom", "fish", "anchovy", "stock", "broth", "parmesan", "tomato", "fermented", "beans", "bean", "tofu", "meat"}
_PROTEIN = {"chicken", "beef", "pork", "lamb", "fish", "salmon", "shrimp", "prawn", "seafood", "tofu", "tempeh", "paneer", "egg", "lentil", "lentils", "beans", "bean", "meat"}


def _tokens(value) -> set[str]:
    if isinstance(value, (list, tuple, set)):
        value = " ".join(str(item) for item in value)
    return {token for token in re.findall(r"[a-z]+", str(value or "").casefold()) if len(token) > 2}


def _clamp(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 2)


def _nutrition(nutrition: dict, key: str) -> float:
    try:
        return float(nutrition.get(f"{key}_high", 0) or 0)
    except (TypeError, ValueError):
        return 0.0


def profile_dish(dish: str, cuisine: str, ingredients: list[dict], nutrition: dict) -> DishWineProfile:
    names = []
    for item in ingredients:
        names.append(item.get("ingredient_name", item.get("name", "")) if isinstance(item, dict) else str(item))
    text = " ".join([dish, cuisine, *names])
    tokens = _tokens(text)
    heat = 0.18 + 0.16 * len(tokens & _HEAT)
    richness = 0.12 + 0.12 * len(tokens & _RICH)
    sweetness = 0.08 + 0.16 * len(tokens & _SWEET)
    acidity = 0.12 + 0.14 * len(tokens & _ACID)
    umami = 0.12 + 0.12 * len(tokens & _UMAMI)
    protein = 0.12 + 0.14 * len(tokens & _PROTEIN)

    kcal = _nutrition(nutrition, "kcal")
    fat = _nutrition(nutrition, "fat_g")
    sodium = _nutrition(nutrition, "sodium_mg")
    protein_grams = _nutrition(nutrition, "protein_g")
    if kcal:
        richness += min(0.25, (fat * 9 / kcal) * 0.45)
    if sodium >= 650:
        salt = 0.72
    elif sodium >= 400:
        salt = 0.48
    else:
        salt = 0.15 + 0.12 * ("soy" in tokens or "fish sauce" in text.casefold())
    if protein_grams >= 25:
        protein += 0.2

    heat, richness, sweetness, acidity, umami, protein = map(_clamp, (heat, richness, sweetness, acidity, umami, protein))
    tags: list[str] = []
    if heat >= 0.32: tags.append("Spicy Food")
    if tokens & {"seafood", "shrimp", "prawn", "shellfish"}: tags.append("Shellfish" if tokens & {"shrimp", "prawn", "shellfish"} else "Seafood")
    elif tokens & {"fish", "salmon"}: tags.append("Rich Fish" if richness >= 0.4 else "Fish")
    if tokens & {"chicken", "poultry"}: tags.append("Poultry")
    if tokens & {"beef", "steak"}: tags.append("Beef")
    if tokens & {"lamb"}: tags.append("Lamb")
    if tokens & {"pork", "bacon"}: tags.append("Pork")
    if tokens & {"tomato"}: tags.append("Tomato Dishes")
    if tokens & {"mushroom", "mushrooms"}: tags.append("Mushrooms")
    if tokens & {"pasta", "noodle", "noodles"}: tags.append("Pasta")
    if tokens & {"tofu", "lentil", "lentils", "beans", "bean", "vegetable", "vegetables"}: tags.append("Vegetarian")
    if not tags: tags.append("Vegetarian" if protein < 0.42 else "Appetizer")

    if sweetness >= 0.45:
        target_style = "A wine at least as sweet as the sauce or dessert"
    elif heat >= 0.3:
        target_style = "Off-dry, aromatic white with lower alcohol and gentle acidity"
    elif richness >= 0.5 and protein >= 0.5:
        target_style = "High-acid red or structured white with enough body for the dish"
    elif salt >= 0.48 or umami >= 0.5:
        target_style = "Fruity, low-tannin red or bright sparkling wine"
    else:
        target_style = "Bright, food-friendly wine with moderate body"

    rationale = []
    if heat >= 0.32: rationale.append("heat calls for freshness and a softer, lower-tannin structure")
    if richness >= 0.45: rationale.append("richness benefits from acidity or a wine with enough body")
    if salt >= 0.48 or umami >= 0.5: rationale.append("salt and umami pair well with fruit, freshness, and restrained tannin")
    if sweetness >= 0.45: rationale.append("the wine should not taste drier than the dish")
    if not rationale: rationale.append("moderate body and freshness keep the pairing flexible")
    return DishWineProfile(
        heat=heat, richness=richness, salt=salt, sweetness=sweetness, acidity=acidity,
        umami=umami, protein_weight=_clamp(protein), target_style=target_style,
        pairing_tags=list(dict.fromkeys(tags)), rationale=rationale,
    )


def load_wine_catalog(path: Path = WINE_CATALOG_PATH) -> list[dict]:
    import json
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []


def _body_score(body: str) -> float:
    body = body.casefold()
    if "very light" in body: return 0.1
    if "light" in body: return 0.25
    if "very full" in body: return 0.95
    if "full" in body: return 0.8
    return 0.5


def _acidity_score(acidity: str) -> float:
    return {"low": 0.2, "medium": 0.55, "high": 0.9}.get(acidity.casefold(), 0.5)


def rank_wines(catalog: list[dict], profile: DishWineProfile, limit: int = 3) -> list[dict]:
    ranked = []
    target_tags = {tag.casefold() for tag in profile.pairing_tags}
    for wine in catalog:
        harmonize = {str(tag).casefold() for tag in wine.get("harmonize", [])}
        overlap = sum(3.2 if tag == "spicy food" and profile.heat >= 0.3 else 2.2 for tag in target_tags & harmonize)
        body = _body_score(str(wine.get("body", "")))
        acidity = _acidity_score(str(wine.get("acidity", "")))
        wine_type = str(wine.get("type", "")).casefold()
        abv = float(wine.get("abv") or 0)
        score = overlap * 2.2
        if profile.heat >= 0.3:
            score += 1.1 if wine_type in {"white", "sparkling", "rosé"} else -0.3
            score += 0.7 if body <= 0.55 else -0.25
            score += 0.45 if abv and abv <= 12.5 else 0
            grape_text = " ".join(str(grape) for grape in wine.get("grapes", [])).casefold()
            if any(grape in grape_text for grape in ("riesling", "gewürztraminer", "gewurztraminer", "pinot gris", "chenin", "viognier")):
                score += 1.0
        if profile.richness >= 0.42:
            score += acidity * 0.9 + (0.55 if body >= 0.5 else 0)
        if profile.salt >= 0.45 or profile.umami >= 0.45:
            score += 0.5 if wine_type in {"red", "rosé", "sparkling"} else 0.2
        if profile.sweetness >= 0.45:
            score += 2.0 if "dessert" in wine_type or "port" in wine_type else -0.8
        rating = float(wine.get("rating") or 0)
        rating_count = int(wine.get("rating_count") or 0)
        score += rating / 5 * 0.85 + min(0.45, math.log1p(rating_count) / 10)
        ranked.append({**wine, "pairing_score": round(score, 3), "matched_pairings": [tag for tag in wine.get("harmonize", []) if str(tag).casefold() in target_tags]})
    ranked.sort(key=lambda row: (-row["pairing_score"], -float(row.get("rating") or 0), -int(row.get("rating_count") or 0), row.get("name", "")))
    return ranked[:limit]
