"""Allocation engine: score macro signals and output offence/defence split."""


def score_valuation(pe: float | None) -> tuple[int, str]:
    """Score based on S&P 500 P/E ratio."""
    if pe is None:
        return 0, "No data"
    if pe < 15:
        return 2, f"Cheap (P/E {pe:.1f})"
    elif pe <= 20:
        return 1, f"Fair-cheap (P/E {pe:.1f})"
    elif pe <= 25:
        return -1, f"Expensive (P/E {pe:.1f})"
    else:
        return -2, f"Very expensive (P/E {pe:.1f})"


def score_erp(pe: float | None, treasury_10y: float | None) -> tuple[int, str]:
    """Score Equity Risk Premium = earnings yield - 10Y yield."""
    if pe is None or treasury_10y is None or pe <= 0:
        return 0, "No data"
    earnings_yield = (1 / pe) * 100
    erp = earnings_yield - treasury_10y
    if erp > 4:
        return 2, f"Stocks attractive (ERP {erp:.1f}%)"
    elif erp >= 2:
        return 0, f"Neutral (ERP {erp:.1f}%)"
    else:
        return -2, f"Stocks expensive (ERP {erp:.1f}%)"


def score_rate_trend(trend: str | None) -> tuple[int, str]:
    """Score based on interest rate direction."""
    if trend is None:
        return 0, "No data"
    if trend == "rising":
        return -1, "Rates rising"
    elif trend == "falling":
        return 1, "Rates falling"
    return 0, "Rates flat"


def score_fear_greed(fg: int | None) -> tuple[int, str]:
    """Score based on CNN Fear & Greed index."""
    if fg is None:
        return 0, "No data"
    if fg <= 25:
        return 2, f"Panic ({fg})"
    elif fg <= 45:
        return 1, f"Fear ({fg})"
    elif fg <= 55:
        return 0, f"Neutral ({fg})"
    elif fg <= 75:
        return -1, f"Greed ({fg})"
    else:
        return -2, f"Euphoria ({fg})"


def score_vix(vix: float | None) -> tuple[int, str]:
    """Score based on VIX level."""
    if vix is None:
        return 0, "No data"
    if vix >= 35:
        return 2, f"Panic (VIX {vix:.1f})"
    elif vix >= 25:
        return 1, f"Fear (VIX {vix:.1f})"
    elif vix >= 15:
        return 0, f"Normal (VIX {vix:.1f})"
    else:
        return -1, f"Complacency (VIX {vix:.1f})"


def score_drawdown(dd: float | None) -> tuple[int, str]:
    """Score based on S&P 500 drawdown from ATH."""
    if dd is None:
        return 0, "No data"
    if dd >= 30:
        return 2, f"Crisis (-{dd:.1f}%)"
    elif dd >= 15:
        return 1, f"Fear (-{dd:.1f}%)"
    elif dd >= 5:
        return 0, f"Normal (-{dd:.1f}%)"
    else:
        return -1, f"Near highs (-{dd:.1f}%)"


def score_yield_curve(spread: float | None) -> tuple[int, str]:
    """Score based on 10Y-2Y yield curve spread."""
    if spread is None:
        return 0, "No data"
    if spread < -0.2:
        return -1, f"Inverted ({spread:+.2f}%)"
    elif spread < 0.2:
        return 0, f"Flat ({spread:+.2f}%)"
    else:
        return 1, f"Normal ({spread:+.2f}%)"


def calculate_allocation(data: dict) -> dict:
    """Calculate full allocation from indicator data.

    Returns dict with scores, total, offence %, defence %.
    """
    signals = [
        ("Valuation (P/E)", *score_valuation(data["sp500_pe"])),
        ("Equity Risk Premium", *score_erp(data["sp500_pe"], data["treasury_10y"])),
        ("Rate Trend", *score_rate_trend(data["rate_trend"])),
        ("Fear & Greed", *score_fear_greed(data["fear_greed"])),
        ("VIX", *score_vix(data["vix"])),
        ("Drawdown", *score_drawdown(data["sp500_drawdown"])),
        ("Yield Curve", *score_yield_curve(data["yield_curve_spread"])),
    ]

    total = sum(s[1] for s in signals)

    # Map score to offence %
    if total >= 4:
        offence_pct = 75
    elif total >= 2:
        offence_pct = 60
    elif total >= -1:
        offence_pct = 50
    elif total >= -3:
        offence_pct = 40
    else:
        offence_pct = 25

    return {
        "signals": signals,  # list of (name, score, description)
        "total_score": total,
        "offence_pct": offence_pct,
        "defence_pct": 100 - offence_pct,
    }
