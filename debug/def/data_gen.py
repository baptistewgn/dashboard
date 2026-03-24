import pandas as pd
import numpy as np

def generate_timeseries_multi(
    assets=("SPX", "VIX", "DXY", "US10Y"),
    n=1000,
    start_date="2020-01-01",
    freq="D",
    seed=42
):
    np.random.seed(seed)

    dates = pd.date_range(start=start_date, periods=n, freq=freq)

    data = {}

    for i, asset in enumerate(assets):
        # different seed per asset (important)
        np.random.seed(seed + i)

        returns = np.random.normal(0, 0.01, n)
        prices = 100 * (1 + returns).cumprod()

        data[asset] = pd.Series(prices, index=dates)

    df = pd.concat(data, axis=1)

    return df

"""simulate config.py"""

windows = {
    1: "1d",
    5: "5d",
    21: "21d"
}

def compute_features(df):
    out = df.copy()
    
    #returns
    rets = []
    
    for w, name in windows.items():
        r = df.pct_change(w).add_suffix(f"_{name}_ret")
        rets.append(r)
    
    out = pd.concat([out] + rets, axis=1)

    # zscore
    z63 = (df - df.rolling(63).mean()) / df.rolling(63).std()
    z63.columns = [f"{c}_z63" for c in df.columns]

    z252 = (df - df.rolling(252).mean()) / df.rolling(252).std()
    z252.columns = [f"{c}_z252" for c in df.columns]

    out = pd.concat([out, z63, z252], axis=1)

    return out