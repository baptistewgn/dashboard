import json
from html import escape
from pathlib import Path

import pandas as pd

from config import tickers
from src.report import get_run_timestamp
from src.time_utils import ensure_utc_timestamp

PROJECT_ROOT = Path(__file__).resolve().parent.parent

SECTIONS = {
    "Macro": ["US2Y", "US5Y", "US10Y", "US30Y", "MOVE"],
    "Indices": ["STOXX", "SPX", "VIX"],
    "FX": ["DXY", "EURUSD"],
    "Commodities": ["GOLD", "WTI"],
    "Crypto": ["BTC", "ETH", "SOL"],
}

RISK_COMPONENTS = [
    {
        "label": "SPX 20D",
        "column": "^GSPC_ret_20d",
        "format": "pct",
        "explanation": "Risk-On when above 0%",
    },
    {
        "label": "VIX Z63",
        "column": "^VIX_z63",
        "format": "num",
        "explanation": "Risk-On when below 0.5, Risk-Off when above 1.0",
    },
]

LIQUIDITY_COMPONENTS = [
    {
        "label": "DXY 20D",
        "column": "DX-Y.NYB_ret_20d",
        "format": "pct",
        "explanation": "Easing when below 0%",
    },
    {
        "label": "US10Y 20D",
        "column": "^TNX_ret_20d",
        "format": "pct",
        "explanation": "Tightening when above 0% with DXY 20D above 0%",
    },
]


def _normalize_display_timestamp(ts):
    if ts is None:
        return None
    return ensure_utc_timestamp(ts).tz_convert("Europe/Luxembourg")


def _describe_staleness(data_ts, run_ts):
    if data_ts is None:
        return "unknown"

    data_day = _normalize_display_timestamp(data_ts).date()
    run_day = run_ts.date()
    delta_days = (run_day - data_day).days

    if delta_days <= 0:
        return "current"
    if delta_days == 1:
        return "1 day old"
    return f"{delta_days} days old"


def _resolve_column(columns, asset_name):
    exact_ticker = tickers.get(asset_name, asset_name)
    if exact_ticker in columns:
        return exact_ticker
    if asset_name in columns:
        return asset_name
    return None


def _fmt_num(value, decimals=2):
    if pd.isna(value):
        return "-"
    return f"{value:.{decimals}f}"


def _fmt_pct(value, decimals=2):
    if pd.isna(value):
        return "-"
    return f"{value * 100:.{decimals}f}%"


def _fmt_metric(value, metric_format):
    if metric_format == "pct":
        return _fmt_pct(value)
    return _fmt_num(value)


def _sign_class(value):
    if pd.isna(value):
        return "neutral"
    if value > 0:
        return "up"
    if value < 0:
        return "down"
    return "neutral"


def _state_class(value):
    if value is None:
        return "state-neutral"

    text = str(value).lower()
    if any(token in text for token in ["risk-on", "easing", "current"]):
        return "state-good"
    if any(token in text for token in ["risk-off", "tightening"]):
        return "state-bad"
    return "state-neutral"


def _build_snapshot_sections(df):
    last = df.iloc[-1]
    output = []

    for section, assets in SECTIONS.items():
        rows = []
        for asset_name in assets:
            asset_col = _resolve_column(df.columns, asset_name)
            if asset_col is None:
                continue

            rows.append(
                {
                    "asset": asset_name,
                    "last": _fmt_num(last.get(asset_col)),
                    "ret_1d": _fmt_pct(last.get(f"{asset_col}_ret_1d")),
                    "ret_1d_class": _sign_class(last.get(f"{asset_col}_ret_1d")),
                    "ret_wtd": _fmt_pct(last.get(f"{asset_col}_ret_wtd")),
                    "ret_wtd_class": _sign_class(last.get(f"{asset_col}_ret_wtd")),
                    "ret_mtd": _fmt_pct(last.get(f"{asset_col}_ret_mtd")),
                    "ret_mtd_class": _sign_class(last.get(f"{asset_col}_ret_mtd")),
                    "z63": _fmt_num(last.get(f"{asset_col}_z63")),
                }
            )

        if rows:
            output.append({"section": section, "rows": rows})

    return output


