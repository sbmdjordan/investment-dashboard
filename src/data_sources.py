"""Fetch macro indicators from free data sources."""

import yfinance as yf
import requests
import streamlit as st
from datetime import datetime


def _yf_latest(ticker: str, period: str = "5d") -> float | None:
    """Get latest close for a yfinance ticker. Uses 5d to handle weekends."""
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period=period)
        if not hist.empty:
            return round(float(hist["Close"].iloc[-1]), 2)
    except Exception:
        pass
    return None


def get_sp500_pe() -> float | None:
    """Get S&P 500 trailing P/E ratio via SPY ETF."""
    try:
        spy = yf.Ticker("SPY")
        pe = spy.info.get("trailingPE")
        if pe is not None:
            return round(float(pe), 1)
    except Exception:
        pass
    # Fallback: calculate from price and EPS
    try:
        spy = yf.Ticker("SPY")
        pe = spy.info.get("forwardPE")
        if pe is not None:
            return round(float(pe), 1)
    except Exception:
        pass
    return None


def get_vix() -> float | None:
    return _yf_latest("^VIX")


def get_treasury_10y() -> float | None:
    return _yf_latest("^TNX")


def get_treasury_3m() -> float | None:
    return _yf_latest("^IRX")


def get_treasury_10y_trend() -> str | None:
    """Check if 10Y yield is trending up or down (3-month lookback)."""
    try:
        tnx = yf.Ticker("^TNX")
        hist = tnx.history(period="3mo")
        if len(hist) < 10:
            return None
        recent = float(hist["Close"].iloc[-1])
        three_months_ago = float(hist["Close"].iloc[0])
        if recent > three_months_ago + 0.1:
            return "rising"
        elif recent < three_months_ago - 0.1:
            return "falling"
        return "flat"
    except Exception:
        return None


def get_sp500_drawdown() -> float | None:
    """Calculate S&P 500 drawdown from all-time high."""
    try:
        sp = yf.Ticker("^GSPC")
        hist = sp.history(period="2y")
        if hist.empty:
            return None
        ath = float(hist["Close"].max())
        current = float(hist["Close"].iloc[-1])
        drawdown = ((ath - current) / ath) * 100
        return round(drawdown, 2)
    except Exception:
        return None


def get_fear_greed() -> int | None:
    """Get CNN Fear & Greed Index value."""
    try:
        url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
            "Referer": "https://edition.cnn.com/markets/fear-and-greed",
        }
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            score = data.get("fear_and_greed", {}).get("score")
            if score is not None:
                return int(round(score))
    except Exception:
        pass
    return None


def get_fed_rate() -> float | None:
    """Get Fed Funds target upper rate from FRED (no API key needed)."""
    try:
        url = (
            "https://fred.stlouisfed.org/graph/fredgraph.csv?"
            "id=DFEDTARU&cosd=2025-01-01&coed=2030-12-31&fq=Daily%2C%207-Day&fam=avg"
        )
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        if r.status_code == 200:
            lines = r.text.strip().split("\n")
            last = lines[-1].split(",")
            if len(last) == 2 and last[1] != ".":
                return float(last[1])
    except Exception:
        pass
    return None


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
            # OBS_VALUE is column index 9
            if len(last) > 9:
                return float(last[9])
    except Exception:
        pass
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
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        if r.status_code == 200:
            lines = r.text.strip().split("\n")
            last = lines[-1].split(",")
            if len(last) >= 3:
                return float(last[2])
    except Exception:
        pass
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
