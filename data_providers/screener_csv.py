"""
╔══════════════════════════════════════════════════════════════════════════╗
║  MarketPulse India — Screener/Tickertape CSV Fundamentals Loader        ║
║                                                                          ║
║  Drop a CSV export from Tickertape (or Screener.in) into the project    ║
║  root, and this module auto-detects and loads it.                        ║
║                                                                          ║
║  Naming convention:  Stock_Screener_*.csv   (any suffix works)          ║
║  Example:            Stock_Screener_4_30_2026.csv                       ║
║                                                                          ║
║  Usage:                                                                  ║
║      from data_providers.screener_csv import load_screener_csv           ║
║      fund_map = load_screener_csv()                                      ║
║      # → {"RELIANCE": {"name": "...", "sector": "...", ...}, ...}       ║
╚══════════════════════════════════════════════════════════════════════════╝
"""

import glob
import logging
import os
import math
from pathlib import Path

import pandas as pd

from config.sector_map import normalize_sector

log = logging.getLogger("marketpulse.screener_csv")

# Project root — same level as scanner.py
_ROOT = Path(__file__).parent.parent.resolve()


def _find_latest_csv() -> Path | None:
    """
    Find the most recently modified Stock_Screener_*.csv in the project root.
    Returns the Path, or None if no match.
    """
    pattern = str(_ROOT / "Stock_Screener_*.csv")
    matches = glob.glob(pattern)
    if not matches:
        return None
    # Sort by modification time (newest first)
    matches.sort(key=os.path.getmtime, reverse=True)
    return Path(matches[0])