def _build_asset_charts(df, lookback=126):
    hist = df.tail(lookback)
    groups = []

    for section, assets in SECTIONS.items():
        charts = []
        for asset_name in assets:
            asset_col = _resolve_column(hist.columns, asset_name)
            if asset_col is None:
                continue

            series = hist[asset_col].dropna()
            if series.empty:
                continue

            charts.append(
                {
                    "id": f"chart-{section.lower()}-{asset_name.lower()}",
                    "title": asset_name,
                    "subtitle": asset_col,
                    "traces": [
                        {
                            "name": asset_name,
                            "mode": "lines",
                            "type": "scatter",
                            "x": [pd.Timestamp(idx).strftime("%Y-%m-%d") for idx in series.index],
                            "y": [None if pd.isna(v) else float(v) for v in series.tolist()],
                            "line": {"width": 1.5, "color": "#f5a623"},
                        }
                    ],
                    "layout": {
                        "paper_bgcolor": "#000000",
                        "plot_bgcolor": "#000000",
                        "font": {"color": "#f0f0f0", "family": "Menlo, Consolas, monospace"},
                        "margin": {"l": 38, "r": 12, "t": 10, "b": 26},
                        "showlegend": False,
                        "xaxis": {
                            "type": "date",
                            "gridcolor": "#202020",
                            "tickfont": {"size": 9},
                            "zeroline": False,
                        },
                        "yaxis": {
                            "gridcolor": "#202020",
                            "tickfont": {"size": 9},
                            "zeroline": False,
                        },
                        "hovermode": "x unified",
                    },
                }
            )

        if charts:
            groups.append({"section": section, "charts": charts})

    return groups


def _build_component_cards(df, components, state_label, chart_prefix, lookback=63):
    hist = df.tail(lookback)
    last = df.iloc[-1]
    cards = []

    for component in components:
        col = component["column"]
        if col not in df.columns:
            continue

        series = hist[col].dropna()
        if series.empty:
            continue

        cards.append(
                {
                    "label": component["label"],
                    "value": _fmt_metric(last.get(col), component["format"]),
                    "value_class": _sign_class(last.get(col)),
                    "explanation": component["explanation"],
                    "id": f"{chart_prefix}-{col.lower().replace('^', '').replace('=', '').replace('.', '-').replace('_', '-')}",
                    "traces": [
                    {
                        "name": component["label"],
                        "mode": "lines",
                        "type": "scatter",
                        "x": [pd.Timestamp(idx).strftime("%Y-%m-%d") for idx in series.index],
                        "y": [None if pd.isna(v) else float(v) for v in series.tolist()],
                        "line": {"width": 1.25, "color": "#f5a623"},
                    }
                ],
                "layout": {
                    "paper_bgcolor": "#000000",
                    "plot_bgcolor": "#000000",
                    "font": {"color": "#f0f0f0", "family": "Menlo, Consolas, monospace"},
                    "margin": {"l": 28, "r": 8, "t": 8, "b": 20},
                    "showlegend": False,
                    "xaxis": {
                        "type": "date",
                        "showgrid": False,
                        "showticklabels": False,
                        "zeroline": False,
                    },
                    "yaxis": {
                        "gridcolor": "#202020",
                        "tickfont": {"size": 9},
                        "zeroline": False,
                    },
                    "hovermode": "x unified",
                },
            }
        )

    return {"state": state_label, "cards": cards}


