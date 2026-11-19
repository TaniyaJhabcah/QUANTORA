import html
import io

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns
import streamlit as st

from urbankart_engine import clean_urbankart, calculate_business_results

# -----------------------------------------------------------------------------
# QUANTORA — UrbanKart sales intelligence
# All business metrics are calculated from the uploaded CSV by urbankart_engine.
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="QUANTORA. | Financial Intelligence",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

BG = "#101412"
PANEL = "#171E1A"
PANEL_2 = "#1D2721"
LIME = "#C6F36A"
MIST = "#EAECE5"
MUTED = "#89918A"
AMBER = "#D8A66A"
RED = "#E07870"
GRID = "#29332D"

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&family=Instrument+Serif:ital@0;1&family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');

    :root {
      --q-bg: #101412; --q-panel: #171E1A; --q-panel2: #1D2721;
      --q-lime: #C6F36A; --q-text: #EAECE5; --q-muted: #89918A;
      --q-amber: #D8A66A; --q-red: #E07870; --q-grid: #29332D;
    }
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background: var(--q-bg); color: var(--q-text); }
    [data-testid="stHeader"] { background: rgba(16,20,18,.92); }
    [data-testid="stToolbar"] { right: 1rem; }
    .block-container { max-width: 1500px; padding-top: 1.6rem; padding-bottom: 3rem; }
    section[data-testid="stSidebar"] { background: #0C100E; border-right: 1px solid #29332D; }
    section[data-testid="stSidebar"] > div { padding-top: 1.2rem; }
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color: var(--q-muted); }
    section[data-testid="stSidebar"] [data-testid="stRadio"] label { padding: .58rem .72rem; border-radius: 5px; }
    section[data-testid="stSidebar"] [data-testid="stRadio"] label:hover { background: #1D2721; }
    section[data-testid="stSidebar"] [data-testid="stRadio"] label p { color: #D5DAD2; font-size: .86rem; }
    section[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] { gap: .22rem; }
    section[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) { background: #283421; border-left: 3px solid var(--q-lime); }
    h1, h2, h3 { font-family: 'Space Grotesk', sans-serif !important; color: var(--q-text); letter-spacing: -.035em; }
    h1 { font-size: clamp(2rem, 3vw, 3.2rem) !important; line-height: 1.04 !important; }
    h2 { font-size: 1.55rem !important; }
    h3 { font-size: 1.08rem !important; }
    p, label, li { color: #C4CBC2; }
    [data-testid="stMetric"] { background: transparent; }
    [data-testid="stFileUploader"] { background: #171E1A; border: 1px dashed #58664E; border-radius: 8px; padding: .65rem; }
    [data-testid="stFileUploader"] section { background: transparent; }
    [data-testid="stFileUploader"] small { color: #89918A !important; }
    [data-testid="stDataFrame"] { border: 1px solid #29332D; border-radius: 7px; overflow: hidden; }
    [data-testid="stExpander"] { border: 1px solid #29332D; border-radius: 7px; background: #141A16; }
    .stButton button { background: var(--q-lime); color: #101412; border: 0; border-radius: 4px; font-weight: 700; }
    .stButton button:hover { background: #D6FF82; color: #101412; border: 0; }
    .q-wordmark { font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 1.2rem; letter-spacing: .13em; color: #EAECE5; }
    .q-wordmark span { color: var(--q-lime); }
    .q-tagline { font-family: 'Instrument Serif', serif; font-style: italic; font-size: 1.08rem; color: #AEB8AC; margin-top: -.15rem; }
    .q-eyebrow { font: 600 .66rem 'IBM Plex Mono', monospace; letter-spacing: .16em; color: var(--q-lime); text-transform: uppercase; margin-bottom: .55rem; }
    .q-page-title { font: 600 clamp(2rem, 3vw, 3.05rem)/1.02 'Space Grotesk', sans-serif; letter-spacing: -.055em; color: #EAECE5; margin: 0 0 .55rem 0; }
    .q-subtitle { color: #89918A; font-size: .91rem; max-width: 780px; margin-bottom: 1.25rem; }
    .q-rule { height: 1px; background: linear-gradient(90deg, #C6F36A 0, #29332D 30%, #29332D 100%); margin: 1rem 0 1.35rem; }
    .q-card { background: linear-gradient(145deg, #1A221D, #141A16); border: 1px solid #2B362E; border-radius: 7px; padding: 1rem 1.05rem; min-height: 112px; position: relative; overflow: hidden; }
    .q-card:before { content: ''; position: absolute; top: 0; left: 0; width: 28px; height: 2px; background: var(--q-lime); }
    .q-card-label { color: #89918A; font: 600 .64rem 'IBM Plex Mono', monospace; letter-spacing: .11em; text-transform: uppercase; margin-bottom: .72rem; }
    .q-card-value { color: #EAECE5; font: 600 clamp(1.1rem, 1.7vw, 1.65rem) 'IBM Plex Mono', monospace; letter-spacing: -.055em; white-space: nowrap; }
    .q-card-foot { color: #89918A; font-size: .72rem; margin-top: .45rem; }
    .q-positive { color: #C6F36A !important; }
    .q-negative { color: #E07870 !important; }
    .q-insight { background: #202B23; border: 1px solid #3C4B36; border-left: 3px solid var(--q-lime); padding: .85rem 1rem; border-radius: 4px; }
    .q-insight-title { color: var(--q-lime); font: 600 .66rem 'IBM Plex Mono', monospace; text-transform: uppercase; letter-spacing: .12em; }
    .q-insight-text { color: #EAECE5; font-size: .9rem; margin-top: .3rem; }
    .q-section-label { color: #AAB4A8; font: 600 .67rem 'IBM Plex Mono', monospace; letter-spacing: .14em; text-transform: uppercase; margin: .5rem 0 .7rem; }
    .q-upload { background: radial-gradient(ellipse at 85% 10%, #283722 0, transparent 38%), #171E1A; border: 1px solid #344332; border-radius: 8px; padding: 1.35rem; }
    .q-status { display: inline-block; padding: .28rem .55rem; border: 1px solid #566B3B; border-radius: 3px; color: var(--q-lime); background: #202B23; font: 600 .63rem 'IBM Plex Mono', monospace; letter-spacing: .08em; }
    .q-empty-mark { color: var(--q-lime); font: 2.2rem 'IBM Plex Mono', monospace; }
    .q-footer { color: #647067; font: .65rem 'IBM Plex Mono', monospace; letter-spacing: .08em; border-top: 1px solid #29332D; padding-top: 1rem; margin-top: 2.5rem; }
    div[data-testid="stPlotlyChart"] { border: 1px solid #29332D; border-radius: 7px; overflow: hidden; background: #141A16; }
    @media (max-width: 900px) {
      .block-container { padding-left: 1rem; padding-right: 1rem; }
      .q-card { min-height: 100px; padding: .8rem; }
      .q-card-value { font-size: 1rem; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Plotly visual system
def style_fig(fig, height=360):
    fig.update_layout(
        template="plotly_dark", height=height, paper_bgcolor="#141A16", plot_bgcolor="#141A16",
        font=dict(family="Inter", color="#C4CBC2", size=11),
        margin=dict(l=18, r=18, t=48, b=28),
        title=dict(font=dict(family="Space Grotesk", size=15, color="#EAECE5"), x=0.02),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#AEB8AC")),
        hoverlabel=dict(bgcolor="#202B23", bordercolor="#C6F36A", font=dict(family="IBM Plex Mono", color="#EAECE5")),
    )
    fig.update_xaxes(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID, tickfont=dict(color=MUTED))
    fig.update_yaxes(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID, tickfont=dict(color=MUTED))
    return fig


def money(v):
    if v is None or pd.isna(v):
        return "N/A"
    return f"₹{v:,.2f}"


def pct(v):
    if v is None or pd.isna(v):
        return "N/A"
    return f"{v:,.2f}%"


def card(label, value, foot="", tone=""):
    tone_class = f" {tone}" if tone else ""
    return f'''<div class="q-card"><div class="q-card-label">{html.escape(str(label))}</div><div class="q-card-value{tone_class}">{html.escape(str(value))}</div><div class="q-card-foot">{html.escape(str(foot))}</div></div>'''


def page_header(section, title, subtitle):
    st.markdown(f'<div class="q-eyebrow">QUANTORA / {html.escape(section)}</div><div class="q-page-title">{html.escape(title)}</div><div class="q-subtitle">{html.escape(subtitle)}</div><div class="q-rule"></div>', unsafe_allow_html=True)


def cards_row(items):
    cols = st.columns(len(items), gap="small")
    for col, item in zip(cols, items):
        with col:
            st.markdown(card(*item), unsafe_allow_html=True)

# Sidebar brand and navigation
with st.sidebar:
    st.markdown('<div class="q-wordmark">QUANTORA<span>.</span></div><div class="q-tagline">Financial intelligence. Engineered for clarity.</div>', unsafe_allow_html=True)
    st.markdown('<div style="height:1px;background:#29332D;margin:1.25rem 0 1rem"></div>', unsafe_allow_html=True)
    st.markdown('<div class="q-eyebrow">WORKSPACE</div>', unsafe_allow_html=True)
    page = st.radio(
        "Navigation",
        ["Command Centre", "Data Integrity", "Revenue Intelligence", "Geospatial Intelligence", "Discount Intelligence"],
        label_visibility="collapsed",
    )
    st.markdown('<div style="height:1px;background:#29332D;margin:1.1rem 0"></div>', unsafe_allow_html=True)
    st.markdown('<div class="q-eyebrow">DATA SOURCE</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Import UrbanKart CSV", type=["csv"], label_visibility="collapsed")
    st.caption("CSV only · Original file remains unchanged")
    st.markdown('<div style="height:1px;background:#29332D;margin:1rem 0"></div>', unsafe_allow_html=True)
    st.markdown('<span class="q-status">● SYSTEM READY</span>', unsafe_allow_html=True)
    st.markdown('<div class="q-footer">ANALYTICS ENGINE / V1.0<br>LOCAL SESSION · NO FILE EXPORT</div>', unsafe_allow_html=True)

# Landing state — upload first; no fake/sample figures are shown.
if uploaded_file is None:
    page_header("COMMAND CENTRE", "Clarity begins with clean data.", "A precision analytics workspace for UrbanKart sales performance. Import your sales ledger to generate five live business intelligence views.")
    left, right = st.columns([1.45, 1], gap="large")
    with left:
        st.markdown('<div class="q-upload"><div class="q-eyebrow">01 / CONNECT YOUR DATA</div><h2 style="margin:.2rem 0 .45rem">Bring your sales ledger into focus.</h2><p style="color:#AAB4A8;font-size:.9rem">Upload the judge-provided CSV. QUANTORA will validate order identifiers, normalize dates and financial fields, remove invalid records and calculate the required business metrics.</p><div style="margin-top:1rem;color:#C6F36A;font:600 .68rem IBM Plex Mono">SUPPORTED FORMAT &nbsp; / &nbsp; CSV</div></div>', unsafe_allow_html=True)
        st.markdown("### Upload dataset")
        st.info("Use the **Import UrbanKart CSV** uploader in the left navigation rail to begin.")
    with right:
        st.markdown('<div class="q-eyebrow">02 / ANALYTICS MODULES</div>', unsafe_allow_html=True)
        modules = [
            ("01", "Command Centre", "Five headline financial KPIs and revenue overview"),
            ("02", "Data Integrity", "Cleaning audit, missing values and quality diagnostics"),
            ("03", "Revenue Intelligence", "Monthly revenue trajectory and performance extremes"),
            ("04", "Geospatial Intelligence", "City rankings and regional revenue contribution"),
            ("05", "Discount Intelligence", "Profit margin sensitivity across discount bands"),
        ]
        for n, title, desc in modules:
            st.markdown(f'<div style="display:flex;gap:.85rem;padding:.72rem 0;border-bottom:1px solid #29332D"><div style="font:600 .75rem IBM Plex Mono;color:#C6F36A">{n}</div><div><div style="font:600 .9rem Space Grotesk;color:#EAECE5">{title}</div><div style="font-size:.75rem;color:#89918A">{desc}</div></div></div>', unsafe_allow_html=True)
    st.markdown('<div class="q-footer">QUANTORA. &nbsp; / &nbsp; FINANCIAL INTELLIGENCE. ENGINEERED FOR CLARITY.</div>', unsafe_allow_html=True)
    st.stop()

# Read and process the uploaded file dynamically.
try:
    raw_df = pd.read_csv(uploaded_file, dtype=object)
    with st.spinner("Validating ledger · standardising fields · computing intelligence..."):
        clean_df, quality = clean_urbankart(raw_df)
        results = calculate_business_results(clean_df)
except Exception as exc:
    page_header("DATA CONNECTION", "We couldn't read this ledger.", "Check the file format and required UrbanKart columns, then upload the CSV again.")
    st.error(f"Processing error: {exc}")
    st.stop()

active_count = results["number_of_orders"]
st.markdown(f'<div style="display:flex;justify-content:space-between;align-items:center;gap:1rem;flex-wrap:wrap;margin-bottom:.65rem"><span class="q-status">● DATASET PROCESSED</span><span style="font: .68rem IBM Plex Mono;color:#89918A">{active_count:,} ACTIVE ORDERS &nbsp; / &nbsp; {quality["clean_rows"]:,} CLEAN ROWS</span></div>', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 01 — COMMAND CENTRE / Q2
# -----------------------------------------------------------------------------
if page == "Command Centre":
    page_header("01 / COMMAND CENTRE", "Precision, without compromise.", "A live executive view of net sales performance, profitability and order activity across the cleaned UrbanKart ledger.")
    cards_row([
        ("NET REVENUE", money(results["net_revenue"]), "After discounts · cancelled orders excluded", "q-positive"),
        ("TOTAL PROFIT", money(results["total_profit"]), "Known profit values · active orders", "q-positive" if pd.notna(results["total_profit"]) and results["total_profit"] >= 0 else "q-negative"),
        ("ORDER COUNT", f'{results["number_of_orders"]:,}', "Unique valid active orders", ""),
        ("AVERAGE ORDER VALUE", money(results["average_order_value"]), "Net revenue / active orders", ""),
        ("PROFIT MARGIN", pct(results["profit_margin_pct"]), "Known profit / corresponding net sales", "q-positive" if pd.notna(results["profit_margin_pct"]) and results["profit_margin_pct"] >= 0 else "q-negative"),
    ])
    st.markdown('<div class="q-section-label">REVENUE PERFORMANCE / MONTHLY TRAJECTORY</div>', unsafe_allow_html=True)
    monthly_df = pd.DataFrame(results["monthly_trend"])
    if not monthly_df.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=monthly_df["month"], y=monthly_df["net_revenue"], mode="lines", line=dict(color=LIME, width=2.5, shape="spline"), fill="tozeroy", fillcolor="rgba(198,243,106,.08)", hovertemplate="%{x}<br><b>₹%{y:,.2f}</b><extra></extra>"))
        fig.add_trace(go.Scatter(x=monthly_df["month"], y=monthly_df["net_revenue"], mode="markers", marker=dict(color=LIME, size=6, line=dict(color="#101412", width=1)), showlegend=False, hoverinfo="skip"))
        fig = style_fig(fig, 350)
        fig.update_layout(yaxis_tickprefix="₹", yaxis_tickformat="~s", showlegend=False)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        a, b = st.columns(2)
        with a:
            st.markdown(f'<div class="q-insight"><div class="q-insight-title">▲ BEST PERFORMING MONTH</div><div class="q-insight-text">{html.escape(results["best_month"])}</div></div>', unsafe_allow_html=True)
        with b:
            st.markdown(f'<div class="q-insight" style="border-left-color:#D8A66A"><div class="q-insight-title" style="color:#D8A66A">▼ LOWEST PERFORMING MONTH</div><div class="q-insight-text">{html.escape(results["worst_month"])}</div></div>', unsafe_allow_html=True)
    st.markdown('<div class="q-footer">Q2 / HEADLINE KPIs &nbsp; · &nbsp; Q3 / MONTHLY REVENUE TREND</div>', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 02 — DATA INTEGRITY / Q1
# -----------------------------------------------------------------------------
elif page == "Data Integrity":
    page_header("02 / DATA INTEGRITY", "Trust the numbers. Verify the ledger.", "A transparent cleaning audit showing how the uploaded source was validated before business metrics were calculated.")
    cards_row([
        ("RAW ROWS", f'{quality["raw_rows"]:,}', "Records received from source"),
        ("JUNK REMOVED", f'{quality["junk_rows_removed"]:,}', "Invalid order identifiers" , "q-negative"),
        ("DUPLICATES REMOVED", f'{quality["duplicate_orders_removed"]:,}', "Repeated order IDs · first retained", "q-negative"),
        ("INVALID ROWS", f'{quality["invalid_rows_removed"]:,}', "Invalid date, quantity or unit price", "q-negative"),
        ("CLEAN ROWS", f'{quality["clean_rows"]:,}', "Rows retained after validation", "q-positive"),
    ])
    st.markdown('<div class="q-section-label">SOURCE DIAGNOSTICS / MISSING VALUES BEFORE CLEANING</div>', unsafe_allow_html=True)
    missing_df = pd.DataFrame({"Column": list(quality["missing_before"].keys()), "Missing values": list(quality["missing_before"].values())})
    m1, m2 = st.columns([1, 1.35], gap="large")
    with m1:
        show_missing = missing_df.sort_values("Missing values", ascending=False)
        fig = px.bar(show_missing.head(12).sort_values("Missing values"), x="Missing values", y="Column", orientation="h", text="Missing values", color="Missing values", color_continuous_scale=[[0, "#52634A"], [1, LIME]])
        fig = style_fig(fig, 390)
        fig.update_layout(coloraxis_showscale=False, yaxis_title="", xaxis_title="Missing cells")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    with m2:
        st.markdown("#### Missing-value register")
        st.dataframe(show_missing.rename(columns={"Column": "Source column", "Missing values": "Missing cells"}), use_container_width=True, hide_index=True, height=390)
    with st.expander("Inspect missingness pattern · Seaborn heatmap", expanded=False):
        sample = raw_df.head(min(250, len(raw_df))).copy()
        heatmap_data = sample.applymap(lambda x: pd.isna(x) or str(x).strip().lower() in {"", "nan", "none", "null", "na", "n/a"})
        fig, ax = plt.subplots(figsize=(15, 5), facecolor="#141A16")
        ax.set_facecolor("#141A16")
        sns.heatmap(heatmap_data, cbar=False, yticklabels=False, cmap=sns.color_palette(["#27332B", "#C6F36A"], as_cmap=True), ax=ax)
        ax.set_xlabel("Original source columns", color="#89918A")
        ax.set_ylabel("Sample rows", color="#89918A")
        ax.tick_params(colors="#89918A", labelrotation=65)
        for spine in ax.spines.values(): spine.set_visible(False)
        fig.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
    st.markdown('<div class="q-footer">Q1 / DATA QUALITY REPORT &nbsp; · &nbsp; SOURCE MISSINGNESS IS MEASURED BEFORE CLEANING</div>', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 03 — REVENUE INTELLIGENCE / Q3
# -----------------------------------------------------------------------------
elif page == "Revenue Intelligence":
    page_header("03 / REVENUE INTELLIGENCE", "Follow the revenue trajectory.", "Monthly net sales performance, ranked from the cleaned ledger. Net sales are recomputed from quantity, unit price and discount.")
    cards_row([
        ("NET REVENUE", money(results["net_revenue"]), "Cancelled orders excluded", "q-positive"),
        ("TOTAL PROFIT", money(results["total_profit"]), "Known profit values", "q-positive" if pd.notna(results["total_profit"]) and results["total_profit"] >= 0 else "q-negative"),
        ("BEST MONTH", results["best_month"], "Highest monthly net revenue", "q-positive"),
        ("WORST MONTH", results["worst_month"], "Lowest monthly net revenue", ""),
    ])
    st.markdown('<div class="q-section-label">MONTHLY NET REVENUE / INTERACTIVE SERIES</div>', unsafe_allow_html=True)
    monthly_df = pd.DataFrame(results["monthly_trend"])
    if not monthly_df.empty:
        view = st.radio("Chart view", ["Trend line", "Monthly columns"], horizontal=True, label_visibility="collapsed")
        if view == "Trend line":
            fig = px.line(monthly_df, x="month", y="net_revenue", markers=True)
            fig.update_traces(line=dict(color=LIME, width=3, shape="spline"), marker=dict(size=7, color=LIME), fill="tozeroy", fillcolor="rgba(198,243,106,.07)", hovertemplate="%{x}<br><b>₹%{y:,.2f}</b><extra></extra>")
        else:
            fig = px.bar(monthly_df, x="month", y="net_revenue", text_auto=".2s")
            fig.update_traces(marker_color=LIME, hovertemplate="%{x}<br><b>₹%{y:,.2f}</b><extra></extra>")
        fig = style_fig(fig, 450)
        fig.update_layout(yaxis_tickprefix="₹", yaxis_tickformat="~s", xaxis_title="Month", yaxis_title="Net revenue")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(monthly_df.rename(columns={"month": "Month", "net_revenue": "Net revenue (₹)"}), use_container_width=True, hide_index=True)
    else:
        st.warning("No valid monthly revenue data was found.")
    st.markdown('<div class="q-footer">Q3 / MONTHLY REVENUE TREND &nbsp; · &nbsp; MONTHS ARE ORDERED CHRONOLOGICALLY</div>', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 04 — GEOSPATIAL INTELLIGENCE / Q4
# -----------------------------------------------------------------------------
elif page == "Geospatial Intelligence":
    page_header("04 / GEOSPATIAL INTELLIGENCE", "Where revenue finds its centre.", "Compare the highest-performing cities and understand how net revenue is distributed across the four operating regions.")
    st.markdown(f'<div class="q-insight"><div class="q-insight-title">TOP REVENUE REGION</div><div class="q-insight-text" style="font:600 1.3rem IBM Plex Mono">{html.escape(results["top_region"])}</div></div>', unsafe_allow_html=True)
    city_df = pd.DataFrame(results["top_5_cities"])
    region_df = pd.DataFrame(results["region_shares"])
    c1, c2 = st.columns([1.15, 1], gap="large")
    with c1:
        st.markdown('<div class="q-section-label">CITY RANKING / TOP FIVE BY NET REVENUE</div>', unsafe_allow_html=True)
        if not city_df.empty:
            chart_city = city_df.sort_values("net_revenue", ascending=True)
            fig = px.bar(chart_city, x="net_revenue", y="city", orientation="h", text="net_revenue", color="net_revenue", color_continuous_scale=[[0, "#52634A"], [1, LIME]])
            fig.update_traces(texttemplate="₹%{x:,.0f}", textposition="outside", hovertemplate="%{y}<br><b>₹%{x:,.2f}</b><extra></extra>")
            fig = style_fig(fig, 400)
            fig.update_layout(coloraxis_showscale=False, xaxis_tickprefix="₹", xaxis_tickformat="~s", xaxis_title="Net revenue", yaxis_title="")
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(city_df.rename(columns={"city": "City", "net_revenue": "Net revenue (₹)"}), use_container_width=True, hide_index=True)
        else:
            st.warning("No recognised city values were found.")
    with c2:
        st.markdown('<div class="q-section-label">REGIONAL MIX / SHARE OF TOTAL REVENUE</div>', unsafe_allow_html=True)
        if not region_df.empty:
            fig = go.Figure(go.Pie(labels=region_df["region"], values=region_df["share_pct"], hole=.68, sort=False, marker=dict(colors=[LIME, "#829A63", AMBER, "#65736A"], line=dict(color="#141A16", width=3)), textinfo="label+percent", hovertemplate="%{label}<br><b>%{percent}</b><extra></extra>"))
            fig = style_fig(fig, 360)
            fig.update_layout(showlegend=False, annotations=[dict(text="REGION<br>SHARE", x=.5, y=.5, showarrow=False, font=dict(family="IBM Plex Mono", size=12, color="#AEB8AC"))])
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(region_df.rename(columns={"region": "Region", "net_revenue": "Net revenue (₹)", "share_pct": "Revenue share (%)"}), use_container_width=True, hide_index=True)
        else:
            st.warning("No recognised region values were found.")
    st.markdown('<div class="q-footer">Q4 / GEOGRAPHIC REVENUE DISTRIBUTION &nbsp; · &nbsp; CITY AND REGION VALUES STANDARDISED</div>', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 05 — DISCOUNT INTELLIGENCE / Q5
# -----------------------------------------------------------------------------
elif page == "Discount Intelligence":
    page_header("05 / DISCOUNT INTELLIGENCE", "The margin cost of every concession.", "Measure profit margin across the required discount bands and identify the first band where profitability turns negative.")
    band_df = pd.DataFrame(results["discount_impact"])
    first_negative = results["first_negative_discount_band"]
    if first_negative == "None":
        st.markdown('<div class="q-insight"><div class="q-insight-title">MARGIN SIGNAL</div><div class="q-insight-text">No discount band with a calculable margin is negative.</div></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="q-insight" style="border-left-color:#E07870;background:#281E1C;border-color:#593B35"><div class="q-insight-title" style="color:#E07870">FIRST NEGATIVE-MARGIN BAND</div><div class="q-insight-text" style="font:600 1.35rem IBM Plex Mono;color:#EAECE5">{html.escape(first_negative)}</div></div>', unsafe_allow_html=True)
    st.markdown('<div class="q-section-label">PROFIT MARGIN BY DISCOUNT BAND / ZERO LINE = BREAK-EVEN</div>', unsafe_allow_html=True)
    if not band_df.empty:
        band_df["margin_label"] = band_df["profit_margin_pct"].map(lambda x: pct(x))
        colors = [RED if pd.notna(v) and v < 0 else LIME for v in band_df["profit_margin_pct"]]
        fig = go.Figure(go.Bar(x=band_df["band"], y=band_df["profit_margin_pct"], marker_color=colors, text=band_df["margin_label"], textposition="outside", hovertemplate="Discount: %{x}<br>Profit margin: %{y:.2f}%<extra></extra>"))
        fig.add_hline(y=0, line_dash="dash", line_color=AMBER, line_width=1.5, annotation_text="BREAK-EVEN", annotation_position="top left", annotation_font_color=AMBER)
        fig = style_fig(fig, 430)
        fig.update_layout(xaxis_title="Discount band", yaxis_title="Profit margin", yaxis_ticksuffix="%", showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
        display = band_df[["band", "orders", "profit_margin_pct"]].copy()
        display["profit_margin_pct"] = display["profit_margin_pct"].map(pct)
        st.dataframe(display.rename(columns={"band": "Discount band", "orders": "Orders", "profit_margin_pct": "Profit margin"}), use_container_width=True, hide_index=True)
    st.markdown('<div class="q-footer">Q5 / DISCOUNT PROFITABILITY &nbsp; · &nbsp; MARGIN = KNOWN PROFIT ÷ CORRESPONDING NET SALES</div>', unsafe_allow_html=True)

# Methodology is visible on every page and preserves transparency for the judge.
with st.expander("Calculation methodology & validation rules"):
    st.markdown("""
    - Cancelled orders are excluded from revenue, profit, order count, average order value, overall margin and discount-band calculations.
    - Net sales are recomputed as **Quantity × Unit Price × (1 − Discount)**. The source Sales column is not used.
    - Profit margin uses only rows with a readable Profit value and their corresponding net sales.
    - Duplicate Order IDs are matched without regard to case or whitespace; the first occurrence is retained.
    - Slash and dot dates are interpreted as DD/MM/YYYY. Excel serial dates are supported.
    - The cleaned dataset is held in memory for this session; no cleaned CSV is saved.
    """)

st.markdown('<div class="q-footer">QUANTORA. &nbsp; / &nbsp; FINANCIAL INTELLIGENCE. ENGINEERED FOR CLARITY. &nbsp; / &nbsp; BUILT FOR URBANKART SALES ANALYSIS</div>', unsafe_allow_html=True)
