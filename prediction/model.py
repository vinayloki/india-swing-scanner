"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  MarketPulse India — Prediction Model                                        ║
║                                                                              ║
║  Wraps two prediction backends:                                              ║
║    1. Rule-based  (default) — works day 1, no training required              ║
║    2. Random Forest (optional) — loaded from prediction/model.pkl            ║
║                                                                              ║
║  Both backends return the same output schema:                                ║
║    ticker, prediction (BUY/SELL/HOLD), confidence (0–100),                  ║
║    expected_return_pct, reasoning (top_features + narrative)                 ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import json
import logging
import math
import pickle
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

log = logging.getLogger("marketpulse.prediction.model")

MODEL_PATH = Path(__file__).parent / "model.pkl"
MODEL_META_PATH = Path(__file__).parent / "model_meta.json"

# ── Rule-based thresholds ─────────────────────────────────────────────────────

# Score threshold for BUY: momentum_score must exceed this
RULE_BUY_MOMENTUM_MIN  = 15.0
RULE_SELL_MOMENTUM_MAX = -15.0

# Confidence calibration constants (rule-based)
RULE_CONF_BASE   = 40
RULE_CONF_SCALE  = 0.55   # each momentum point adds this much confidence

# Regime adjustments applied to expected return estimate
REGIME_RETURN_MULT = {"Bull": 1.0, "Sideways": 0.6, "Bear": 0.3}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _build_reasoning(row: pd.Series, prediction: str, confidence: int) -> dict:
    """
    Generate top-3 feature contributions and a short narrative string.
    Contribution is a heuristic weight, not SHAP — suitable for rule-based.
    """
    features = {
        "momentum_score": row.get("momentum_score", 0),
        "rsi_14":         row.get("rsi_14", 50),
        "rsi_trend":      row.get("rsi_trend", "flat"),
        "ema_aligned":    row.get("ema_aligned", 0),
        "breakout_pct":   row.get("breakout_pct", -10),
        "vol_ratio":      row.get("vol_ratio", 1),
        "macd_sign":      row.get("macd_sign", 0),
        "rel_strength":   row.get("rel_strength", 0),
    }

    # Contribution weights (heuristic for rule-based model)
    contributions = {
        "momentum_score": min(1.0, abs(features["momentum_score"]) / 50) * 0.30,
        "rsi_14":         abs(features["rsi_14"] - 50) / 50 * 0.20,
        "ema_aligned":    float(features["ema_aligned"]) * 0.18,
        "breakout_pct":   min(1.0, abs(features["breakout_pct"]) / 5) * 0.15,
        "vol_ratio":      min(1.0, max(0, features["vol_ratio"] - 1) / 3) * 0.12,
        "rel_strength":   min(1.0, abs(features["rel_strength"]) / 20) * 0.05,
    }

    top3 = sorted(contributions.items(), key=lambda x: x[1], reverse=True)[:3]
    top_features = [
        {
            "feature":      feat,
            "value":        round(float(features.get(feat, 0)), 2)
                            if feat != "rsi_trend" else features.get(feat, "flat"),
            "contribution": round(score, 3),
        }
        for feat, score in top3
    ]

    # ── Narrative ─────────────────────────────────────────────────────────
    parts = []
    mom = float(features["momentum_score"])
    rsi = float(features["rsi_14"])
    rsi_t = features["rsi_trend"]
    ema_ok = bool(features["ema_aligned"])
    brk = float(features["breakout_pct"])
    vol = float(features["vol_ratio"])

    if prediction == "BUY":
        if mom > 20:
            parts.append(f"Strong momentum ({mom:.0f}/100)")
        if rsi_t == "rising" and 45 < rsi < 75:
            parts.append(f"RSI {rsi:.0f} rising in buy zone")
        if ema_ok:
            parts.append("EMA stack aligned bullish")
        if brk > -2:
            parts.append("Near 52W high")
        if vol > 1.5:
            parts.append(f"Volume surge {vol:.1f}×")
    elif prediction == "SELL":
        if mom < -20:
            parts.append(f"Weak momentum ({mom:.0f}/100)")
        if rsi_t == "falling" and rsi < 55:
            parts.append(f"RSI {rsi:.0f} declining")
        if not ema_ok:
            parts.append("EMA stack bearish")
        if brk < -10:
            parts.append(f"{abs(brk):.0f}% below 52W high")
    else:
        parts.append(f"Mixed signals (momentum {mom:.0f})")
        if 45 < rsi < 60:
            parts.append(f"RSI neutral at {rsi:.0f}")
        parts.append("Awaiting directional catalyst")

    narrative = " + ".join(parts[:3]) if parts else "Insufficient data"

    return {"top_features": top_features, "narrative": narrative}


