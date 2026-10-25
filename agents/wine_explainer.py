"""Bounded, evidence-aware explanations for deterministic wine matches."""

from __future__ import annotations

import json

from pydantic import ValidationError

from llm import chat
from schemas import DishWineProfile, WineExplanation, WineExplanationResponse


SYSTEM = (
    "Explain exactly three deterministic wine pairing results for a dish. "
    "Use only the supplied wine_id values and catalog facts. Return one concise, "
    "specific sentence per wine that mentions the dish profile or listed Harmonize "
    "pairing. Do not invent tasting notes, prices, health benefits, sweetness, or "
    "a bottle link. Do not make medical or alcohol-safety claims. Return JSON only: "
    "{explanations:[{wine_id,explanation}]}"
)


def _fallback(profile: DishWineProfile, wines: list[dict]) -> list[WineExplanation]:
    explanations = []
    for wine in wines[:3]:
        matched = wine.get("matched_pairings", [])
        pairing = ", ".join(matched[:2]) if matched else "its balance of body and acidity"
        details = []
        if profile.heat >= 0.35:
            details.append("freshness helps keep the heat lively")
        if profile.richness >= 0.42:
            details.append("acidity helps refresh a richer bite")
        if profile.salt >= 0.45 or profile.umami >= 0.45:
            details.append("fruit and restrained structure suit savory flavors")
        if not details:
            details.append("its structure keeps the meal in balance")
        explanations.append(WineExplanation(
            wine_id=str(wine["id"]),
            explanation=f"The catalog lists it with {pairing}, and {details[0]}.",
        ))
    return explanations


def explain_pairings(profile: DishWineProfile, wines: list[dict], budget) -> list[WineExplanation]:
    if len(wines) < 3:
        return _fallback(profile, wines)
    prompt = json.dumps({"dish_profile": profile.model_dump(), "wines": [
        {key: wine.get(key) for key in ("id", "name", "type", "grapes", "harmonize", "body", "acidity", "abv", "country", "region", "rating")}
        for wine in wines[:3]
    ]}, ensure_ascii=False)
    try:
        raw = chat([{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}], "wine_explainer", budget, {"type": "json_object"})
        parsed = WineExplanationResponse.model_validate(json.loads(raw))
    except Exception:
        return _fallback(profile, wines)
    allowed = {str(wine["id"]): wine for wine in wines[:3]}
    output: list[WineExplanation] = []
    seen: set[str] = set()
    for item in parsed.explanations:
        if item.wine_id in allowed and item.wine_id not in seen:
            output.append(item)
            seen.add(item.wine_id)
    for item in _fallback(profile, wines[:3]):
        if item.wine_id not in seen:
            output.append(item)
            seen.add(item.wine_id)
    return output[:3]
