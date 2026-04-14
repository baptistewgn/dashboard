import pandas as pd
from pathlib import Path
from config import data_paths
from src.time_utils import ensure_utc_index, ensure_utc_timestamp

PROJECT_ROOT = Path(__file__).resolve().parent.parent
data_path = PROJECT_ROOT / data_paths["raw"]

def load_prices():
    if data_path.exists():
        df = pd.read_parquet(data_path)
        if not df.empty:
            df = df.copy()
            df.index = ensure_utc_index(df.index)
        return df
    return pd.DataFrame()

def save_prices(df):
    df = df.copy()
    if not df.empty:
        df.index = ensure_utc_index(df.index)
    df = df[~df.index.duplicated(keep="last")]      # '~' obtained with 'opt + n' and stands for NOT
    df.sort_index(inplace=True)
    data_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(data_path)

def get_last_timestamp(df):
    if df.empty:
        return None
    return ensure_utc_timestamp(df.index.max())