# ── Rule-Based Model ──────────────────────────────────────────────────────────

def _rule_predict_row(row: pd.Series, regime: str = "Bull") -> dict:
    """Apply rule-based BUY/SELL/HOLD logic to one feature row."""
    mom   = float(row.get("momentum_score", 0))
    rsi   = float(row.get("rsi_14", 50))
    rsi_t = str(row.get("rsi_trend", "flat"))
    ema   = int(row.get("ema_aligned", 0))
    brk   = float(row.get("breakout_pct", -100))
    vol   = float(row.get("vol_ratio", 1))
    macd  = int(row.get("macd_sign", 0))
    atr   = float(row.get("atr_pct", 3))

    # ── BUY signals ───────────────────────────────────────────────────────
    buy_score = 0.0
    if mom > RULE_BUY_MOMENTUM_MIN:
        buy_score += 30 + min(20, (mom - RULE_BUY_MOMENTUM_MIN) * 0.8)
    if rsi_t == "rising" and 45 <= rsi <= 72:
        buy_score += 15
    elif rsi > 72:
        buy_score -= 10  # overbought penalty
    if ema == 1:
        buy_score += 15
    if brk > -3:
        buy_score += 10  # near 52W high = breakout territory
    if vol >= 1.5:
        buy_score += 8
    if macd > 0:
        buy_score += 7

    # ── SELL signals ──────────────────────────────────────────────────────
    sell_score = 0.0
    if mom < RULE_SELL_MOMENTUM_MAX:
        sell_score += 30 + min(20, (abs(mom) - abs(RULE_SELL_MOMENTUM_MAX)) * 0.8)
    if rsi_t == "falling" and rsi <= 55:
        sell_score += 15
    elif rsi < 30:
        sell_score -= 5   # oversold = potential bounce
    if ema == 0 and mom < 0:
        sell_score += 10
    if brk < -15:
        sell_score += 8
    if macd < 0:
        sell_score += 7

    # ── Regime adjustments ────────────────────────────────────────────────
    if regime == "Bear":
        buy_score  *= 0.75   # harder to trigger BUY in bear
        sell_score *= 1.20   # easier to trigger SELL in bear
    elif regime == "Sideways":
        buy_score  *= 0.88
        sell_score *= 1.05

    # ── Decision ──────────────────────────────────────────────────────────
    if buy_score > 55 and buy_score > sell_score + 10:
        prediction = "BUY"
        raw_conf = _clamp(RULE_CONF_BASE + buy_score * RULE_CONF_SCALE, 45, 92)
    elif sell_score > 55 and sell_score > buy_score + 10:
        prediction = "SELL"
        raw_conf = _clamp(RULE_CONF_BASE + sell_score * RULE_CONF_SCALE, 45, 92)
    else:
        prediction = "HOLD"
        raw_conf = _clamp(30 + (55 - max(buy_score, sell_score)) * 0.3, 30, 65)

    confidence = int(round(raw_conf))

    # ── Expected return estimate ───────────────────────────────────────────
    regime_mult = REGIME_RETURN_MULT.get(regime, 1.0)
    if prediction == "BUY":
        expected_return = round(min(8.0, max(1.0, mom * 0.12 + atr * 0.5)) * regime_mult, 2)
    elif prediction == "SELL":
        expected_return = round(-min(8.0, max(1.0, abs(mom) * 0.12 + atr * 0.5)) * regime_mult, 2)
    else:
        expected_return = round(mom * 0.04 * regime_mult, 2)

    reasoning = _build_reasoning(row, prediction, confidence)

    return {
        "prediction":        prediction,
        "confidence":        confidence,
        "expected_return_pct": expected_return,
        "reasoning":         reasoning,
    }


def rule_based_predict(features_df: pd.DataFrame, regime: str = "Bull") -> pd.DataFrame:
    """
    Apply rule-based predictions to a feature DataFrame.

    Args:
        features_df : Output of prediction/features.build_feature_matrix()
        regime      : "Bull" | "Sideways" | "Bear"

    Returns:
        DataFrame indexed by ticker, with prediction columns appended.
    """
    log.info(f"  🔮 Rule-based predictions ({regime} regime) for {len(features_df)} stocks...")

    results = []
    for ticker, row in features_df.iterrows():
        pred = _rule_predict_row(row, regime=regime)
        pred["ticker"] = ticker
        results.append(pred)

    out_df = pd.DataFrame(results).set_index("ticker")
    log.info(
        f"     BUY: {(out_df.prediction=='BUY').sum()}  "
        f"SELL: {(out_df.prediction=='SELL').sum()}  "
        f"HOLD: {(out_df.prediction=='HOLD').sum()}"
    )
    return out_df


