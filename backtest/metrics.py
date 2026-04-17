"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  MarketPulse India — Prediction Accuracy Metrics                             ║
║                                                                              ║
║  Computes all accuracy and performance statistics from walk-forward          ║
║  prediction results, including benchmark comparisons.                        ║
║                                                                              ║
║  Outputs:                                                                    ║
║    overall classification accuracy                                           ║
║    per-class precision (BUY / SELL / HOLD)                                  ║
║    win rate (return > 0 for predicted BUY/SELL)                             ║
║    average return per predicted class                                        ║
║    3×3 confusion matrix                                                      ║
║    benchmark comparison (vs buy-and-hold, equal-weight)                     ║
║    monthly accuracy timeline                                                 ║
║    weekly log (last N weeks)                                                 ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import logging
import math
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional

import numpy as np
import pandas as pd

log = logging.getLogger("marketpulse.backtest.metrics")

LABELS = ["BUY", "SELL", "HOLD"]


# ── Core accuracy metrics ─────────────────────────────────────────────────────

def compute_accuracy_metrics(results: list[dict]) -> dict:
    """
    Compute classification accuracy metrics from walk-forward prediction records.

    Args:
        results: List returned by backtest/walk_forward.run_prediction_backtest()

    Returns:
        dict with accuracy stats, confusion matrix, win rate, avg returns, etc.
    """
    if not results:
        return _empty_metrics()

    df = pd.DataFrame(results)

    # ── Overall accuracy ───────────────────────────────────────────────────
    total          = len(df)
    correct        = df["correct"].sum()
    overall_acc    = round(correct / total * 100, 2) if total else 0

    # ── Per-class precision ────────────────────────────────────────────────
    precision = {}
    recall    = {}
    for cls in LABELS:
        predicted_as_cls = df[df["predicted"] == cls]
        n_pred = len(predicted_as_cls)
        if n_pred:
            n_correct = predicted_as_cls["correct"].sum()
            precision[cls] = round(n_correct / n_pred * 100, 2)
        else:
            precision[cls] = None

        actually_cls = df[df["actual"] == cls]
        n_actual = len(actually_cls)
        if n_actual:
            n_tp = ((df["predicted"] == cls) & (df["actual"] == cls)).sum()
            recall[cls] = round(n_tp / n_actual * 100, 2)
        else:
            recall[cls] = None

    # ── Win rate (when it profits) ─────────────────────────────────────────
    # BUY: win if actual return > 0
    # SELL: win if actual return < 0
    buy_trades  = df[df["predicted"] == "BUY"]
    sell_trades = df[df["predicted"] == "SELL"]
    hold_trades = df[df["predicted"] == "HOLD"]

    buy_wr  = _win_rate(buy_trades,  direction="long")
    sell_wr = _win_rate(sell_trades, direction="short")

    # ── Average returns per class ──────────────────────────────────────────
    avg_ret = {}
    for cls in LABELS:
        cls_df = df[df["predicted"] == cls]
        if len(cls_df):
            # For SELL predictions, invert return sign (shorting)
            rets = cls_df["return_pct"] * (-1 if cls == "SELL" else 1)
            avg_ret[cls] = round(float(rets.mean()), 3)
        else:
            avg_ret[cls] = None

    # ── Confusion matrix ──────────────────────────────────────────────────
    cm = {pred: {act: 0 for act in LABELS} for pred in LABELS}
    for _, row in df.iterrows():
        p = row["predicted"]
        a = row["actual"]
        if p in cm and a in LABELS:
            cm[p][a] += 1

    # ── Monthly accuracy timeline ──────────────────────────────────────────
    df["month"] = pd.to_datetime(df["week"]).dt.to_period("M").astype(str)
    monthly = (
        df.groupby("month")
          .agg(accuracy_pct=("correct", lambda x: round(x.mean() * 100, 1)),
               trades=("correct", "count"))
          .reset_index()
          .rename(columns={"month": "month"})
    )
    accuracy_timeline = monthly.to_dict(orient="records")

    # ── Confidence calibration (avg accuracy per confidence band) ─────────
    df["conf_band"] = pd.cut(df["confidence"], bins=[0,40,50,60,70,80,100],
                             labels=["<40","40-50","50-60","60-70","70-80",">80"])
    conf_cal = (
        df.groupby("conf_band", observed=True)
          .agg(acc=("correct", lambda x: round(x.mean() * 100, 1)),
               n=("correct", "count"))
          .reset_index()
          .to_dict(orient="records")
    )

    # ── Weekly log (last 100 records, latest first) ────────────────────────
    log_cols = ["week", "ticker", "predicted", "actual", "return_pct", "correct", "confidence"]
    weekly_log = (
        df.sort_values("week", ascending=False)
          .head(200)[log_cols]
          .to_dict(orient="records")
    )

    # ── Summary ───────────────────────────────────────────────────────────
    total_non_hold = len(buy_trades) + len(sell_trades)
    overall_win_rate = None
    if total_non_hold:
        buy_wins  = (buy_trades["return_pct"]  > 0).sum()
        sell_wins = (sell_trades["return_pct"] < 0).sum()
        overall_win_rate = round((buy_wins + sell_wins) / total_non_hold * 100, 2)

    return {
        "total_predictions":    total,
        "correct_predictions":  int(correct),
        "overall_accuracy_pct": overall_acc,
        "precision": {
            "buy_pct":  precision.get("BUY"),
            "sell_pct": precision.get("SELL"),
            "hold_pct": precision.get("HOLD"),
        },
        "recall": {
            "buy_pct":  recall.get("BUY"),
            "sell_pct": recall.get("SELL"),
            "hold_pct": recall.get("HOLD"),
        },
        "win_rate": {
            "buy_pct":     buy_wr,
            "sell_pct":    sell_wr,
            "overall_pct": overall_win_rate,
        },
        "avg_return_per_prediction": {
            "buy_pct":  avg_ret.get("BUY"),
            "sell_pct": avg_ret.get("SELL"),
            "hold_pct": avg_ret.get("HOLD"),
        },
        "class_counts": {
            "buy":  len(buy_trades),
            "sell": len(sell_trades),
            "hold": len(hold_trades),
        },
        "confusion_matrix":     cm,
        "accuracy_timeline":    accuracy_timeline,
        "confidence_calibration": conf_cal,
        "weekly_log":           weekly_log,
    }


