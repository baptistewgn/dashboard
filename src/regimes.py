import pandas as pd

def compute_regimes(df):
    out = pd.DataFrame(index=df.index)

    # Risk regime
    risk_on = (df["^GSPC_ret_20d"] > 0) & (df["^VIX_z63"] < 0.5)
    risk_off = (df["^GSPC_ret_20d"] < 0) & (df["^VIX_z63"] > 1)

    out["risk_regime"] = "Mixed"
    out.loc[risk_on, "risk_regime"] = "Risk-On"
    out.loc[risk_off, "risk_regime"] = "Risk-Off"

    # Liquidity regime
    out["liquidity_regime"] = "Neutral"
    if {"^DX-Y.NYB_ret_20d", "^TNX_ret_20d"}.issubset(df.columns):
        liq_tight = (df["^DX-Y.NYB_ret_20d"] > 0) & (df["^TNX_ret_20d"] > 0)
        liq_ease = (df["^DX-Y.NYB_ret_20d"] < 0)

        out.loc[liq_tight, "liquidity_regime"] = "Tightening"
        out.loc[liq_ease, "liquidity_regime"] = "Easing"

    return out
