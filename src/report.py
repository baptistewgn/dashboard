import pandas as pd
from pathlib import Path
from config import tickers

PROJECT_ROOT = Path(__file__).resolve().parent.parent

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
        "MACRO": ["US2Y", "US5Y", "US10Y", "US30Y", "MOVE"],
        "INDICES": ["STOXX", "SPX", "VIX"],
        "FX": ["DXY", "EURUSD"],
        "COMMODITIES": ["GOLD", "WTI"],
        "CRYPTO": ["BTC", "ETH", "SOL"],
    }

    def resolve_column(asset_name):
        exact_ticker = tickers.get(asset_name, asset_name)
        if exact_ticker in last.index:
            return exact_ticker
        if asset_name in last.index:
            return asset_name
        return exact_ticker

    for section, assets in sections.items():
        print(f"\n[{section}]")
        print("ASSET         LAST     1D%    WTD%    MTD%     Z63")
        print("-" * 50)

        for asset_name in assets:
            asset_col = resolve_column(asset_name)
            print(
                f"{asset_name:<8} "
                f"{fmt_num(last[asset_col], 9)} "
                f"{fmt_pct(last[f'{asset_col}_ret_1d'], 7)} "
                f"{fmt_pct(last[f'{asset_col}_ret_wtd'], 7)} "
                f"{fmt_pct(last[f'{asset_col}_ret_mtd'], 7)} "
                f"{fmt_num(last[f'{asset_col}_z63'], 7)}"
            )
    
    print()

def save_snapshot_json(df, path="data/snapshots/json"):
    save_path = PROJECT_ROOT / Path(path)
    save_path.mkdir(parents=True, exist_ok=True)
    ts = df.index[-1].strftime("%Y-%m-%d")
    file = save_path / f"snapshot_{ts}.json"

    df.iloc[-1].to_json(file)

    print(f"Saved JSON: {file}")

def save_snapshot_txt(df, path="data/snapshots/txt"):
    import sys

    save_path = PROJECT_ROOT / Path(path)
    save_path.mkdir(parents=True, exist_ok=True)
    ts = df.index[-1].strftime("%Y-%m-%d")
    file = save_path / f"snapshot_{ts}.txt"

    with open(file, "w") as f:
        old_stdout = sys.stdout
        sys.stdout = f

        print_dashboard(df)

        sys.stdout = old_stdout

    print(f"Saved TXT: {file}")