# ── Random Forest Model (optional) ───────────────────────────────────────────

NUMERIC_FEATURES = [
    "rsi_14", "macd_hist", "macd_sign", "ema_aligned", "ema9_21_gap_pct",
    "atr_pct", "vol_ratio", "breakout_pct", "momentum_score", "rel_strength",
]


def _load_rf_model():
    """Load sklearn RandomForest from disk. Returns None if unavailable."""
    if not MODEL_PATH.exists():
        return None, None
    try:
        with open(MODEL_PATH, "rb") as fh:
            model = pickle.load(fh)
        meta = {}
        if MODEL_META_PATH.exists():
            with open(MODEL_META_PATH, encoding="utf-8") as fh:
                meta = json.load(fh)
        log.info(f"  📦 Loaded RF model from {MODEL_PATH} (trained: {meta.get('trained_at','?')})")
        return model, meta
    except Exception as exc:
        log.warning(f"  ⚠️  Could not load RF model: {exc}")
        return None, None


def rf_predict(features_df: pd.DataFrame, regime: str = "Bull") -> pd.DataFrame:
    """
    Apply trained RandomForest model if available.
    Falls back to rule_based_predict automatically.
    """
    model, meta = _load_rf_model()
    if model is None:
        log.info("  ℹ️  RF model not found — using rule-based fallback")
        return rule_based_predict(features_df, regime=regime)

    # Encode rsi_trend as integer
    enc = features_df.copy()
    enc["rsi_trend_enc"] = enc.get("rsi_trend", "flat").map(
        {"rising": 1, "flat": 0, "falling": -1}
    ).fillna(0)

    feat_cols = NUMERIC_FEATURES + ["rsi_trend_enc"]
    X = enc.reindex(columns=feat_cols).fillna(0).values

    try:
        raw_pred = model.predict(X)
        proba    = model.predict_proba(X)
        classes  = list(model.classes_)

        results = []
        for i, (ticker, row) in enumerate(features_df.iterrows()):
            pred_label  = raw_pred[i]
            pred_proba  = proba[i]
            confidence  = int(round(max(pred_proba) * 100))

            # Regime dampening applied to confidence
            if regime == "Bear" and pred_label == "BUY":
                confidence = int(confidence * 0.75)
            elif regime == "Sideways" and pred_label in ("BUY", "SELL"):
                confidence = int(confidence * 0.88)

            # Expected return from class + confidence
            regime_mult = REGIME_RETURN_MULT.get(regime, 1.0)
            atr = float(row.get("atr_pct", 3))
            mom = float(row.get("momentum_score", 0))
            if pred_label == "BUY":
                exp_ret = round(min(8, max(1, mom * 0.12 + atr * 0.5)) * regime_mult, 2)
            elif pred_label == "SELL":
                exp_ret = round(-min(8, max(1, abs(mom) * 0.12 + atr * 0.5)) * regime_mult, 2)
            else:
                exp_ret = round(mom * 0.04 * regime_mult, 2)

            reasoning = _build_reasoning(row, pred_label, confidence)
            results.append({
                "ticker":              ticker,
                "prediction":          pred_label,
                "confidence":          _clamp(confidence, 30, 95),
                "expected_return_pct": exp_ret,
                "reasoning":           reasoning,
            })

        out_df = pd.DataFrame(results).set_index("ticker")
        log.info(
            f"  ✅ RF predictions done — "
            f"BUY: {(out_df.prediction=='BUY').sum()}  "
            f"SELL: {(out_df.prediction=='SELL').sum()}  "
            f"HOLD: {(out_df.prediction=='HOLD').sum()}"
        )
        return out_df

    except Exception as exc:
        log.error(f"  ❌ RF prediction failed ({exc}) — falling back to rule-based")
        return rule_based_predict(features_df, regime=regime)


# ── Public API ────────────────────────────────────────────────────────────────

def predict_next_week(
    features_df: pd.DataFrame,
    regime: str = "Bull",
    prefer_ml: bool = True,
) -> pd.DataFrame:
    """
    Generate next-week BUY/SELL/HOLD predictions for all stocks.

    Args:
        features_df: Output of prediction/features.build_feature_matrix()
        regime:      Market regime label ("Bull" | "Sideways" | "Bear")
        prefer_ml:   Try RF model first; fall back to rule-based if unavailable

    Returns:
        DataFrame indexed by ticker with columns:
            prediction, confidence, expected_return_pct, reasoning
    """
    if prefer_ml and MODEL_PATH.exists():
        return rf_predict(features_df, regime=regime)
    return rule_based_predict(features_df, regime=regime)
