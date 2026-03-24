from src.pipeline import run_pipeline
from src.report import print_dashboard, save_snapshot_json, save_snapshot_txt      #from src.report_rich import print_dashboard
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

df = run_pipeline()
print_dashboard(df)
save_snapshot_json(df)
save_snapshot_txt(df)
