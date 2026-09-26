"""Executive overview: KPIs and charts from analytics.duckdb marts."""

import os
from pathlib import Path

import duckdb
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DUCKDB_PATH = PROJECT_ROOT / "warehouse" / "analytics.duckdb"

INK = "#1C1917"
MUTED = "#78716C"
LINE = "#E7E5E0"
ACCENT = "#C45C3E"
PAPER = "#F7F5F0"
BAR = "#2C2A27"

st.set_page_config(page_title="Overview", page_icon="○", layout="wide")

st.markdown(
    """
    <style>
      @import url("https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,400;6..72,500&family=Source+Sans+3:wght@400;500;600&display=swap");
      html, body, [class*="css"] { font-family: "Source Sans 3", system-ui, sans-serif; }
      .stApp { background: #F7F5F0; }
      header[data-testid="stHeader"] { background: #F7F5F0; }
      .block-container { padding-top: 2.4rem; max-width: 1120px; }
      h1 { font-family: Newsreader, Georgia, serif !important; font-weight: 500 !important;
           letter-spacing: -0.03em; color: #1C1917 !important; }
      .subtitle { color: #78716C; font-size: 0.95rem; margin: -0.6rem 0 1.8rem; }
      .kpi { background: #FFFcf7; border: 1px solid #E7E5E0; border-radius: 16px;
             padding: 1.15rem 1.25rem 1.05rem; height: 100%; }
      .kpi-label { font-size: 0.72rem; letter-spacing: 0.08em; text-transform: uppercase;
                   color: #78716C; font-weight: 500; }
      .kpi-value { font-family: Newsreader, Georgia, serif; font-size: 2.05rem;
                   letter-spacing: -0.03em; color: #1C1917; margin-top: 0.35rem; line-height: 1.1; }
      .chart-title { font-size: 0.92rem; font-weight: 600; color: #1C1917;
                     margin: 1.4rem 0 0.35rem; }
      div[data-testid="stPlotlyChart"] { background: transparent; }
    </style>
    """,
    unsafe_allow_html=True,
)


def _duckdb_path() -> str:
    value = os.getenv("ANALYTICS_DUCKDB_PATH")
    if not value:
        return str(DEFAULT_DUCKDB_PATH)
    path = Path(value)
    return str(path if path.is_absolute() else PROJECT_ROOT / path)


@st.cache_data(show_spinner=False)
def load_monthly():
    con = duckdb.connect(_duckdb_path(), read_only=True)
    frame = con.execute(
        "select * from marts.mart_sales_monthly order by purchase_month"
    ).df()
    con.close()
    return frame


@st.cache_data(show_spinner=False)
def load_category(limit: int = 10):
    con = duckdb.connect(_duckdb_path(), read_only=True)
    frame = con.execute(
        """
        select product_category_name_english, revenue, quantity, order_count
        from marts.mart_sales_category
        order by revenue desc
        limit ?
        """,
        [limit],
    ).df()
    con.close()
    return frame


def format_brl(value: float) -> str:
    if abs(value) >= 1_000_000:
        return f"R$ {value / 1_000_000:,.1f}M"
    if abs(value) >= 1_000:
        return f"R$ {value / 1_000:,.0f}k"
    return f"R$ {value:,.0f}"


def format_int(value: float) -> str:
    return f"{int(value):,}"


def chart_layout(fig: go.Figure, height: int = 340) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=8, r=8, t=28, b=48),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Source Sans 3, system-ui, sans-serif", color=MUTED, size=12),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, bgcolor="rgba(0,0,0,0)"),
        hoverlabel=dict(bgcolor="#FFFcf7", font_size=12, font_color=INK),
    )
    fig.update_xaxes(showgrid=False, linecolor=LINE, tickfont=dict(color=MUTED))
    fig.update_yaxes(showgrid=True, gridcolor=LINE, zeroline=False, tickfont=dict(color=MUTED))
    return fig


monthly = load_monthly()
categories = load_category()

total_revenue = float(monthly["revenue"].sum())
order_count = float(monthly["order_count"].sum())
aov = total_revenue / order_count if order_count else 0

st.title("Overview")
st.markdown("<p class='subtitle'>Olist · executive snapshot from the monthly and category marts</p>", unsafe_allow_html=True)

left, mid, right = st.columns(3)
with left:
    st.markdown(
        f"<div class='kpi'><div class='kpi-label'>Total revenue</div>"
        f"<div class='kpi-value'>{format_brl(total_revenue)}</div></div>",
        unsafe_allow_html=True,
    )
with mid:
    st.markdown(
        f"<div class='kpi'><div class='kpi-label'>Order count</div>"
        f"<div class='kpi-value'>{format_int(order_count)}</div></div>",
        unsafe_allow_html=True,
    )
with right:
    st.markdown(
        f"<div class='kpi'><div class='kpi-label'>AOV</div>"
        f"<div class='kpi-value'>{format_brl(aov)}</div></div>",
        unsafe_allow_html=True,
    )

st.write("")

months = monthly["purchase_month"].dt.strftime("%b %Y")
combo = make_subplots(specs=[[{"secondary_y": True}]])
combo.add_trace(
    go.Bar(x=months, y=monthly["revenue"], name="Revenue", marker_color=BAR, opacity=0.88),
    secondary_y=False,
)
combo.add_trace(
    go.Scatter(
        x=months,
        y=monthly["order_count"],
        name="Orders",
        mode="lines+markers",
        line=dict(color=ACCENT, width=2),
        marker=dict(size=6, color=ACCENT),
    ),
    secondary_y=True,
)
combo.update_yaxes(title_text="Revenue (R$)", secondary_y=False, showgrid=True, gridcolor=LINE)
combo.update_yaxes(title_text="Orders", secondary_y=True, showgrid=False)
chart_layout(combo)

st.markdown("<div class='chart-title'>Revenue and orders by month</div>", unsafe_allow_html=True)
st.plotly_chart(combo, use_container_width=True, config={"displayModeBar": False})

mom = monthly.dropna(subset=["revenue_mom_rate"]).copy()
mom["label"] = mom["purchase_month"].dt.strftime("%b %Y")
mom["pct"] = mom["revenue_mom_rate"] * 100
mom_colors = [ACCENT if v >= 0 else "#8A6A62" for v in mom["pct"]]
growth = go.Figure(
    go.Bar(x=mom["label"], y=mom["pct"], marker_color=mom_colors, name="MoM revenue")
)
growth.update_yaxes(ticksuffix="%", zeroline=True, zerolinecolor=LINE)
chart_layout(growth)
st.markdown("<div class='chart-title'>Month-over-month revenue growth</div>", unsafe_allow_html=True)
st.plotly_chart(growth, use_container_width=True, config={"displayModeBar": False})

cat = categories.copy()
cat["label"] = cat["product_category_name_english"].str.replace("_", " ").str.title()
top = go.Figure(
    go.Bar(x=cat["label"], y=cat["revenue"], marker_color=BAR, name="Revenue")
)
chart_layout(top, height=400)
top.update_xaxes(tickangle=-28, automargin=True)
st.markdown("<div class='chart-title'>Top categories by revenue</div>", unsafe_allow_html=True)
st.plotly_chart(top, use_container_width=True, config={"displayModeBar": False})
