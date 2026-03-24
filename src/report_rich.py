import pandas as pd
from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich.panel import Panel

console = Console()

DISPLAY_MAP = {
    "^GSPC": "SPX",
    "^TNX": "US10Y",
    "^VIX": "VIX",
    "DX-Y.NYB": "DXY",
    "BTC-USD": "BTC",
    "ETH-USD": "ETH",
}

SECTIONS = {
    "MACRO": ["^GSPC", "^TNX", "^VIX"],
    "FX": ["DX-Y.NYB"],
    "CRYPTO": ["BTC-USD", "ETH-USD"],
}


def _fmt_num(x, decimals=2):
    if pd.isna(x):
        return "--"
    return f"{x:.{decimals}f}"


def _fmt_pct(x, decimals=2):
    if pd.isna(x):
        return "--"
    return f"{x * 100:+.{decimals}f}"


def _style_pct(x):
    if pd.isna(x):
        return "dim"
    if x > 0:
        return "green"
    if x < 0:
        return "red"
    return "white"


def _style_z(x):
    if pd.isna(x):
        return "dim"
    if x >= 1:
        return "green"
    if x <= -1:
        return "red"
    return "yellow"


def _style_regime(label):
    label = str(label).lower()
    if "risk-on" in label or "easing" in label:
        return "green"
    if "risk-off" in label or "stress" in label or "tight" in label:
        return "red"
    return "yellow"


def _build_section_table(last: pd.Series, section: str, assets: list[str]) -> Table:
    table = Table(
        title=f"[bold cyan]{section}[/bold cyan]",
        show_header=True,
        header_style="bold white",
        box=None,
        pad_edge=False,
        expand=False,
    )

    table.add_column("ASSET", style="bold white", width=8)
    table.add_column("LAST", justify="right", width=10)
    table.add_column("1D%", justify="right", width=8)
    table.add_column("WTD%", justify="right", width=8)
    table.add_column("MTD%", justify="right", width=8)
    table.add_column("Z63", justify="right", width=8)

    for asset in assets:
        label = DISPLAY_MAP.get(asset, asset)

        last_val = _fmt_num(last.get(asset))
        ret_1d = last.get(f"{asset}_ret_1d")
        ret_wtd = last.get(f"{asset}_ret_wtd")
        ret_mtd = last.get(f"{asset}_ret_mtd")
        z63 = last.get(f"{asset}_z63")

        table.add_row(
            label,
            _fmt_num(last.get(asset)),
            Text(_fmt_pct(ret_1d), style=_style_pct(ret_1d)),
            Text(_fmt_pct(ret_wtd), style=_style_pct(ret_wtd)),
            Text(_fmt_pct(ret_mtd), style=_style_pct(ret_mtd)),
            Text(_fmt_num(z63), style=_style_z(z63)),
        )

    return table


def print_dashboard(df: pd.DataFrame) -> None:
    if df.empty:
        console.print("[bold red]Dashboard error:[/bold red] empty dataframe")
        return

    last = df.iloc[-1]
    ts = df.index[-1]

    risk = str(last.get("risk_regime", "N/A"))
    liq = str(last.get("liquidity_regime", "N/A"))

    header = Text()
    header.append(" MACRO / FX / CRYPTO DASHBOARD ", style="bold black on yellow")
    header.append(f" {ts} ", style="bold white on blue")

    console.print(header)
    console.print(
        Panel.fit(
            f"RISK: [{_style_regime(risk)}]{risk}[/{_style_regime(risk)}]    "
            f"LIQ: [{_style_regime(liq)}]{liq}[/{_style_regime(liq)}]",
            border_style="white",
            padding=(0, 1),
        )
    )

    for section, assets in SECTIONS.items():
        console.print(_build_section_table(last, section, assets))