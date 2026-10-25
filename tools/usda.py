from pathlib import Path
import pandas as pd
from rapidfuzz import process, fuzz
DATA=Path(__file__).resolve().parents[1]/"data"/"usda_sample.csv"; _df=None
def table():
    global _df
    if _df is None: _df=pd.read_csv(DATA,dtype={"fdc_id":str})
    return _df
def search(name,k=10):
    df=table(); hits=process.extract(name,df.description.tolist(),scorer=fuzz.WRatio,limit=k)
    return [df.iloc[idx].to_dict() for _,_,idx in hits]
