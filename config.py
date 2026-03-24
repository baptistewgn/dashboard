"""Data Config"""

tickers = {
    # macro
    "SPX": "^GSPC",
    "DXY": "DX-Y.NYB",
    "US10Y": "^TNX",
    "VIX": "^VIX",

    # crypto
    "BTC": "BTC-USD",
    "ETH": "ETH-USD",

    # commodities
    "GOLD": "GC=F",
    "WTI": "CL=F",
}


"""Feature Config"""

return_windows = {
    1: "1d",
    20: "20d",
}

zscore_windows = {
    "short": 63,
    "long" : 252,
}


"""Storage Config"""

data_paths = {
    "raw": "data/raw_prices.parquet",
    "features": "data/features.parquet"
}


"""Ingest Config"""

start_date = "2020-01-01"
