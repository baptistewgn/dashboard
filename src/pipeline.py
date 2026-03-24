from src.storage import load_prices, save_prices, get_last_timestamp
from src.ingest import fetch_incremental
from src.transform import compute_features
from src.regimes import compute_regimes
import pandas as pd
from pathlib import Path
from config import data_paths

PROJECT_ROOT = Path(__file__).resolve().parent.parent
features_path = PROJECT_ROOT / data_paths["features"]

def build_feature_prices(df):
    if df.empty:
        return df

    market_columns = [col for col in ["^GSPC", "^TNX", "^VIX"] if col in df.columns]
    if not market_columns:
        return df.sort_index()

    market_index = df[market_columns].dropna(how="all").index
    return df.reindex(market_index).sort_index()

def run_pipeline():
    # load existing
    df_old = load_prices()                                      # debug_storage.ipynb
    last_ts = get_last_timestamp(df_old)                        # debug_ingest.ipynb

    # fetch new
    df_new = fetch_incremental(last_ts)                         # debug_ingest.ipynb

    # merge
    df_all = pd.concat([df_old, df_new])                        # debug_pipeline.ipynb
    df_all = df_all[~df_all.index.duplicated(keep="last")]      # debug_pipeline.ipynb

    # save raw
    save_prices(df_all)                                         # debug_storage.ipynb

    # compute features on market days only to avoid weekend NaNs
    df_features_input = build_feature_prices(df_all)            # debug_pipeline.ipynb
    feat = compute_features(df_features_input)                  # debug_transform.ipynb

    # regimes
    regimes = compute_regimes(feat)                             # debug_regimes.ipynb

    final = pd.concat([feat, regimes], axis=1)                  # debug_regimes.ipynb

    features_path.parent.mkdir(parents=True, exist_ok=True)
    final.to_parquet(features_path)                             # debug_regimes.ipynb

    return final
