from src.pipeline import run_pipeline
from src.report import (
    get_run_timestamp,
    print_dashboard,
    save_snapshot_json,
    save_snapshot_txt,
)      #from src.report_rich import print_dashboard
from src.dashboard_html import render_dashboard_html
import sys
import os
import warnings

warnings.filterwarnings("ignore")
warnings.filterwarnings(
    "ignore",
    message=r".*Timestamp\.utcnow is deprecated.*",
    category=FutureWarning,
)

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

run_ts = get_run_timestamp()
df = run_pipeline()
print_dashboard(df, run_ts=run_ts)

if df.empty:
    raise SystemExit("run_daily.py: empty dataframe after pipeline; snapshots not written")

save_snapshot_json(df, run_ts=run_ts)
save_snapshot_txt(df, run_ts=run_ts)
render_dashboard_html(df, run_ts=run_ts)
