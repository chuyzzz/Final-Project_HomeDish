import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]))
from agents.critic import critic
def test_medical_claim_rejected():
    class V:
        def model_dump(self): return {"steps":["This cures diabetes"]}
    assert not critic(V()).accepted
