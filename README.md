# Dashboard

Simple Python dashboard for daily macro, FX, and crypto market monitoring.

It pulls price data, builds rolling features and regime labels, prints a terminal dashboard, and saves daily snapshots.

## What It Does

- Fetches market data incrementally with `yfinance`
- Stores raw prices in a `.parquet` file
- Builds features such as 1d, 20d, WTD, MTD, `z63`, and `z252`
- Computes simple risk and liquidity regimes
- Prints a daily dashboard in the terminal
- Genrate daily snapshots to `data/snapshots/`

## Project Structure

- `run_daily.py` - main entry point
- `config.py` - tickers, windows, paths, and start date
- `src/ingest.py` - data fetch logic
- `src/pipeline.py` - end-to-end pipeline
- `src/report.py` - terminal dashboard and snapshot export
- `doc/` - specification and architecture notes

## Requirements

- Python 3.11+ recommended
- Install dependencies:

```bash
pip install pandas pyarrow yfinance
```

## Run

From the project root:

```bash
python run_daily.py
```

## Output

After a run, the project updates:

- `data/raw_prices.parquet`
- `data/features.parquet`
- `data/snapshots/json/snapshot_YYYY-MM-DD.json`
- `data/snapshots/txt/snapshot_YYYY-MM-DD.txt`

## Notes

- Raw prices keep the original trading calendar, including weekend crypto data.
- Features and regimes are computed on market days to avoid weekend gaps distorting macro calculations.