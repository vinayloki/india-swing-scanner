"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  MarketPulse India — Walk-Forward Prediction Accuracy Backtest               ║
║                                                                              ║
║  Evaluates prediction accuracy (NOT trade P&L) over historical weeks.        ║
║                                                                              ║
║  For each week T in the backtest window:                                     ║
║    1. Build features using data[:T] (strict no-lookahead)                   ║
║    2. Apply prediction model → predicted label                               ║
║    3. Compute actual T→T+1 weekly return                                    ║
║    4. Assign actual label using ATR-adjusted thresholds                      ║
║    5. Record (ticker, week, predicted, actual, return)                       ║
║                                                                              ║
║  Results feed into backtest/metrics.py for full accuracy statistics.         ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import logging
import sys
from typing import Optional

import numpy as np
import pandas as pd

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))

from prediction.features import (
    build_feature_matrix,
    resample_to_weekly,
    _atr_df,
)
from prediction.model import predict_next_week

log = logging.getLogger("marketpulse.backtest.walk_forward")

# ATR-adjusted label parameters
MIN_THRESHOLD_PCT = 2.0   # never tighter than ±2%
ATR_MULTIPLIER    = 1.5   # threshold = max(2%, ATR * 1.5)


def _assign_actual_label(ret: float, atr_pct: float, regime: str = "Bull") -> str:
    """Assign BUY/SELL/HOLD label to an actual realized return."""
    threshold = max(MIN_THRESHOLD_PCT, atr_pct * ATR_MULTIPLIER)
    # Regime adjustment: Bear → raise BUY bar, lower SELL bar
    if regime == "Bear":
        threshold += 0.5
    if ret > threshold:
        return "BUY"
    elif ret < -threshold:
        return "SELL"
    else:
        return "HOLD"


def run_prediction_backtest(
    ohlcv_daily: pd.DataFrame,
    backtest_weeks: int = 52,
    regime: str = "Bull",
    prefer_ml: bool = True,
) -> list[dict]:
    """
    Walk-forward prediction accuracy backtest.

    Args:
        ohlcv_daily   : Full daily multi-level OHLCV (from backtest.py load_ohlcv)
        backtest_weeks: How many historical weeks to evaluate
        regime        : Market regime (used in model prediction + label assignment)
        prefer_ml     : Use RF model if available, else rule-based

    Returns:
        List of dicts, one per (ticker, week) prediction made.
    """
    log.info(f"{'─'*65}")
    log.info(f"  🔁  Walk-Forward Prediction Accuracy Backtest ({backtest_weeks}w)")
    log.info(f"{'─'*65}")

    # ── Resample to weekly ─────────────────────────────────────────────────
    weekly  = resample_to_weekly(ohlcv_daily)
    close_w = weekly["Close"]
    high_w  = weekly["High"]
    low_w   = weekly["Low"]
    atr_w   = _atr_df(high_w, low_w, close_w, period=14)

    all_weeks = close_w.index
    # Need at least 60 warm-up weeks + 1 forward week
    if len(all_weeks) < 38:
        log.error("  ❌ Insufficient weekly data for backtest (need ≥38 weeks)")
        return []

    # Reserve last week — no label available for it
    # Need at least 30 warm-up weeks for EMA50/RSI stability
    usable = all_weeks[30:-1]
    if backtest_weeks < len(usable):
        usable = usable[-backtest_weeks:]

    log.info(
        f"  📅 Scanning {usable[0].date()} → {usable[-1].date()} "
        f"({len(usable)} weeks across {close_w.shape[1]} stocks)"
    )

    results: list[dict] = []
    weekly_stats = []

    for week_idx, week_t in enumerate(usable):
        # ── Strict cutoff: no data beyond week_t ──────────────────────────
        cutoff_daily = ohlcv_daily.index[ohlcv_daily.index <= week_t].max()
        if pd.isna(cutoff_daily):
            continue

        week_t_pos = list(close_w.index).index(week_t)
        week_t1    = close_w.index[week_t_pos + 1]

        # ── Build features ────────────────────────────────────────────────
        feats = build_feature_matrix(ohlcv_daily, as_of_date=cutoff_daily)
        if feats.empty:
            continue

        # ── Predict ───────────────────────────────────────────────────────
        preds = predict_next_week(feats, regime=regime, prefer_ml=prefer_ml)

        # ── Actual next-week returns ───────────────────────────────────────
        next_close  = close_w.loc[week_t1]
        curr_close  = close_w.loc[week_t]
        actual_ret  = ((next_close - curr_close) / curr_close.replace(0, float("nan"))) * 100
        atr_pct_t   = (atr_w.loc[week_t] / curr_close.replace(0, float("nan"))) * 100

        week_correct = 0
        week_total   = 0

        # ── Record each prediction ─────────────────────────────────────────
        for ticker in preds.index:
            ret = actual_ret.get(ticker)
            atr = atr_pct_t.get(ticker, 2.0)
            if pd.isna(ret) or pd.isna(atr):
                continue

            predicted  = str(preds.loc[ticker, "prediction"])
            confidence = int(preds.loc[ticker, "confidence"])
            exp_ret    = float(preds.loc[ticker, "expected_return_pct"])
            actual_lbl = _assign_actual_label(float(ret), float(atr), regime)
            correct    = predicted == actual_lbl

            week_correct += int(correct)
            week_total   += 1

            results.append({
                "week":              str(week_t.date()),
                "ticker":            ticker,
                "predicted":         predicted,
                "actual":            actual_lbl,
                "return_pct":        round(float(ret), 3),
                "expected_return_pct": exp_ret,
                "confidence":        confidence,
                "correct":           correct,
                "regime":            regime,
                "atr_pct":           round(float(atr), 3),
            })

        week_acc = (week_correct / week_total * 100) if week_total else 0
        weekly_stats.append({
            "week": str(week_t.date()), "acc": week_acc, "n": week_total
        })

        if (week_idx + 1) % 10 == 0 or (week_idx + 1) == len(usable):
            overall_correct = sum(1 for r in results if r["correct"])
            overall_total   = len(results)
            oa = overall_correct / overall_total * 100 if overall_total else 0
            log.info(
                f"  Week {week_idx+1:>3}/{len(usable)}  [{week_t.date()}]  "
                f"week_n={week_total:>5}  week_acc={week_acc:.0f}%  "
                f"overall_acc={oa:.1f}%  total={overall_total:,}"
            )

    log.info(
        f"\n  ✅ Backtest complete — {len(results):,} predictions "
        f"across {len(usable)} weeks"
    )
    return results
