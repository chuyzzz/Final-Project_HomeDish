import json
from pydantic import ValidationError
from schemas import SwapResponse
from llm import chat

SYSTEM = "Suggest exactly two lighter versions of the same culturally recognizable dish, ordered gentle to balanced. Preserve signature ingredients and techniques, target the largest contributors, respect allergies, and make no medical claims. Return JSON only with a top-level `versions` array. Each version should have title, authenticity_note, changes, new_ingredients, steps, and flavor_tradeoff. Do not use the key `lighter_versions`; do not give nutrition numbers."

def _normalise(payload):
    if "versions" not in payload:
        payload["versions"] = payload.pop("lighter_versions", payload.pop("options", []))
    for version in payload.get("versions", []):
        if not isinstance(version, dict):
            continue
        version.setdefault("title", version.get("name", version.get("label", "Lighter version")))
        version.setdefault("authenticity_note", version.get("authenticity", "Keeps the dish recognizable."))
        version.setdefault("flavor_tradeoff", version.get("tradeoff", "A small flavor tradeoff."))
        version.setdefault("changes", version.get("substitutions", []))
        version.setdefault("new_ingredients", version.get("ingredients", []))
        version.setdefault("steps", version.get("method", []))
        version["changes"] = [{"from": change, "to": "updated amount", "why": "Supports the selected goal."} if isinstance(change, str) else change for change in version["changes"]]
        version["new_ingredients"] = [{"name": ingredient, "grams_low": 0, "grams_high": 0} if isinstance(ingredient, str) else ingredient for ingredient in version["new_ingredients"]]
        version["steps"] = [str(step) for step in version["steps"]]
        for change in version["changes"]:
            if isinstance(change, dict):
                change.setdefault("from", change.get("original_ingredient", change.get("old", "ingredient")))
                change.setdefault("to", change.get("replacement", change.get("new", "updated amount")))
                change.setdefault("why", change.get("reason", change.get("rationale", "Supports the selected goal.")))
        for ingredient in version["new_ingredients"]:
            if isinstance(ingredient, dict):
                ingredient.setdefault("name", ingredient.get("ingredient_name", ingredient.get("ingredient", "new ingredient")))
    payload["versions"] = payload.get("versions", [])[:2]
    return payload

def suggest(dish, cuisine, ingredients, nutrition, goal, constraints, budget):
    prompt = json.dumps({"dish": dish, "cuisine": cuisine, "ingredients": ingredients, "nutrition": nutrition, "goal": goal, "constraints": constraints})
    messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}]
    raw = chat(messages, "swap_chef", budget, {"type": "json_object"})
    try:
        return SwapResponse.model_validate(_normalise(json.loads(raw)))
    except (ValidationError, json.JSONDecodeError) as first_error:
        repair = {"role": "user", "content": "Return corrected JSON only with a top-level versions array. Validation issue: " + str(first_error)}
        repaired = chat(messages + [{"role": "assistant", "content": raw}, repair], "swap_chef_repair", budget, {"type": "json_object"})
        return SwapResponse.model_validate(_normalise(json.loads(repaired)))
