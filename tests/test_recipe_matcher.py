import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from agents import recipe_matcher
from config import Budget
from agents.recipe_matcher import retrieve_candidates


def test_retrieval_requires_overlap_and_a_source_url():
    recipes = [
        {"id": "same", "name": "Mapo Tofu", "ingredients": ["tofu", "garlic"], "url": "https://example.com/mapo"},
        {"id": "good", "name": "Tofu lettuce cups", "ingredients": ["tofu", "lettuce", "ginger"], "url": "https://example.com/tofu"},
        {"id": "local", "name": "Garlic rice", "ingredients": ["garlic", "rice"], "url": ""},
        {"id": "unrelated", "name": "Apple crumble", "ingredients": ["apple", "oats"], "url": "https://example.com/apple"},
    ]

    candidates = retrieve_candidates(recipes, [{"ingredient_name": "tofu"}], "Mapo tofu", "Chinese")

    assert [item["recipe_id"] for item in candidates] == ["good"]
    assert candidates[0]["shared_ingredients"] == ["tofu"]


def test_agent_is_clamped_to_shortlist(monkeypatch):
    recipes = [
        {"id": "one", "name": "Tofu lettuce cups", "ingredients": ["tofu", "lettuce"], "url": "https://example.com/one"},
        {"id": "two", "name": "Tofu rice bowl", "ingredients": ["tofu", "rice"], "url": "https://example.com/two"},
        {"id": "three", "name": "Tofu noodle soup", "ingredients": ["tofu", "noodles"], "url": "https://example.com/three"},
    ]
    monkeypatch.setattr(
        recipe_matcher,
        "chat",
        lambda *args, **kwargs: '{"recommendations":[{"recipe_id":"one","shared_ingredients":["invented ingredient"]},{"recipe_id":"not-in-catalog"}]}',
    )

    result = recipe_matcher.recommend_recipes(
        recipes,
        [{"ingredient_name": "tofu"}],
        "tofu curry",
        "",
        "fewer calories",
        "",
        Budget(),
    )

    assert len(result) == 3
    assert {item.recipe_id for item in result} == {"one", "two", "three"}
    assert result[0].shared_ingredients == ["tofu"]
