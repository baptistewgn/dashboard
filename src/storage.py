import pandas as pd
from pathlib import Path
from config import data_paths

PROJECT_ROOT = Path(__file__).resolve().parent.parent
data_path = PROJECT_ROOT / data_paths["raw"]

def load_prices():
    if data_path.exists():
        return pd.read_parquet(data_path)
    return pd.DataFrame()

def save_prices(df):
    df = df[~df.index.duplicated(keep="last")]      # '~' obtained with 'opt + n' and stands for NOT
    df.sort_index(inplace=True)
    data_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(data_path)

def get_last_timestamp(df):
    if df.empty:
        return None
    return df.index.max()
