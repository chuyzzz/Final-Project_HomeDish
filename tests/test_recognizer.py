import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1]))
from agents.recognizer import _normalise
from schemas import Recognition

def test_recognizer_accepts_items_alias_and_missing_confidence():
    value = _normalise({"is_food": True, "dish_name": "Tofu bowl", "items": ["tofu"]})
    result = Recognition.model_validate(value)
    assert result.confidence == 0.6
    assert result.ingredients[0].name == "tofu"
