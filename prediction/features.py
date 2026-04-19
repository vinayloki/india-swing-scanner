"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  MarketPulse India — Prediction Feature Engineering                         ║
║                                                                              ║
║  Builds a weekly feature matrix from the OHLCV parquet cache                ║
║  (same data used by backtest.py) — NO return-proxy shortcuts.                ║
║                                                                              ║
║  All indicators computed via pandas vectorized operations across all         ║
║  2100+ stocks simultaneously for efficiency.                                 ║
║                                                                              ║
║  Features produced per stock per week:                                       ║
║    rsi_14            — RSI(14) on weekly bars                                ║
║    rsi_trend         — RSI rising/flat/falling over last 4 weeks             ║
║    macd_signal       — MACD histogram sign (bullish/bearish/neutral)        ║
║    ema_aligned       — EMA9 > EMA21 > EMA50 on weekly bars                  ║
║    ema9_21_gap_pct   — (EMA9 - EMA21) / Close                               ║
║    atr_pct           — ATR(14) / Close on weekly bars                       ║
║    vol_ratio         — Volume / 20-week SMA                                  ║
║    breakout_pct      — (Close - 52W High) / 52W High  [0 = AT high]         ║
║    momentum_score    — Weighted return score (ai_engine logic)              ║
║    rel_strength      — Stock 1M return - market median 1M return             ║
║    bb_squeeze        — BBW < 20-week median BBW (1=compressed, 0=normal)     ║
║    sector_rs_pct     — 1M return minus sector peer median return             ║
║    vol_contraction   — Vol avg(3w) < Vol avg(10w) (1=drying up, 0=normal)   ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import logging
from typing import Optional

import numpy as np
import pandas as pd

log = logging.getLogger("marketpulse.prediction.features")


# ── EMA / RSI / ATR helpers (vectorized, identical to backtest.py) ────────────

def _ema_df(df: pd.DataFrame, span: int) -> pd.DataFrame:
    return df.ewm(span=span, adjust=False).mean()


