import sys
import math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]))
from tools.nutrition import compute
def test_hand_computed_recipe():
    out=compute([{"fdc_id":"1001","grams_low":100,"grams_high":100},{"fdc_id":"1002","grams_low":15,"grams_high":15}])
    assert abs(out["kcal_low"]-(144+132.6)) < .01

def test_bundled_table_has_no_missing_nutrients():
    out=compute([{"fdc_id":"1002","grams_low":10,"grams_high":10}])
    assert all(math.isfinite(value) for key,value in out.items() if key != "contributors")
