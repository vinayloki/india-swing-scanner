"""
╔══════════════════════════════════════════════════════════════════════════╗
║  MarketPulse India — AI EOD Intelligence Engine                         ║
║                                                                          ║
║  Reads: scan_results/full_summary.json  (2100+ stocks, 1W-12M returns)  ║
║         scan_results/fundamentals.json  (P/E, sector, mcap for ~85)     ║
║  Writes: scan_results/ai_picks.json                                      ║
║                                                                          ║
║  Runs standalone — no network calls, uses existing scan data.            ║
║  Add to GitHub Actions after scanner.py for fully automated AI picks.    ║
╚══════════════════════════════════════════════════════════════════════════╝
"""

import json
import sys
import math
from datetime import datetime
from pathlib import Path

# Fix Windows console encoding for Unicode / box-drawing characters
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ── Paths ─────────────────────────────────────────────────────────────────
OUTPUT_DIR     = Path("scan_results")
FULL_SUMMARY   = OUTPUT_DIR / "full_summary.json"
FUNDAMENTALS   = OUTPUT_DIR / "fundamentals.json"
AI_PICKS_OUT   = OUTPUT_DIR / "ai_picks.json"

# ── Timeframe weights for scoring ─────────────────────────────────────────
# More recent = higher weight. Longer = confirms structural trend.
TF_WEIGHTS = {
    "1W":  0.10,   # very short — noise possible
    "2W":  0.15,
    "1M":  0.25,   # primary signal
    "3M":  0.25,   # confirms trend
    "6M":  0.15,
    "12M": 0.10,
}

TF_KEYS = list(TF_WEIGHTS.keys())

# ── Thresholds ────────────────────────────────────────────────────────────
STRONG_GAIN  =  8.0   # % — strong positive in a timeframe
WEAK_GAIN    =  2.0   # % — mild positive
STRONG_LOSS  = -8.0   # % — strong negative
WEAK_LOSS    = -2.0   # % — mild negative

# Min % of available timeframes that must have data
MIN_TF_COVERAGE = 0.5  # at least 3 of 6


def load_data():
    """Load full_summary.json and fundamentals.json."""
    if not FULL_SUMMARY.exists():
        print(f"ERROR: {FULL_SUMMARY} not found. Run scanner.py first.")
        sys.exit(1)

    with open(FULL_SUMMARY, encoding="utf-8") as f:
        full = json.load(f)
    stocks = full.get("stocks", [])
    generated = full.get("generated", "Unknown")

    fund_map = {}
    if FUNDAMENTALS.exists():
        with open(FUNDAMENTALS, encoding="utf-8") as f:
            fj = json.load(f)
        for s in fj.get("stocks", []):
            if s.get("s"):
                fund_map[s["s"]] = s

    print(f"✅ Loaded {len(stocks)} stocks · Generated: {generated}")
    print(f"✅ Fundamentals available for {len(fund_map)} stocks")
    return stocks, fund_map, generated


def weighted_score(stock: dict) -> tuple[float, int]:
    """
    Compute a weighted momentum score in range [-100, +100].
    Returns (score, available_tf_count).
    """
    total_weight = 0.0
    weighted_sum = 0.0
    available    = 0

    for tf, w in TF_WEIGHTS.items():
        val = stock.get(tf)
        if val is None:
            continue
        available += 1
        total_weight += w
        # Normalize: cap at ±50% so extreme moves don't dominate
        capped = max(-50.0, min(50.0, val))
        # Scale: +50% → +100 pts, -50% → -100 pts
        weighted_sum += (capped / 50.0) * 100 * w

    if total_weight == 0:
        return 0.0, 0

    # Normalize to account for missing timeframes
    score = weighted_sum / total_weight
    return round(score, 2), available


def classify_trend(stock: dict) -> tuple[str, str]:
    """
    Classify trend direction based on timeframe pattern.
    Returns (trend_code, trend_label): 'up'/'down'/'sideways'
    """
    vals = {tf: stock.get(tf) for tf in TF_KEYS}
    available = [(tf, v) for tf, v in vals.items() if v is not None]

    if len(available) < 2:
        return "sideways", "→ Sideways"

    positives = sum(1 for _, v in available if v > WEAK_GAIN)
    negatives = sum(1 for _, v in available if v < WEAK_LOSS)
    total     = len(available)

    # Strong uptrend: majority positive AND recent (1M) positive
    if positives >= math.ceil(total * 0.6) and (vals.get("1M") or 0) > 0:
        return "up", "↑ Uptrend"

    # Strong downtrend: majority negative AND recent (1M) negative
    if negatives >= math.ceil(total * 0.6) and (vals.get("1M") or 0) < 0:
        return "down", "↓ Downtrend"

    return "sideways", "→ Sideways"


