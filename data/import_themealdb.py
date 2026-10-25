"""Import a large, source-attributed recipe library from TheMealDB.

The API is public and returns structured recipe metadata, ingredient measures,
instructions, cuisine/area, and thumbnail URLs. The importer keeps the source
URL and attribution in every record and de-duplicates by TheMealDB meal ID.
"""
import argparse
import json
import re
import time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

API = "https://www.themealdb.com/api/json/v1/1"

def get(path, params=None):
    query = "?" + urlencode(params) if params else ""
    request = Request(API + path + query, headers={"User-Agent": "HomeDishRecipeLibrary/1.0"})
    with urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))

def ingredients(detail):
    result=[]
    for index in range(1, 21):
        name=(detail.get(f"strIngredient{index}") or "").strip()
        measure=(detail.get(f"strMeasure{index}") or "").strip()
        if name: result.append(f"{measure} {name}".strip())
    return result

def steps(instructions):
    clean=re.sub(r"\s+", " ", instructions or "").strip()
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", clean) if len(part.strip()) > 12][:12]

def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--target",type=int,default=240); parser.add_argument("--output",default="data/recipe_library.json"); parser.add_argument("--delay",type=float,default=.12); args=parser.parse_args()
    areas=[item["strArea"] for item in get("/list.php", {"a":"list"}).get("meals", [])]
    summaries={}
    for area in areas:
        for meal in get("/filter.php", {"a":area}).get("meals", []) or []:
            summaries[meal["idMeal"]]={**meal,"area":area}
        if len(summaries) >= args.target: break
        time.sleep(args.delay)
    records=[]
    for index, (meal_id, summary) in enumerate(list(summaries.items())[:args.target], 1):
        detail_rows=get("/lookup.php", {"i":meal_id}).get("meals", [])
        if not detail_rows: continue
        detail=detail_rows[0]; area=detail.get("strArea") or summary.get("area") or "Global"; tags=[tag.strip() for tag in (detail.get("strTags") or "").split(",") if tag.strip()]
        records.append({"id":f"themealdb:{meal_id}","name":detail.get("strMeal","Recipe"),"description":f"A {area.lower()} recipe from TheMealDB.","url":detail.get("strSource") or f"https://www.themealdb.com/meal/{meal_id}","image":detail.get("strMealThumb", ""),"source":"TheMealDB","cuisine":area,"category":detail.get("strCategory", ""),"diet":"Flexible","tags":tags,"ingredients":ingredients(detail),"steps":steps(detail.get("strInstructions")),"nutrition":""})
        if index % 25 == 0: print(f"Imported {index}/{min(args.target,len(summaries))}")
        time.sleep(args.delay)
    output=Path(args.output); existing=[]
    if output.exists():
        try: existing=json.loads(output.read_text(encoding="utf-8"))
        except json.JSONDecodeError: existing=[]
    merged={str(item.get("id") or item.get("url") or item.get("name")):item for item in existing if item.get("name")}
    merged.update({item["id"]:item for item in records})
    output.write_text(json.dumps(list(merged.values()),indent=2,ensure_ascii=False),encoding="utf-8")
    print(f"Wrote {len(merged)} recipes to {output}; added {len(records)} TheMealDB recipes")

if __name__ == "__main__": main()
