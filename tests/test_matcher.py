import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1]))
from agents import matcher
from schemas import IngredientEstimate
from config import Budget

def test_match_uses_candidate_names_and_rejects_unknown_ids(monkeypatch):
    monkeypatch.setattr(matcher, "chat", lambda *args, **kwargs: json.dumps({"matches": [{"ingredient_name": "Tofu firm", "fdc_id": "1001"}, {"ingredient_name": "oil", "fdc_id": "not-a-candidate"}]}))
    items = [IngredientEstimate(name="Tofu firm", grams_low=100, grams_high=120), IngredientEstimate(name="oil", grams_low=5, grams_high=10)]
    result = matcher.match(items, Budget())
    assert result[0].fdc_id == "1001"
    assert result[1].fdc_id is None