def _build_history_payload(df):
    history = {}

    for idx, row in df.iterrows():
        date_key = pd.Timestamp(idx).strftime("%Y-%m-%d")
        sections = []

        for section, assets in SECTIONS.items():
            rows = []
            for asset_name in assets:
                asset_col = _resolve_column(df.columns, asset_name)
                if asset_col is None:
                    continue

                rows.append(
                    {
                        "asset": asset_name,
                        "last": _fmt_num(row.get(asset_col)),
                        "ret_1d": _fmt_pct(row.get(f"{asset_col}_ret_1d")),
                        "ret_1d_class": _sign_class(row.get(f"{asset_col}_ret_1d")),
                        "ret_wtd": _fmt_pct(row.get(f"{asset_col}_ret_wtd")),
                        "ret_wtd_class": _sign_class(row.get(f"{asset_col}_ret_wtd")),
                        "ret_mtd": _fmt_pct(row.get(f"{asset_col}_ret_mtd")),
                        "ret_mtd_class": _sign_class(row.get(f"{asset_col}_ret_mtd")),
                        "z63": _fmt_num(row.get(f"{asset_col}_z63")),
                    }
                )

            if rows:
                sections.append(
                    {
                        "section": section,
                        "slug": section.lower().replace(" ", "-"),
                        "rows": rows,
                    }
                )

        risk_components = []
        for component in RISK_COMPONENTS:
            value = row.get(component["column"])
            risk_components.append(
                {
                    "label": component["label"],
                    "value": _fmt_metric(value, component["format"]),
                    "value_class": _sign_class(value),
                    "explanation": component["explanation"],
                }
            )

        liquidity_components = []
        for component in LIQUIDITY_COMPONENTS:
            value = row.get(component["column"])
            liquidity_components.append(
                {
                    "label": component["label"],
                    "value": _fmt_metric(value, component["format"]),
                    "value_class": _sign_class(value),
                    "explanation": component["explanation"],
                }
            )

        history[date_key] = {
            "risk_state": str(row.get("risk_regime", "-")),
            "risk_state_class": _state_class(row.get("risk_regime", "-")),
            "liquidity_state": str(row.get("liquidity_regime", "-")),
            "liquidity_state_class": _state_class(row.get("liquidity_regime", "-")),
            "sections": sections,
            "risk_components": risk_components,
            "liquidity_components": liquidity_components,
        }

    return history


