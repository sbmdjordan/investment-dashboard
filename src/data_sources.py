"""Fetch macro indicators from free data sources.

Primary sources use simple HTTP APIs (FRED, multpl.com, CNN).
yfinance is used only for .history() calls which are reliable.
yfinance .info is NOT used — it gets blocked on cloud servers.
"""

import logging
import re

import requests
import streamlit as st
import yfinance as yf

log = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}


# --- FRED helper (free, no API key, very reliable) ---

def _fred_latest(series_id: str) -> float | None:
    """Get latest value from a FRED CSV series."""
    try:
        url = (
            f"https://fred.stlouisfed.org/graph/fredgraph.csv?"
            f"id={series_id}&cosd=2025-01-01&coed=2030-12-31"
        )
        r = requests.get(url, headers=_HEADERS, timeout=10)
        if r.status_code == 200:
            lines = r.text.strip().split("\n")
            # Walk backwards to find latest non-empty value
            for line in reversed(lines[1:]):
                parts = line.split(",")
                if len(parts) == 2 and parts[1] not in (".", ""):
                    return float(parts[1])
        log.warning("FRED %s: status %s", series_id, r.status_code)
    except Exception as e:
        log.error("FRED %s failed: %s", series_id, e)
    return None


# --- S&P 500 P/E from multpl.com (no API key, reliable) ---

def get_sp500_pe() -> float | None:
    """Get S&P 500 trailing P/E ratio from multpl.com."""
    try:
        r = requests.get(
            "https://www.multpl.com/s-p-500-pe-ratio",
            headers=_HEADERS, timeout=10,
        )
        if r.status_code == 200:
            match = re.search(
                r"Current S&(?:amp;)?P 500 PE Ratio is ([\d.]+)", r.text
            )
            if match:
                return round(float(match.group(1)), 1)
        log.warning("multpl.com PE: status %s, no match", r.status_code)
    except Exception as e:
        log.error("multpl.com PE failed: %s", e)
    # Fallback: yfinance .info (works locally, often blocked on cloud)
    try:
        pe = yf.Ticker("SPY").info.get("trailingPE")
        if pe is not None:
            return round(float(pe), 1)
    except Exception as e:
        log.error("yfinance SPY PE fallback failed: %s", e)
    return None


# --- Market data from yfinance .history() (reliable even on cloud) ---

def _yf_latest(ticker: str, period: str = "5d") -> float | None:
    """Get latest close for a yfinance ticker. Uses 5d to handle weekends."""
    try:
        hist = yf.Ticker(ticker).history(period=period)
        if not hist.empty:
            return round(float(hist["Close"].iloc[-1]), 2)
        log.warning("yf %s history empty (period=%s)", ticker, period)
    except Exception as e:
        log.error("yf %s failed: %s", ticker, e)
    return None


def get_vix() -> float | None:
    """Get VIX — try FRED first, yfinance fallback."""
    val = _fred_latest("VIXCLS")
    if val is not None:
        return round(val, 2)
    return _yf_latest("^VIX")


def get_treasury_10y() -> float | None:
    """Get 10Y Treasury yield — FRED primary, yfinance fallback."""
    val = _fred_latest("DGS10")
    if val is not None:
        return round(val, 2)
    return _yf_latest("^TNX")


def get_treasury_3m() -> float | None:
    """Get 3M T-bill rate — FRED primary, yfinance fallback."""
    val = _fred_latest("DTB3")
    if val is not None:
        return round(val, 2)
    return _yf_latest("^IRX")


def get_treasury_10y_trend() -> str | None:
    """Check if 10Y yield is trending up or down (3-month lookback)."""
    try:
        hist = yf.Ticker("^TNX").history(period="3mo")
        if len(hist) < 10:
            return None
        recent = float(hist["Close"].iloc[-1])
        three_months_ago = float(hist["Close"].iloc[0])
        if recent > three_months_ago + 0.1:
            return "rising"
        elif recent < three_months_ago - 0.1:
            return "falling"
        return "flat"
    except Exception as e:
        log.error("10Y trend failed: %s", e)
        return None


def get_sp500_drawdown() -> float | None:
    """Calculate S&P 500 drawdown from all-time high."""
    try:
        hist = yf.Ticker("^GSPC").history(period="2y")
        if hist.empty:
            return None
        ath = float(hist["Close"].max())
        current = float(hist["Close"].iloc[-1])
        drawdown = ((ath - current) / ath) * 100
        return round(drawdown, 2)
    except Exception as e:
        log.error("S&P drawdown failed: %s", e)
        return None


def get_fear_greed() -> int | None:
    """Get CNN Fear & Greed Index value."""
    try:
        resp = requests.get(
            "https://production.dataviz.cnn.io/index/fearandgreed/graphdata",
            headers={**_HEADERS, "Accept": "application/json",
                     "Referer": "https://edition.cnn.com/markets/fear-and-greed"},
            timeout=10,
        )
        if resp.status_code == 200:
            score = resp.json().get("fear_and_greed", {}).get("score")
            if score is not None:
                return int(round(score))
    except Exception as e:
        log.error("Fear & Greed failed: %s", e)
    return None


def get_fed_rate() -> float | None:
    """Get Fed Funds target upper rate from FRED."""
    return _fred_latest("DFEDTARU")


def get_ecb_rate() -> float | None:
    """Get ECB main refinancing rate from ECB data API."""
    try:
        url = (
            "https://data-api.ecb.europa.eu/service/data/FM/"
            "B.U2.EUR.4F.KR.MRR_FR.LEV?lastNObservations=1&format=csvdata"
        )
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            lines = r.text.strip().split("\n")
            last = lines[-1].split(",")
            if len(last) > 9:
                return float(last[9])
    except Exception as e:
        log.error("ECB rate failed: %s", e)
    return None


def get_boe_rate() -> float | None:
    """Get Bank of England base rate."""
    try:
        url = (
            "https://www.bankofengland.co.uk/boeapps/database/"
            "_iadb-fromshowcolumns.asp?csv.x=yes"
            "&Datefrom=01/Jan/2024&Dateto=31/Dec/2030"
            "&SeriesCodes=IUDBEDR&CSVF=CN&UsingCodes=Y&VPD=Y&VFD=N"
        )
        r = requests.get(url, headers=_HEADERS, timeout=10)
        if r.status_code == 200:
            lines = r.text.strip().split("\n")
            last = lines[-1].split(",")
            if len(last) >= 3:
                return float(last[2])
    except Exception as e:
        log.error("BoE rate failed: %s", e)
    return None


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_all() -> dict:
    """Fetch all indicators, returning dict with values (None if unavailable)."""
    t10 = get_treasury_10y()
    t3m = get_treasury_3m()
    fed = get_fed_rate()
    ecb = get_ecb_rate()
    boe = get_boe_rate()

    rates = [r for r in [fed, ecb, boe] if r is not None]
    avg_rate = round(sum(rates) / len(rates), 2) if rates else None

    return {
        "sp500_pe": get_sp500_pe(),
        "vix": get_vix(),
        "treasury_10y": t10,
        "treasury_3m": t3m,
        "yield_curve_spread": round(t10 - t3m, 2) if t10 and t3m else None,
        "rate_trend": get_treasury_10y_trend(),
        "sp500_drawdown": get_sp500_drawdown(),
        "fear_greed": get_fear_greed(),
        "fed_rate": fed,
        "ecb_rate": ecb,
        "boe_rate": boe,
        "avg_policy_rate": avg_rate,
    }