def build_reasons_and_risks(stock: dict, fund: dict, score: float,
                            trend: str, rec: str) -> tuple[list, list]:
    """Generate plain-English bullet reasons and risk warnings."""
    reasons = []
    risks   = []
    vals    = {tf: stock.get(tf) for tf in TF_KEYS}

    # ── Trend-based reasons ────────────────────────────────────────
    if trend == "up":
        reasons.append("Uptrend confirmed — price gaining across multiple timeframes")
        if (vals.get("3M") or 0) > 15:
            reasons.append(f"Strong 3-month momentum: +{vals['3M']:.1f}%")
        if (vals.get("12M") or 0) > 20:
            reasons.append(f"Solid 12-month trend: +{vals['12M']:.1f}%")
    elif trend == "down":
        reasons.append("Downtrend confirmed — price declining across multiple timeframes")
        if (vals.get("3M") or 0) < -15:
            reasons.append(f"Persistent selling in 3M: {vals['3M']:.1f}%")
    else:
        reasons.append("Price consolidating — no clear directional trend yet")

    # ── Recent momentum ────────────────────────────────────────────
    r1w  = vals.get("1W")
    r1m  = vals.get("1M")
    r3m  = vals.get("3M")
    r12m = vals.get("12M")

    if r1w is not None:
        if r1w > 10:
            reasons.append(f"Strong short-term breakout momentum: +{r1w:.1f}% this week")
        elif r1w < -10:
            risks.append(f"Sharp recent selloff: {r1w:.1f}% this week — monitor support")

    if r1m is not None and r3m is not None:
        if r1m > 0 and r3m > 0 and r1m < r3m * 0.3:
            risks.append("Recent acceleration slowing vs 3M trend — momentum may be fading")
        elif r1m > r3m and r1m > 0 and r3m > 0:
            reasons.append("Recent month outperforming 3M trend — momentum accelerating")

    if r12m is not None and abs(r12m) > 100:
        if r12m > 0:
            reasons.append(f"Multibagger in 12 months: +{r12m:.1f}%")
        else:
            risks.append(f"Significant 12M drawdown: {r12m:.1f}% — value trap risk")

    # ── Fundamental reasons ────────────────────────────────────────
    pe   = fund.get("pe")
    dy   = fund.get("dy")
    mcap = fund.get("mcap")
    sect = fund.get("sector") or fund.get("ind")

    if pe is not None:
        if pe < 15 and rec == "buy":
            reasons.append(f"Attractive valuation: P/E {pe:.1f}x (below 15x threshold)")
        elif pe > 50:
            risks.append(f"High valuation risk: P/E {pe:.1f}x — limited margin of safety")
        elif pe > 0 and rec == "buy":
            reasons.append(f"Reasonable valuation: P/E {pe:.1f}x")

    if dy and dy > 3.0 and rec in ("buy", "hold"):
        reasons.append(f"Attractive dividend yield: {dy:.1f}% — income cushion for holders")

    if mcap:
        if mcap > 20000 and rec == "buy":
            reasons.append("Large-cap stability — high liquidity, institutional backing")
        elif mcap < 2000:
            risks.append("Small-cap liquidity risk — wider bid-ask spreads possible")

    # ── Catch-all ─────────────────────────────────────────────────
    if not reasons:
        reasons.append("EOD data analysis: no strong directional signal detected")
    if not risks:
        if rec == "buy":
            risks.append("Market-wide correction could override stock-specific trend")
        elif rec == "sell":
            risks.append("Recovery in sector could trigger short-squeeze — use stop-loss")
        else:
            risks.append("Trend breakout (up or down) could occur — wait for confirmation")

    return reasons[:5], risks[:3]


def determine_recommendation(score: float, trend: str) -> tuple[str, str, int]:
    """
    Map score + trend → (recommendation, horizon, confidence).
    recommendation: 'buy' | 'hold' | 'sell'
    horizon: human-readable string
    confidence: 0-100
    """
    abs_score = abs(score)

    # Confidence scales with score strength
    confidence = min(95, max(35, int(35 + abs_score * 0.7)))

    if score >= 20:
        rec = "buy"
        if score >= 50:
            horizon = "Short Term · 2–4 Weeks"
        elif trend == "up":
            horizon = "Medium Term · 1–2 Months"
        else:
            horizon = "Short Term · 3–4 Weeks"

    elif score <= -20:
        rec = "sell"
        if score <= -50:
            horizon = "Short Term · 2–3 Weeks"
        else:
            horizon = "Short Term · 3–5 Weeks"

    else:
        rec = "hold"
        horizon = "Medium Term · 4–6 Weeks"
        confidence = min(65, confidence)  # lower confidence for hold

    return rec, horizon, confidence


def get_cap_label(mcap_code: str, fund_mcap: float = None) -> str:
    """Return a human-readable market cap label."""
    if fund_mcap:
        if fund_mcap > 20000:
            return "Large Cap"
        elif fund_mcap > 5000:
            return "Mid Cap"
        elif fund_mcap > 500:
            return "Small Cap"
        else:
            return "Micro Cap"
    mapping = {"L": "Large Cap", "M": "Mid Cap", "S": "Small Cap"}
    return mapping.get(mcap_code, "Small Cap")