def render_dashboard_html(df, run_ts=None, path="output/dashboard.html"):
    run_ts = run_ts or get_run_timestamp()

    if df.empty:
        raise ValueError("Cannot render HTML dashboard for an empty dataframe")

    output_path = PROJECT_ROOT / Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    last = df.iloc[-1]
    data_ts = _normalize_display_timestamp(df.index[-1])
    stale_label = _describe_staleness(data_ts, run_ts)
    available_dates = [pd.Timestamp(idx).strftime("%Y-%m-%d") for idx in df.index]
    selected_date = available_dates[-1]
    history_payload = _build_history_payload(df)

    snapshot_sections = _build_snapshot_sections(df)
    asset_groups = _build_asset_charts(df)
    risk_detail = _build_component_cards(
        df,
        RISK_COMPONENTS,
        str(last.get("risk_regime", "-")),
        "risk-detail",
    )
    liquidity_detail = _build_component_cards(
        df,
        LIQUIDITY_COMPONENTS,
        str(last.get("liquidity_regime", "-")),
        "liquidity-detail",
    )

    snapshot_blocks = []
    for section in snapshot_sections:
        section_slug = section["section"].lower().replace(" ", "-")
        row_html = "".join(
            (
                "<tr>"
                f"<td class=\"asset-col\">{escape(row['asset'])}</td>"
                f"<td class=\"num-col\">{escape(row['last'])}</td>"
                f"<td class=\"num-col {escape(row['ret_1d_class'])}\">{escape(row['ret_1d'])}</td>"
                f"<td class=\"num-col {escape(row['ret_wtd_class'])}\">{escape(row['ret_wtd'])}</td>"
                f"<td class=\"num-col {escape(row['ret_mtd_class'])}\">{escape(row['ret_mtd'])}</td>"
                f"<td class=\"num-col\">{escape(row['z63'])}</td>"
                "</tr>"
            )
            for row in section["rows"]
        )

        snapshot_blocks.append(
            f"""
        <section class="snapshot-group" id="snapshot-{escape(section_slug)}">
          <div class="section-head">
            <div class="section-label">{escape(section['section'])}</div>
            <a class="jump-link" href="#charts-{escape(section_slug)}">charts</a>
          </div>
          <div class="table-wrap">
            <table>
              <colgroup>
                <col class="asset-col">
                <col class="num-col">
                <col class="num-col">
                <col class="num-col">
                <col class="num-col">
                <col class="num-col">
              </colgroup>
              <thead>
                <tr>
                  <th class="asset-col">Asset</th>
                  <th class="num-col">Last</th>
                  <th class="num-col">1D</th>
                  <th class="num-col">WTD</th>
                  <th class="num-col">MTD</th>
                  <th class="num-col">Z63</th>
                </tr>
              </thead>
              <tbody>
                {row_html}
              </tbody>
            </table>
          </div>
        </section>
        """
        )

    snapshot_html = "\n".join(snapshot_blocks)

    chart_panels_html = "\n".join(
        f"""
        <section class="panel" id="charts-{escape(group['section'].lower().replace(' ', '-'))}">
          <div class="panel-head">
            <div class="panel-title">{escape(group['section'])}</div>
            <a class="jump-link" href="#snapshot-{escape(group['section'].lower().replace(' ', '-'))}">snapshot</a>
          </div>
          <div class="chart-grid">
            {"".join(
                f'''
                <article class="mini-chart-card">
                  <div class="mini-chart-head">
                    <div class="mini-chart-title">{escape(chart["title"])}</div>
                    <div class="mini-chart-subtitle">{escape(chart["subtitle"])}</div>
                  </div>
                  <div id="{escape(chart["id"])}" class="mini-chart"></div>
                </article>
                '''
                for chart in group["charts"]
            )}
          </div>
        </section>
        """
        for group in asset_groups
    )

    regime_blocks = []
    for title, detail in [
        ("Risk Detail", risk_detail),
        ("Liquidity Detail", liquidity_detail),
    ]:
        cards_html = "".join(
            f'''
                <article class="metric-card">
                  <div class="metric-top">
                    <div>
                      <div class="metric-label">{escape(card["label"])}</div>
                      <div class="metric-value {escape(card["value_class"])}">{escape(card["value"])}</div>
                    </div>
                    <div class="metric-explainer">{escape(card["explanation"])}</div>
                  </div>
                  <div id="{escape(card["id"])}" class="spark-chart"></div>
                </article>
            '''
            for card in detail["cards"]
        )

        regime_blocks.append(
            f"""
        <section class="panel regime-panel">
          <div class="regime-head">
            <div class="panel-title">{escape(title)}</div>
            <div class="state-badge {escape(_state_class(detail['state']))}">{escape(detail['state'])}</div>
          </div>
          <div class="regime-grid">
            {cards_html}
          </div>
        </section>
        """
        )

    regime_section_html = "\n".join(regime_blocks)

    all_charts = []
    for group in asset_groups:
        all_charts.extend(group["charts"])
    all_charts.extend(risk_detail["cards"])
    all_charts.extend(liquidity_detail["cards"])

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="refresh" content="900">
  <title>Market Dashboard</title>
  <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
  <style>
    :root {{
      --bg: #000000;
      --panel: #050505;
      --line: #1e1e1e;
      --text: #e8e8e8;
      --muted: #8e8e8e;
      --accent: #f5a623;
      --accent-soft: #3a2a10;
      --up: #7fbf7f;
      --down: #d97a7a;
      --good: #8bbf8b;
      --bad: #d18a8a;
      --neutral: #b0b0b0;
    }}
    * {{
      box-sizing: border-box;
    }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: Menlo, Consolas, Monaco, monospace;
      font-size: 13px;
      line-height: 1.35;
    }}
    .shell {{
      width: min(1500px, calc(100vw - 24px));
      margin: 0 auto;
      padding: 12px 0 32px;
    }}
    .topbar {{
      display: grid;
      grid-template-columns: 2fr 1fr;
      gap: 12px;
      margin-bottom: 12px;
    }}
    .panel {{
      border: 1px solid var(--line);
      background: var(--panel);
    }}
    .status-panel, .meta-panel {{
      padding: 12px;
    }}
    .terminal-title {{
      color: var(--accent);
      margin: 0 0 8px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }}
    .status-strip {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
    }}
    .status-box {{
      border: 1px solid var(--line);
      padding: 10px;
      background: #020202;
    }}
    .status-label, .meta-label, .metric-label, .section-label, .panel-title, th {{
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.08em;
      font-size: 11px;
    }}
    .status-value {{
      margin-top: 4px;
      color: var(--accent);
      font-size: 18px;
      font-weight: 700;
    }}
    .status-value.state-good, .state-badge.state-good {{
      color: var(--good);
      border-color: #213421;
      background: #071007;
    }}
    .status-value.state-bad, .state-badge.state-bad {{
      color: var(--bad);
      border-color: #362020;
      background: #100707;
    }}
    .status-value.state-neutral, .state-badge.state-neutral {{
      color: var(--neutral);
      border-color: #2a2a2a;
      background: #090909;
    }}
    .meta-grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
    }}
    .meta-item {{
      border: 1px solid var(--line);
      padding: 10px;
      background: #020202;
    }}
    .meta-value {{
      margin-top: 4px;
      color: var(--text);
      font-size: 14px;
    }}
    .date-select {{
      width: 100%;
      background: #000000;
      color: var(--text);
      border: 1px solid var(--line);
      font: inherit;
      padding: 6px 8px;
      outline: none;
    }}
    .content {{
      display: grid;
      gap: 12px;
    }}
    .panel-title {{
      padding: 10px 12px 0;
    }}
    .panel-head, .section-head {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
    }}
    .jump-link {{
      color: var(--accent);
      text-decoration: none;
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      padding: 2px 0;
    }}
    .jump-link:hover {{
      color: #ffd08a;
    }}
    .snapshot-layout {{
      padding: 0 12px 12px;
      display: grid;
      gap: 10px;
    }}
    .snapshot-group {{
      border: 1px solid var(--line);
      background: #020202;
    }}
    .section-label {{
      padding: 8px 10px 0;
    }}
    .table-wrap {{
      overflow-x: auto;
      padding: 4px 10px 10px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      table-layout: fixed;
    }}
    th, td {{
      padding: 6px 8px;
      border-bottom: 1px solid #111111;
      white-space: nowrap;
      text-align: right;
      overflow: hidden;
      text-overflow: ellipsis;
    }}
    th:first-child, td:first-child {{
      text-align: left;
    }}
    th.asset-col, td.asset-col {{
      width: 22%;
    }}
    th.num-col, td.num-col {{
      width: 15.6%;
    }}
    .up {{
      color: var(--up);
    }}
    .down {{
      color: var(--down);
    }}
    .neutral {{
      color: var(--neutral);
    }}
    .regime-head {{
      padding: 10px 12px 0;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
    }}
    .state-badge {{
      border: 1px solid var(--accent-soft);
      color: var(--accent);
      padding: 4px 8px;
      font-size: 12px;
    }}
    .regime-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 10px;
      padding: 10px 12px 12px;
    }}
    .metric-card {{
      border: 1px solid var(--line);
      background: #020202;
      padding: 10px;
    }}
    .metric-top {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 10px;
      align-items: start;
    }}
    .metric-value {{
      color: var(--accent);
      font-size: 18px;
      margin-top: 2px;
    }}
    .metric-explainer {{
      color: var(--muted);
      font-size: 11px;
      text-align: right;
      max-width: 180px;
    }}
    .spark-chart {{
      height: 90px;
      margin-top: 6px;
    }}
    .chart-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 10px;
      padding: 10px 12px 12px;
    }}
    .mini-chart-card {{
      border: 1px solid var(--line);
      background: #020202;
      padding: 8px;
    }}
    .mini-chart-head {{
      display: flex;
      align-items: baseline;
      justify-content: space-between;
      gap: 8px;
      margin-bottom: 4px;
    }}
    .mini-chart-title {{
      color: var(--text);
      font-size: 13px;
    }}
    .mini-chart-subtitle {{
      color: var(--muted);
      font-size: 10px;
    }}
    .mini-chart {{
      aspect-ratio: 1 / 1;
      min-height: 220px;
    }}
    @media (max-width: 900px) {{
      .topbar {{
        grid-template-columns: 1fr;
      }}
      .status-strip, .meta-grid {{
        grid-template-columns: 1fr;
      }}
      .metric-top {{
        grid-template-columns: 1fr;
      }}
      .metric-explainer {{
        text-align: left;
        max-width: none;
      }}
    }}
  </style>
