import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1]))
from agents.swap_chef import _normalise
from schemas import SwapResponse

def test_swap_alias_is_normalized():
    response = _normalise({"lighter_versions": [{"name": "Less oil", "authenticity": "Same dish", "tradeoff": "Less glossy"}]})
    result = SwapResponse.model_validate(response)
    assert result.versions[0].title == "Less oil"
    assert result.versions[0].authenticity_note == "Same dish"