def process_stock(stock: dict, fund: dict) -> dict:
    """Process one stock → AI pick record."""
    ticker = stock["t"]
    price  = stock["c"]
    mcap_code = stock.get("m", "S")

    score, avail_tfs = weighted_score(stock)
    trend, trend_label = classify_trend(stock)
    rec, horizon, confidence = determine_recommendation(score, trend)
    reasons, risks = build_reasons_and_risks(stock, fund, score, trend, rec)

    # Direction arrow
    direction = {"up": "▲ Up", "down": "▼ Down", "sideways": "→ Neutral"}[trend]

    # Timeframe details — always include all 6
    tf_details = {}
    for tf in TF_KEYS:
        val = stock.get(tf)
        if val is None:
            tf_details[tf] = {"pct": None, "signal": "na"}
        elif val > STRONG_GAIN:
            tf_details[tf] = {"pct": round(val, 2), "signal": "strong_up"}
        elif val > WEAK_GAIN:
            tf_details[tf] = {"pct": round(val, 2), "signal": "up"}
        elif val < STRONG_LOSS:
            tf_details[tf] = {"pct": round(val, 2), "signal": "strong_down"}
        elif val < WEAK_LOSS:
            tf_details[tf] = {"pct": round(val, 2), "signal": "down"}
        else:
            tf_details[tf] = {"pct": round(val, 2), "signal": "neutral"}

    return {
        "ticker":       ticker,
        "price":        price,
        "date":         stock.get("d", ""),
        "mcap_code":    mcap_code,
        "cap_label":    get_cap_label(mcap_code, fund.get("mcap")),
        "sector":       fund.get("sector") or fund.get("ind") or "",
        "name":         fund.get("name") or ticker,
        "pe":           fund.get("pe"),
        "mcap_cr":      fund.get("mcap"),
        "div_yield":    fund.get("dy"),
        # AI output
        "recommendation": rec,
        "trend":          trend,
        "trend_label":    trend_label,
        "direction":      direction,
        "horizon":        horizon,
        "confidence":     confidence,
        "score":          score,
        "tf_details":     tf_details,
        "reasons":        reasons,
        "risks":          risks,
    }


def main():
    print("""
╔══════════════════════════════════════════════════════════════════╗
║  🤖  MarketPulse India — AI EOD Intelligence Engine              ║
║  Generating Buy/Hold/Sell for all NSE stocks...                  ║
╚══════════════════════════════════════════════════════════════════╝
""")

    stocks, fund_map, generated = load_data()

    picks = []
    skipped = 0

    for stock in stocks:
        ticker = stock.get("t", "")
        fund   = fund_map.get(ticker, {})

        # Skip if almost no timeframe data
        avail = sum(1 for tf in TF_KEYS if stock.get(tf) is not None)
        if avail < int(len(TF_KEYS) * MIN_TF_COVERAGE):
            skipped += 1
            continue

        pick = process_stock(stock, fund)
        picks.append(pick)

    # Sort: BUY by score desc, then HOLDs, then SELLs
    order = {"buy": 0, "hold": 1, "sell": 2}
    picks.sort(key=lambda p: (order[p["recommendation"]], -p["score"]))

    # Add rank within each category
    ranks = {"buy": 1, "hold": 1, "sell": 1}
    for p in picks:
        p["rank"] = ranks[p["recommendation"]]
        ranks[p["recommendation"]] += 1

    # Summary stats
    buys  = sum(1 for p in picks if p["recommendation"] == "buy")
    holds = sum(1 for p in picks if p["recommendation"] == "hold")
    sells = sum(1 for p in picks if p["recommendation"] == "sell")

    output = {
        "generated":    generated,
        "run_at":       datetime.now().strftime("%Y-%m-%d %H:%M"),
        "total_stocks": len(picks),
        "skipped":      skipped,
        "summary": {
            "buy":  buys,
            "hold": holds,
            "sell": sells,
            "avg_confidence": round(
                sum(p["confidence"] for p in picks) / len(picks), 1
            ) if picks else 0,
        },
        "picks": picks,
    }

    with open(AI_PICKS_OUT, "w", encoding="utf-8") as f:
        json.dump(output, f, separators=(",", ":"), ensure_ascii=False)

    size_kb = AI_PICKS_OUT.stat().st_size // 1024

    print(f"""
╔══════════════════════════════════════════════════════════════════╗
║  ✅  AI PICKS COMPLETE — {generated:<37} ║
╠══════════════════════════════════════════════════════════════════╣
║  Total processed : {len(picks):<46} ║
║  Skipped         : {skipped:<46} ║
║  🟢 BUY          : {buys:<46} ║
║  🟡 HOLD         : {holds:<46} ║
║  🔴 SELL         : {sells:<46} ║
║  Output          : {str(AI_PICKS_OUT):<46} ║
║  File size       : {f"{size_kb} KB":<46} ║
╚══════════════════════════════════════════════════════════════════╝
""")


if __name__ == "__main__":
    main()
