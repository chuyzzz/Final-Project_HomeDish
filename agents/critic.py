import re
from schemas import CriticResult
BAD = re.compile(r"\b(cures?|safe for diabetics?|lose \d+ ?lbs?)\b", re.I)

def critic(version, allergies=""):
    text = str(version.model_dump()).lower(); flags = []
    if allergies and any(a.strip().lower() in text for a in allergies.split(",")): flags.append("allergen")
    claims = BAD.findall(text)
    return CriticResult(accepted=not flags and not claims, authenticity_score=4 if not flags else 1, reason="Passed rule-based safety checks." if not flags and not claims else "Needs revision or removal.", allergen_flags=flags, medical_claims=claims)
