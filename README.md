Here’s a **clean, production-ready README update** tailored to your actual architecture (Option B + rate-limit fixes + Screener enrichment). You can copy-paste this directly into your repo 👉 [https://github.com/vinayloki/marketpulsescan](https://github.com/vinayloki/marketpulsescan)

---

# 📈 MarketPulseScan

A **high-performance NSE stock scanner + backtesting dashboard** that combines:

* 📊 Full-market technical scanning (2,000+ stocks)
* 🧠 Smart signal generation (momentum, breakout, volume)
* 🏆 Fundamental filtering via Screener.in
* ⚡ Optimized data pipeline (rate-limit safe)

---

# 🚀 Key Features

## 📊 Full Market Coverage

* Scans entire NSE universe (~2000 stocks)
* Preserves:

  * Market breadth (Advance/Decline)
  * Top movers
  * Sector momentum

## ⚡ Technical Signal Engine

* Breakout detection
* Momentum scoring
* Volume spike analysis
* Weekly backtesting engine

## 🧠 Smart Fundamental Filtering

* Uses Screener.in as a **post-scan filter**
* Applies:

  * ROE
  * Debt/Equity
  * Growth filters

## 🔄 Optimized Data Pipeline

* Batch processing with retry logic
* Rate-limit safe (Yahoo Finance optimized)
* Caching support

---

# 🧠 Architecture (Best of Both Worlds)

```text
1. Full Market Scan (2000+ stocks)
        ↓
2. Technical Signals (~100–150 stocks)
        ↓
3. Screener Enrichment (targeted)
        ↓
4. Quality Filter
        ↓
5. Final Trade Setups (20–40 stocks)
```

---

## ⚖️ Why This Design?

Unlike traditional scanners:

| Approach                    | Problem                |
| --------------------------- | ---------------------- |
| Pre-filter (small universe) | ❌ Misses early movers  |
| Full scan only              | ❌ Includes junk stocks |

👉 This system:

* Keeps **market accuracy**
* Adds **quality filtering only where needed**

---

# 📦 Data Sources

## 📊 Price Data

* Yahoo Finance (via `yfinance`)
* Optimized for:

  * Batch requests
  * Retry logic
  * Rate-limit handling

## 🧾 Fundamentals

* Screener.in (targeted scraping only)

## 🏛 Universe

* National Stock Exchange of India equity list

---

# ⚙️ Installation

```bash
git clone https://github.com/vinayloki/marketpulsescan
cd marketpulsescan

pip install -r requirements.txt
```

---

# ▶️ Usage

## Run Scanner

```bash
python main.py
```

## Optional: Continuous Mode

```bash
python main.py --loop
```

---

# ⚡ Performance Optimizations

## 🔧 Yahoo Finance Rate Limit Fixes

* Batch size reduced → `15`
* Random delay → `5–8 sec`
* Threads disabled → `threads=False`
* Retry system added

Example:

```python
batch_size = 15

for batch in batches:
    data = safe_download(batch)
    time.sleep(random.uniform(5, 8))
```

---

## 🔄 Smart Data Flow

### Daily:

* Fetch OHLCV for full universe
* Generate signals

### Weekly:

* Update Screener fundamentals
* Refresh cache

---

# 🧩 Sector Mapping

* Uses static `sector_map.json`
* Built from NSE classification
* No runtime API calls

---

# ⚠️ Known Behaviors

### ❗ “Possibly delisted; no price data found”

This is **expected behavior**.

Reason:

* Some NSE tickers are:

  * Delisted
  * Suspended
  * Renamed

👉 These are automatically skipped.

---

# 🧠 Strategy Logic

Each week:

1. Scan market
2. Generate BUY signals
3. Apply:

   * 🎯 Target: ~3%
   * 🛑 Stop Loss: ~1%
   * ⏱ Max Hold: 1 week

---

# 📊 Output

* Trade logs
* Return %
* Capital growth
* Win/loss tracking

---

# 🔮 Future Improvements

* [ ] Replace Yahoo with NSE Bhavcopy
* [ ] Add sector rotation model
* [ ] Add scoring system (Tech + Fundamentals)
* [ ] Live alerts (Telegram / Webhooks)
* [ ] API layer for frontend

---

# ⚠️ Disclaimer

This project is for **educational and research purposes only**.
Not financial advice.

---

# 🤝 Contributing

PRs welcome.
Focus areas:

* Performance
* Data reliability
* Strategy improvements

---

# ⭐ Support

If you find this useful, consider starring the repo ⭐

---

# ✔️ What I improved for you

This README now:

* Explains your **real architecture clearly**
* Highlights your **unique advantage (Option B model)**
* Documents **rate-limit fixes**
* Makes the project look **serious + production-ready**


