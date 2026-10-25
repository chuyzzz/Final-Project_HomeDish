import json
from schemas import Match
from tools.usda import search
from llm import chat

SYSTEM = "Choose the best USDA candidate for each ingredient. You may only return IDs included in the candidates. Return JSON {matches:[{ingredient_name:str,fdc_id:str|null}]} and never invent nutrition."

def match(ingredients, budget):
    candidates = {i.name: search(i.name) for i in ingredients}
    raw = chat([{"role": "system", "content": SYSTEM}, {"role": "user", "content": json.dumps({"ingredients": [i.model_dump() for i in ingredients], "candidates": candidates})}], "matcher", budget, {"type": "json_object"})
    values = json.loads(raw).get("matches", []); allowed = {name: {str(x["fdc_id"]) for x in candidate_rows} for name, candidate_rows in candidates.items()}
    by_name = {v.get("ingredient_name"): v.get("fdc_id") for v in values}
    out = []
    for item in ingredients:
        fid = by_name.get(item.name)
        fid = str(fid) if fid is not None and str(fid) in allowed[item.name] else None
        out.append(Match(ingredient_name=item.name, fdc_id=fid, grams_low=item.grams_low, grams_high=item.grams_high))
    return out
