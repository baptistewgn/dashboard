import yfinance as yf
import pandas as pd
from config import tickers, start_date
from src.time_utils import ensure_utc_index, ensure_utc_timestamp

def fetch_incremental(last_ts=None):
    # end_date = pd.Timestamp.now().normalize()  # if fetch after 12pm
    end_date = pd.Timestamp.now("UTC").normalize() + pd.Timedelta(days=1)  # if fetch before 12pm

    if last_ts is None:
        start_ts = ensure_utc_timestamp(start_date)
    else:
        start_ts = ensure_utc_timestamp(last_ts) + pd.Timedelta(days=1)

    if start_ts > end_date:
        return pd.DataFrame()  # nothing to fetch

    start_date_str = start_ts.strftime("%Y-%m-%d")
    df = yf.download(
        tickers=list(tickers.values()),
        start=start_date_str,
        end=end_date.strftime("%Y-%m-%d"),
        interval="1d"
        ,
        auto_adjust=False,
        threads=False,
        progress=False,
    )["Close"]

    if not df.empty:
        df.index = ensure_utc_index(df.index)

    return df
