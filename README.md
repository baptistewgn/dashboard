# Dashboard

Simple Python dashboard for daily macro, FX, and crypto market monitoring.

It pulls price data, builds rolling features and regime labels, prints a terminal dashboard, and saves daily snapshots.

## What It Does

- Fetches market data incrementally with `yfinance`
- Stores raw prices in `data/raw_prices.parquet`
- Normalizes stored price timestamps to UTC
- Builds features such as 1d, 20d, WTD, MTD, `z63`, and `z252`
- Computes simple risk and liquidity regimes
- Prints a daily dashboard in the terminal
- Saves daily snapshots to `data/snapshots/`
- Generates a static HTML dashboard at `output/dashboard.html`

## Project Structure

- `run_daily.py` - main entry point
- `config.py` - tickers, windows, paths, and start date
- `src/ingest.py` - data fetch logic
- `src/time_utils.py` - shared UTC timestamp helpers
- `src/pipeline.py` - end-to-end pipeline
- `src/report.py` - terminal dashboard and snapshot export
- `cron_logs/run_daily_cron.sh` - cron wrapper that captures stderr and sends failure alerts
- `cron_logs/dashboard.crontab` - saved cron entry used to schedule the daily run
- `data/` - local parquet files and snapshots
- `doc/` - specification and architecture notes

## Requirements

- Python 3.11+ recommended
- Create and activate a virtual environment, then install dependencies:

```bash
python3.11 -m venv .venv
. .venv/bin/activate
pip install pandas pyarrow yfinance
```

## Run

From the project root:

```bash
.venv/bin/python run_daily.py
```

To run with the cron wrapper used for scheduled jobs:

```bash
sh cron_logs/run_daily_cron.sh
```

## Output

After a run, the project updates:

- `data/raw_prices.parquet`
- `data/features.parquet`
- `data/snapshots/json/snapshot_run_YYYY-MM-DD_data_YYYY-MM-DD.json`
- `data/snapshots/txt/snapshot_run_YYYY-MM-DD_data_YYYY-MM-DD.txt`
- `output/dashboard.html`

## Notes

- Raw prices keep the original trading calendar, including weekend crypto data.
- Raw price indexes are normalized to UTC on load, fetch, and save so timestamp comparisons stay timezone-safe.
- Features and regimes are computed on market days to avoid weekend gaps distorting macro calculations.
- The dashboard header shows the run timestamp separately from the market data timestamp.
- If market data fetch fails and the dataframe is empty, the script prints an explicit empty-data status and does not write snapshots.
- The scheduled job should call `cron_logs/run_daily_cron.sh`, which writes to `cron_logs/logfile.log`.
- On non-zero exit, the cron wrapper attempts to send an email alert and now logs whether that alert was sent, skipped, or failed.
- Deprecation warnings from inside `yfinance` may still appear upstream; the repository code avoids deprecated UTC timestamp creation.
