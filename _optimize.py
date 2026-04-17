"""
Patch backtest.py to dramatically speed up 50-week loop by precomputing common
technical indicators globally instead of per-ticker per-week.
"""

import re

path = 'backtest.py'
with open(path, encoding='utf-8') as f:
    c = f.read()

# 1. Add PRECOMPUTE logic at the beginning of run_backtest
precompute_block = """
def precompute_indicators(ohlcv: pd.DataFrame) -> dict:
    log.info("  ⚙️  Precomputing technical indicators (vectorized over 2100 stocks)...")
    import numpy as np
    c = ohlcv["Close"]
    h = ohlcv["High"]
    l = ohlcv["Low"]
    v = ohlcv["Volume"]

    # EMA
    ema9  = c.ewm(span=EMA_FAST, adjust=False).mean()
    ema21 = c.ewm(span=EMA_MID, adjust=False).mean()
    ema50 = c.ewm(span=EMA_SLOW, adjust=False).mean()

    # RSI
    delta = c.diff()
    gain = delta.clip(lower=0).ewm(com=RSI_PERIOD - 1, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(com=RSI_PERIOD - 1, adjust=False).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))

    # ATR
    prev_c = c.shift(1)
    tr1 = h - l
    tr2 = (h - prev_c).abs()
    tr3 = (l - prev_c).abs()
    tr = np.maximum(np.maximum(tr1.values, tr2.values), tr3.values)
    tr_df = pd.DataFrame(tr, index=c.index, columns=c.columns)
    atr = tr_df.ewm(com=ATR_PERIOD - 1, adjust=False).mean()

    # Vol SMA
    vol_sma = v.rolling(window=20, min_periods=20).mean()

    # High 52w (rolling 252 days)
    high_52w = h.rolling(window=252, min_periods=20).max()

    return {
        "ema9": ema9, "ema21": ema21, "ema50": ema50,
        "rsi": rsi, "atr": atr, "vol_sma": vol_sma, "high_52w": high_52w
    }

"""

if 'def precompute_indicators' not in c:
    idx = c.find('# ══════════════════════════════════════════════════════════════════════════════\n#  MAIN BACKTEST LOOP')
    c = c[:idx] + precompute_block + c[idx:]

# 2. Modify run_backtest to accept PRECOMPUTED
find_rb = 'def run_backtest(ohlcv: pd.DataFrame, mode: str = "A") -> list[Trade]:'
idx_rb = c.find(find_rb)

if 'ind = precompute_indicators(ohlcv)' not in c[idx_rb:idx_rb+1000]:
    after_dates = c.find('    all_trades:    list[Trade]  = []', idx_rb)
    c = c[:after_dates] + '    ind = precompute_indicators(ohlcv)\n\n' + c[after_dates:]

# 3. Pass `ind` to detect_signals
c = c.replace('signals = detect_signals(hist)', 'signals = detect_signals(hist, ind, scan_date)')

# 4. Update detect_signals signature
old_sig = 'def detect_signals(hist_slice: pd.DataFrame) -> dict[str, dict]:'
new_sig = 'def detect_signals(hist_slice: pd.DataFrame, ind: dict = None, scan_date = None) -> dict[str, dict]:'
c = c.replace(old_sig, new_sig)

# 5. Overhaul detect_signals body internally to use `ind` dict instead of calculating
# We will use regex to replace everything from `min_bars = ...` to the end of the loop with a fast vectorized row extraction.
sig_start = c.find('    min_bars = ')
sig_end = c.find('    return signals', sig_start)

