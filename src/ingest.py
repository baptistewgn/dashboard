import yfinance as yf
import pandas as pd
from config import tickers, start_date

def _download_close_series(symbol, start_date_str, end_date_str):
    df = yf.download(
        tickers=symbol,
        start=start_date_str,
        end=end_date_str,
        interval="1d",
        auto_adjust=False,
        threads=False,
        progress=False,
    )

    if df.empty or "Close" not in df:
        return pd.Series(name=symbol, dtype=float)

    close = df["Close"]
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]

    close.name = symbol
    return close

def fetch_incremental(last_ts=None):
    # yfinance treats `end` as exclusive. Using today's UTC date keeps the
    # fetch window bounded to completed daily bars and avoids deprecated UTC APIs.
    end_date = pd.Timestamp.now(tz="UTC").normalize().tz_localize(None)
    overlap_days = 7

    if last_ts is None:
        start_date_str = pd.Timestamp(start_date).strftime("%Y-%m-%d")
    else:
        refresh_start_date = pd.Timestamp(last_ts).normalize() - pd.Timedelta(days=overlap_days)
        start_date_str = max(refresh_start_date, pd.Timestamp(start_date)).strftime("%Y-%m-%d")

    if pd.Timestamp(start_date_str) > end_date:
        return pd.DataFrame()  # nothing to fetch

    frames = []
    end_date_str = end_date.strftime("%Y-%m-%d")
    for symbol in tickers.values():
        close = _download_close_series(symbol, start_date_str, end_date_str)
        if not close.empty:
            frames.append(close)

    if not frames:
        return pd.DataFrame()

    df = pd.concat(frames, axis=1).sort_index()
    df.index.name = "Date"
    return df
