# HomeDish

HomeDish helps international students rebuilding a kitchen in the U.S. make familiar home dishes healthier without losing the feeling of home.

Upload a dish photo, review the ingredient and portion assumptions, choose one of two culturally recognizable lighter versions, or open a “How about?” set of three ingredient-linked source recipes. Move the choice into a weekly plan, pantry, Cook Mode, or grocery list. The current Discover catalog contains 238 recipes: 15 curated HomeDish recipes plus 223 source-linked records.

## Course submission package

- `app.py` — Streamlit product experience with Home, Discover, Planner, Pantry, Cook Mode, Grocery, Recipe Box, and photo analysis.
- `backend/` — FastAPI image-recognition and deterministic-calculation boundary.
- `agents/` — recognizer, USDA ingredient matcher, Swap Chef, ingredient-aware recipe matcher, and safety critic.
- `tools/` — USDA search, deterministic nutrition, and grocery-list utilities.
- `data/` — bundled USDA sample table, recipe catalog, and import/build scripts.
- `report/report.html` — 10-page course report.
- `report/slides.html` — 9-slide reveal.js presentation.
- `report_portal/` — local portal for opening both HTML documents.
- `logs/sample_run.jsonl` — redacted token/latency sample; live logs remain ignored.

## Run the app locally

Use Python 3.11+ and run these commands from this folder:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Add the teaching environment's PORTKEY_API value to .env.
```

Start the FastAPI backend in one terminal:

```bash
.venv/bin/uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Start Streamlit in a second terminal:

```bash
.venv/bin/streamlit run app.py
```

Open `http://127.0.0.1:8501`. The backend exposes `/health`, `/recognize`, and `/calculate`.

The app uses only `gpt_luna` through Portkey. Environment lookup checks `Final Project/.env` first and then the parent `.env`; the key is never committed. `.env.example` contains names only.

## Open the report and slide deck

For the local document portal, run from this folder:

```bash
.venv/bin/python -m http.server 8600 --bind 127.0.0.1
```

Then open `http://127.0.0.1:8600/report_portal/`. The portal links to both HTML documents and includes embedded previews.

## Tests and data

Run the current automated checks:

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m py_compile app.py
```

The bundled `data/usda_sample.csv` keeps a fresh setup small and keyless. Rebuild a larger table with:

```bash
python data/build_usda_table.py --input-dir /path/to/usda --output data/usda_full.csv
```

Then point `tools/usda.py` at the expanded table. Nutrition values and swap savings are computed by Python from USDA rows; the model does not provide final nutrition numbers. Estimates are not medical advice.

## Recipe library and provenance

`data/recipe_library.json` contains source-linked recipe metadata collected from public Recipe JSON-LD where each site permits automated access. The importer respects robots.txt, rate-limits requests, stores metadata and links rather than mirroring full publisher pages, and skips sites that block automated access.

Refresh source-linked records with:

```bash
python data/scrape_recipe_library.py --limit-per-source 4
```

To populate 200+ structured recipes from TheMealDB:

```bash
python data/import_themealdb.py --target 240
```

## Architecture and safeguards

The flow is: photo → vision recognizer → user confirmation → USDA candidate matcher → deterministic nutrition calculator → Swap Chef (two lighter versions) → ingredient-overlap retrieval → recipe matcher agent (three source-linked “How about?” recipes) → safety critic → grocery list. Pydantic validates structured handoffs; image uploads are resized to 768 px; visible image text is treated as data, not instructions; the recipe agent can only select from the deterministic shortlist; the critic permits at most one repair; and the budget caps each run at 10 LLM calls and `$0.05`.

The report records the measured local sample: 29 provider calls, 82,750 input tokens, 23,139 output tokens, zero cached input tokens, and 119.62 seconds total latency. Dollar cost is intentionally not calculated until the official course price configuration is populated.

## Course references

- [MGT 409 project requirements](https://zlisto.github.io/mgt_409_fa26/project_requirements.html)
- [USDA FoodData Central](https://fdc.nal.usda.gov/)
- [TheMealDB API](https://www.themealdb.com/api.php)
- [reveal.js](https://revealjs.com/)