fast_body = """
    close_df  = hist_slice["Close"]
    volume_df = hist_slice["Volume"]
    
    signals: dict[str, dict] = {}
    
    # Pull the exact day cross-section
    if scan_date not in close_df.index:
        return signals
        
    idx_num = close_df.index.get_loc(scan_date)
    if isinstance(idx_num, slice): return signals
    if idx_num < max(EMA_SLOW + 10, 60):
        return signals
        
    prev_idx_num = idx_num - 1
    
    # 1D slices for the current date
    c_row = close_df.iloc[idx_num]
    v_row = volume_df.iloc[idx_num]
    prev_c_row = close_df.iloc[prev_idx_num]
    
    e9_row  = ind["ema9"].loc[scan_date]
    e21_row = ind["ema21"].loc[scan_date]
    e50_row = ind["ema50"].loc[scan_date]
    rsi_row = ind["rsi"].loc[scan_date]
    atr_row = ind["atr"].loc[scan_date]
    v_sma_row = ind["vol_sma"].loc[scan_date]
    h52_row = ind["high_52w"].loc[scan_date]
    
    # 1-month return (approx 21 trading days ago)
    ret_idx = max(0, idx_num - 21)
    ret_row = close_df.iloc[ret_idx]
    
    # 10-day sma for volume score bonus
    sma10_row = close_df.iloc[max(0, idx_num-9):idx_num+1].mean(axis=0)

    for ticker in c_row.index:
        try:
            curr_close = float(c_row[ticker])
            if pd.isna(curr_close) or curr_close <= 0: continue
            
            curr_vol = float(v_row[ticker])
            prev_close = float(prev_c_row[ticker])
            
            e9 = float(e9_row[ticker])
            e21 = float(e21_row[ticker])
            e50 = float(e50_row[ticker])
            rsi_val = float(rsi_row[ticker])
            atr_val = float(atr_row[ticker])
            vol_avg = float(v_sma_row[ticker])
            high_52w = float(h52_row[ticker])
            
            if pd.isna(e50) or vol_avg <= 0 or atr_val <= 0:
                continue
                
            vol_ratio = curr_vol / vol_avg
            pct_from_h = (1 - curr_close / high_52w) * 100 if high_52w > 0 else 100

            # Signal 1: 52-Week Breakout
            score_breakout = 0
            triggered = []
            if pct_from_h <= BREAKOUT_PROXIMITY_PCT and vol_ratio >= BREAKOUT_VOLUME_MULT:
                s = 20
                s += min(10, int((vol_ratio - BREAKOUT_VOLUME_MULT) / 1.5 * 10))
                if pct_from_h <= 0.5: s += 5
                score_breakout = min(30, s)
                triggered.append("BREAKOUT")

            # Signal 2: EMA + RSI Momentum
            score_momentum = 0
            ema_aligned = e9 > e21 > e50
            rsi_in_zone = RSI_MOMENTUM_LOW <= rsi_val <= RSI_MOMENTUM_HIGH
            if ema_aligned and rsi_in_zone:
                ema9_21_gap   = (e9 - e21) / curr_close * 100
                ema21_50_gap  = (e21 - e50) / curr_close * 100
                align_str     = (ema9_21_gap + ema21_50_gap) / 2
                ema_sc        = min(20, int(align_str * 10))
                rsi_center = 62.0
                rsi_dev    = abs(rsi_val - rsi_center) / max(1, rsi_center - RSI_MOMENTUM_LOW)
                rsi_sc     = max(0, int(15 * (1 - rsi_dev)))
                
                ret_1m = (curr_close / float(ret_row[ticker]) - 1) * 100
                ret_sc = min(10, max(0, int(ret_1m / 2)))
                
                score_momentum = min(45, ema_sc + rsi_sc + ret_sc)
                triggered.append("MOMENTUM")

            # Signal 3: Volume Spike
            score_volume = 0
            if vol_ratio >= VOLUME_SPIKE_MULT and curr_close > prev_close:
                norm = (vol_ratio - VOLUME_SPIKE_MULT) / max(1, (6.0 - VOLUME_SPIKE_MULT))
                s    = int(min(22, norm * 22))
                sma10 = float(sma10_row[ticker])
                if curr_close > sma10: s += 3
                score_volume = min(25, s)
                triggered.append("VOLUME")

            if not triggered:
                continue

            raw_score = score_breakout + score_momentum + score_volume
            n_signals = len(triggered)
            bonus     = {2: 5, 3: 10}.get(n_signals, 0)
            score     = min(100, raw_score + bonus)

            if score < REGIME_BULL_MIN_SCORE:
                continue

            sig_type = "MULTI" if n_signals >= 2 else triggered[0]

            signals[ticker] = {
                "score":      score,
                "type":       sig_type,
                "triggered":  triggered,
                "atr":        round(atr_val, 4),
                "price":      round(curr_close, 2),
                "indicators": {
                    "pct_from_52w_high": round(pct_from_h, 2),
                    "vol_ratio":         round(vol_ratio, 2),
                    "rsi":               round(rsi_val, 1),
                    "ema9":              round(e9, 2),
                    "ema50":             round(e50, 2),
                },
            }
        except Exception:
            continue

"""
c = c[:sig_start] + fast_body + c[sig_end:]

with open(path, 'w', encoding='utf-8') as f:
    f.write(c)

print("backtest.py vectorized successfully.")
