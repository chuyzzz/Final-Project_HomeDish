"""Normalize X-Wines CSV files into the small catalog used by HomeDish.

The repository's Test version is intentionally small (100 wines plus 1,000
ratings) and is bundled for a reproducible demo. The same command accepts the
Slim or Full X-Wines CSV exports downloaded from the official project.
"""

from __future__ import annotations

import argparse
import ast
import csv
import json
from collections import defaultdict
from pathlib import Path


XWINES_WINES_URL = "https://raw.githubusercontent.com/rogerioxavier/X-Wines/main/Dataset/last/XWines_Test_100_wines.csv"
XWINES_RATINGS_URL = "https://raw.githubusercontent.com/rogerioxavier/X-Wines/main/Dataset/last/XWines_Test_1K_ratings.csv"
XWINES_SOURCE = "https://github.com/rogerioxavier/X-Wines"


def parse_list(value: str) -> list[str]:
    try:
        parsed = ast.literal_eval(value or "[]")
    except (SyntaxError, ValueError):
        parsed = []
    if isinstance(parsed, (list, tuple)):
        return [str(item).strip() for item in parsed if str(item).strip()]
    return [str(parsed).strip()] if parsed else []


def load_ratings(path: Path) -> dict[str, dict[str, float | int]]:
    values: dict[str, list[float]] = defaultdict(list)
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            try:
                values[str(row["WineID"])].append(float(row["Rating"]))
            except (KeyError, TypeError, ValueError):
                continue
    return {
        wine_id: {"rating": round(sum(scores) / len(scores), 2), "rating_count": len(scores)}
        for wine_id, scores in values.items()
        if scores
    }


def build_catalog(wines_path: Path, ratings_path: Path | None = None, limit: int | None = None) -> list[dict]:
    ratings = load_ratings(ratings_path) if ratings_path and ratings_path.exists() else {}
    catalog: list[dict] = []
    with wines_path.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            wine_id = str(row.get("WineID", "")).strip()
            if not wine_id:
                continue
            score = ratings.get(wine_id, {"rating": 0.0, "rating_count": 0})
            catalog.append({
                "id": f"xwines:{wine_id}",
                "name": row.get("WineName", "Unnamed wine").strip(),
                "type": row.get("Type", "").strip(),
                "grapes": parse_list(row.get("Grapes", "")),
                "harmonize": parse_list(row.get("Harmonize", "")),
                "abv": float(row["ABV"]) if row.get("ABV") else None,
                "body": row.get("Body", "").strip(),
                "acidity": row.get("Acidity", "").strip(),
                "country": row.get("Country", "").strip(),
                "region": row.get("RegionName", "").strip(),
                "winery": row.get("WineryName", "").strip(),
                "website": row.get("Website", "").strip(),
                "rating": score["rating"],
                "rating_count": score["rating_count"],
                "source": "X-Wines Test sample",
                "source_url": XWINES_SOURCE,
            })
            if limit and len(catalog) >= limit:
                break
    return catalog


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wines", type=Path, required=True, help="X-Wines *_wines.csv file")
    parser.add_argument("--ratings", type=Path, help="Optional X-Wines ratings CSV")
    parser.add_argument("--output", type=Path, required=True, help="Normalized JSON output")
    parser.add_argument("--limit", type=int, help="Optional row limit for a demo catalog")
    args = parser.parse_args()
    result = build_catalog(args.wines, args.ratings, args.limit)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(result)} wines to {args.output}")


if __name__ == "__main__":
    main()
