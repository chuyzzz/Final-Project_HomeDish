import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from tools.wine_pairing import profile_dish, rank_wines


def test_spicy_dish_targets_off_dry_style():
    profile = profile_dish(
        "Mapo tofu",
        "Chinese",
        [{"ingredient_name": "tofu"}, {"ingredient_name": "chili"}, {"ingredient_name": "soy sauce"}],
        {"kcal_high": 500, "fat_g_high": 22, "sodium_mg_high": 800, "protein_g_high": 24},
    )

    assert "Off-dry" in profile.target_style
    assert "Spicy Food" in profile.pairing_tags


def test_ranker_uses_harmonize_and_rating_without_an_llm():
    profile = profile_dish("Mapo tofu", "Chinese", [{"ingredient_name": "tofu"}, {"ingredient_name": "chili"}], {})
    catalog = [
        {"id": "x:matched", "name": "A", "type": "White", "grapes": ["Riesling"], "harmonize": ["Spicy Food"], "abv": 11.5, "body": "Light-bodied", "acidity": "High", "rating": 3.8, "rating_count": 10},
        {"id": "x:unmatched", "name": "B", "type": "Red", "grapes": ["Merlot"], "harmonize": ["Beef"], "abv": 14, "body": "Full-bodied", "acidity": "Medium", "rating": 5.0, "rating_count": 100},
    ]

    result = rank_wines(catalog, profile, limit=1)

    assert result[0]["id"] == "x:matched"
    assert result[0]["matched_pairings"] == ["Spicy Food"]