def _safe_float(val) -> float | None:
    """Convert a value to float, returning None for NaN/empty/errors."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        if math.isnan(val) or math.isinf(val):
            return None
        return float(val)
    try:
        s = str(val).strip().replace(",", "")
        if not s or s.lower() in ("nan", "inf", "-inf", "–", "-"):
            return None
        return float(s)
    except (ValueError, TypeError):
        return None


def _mcap_category(mcap_cr: float | None) -> str:
    """Classify market cap into L/M/S."""
    if mcap_cr is None:
        return "S"
    if mcap_cr > 20000:
        return "L"
    if mcap_cr > 5000:
        return "M"
    return "S"


def _normalize_tickertape_sector(sub_sector: str | None) -> str:
    """
    Map Tickertape's granular Sub-Sector labels to our canonical sectors.

    Tickertape uses very specific labels like "Private Banks", "IT Services & Consulting",
    "Oil & Gas - Refining & Marketing". We first try the canonical normalize_sector(),
    then apply Tickertape-specific keyword matching.
    """
    if not sub_sector:
        return "Others"

    # Try the standard normalize_sector first
    result = normalize_sector(sub_sector)
    if result != "Others":
        return result

    # Tickertape-specific keyword mapping
    low = sub_sector.lower()

    # Banking & Finance
    if any(kw in low for kw in [
        "bank", "financ", "insurance", "brokerage", "asset management",
        "housing finance", "home financing", "consumer finance",
        "specialized finance", "investment", "stock exchange", "rating",
        "depository", "amc", "wealth", "equity", "debt", "gold", "silver",
        "commodit",
    ]):
        return "Banking & Finance"

    # IT & Technology
    if any(kw in low for kw in [
        "it service", "software", "consulting", "tech", "digital",
        "internet", "online", "e-commerce", "saas", "data processing",
        "outsourced service",
    ]):
        return "IT & Technology"

    # Pharma & Healthcare
    if any(kw in low for kw in [
        "pharma", "healthcare", "hospital", "diagnostic", "biotech",
        "life science", "lab", "medical", "drug", "wellness",
    ]):
        return "Pharma & Healthcare"

    # FMCG & Consumer
    if any(kw in low for kw in [
        "fmcg", "personal product", "household", "tobacco", "food",
        "beverage", "consumer", "tea", "coffee", "soft drink",
        "dairy", "alcohol", "brew", "distill", "restaurant", "cafe",
        "hotel", "resort", "cruise", "housewares", "home furnish",
        "stationery", "wood product",
    ]):
        return "FMCG & Consumer"

    # Auto & Auto Ancillaries
    if any(kw in low for kw in [
        "auto", "vehicle", "car", "bike", "motor", "tyre", "tire",
        "tractor", "two wheeler", "four wheeler", "truck", "bus",
        "cycle", "three wheeler",
    ]):
        return "Auto & Auto Ancillaries"

    # Capital Goods & Engineering
    if any(kw in low for kw in [
        "capital good", "engineering", "electrical", "heavy", "industrial",
        "machinery", "equipment", "defence", "defense", "aerospace",
        "shipbuild", "cable", "wire", "transformer", "turbine",
        "electronic", "battery", "batteries", "packaging",
    ]):
        return "Capital Goods & Engineering"

    # Metals & Mining
    if any(kw in low for kw in [
        "metal", "mining", "steel", "iron", "alumin", "copper",
        "zinc", "ferro", "alloy", "ore",
    ]):
        return "Metals & Mining"

    # Oil, Gas & Energy
    if any(kw in low for kw in [
        "oil", "gas", "petro", "refin", "energy", "power", "renewable",
        "solar", "wind", "electric", "fuel", "coal", "water management",
    ]):
        return "Oil, Gas & Energy"

    # Real Estate
    if any(kw in low for kw in [
        "real estate", "realty", "developer", "housing", "reit",
        "property", "estate",
    ]):
        return "Real Estate"

    # Chemicals & Specialty
    if any(kw in low for kw in [
        "chemical", "specialty", "fertiliz", "agro", "paint",
        "adhesive", "plastic", "polymer", "paper",
    ]):
        return "Chemicals & Specialty"

    # Infrastructure
    if any(kw in low for kw in [
        "infrastr", "cement", "logistic", "transport", "shipping",
        "port", "road", "highway", "construction", "building",
        "pipe", "ceramic", "glass", "laminate", "rail", "airline",
        "dredg", "tour", "travel",
    ]):
        return "Infrastructure"

    # Telecom & Media
    if any(kw in low for kw in [
        "telecom", "media", "broadcast", "entertainment", "gaming",
        "movie", "tv", "film", "advert", "animation",
        "music", "communi", "network", "publishing", "radio",
        "theatre",
    ]):
        return "Telecom & Media"

    # Textiles & Apparel
    if any(kw in low for kw in [
        "textile", "apparel", "garment", "footwear", "fashion",
        "jeweller", "watch", "retail",
    ]):
        return "Textiles & Apparel"

    # Agri & Food Processing
    if any(kw in low for kw in [
        "agri", "sugar", "packaged food", "crop", "seed",
        "farm",
    ]):
        return "Agri & Food Processing"

    # Services catch-all (education, employment, etc.) → Others is fine
    return "Others"


def load_screener_csv(csv_path: Path | str | None = None) -> dict[str, dict]:
    """
    Load a Tickertape/Screener CSV export and convert to fundamentals dict.

    If csv_path is None, auto-detects the latest Stock_Screener_*.csv in the
    project root.

    Returns:
        Dict keyed by ticker symbol:
        {
            "RELIANCE": {
                "s":       "RELIANCE",
                "name":    "Reliance Industries Ltd",
                "sector":  "Oil, Gas & Energy",
                "ind":     "Oil & Gas - Refining & Marketing",
                "mcap":    1936235.6,      # ₹ Crores
                "pe":      23.97,
                "roe":     7.2,
                "pb":      1.92,
                "price":   1430.8,
                "return_1m": 6.68,
                "return_1d": 0.38,
            },
            ...
        }
    """
    # Find CSV
    if csv_path:
        path = Path(csv_path)
    else:
        path = _find_latest_csv()

    if not path or not path.exists():
        log.info("📄 No Screener CSV found in project root — skipping CSV enrichment")
        return {}

    log.info(f"📄 Loading Screener CSV: {path.name}")

    try:
        # Some CSVs have unquoted commas in company names (e.g. "Bombay Burmah Trading Corporation, Ltd")
        # Use on_bad_lines='skip' to handle these gracefully
        df = pd.read_csv(path, encoding="utf-8", on_bad_lines="skip")
    except Exception as e:
        log.warning(f"   ⚠️ Could not read CSV: {e}")
        return {}

    # Normalize column names for flexible matching
    col_map = {}
    for c in df.columns:
        cl = c.strip().lower()
        if cl == "name":
            col_map[c] = "name"
        elif cl == "ticker":
            col_map[c] = "ticker"
        elif cl in ("sub-sector", "sub_sector", "subsector", "sector"):
            col_map[c] = "sub_sector"
        elif cl in ("market cap", "market_cap", "mcap"):
            col_map[c] = "mcap"
        elif cl in ("close price", "close_price", "close", "price"):
            col_map[c] = "price"
        elif cl in ("pe ratio", "pe_ratio", "pe", "p/e"):
            col_map[c] = "pe"
        elif cl in ("1m return", "1m_return", "return_1m"):
            col_map[c] = "return_1m"
        elif cl in ("1d return", "1d_return", "return_1d"):
            col_map[c] = "return_1d"
        elif cl in ("return on equity", "roe", "return_on_equity"):
            col_map[c] = "roe"
        elif cl in ("pb ratio", "pb_ratio", "pb", "p/b"):
            col_map[c] = "pb"

    df = df.rename(columns=col_map)

    if "ticker" not in df.columns:
        log.warning("   ⚠️ CSV has no 'Ticker' column — cannot load")
        return {}

    fund_map: dict[str, dict] = {}
    loaded = 0
    skipped = 0

    for _, row in df.iterrows():
        ticker = str(row.get("ticker", "")).strip().upper()
        if not ticker or ticker == "NAN":
            skipped += 1
            continue

        name = str(row.get("name", ticker)).strip() if pd.notna(row.get("name")) else ticker
        sub_sector = str(row.get("sub_sector", "")).strip() if pd.notna(row.get("sub_sector")) else ""
        mcap_raw = _safe_float(row.get("mcap"))
        # Tickertape CSV: Market Cap is in ₹ Crores already (no conversion needed)
        mcap_cr = round(mcap_raw, 1) if mcap_raw else None

        pe = _safe_float(row.get("pe"))
        price = _safe_float(row.get("price"))
        roe = _safe_float(row.get("roe"))
        pb = _safe_float(row.get("pb"))
        ret_1m = _safe_float(row.get("return_1m"))
        ret_1d = _safe_float(row.get("return_1d"))

        # Sanity: skip if PE is absurdly negative (likely bad data)
        if pe is not None and pe < -10000:
            pe = None

        fund_map[ticker] = {
            "s":         ticker,
            "name":      name,
            "sector":    _normalize_tickertape_sector(sub_sector),
            "ind":       sub_sector,            # preserve original sub-sector
            "mcap":      mcap_cr,
            "pe":        round(pe, 1) if pe else None,
            "roe":       round(roe, 2) if roe else None,
            "pb":        round(pb, 2) if pb else None,
            "price":     round(price, 2) if price else None,
            "return_1m": round(ret_1m, 2) if ret_1m else None,
            "return_1d": round(ret_1d, 2) if ret_1d else None,
            "mcap_code": _mcap_category(mcap_cr),
        }
        loaded += 1

    log.info(f"   ✅ Loaded {loaded:,} stocks from CSV ({skipped} skipped)")
    return fund_map


def get_csv_tickers(csv_path: Path | str | None = None) -> list[str]:
    """
    Extract all ticker symbols from the CSV.
    Useful for expanding the scanner universe.
    """
    fund_map = load_screener_csv(csv_path)
    tickers = sorted(fund_map.keys())
    if tickers:
        log.info(f"   📊 CSV tickers extracted: {len(tickers)}")
    return tickers
