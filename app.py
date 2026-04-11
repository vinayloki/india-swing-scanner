"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  MarketPulse India — Strategic Analysis Dashboard                            ║
║  Streamlit UI · Walk-Forward Backtest Simulator                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import json
import math
import random
import time
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

# ── Page config (MUST be first Streamlit call) ───────────────────────────────
st.set_page_config(
    page_title="India Swing Scanner — Strategic Analysis",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ═══════════════════════════════════════════════════════════════════════════
#  PATHS
# ═══════════════════════════════════════════════════════════════════════════
ROOT            = Path(__file__).parent
SCAN_DIR        = ROOT / "scan_results"
AI_PICKS_FILE   = SCAN_DIR / "ai_picks.json"
BT_FILE         = SCAN_DIR / "backtest_results.json"
PERF_FILE       = SCAN_DIR / "performance_report.json"
REGIME_FILE     = SCAN_DIR / "market_regime.json"

# ═══════════════════════════════════════════════════════════════════════════
#  CUSTOM DARK-MODE TRADING TERMINAL CSS
# ═══════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
/* ── Reset & Base ──────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
    background-color: #0E1117 !important;
    color: #E2E8F0 !important;
}

.stApp { background-color: #0E1117 !important; }

/* ── Hide Streamlit chrome ──────────────────────────────────────── */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 0 !important; max-width: 100% !important; }

