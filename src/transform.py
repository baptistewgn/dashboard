import pandas as pd
from config import return_windows

def compute_features(df):
    out = df.copy()
    
    # returns based on row counts
    rets = []
    
    for w, name in return_windows.items():
        r = df.pct_change(w, fill_method=None).add_suffix(f"_ret_{name}")
        rets.append(r)

    # Anchor each trading week to the prior close before the week's first row.
    week_base = df.shift(1).groupby(df.index.to_period("W-SUN")).transform("first")
    wtd = df.div(week_base).sub(1)
    wtd.columns = [f"{c}_ret_wtd" for c in df.columns]

    # Anchor each trading month to the prior close before the month's first row.
    month_base = df.shift(1).groupby(df.index.to_period("M")).transform("first")
    mtd = df.div(month_base).sub(1)
    mtd.columns = [f"{c}_ret_mtd" for c in df.columns]
    
    out = pd.concat([out] + rets + [wtd, mtd], axis=1)

    # zscore
    z63 = (df - df.rolling(63).mean()) / df.rolling(63).std()
    z63.columns = [f"{c}_z63" for c in df.columns]

    z252 = (df - df.rolling(252).mean()) / df.rolling(252).std()
    z252.columns = [f"{c}_z252" for c in df.columns]

    out = pd.concat([out, z63, z252], axis=1)

    return out