def _win_rate(df_cls: pd.DataFrame, direction: str) -> Optional[float]:
    if len(df_cls) == 0:
        return None
    if direction == "long":
        wins = (df_cls["return_pct"] > 0).sum()
    else:
        wins = (df_cls["return_pct"] < 0).sum()
    return round(wins / len(df_cls) * 100, 2)


# ── Benchmark comparison ──────────────────────────────────────────────────────

def compute_benchmarks(
    results: list[dict],
    nifty_weekly_returns: Optional[pd.Series] = None,
) -> dict:
    """
    Compare prediction-based P&L vs buy-and-hold and equal-weight benchmarks.

    The prediction strategy: take BUY positions, short SELL, skip HOLD.
    Each position = equal weight, 1 week hold.

    Args:
        results             : Walk-forward prediction records
        nifty_weekly_returns: Optional NIFTY 50 weekly return series (for buy-and-hold)

    Returns:
        dict with strategy vs benchmark return comparison.
    """
    if not results:
        return {}

    df = pd.DataFrame(results)

    # ── Prediction strategy ────────────────────────────────────────────────
    tradeable = df[df["predicted"].isin(["BUY", "SELL"])].copy()
    tradeable["strategy_ret"] = np.where(
        tradeable["predicted"] == "BUY",
        tradeable["return_pct"],
        -tradeable["return_pct"],   # short SELL
    )

    # Weekly portfolio return = mean of all active trades that week
    weekly_strategy = (
        tradeable.groupby("week")["strategy_ret"].mean()
        if len(tradeable) else pd.Series(dtype=float)
    )

    # ── Equal-weight benchmark ─────────────────────────────────────────────
    all_weekly_eq = (
        df.groupby("week")["return_pct"].mean()
        if len(df) else pd.Series(dtype=float)
    )

    # ── Compute cumulative returns ─────────────────────────────────────────
    cum_strategy = _cumulative_return(weekly_strategy)
    cum_eq       = _cumulative_return(all_weekly_eq)

    # ── Sharpe-like ratio (weekly returns, annualized) ─────────────────────
    sharpe_strategy = _sharpe(weekly_strategy)
    sharpe_eq       = _sharpe(all_weekly_eq)

    # ── NIFTY buy-and-hold ─────────────────────────────────────────────────
    if nifty_weekly_returns is not None:
        # Align to same weeks
        common = weekly_strategy.index.intersection(nifty_weekly_returns.index)
        cum_nifty   = _cumulative_return(nifty_weekly_returns.loc[common])
        sharpe_nifty = _sharpe(nifty_weekly_returns.loc[common])
    else:
        cum_nifty    = None
        sharpe_nifty = None

    outperformance = (
        round(cum_strategy - cum_eq, 2) if cum_strategy is not None and cum_eq is not None
        else None
    )

    # ── Binomial significance vs 50% random ───────────────────────────────
    total_trades = len(tradeable)
    wins = (tradeable["strategy_ret"] > 0).sum() if total_trades else 0
    sig_note = _binomial_significance(wins, total_trades)

    return {
        "prediction_strategy": {
            "total_return_pct": cum_strategy,
            "sharpe_like":      sharpe_strategy,
            "n_trades":         total_trades,
        },
        "equal_weight_benchmark": {
            "total_return_pct": cum_eq,
            "sharpe_like":      sharpe_eq,
        },
        "buy_and_hold_nifty": {
            "total_return_pct": cum_nifty,
            "sharpe_like":      sharpe_nifty,
        },
        "outperformance_vs_eq_pct": outperformance,
        "statistical_significance": sig_note,
    }


