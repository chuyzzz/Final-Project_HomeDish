def build(ingredients,servings=1):
    out={x:[] for x in ["produce","protein","pantry/sauces","specialty/international aisle"]}
    for item in ingredients:
        name=item["name"]; low=name.lower(); section="pantry/sauces"
        if any(x in low for x in ["onion","garlic","ginger","pepper","scallion","cilantro"]): section="produce"
        elif any(x in low for x in ["tofu","chicken","beef","fish","paneer"]): section="protein"
        elif any(x in low for x in ["doubanjiang","gochujang","fish sauce"]): section="specialty/international aisle"
        suffix=" (probably already have)" if section=="pantry/sauces" else ""; grams=item.get("grams",item.get("grams_high",0))*servings; out[section].append(f"{name}: {grams:g} g{suffix}")
    return out
