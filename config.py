from dataclasses import dataclass
import os

MODEL = "gpt-6-luna"
BASE_URL = "https://api.portkey.ai/v1"
MAX_LLM_CALLS = 10
MAX_RUN_COST_USD = 0.05
PRICE_INPUT_PER_MILLION = float(os.getenv("PRICE_INPUT_PER_MILLION", "0"))
PRICE_CACHED_PER_MILLION = float(os.getenv("PRICE_CACHED_PER_MILLION", "0"))
PRICE_OUTPUT_PER_MILLION = float(os.getenv("PRICE_OUTPUT_PER_MILLION", "0"))

class BudgetExceeded(RuntimeError): pass

@dataclass
class Budget:
    calls: int = 0
    cost_usd: float = 0.0
    def charge(self, input_tokens, cached_tokens, output_tokens):
        self.calls += 1
        self.cost_usd += ((input_tokens-cached_tokens)*PRICE_INPUT_PER_MILLION + cached_tokens*PRICE_CACHED_PER_MILLION + output_tokens*PRICE_OUTPUT_PER_MILLION)/1_000_000
        if self.calls > MAX_LLM_CALLS: raise BudgetExceeded("This run reached the 10-call safety limit.")
        if self.cost_usd > MAX_RUN_COST_USD: raise BudgetExceeded("This run reached its cost safety limit.")
