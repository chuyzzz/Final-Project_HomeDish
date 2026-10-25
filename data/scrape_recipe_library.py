"""Build a source-linked recipe library from public Recipe JSON-LD metadata.

This intentionally stores metadata and source URLs, not copied recipe pages. It
is rate-limited, stays on each source domain, and is meant for a small curated
catalogue rather than an unrestricted mirror of any publisher.
"""
import argparse
import json
import time
from html import unescape
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.request import Request, build_opener, urlopen
from urllib.robotparser import RobotFileParser

from bs4 import BeautifulSoup

SOURCES = [
    ("EatingWell", "https://www.eatingwell.com/recipes/"),
    ("BBC Good Food", "https://www.bbcgoodfood.com/recipes/collection/healthy-recipes"),
    ("Mayo Clinic", "https://www.mayoclinic.org/healthy-lifestyle/recipes"),
    ("American Heart Association", "https://recipes.heart.org/"),
    ("Skinnytaste", "https://www.skinnytaste.com/recipes/"),
    ("Cookie and Kate", "https://cookieandkate.com/recipes/"),
    ("Love & Lemons", "https://www.loveandlemons.com/recipes/"),
    ("Minimalist Baker", "https://minimalistbaker.com/recipes/"),
    ("Pinch of Yum", "https://pinchofyum.com/recipes"),
    ("Well Plated", "https://www.wellplated.com/recipes/"),
    ("Ambitious Kitchen", "https://www.ambitiouskitchen.com/recipes/"),
    ("Feel Good Foodie", "https://feelgoodfoodie.net/recipes/"),
    ("The Mediterranean Dish", "https://www.themediterraneandish.com/recipes/"),
    ("Oh She Glows", "https://ohsheglows.com/recipes/"),
    ("Diabetes Food Hub", "https://www.diabetesfoodhub.org/recipes.html"),
    ("MyPlate Kitchen", "https://www.myplate.gov/myplate-kitchen"),
    ("Allrecipes", "https://www.allrecipes.com/recipes/"),
    ("Serious Eats", "https://www.seriouseats.com/recipes-5117985"),
    ("Food Network", "https://www.foodnetwork.com/recipes"),
    ("Epicurious", "https://www.epicurious.com/recipes-menus"),
    ("Simply Recipes", "https://www.simplyrecipes.com/recipes/"),
    ("Delish", "https://www.delish.com/cooking/recipe-ideas/"),
    ("Omnivore's Cookbook", "https://omnivorescookbook.com/recipes/"),
    ("Red House Spice", "https://redhousespice.com/recipes/"),
    ("Maangchi", "https://www.maangchi.com/recipes"),
    ("Just One Cookbook", "https://www.justonecookbook.com/recipes/"),
    ("Hebbar's Kitchen", "https://hebbarskitchen.com/recipes/"),
    ("Swasthi's Recipes", "https://www.indianhealthyrecipes.com/recipes/"),
    ("Hot Thai Kitchen", "https://hot-thai-kitchen.com/recipes/"),
]

def fetch(url, timeout=18):
    req = Request(url, headers={"User-Agent": "HomeDishRecipeIndexer/1.0 (educational project)"})
    with urlopen(req, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")

def allowed(url):
    parsed = urlparse(url)
    robots = RobotFileParser(f"{parsed.scheme}://{parsed.netloc}/robots.txt")
    try:
        robots.read()
        return robots.can_fetch("HomeDishRecipeIndexer", url)
    except Exception:
        return False

def recipe_objects(html, page_url, source):
    soup = BeautifulSoup(html, "html.parser")
    found = []
    for script in soup.select('script[type="application/ld+json"]'):
        try:
            payload = json.loads(unescape(script.string or script.get_text()))
        except (json.JSONDecodeError, TypeError):
            continue
        objects = payload if isinstance(payload, list) else payload.get("@graph", [payload]) if isinstance(payload, dict) else []
        for obj in objects:
            if not isinstance(obj, dict):
                continue
            types = obj.get("@type", [])
            if isinstance(types, str): types = [types]
            if "Recipe" not in types or not obj.get("name"): continue
            image = obj.get("image", "")
            if isinstance(image, list): image = image[0] if image else ""
            found.append({
                "name": obj["name"], "description": obj.get("description", ""), "url": obj.get("url", page_url),
                "image": image, "source": source, "cuisine": obj.get("recipeCuisine", ""),
                "category": obj.get("recipeCategory", ""), "ingredients": obj.get("recipeIngredient", []),
                "nutrition": obj.get("nutrition", {}),
            })
    return found

def recipe_links(html, page_url, domain):
    soup = BeautifulSoup(html, "html.parser")
    links=[]
    for anchor in soup.find_all("a", href=True):
        url=urljoin(page_url, anchor["href"]).split("#")[0]
        parsed=urlparse(url)
        if parsed.netloc != domain or url in links: continue
        path=parsed.path.lower()
        generic = path.rstrip("/").endswith(("/recipes", "/recipe", "/recipe-ideas", "/recipes-menus")) or "/collection/" in path or "/category/" in path
        if not generic and any(token in path for token in ("recipe", "recipes", "dish", "meal", "food")): links.append(url)
    return links

def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--limit-per-source",type=int,default=4); parser.add_argument("--delay",type=float,default=.6); parser.add_argument("--output",default="data/recipe_library.json"); args=parser.parse_args()
    all_recipes=[]; seen=set()
    for source, seed in SOURCES:
        try:
            if not allowed(seed): print(f"skip robots: {source}"); continue
            seed_html=fetch(seed); pages=[seed]+recipe_links(seed_html,seed,urlparse(seed).netloc)[:args.limit_per_source]
            for page in pages:
                if page in seen or not allowed(page): continue
                seen.add(page); time.sleep(args.delay)
                recipes=recipe_objects(fetch(page),page,source)
                all_recipes.extend(recipes)
                print(f"{source}: {len(recipes)} recipe(s) from {page}")
        except Exception as error:
            print(f"skip {source}: {error}")
    unique={recipe["url"]:recipe for recipe in all_recipes if recipe.get("url")}
    output=Path(args.output); output.parent.mkdir(exist_ok=True); output.write_text(json.dumps(list(unique.values()),indent=2,ensure_ascii=False),encoding="utf-8")
    print(f"Wrote {len(unique)} source-linked recipes to {output}")

if __name__ == "__main__": main()
