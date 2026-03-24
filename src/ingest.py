import yfinance as yf
import pandas as pd
from config import tickers, start_date

def fetch_incremental(last_ts=None):
    # end_date = pd.Timestamp.now().normalize()  # if fetch after 12pm
    end_date = pd.Timestamp.now().normalize() + pd.Timedelta(days=1) # if fetch before 12pm

    if last_ts is None:
        start_date_str = pd.Timestamp(start_date).strftime("%Y-%m-%d")
    else:
        next_start_date = pd.Timestamp(last_ts) + pd.Timedelta(days=1)
        start_date_str = next_start_date.strftime("%Y-%m-%d")

    if pd.Timestamp(start_date_str) > end_date:
        return pd.DataFrame()  # nothing to fetch
    
    df = yf.download(
        tickers=list(tickers.values()),
        start=start_date_str,
        end=end_date.strftime("%Y-%m-%d"),
        interval="1d"
        ,
        auto_adjust=False,
        threads=False,
    )["Close"]

    return df
