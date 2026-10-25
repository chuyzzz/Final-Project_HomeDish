"""Convert extracted USDA food/food_nutrient CSVs into the compact app table."""
import argparse
import pandas as pd

FIELDS = {1008: "kcal", 1003: "protein_g", 1004: "fat_g", 1005: "carbs_g", 1079: "fiber_g", 2000: "sugar_g", 1093: "sodium_mg", 1258: "sat_fat_g"}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--output", default="data/usda_full.csv")
    args = parser.parse_args()
    root = pd.read_csv(f"{args.input_dir}/food.csv", low_memory=False)
    nutrients = pd.read_csv(f"{args.input_dir}/food_nutrient.csv", low_memory=False)
    nutrients = nutrients[nutrients.nutrient_id.isin(FIELDS)].pivot_table(index="fdc_id", columns="nutrient_id", values="amount", aggfunc="first").rename(columns=FIELDS).reset_index()
    root[["fdc_id", "description"]].merge(nutrients, on="fdc_id").to_csv(args.output, index=False)

if __name__ == "__main__":
    main()
