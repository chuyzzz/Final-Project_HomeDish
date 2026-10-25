import math
from .usda import table
NUTRIENTS=["kcal","protein_g","fat_g","carbs_g","fiber_g","sugar_g","sodium_mg","sat_fat_g"]
def compute(ingredients,servings=1):
    df=table().set_index("fdc_id"); totals={f"{n}_{x}":0.0 for n in NUTRIENTS for x in ("low","high")}; contributors=[]
    for item in ingredients:
        fid=str(item["fdc_id"])
        if fid not in df.index: continue
        row=df.loc[fid]
        if any(not math.isfinite(float(row[n])) for n in NUTRIENTS):
            raise ValueError(f"USDA row {fid} has an incomplete nutrient value")
        lo=float(item["grams_low"]); hi=float(item["grams_high"]); contributors.append({"ingredient":item.get("name",row.description),"kcal_low":row.kcal*lo/100,"kcal_high":row.kcal*hi/100,"sodium_low":row.sodium_mg*lo/100,"sodium_high":row.sodium_mg*hi/100})
        for n in NUTRIENTS: totals[f"{n}_low"]+=row[n]*lo/100; totals[f"{n}_high"]+=row[n]*hi/100
    return {**{k:round(v/servings,2) for k,v in totals.items()},"contributors":sorted(contributors,key=lambda x:x["kcal_high"],reverse=True)}
