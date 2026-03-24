import pandas as pd

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
        r = df.pct_change(w).add_suffix(f"_ret_{name}")
        rets.append(r)
    
    out = pd.concat([out] + rets, axis=1)

    # zscore
    z63 = (df - df.rolling(63).mean()) / df.rolling(63).std()
    z63.columns = [f"{c}_z63" for c in df.columns]

    z252 = (df - df.rolling(252).mean()) / df.rolling(252).std()
    z252.columns = [f"{c}_z252" for c in df.columns]

    out = pd.concat([out, z63, z252], axis=1)

    return out