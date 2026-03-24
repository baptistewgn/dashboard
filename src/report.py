import pandas as pd

def print_dashboard(df):
    last = df.iloc[-1]

    def fmt_num(x, width=8, decimals=2):
        if pd.isna(x):
            return " " * width
        return f"{x:>{width}.{decimals}f}"

    def fmt_pct(x, width=7, decimals=2):
        if pd.isna(x):
            return " " * width
        return f"{x * 100:>{width}.{decimals}f}"

    print()
    print("=" * 50)
    print("DASHBOARD".ljust(31) + f"{df.index[-1]}")
    print("=" * 50)

    print(
        f"RISK: {last['risk_regime']:<10}"
        f" LIQ: {last['liquidity_regime']:<14}"
    )
    print("-" * 50)

    sections = {
        "MACRO": ["^GSPC", "^TNX", "^VIX"],
        "FX": ["DX-Y.NYB"],
        "CRYPTO": ["BTC-USD", "ETH-USD"],
        "COMMODITIES": ["GC=F", "CL=F"],
    }

    for section, assets in sections.items():
        print(f"\n[{section}]")
        print("ASSET         LAST     1D%    WTD%    MTD%     Z63")
        print("-" * 50)

        for asset in assets:
            print(
                f"{asset:<8} "
                f"{fmt_num(last[asset], 9)} "
                f"{fmt_pct(last[f'{asset}_ret_1d'], 7)} "
                f"{fmt_pct(last[f'{asset}_ret_wtd'], 7)} "
                f"{fmt_pct(last[f'{asset}_ret_mtd'], 7)} "
                f"{fmt_num(last[f'{asset}_z63'], 7)}"
            )
    
    print()

def save_snapshot_json(df, path="data/snapshots/"):
    import os

    os.makedirs(path, exist_ok=True)

    ts = df.index[-1].strftime("%Y-%m-%d")
    file = f"{path}/snapshot_{ts}.json"

    df.iloc[-1].to_json(file)

    print(f"Saved JSON: {file}")

def save_snapshot_txt(df, path="data/snapshots/"):
    import os
    import sys

    os.makedirs(path, exist_ok=True)

    ts = df.index[-1].strftime("%Y-%m-%d")
    file = f"{path}/snapshot_{ts}.txt"

    with open(file, "w") as f:
        old_stdout = sys.stdout
        sys.stdout = f

        print_dashboard(df)

        sys.stdout = old_stdout

    print(f"Saved TXT: {file}")