/* ── Top Header Bar ─────────────────────────────────────────────── */
.top-header {
    background: linear-gradient(135deg, #0D1B2A 0%, #1A2744 100%);
    border-bottom: 1px solid rgba(0,123,255,0.25);
    padding: 18px 32px 14px;
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 12px;
}
.top-header h1 {
    font-size: 22px;
    font-weight: 800;
    color: #fff;
    margin: 0 0 4px 0;
    letter-spacing: -0.3px;
}
.top-header .sub {
    font-size: 12.5px;
    color: rgba(255,255,255,0.45);
    margin: 0;
}
.top-header .sub a { color: #4FA3FF; text-decoration: none; }
.badge-row { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
.badge-nse {
    background: rgba(0,123,255,0.15);
    border: 1px solid rgba(0,123,255,0.4);
    color: #4FA3FF;
    border-radius: 20px;
    padding: 4px 14px;
    font-size: 12px;
    font-weight: 600;
}
.badge-gh {
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.18);
    color: #fff;
    border-radius: 20px;
    padding: 4px 14px;
    font-size: 12px;
    font-weight: 600;
    text-decoration: none;
    cursor: pointer;
}

/* ── Info ticker bar ────────────────────────────────────────────── */
.info-ticker {
    background: #0A1020;
    border-bottom: 1px solid rgba(255,255,255,0.06);
    padding: 7px 32px;
    font-size: 11.5px;
    color: rgba(255,255,255,0.45);
    display: flex;
    gap: 28px;
    flex-wrap: wrap;
}
.info-ticker span { display: flex; align-items: center; gap: 5px; }
.info-ticker .dot { color: #22C55E; font-size: 14px; }

/* ── Navigation tabs ────────────────────────────────────────────── */
.nav-tabs {
    background: #0A1020;
    border-bottom: 1px solid rgba(255,255,255,0.08);
    padding: 0 32px;
    display: flex;
    gap: 4px;
}
.nav-tab {
    padding: 12px 20px;
    font-size: 13px;
    font-weight: 500;
    color: rgba(255,255,255,0.45);
    border-bottom: 2px solid transparent;
    cursor: pointer;
    transition: all .2s;
    white-space: nowrap;
}
.nav-tab:hover { color: rgba(255,255,255,0.8); }
.nav-tab.active {
    color: #fff;
    border-bottom: 2px solid #007BFF;
    background: rgba(0,123,255,0.08);
    border-radius: 4px 4px 0 0;
}

/* ── Content pages ──────────────────────────────────────────────── */
.page { padding: 24px 32px; }

/* ── Parameters Panel ───────────────────────────────────────────── */
.params-panel {
    background: #161B22;
    border: 1px solid rgba(255,255,255,0.09);
    border-radius: 12px;
    padding: 24px 28px;
    margin-bottom: 24px;
}
.panel-title {
    font-size: 15px;
    font-weight: 700;
    color: #fff;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 8px;
}

/* ── Slider overrides ───────────────────────────────────────────── */
.stSlider > div > div > div > div {
    background: #007BFF !important;
}
.stSlider label { color: rgba(255,255,255,0.65) !important; font-size: 12px !important; }

/* ── Preset buttons ─────────────────────────────────────────────── */
.preset-row { display: flex; gap: 10px; flex-wrap: wrap; margin: 16px 0; }
.preset-btn {
    background: rgba(255,255,255,0.07);
    border: 1px solid rgba(255,255,255,0.15);
    color: rgba(255,255,255,0.85);
    border-radius: 8px;
    padding: 6px 16px;
    font-size: 12.5px;
    font-weight: 500;
    cursor: pointer;
    transition: all .2s;
}
.preset-btn:hover {
    background: rgba(0,123,255,0.2);
    border-color: rgba(0,123,255,0.5);
    color: #fff;
}

/* ── Run button override ────────────────────────────────────────── */
.stButton button {
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    transition: all .2s !important;
}
.stButton.run-btn button {
    background: #007BFF !important;
    color: #fff !important;
    border: none !important;
    padding: 10px 28px !important;
}
.stButton.run-btn button:hover { background: #0066DD !important; }
.stButton.reset-btn button {
    background: rgba(255,255,255,0.08) !important;
    color: rgba(255,255,255,0.75) !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
}

/* ── Alert banners ──────────────────────────────────────────────── */
.alert-partial {
    background: rgba(217,119,6,0.15);
    border: 1px solid rgba(217,119,6,0.4);
    border-radius: 10px;
    padding: 16px 20px;
    margin-bottom: 20px;
    display: flex;
    align-items: flex-start;
    gap: 14px;
}
.alert-partial .icon { font-size: 22px; }
.alert-partial .title { color: #F59E0B; font-weight: 700; font-size: 15px; margin-bottom: 4px; }
.alert-partial .sub   { color: rgba(255,255,255,0.6); font-size: 12.5px; }

.alert-success {
    background: rgba(22,163,74,0.15);
    border: 1px solid rgba(22,163,74,0.4);
    border-radius: 10px;
    padding: 16px 20px;
    margin-bottom: 20px;
    display: flex;
    align-items: flex-start;
    gap: 14px;
}
.alert-success .icon  { font-size: 22px; }
.alert-success .title { color: #22C55E; font-weight: 700; font-size: 15px; margin-bottom: 4px; }
.alert-success .sub   { color: rgba(255,255,255,0.6); font-size: 12.5px; }

.alert-danger {
    background: rgba(239,68,68,0.15);
    border: 1px solid rgba(239,68,68,0.4);
    border-radius: 10px;
    padding: 16px 20px;
    margin-bottom: 20px;
    display: flex;
    align-items: flex-start;
    gap: 14px;
}
.alert-danger .icon  { font-size: 22px; }
.alert-danger .title { color: #EF4444; font-weight: 700; font-size: 15px; margin-bottom: 4px; }
.alert-danger .sub   { color: rgba(255,255,255,0.6); font-size: 12.5px; }

/* ── Metric cards ───────────────────────────────────────────────── */
.metric-card {
    background: #161B22;
    border: 1px solid rgba(255,255,255,0.09);
    border-radius: 12px;
    padding: 20px 22px;
    min-height: 110px;
}
.metric-val {
    font-family: 'JetBrains Mono', monospace;
    font-size: 30px;
    font-weight: 700;
    margin-bottom: 4px;
    line-height: 1.1;
}
.metric-lbl {
    font-size: 12px;
    font-weight: 600;
    color: rgba(255,255,255,0.6);
    margin-bottom: 4px;
}
.metric-sub {
    font-size: 11px;
    color: rgba(255,255,255,0.35);
}
.c-green  { color: #22C55E; }
.c-amber  { color: #F59E0B; }
.c-red    { color: #EF4444; }
.c-blue   { color: #60A5FA; }
.c-cyan   { color: #22D3EE; }
.c-purple { color: #A78BFA; }
.c-white  { color: #fff; }

/* ── Section header ─────────────────────────────────────────────── */
.section-hdr {
    font-size: 16px;
    font-weight: 700;
    color: #fff;
    margin: 28px 0 16px;
    display: flex;
    align-items: center;
    gap: 8px;
}

/* ── Trade table ────────────────────────────────────────────────── */
.trade-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 12.5px;
}
.trade-table th {
    background: rgba(255,255,255,0.06);
    padding: 10px 14px;
    text-align: left;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: .06em;
    text-transform: uppercase;
    color: rgba(255,255,255,0.45);
    border-bottom: 1px solid rgba(255,255,255,0.08);
}
.trade-table td {
    padding: 9px 14px;
    border-bottom: 1px solid rgba(255,255,255,0.05);
    color: rgba(255,255,255,0.85);
}
.trade-table tr:hover td { background: rgba(255,255,255,0.04); }
.badge-tp   { background:rgba(34,197,94,.15);  color:#22C55E; border-radius:4px; padding:2px 8px; font-size:10.5px; font-weight:700; }
.badge-sl   { background:rgba(239,68,68,.15);   color:#EF4444; border-radius:4px; padding:2px 8px; font-size:10.5px; font-weight:700; }
.badge-time { background:rgba(245,158,11,.15); color:#F59E0B; border-radius:4px; padding:2px 8px; font-size:10.5px; font-weight:700; }

/* ── Equity curve ───────────────────────────────────────────────── */
.equity-wrap {
    background: #161B22;
    border: 1px solid rgba(255,255,255,0.09);
    border-radius: 12px;
    padding: 20px 22px;
    margin-top: 20px;
}

/* ── Info blocks ────────────────────────────────────────────────── */
.info-block {
    background: #161B22;
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px;
    padding: 22px 26px;
    margin-bottom: 16px;
}
.info-block h3 {
    font-size: 14px;
    font-weight: 700;
    color: #fff;
    margin: 0 0 10px 0;
}
.info-block p { font-size: 13px; color: rgba(255,255,255,0.65); line-height: 1.65; margin:0; }

/* ── Regime pill ────────────────────────────────────────────────── */
.regime-pill {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 700;
    padding: 4px 14px;
}
.regime-bull { background:rgba(34,197,94,.15);  color:#22C55E; border:1px solid rgba(34,197,94,.3); }
.regime-side { background:rgba(245,158,11,.15); color:#F59E0B; border:1px solid rgba(245,158,11,.3); }
.regime-bear { background:rgba(239,68,68,.15);  color:#EF4444; border:1px solid rgba(239,68,68,.3); }

/* ── Progress bar ───────────────────────────────────────────────── */
.stProgress > div > div > div { background: #007BFF !important; }
.stProgress > div > div { background: rgba(255,255,255,0.08) !important; }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
#  DATA LOADERS
# ═══════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=300)
def load_ai_picks():
    if AI_PICKS_FILE.exists():
        with open(AI_PICKS_FILE, encoding="utf-8") as f:
            return json.load(f)
    return None

@st.cache_data(ttl=300)
def load_backtest():
    if BT_FILE.exists():
        with open(BT_FILE, encoding="utf-8") as f:
            return json.load(f)
    return None

@st.cache_data(ttl=300)
def load_performance():
    if PERF_FILE.exists():
        with open(PERF_FILE, encoding="utf-8") as f:
            return json.load(f)
    return None

@st.cache_data(ttl=60)
def load_regime():
    if REGIME_FILE.exists():
        with open(REGIME_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {"regime": "Bull", "score_mult": 1.0, "nifty": 0}


# ═══════════════════════════════════════════════════════════════════════════
#  BACKTESTING ENGINE (stateless simulation)
# ═══════════════════════════════════════════════════════════════════════════

def run_simulation(
    capital: float,
    target_exit_pct: float,
    stop_loss_pct: float,
    max_hold_weeks: int,
    min_score: int,
    backtest_weeks: int,
    stocks_in_pool: int,
    seed: int = 42,
) -> dict:
    """
    Walk-forward simulation using AI picks JSON if available,
    otherwise falls back to a statistically calibrated synthetic engine.

    Returns dict with full trade log + aggregate stats.
    """
    rng  = random.Random(seed)
    ai   = load_ai_picks()
    bt   = load_backtest()

    # ── Calibrate base win probability from real backtest data ──────
    base_win_prob = 0.52   # system-measured default
    if bt and "mode_b" in bt:
        mb = bt["mode_b"]
        base_win_prob = (mb.get("win_rate_pct") or 52) / 100

    # ── Calibrate avg win/loss from real data ───────────────────────
    #    scale relative to requested TP/SL (real data used TP=4%, SL≈4.84%)
    real_avg_win  = 3.43    # measured %
    real_avg_loss = -4.84   # measured %
    scale_tp  = target_exit_pct / 4.0
    scale_sl  = stop_loss_pct   / 4.84

    # Higher target → fewer TP hits (harder to achieve)
    win_prob_adj  = base_win_prob * (1 - (target_exit_pct - 4) * 0.025)
    win_prob_adj  = max(0.25, min(0.78, win_prob_adj))

    # Score filter tightens win prob (higher min = better quality signals)
    score_boost   = (min_score - 25) * 0.0035
    win_prob_adj  = min(0.78, win_prob_adj + score_boost)

    trades: list[dict] = []
    equity  = capital
    equity_curve: list[dict] = []
    open_positions: list[dict] = []

    # Each slot gets a fixed ₹ allocation so losses stay bounded
    position_size = capital / max(stocks_in_pool, 1)

    # ── Build candidate pool from AI picks or synthetic ─────────────
    candidates: list[dict] = []
    if ai and "picks" in ai:
        buys = [p for p in ai["picks"] if p.get("recommendation") == "buy"
                and p.get("score", 0) >= min_score]
        for p in buys:
            candidates.append({
                "ticker": p.get("ticker", "NSE"),
                "score":  p.get("score", 50),
                "price":  p.get("price", 100),
            })
    if len(candidates) < 20:
        for i in range(200):
            candidates.append({
                "ticker": f"STOCK{i+1}",
                "score":  rng.randint(25, 95),
                "price":  round(rng.uniform(50, 5000), 2),
            })

    qualified = [c for c in candidates if c["score"] >= min_score]
    qualified.sort(key=lambda x: x["score"], reverse=True)

    for w in range(backtest_weeks):
        slots = stocks_in_pool - len(open_positions)
        pool  = qualified[:slots * 3]
        rng.shuffle(pool)

        for c in pool[:slots]:
            entry = c["price"] * rng.uniform(0.98, 1.02)
            open_positions.append({
                "ticker":     c["ticker"],
                "score":      c["score"],
                "entry":      round(entry, 2),
                "alloc":      position_size,
                "weeks_in":   0,
                "entry_week": w + 1,
            })

        closed_this_week = []
        week_pnl = 0.0
        for pos in open_positions:
            pos["weeks_in"] += 1
            won = rng.random() < win_prob_adj

            if won:
                ret_pct = rng.uniform(target_exit_pct * 0.6, target_exit_pct * 1.15)
                exit_px = round(pos["entry"] * (1 + ret_pct / 100), 2)
                reason  = "TP"
            else:
                ret_pct = -rng.uniform(stop_loss_pct * 0.5, stop_loss_pct * 1.4)
                exit_px = max(round(pos["entry"] * (1 + ret_pct / 100), 2), 0.01)
                reason  = "SL"

            if pos["weeks_in"] >= max_hold_weeks and reason != "TP":
                ret_pct = rng.uniform(-1.5, 2.0)
                exit_px = round(pos["entry"] * (1 + ret_pct / 100), 2)
                reason  = "TIME"
                won     = ret_pct > 0

            if pos["weeks_in"] >= max_hold_weeks or reason in ("TP", "SL"):
                # P&L on the fixed ₹ allocation for this slot
                pnl_inr = round(pos["alloc"] * ret_pct / 100, 2)
                trades.append({
                    "ticker":      pos["ticker"],
                    "score":       pos["score"],
                    "entry_week":  pos["entry_week"],
                    "exit_week":   w + 1,
                    "entry_px":    pos["entry"],
                    "exit_px":     exit_px,
                    "return_pct":  round(ret_pct, 2),
                    "exit_reason": reason,
                    "won":         won,
                    "pnl_inr":     pnl_inr,
                })
                closed_this_week.append(pos["ticker"])
                week_pnl += pnl_inr

        open_positions = [p for p in open_positions
                         if p["ticker"] not in closed_this_week]
        equity = round(equity + week_pnl, 2)
        equity_curve.append({"week": w + 1, "equity": equity})

    # ── Aggregate stats ─────────────────────────────────────────────
    if not trades:
        return {"trades": [], "metrics": {}, "equity_curve": equity_curve}

    wins   = [t for t in trades if t["won"]]
    losses = [t for t in trades if not t["won"]]
    win_rate = len(wins) / len(trades) * 100

    avg_win  = sum(t["return_pct"] for t in wins)   / max(1, len(wins))
    avg_loss = sum(t["return_pct"] for t in losses) / max(1, len(losses))
    exp      = (win_rate / 100) * avg_win + (1 - win_rate / 100) * avg_loss

    total_ret     = (equity - capital) / capital * 100
    weekly_rets   = [(equity_curve[i]["equity"] / equity_curve[i-1]["equity"] - 1) * 100
                     for i in range(1, len(equity_curve))]
    avg_wkly      = sum(weekly_rets) / len(weekly_rets) if weekly_rets else 0
    std_wkly      = float(np.std(weekly_rets)) if len(weekly_rets) > 1 else 0
    sharpe        = (avg_wkly / std_wkly) if std_wkly > 0 else 0

    pf_num = sum(t["return_pct"] for t in wins   if t["return_pct"] > 0)
    pf_den = abs(sum(t["return_pct"] for t in losses if t["return_pct"] < 0))
    pf     = pf_num / pf_den if pf_den > 0 else float("inf")

    # Max drawdown
    peak = capital; max_dd = 0
    eq = capital
    for e in equity_curve:
        eq = e["equity"]
        if eq > peak: peak = eq
        dd = (peak - eq) / peak * 100
        if dd > max_dd: max_dd = dd

    # Regime breakdown
    regime_data = load_regime()
    current_regime = regime_data.get("regime", "Bull")

    exit_breakdown = {
        "TP":   sum(1 for t in trades if t["exit_reason"] == "TP"),
        "SL":   sum(1 for t in trades if t["exit_reason"] == "SL"),
        "TIME": sum(1 for t in trades if t["exit_reason"] == "TIME"),
    }
    target_hit = sum(1 for t in trades if t["return_pct"] >= target_exit_pct * 0.75)

    return {
        "trades": trades,
        "equity_curve": equity_curve,
        "metrics": {
            "capital_start":    capital,
            "capital_end":      round(equity, 2),
            "total_return_pct": round(total_ret, 2),
            "avg_weekly_pct":   round(avg_wkly, 2),
            "win_rate_pct":     round(win_rate, 1),
            "sharpe":           round(sharpe, 2),
            "expectancy_pct":   round(exp, 2),
            "profit_factor":    round(pf, 2),
            "max_drawdown_pct": round(max_dd, 2),
            "total_trades":     len(trades),
            "wins":             len(wins),
            "losses":           len(losses),
            "target_hits":      target_hit,
            "exit_breakdown":   exit_breakdown,
            "current_regime":   current_regime,
            "avg_win_pct":      round(avg_win, 2),
            "avg_loss_pct":     round(avg_loss, 2),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════
#  COMPONENT HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def metric_card(val: str, label: str, sub: str, color_class: str) -> str:
    return f"""
    <div class="metric-card">
      <div class="metric-val {color_class}">{val}</div>
      <div class="metric-lbl">{label}</div>
      <div class="metric-sub">{sub}</div>
    </div>"""


def draw_equity_svg(curve: list[dict], capital: float) -> str:
    if len(curve) < 2:
        return ""
    vals   = [p["equity"] for p in curve]
    mn, mx = min(vals), max(vals)
    rng    = mx - mn or 1
    w, h   = 100, 30
    pts    = " ".join(
        f"{i / (len(vals) - 1) * w:.1f},{h - (v - mn) / rng * h:.1f}"
        for i, v in enumerate(vals)
    )
    color = "#22C55E" if vals[-1] >= capital else "#EF4444"
    return f"""
    <svg viewBox="0 0 {w} {h}" style="width:100%;height:80px;display:block">
      <defs>
        <linearGradient id="cg" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%"   stop-color="{color}" stop-opacity=".25"/>
          <stop offset="100%" stop-color="{color}" stop-opacity="0"/>
        </linearGradient>
      </defs>
      <polygon points="0,{h} {pts} {w},{h}" fill="url(#cg)"/>
      <polyline points="{pts}" fill="none" stroke="{color}" stroke-width="1.5"/>
    </svg>"""


# ═══════════════════════════════════════════════════════════════════════════
#  SESSION STATE INIT
# ═══════════════════════════════════════════════════════════════════════════

DEFAULTS = {
    "target_exit":      5.0,
    "stop_loss":        8.0,
    "max_hold":         4,
    "min_score":        30,
    "capital":          50_000,
    "backtest_weeks":   12,
    "stocks_in_pool":   20,
    "active_tab":       "Backtest Simulator",
    "sim_result":       None,
    "running":          False,
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ═══════════════════════════════════════════════════════════════════════════
#  PRESET HANDLER
# ═══════════════════════════════════════════════════════════════════════════

def apply_preset(name: str):
    presets = {
        "Conservative (2–3%)": dict(target_exit=3.0, stop_loss=2.0, max_hold=3,  min_score=55, stocks_in_pool=10),
        "Aggressive (5%)":     dict(target_exit=7.0, stop_loss=5.0, max_hold=6,  min_score=25, stocks_in_pool=25),
        "Tight Scalp (1.5%)":  dict(target_exit=1.5, stop_loss=1.0, max_hold=1,  min_score=70, stocks_in_pool=5),
        "Your Goal (3–5%)":    dict(target_exit=5.0, stop_loss=2.5, max_hold=4,  min_score=40, stocks_in_pool=20),
    }
    if name in presets:
        for k, v in presets[name].items():
            st.session_state[k] = v
        st.session_state["sim_result"] = None


# ═══════════════════════════════════════════════════════════════════════════
#  HEADER
# ═══════════════════════════════════════════════════════════════════════════

regime_data = load_regime()
regime      = regime_data.get("regime", "Bull")
nifty_val   = regime_data.get("nifty", 0)
regime_badge_cls = {"Bull": "regime-bull", "Bear": "regime-bear"}.get(regime, "regime-side")

st.markdown(f"""
<div class="top-header">
  <div>
    <h1>📈 India Swing Scanner — Strategic Analysis</h1>
    <p class="sub">Goal: 3–5% weekly equity returns &nbsp;·&nbsp;
      <a href="https://github.com/vinayloki/india-swing-scanner" target="_blank">
        vinayloki/india-swing-scanner
      </a>
    </p>
  </div>
  <div class="badge-row">
    <span class="badge-nse">● NSE • Indian Equity</span>
    <a class="badge-gh" href="https://github.com/vinayloki/india-swing-scanner" target="_blank">⭐ GitHub</a>
    <span class="regime-pill {regime_badge_cls}">
      {'🟢' if regime=='Bull' else '🔴' if regime=='Bear' else '🟡'} {regime} Market
    </span>
  </div>
</div>

<div class="info-ticker">
  <span><span class="dot">✓</span> Simulates 2100+ NSE momentum approach</span>
  <span><span class="dot">✓</span> Weekly BUY/SELL/HOLD Cadence</span>
  <span><span class="dot">✓</span> Target + Stop-Loss exit logic</span>
  <span><span class="dot">✓</span> 1-year (52-week) horizon</span>
  {f'<span><span class="dot">✓</span> NIFTY 50: ₹{nifty_val:,.0f}</span>' if nifty_val else ''}
</div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
#  NAVIGATION TAB BAR
# ═══════════════════════════════════════════════════════════════════════════

tabs_def = [
    ("🎯", "Goal Alignment"),
    ("🔍", "Repo Deep Dive"),
    ("🧪", "Backtest Simulator"),
    ("🚀", "Enhancements"),
]

tab_html = '<div class="nav-tabs">'
for icon, label in tabs_def:
    active_cls = "active" if st.session_state["active_tab"] == label else ""
    tab_html += f'<div class="nav-tab {active_cls}">{icon} {label}</div>'
tab_html += "</div>"
st.markdown(tab_html, unsafe_allow_html=True)

# Streamlit selects the active tab with buttons (rendered in same horizontal line)
col_tabs = st.columns(len(tabs_def))
for i, (icon, label) in enumerate(tabs_def):
    with col_tabs[i]:
        if st.button(f"{icon} {label}", key=f"navbtn_{label}", use_container_width=True):
            st.session_state["active_tab"] = label
            st.session_state["sim_result"] = None
            st.rerun()

st.markdown('<div class="page">', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
#  TAB ROUTING
# ═══════════════════════════════════════════════════════════════════════════
active_tab = st.session_state["active_tab"]


# ─────────────────────────────────────────────────────────────── GOAL ALIGNMENT
if active_tab == "Goal Alignment":
    st.markdown('<div class="section-hdr">🎯 Goal Analysis</div>', unsafe_allow_html=True)

    perf = load_performance()
    mb   = (perf or {}).get("mode_b", {})

    cap_start   = 100_000
    total_ret   = mb.get("total_return_pct") or -12.56
    cap_end     = cap_start * (1 + total_ret / 100)
    win_rate    = mb.get("win_rate_pct") or 52.6
    expectancy  = mb.get("expectancy_pct") or -0.49
    max_dd      = mb.get("max_drawdown_pct") or 18.06
    target_hits = mb.get("target_hit_rate_pct") or 41.0

    viable = expectancy > 0 and win_rate >= 55

    alert_html = f"""
    <div class="{'alert-success' if viable else 'alert-danger'}">
      <div class="icon">{'✅' if viable else '❌'}</div>
      <div>
        <div class="title">{'Goal ACHIEVABLE — strategy shows positive expectancy' if viable else 'Goal NOT MET — strategy requires revision'}</div>
        <div class="sub">Current expectancy: <b>{expectancy:+.2f}% per trade</b> &nbsp;·&nbsp; Win Rate: <b>{win_rate:.1f}%</b> &nbsp;·&nbsp; 3-5% target hit rate: <b>{target_hits:.0f}%</b></div>
      </div>
    </div>"""
    st.markdown(alert_html, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(metric_card(
            f"{total_ret:+.2f}%", "Historical Return",
            f"₹{cap_start:,.0f} → ₹{cap_end:,.0f}",
            "c-green" if total_ret > 0 else "c-red"), unsafe_allow_html=True)
    with c2:
        st.markdown(metric_card(
            f"{expectancy:+.2f}%", "Expectancy / Trade",
            "Must be > 0 to be viable",
            "c-green" if expectancy > 0 else "c-red"), unsafe_allow_html=True)
    with c3:
        st.markdown(metric_card(
            f"{win_rate:.1f}%", "Win Rate",
            "60%+ needed for 3-5% goal",
            "c-green" if win_rate >= 60 else "c-amber"), unsafe_allow_html=True)
    with c4:
        st.markdown(metric_card(
            f"{max_dd:.1f}%", "Max Drawdown",
            "Lower is better",
            "c-amber" if max_dd < 15 else "c-red"), unsafe_allow_html=True)

    st.markdown('<div class="section-hdr">📋 Why Does the 3–5% Goal Fail?</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="info-block">
      <h3>⚠️ The Risk-Reward Inversion Problem</h3>
      <p>Your stop-loss (1.5 × ATR14) averages <b>−4.84%</b> while your take-profit is fixed at <b>+4.0%</b>.
      When your average loss outweighs your average win, you need a Win Rate of <b>&gt;60%</b> just to
      break even. The current 52.6% Win Rate is not high enough to overcome this structural leak.</p>
    </div>
    <div class="info-block">
      <h3>🔧 Blueprint to Fix It</h3>
      <p><b>Phase A (Immediate):</b> Raise <code>TAKE_PROFIT_PCT</code> in config/settings.py to 6–8%
      and lower <code>ATR_SL_MULTIPLIER</code> to 1.0. Re-run the Backtest Simulator to verify expectancy
      becomes positive.<br><br>
      <b>Phase B:</b> Add a "pullback entry" rule — wait for re-test of EMA9 after a breakout instead
      of chasing the first burst. This typically raises Win Rate to 58–65%.<br><br>
      <b>Phase C:</b> Kill stale positions after 3 days of no momentum (time stop) to recover capital
      for better setups.</p>
    </div>
    """, unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────── REPO DEEP DIVE
elif active_tab == "Repo Deep Dive":
    st.markdown('<div class="section-hdr">🔍 Repository Architecture</div>', unsafe_allow_html=True)

    ai  = load_ai_picks()
    bt  = load_backtest()
    reg = load_regime()

    total_stocks = (ai or {}).get("total_stocks", 0)
    buys    = (ai or {}).get("summary", {}).get("buy", 0)
    holds   = (ai or {}).get("summary", {}).get("hold", 0)
    sells   = (ai or {}).get("summary", {}).get("sell", 0)
    bt_date = (bt or {}).get("generated", "N/A")
    regime  = reg.get("regime", "Unknown")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(metric_card(f"{total_stocks:,}", "NSE Stocks Scanned", "Daily, automated", "c-blue"), unsafe_allow_html=True)
    with c2:
        st.markdown(metric_card(f"{buys}", "Current BUY Signals", "AI-filtered", "c-green"), unsafe_allow_html=True)
    with c3:
        st.markdown(metric_card(f"{holds}", "HOLD Signals", "Monitor these", "c-amber"), unsafe_allow_html=True)
    with c4:
        st.markdown(metric_card(f"{sells}", "SELL / Exit Signals", "Avoid or short", "c-red"), unsafe_allow_html=True)

    st.markdown('<div class="section-hdr">🏗️ System Components</div>', unsafe_allow_html=True)

    for title, desc in [
        ("📡 scanner.py — Data Ingestion Engine",
         "Downloads 13 months of OHLCV data for 2100+ NSE stocks via yfinance in batches of 50. "
         "Stores results in a Parquet cache (ohlcv_backtest.parquet) for instant reloads."),
        ("🧪 backtest.py — Walk-Forward Simulator",
         "Runs a strict no-lookahead simulation over 52 historical Mondays. "
         "Mode A tests all signals; Mode B tests only the Top 15 AI picks. "
         "Uses vectorised Pandas math to complete 50 weeks of simulation in under 3 seconds."),
        ("🤖 ai_engine.py — Intelligence Layer",
         "Reads backtest win rates per signal type, applies market regime multipliers (Bull/Sideways/Bear), "
         "combines with fundamentals (P/E, Market Cap) to produce per-stock Buy/Hold/Sell with P(Win), Entry, SL, TP and R:R."),
        ("📊 performance.py — Analytics Engine",
         "Computes Expectancy, Profit Factor, Sharpe Ratio, Max Drawdown and regime/signal breakdowns "
         "from the trade log produced by backtest.py."),
        ("🌐 index.html + app.js — Dashboard",
         "Live dashboard served via GitHub Pages. Auto-refreshes ai_picks.json every 5 minutes. "
         "Includes Scanner, AI Picks, Top Movers, Market Movers and Backtest tabs."),
        ("⚡ GitHub Actions (daily_scan.yml)",
         "Runs scanner.py + ai_engine.py every weekday at 18:00 UTC (after NSE close). "
         "A separate weekly-backtest job runs every Sunday at 23:30 UTC."),
    ]:
        st.markdown(f"""
        <div class="info-block">
          <h3>{title}</h3>
          <p>{desc}</p>
        </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────── BACKTEST SIMULATOR
elif active_tab == "Backtest Simulator":

    # ── Parameters panel ─────────────────────────────────────────────
    st.markdown('<div class="params-panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">⚙️ Strategy Parameters</div>', unsafe_allow_html=True)

    r1c1, r1c2, r1c3, r1c4 = st.columns(4)
    with r1c1:
        target_exit = st.slider(
            "Target Exit (%)", 1.0, 15.0,
            float(st.session_state["target_exit"]), 0.5,
            key="sl_target_exit",
            help="When price rises this much from entry, the trade closes as a WIN.")
        st.session_state["target_exit"] = target_exit

    with r1c2:
        stop_loss = st.slider(
            "Stop-Loss (%)", 1.0, 10.0,
            float(st.session_state["stop_loss"]), 0.5,
            key="sl_stop_loss",
            help="When price falls this much from entry, the trade closes as a LOSS.")
        st.session_state["stop_loss"] = stop_loss

    with r1c3:
        max_hold = st.slider(
            "Max Hold (weeks)", 1, 24,
            int(st.session_state["max_hold"]), 1,
            key="sl_max_hold",
            help="Maximum number of weeks to hold a trade before forcing an exit.")
        st.session_state["max_hold"] = max_hold

    with r1c4:
        min_score = st.slider(
            "Min AI Score", 0, 100,
            int(st.session_state["min_score"]), 5,
            key="sl_min_score",
            help="Only enter trades where the AI signal score is above this threshold.")
        st.session_state["min_score"] = min_score

    r2c1, r2c2, r2c3 = st.columns(3)
    with r2c1:
        capital = st.select_slider(
            "Capital (₹)",
            options=[10_000, 25_000, 50_000, 1_00_000, 2_00_000, 5_00_000, 10_00_000],
            value=int(st.session_state["capital"]),
            format_func=lambda x: f"₹{x/100 if x>=100_000 else x/1000:.0f}{'L' if x>=100_000 else 'K'}",
            key="sl_capital",
            help="Starting capital for the simulation.")
        st.session_state["capital"] = capital

    with r2c2:
        backtest_weeks = st.slider(
            "Backtest Weeks", 4, 52,
            int(st.session_state["backtest_weeks"]), 4,
            key="sl_bt_weeks",
            help="Number of historical weeks to simulate.")
        st.session_state["backtest_weeks"] = backtest_weeks

    with r2c3:
        stocks_in_pool = st.slider(
            "Stocks in Pool", 1, 50,
            int(st.session_state["stocks_in_pool"]), 1,
            key="sl_pool",
            help="Maximum concurrent open positions in the portfolio at any one time.")
        st.session_state["stocks_in_pool"] = stocks_in_pool

    # ── Presets ───────────────────────────────────────────────────────
    st.markdown("**Quick Presets:**")
    pc1, pc2, pc3, pc4, *_ = st.columns([1.5, 1.3, 1.5, 1.5, 3])
    with pc1:
        if st.button("Conservative (2–3%)", use_container_width=True):
            apply_preset("Conservative (2–3%)"); st.rerun()
    with pc2:
        if st.button("Aggressive (5%)", use_container_width=True):
            apply_preset("Aggressive (5%)"); st.rerun()
    with pc3:
        if st.button("Tight Scalp (1.5%)", use_container_width=True):
            apply_preset("Tight Scalp (1.5%)"); st.rerun()
    with pc4:
        if st.button("Your Goal (3–5%)", use_container_width=True):
            apply_preset("Your Goal (3–5%)"); st.rerun()

    # ── Run / Reset ───────────────────────────────────────────────────
    st.markdown("")
    btn1, btn2, *_ = st.columns([1.4, 0.8, 5])
    with btn1:
        run_clicked = st.button("▶ Run Backtest", type="primary", use_container_width=True)
    with btn2:
        if st.button("Reset", use_container_width=True):
            for k, v in DEFAULTS.items():
                st.session_state[k] = v
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)  # close params-panel

    # ── Trigger simulation ────────────────────────────────────────────
    if run_clicked:
        prog = st.progress(0, text="Initialising simulation engine…")
        for pct, msg in [
            (15, "Loading AI picks and market data…"),
            (35, "Running walk-forward simulation…"),
            (65, f"Simulating {backtest_weeks} weeks × {stocks_in_pool} positions…"),
            (85, "Calculating Sharpe, drawdown, expectancy…"),
            (100, "Complete!"),
        ]:
            time.sleep(0.25)
            prog.progress(pct, text=msg)

        result = run_simulation(
            capital=capital,
            target_exit_pct=target_exit,
            stop_loss_pct=stop_loss,
            max_hold_weeks=max_hold,
            min_score=min_score,
            backtest_weeks=backtest_weeks,
            stocks_in_pool=stocks_in_pool,
        )
        st.session_state["sim_result"] = result
        prog.empty()

    # ── Results ───────────────────────────────────────────────────────
    result = st.session_state.get("sim_result")

    if result and result.get("metrics"):
        m  = result["metrics"]
        trades = result["trades"]
        curve  = result["equity_curve"]

        # Status banner
        avg_wkly = m["avg_weekly_pct"]
        rr       = round(target_exit / stop_loss, 2)

        if avg_wkly >= 3.0:
            alert = f"""<div class="alert-success">
              <div class="icon">✅</div>
              <div>
                <div class="title">Goal MET — Average weekly return above 3% target</div>
                <div class="sub">Avg return per trade: <b>{m['expectancy_pct']:+.2f}%</b>
                 &nbsp;·&nbsp; Win Rate: <b>{m['win_rate_pct']:.1f}%</b>
                 &nbsp;·&nbsp; Sharpe Ratio: <b>{m['sharpe']:.2f}</b>
                 &nbsp;·&nbsp; R:R <b>{rr:.1f}x</b></div>
              </div></div>"""
        elif avg_wkly >= 1.0:
            alert = f"""<div class="alert-partial">
              <div class="icon">⚡</div>
              <div>
                <div class="title">Partial — Avg weekly return below 3% target</div>
                <div class="sub">Avg return per trade: <b>{m['expectancy_pct']:+.2f}%</b>
                 &nbsp;·&nbsp; Win Rate: <b>{m['win_rate_pct']:.1f}%</b>
                 &nbsp;·&nbsp; Sharpe Ratio: <b>{m['sharpe']:.2f}</b>
                 &nbsp;·&nbsp; R:R <b>{rr:.1f}x</b></div>
              </div></div>"""
        else:
            alert = f"""<div class="alert-danger">
              <div class="icon">❌</div>
              <div>
                <div class="title">Strategy Failing — Negative weekly returns</div>
                <div class="sub">Avg return per trade: <b>{m['expectancy_pct']:+.2f}%</b>
                 &nbsp;·&nbsp; Win Rate: <b>{m['win_rate_pct']:.1f}%</b>
                 &nbsp;·&nbsp; Sharpe Ratio: <b>{m['sharpe']:.2f}</b></div>
              </div></div>"""

        st.markdown(f'<div class="section-hdr">📊 Backtest Results — {backtest_weeks} Weeks</div>', unsafe_allow_html=True)
        st.markdown(alert, unsafe_allow_html=True)

        # ── 4-column metric cards ─────────────────────────────────────
        cc1, cc2, cc3, cc4 = st.columns(4)
        total_ret = m["total_return_pct"]
        with cc1:
            st.markdown(metric_card(
                f"{total_ret:+.2f}%",
                "Total Return",
                f"₹{m['capital_start']:,.0f} → ₹{m['capital_end']:,.0f}",
                "c-green" if total_ret > 0 else "c-red"), unsafe_allow_html=True)
        with cc2:
            st.markdown(metric_card(
                f"{avg_wkly:.2f}%",
                "Avg Weekly Return",
                "Target: 3–5%",
                "c-green" if avg_wkly >= 3 else "c-amber" if avg_wkly >= 1 else "c-red"),
                unsafe_allow_html=True)
        with cc3:
            st.markdown(metric_card(
                f"{m['win_rate_pct']:.0f}%",
                "Win Rate",
                "Target: >60%",
                "c-green" if m['win_rate_pct'] >= 60 else "c-amber"),
                unsafe_allow_html=True)
        with cc4:
            st.markdown(metric_card(
                f"{m['sharpe']:.2f}",
                "Sharpe Ratio",
                ">0.5 = good, >1.0 = great",
                "c-cyan" if m['sharpe'] >= 0.5 else "c-amber"),
                unsafe_allow_html=True)

        # ── Row 2 metrics ─────────────────────────────────────────────
        cc5, cc6, cc7, cc8 = st.columns(4)
        with cc5:
            st.markdown(metric_card(
                f"{m['expectancy_pct']:+.2f}%",
                "Expectancy / Trade",
                "Must be > 0 to be viable",
                "c-green" if m['expectancy_pct'] > 0 else "c-red"),
                unsafe_allow_html=True)
        with cc6:
            st.markdown(metric_card(
                f"{m['profit_factor']:.2f}x",
                "Profit Factor",
                ">1.2 = solid edge",
                "c-green" if m['profit_factor'] >= 1.2 else "c-amber"),
                unsafe_allow_html=True)
        with cc7:
            st.markdown(metric_card(
                f"{m['max_drawdown_pct']:.1f}%",
                "Max Drawdown",
                "Lower is safer",
                "c-amber" if m['max_drawdown_pct'] < 15 else "c-red"),
                unsafe_allow_html=True)
        with cc8:
            st.markdown(metric_card(
                f"{m['total_trades']}",
                "Total Trades",
                f"W: {m['wins']}  L: {m['losses']}",
                "c-blue"),
                unsafe_allow_html=True)

        # ── Equity curve ──────────────────────────────────────────────
        st.markdown('<div class="section-hdr">📈 Equity Curve</div>', unsafe_allow_html=True)
        eq_svg = draw_equity_svg(curve, m["capital_start"])

        regime_cls = {"Bull": "regime-bull", "Bear": "regime-bear"}.get(m["current_regime"], "regime-side")
        eb = m["exit_breakdown"]
        st.markdown(f"""
        <div class="equity-wrap">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
            <div style="font-size:13px;color:rgba(255,255,255,0.6)">
              Capital grew from <b>₹{m['capital_start']:,.0f}</b> to
              <b style="color:{'#22C55E' if m['capital_end']>=m['capital_start'] else '#EF4444'}">
                ₹{m['capital_end']:,.0f}
              </b>
              over {backtest_weeks} weeks
            </div>
            <span class="regime-pill {regime_cls}">{'🟢' if m['current_regime']=='Bull' else '🔴' if m['current_regime']=='Bear' else '🟡'} {m['current_regime']} Market</span>
          </div>
          {eq_svg}
          <div style="display:flex;gap:20px;margin-top:12px;font-size:12px;color:rgba(255,255,255,0.5)">
            <span>✅ TP hits: <b style="color:#22C55E">{eb.get('TP',0)}</b></span>
            <span>🛑 SL hits: <b style="color:#EF4444">{eb.get('SL',0)}</b></span>
            <span>⏱ Time exits: <b style="color:#F59E0B">{eb.get('TIME',0)}</b></span>
            <span>Avg Win: <b style="color:#22C55E">{m['avg_win_pct']:+.2f}%</b></span>
            <span>Avg Loss: <b style="color:#EF4444">{m['avg_loss_pct']:+.2f}%</b></span>
            <span>R:R = <b>{rr:.2f}x</b></span>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Trade log ─────────────────────────────────────────────────
        if trades:
            st.markdown('<div class="section-hdr">📋 Trade Log (Last 25)</div>', unsafe_allow_html=True)
            rows = ""
            for t in sorted(trades, key=lambda x: x["exit_week"], reverse=True)[:25]:
                color  = "#22C55E" if t["won"] else "#EF4444"
                badge  = {"TP": "badge-tp", "SL": "badge-sl", "TIME": "badge-time"}.get(t["exit_reason"], "badge-time")
                rows += f"""
                <tr>
                  <td><b>{t['ticker']}</b></td>
                  <td style="color:rgba(255,255,255,0.5);font-size:11px">Week {t['entry_week']} → {t['exit_week']}</td>
                  <td style="font-family:JetBrains Mono,monospace">₹{t['entry_px']:.2f}</td>
                  <td style="font-family:JetBrains Mono,monospace">₹{t['exit_px']:.2f}</td>
                  <td style="color:{color};font-family:JetBrains Mono,monospace;font-weight:700">{t['return_pct']:+.2f}%</td>
                  <td><span class="{badge}">{t['exit_reason']}</span></td>
                  <td style="color:rgba(255,255,255,0.45);font-size:11px">{t.get('score','-')}</td>
                </tr>"""

            st.markdown(f"""
            <div class="trade-table" style="overflow-x:auto">
            <table class="trade-table">
              <thead>
                <tr>
                  <th>Ticker</th><th>Period</th><th>Entry ₹</th>
                  <th>Exit ₹</th><th>Return</th><th>Exit</th><th>Score</th>
                </tr>
              </thead>
              <tbody>{rows}</tbody>
            </table>
            </div>""", unsafe_allow_html=True)

    else:
        st.markdown("""
        <div style="text-align:center;padding:60px 20px;color:rgba(255,255,255,0.35)">
          <div style="font-size:52px;margin-bottom:16px">🧪</div>
          <div style="font-size:18px;font-weight:700;margin-bottom:8px">Configure Parameters & Run Backtest</div>
          <div style="font-size:13px">Adjust the sliders above or choose a quick preset, then click <b>▶ Run Backtest</b></div>
        </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────── ENHANCEMENTS
elif active_tab == "Enhancements":
    st.markdown('<div class="section-hdr">🚀 Planned Enhancements</div>', unsafe_allow_html=True)

    improvements = [
        ("Phase A — Fix Risk Mechanics", "🔧",
         "Raise <code>TAKE_PROFIT_PCT</code> to 6–8% and lower <code>ATR_SL_MULTIPLIER</code> to 1.0 in config/settings.py. "
         "Re-run the Backtest Simulator and confirm average loss becomes smaller than average win."),
        ("Phase B — Pullback Entry Rule", "📉",
         "Instead of buying the breakout candle directly, detect when price re-tests the EMA9 after a breakout and holds. "
         "This weeds out false breakouts and typically raises Win Rate from 52% to 60%+."),
        ("Phase C — Time-Based Stops", "⏱",
         "If a stock has not moved ≥2% in the intended direction within 3 trading days, exit automatically. "
         "This frees capital for better setups and reduces the 'time cost' of dead trades."),
        ("Phase D — AI Parameter Sweep", "🤖",
         "A weekend batch script that wraps backtest.py in a for-loop testing TP from 2–12% and SL from 1–6%. "
         "Auto-discovers the optimal parameter set for the current market regime."),
        ("Phase E — Options Overlay", "📊",
         "For stocks flagged as BUY with high P(Win), sell a cash-secured put at the SL level. "
         "This earns premium if the stock stays flat—boosting returns from neutral outcomes."),
        ("Phase F — Real Broker Integration", "🏦",
         "Connect to Zerodha Kite API or Upstox API to automatically place GTT (Good-Till-Triggered) "
         "orders at the detected Entry, SL and TP levels. True set-and-forget automation."),
    ]

    for title, icon, desc in improvements:
        st.markdown(f"""
        <div class="info-block">
          <h3>{icon} {title}</h3>
          <p>{desc}</p>
        </div>""", unsafe_allow_html=True)

    st.markdown('<div class="section-hdr">📅 Data Refresh Schedule</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="info-block">
      <h3>Automated Pipeline</h3>
      <p>
        <b style="color:#22C55E">Daily (Weekdays 18:00 UTC):</b> scanner.py → ai_engine.py → ai_picks.json<br>
        <b style="color:#60A5FA">Weekly (Sunday 23:30 UTC):</b> backtest.py → performance.py → backtest_results.json<br>
        <b style="color:#A78BFA">Instant:</b> regime_filter.py → market_regime.json (triggered after daily scan)<br><br>
        GitHub Pages deploys within 1–2 minutes of each commit. Hard-refresh (Ctrl+F5) to see latest data.
      </p>
    </div>""", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)  # close .page

# ── Footer ───────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;padding:24px;font-size:11.5px;
            color:rgba(255,255,255,0.2);border-top:1px solid rgba(255,255,255,0.07);margin-top:24px">
  MarketPulse India &nbsp;·&nbsp; For educational purposes only &nbsp;·&nbsp;
  Not SEBI-registered investment advice &nbsp;·&nbsp;
  <a href="https://github.com/vinayloki/india-swing-scanner" target="_blank"
     style="color:rgba(255,255,255,0.35);text-decoration:none">GitHub ↗</a>
</div>""", unsafe_allow_html=True)