def _cumulative_return(weekly_rets: pd.Series) -> Optional[float]:
    if weekly_rets.empty:
        return None
    # product of (1 + r/100) - 1
    cum = (1 + weekly_rets / 100).prod() - 1
    return round(float(cum) * 100, 2)


def _sharpe(weekly_rets: pd.Series, risk_free_annual: float = 6.5) -> Optional[float]:
    """Annualized Sharpe assuming 52 weekly returns per year."""
    if weekly_rets.empty or weekly_rets.std() == 0:
        return None
    rf_weekly  = (1 + risk_free_annual / 100) ** (1 / 52) - 1
    excess     = weekly_rets / 100 - rf_weekly
    sharpe     = excess.mean() / excess.std() * math.sqrt(52)
    return round(float(sharpe), 3)


def _binomial_significance(wins: int, n: int, p0: float = 0.50) -> str:
    """
    Approximate z-test: is win rate significantly > 50% (random)?
    Returns a plain-English note.
    """
    if n < 30:
        return "Insufficient trades for significance test"
    import math
    se     = math.sqrt(p0 * (1 - p0) / n)
    z      = (wins / n - p0) / se
    # Approximate p-value from z
    # p < 0.05 → z > 1.645  (one-tailed)
    if z > 2.33:
        return f"Statistically significant (p<0.01) — model has real edge (z={z:.2f})"
    elif z > 1.645:
        return f"Borderline significant (p<0.05) — likely real edge (z={z:.2f})"
    elif z > 0:
        return f"Positive but not significant yet (z={z:.2f}) — need more data"
    else:
        return f"No statistical edge detected (z={z:.2f})"


# ── Fallback empty structure ──────────────────────────────────────────────────

def _empty_metrics() -> dict:
    return {
        "total_predictions": 0,
        "correct_predictions": 0,
        "overall_accuracy_pct": 0,
        "precision": {"buy_pct": None, "sell_pct": None, "hold_pct": None},
        "recall":    {"buy_pct": None, "sell_pct": None, "hold_pct": None},
        "win_rate":  {"buy_pct": None, "sell_pct": None, "overall_pct": None},
        "avg_return_per_prediction": {"buy_pct": None, "sell_pct": None, "hold_pct": None},
        "class_counts": {"buy": 0, "sell": 0, "hold": 0},
        "confusion_matrix": {l: {a: 0 for a in LABELS} for l in LABELS},
        "accuracy_timeline": [],
        "confidence_calibration": [],
        "weekly_log": [],
    }