def _rsi_df(close_df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """Wilder RSI on a wide DataFrame (rows=dates, cols=tickers)."""
    delta = close_df.diff()
    gain  = delta.clip(lower=0).ewm(com=period - 1, adjust=False).mean()
    loss  = (-delta.clip(upper=0)).ewm(com=period - 1, adjust=False).mean()
    rs    = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def _atr_df(high: pd.DataFrame, low: pd.DataFrame,
            close: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """Vectorized ATR over a wide DataFrame."""
    prev_c = close.shift(1)
    tr1 = high - low
    tr2 = (high - prev_c).abs()
    tr3 = (low  - prev_c).abs()
    tr  = np.maximum(np.maximum(tr1.values, tr2.values), tr3.values)
    tr_df = pd.DataFrame(tr, index=close.index, columns=close.columns)
    return tr_df.ewm(com=period - 1, adjust=False).mean()


def _macd_df(close_df: pd.DataFrame) -> pd.DataFrame:
    """MACD histogram = (EMA12 - EMA26) - EMA9_of_(EMA12-EMA26)."""
    ema12  = _ema_df(close_df, 12)
    ema26  = _ema_df(close_df, 26)
    macd   = ema12 - ema26
    signal = _ema_df(macd, 9)
    return macd - signal   # histogram > 0 → bullish, < 0 → bearish


# ── Resample Daily → Weekly ───────────────────────────────────────────────────

def resample_to_weekly(ohlcv_daily: pd.DataFrame) -> pd.DataFrame:
    """
    Resample daily multi-level OHLCV (rows=dates, cols=(field, ticker))
    to weekly bars (Friday close).

    Returns same multi-level structure on weekly index.
    """
    log.info("  📐 Resampling daily OHLCV → weekly bars (Friday close)...")

    result = {}
    agg_map = {
        "Open":   "first",
        "High":   "max",
        "Low":    "min",
        "Close":  "last",
        "Volume": "sum",
    }

    for field, agg in agg_map.items():
        if field not in ohlcv_daily.columns.get_level_values(0):
            continue
        daily_field = ohlcv_daily[field]
        # Resample: W-FRI = week ending Friday
        weekly_field = daily_field.resample("W-FRI").agg(agg)
        result[field] = weekly_field

    if not result:
        raise ValueError("OHLCV data missing required OHLCV fields")

    weekly = pd.concat(result, axis=1)
    log.info(f"     ✅ Weekly bars: {len(weekly)} weeks × {weekly.shape[1]} columns")
    return weekly


# ── Full Feature Matrix ───────────────────────────────────────────────────────

def build_feature_matrix(
    ohlcv_daily: pd.DataFrame,
    as_of_date: Optional[pd.Timestamp] = None,
) -> pd.DataFrame:
    """
    Build a feature matrix for ONE snapshot point in time.

    Args:
        ohlcv_daily   : Full daily OHLCV (multi-level: field × ticker).
                        Only data up to as_of_date is used (no lookahead).
        as_of_date    : Compute features as if today is this date.
                        Defaults to the last date in the data.

    Returns:
        DataFrame with index = ticker, columns = feature names.
        Stocks with insufficient data are dropped.
    """
    # ── Slice to as_of_date (strict no-lookahead) ──────────────────────────
    if as_of_date is not None:
        ohlcv_daily = ohlcv_daily.loc[:as_of_date]

    if len(ohlcv_daily) < 60:
        log.warning("  ⚠️  Insufficient daily data for feature engineering (< 60 bars)")
        return pd.DataFrame()

    # ── Resample to weekly ─────────────────────────────────────────────────
    weekly = resample_to_weekly(ohlcv_daily)

    close_w  = weekly["Close"]
    high_w   = weekly["High"]
    low_w    = weekly["Low"]
    volume_w = weekly["Volume"]

    if len(close_w) < 30:
        log.warning("  ⚠️  Insufficient weekly bars (< 30 weeks)")
        return pd.DataFrame()

    log.info("  ⚙️  Computing vectorized features across all tickers...")

    # ── Indicators ────────────────────────────────────────────────────────
    rsi_w    = _rsi_df(close_w, period=14)
    atr_w    = _atr_df(high_w, low_w, close_w, period=14)
    macd_h   = _macd_df(close_w)
    ema9_w   = _ema_df(close_w, 9)
    ema21_w  = _ema_df(close_w, 21)
    ema50_w  = _ema_df(close_w, 50)
    vol_sma  = volume_w.rolling(20, min_periods=10).mean()
    high_52w = high_w.rolling(52, min_periods=10).max()

    # RSI trend: direction over last 4 weeks
    rsi_slope = rsi_w.diff(4)   # positive → rising

    # MACD histogram sign
    macd_sign = macd_h.apply(lambda col: np.sign(col))

    # ── Snapshot: last row only ────────────────────────────────────────────
    last = close_w.iloc[-1]          # Series: ticker → close price
    rsi_last    = rsi_w.iloc[-1]
    rsi_sl      = rsi_slope.iloc[-1]
    macd_last   = macd_h.iloc[-1]
    atr_last    = atr_w.iloc[-1]
    e9          = ema9_w.iloc[-1]
    e21         = ema21_w.iloc[-1]
    e50         = ema50_w.iloc[-1]
    vol_last    = volume_w.iloc[-1]
    vol_avg     = vol_sma.iloc[-1]
    h52         = high_52w.iloc[-1]

    # Multi-timeframe momentum (mirrors ai_engine TF_WEIGHTS)
    tf_weights  = {"1W": 0.10, "2W": 0.15, "1M": 0.25,
                   "3M": 0.25, "6M": 0.15, "12M": 0.10}
    lag_map     = {"1W": 1, "2W": 2, "1M": 4, "3M": 13, "6M": 26, "12M": 52}

    # Build momentum score from weekly close returns (cap at ±50%)
    total_w = 0.0
    mom_sum = pd.Series(0.0, index=close_w.columns)
    for tf, w in tf_weights.items():
        lag = lag_map[tf]
        if len(close_w) <= lag:
            continue
        ret = (close_w.iloc[-1] / close_w.iloc[-1 - lag] - 1) * 100
        capped = ret.clip(-50, 50)
        mom_sum += capped / 50.0 * 100 * w
        total_w += w
    momentum_score = mom_sum / total_w if total_w > 0 else pd.Series(0.0, index=close_w.columns)

    # Relative strength vs market (median of all stocks)
    ret_1m = (close_w.iloc[-1] / close_w.iloc[max(0, len(close_w) - 4)] - 1) * 100
    market_median_1m = ret_1m.median()
    rel_strength = ret_1m - market_median_1m

    # ── NEW: Bollinger Band Squeeze ────────────────────────────────────────
    # BBW = (Upper - Lower) / Middle ; squeeze = current BBW < 20w median BBW
    bb_sma20  = close_w.rolling(20, min_periods=10).mean()
    bb_std20  = close_w.rolling(20, min_periods=10).std()
    bb_upper  = bb_sma20 + 2 * bb_std20
    bb_lower  = bb_sma20 - 2 * bb_std20
    bb_width  = (bb_upper - bb_lower) / bb_sma20.replace(0, np.nan)  # normalised
    bbw_median_20w = bb_width.rolling(20, min_periods=10).median()
    bb_squeeze_raw = (bb_width.iloc[-1] < bbw_median_20w.iloc[-1]).astype(int)

    # ── NEW: Volume Contraction (3w avg < 10w avg) ─────────────────────────
    vol_avg3   = volume_w.rolling(3, min_periods=2).mean()
    vol_avg10  = volume_w.rolling(10, min_periods=5).mean()
    vol_contr  = (vol_avg3.iloc[-1] < vol_avg10.iloc[-1]).astype(int)

    # ── NEW: Sector Relative Strength (placeholder — market RS proxy) ──────
    # True sector RS requires a sector mapping; we approximate using decile
    # grouping by 3M momentum as a proxy for the sector rotation effect.
    ret_3m = (close_w.iloc[-1] / close_w.iloc[max(0, len(close_w) - 13)] - 1) * 100
    market_median_3m = ret_3m.median()
    sector_rs_pct = ret_1m - market_median_1m  # stock 1M vs market (sector-proxy)

    # ── Assemble feature DataFrame ─────────────────────────────────────────
    tickers = close_w.columns

    def safe(s: pd.Series) -> pd.Series:
        return s.reindex(tickers)

    features = pd.DataFrame({
        "close":           safe(last),
        "rsi_14":          safe(rsi_last),
        "rsi_trend":       safe(rsi_sl.apply(
                               lambda v: "rising" if v > 2 else ("falling" if v < -2 else "flat")
                           )),
        "macd_hist":       safe(macd_last),
        "macd_sign":       safe(macd_last.apply(lambda v: int(np.sign(v)) if pd.notna(v) else 0)),
        "ema_aligned":     safe((e9 > e21) & (e21 > e50)).astype(int),
        "ema9_21_gap_pct": safe(((e9 - e21) / last.replace(0, np.nan)) * 100),
        "atr_pct":         safe((atr_last / last.replace(0, np.nan)) * 100),
        "vol_ratio":       safe(vol_last / vol_avg.replace(0, np.nan)),
        "breakout_pct":    safe(((last - h52) / h52.replace(0, np.nan)) * 100),  # negative = below 52W high
        "momentum_score":  safe(momentum_score),
        "rel_strength":    safe(rel_strength),
        "ret_1m_pct":      safe(ret_1m),
        # Professional features (P3)
        "bb_squeeze":      safe(bb_squeeze_raw),
        "vol_contraction": safe(vol_contr),
        "sector_rs_pct":   safe(sector_rs_pct),
    }, index=tickers)

    # ── Drop rows with too many NaNs ───────────────────────────────────────
    before = len(features)
    features = features.dropna(
        subset=["rsi_14", "ema_aligned", "atr_pct", "momentum_score"],
        how="any",
    )
    after = len(features)
    if before - after > 0:
        log.debug(f"     Dropped {before - after} tickers (insufficient history)")

    log.info(f"     ✅ Feature matrix: {len(features)} tickers × {len(features.columns)} features")
    return features


def build_historical_feature_label_dataset(
    ohlcv_daily: pd.DataFrame,
    backtest_weeks: int = 52,
) -> pd.DataFrame:
    """
    Build a historical dataset of (features, label) pairs for model training.

    Walks forward week by week using the existing OHLCV data.
    No lookahead: features at week T use only data ≤ T.
    Label at week T = direction of actual return T → T+1.

    Args:
        ohlcv_daily   : Full OHLCV (multi-level) — typically 13-month cache
        backtest_weeks: Number of weeks to walk back

    Returns:
        DataFrame with feature columns + 'label' + 'next_week_return_pct'
    """
    weekly = resample_to_weekly(ohlcv_daily)
    close_w = weekly["Close"]
    high_w  = weekly["High"]
    low_w   = weekly["Low"]
    atr_w   = _atr_df(high_w, low_w, close_w, period=14)

    all_weeks = close_w.index
    # Reserve last week — no label available for it
    usable_weeks = all_weeks[60:-1]  # need 60 weeks min warm-up; skip last
    if backtest_weeks < len(usable_weeks):
        usable_weeks = usable_weeks[-backtest_weeks:]

    log.info(
        f"  📅 Building historical features: {usable_weeks[0].date()} → "
        f"{usable_weeks[-1].date()} ({len(usable_weeks)} weeks)"
    )

    records = []
    for week_t in usable_weeks:
        week_t_idx = list(close_w.index).index(week_t)
        week_t1    = close_w.index[week_t_idx + 1]   # next week

        # Features: data up to week_t (inclusive)
        week_t_date = pd.Timestamp(week_t)
        # Find corresponding daily cutoff
        cutoff_daily = ohlcv_daily.index[ohlcv_daily.index <= week_t_date].max()
        if pd.isna(cutoff_daily):
            continue

        feats = build_feature_matrix(ohlcv_daily, as_of_date=cutoff_daily)
        if feats.empty:
            continue

        # Actual next-week returns (T → T+1)
        next_close   = close_w.loc[week_t1]
        curr_close   = close_w.loc[week_t]
        actual_ret   = ((next_close - curr_close) / curr_close.replace(0, np.nan)) * 100

        # ATR-adjusted label thresholds
        atr_pct_t    = (atr_w.loc[week_t] / curr_close.replace(0, np.nan)) * 100

        for ticker in feats.index:
            if ticker not in actual_ret.index:
                continue
            ret  = actual_ret.get(ticker)
            atr  = atr_pct_t.get(ticker, 2.0)
            if pd.isna(ret) or pd.isna(atr):
                continue

            threshold = max(2.0, float(atr) * 1.5)
            if ret > threshold:
                label = "BUY"
            elif ret < -threshold:
                label = "SELL"
            else:
                label = "HOLD"

            row = feats.loc[ticker].to_dict()
            row.update({
                "ticker":               ticker,
                "week":                 str(week_t.date()),
                "next_week_return_pct": round(float(ret), 3),
                "label":                label,
                "atr_threshold_pct":    round(float(threshold), 3),
            })
            records.append(row)

    log.info(f"  ✅ Built {len(records)} feature-label examples")
    return pd.DataFrame(records)
