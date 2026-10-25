import argparse
import json
from config import Budget
from agents.recognizer import recognize
from agents.matcher import match
from agents.swap_chef import suggest
from agents.critic import critic
from tools.nutrition import compute

def run(image, hint="", cuisine="", goal="fewer calories", constraints=""):
    budget = Budget(); recognition = recognize(image, hint, cuisine, budget)
    if not recognition.is_food:
        return {"message": "This doesn't look like food. Please upload a dish photo."}
    estimates = recognition.ingredients + recognition.hidden_ingredients
    matches = match(estimates, budget)
    counted = [m.model_dump() for m in matches if m.fdc_id]
    nutrition = compute(counted, recognition.servings_estimate)
    swaps = suggest(recognition.dish_name, recognition.cuisine, [m.model_dump() for m in matches], nutrition, goal, constraints, budget)
    checks = [critic(v, constraints) for v in swaps.versions]
    return {"recognition": recognition.model_dump(), "matches": [m.model_dump() for m in matches], "nutrition": nutrition, "swaps": swaps.model_dump(by_alias=True), "critic": [c.model_dump() for c in checks], "budget": budget.__dict__}

if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("image"); args = p.parse_args(); print(json.dumps(run(args.image), indent=2))
