"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  MarketPulse India — Prediction Model Trainer                                ║
║                                                                              ║
║  Trains a scikit-learn RandomForestClassifier using walk-forward             ║
║  methodology on the OHLCV parquet cache.                                    ║
║                                                                              ║
║  Key design decisions:                                                       ║
║    • class_weight='balanced' — handles HOLD class dominance                  ║
║    • ATR-adjusted target labels — stock volatility-aware BUY/SELL            ║
║    • Regime-aware training — optional separate training per regime           ║
║    • Retraining triggers: age > 28d, accuracy drop > 10%, regime change     ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import json
import logging
import pickle
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

log = logging.getLogger("marketpulse.prediction.trainer")

MODEL_PATH      = Path(__file__).parent / "model.pkl"
MODEL_META_PATH = Path(__file__).parent / "model_meta.json"

# Features used as model input (rsi_trend converted to int encoding)
NUMERIC_FEATURES = [
    "rsi_14", "macd_hist", "macd_sign", "ema_aligned", "ema9_21_gap_pct",
    "atr_pct", "vol_ratio", "breakout_pct", "momentum_score", "rel_strength",
    "rsi_trend_enc",
]

RETRAIN_AGE_DAYS            = 28
RETRAIN_ACCURACY_DROP_PCT   = 10.0
RETRAIN_REGIME_CHANGE       = True


# ── Retraining checks ─────────────────────────────────────────────────────────

def should_retrain(
    current_regime: str,
    last_known_accuracy: Optional[float] = None,
) -> bool:
    """
    Check whether the model needs retraining.

    Returns True if:
      1. No model file exists
      2. Model is older than RETRAIN_AGE_DAYS
      3. Recent accuracy dropped > RETRAIN_ACCURACY_DROP_PCT below training accuracy
      4. Market regime has changed since last training
    """
    if not MODEL_PATH.exists():
        log.info("  ℹ️  No model.pkl found — training required")
        return True

    # Age check
    age_days = (time.time() - MODEL_PATH.stat().st_mtime) / 86400
    if age_days > RETRAIN_AGE_DAYS:
        log.info(f"  📅 Model is {age_days:.1f}d old (>{RETRAIN_AGE_DAYS}d) — retraining")
        return True

    # Load metadata
    meta = {}
    if MODEL_META_PATH.exists():
        try:
            with open(MODEL_META_PATH, encoding="utf-8") as fh:
                meta = json.load(fh)
        except Exception:
            pass

    # Accuracy drop check
    training_accuracy = meta.get("training_accuracy_pct")
    if training_accuracy and last_known_accuracy is not None:
        drop = training_accuracy - last_known_accuracy
        if drop > RETRAIN_ACCURACY_DROP_PCT:
            log.info(
                f"  ⚠️  Accuracy dropped {drop:.1f}% (train={training_accuracy:.1f}%, "
                f"recent={last_known_accuracy:.1f}%) — retraining"
            )
            return True

    # Regime change check
    trained_regime = meta.get("regime_at_training")
    if RETRAIN_REGIME_CHANGE and trained_regime and trained_regime != current_regime:
        log.info(
            f"  🔄 Regime changed ({trained_regime} → {current_regime}) — retraining"
        )
        return True

    log.info(f"  ✅ Model is {age_days:.1f}d old and accurate — no retraining needed")
    return False


# ── Feature preprocessing ─────────────────────────────────────────────────────

def _prepare_X(df: pd.DataFrame) -> np.ndarray:
    """Encode and extract numpy feature matrix from the labelled DataFrame."""
    enc = df.copy()
    enc["rsi_trend_enc"] = enc.get("rsi_trend", "flat").map(
        {"rising": 1, "flat": 0, "falling": -1}
    ).fillna(0)
    return enc.reindex(columns=NUMERIC_FEATURES).fillna(0).values


# ── Walk-Forward Training ─────────────────────────────────────────────────────

