"""Data Config"""

tickers = {
    # macro
    "US2Y": "^IRX",
    "US5Y": "^FVX",
    "US10Y": "^TNX",
    "US30Y": "^TYX",
    "MOVE": "^MOVE",

    #indices
    "STOXX": "^STOXX50E",
    "SPX": "^GSPC",
    "VIX": "^VIX",

    #fx
    "DXY": "DX-Y.NYB",
    "EURUSD": "EURUSD=X",

    # commodities
    "GOLD": "GC=F",
    "WTI": "CL=F",

    # crypto
    "BTC": "BTC-USD",
    "ETH": "ETH-USD",
    "SOL": "SOL-USD",
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
