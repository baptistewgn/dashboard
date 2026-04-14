import pandas as pd


UTC = "UTC"


def ensure_utc_timestamp(value):
    if value is None:
        return None

    ts = pd.Timestamp(value)
    if ts.tzinfo is None:
        return ts.tz_localize(UTC)
    return ts.tz_convert(UTC)


def ensure_utc_index(index_like):
    idx = pd.DatetimeIndex(pd.to_datetime(index_like))
    if idx.tz is None:
        return idx.tz_localize(UTC)
    return idx.tz_convert(UTC)
