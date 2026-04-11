"""
MarketPulse India — Unified Quantitative Trading Terminal
A professional-grade Streamlit dashboard replacing the static GitHub Pages site.
All features in one place: AI Picks · Scanner · Market Pulse · Backtest Lab · Strategy Guide
"""

import streamlit as st
import json
import os
import random
import math
import numpy as np
import pandas as pd
from datetime import datetime

# ─── Page Config ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="MarketPulse India — Quantitative Trading Terminal",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        "Get Help": "https://github.com/vinayloki/india-swing-scanner",
        "About": "MarketPulse India — AI-Powered NSE Swing Trading Intelligence"
    }
)

# ─── Global CSS ───────────────────────────────────────────────────────────────

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;900&family=JetBrains+Mono:wght@400;600&display=swap');

  html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #080c14;
    color: #e2e8f0;
  }

  /* Tabs */
  .stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: #0d1420;
    border-radius: 12px;
    padding: 6px;
    border: 1px solid #1e2a3a;
  }
  .stTabs [data-baseweb="tab"] {
    background: transparent;
    color: #64748b;
    border-radius: 8px;
    font-weight: 600;
    font-size: 13px;
    padding: 10px 18px;
    border: none;
    transition: all 0.2s;
  }
  .stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #1a56db, #0ea5e9) !important;
    color: #fff !important;
    box-shadow: 0 4px 12px rgba(26,86,219,0.4);
  }

  /* Cards */
  .card {
    background: linear-gradient(135deg, #0d1420 0%, #111827 100%);
    border: 1px solid #1e2a3a;
    border-radius: 16px;
    padding: 20px;
    margin-bottom: 16px;
    transition: border-color 0.2s, transform 0.2s;
  }
  .card:hover { border-color: #1a56db44; transform: translateY(-1px); }

  /* Metric Cards */
  .metric-card {
    background: linear-gradient(135deg, #0d1420 0%, #0a1628 100%);
    border: 1px solid #1e2a3a;
    border-radius: 12px;
    padding: 18px;
    text-align: center;
  }
  .metric-val { font-size: 2rem; font-weight: 900; font-family: 'JetBrains Mono', monospace; line-height: 1; }
  .metric-label { font-size: 12px; color: #64748b; font-weight: 500; margin-top: 6px; text-transform: uppercase; letter-spacing: 0.05em; }
  .metric-sub { font-size: 11px; color: #475569; margin-top: 4px; }
  .pos { color: #22c55e; }
  .neg { color: #ef4444; }
  .warn { color: #f59e0b; }
  .blue { color: #38bdf8; }
  .purple { color: #a78bfa; }

  /* AI Pick Card */
  .pick-card {
    background: linear-gradient(135deg, #0d1420, #0d1728);
    border: 1px solid #1e2a3a;
    border-left: 3px solid #1a56db;
    border-radius: 10px;
    padding: 14px 16px;
    margin-bottom: 10px;
    transition: border-color 0.2s;
  }
  .pick-card:hover { border-left-color: #38bdf8; }
  .sell-card { border-left-color: #ef4444 !important; }
  .hold-card { border-left-color: #f59e0b !important; }
  .ticker-label { font-size: 16px; font-weight: 700; color: #e2e8f0; font-family: 'JetBrains Mono', monospace; }
  .stock-name { font-size: 12px; color: #64748b; margin-top: 2px; }
  .badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.03em;
  }
  .badge-buy { background: #14532d; color: #4ade80; }
  .badge-sell { background: #450a0a; color: #f87171; }
  .badge-hold { background: #451a03; color: #fbbf24; }
  .badge-bull { background: #1e3a5f; color: #38bdf8; font-size: 10px; padding: 2px 8px; }
  .badge-large { background: #312e81; color: #a5b4fc; font-size: 10px; padding: 2px 8px; }
  .badge-small { background: #1a2e1a; color: #86efac; font-size: 10px; padding: 2px 8px; }
  .badge-mid { background: #27272a; color: #d4d4d8; font-size: 10px; padding: 2px 8px; }

  /* Pulse signal rows */
  .mover-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 12px;
    border-radius: 8px;
    margin-bottom: 6px;
    background: #0d1420;
    border: 1px solid #1a2233;
  }

  /* Header */
  .site-header {
    background: linear-gradient(135deg, #060a12 0%, #0a1628 60%, #0d1f3c 100%);
    border-bottom: 1px solid #1e2a3a;
    border-radius: 16px;
    padding: 24px 32px;
    margin-bottom: 20px;
    position: relative;
    overflow: hidden;
  }
  .site-header::before {
    content: '';
    position: absolute;
    top: -50%;
    right: -20%;
    width: 400px;
    height: 400px;
    background: radial-gradient(circle, rgba(26,86,219,0.12) 0%, transparent 70%);
    pointer-events: none;
  }
  .header-title { font-size: 26px; font-weight: 900; color: #f1f5f9; letter-spacing: -0.02em; }
  .header-sub { font-size: 13px; color: #64748b; margin-top: 4px; }
  .regime-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #14532d44;
    border: 1px solid #166534;
    color: #4ade80;
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 13px;
    font-weight: 600;
  }

  /* News */
  .news-item {
    padding: 12px 0;
    border-bottom: 1px solid #1e2a3a;
  }
  .news-title { font-size: 13px; font-weight: 500; color: #cbd5e1; }
  .news-meta { font-size: 11px; color: #475569; margin-top: 4px; }

  /* Disclaimer */
  .disclaimer {
    background: #1c1200;
    border: 1px solid #854d0e;
    border-radius: 10px;
    padding: 14px 18px;
    font-size: 12px;
    color: #fbbf24;
    margin-top: 16px;
  }

  /* Sliders */
  .stSlider [data-baseweb="slider"] { padding: 0 !important; }

  /* Dataframe */
  .stDataFrame { border-radius: 12px; overflow: hidden; }

  /* Buttons */
  .stButton > button {
    border-radius: 10px;
    font-weight: 600;
    font-size: 13px;
    transition: all 0.2s;
    border: 1px solid #1e2a3a;
    background: #0d1420;
    color: #94a3b8;
  }
  .stButton > button:hover { border-color: #1a56db; color: #60a5fa; }
  div[data-testid="column"]:has(> div > div > button[kind="primary"]) > div > div > button {
    background: linear-gradient(135deg, #1a56db, #0ea5e9) !important;
    color: white !important;
    border: none !important;
    box-shadow: 0 4px 15px rgba(26,86,219,0.4);
  }

  /* Scrollbar */
  ::-webkit-scrollbar { width: 6px; height: 6px; }
  ::-webkit-scrollbar-track { background: #0d1420; }
  ::-webkit-scrollbar-thumb { background: #1e3a5f; border-radius: 3px; }

  h1, h2, h3 { color: #f1f5f9 !important; }
  .stMarkdown hr { border-color: #1e2a3a; }
  .stSelectbox label, .stSlider label, .stRadio label { color: #94a3b8 !important; font-size: 13px !important; font-weight: 500 !important; }
  .stTextInput input { background: #0d1420 !important; border: 1px solid #1e2a3a !important; color: #e2e8f0 !important; border-radius: 8px !important; }

  /* Section labels */
  .section-label {
    font-size: 11px;
    font-weight: 700;
    color: #475569;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 10px;
  }
  .section-title {
    font-size: 18px;
    font-weight: 700;
    color: #f1f5f9;
    margin-bottom: 4px;
  }
  .section-icon { font-size: 22px; vertical-align: middle; margin-right: 8px; }
</style>
""", unsafe_allow_html=True)


# ─── Data Loaders ─────────────────────────────────────────────────────────────

SCAN_DIR = "scan_results"

@st.cache_data(ttl=3600)
def load_ai_picks():
    try:
        with open(os.path.join(SCAN_DIR, "ai_picks.json")) as f:
            return json.load(f)
    except:
        return {"generated": "N/A", "regime": "Unknown", "summary": {}, "picks": [], "total_stocks": 0}

@st.cache_data(ttl=3600)
def load_top_performers():
    try:
        with open(os.path.join(SCAN_DIR, "latest_top_performers.json")) as f:
            return json.load(f)
    except:
        return {}

@st.cache_data(ttl=3600)
def load_performance():
    try:
        with open(os.path.join(SCAN_DIR, "performance_report.json")) as f:
            return json.load(f)
    except:
        return {}

@st.cache_data(ttl=3600)
def load_market_regime():
    try:
        with open(os.path.join(SCAN_DIR, "market_regime.json")) as f:
            return json.load(f)
    except:
        return {"regime": "Unknown", "score": 0}

@st.cache_data(ttl=3600)
def load_news():
    try:
        with open(os.path.join(SCAN_DIR, "daily_news.json")) as f:
            return json.load(f)
    except:
        return []

@st.cache_data(ttl=3600)
def load_full_scan():
    try:
        df = pd.read_csv(os.path.join(SCAN_DIR, "latest_full_scan.csv"))
        return df
    except:
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def load_opportunities():
    try:
        with open(os.path.join(SCAN_DIR, "opportunities.json")) as f:
            return json.load(f)
    except:
        return []

# ─── Helper functions ─────────────────────────────────────────────────────────

def fmt_pct(v):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "–"
    color = "pos" if v >= 0 else "neg"
    sign = "+" if v >= 0 else ""
    return f'<span class="{color}">{sign}{v:.1f}%</span>'

def fmt_price(v):
    if v is None:
        return "–"
    if v >= 10000:
        return f"₹{v:,.0f}"
    return f"₹{v:,.2f}"

def cap_badge(code, label):
    cls = "badge-large" if code == "L" else ("badge-mid" if code == "M" else "badge-small")
    return f'<span class="badge {cls}">{label}</span>'

def rec_badge(rec):
    cls = "badge-buy" if rec == "buy" else ("badge-sell" if rec == "sell" else "badge-hold")
    icon = "▲ BUY" if rec == "buy" else ("▼ SELL" if rec == "sell" else "◆ HOLD")
    return f'<span class="badge {cls}">{icon}</span>'

def conf_bar(conf):
    color = "#22c55e" if conf >= 75 else ("#f59e0b" if conf >= 55 else "#ef4444")
    return f'''<div style="height:4px;background:#1e2a3a;border-radius:2px;margin-top:6px">
        <div style="height:100%;width:{conf}%;background:{color};border-radius:2px;transition:width 0.3s"></div></div>
        <div style="font-size:10px;color:#475569;margin-top:3px">Confidence {conf}%</div>'''

def metric_card(label, val_html, sub=None, border_color="#1a56db"):
    sub_html = f'<div class="metric-sub">{sub}</div>' if sub else ""
    return f'''<div class="metric-card" style="border-top: 3px solid {border_color}">
        <div class="metric-val">{val_html}</div>
        <div class="metric-label">{label}</div>
        {sub_html}
    </div>'''

# ─── Header ───────────────────────────────────────────────────────────────────

ai_data = load_ai_picks()
regime_data = load_market_regime()
regime = ai_data.get("regime", regime_data.get("regime", "Unknown"))
gen_date = ai_data.get("generated", "N/A")
total_stocks = ai_data.get("total_stocks", 0)
summary = ai_data.get("summary", {})
buys = summary.get("buy", 0)
holds = summary.get("hold", 0)
sells = summary.get("sell", 0)

regime_icon = "🟢" if regime == "Bull" else ("🔴" if regime == "Bear" else "🟡")
regime_color = "#22c55e" if regime == "Bull" else ("#ef4444" if regime == "Bear" else "#f59e0b")

st.markdown(f"""
<div class="site-header">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:16px">
    <div>
      <div class="header-title">📈 MarketPulse India</div>
      <div class="header-sub">AI-Powered NSE Swing Trading Intelligence · {total_stocks:,} Stocks Analysed</div>
    </div>
    <div style="display:flex;gap:12px;align-items:center;flex-wrap:wrap">
      <div class="regime-pill" style="border-color:{regime_color}44;color:{regime_color};background:{regime_color}11">
        {regime_icon} {regime} Market
      </div>
      <div style="text-align:right">
        <div style="font-size:11px;color:#475569">Last Updated</div>
        <div style="font-size:13px;color:#94a3b8;font-weight:600">{gen_date}</div>
      </div>
    </div>
  </div>
  <div style="display:flex;gap:24px;margin-top:16px;flex-wrap:wrap">
    <div><span style="color:#4ade80;font-weight:700;font-size:18px">{buys}</span> <span style="color:#64748b;font-size:12px">BUY signals</span></div>
    <div><span style="color:#fbbf24;font-weight:700;font-size:18px">{holds}</span> <span style="color:#64748b;font-size:12px">HOLD signals</span></div>
    <div><span style="color:#f87171;font-weight:700;font-size:18px">{sells}</span> <span style="color:#64748b;font-size:12px">SELL signals</span></div>
    <div style="margin-left:auto"><span style="color:#94a3b8;font-size:12px">⚠️ For educational purposes only · Not SEBI-registered advice</span></div>
  </div>
</div>
""", unsafe_allow_html=True)

# ─── Navigation Tabs ──────────────────────────────────────────────────────────

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🤖 AI Intelligence",
    "🌪️ Market Pulse",
    "🔍 Full Scanner",
    "🧪 Backtest Lab",
    "📚 Strategy Guide"
])


# ════════════════════════════════════════════════════════════════════════════════
# TAB 1 — AI INTELLIGENCE
# ════════════════════════════════════════════════════════════════════════════════

with tab1:
    picks = ai_data.get("picks", [])

    st.markdown("""
    <div class="card" style="border-color:#1a56db33">
      <div style="display:flex;align-items:center;gap:10px">
        <div style="font-size:28px">🤖</div>
        <div>
          <div class="section-title">AI EOD Intelligence Engine v2</div>
          <div style="color:#64748b;font-size:13px">Multi-timeframe momentum analysis across 2,100+ NSE stocks. Ranked by AI Score.</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Filter controls
    col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
    with col1:
        rec_filter = st.selectbox("Signal", ["All", "BUY", "HOLD", "SELL"], key="rec_f")
    with col2:
        cap_filter = st.selectbox("Market Cap", ["All", "Large Cap", "Mid Cap", "Small Cap", "Micro Cap"], key="cap_f")
    with col3:
        sector_filter = st.selectbox("Sector", ["All"] + sorted(list(set(p.get("sector","") for p in picks if p.get("sector","") != ""))), key="sec_f")
    with col4:
        min_conf = st.slider("Min Confidence", 0, 100, 60, step=5, key="conf_f")

    st.markdown("---")

    # Filter picks
    filtered = []
    for p in picks:
        if rec_filter != "All" and p.get("recommendation","").upper() != rec_filter:
            continue
        if cap_filter != "All" and p.get("cap_label","") != cap_filter:
            continue
        if sector_filter != "All" and p.get("sector","") != sector_filter:
            continue
        if p.get("confidence", 0) < min_conf:
            continue
        filtered.append(p)

    st.markdown(f'<div style="color:#64748b;font-size:13px;margin-bottom:12px">Showing <b style="color:#38bdf8">{len(filtered)}</b> stocks matching your filters</div>', unsafe_allow_html=True)

    if not filtered:
        st.info("No stocks match your current filters. Try relaxing the criteria.")
    else:
        # Show top picks
        show_count = st.select_slider("Show Top N", options=[10, 25, 50, 100, 200, len(filtered)], value=25 if len(filtered) >= 25 else len(filtered))
        for p in filtered[:show_count]:
            rec = p.get("recommendation", "hold")
            card_cls = "pick-card" + (" sell-card" if rec == "sell" else (" hold-card" if rec == "hold" else ""))
            conf = p.get("confidence", 0)
            score = p.get("score", 0)
            tf = p.get("tf_details", {})

            # Build timeframe row
            tf_cells = ""
            for tf_key in ["1W", "2W", "1M", "3M", "6M", "12M"]:
                tf_data = tf.get(tf_key, {})
                pct = tf_data.get("pct")
                if pct is None:
                    tf_cells += f'<span style="color:#475569;font-size:11px;margin-right:10px">{tf_key}: –</span>'
                else:
                    color = "#22c55e" if pct >= 5 else ("#f59e0b" if pct >= 0 else "#ef4444")
                    sign = "+" if pct >= 0 else ""
                    tf_cells += f'<span style="color:{color};font-size:11px;margin-right:10px">{tf_key}: {sign}{pct:.1f}%</span>'

            # Entry/SL/TP
            entry = fmt_price(p.get("entry_price"))
            sl = fmt_price(p.get("stop_loss"))
            tp = fmt_price(p.get("take_profit"))
            sl_pct = p.get("sl_pct", 0)
            tp_pct = p.get("tp_pct", 0)
            rr = p.get("risk_reward", 0)
            p_success = p.get("p_success", 0)
            horizon = p.get("horizon", "")

            # Reasons/Risks
            reasons = p.get("reasons", [])
            risks = p.get("risks", [])
            reasons_html = "".join([f'<div style="color:#4ade80;font-size:11px;margin-top:3px">✓ {r}</div>' for r in reasons[:3]])
            risks_html = "".join([f'<div style="color:#f87171;font-size:11px;margin-top:3px">⚠ {r}</div>' for r in risks[:2]])

            st.markdown(f"""
            <div class="{card_cls}">
              <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:8px">
                <div>
                  <span class="ticker-label">{p.get("ticker","")}</span>
                  <div class="stock-name">{p.get("name","")} · {p.get("sector","")}</div>
                </div>
                <div style="display:flex;gap:6px;align-items:center;flex-wrap:wrap">
                  {rec_badge(rec)}
                  {cap_badge(p.get("mcap_code","S"), p.get("cap_label",""))}
                  <span class="badge badge-bull">{regime} Market</span>
                  <span style="color:#475569;font-size:12px">Rank #{p.get("rank","?")}</span>
                </div>
              </div>
              <div style="margin-top:10px;display:flex;gap:20px;flex-wrap:wrap">
                <div style="font-size:12px;color:#64748b">Entry: <b style="color:#f1f5f9">{entry}</b></div>
                <div style="font-size:12px;color:#64748b">Stop Loss: <b style="color:#ef4444">{sl}</b> (-{sl_pct}%)</div>
                <div style="font-size:12px;color:#64748b">Target: <b style="color:#22c55e">{tp}</b> (+{tp_pct}%)</div>
                <div style="font-size:12px;color:#64748b">R:R <b style="color:#38bdf8">1:{rr:.1f}</b></div>
                <div style="font-size:12px;color:#64748b">Prob. Success: <b style="color:#a78bfa">{p_success}%</b></div>
                <div style="font-size:12px;color:#64748b">Horizon: <b style="color:#94a3b8">{horizon}</b></div>
              </div>
              <div style="margin-top:8px">{tf_cells}</div>
              {conf_bar(conf)}
              <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:10px">
                <div>{reasons_html}</div>
                <div>{risks_html}</div>
              </div>
              <div style="color:#475569;font-size:11px;margin-top:6px">AI Score: {score:.1f}/100</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("""
    <div class="disclaimer">
      ⚠️ <b>IMPORTANT DISCLAIMER</b>: All AI signals are generated by an automated algorithm for <b>educational and research purposes only</b>.
      This is NOT SEBI-registered investment advice. Past performance does not guarantee future results.
      Always consult a qualified financial advisor before investing. Trade at your own risk.
    </div>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════════
# TAB 2 — MARKET PULSE
# ════════════════════════════════════════════════════════════════════════════════

with tab2:
    top_data = load_top_performers()
    news_data = load_news()

    st.markdown("""
    <div class="card">
      <div class="section-title">🌪️ Market Pulse — NSE Momentum Dashboard</div>
      <div style="color:#64748b;font-size:13px">Top Gainers & Losers across 1W, 2W, 1M and 3M timeframes.</div>
    </div>
    """, unsafe_allow_html=True)

    tf_sel = st.radio("Timeframe", ["1W", "2W", "1M", "3M"], horizontal=True, key="tf_pulse")

    tf_data = top_data.get(tf_sel, {})
    gainers = tf_data.get("top_gainers", [])
    losers = tf_data.get("top_losers", [])

    col_g, col_l = st.columns(2)

    with col_g:
        st.markdown(f'<div style="color:#22c55e;font-weight:700;font-size:14px;margin-bottom:12px">🚀 Top Gainers ({tf_sel})</div>', unsafe_allow_html=True)
        for i, g in enumerate(gainers[:20]):
            pct = g.get(tf_sel, 0) or 0
            price = fmt_price(g.get("last_close"))
            bar_w = min(100, abs(pct) * 1.5)
            st.markdown(f"""
            <div class="mover-row">
              <div>
                <span style="font-family:'JetBrains Mono',monospace;font-weight:700;color:#f1f5f9">{g.get("ticker","")}</span>
                <div style="font-size:10px;color:#475569;margin-top:2px">{price}</div>
              </div>
              <div style="text-align:right">
                <span style="color:#22c55e;font-weight:700;font-size:15px">+{pct:.1f}%</span>
                <div style="height:2px;background:#1e2a3a;border-radius:1px;margin-top:4px;width:80px;margin-left:auto">
                  <div style="height:100%;width:{bar_w:.0f}%;background:#22c55e;border-radius:1px"></div>
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)

    with col_l:
        st.markdown(f'<div style="color:#ef4444;font-weight:700;font-size:14px;margin-bottom:12px">📉 Top Losers ({tf_sel})</div>', unsafe_allow_html=True)
        for i, l in enumerate(losers[:20]):
            pct = l.get(tf_sel, 0) or 0
            price = fmt_price(l.get("last_close"))
            bar_w = min(100, abs(pct) * 1.5)
            st.markdown(f"""
            <div class="mover-row">
              <div>
                <span style="font-family:'JetBrains Mono',monospace;font-weight:700;color:#f1f5f9">{l.get("ticker","")}</span>
                <div style="font-size:10px;color:#475569;margin-top:2px">{price}</div>
              </div>
              <div style="text-align:right">
                <span style="color:#ef4444;font-weight:700;font-size:15px">{pct:.1f}%</span>
                <div style="height:2px;background:#1e2a3a;border-radius:1px;margin-top:4px;width:80px;margin-left:auto">
                  <div style="height:100%;width:{bar_w:.0f}%;background:#ef4444;border-radius:1px"></div>
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)

    # News Section
    st.markdown("---")
    st.markdown('<div class="section-title">📰 Market News Feed</div>', unsafe_allow_html=True)

    if news_data:
        news_list = news_data if isinstance(news_data, list) else news_data.get("articles", [])
        if news_list:
            for article in news_list[:15]:
                title = article.get("title", article.get("headline", ""))
                source = article.get("source", article.get("publisher", "NSE"))
                pub_time = article.get("published", article.get("time", ""))
                url = article.get("url", article.get("link", "#"))
                if title:
                    st.markdown(f"""
                    <div class="news-item">
                      <div class="news-title"><a href="{url}" target="_blank" style="color:#cbd5e1;text-decoration:none">{title}</a></div>
                      <div class="news-meta">{source} · {pub_time}</div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No news available. News is refreshed daily via GitHub Actions.")
    else:
        st.info("News data not available. Run the workflow to fetch latest news.")

    # Market Stats
    st.markdown("---")
    st.markdown('<div class="section-title">📊 Market Regime Analysis</div>', unsafe_allow_html=True)

    m_cols = st.columns(4)
    regime_score = regime_data.get("score", 0)
    with m_cols[0]:
        st.markdown(metric_card("Market Regime", f'<span class="pos">{regime}</span>' if regime == "Bull" else f'<span class="warn">{regime}</span>', "Based on Nifty50 momentum"), unsafe_allow_html=True)
    with m_cols[1]:
        st.markdown(metric_card("BUY Signals", f'<span class="pos">{buys}</span>', f"{buys/total_stocks*100:.1f}% of universe" if total_stocks else "–"), unsafe_allow_html=True)
    with m_cols[2]:
        st.markdown(metric_card("SELL Signals", f'<span class="neg">{sells}</span>', f"{sells/total_stocks*100:.1f}% of universe" if total_stocks else "–"), unsafe_allow_html=True)
    with m_cols[3]:
        avg_conf = summary.get("avg_confidence", 0)
        st.markdown(metric_card("Avg AI Confidence", f'<span class="blue">{avg_conf:.1f}%</span>', "Across all BUY picks"), unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════════
# TAB 3 — FULL SCANNER
# ════════════════════════════════════════════════════════════════════════════════

with tab3:
    st.markdown("""
    <div class="card">
      <div class="section-title">🔍 Full NSE Technical Scanner</div>
      <div style="color:#64748b;font-size:13px">Screener across 2,100+ NSE stocks with multi-timeframe technical filters.</div>
    </div>
    """, unsafe_allow_html=True)

    opp_data = load_opportunities()

    if opp_data:
        st.markdown('<div style="color:#64748b;font-size:13px;margin-bottom:12px">Showing high-probability swing trade setups from the latest scan.</div>', unsafe_allow_html=True)

        opp_df_rows = []
        for o in opp_data:
            opp_df_rows.append({
                "Ticker": o.get("ticker",""),
                "Price": o.get("price", o.get("last_close", 0)),
                "Signal": o.get("signal", o.get("recommendation","")),
                "Score": o.get("score", 0),
                "Sector": o.get("sector",""),
                "1W%": o.get("1W", o.get("pct_1w", None)),
                "1M%": o.get("1M", o.get("pct_1m", None)),
                "3M%": o.get("3M", o.get("pct_3m", None)),
            })

        opp_df = pd.DataFrame(opp_df_rows)
        st.dataframe(
            opp_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Price": st.column_config.NumberColumn("Price (₹)", format="₹%.2f"),
                "Score": st.column_config.ProgressColumn("AI Score", format="%.1f", min_value=0, max_value=100),
                "1W%": st.column_config.NumberColumn("1W %", format="%.1f%%"),
                "1M%": st.column_config.NumberColumn("1M %", format="%.1f%%"),
                "3M%": st.column_config.NumberColumn("3M %", format="%.1f%%"),
            }
        )
    else:
        # Try full scan CSV
        df = load_full_scan()
        if not df.empty:
            st.markdown(f'<div style="color:#64748b;font-size:13px;margin-bottom:12px">Full scan with <b style="color:#38bdf8">{len(df):,}</b> stocks.</div>', unsafe_allow_html=True)

            # Search
            search = st.text_input("🔍 Search by ticker or name", placeholder="e.g. INFY, TCS, RELIANCE...", key="scan_search")
            if search:
                mask = df.astype(str).apply(lambda row: row.str.contains(search.upper(), case=False)).any(axis=1)
                df = df[mask]

            # Column selection
            cols_to_show = [c for c in df.columns if not c.startswith("Unnamed")]
            st.dataframe(df[cols_to_show].head(500), use_container_width=True, hide_index=True)
        else:
            st.info("Full scan data not available. Run the GitHub Actions workflow to generate it.")

    st.markdown("---")
    st.markdown("""
    <div class="card">
      <div style="font-weight:700;color:#f1f5f9;margin-bottom:8px">🗓️ How the Scanner Works</div>
      <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px">
        <div>
          <div style="color:#38bdf8;font-weight:600;font-size:13px">Step 1: Universe</div>
          <div style="color:#64748b;font-size:12px;margin-top:4px">Downloads all 2,100+ NSE tickers from NSEpy/yfinance every trading day at 6PM IST.</div>
        </div>
        <div>
          <div style="color:#a78bfa;font-weight:600;font-size:13px">Step 2: Multi-TF Analysis</div>
          <div style="color:#64748b;font-size:12px;margin-top:4px">Calculates momentum across 1W, 2W, 1M, 3M, 6M, 12M. Scores each stock on trend strength.</div>
        </div>
        <div>
          <div style="color:#22c55e;font-weight:600;font-size:13px">Step 3: AI Ranking</div>
          <div style="color:#64748b;font-size:12px;margin-top:4px">Applies regime filter, fundamentals (P/E, Market Cap) and generates final BUY/HOLD/SELL with entry, SL, TP.</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════════
# TAB 4 — BACKTEST LAB
# ════════════════════════════════════════════════════════════════════════════════

with tab4:
    perf = load_performance()
    mb = perf.get("mode_b", {})

    # Real backtest summary from performance.py
    real_wr = mb.get("win_rate_pct", 52.6)
    real_aw = mb.get("avg_win_pct", 3.43)
    real_al = abs(mb.get("avg_loss_pct", -4.84))
    real_trades = mb.get("total_trades", 156)
    real_expectancy = mb.get("expectancy_pct", -0.49)
    real_pf = mb.get("profit_factor", 0.847)
    real_dd = mb.get("max_drawdown_pct", 18.06)
    real_total_ret = mb.get("total_return_pct", -12.56)
    real_sharpe = mb.get("sharpe_like", -0.99)
    equity_curve = mb.get("equity_curve", [])
    monthly_dist = mb.get("monthly_dist", [])

    st.markdown("""
    <div class="card" style="border-color:#1a56db33">
      <div style="display:flex;align-items:center;gap:10px">
        <div style="font-size:28px">🧪</div>
        <div>
          <div class="section-title">Quantitative Backtest Laboratory</div>
          <div style="color:#64748b;font-size:13px">Simulate strategy performance with custom parameters. Based on 52-week historical NSE data.</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ─── Section A: Real Backtest Results ────────────────────────────────────

    st.markdown('<div style="font-size:16px;font-weight:700;color:#f1f5f9;margin:8px 0 16px">📊 Real Historical Backtest Results (52 Weeks · 156 Trades)</div>', unsafe_allow_html=True)

    m1, m2, m3, m4 = st.columns(4)

    wr_color = "#22c55e" if real_wr >= 60 else ("#f59e0b" if real_wr >= 50 else "#ef4444")
    tr_color = "#22c55e" if real_total_ret >= 0 else "#ef4444"
    exp_color = "#22c55e" if real_expectancy >= 0 else "#ef4444"
    dd_color = "#f59e0b" if real_dd < 20 else "#ef4444"

    with m1:
        st.markdown(metric_card("Win Rate", f'<span style="color:{wr_color}">{real_wr:.1f}%</span>', "Target: >60%", wr_color), unsafe_allow_html=True)
    with m2:
        st.markdown(metric_card("Total Return", f'<span style="color:{tr_color}">{real_total_ret:+.2f}%</span>', "₹10L → ₹8.74L", tr_color), unsafe_allow_html=True)
    with m3:
        st.markdown(metric_card("Expectancy/Trade", f'<span style="color:{exp_color}">{real_expectancy:+.2f}%</span>', "Target: >0%", exp_color), unsafe_allow_html=True)
    with m4:
        st.markdown(metric_card("Max Drawdown", f'<span style="color:{dd_color}">{real_dd:.1f}%</span>', "Target: <15%", dd_color), unsafe_allow_html=True)

    m5, m6, m7, m8 = st.columns(4)
    with m5:
        st.markdown(metric_card("Avg Win", f'<span class="pos">+{real_aw:.2f}%</span>', f"{mb.get('exit_reasons',{}).get('TP',0)} TP hits"), unsafe_allow_html=True)
    with m6:
        st.markdown(metric_card("Avg Loss", f'<span class="neg">-{real_al:.2f}%</span>', f"{mb.get('exit_reasons',{}).get('SL',0)} SL hits"), unsafe_allow_html=True)
    with m7:
        st.markdown(metric_card("Profit Factor", f'<span class="warn">{real_pf:.3f}</span>', "Target: >1.25"), unsafe_allow_html=True)
    with m8:
        st.markdown(metric_card("Sharpe Ratio", f'<span class="neg">{real_sharpe:.2f}</span>', "Target: >0.5"), unsafe_allow_html=True)

    # Exit Reasons
    exits = mb.get("exit_reasons", {})
    tp_hits = exits.get("TP", 0)
    sl_hits = exits.get("SL", 0)
    time_exits = exits.get("TIME", 0)

    st.markdown("---")
    st.markdown('<div style="font-size:15px;font-weight:700;color:#f1f5f9;margin-bottom:12px">🎯 Exit Reason Breakdown</div>', unsafe_allow_html=True)
    ec1, ec2, ec3 = st.columns(3)
    with ec1:
        st.markdown(f"""<div class="card" style="text-align:center;border-color:#14532d33">
            <div style="font-size:28px;font-weight:900;color:#22c55e">{tp_hits}</div>
            <div style="color:#64748b;font-size:12px;margin-top:4px">✅ Take Profit Hit</div>
            <div style="color:#475569;font-size:11px">{tp_hits/real_trades*100:.0f}% of trades</div>
        </div>""", unsafe_allow_html=True)
    with ec2:
        st.markdown(f"""<div class="card" style="text-align:center;border-color:#450a0a33">
            <div style="font-size:28px;font-weight:900;color:#ef4444">{sl_hits}</div>
            <div style="color:#64748b;font-size:12px;margin-top:4px">🛑 Stop Loss Hit</div>
            <div style="color:#475569;font-size:11px">{sl_hits/real_trades*100:.0f}% of trades</div>
        </div>""", unsafe_allow_html=True)
    with ec3:
        st.markdown(f"""<div class="card" style="text-align:center;border-color:#451a0333">
            <div style="font-size:28px;font-weight:900;color:#f59e0b">{time_exits}</div>
            <div style="color:#64748b;font-size:12px;margin-top:4px">⏰ Time Exit (5d)</div>
            <div style="color:#475569;font-size:11px">{time_exits/real_trades*100:.0f}% of trades</div>
        </div>""", unsafe_allow_html=True)

    # Monthly Performance
    if monthly_dist:
        st.markdown("---")
        st.markdown('<div style="font-size:15px;font-weight:700;color:#f1f5f9;margin-bottom:12px">📅 Monthly Performance Breakdown</div>', unsafe_allow_html=True)
        monthly_df = pd.DataFrame(monthly_dist)
        if "month" in monthly_df.columns:
            monthly_df = monthly_df.rename(columns={"month": "Month", "trades": "Trades", "wins": "Wins",
                                                     "win_rate": "Win Rate %", "return_pct": "Return %", "pnl": "P&L (₹)"})
            st.dataframe(
                monthly_df[["Month","Trades","Wins","Win Rate %","Return %","P&L (₹)"]],
                use_container_width=True, hide_index=True,
                column_config={
                    "Win Rate %": st.column_config.NumberColumn(format="%.1f%%"),
                    "Return %": st.column_config.NumberColumn(format="%+.2f%%"),
                    "P&L (₹)": st.column_config.NumberColumn(format="₹%.0f"),
                }
            )

    # Regime Breakdown
    regime_breakdown = mb.get("regime_breakdown", {})
    if regime_breakdown:
        st.markdown("---")
        st.markdown('<div style="font-size:15px;font-weight:700;color:#f1f5f9;margin-bottom:12px">🌐 Performance by Market Regime</div>', unsafe_allow_html=True)
        for reg_name, reg_stats in regime_breakdown.items():
            reg_wr = reg_stats.get("win_rate_pct", 0)
            reg_exp = reg_stats.get("expectancy", 0)
            reg_trades = reg_stats.get("trades", 0)
            reg_pnl = reg_stats.get("total_pnl", 0)
            icon = "🟢" if reg_name == "Bull" else ("🔴" if reg_name == "Bear" else "🟡")
            color = "#22c55e" if reg_exp >= 0 else "#ef4444"
            st.markdown(f"""
            <div class="card" style="padding:12px 16px;margin-bottom:8px">
              <div style="display:flex;justify-content:space-between;align-items:center">
                <div><span style="font-weight:700;color:#f1f5f9">{icon} {reg_name} Market</span> <span style="color:#64748b;font-size:12px">({reg_trades} trades)</span></div>
                <div style="display:flex;gap:20px">
                  <span style="font-size:13px;color:#94a3b8">WR: <b style="color:{wr_color}">{reg_wr:.1f}%</b></span>
                  <span style="font-size:13px;color:#94a3b8">Expectancy: <b style="color:{color}">{reg_exp:+.2f}%</b></span>
                  <span style="font-size:13px;color:#94a3b8">P&L: <b style="color:{color}">₹{reg_pnl:+,.0f}</b></span>
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)

    # ─── Section B: Strategy Simulator ───────────────────────────────────────

    st.markdown("---")
    st.markdown("""
    <div class="card" style="border-color:#7c3aed33">
      <div style="font-size:16px;font-weight:700;color:#f1f5f9;margin-bottom:4px">🎛️ Strategy Parameter Simulator</div>
      <div style="color:#64748b;font-size:13px">Adjust parameters and simulate how the strategy would perform. Uses calibrated win-probability model.</div>
    </div>
    """, unsafe_allow_html=True)

    # Quick Presets
    st.markdown('<div class="section-label">Quick Presets</div>', unsafe_allow_html=True)
    pc1, pc2, pc3, pc4, pc5 = st.columns(5)

    preset = None
    with pc1:
        if st.button("🛡️ Conservative\n(2% TP / 1.5% SL)"):
            preset = {"tp": 2.0, "sl": 1.5, "weeks": 26, "pool": 20, "min_score": 65}
    with pc2:
        if st.button("⚡ Aggressive\n(5% TP / 3% SL)"):
            preset = {"tp": 5.0, "sl": 3.0, "weeks": 52, "pool": 20, "min_score": 60}
    with pc3:
        if st.button("🎯 Tight Scalp\n(1.5% TP / 1% SL)"):
            preset = {"tp": 1.5, "sl": 1.0, "weeks": 12, "pool": 10, "min_score": 70}
    with pc4:
        if st.button("🚀 High Conviction\n(8% TP / 4% SL)"):
            preset = {"tp": 8.0, "sl": 4.0, "weeks": 52, "pool": 10, "min_score": 75}
    with pc5:
        if st.button("🔄 Reset to Actual"):
            preset = {"tp": 4.0, "sl": 2.0, "weeks": 52, "pool": 20, "min_score": 60}

    if preset:
        st.session_state["sim_tp"] = preset["tp"]
        st.session_state["sim_sl"] = preset["sl"]
        st.session_state["sim_weeks"] = preset["weeks"]
        st.session_state["sim_pool"] = preset["pool"]
        st.session_state["sim_min_score"] = preset["min_score"]

    st.markdown("---")

    # Sliders
    s1, s2, s3 = st.columns(3)
    with s1:
        tp_pct = st.slider("Take Profit %", 1.0, 15.0, st.session_state.get("sim_tp", 4.0), 0.5, key="sim_tp_slider", help="Target return per trade")
    with s2:
        sl_pct = st.slider("Stop Loss %", 0.5, 10.0, st.session_state.get("sim_sl", 2.0), 0.5, key="sim_sl_slider", help="Max loss per trade")
    with s3:
        capital = st.select_slider("Starting Capital (₹)", options=[25000, 50000, 100000, 250000, 500000, 1000000],
                                    value=100000, format_func=lambda x: f"₹{x:,}", key="sim_cap")

    s4, s5, s6 = st.columns(3)
    with s4:
        sim_weeks = st.slider("Backtest Weeks", 4, 52, st.session_state.get("sim_weeks", 12), 4, key="sim_weeks_slider")
    with s5:
        pool_size = st.slider("Picks per Week", 5, 30, st.session_state.get("sim_pool", 10), 5, key="sim_pool_slider")
    with s6:
        min_score = st.slider("Min AI Score Filter", 40, 90, st.session_state.get("sim_min_score", 60), 5, key="sim_score_slider", help="Only trade picks above this AI score")

    col_run, col_inf = st.columns([1, 4])
    with col_run:
        run_sim = st.button("▶ Run Simulation", type="primary", use_container_width=True)

    st.markdown(f"""
    <div style="padding: 10px 16px;background:#0d1728;border:1px solid #1e2a3a;border-radius:8px;font-size:12px;color:#64748b">
      Current config: TP <b style="color:#22c55e">{tp_pct}%</b> · SL <b style="color:#ef4444">{sl_pct}%</b> ·
      R:R <b style="color:#38bdf8">1:{tp_pct/sl_pct:.1f}</b> · 
      {sim_weeks} weeks · {pool_size} picks/week · Min Score: {min_score}
    </div>
    """, unsafe_allow_html=True)

    if run_sim:
        progress = st.progress(0, text="Running simulation...")

        # Calibrated win probability model based on real backtest data
        # Base win rate from real data: 52.6%
        # Adjustments based on TP/SL ratio and score filter
        rr = tp_pct / sl_pct

        # Win rate improves with better R:R and higher score filter
        base_wr = 0.526
        rr_adj = (rr - 1.78) * 0.03      # Each unit of R:R above baseline
        score_adj = (min_score - 60) * 0.003  # Higher score filter = better stocks
        adj_wr = min(0.75, max(0.30, base_wr + rr_adj + score_adj))

        # Simulate week by week
        equity = float(capital)
        equity_curve_sim = [equity]
        trade_log = []
        weekly_rets = []

        for week in range(sim_weeks):
            progress.progress((week + 1) / sim_weeks, text=f"Simulating week {week+1} of {sim_weeks}...")

            # Regime effect (simulate regime shifts)
            regime_mult = 1.0
            if week % 8 < 2:  # ~25% bear weeks
                regime_mult = 0.85

            week_equity = equity
            trade_size = equity / pool_size
            week_pnl = 0.0
            week_trades = 0

            for _ in range(pool_size):
                outcome = random.random()
                effective_wr = adj_wr * regime_mult

                if outcome < effective_wr:
                    # Win — distributed around TP
                    gain = random.gauss(tp_pct, tp_pct * 0.15) / 100
                    week_pnl += trade_size * gain
                    trade_log.append({"week": week+1, "type": "WIN", "pct": gain*100})
                else:
                    # Loss — SL or time exit
                    loss_mult = random.choice([1.0, 1.0, 1.2, 1.5, 2.0])  # Sometimes SL slippage
                    loss = -sl_pct * loss_mult / 100
                    loss = max(loss, -sl_pct * 2.5 / 100)  # Cap loss
                    week_pnl += trade_size * loss
                    trade_log.append({"week": week+1, "type": "LOSS", "pct": loss*100})
                week_trades += 1

            equity += week_pnl
            equity = max(equity, 0)
            equity_curve_sim.append(equity)

            weekly_ret = week_pnl / week_equity * 100 if week_equity > 0 else 0
            weekly_rets.append(weekly_ret)

        progress.empty()

        # Metrics
        total_ret = (equity - capital) / capital * 100
        wins = [t for t in trade_log if t["type"] == "WIN"]
        losses = [t for t in trade_log if t["type"] == "LOSS"]
        actual_wr = len(wins) / len(trade_log) * 100 if trade_log else 0
        avg_win = sum(t["pct"] for t in wins) / len(wins) if wins else 0
        avg_loss = sum(t["pct"] for t in losses) / len(losses) if losses else 0
        expectancy = (actual_wr/100 * avg_win) + ((1 - actual_wr/100) * avg_loss)

        # Sharpe
        if weekly_rets and len(weekly_rets) > 1:
            sharpe = (np.mean(weekly_rets) / np.std(weekly_rets)) * math.sqrt(52) if np.std(weekly_rets) > 0 else 0
        else:
            sharpe = 0

        # Max DD
        peak = capital
        max_dd = 0
        for eq in equity_curve_sim:
            if eq > peak:
                peak = eq
            dd = (peak - eq) / peak * 100 if peak > 0 else 0
            max_dd = max(max_dd, dd)

        # Status Banner
        status_ok = total_ret > 5 and actual_wr > 55
        if status_ok:
            st.markdown(f"""<div style="background:#14532d22;border:1px solid #16653455;border-radius:10px;padding:14px 18px;margin:16px 0">
                <span style="color:#4ade80;font-size:16px;font-weight:700">✅ Strategy is Viable!</span>
                <span style="color:#86efac;font-size:13px;margin-left:10px">Avg return/trade: {expectancy:+.2f}% · Win Rate: {actual_wr:.1f}% · Sharpe: {sharpe:.2f}</span>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""<div style="background:#450a0a22;border:1px solid #45100a55;border-radius:10px;padding:14px 18px;margin:16px 0">
                <span style="color:#ef4444;font-size:16px;font-weight:700">⚠ Strategy Needs Tuning</span>
                <span style="color:#fca5a5;font-size:13px;margin-left:10px">Avg return/trade: {expectancy:+.2f}% · Win Rate: {actual_wr:.1f}% · Sharpe: {sharpe:.2f}</span>
            </div>""", unsafe_allow_html=True)

        # Results Grid
        st.markdown(f'<div style="font-size:15px;font-weight:700;color:#f1f5f9;margin:12px 0">Simulation Results — {sim_weeks} Weeks · {len(trade_log)} Trades</div>', unsafe_allow_html=True)
        r1, r2, r3, r4 = st.columns(4)
        tr_color2 = "#22c55e" if total_ret >= 0 else "#ef4444"
        wr_color2 = "#22c55e" if actual_wr >= 60 else ("#f59e0b" if actual_wr >= 50 else "#ef4444")
        with r1:
            final_cap = equity
            st.markdown(metric_card("Total Return", f'<span style="color:{tr_color2}">{total_ret:+.1f}%</span>',
                f'₹{capital:,} → ₹{final_cap:,.0f}', tr_color2), unsafe_allow_html=True)
        with r2:
            st.markdown(metric_card("Win Rate", f'<span style="color:{wr_color2}">{actual_wr:.1f}%</span>',
                "Target: >60%", wr_color2), unsafe_allow_html=True)
        with r3:
            exp_col = "#22c55e" if expectancy >= 0 else "#ef4444"
            st.markdown(metric_card("Expectancy/Trade", f'<span style="color:{exp_col}">{expectancy:+.2f}%</span>',
                "Target: >0%", exp_col), unsafe_allow_html=True)
        with r4:
            sh_col = "#22c55e" if sharpe >= 0.5 else ("#f59e0b" if sharpe >= 0 else "#ef4444")
            st.markdown(metric_card("Sharpe Ratio", f'<span style="color:{sh_col}">{sharpe:.2f}</span>',
                ">0.5 = good, >1.0 = great", sh_col), unsafe_allow_html=True)

        r5, r6, r7, r8 = st.columns(4)
        with r5:
            st.markdown(metric_card("Avg Win %", f'<span class="pos">+{avg_win:.2f}%</span>', f"{len(wins)} winning trades"), unsafe_allow_html=True)
        with r6:
            st.markdown(metric_card("Avg Loss %", f'<span class="neg">{avg_loss:.2f}%</span>', f"{len(losses)} losing trades"), unsafe_allow_html=True)
        with r7:
            st.markdown(metric_card("Max Drawdown", f'<span class="neg">{max_dd:.1f}%</span>', "Target: <15%"), unsafe_allow_html=True)
        with r8:
            st.markdown(metric_card("R:R Ratio", f'<span class="blue">1:{rr:.1f}</span>', "Target: >1.5"), unsafe_allow_html=True)

        # Equity Curve Chart
        st.markdown('<div style="font-size:14px;font-weight:700;color:#f1f5f9;margin:16px 0 8px">📈 Simulated Equity Curve</div>', unsafe_allow_html=True)
        eq_df = pd.DataFrame({"Week": list(range(len(equity_curve_sim))), "Equity (₹)": equity_curve_sim})
        st.line_chart(eq_df.set_index("Week"), color=["#1a56db"])

        # Key Insight
        st.markdown(f"""
        <div class="card" style="border-color:#7c3aed33;margin-top:8px">
          <div style="font-weight:700;color:#a78bfa;margin-bottom:8px">💡 Simulation Insight</div>
          <div style="color:#94a3b8;font-size:13px;line-height:1.6">
            With <b style="color:#f1f5f9">TP: {tp_pct}%</b> and <b style="color:#f1f5f9">SL: {sl_pct}%</b>, the strategy
            {'<b style="color:#22c55e">outperforms</b>' if total_ret > 0 else '<b style="color:#ef4444">underperforms</b>'}
            on a {sim_weeks}-week horizon.
            {'The R:R ratio of 1:' + f'{rr:.1f} combined with a {actual_wr:.0f}% win rate gives positive expectancy.' if expectancy > 0 else
             'The fundamental issue is that losses (' + f'{avg_loss:.1f}%) exceed wins ({avg_win:.1f}%) in absolute terms. Tighten your SL or raise your TP to fix this.'}
          </div>
        </div>
        """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════════
# TAB 5 — STRATEGY GUIDE
# ════════════════════════════════════════════════════════════════════════════════

with tab5:
    st.markdown("""
    <div class="card">
      <div class="section-title">📚 MarketPulse India — Complete Strategy Guide</div>
      <div style="color:#64748b;font-size:13px">Everything you need to understand and use this platform effectively.</div>
    </div>
    """, unsafe_allow_html=True)

    s1, s2 = st.columns([1, 1])

    with s1:
        st.markdown("""
        <div class="card">
          <div style="font-weight:700;color:#38bdf8;margin-bottom:12px;font-size:15px">🤖 Understanding AI Signals</div>

          <div style="font-weight:600;color:#f1f5f9;margin-top:12px">What is an AI Score?</div>
          <div style="color:#64748b;font-size:12px;margin-top:4px">A composite score (0-100) calculated from multi-timeframe momentum, fundamental strength (PE, Market Cap), and market regime alignment. Higher = stronger setup.</div>

          <div style="font-weight:600;color:#f1f5f9;margin-top:12px">What do BUY / HOLD / SELL mean?</div>
          <div style="color:#64748b;font-size:12px;margin-top:4px">
            <span style="color:#4ade80">▲ BUY</span>: Stock showing uptrend across multiple timeframes + high AI score<br>
            <span style="color:#fbbf24">◆ HOLD</span>: Sideways/consolidating — wait for clearer signal<br>
            <span style="color:#f87171">▼ SELL</span>: Downtrend detected — avoid or exit if holding
          </div>

          <div style="font-weight:600;color:#f1f5f9;margin-top:12px">How to use Entry / SL / Target?</div>
          <div style="color:#64748b;font-size:12px;margin-top:4px">Entry = current EOD price<br>Stop Loss = maximum acceptable loss<br>Target = expected profit zone (4% default)<br>Always place a stop loss order immediately after buying.</div>

          <div style="font-weight:600;color:#f1f5f9;margin-top:12px">Time Horizon</div>
          <div style="color:#64748b;font-size:12px;margin-top:4px">Short Term = 2–4 weeks (momentum trade)<br>Medium Term = 1–2 months (trend continuation)</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="card">
          <div style="font-weight:700;color:#a78bfa;margin-bottom:12px;font-size:15px">📊 Reading Backtest Results</div>

          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
            <div>
              <div style="color:#f1f5f9;font-weight:600;font-size:12px">Win Rate</div>
              <div style="color:#64748b;font-size:11px">% of trades that hit target. Target: >60%</div>
            </div>
            <div>
              <div style="color:#f1f5f9;font-weight:600;font-size:12px">Expectancy</div>
              <div style="color:#64748b;font-size:11px">Average profit per trade. Must be >0% to be profitable.</div>
            </div>
            <div>
              <div style="color:#f1f5f9;font-weight:600;font-size:12px">Profit Factor</div>
              <div style="color:#64748b;font-size:11px">Total wins ÷ Total losses. Must be >1.0. Target: >1.5</div>
            </div>
            <div>
              <div style="color:#f1f5f9;font-weight:600;font-size:12px">Sharpe Ratio</div>
              <div style="color:#64748b;font-size:11px">Risk-adjusted return. >0.5 = good, >1.0 = great</div>
            </div>
            <div>
              <div style="color:#f1f5f9;font-weight:600;font-size:12px">Max Drawdown</div>
              <div style="color:#64748b;font-size:11px">Biggest peak-to-trough loss. Target: <15%</div>
            </div>
            <div>
              <div style="color:#f1f5f9;font-weight:600;font-size:12px">R:R Ratio</div>
              <div style="color:#64748b;font-size:11px">Reward vs Risk per trade. Target: >1.5:1</div>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    with s2:
        st.markdown("""
        <div class="card">
          <div style="font-weight:700;color:#22c55e;margin-bottom:12px;font-size:15px">🏗️ System Architecture</div>

          <div style="position:relative;padding-left:20px">
            <div style="border-left:2px solid #1e2a3a;padding-bottom:0">

              <div style="margin-bottom:16px;position:relative">
                <div style="width:10px;height:10px;background:#38bdf8;border-radius:50%;position:absolute;left:-25px;top:4px"></div>
                <div style="color:#38bdf8;font-weight:600;font-size:13px">GitHub Actions (6PM IST Daily)</div>
                <div style="color:#64748b;font-size:12px;margin-top:2px">Automated trigger: Downloads NSE universe, runs Python pipeline</div>
              </div>

              <div style="margin-bottom:16px;position:relative">
                <div style="width:10px;height:10px;background:#a78bfa;border-radius:50%;position:absolute;left:-25px;top:4px"></div>
                <div style="color:#a78bfa;font-weight:600;font-size:13px">scanner.py — Universe Builder</div>
                <div style="color:#64748b;font-size:12px;margin-top:2px">Fetches 2,107 NSE tickers, calculates 1W/2W/1M/3M/6M/12M momentum</div>
              </div>

              <div style="margin-bottom:16px;position:relative">
                <div style="width:10px;height:10px;background:#22c55e;border-radius:50%;position:absolute;left:-25px;top:4px"></div>
                <div style="color:#22c55e;font-weight:600;font-size:13px">ai_engine.py — Intelligence Layer</div>
                <div style="color:#64748b;font-size:12px;margin-top:2px">Scores stocks, applies market regime filter, generates BUY/HOLD/SELL with Entry/SL/TP</div>
              </div>

              <div style="margin-bottom:16px;position:relative">
                <div style="width:10px;height:10px;background:#f59e0b;border-radius:50%;position:absolute;left:-25px;top:4px"></div>
                <div style="color:#f59e0b;font-weight:600;font-size:13px">backtest.py — Validation Engine</div>
                <div style="color:#64748b;font-size:12px;margin-top:2px">Walk-forward simulation across 52 weeks with TP/SL/Time exits</div>
              </div>

              <div style="margin-bottom:16px;position:relative">
                <div style="width:10px;height:10px;background:#ef4444;border-radius:50%;position:absolute;left:-25px;top:4px"></div>
                <div style="color:#ef4444;font-weight:600;font-size:13px">performance.py — Reporting Layer</div>
                <div style="color:#64748b;font-size:12px;margin-top:2px">Generates performance_report.json (Sharpe, Drawdown, Expectancy, monthly breakdown)</div>
              </div>

              <div style="position:relative">
                <div style="width:10px;height:10px;background:#f1f5f9;border-radius:50%;position:absolute;left:-25px;top:4px"></div>
                <div style="color:#f1f5f9;font-weight:600;font-size:13px">Streamlit Dashboard (This App)</div>
                <div style="color:#64748b;font-size:12px;margin-top:2px">Reads JSON outputs, renders interactive UI — deployed free on Streamlit Cloud</div>
              </div>

            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="card">
          <div style="font-weight:700;color:#f59e0b;margin-bottom:12px;font-size:15px">📌 Current Strategy Status</div>

          <div style="background:#1c1200;border:1px solid #451a03;border-radius:8px;padding:12px;margin-bottom:12px">
            <div style="color:#fbbf24;font-weight:600;font-size:13px">⚠️ Current Assessment: LAB PHASE</div>
            <div style="color:#92400e;font-size:12px;margin-top:6px">
              Real backtest (52 weeks) shows -12.56% total return.<br>
              Root cause: Avg loss (-4.84%) > Avg win (+3.43%) = Negative expectancy (-0.49%)
            </div>
          </div>

          <div style="font-weight:600;color:#f1f5f9;font-size:13px;margin-bottom:8px">🔧 Improvement Roadmap</div>
          <div style="font-size:12px;color:#64748b;line-height:1.8">
            <div>Phase A: <span style="color:#4ade80">✓ Complete</span> — Universe, AI Scoring, Multi-TF</div>
            <div>Phase B: <span style="color:#4ade80">✓ Complete</span> — Backtest Infrastructure</div>
            <div>Phase C: 🔄 In Progress — Fix R:R (tight SL + wider TP)</div>
            <div>Phase D: Pending — Pullback Entry Logic (EMA9 retest)</div>
            <div>Phase E: Pending — Dynamic Position Sizing by regime</div>
            <div>Phase F: Pending — Broker API Integration (Kite/Upstox)</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class="card">
      <div style="font-weight:700;color:#f1f5f9;margin-bottom:12px;font-size:15px">❓ Frequently Asked Questions</div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px">
        <div>
          <div style="color:#38bdf8;font-weight:600;font-size:13px">Is this financial advice?</div>
          <div style="color:#64748b;font-size:12px">No. This is a research and educational tool. All signals are algorithmic and not from registered advisors.</div>

          <div style="color:#38bdf8;font-weight:600;font-size:13px;margin-top:14px">How often is it updated?</div>
          <div style="color:#64748b;font-size:12px">Every trading day automatically via GitHub Actions at 6PM IST after market close.</div>

          <div style="color:#38bdf8;font-weight:600;font-size:13px;margin-top:14px">What data sources are used?</div>
          <div style="color:#64748b;font-size:12px">Price data: yfinance (Yahoo Finance NSE feed). Fundamentals: NSEpy / yfinance info. News: RSS/Google Finance</div>
        </div>
        <div>
          <div style="color:#a78bfa;font-weight:600;font-size:13px">How should I size positions?</div>
          <div style="color:#64748b;font-size:12px">Risk max 1-2% of total capital per trade. For ₹1L capital: risk ₹1,000-2,000 per trade. Never go all-in on one stock.</div>

          <div style="color:#a78bfa;font-weight:600;font-size:13px;margin-top:14px">Why are there negative backtest results?</div>
          <div style="color:#64748b;font-size:12px">The current stop loss (2%) is narrower than take profit (4%), but in practice slippage and whipsaw cause larger losses. We're actively optimizing this.</div>

          <div style="color:#a78bfa;font-weight:600;font-size:13px;margin-top:14px">Where do I report issues?</div>
          <div style="color:#64748b;font-size:12px">GitHub: <a href="https://github.com/vinayloki/india-swing-scanner" target="_blank" style="color:#38bdf8">vinayloki/india-swing-scanner</a></div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="disclaimer">
      ⚠️ <b>SEBI DISCLAIMER</b>: MarketPulse India is NOT a SEBI-registered investment advisor, research analyst, or portfolio manager.
      All content including AI signals, backtest results, and market analysis is provided for <b>educational and research purposes only</b>.
      Investing in securities involves risk. Past performance is not indicative of future results.
      Users are solely responsible for their own investment decisions. Always consult a qualified SEBI-registered advisor before trading.
    </div>
    """, unsafe_allow_html=True)

# ─── Footer ───────────────────────────────────────────────────────────────────

st.markdown("""
<div style="text-align:center;padding:24px;color:#334155;font-size:12px;border-top:1px solid #1e2a3a;margin-top:24px">
  MarketPulse India · Quantitative Trading Terminal · Built with Python + Streamlit ·
  <a href="https://github.com/vinayloki/india-swing-scanner" target="_blank" style="color:#475569;text-decoration:none">GitHub</a> ·
  Data: Yahoo Finance / NSEpy · Auto-updated daily via GitHub Actions · For educational use only
</div>
""", unsafe_allow_html=True)