</head>
<body>
  <main class="shell">
    <section class="topbar">
      <div class="panel status-panel">
        <div class="terminal-title">Market State</div>
        <div class="status-strip">
          <div class="status-box">
            <div class="status-label">Risk</div>
            <div id="risk-state" class="status-value {escape(_state_class(last.get('risk_regime', '-')))}">{escape(str(last.get("risk_regime", "-")))}</div>
          </div>
          <div class="status-box">
            <div class="status-label">Liquidity</div>
            <div id="liquidity-state" class="status-value {escape(_state_class(last.get('liquidity_regime', '-')))}">{escape(str(last.get("liquidity_regime", "-")))}</div>
          </div>
        </div>
      </div>

      <div class="panel meta-panel">
        <div class="terminal-title">Run Metadata</div>
        <div class="meta-grid">
          <div class="meta-item">
            <div class="meta-label">Snapshot Date</div>
            <div class="meta-value">
              <select id="snapshot-date-select" class="date-select">
                {"".join(f'<option value="{escape(date)}"{(" selected" if date == selected_date else "")}>{escape(date)}</option>' for date in available_dates)}
              </select>
            </div>
          </div>
          <div class="meta-item">
            <div class="meta-label">Data As Of</div>
            <div id="data-as-of" class="meta-value">{escape(data_ts.strftime("%Y-%m-%d"))}</div>
          </div>
          <div class="meta-item">
            <div class="meta-label">Run Time</div>
            <div class="meta-value">{escape(run_ts.strftime("%Y-%m-%d %H:%M:%S %Z"))}</div>
          </div>
          <div class="meta-item">
            <div class="meta-label">Selected vs Run</div>
            <div id="staleness" class="meta-value">{escape(stale_label)}</div>
          </div>
          <div class="meta-item">
            <div class="meta-label">History Window</div>
            <div class="meta-value">126 market days</div>
          </div>
        </div>
      </div>
    </section>

    <section class="content">
      <section class="panel">
        <div class="panel-title">Snapshot View</div>
        <div id="snapshot-layout" class="snapshot-layout">
          {snapshot_html}
        </div>
      </section>

      <div id="regime-sections">
        {regime_section_html}
      </div>

      {chart_panels_html}
    </section>
  </main>

  <script>
    const charts = {json.dumps(all_charts)};
    const snapshotHistory = {json.dumps(history_payload)};
    const selectedDateDefault = {json.dumps(selected_date)};
    const runDate = {json.dumps(run_ts.strftime("%Y-%m-%d"))};
    const config = {{
      responsive: true,
      displaylogo: false,
      modeBarButtonsToRemove: ["lasso2d", "select2d", "autoScale2d"]
    }};

    charts.forEach((chart) => {{
      Plotly.newPlot(chart.id, chart.traces, chart.layout, config);
    }});

    const snapshotLayout = document.getElementById("snapshot-layout");
    const regimeSections = document.getElementById("regime-sections");
    const riskState = document.getElementById("risk-state");
    const liquidityState = document.getElementById("liquidity-state");
    const dataAsOf = document.getElementById("data-as-of");
    const staleness = document.getElementById("staleness");
    const dateSelect = document.getElementById("snapshot-date-select");

    function escapeHtml(value) {{
      return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
    }}

    function describeStaleness(selected, run) {{
      const selectedDateObj = new Date(`${{selected}}T00:00:00`);
      const runDateObj = new Date(`${{run}}T00:00:00`);
      const deltaDays = Math.round((runDateObj - selectedDateObj) / 86400000);

      if (deltaDays <= 0) return "current";
      if (deltaDays === 1) return "1 day old";
      return `${{deltaDays}} days old`;
    }}

    function renderSnapshotSection(section) {{
      const rowHtml = section.rows.map((row) => `
        <tr>
          <td class="asset-col">${{escapeHtml(row.asset)}}</td>
          <td class="num-col">${{escapeHtml(row.last)}}</td>
          <td class="num-col ${{escapeHtml(row.ret_1d_class)}}">${{escapeHtml(row.ret_1d)}}</td>
          <td class="num-col ${{escapeHtml(row.ret_wtd_class)}}">${{escapeHtml(row.ret_wtd)}}</td>
          <td class="num-col ${{escapeHtml(row.ret_mtd_class)}}">${{escapeHtml(row.ret_mtd)}}</td>
          <td class="num-col">${{escapeHtml(row.z63)}}</td>
        </tr>
      `).join("");

      return `
        <section class="snapshot-group" id="snapshot-${{escapeHtml(section.slug)}}">
          <div class="section-head">
            <div class="section-label">${{escapeHtml(section.section)}}</div>
            <a class="jump-link" href="#charts-${{escapeHtml(section.slug)}}">charts</a>
          </div>
          <div class="table-wrap">
            <table>
              <colgroup>
                <col class="asset-col">
                <col class="num-col">
                <col class="num-col">
                <col class="num-col">
                <col class="num-col">
                <col class="num-col">
              </colgroup>
              <thead>
                <tr>
                  <th class="asset-col">Asset</th>
                  <th class="num-col">Last</th>
                  <th class="num-col">1D</th>
                  <th class="num-col">WTD</th>
                  <th class="num-col">MTD</th>
                  <th class="num-col">Z63</th>
                </tr>
              </thead>
              <tbody>${{rowHtml}}</tbody>
            </table>
          </div>
        </section>
      `;
    }}

    function renderRegimePanel(title, detailKey, stateKey, stateClassKey, snapshot) {{
      const cardsHtml = snapshot[detailKey].map((card) => `
        <article class="metric-card">
          <div class="metric-top">
            <div>
              <div class="metric-label">${{escapeHtml(card.label)}}</div>
              <div class="metric-value ${{escapeHtml(card.value_class)}}">${{escapeHtml(card.value)}}</div>
            </div>
            <div class="metric-explainer">${{escapeHtml(card.explanation)}}</div>
          </div>
        </article>
      `).join("");

      return `
        <section class="panel regime-panel">
          <div class="regime-head">
            <div class="panel-title">${{escapeHtml(title)}}</div>
            <div class="state-badge ${{escapeHtml(snapshot[stateClassKey])}}">${{escapeHtml(snapshot[stateKey])}}</div>
          </div>
          <div class="regime-grid">${{cardsHtml}}</div>
        </section>
      `;
    }}

    function renderSnapshot(dateKey) {{
      const snapshot = snapshotHistory[dateKey];
      if (!snapshot) return;

      snapshotLayout.innerHTML = snapshot.sections.map(renderSnapshotSection).join("");
      regimeSections.innerHTML = [
        renderRegimePanel("Risk Detail", "risk_components", "risk_state", "risk_state_class", snapshot),
        renderRegimePanel("Liquidity Detail", "liquidity_components", "liquidity_state", "liquidity_state_class", snapshot)
      ].join("");

      riskState.textContent = snapshot.risk_state;
      riskState.className = `status-value ${{snapshot.risk_state_class}}`;
      liquidityState.textContent = snapshot.liquidity_state;
      liquidityState.className = `status-value ${{snapshot.liquidity_state_class}}`;
      dataAsOf.textContent = dateKey;
      staleness.textContent = describeStaleness(dateKey, runDate);
      updateChartMarkers(dateKey);
    }}

    function updateChartMarkers(dateKey) {{
      charts.forEach((chart) => {{
        if (!chart.id.startsWith("chart-")) return;

        const chartNode = document.getElementById(chart.id);
        if (!chartNode) return;

        const hasDate = chart.traces.some((trace) => Array.isArray(trace.x) && trace.x.includes(dateKey));
        if (!hasDate) {{
          Plotly.relayout(chart.id, {{
            shapes: [],
            annotations: []
          }});
          return;
        }}

        Plotly.relayout(chart.id, {{
          shapes: [
            {{
              type: "line",
              xref: "x",
              yref: "paper",
              x0: dateKey,
              x1: dateKey,
              y0: 0,
              y1: 1,
              line: {{
                color: "#7a7a7a",
                width: 1,
                dash: "dot"
              }}
            }}
          ],
          annotations: [
            {{
              x: dateKey,
              y: 1,
              yref: "paper",
              xref: "x",
              text: "selected",
              showarrow: false,
              yshift: 10,
              font: {{
                color: "#8e8e8e",
                size: 9
              }}
            }}
          ]
        }});
      }});
    }}

    dateSelect.addEventListener("change", (event) => {{
      renderSnapshot(event.target.value);
    }});

    renderSnapshot(selectedDateDefault);
  </script>
</body>
</html>
"""

    output_path.write_text(html, encoding="utf-8")
    print(f"Saved HTML: {output_path}")
