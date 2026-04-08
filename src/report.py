import pandas as pd
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from config import tickers

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RUN_TZ = ZoneInfo("Europe/Luxembourg")


def get_run_timestamp():
    return datetime.now(RUN_TZ)


def _normalize_display_timestamp(ts):
    if ts is None:
        return None
    out = pd.Timestamp(ts)
    if out.tzinfo is None:
        return out
    return out.tz_convert(RUN_TZ)


def _describe_staleness(data_ts, run_ts):
    if data_ts is None:
        return "unknown"

    data_day = _normalize_display_timestamp(data_ts).date()
    run_day = run_ts.date()
    delta_days = (run_day - data_day).days

    if delta_days <= 0:
        return "current"
    if delta_days == 1:
        return "1 day old"
    return f"{delta_days} days old"


def print_dashboard(df, run_ts=None):
    run_ts = run_ts or get_run_timestamp()

    if df.empty:
        print()
        print("=" * 50)
        print("DASHBOARD".ljust(31) + run_ts.strftime("%Y-%m-%d %H:%M:%S %Z"))
        print("=" * 50)
        print("DATA STATUS: empty dataframe")
        print("FETCH STATUS: no market data available for this run")
        print()
        return

    last = df.iloc[-1]
    data_ts = _normalize_display_timestamp(df.index[-1])
    stale_label = _describe_staleness(data_ts, run_ts)

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
    print("DASHBOARD".ljust(31) + run_ts.strftime("%Y-%m-%d %H:%M:%S %Z"))
    print("=" * 50)
    print(f"DATA AS OF: {data_ts}")
    print(f"DATA STALENESS: {stale_label}")

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

def save_snapshot_json(df, run_ts=None, path="data/snapshots/json"):
    run_ts = run_ts or get_run_timestamp()

    if df.empty:
        raise ValueError("Cannot save JSON snapshot for an empty dataframe")

    save_path = PROJECT_ROOT / Path(path)
    save_path.mkdir(parents=True, exist_ok=True)
    ts = run_ts.strftime("%Y-%m-%d")
    data_ts = _normalize_display_timestamp(df.index[-1]).strftime("%Y-%m-%d")
    file = save_path / f"snapshot_run_{ts}_data_{data_ts}.json"

    df.iloc[-1].to_json(file)

    print(f"Saved JSON: {file}")

def save_snapshot_txt(df, run_ts=None, path="data/snapshots/txt"):
    import sys

    run_ts = run_ts or get_run_timestamp()

    if df.empty:
        raise ValueError("Cannot save TXT snapshot for an empty dataframe")

    save_path = PROJECT_ROOT / Path(path)
    save_path.mkdir(parents=True, exist_ok=True)
    ts = run_ts.strftime("%Y-%m-%d")
    data_ts = _normalize_display_timestamp(df.index[-1]).strftime("%Y-%m-%d")
    file = save_path / f"snapshot_run_{ts}_data_{data_ts}.txt"

    with open(file, "w") as f:
        old_stdout = sys.stdout
        sys.stdout = f

        print_dashboard(df, run_ts=run_ts)

        sys.stdout = old_stdout

    print(f"Saved TXT: {file}")