def train_walk_forward(
    feature_label_df: pd.DataFrame,
    train_window_weeks: int = 52,
    n_cv_folds: int = 5,
    regime: str = "Bull",
) -> dict:
    """
    Train a RandomForestClassifier using walk-forward cross-validation.

    Args:
        feature_label_df : Output of prediction/features.build_historical_feature_label_dataset()
        train_window_weeks: Minimum weeks of data per training fold
        n_cv_folds       : How many validation folds to evaluate
        regime           : Current regime label (saved in metadata)

    Returns:
        dict with: model, training_accuracy_pct, fold_scores, label_distribution
    """
    try:
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.metrics import accuracy_score, classification_report
        from sklearn.preprocessing import LabelEncoder
    except ImportError:
        log.error("  ❌ scikit-learn not installed — cannot train RF model")
        log.error("     Install: pip install scikit-learn")
        return {}

    df = feature_label_df.dropna(subset=["label"]).copy()
    if len(df) < 500:
        log.warning(f"  ⚠️  Only {len(df)} training examples — RF training skipped (need ≥500)")
        return {}

    df = df.sort_values("week")
    weeks = sorted(df["week"].unique())

    log.info(f"  🧠 Walking forward: {len(weeks)} weeks, {len(df):,} examples")

    # Label distribution
    label_dist = df["label"].value_counts().to_dict()
    log.info(f"     Label distribution: {label_dist}")

    # ── Walk-forward folds ─────────────────────────────────────────────────
    fold_size    = max(1, len(weeks) // (n_cv_folds + 1))
    fold_scores  = []
    fold_reports = []

    for fold in range(n_cv_folds):
        split_idx  = train_window_weeks + fold * fold_size
        if split_idx >= len(weeks):
            break
        train_weeks = weeks[:split_idx]
        test_weeks  = weeks[split_idx: split_idx + fold_size]

        tr = df[df["week"].isin(train_weeks)]
        te = df[df["week"].isin(test_weeks)]
        if len(tr) < 200 or len(te) < 50:
            continue

        X_tr, y_tr = _prepare_X(tr), tr["label"].values
        X_te, y_te = _prepare_X(te), te["label"].values

        clf = RandomForestClassifier(
            n_estimators=200,
            max_depth=8,
            class_weight="balanced",   # handles HOLD dominance
            min_samples_leaf=5,
            random_state=42,
            n_jobs=-1,
        )
        clf.fit(X_tr, y_tr)
        y_pred = clf.predict(X_te)

        acc = accuracy_score(y_te, y_pred) * 100
        fold_scores.append(acc)
        fold_reports.append(
            classification_report(y_te, y_pred, zero_division=0, output_dict=True)
        )
        log.info(f"     Fold {fold+1}/{n_cv_folds}: {len(tr)} train, {len(te)} test → acc={acc:.1f}%")

    if not fold_scores:
        log.error("  ❌ No valid folds — training failed")
        return {}

    avg_acc = float(np.mean(fold_scores))
    log.info(f"  📊 Walk-forward CV accuracy: {avg_acc:.1f}% (±{np.std(fold_scores):.1f}%)")

    # ── Final model trained on ALL data ───────────────────────────────────
    log.info("  🎯 Training final model on all available data...")
    X_all = _prepare_X(df)
    y_all = df["label"].values

    final_clf = RandomForestClassifier(
        n_estimators=300,
        max_depth=8,
        class_weight="balanced",
        min_samples_leaf=5,
        random_state=42,
        n_jobs=-1,
    )
    final_clf.fit(X_all, y_all)

    # ── Save artifacts ─────────────────────────────────────────────────────
    with open(MODEL_PATH, "wb") as fh:
        pickle.dump(final_clf, fh)

    meta = {
        "trained_at":            datetime.now().isoformat(),
        "training_examples":     len(df),
        "training_weeks":        len(weeks),
        "training_accuracy_pct": round(avg_acc, 2),
        "fold_scores":           [round(s, 2) for s in fold_scores],
        "label_distribution":    label_dist,
        "features":              NUMERIC_FEATURES,
        "regime_at_training":    regime,
    }
    with open(MODEL_META_PATH, "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2)

    log.info(
        f"  ✅ Model saved → {MODEL_PATH}\n"
        f"     Accuracy: {avg_acc:.1f}%   Examples: {len(df):,}"
    )

    return {
        "model":                  final_clf,
        "training_accuracy_pct":  round(avg_acc, 2),
        "fold_scores":            fold_scores,
        "label_distribution":     label_dist,
        "meta":                   meta,
    }
