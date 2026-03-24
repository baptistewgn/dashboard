import pandas as pd
from config import return_windows

def compute_features(df):
    out = df.copy()
    
    # returns based on row counts
    rets = []
    
    for w, name in return_windows.items():
        r = df.pct_change(w).add_suffix(f"_ret_{name}")
        rets.append(r)

    # week-to-date return anchored to the previous Friday close
    weekly_close = df.resample("W-FRI").last()
    prev_week_close = weekly_close.shift(1).reindex(df.index, method="ffill")
    wtd = df.div(prev_week_close).sub(1)
    wtd.columns = [f"{c}_ret_wtd" for c in df.columns]

    # month-to-date return anchored to the previous month-end close
    monthly_close = df.resample("M").last()
    prev_month_close = monthly_close.shift(1).reindex(df.index, method="ffill")
    mtd = df.div(prev_month_close).sub(1)
    mtd.columns = [f"{c}_ret_mtd" for c in df.columns]
    
    out = pd.concat([out] + rets + [wtd, mtd], axis=1)

    # zscore
    z63 = (df - df.rolling(63).mean()) / df.rolling(63).std()
    z63.columns = [f"{c}_z63" for c in df.columns]

    z252 = (df - df.rolling(252).mean()) / df.rolling(252).std()
    z252.columns = [f"{c}_z252" for c in df.columns]

    out = pd.concat([out, z63, z252], axis=1)

    return out
