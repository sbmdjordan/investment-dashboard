"""Investment Allocation Dashboard — Streamlit UI."""

import streamlit as st

st.set_page_config(page_title="Investment Allocation", layout="wide")

from src.data_sources import fetch_all
from src.scoring import calculate_allocation

SIGNAL_INFO = {
    "Valuation (P/E)": (
        "**Price-to-Earnings ratio** — how many years of profits "
        "you're paying for when you buy the stock market.\n\n"
        "| P/E | Meaning |\n|---|---|\n"
        "| Under 15 | Cheap — good time to buy |\n"
        "| 15-20 | Fair value |\n"
        "| 20-25 | Expensive |\n"
        "| Over 25 | Very expensive |\n\n"
        "Lower = cheaper market = lean offensive."
    ),
    "Equity Risk Premium": (
        "**Are stocks worth the risk vs bonds?**\n\n"
        "Compares what the stock market earns (earnings yield) "
        "vs what safe government bonds pay.\n\n"
        "ERP = (1 / P/E ratio) - 10Y bond yield\n\n"
        "| ERP | Meaning |\n|---|---|\n"
        "| Over 4% | Stocks are a good deal |\n"
        "| 2-4% | Neutral |\n"
        "| Under 2% | Bonds look better |\n\n"
        "Higher = stocks more attractive = lean offensive."
    ),
    "Rate Trend": (
        "**Is borrowing getting cheaper or more expensive?**\n\n"
        "Tracks the 10-year US Treasury yield over the last 3 months.\n\n"
        "| Trend | What happens |\n|---|---|\n"
        "| Rising | Money costs more, slows growth |\n"
        "| Falling | Cheaper money, fuels growth |\n\n"
        "Rising = lean defensive. Falling = lean offensive."
    ),
    "Fear & Greed": (
        "**CNN's investor emotion index** (0-100).\n\n"
        "Combines 7 market signals: stock momentum, "
        "stock price strength, breadth, put/call ratio, "
        "junk bond demand, volatility, and safe haven demand.\n\n"
        "| Score | Mood |\n|---|---|\n"
        "| 0-25 | Panic |\n| 25-45 | Fear |\n"
        "| 45-55 | Neutral |\n| 55-75 | Greed |\n"
        "| 75-100 | Euphoria |\n\n"
        '"Be greedy when others are fearful."'
    ),
    "VIX": (
        '**"Wall Street\'s fear gauge"** — measures how much '
        "the market expects prices to swing over the next 30 days.\n\n"
        "Calculated from S&P 500 options prices.\n\n"
        "| VIX | Meaning |\n|---|---|\n"
        "| Under 15 | Very calm (complacency) |\n"
        "| 15-25 | Normal |\n"
        "| 25-35 | Fearful |\n"
        "| Over 35 | Panic |\n\n"
        "High fear = potential buying opportunity."
    ),
    "Drawdown": (
        "**How far the S&P 500 has fallen from its all-time high.**\n\n"
        "| Drop | Meaning |\n|---|---|\n"
        "| 0-5% | Near highs (complacency) |\n"
        "| 5-15% | Normal pullback |\n"
        "| 15-30% | Fearful territory |\n"
        "| Over 30% | Crisis |\n\n"
        "Bigger drops = more fear = potential opportunity."
    ),
    "Yield Curve": (
        "**Gap between long-term (10Y) and short-term (3M) interest rates.**\n\n"
        "Normally long-term rates are higher (positive spread). "
        "When short-term rates exceed long-term (inverted), "
        "it's one of the strongest recession warning signals.\n\n"
        "| Spread | Meaning |\n|---|---|\n"
        "| Positive | Normal — economy healthy |\n"
        "| Flat | Caution |\n"
        "| Negative | Inverted — recession risk |\n\n"
        "Inverted = lean defensive."
    ),
}


def signal_color(score: int) -> str:
    if score >= 2:
        return "#22c55e"
    elif score == 1:
        return "#86efac"
    elif score == 0:
        return "#9ca3af"
    elif score == -1:
        return "#fca5a5"
    else:
        return "#ef4444"


def render_gauge(label: str, pct: int, color: str):
    st.markdown(
        f"""
        <div style="text-align:center;">
            <div style="font-size:3rem; font-weight:bold; color:{color};">{pct}%</div>
            <div style="font-size:1.1rem; color:#ccc;">{label}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main():
    st.title("Investment Allocation Dashboard")
    st.caption("Monthly macro signal monitor — Offence vs Defence")

    # --- Fetch data ---
    with st.spinner("Fetching market data..."):
        data = fetch_all()

    result = calculate_allocation(data)

    # --- Sidebar ---
    with st.sidebar:
        st.header("Allocation Overrides")
        st.caption("Adjust from the system's suggestion if needed")

        offence_override = st.slider(
            "Offence %",
            min_value=25,
            max_value=75,
            value=result["offence_pct"],
            step=5,
            help="The system suggests this value based on macro signals. Slide to override.",
        )
        defence_override = 100 - offence_override

        st.divider()
        st.subheader("Inside Offence")
        stocks_pct = st.slider("Stocks %", 0, 100, 60, 5)
        btc_pct = 100 - stocks_pct
        st.caption(f"Bitcoin: {btc_pct}%")

        st.subheader("Inside Defence")
        bonds_pct = st.slider("Bonds/Gilts %", 0, 100, 70, 5)
        gold_pct = 100 - bonds_pct
        st.caption(f"Gold: {gold_pct}%")

    # --- Top: Allocation suggestion ---
    hdr_col, info_col = st.columns([6, 1])
    with hdr_col:
        st.header("Suggested Allocation")
    with info_col:
        with st.popover("i", use_container_width=True):
            st.markdown(
                "The system scores 7 macro signals from **-2 to +2** each.\n\n"
                "Positive total = market looks favourable = more offence.\n"
                "Negative total = caution = more defence.\n\n"
                "Offence (stocks + BTC) always stays between **25-75%**.\n"
                "Defence (bonds + gold) is the remainder."
            )

    col1, col2, col3 = st.columns([2, 1, 2])
    with col1:
        render_gauge("Offence", result["offence_pct"], "#22c55e")
        st.caption("Stocks + Bitcoin")
    with col2:
        score = result["total_score"]
        color = "#22c55e" if score > 0 else "#ef4444" if score < 0 else "#9ca3af"
        st.markdown(
            f'<div style="text-align:center; padding-top:0.5rem;">'
            f'<div style="font-size:2rem; font-weight:bold; color:{color};">Score: {score:+d}</div>'
            f'<div style="font-size:0.9rem; color:#888;">Range: -9 to +9</div>'
            f"</div>",
            unsafe_allow_html=True,
        )
    with col3:
        render_gauge("Defence", result["defence_pct"], "#3b82f6")
        st.caption("Bonds/Gilts + Gold")

    # --- Signals breakdown ---
    st.header("Signal Breakdown")

    # Build signal rows as a single HTML block for clean alignment
    rows_html = ""
    for name, score, desc in result["signals"]:
        bar_color = signal_color(score)
        bar_width = max(abs(score) * 25, 8)
        score_color = signal_color(score)
        rows_html += (
            f'<div style="display:flex; align-items:center; padding:0.6rem 0; '
            f'border-bottom:1px solid rgba(255,255,255,0.06);">'
            f'  <div style="width:160px; font-weight:600; flex-shrink:0;">{name}</div>'
            f'  <div style="flex:1; padding:0 1rem;">'
            f'    <div style="background:rgba(255,255,255,0.05); border-radius:4px; height:1.2rem; position:relative;">'
            f'      <div style="width:{bar_width}%; background:{bar_color}; height:100%; border-radius:4px;'
            f'        {"margin-left:auto;" if score < 0 else ""}"></div>'
            f"    </div>"
            f'    <div style="font-size:0.78rem; color:#888; margin-top:2px;">{desc}</div>'
            f"  </div>"
            f'  <div style="width:50px; text-align:center; font-size:1.3rem; font-weight:bold; '
            f'color:{score_color}; flex-shrink:0;">{score:+d}</div>'
            f"</div>"
        )

    st.markdown(
        f'<div style="margin-bottom:1rem;">{rows_html}</div>',
        unsafe_allow_html=True,
    )

    # Info buttons in a row below the table
    info_cols = st.columns(len(result["signals"]))
    for i, (name, _, _) in enumerate(result["signals"]):
        with info_cols[i]:
            if name in SIGNAL_INFO:
                with st.popover(f"i {name.split('(')[0].strip()}", use_container_width=True):
                    st.markdown(SIGNAL_INFO[name])

    # --- Extra indicators ---
    hdr2_col, info2_col = st.columns([6, 1])
    with hdr2_col:
        st.header("Additional Indicators")
    with info2_col:
        with st.popover("i", use_container_width=True):
            st.markdown(
                "These are extra context — they don't directly affect the score "
                "but help you understand the environment.\n\n"
                "**Policy rates** are auto-fetched from the Fed, ECB, and Bank of England. "
                "Higher average = tighter money = generally defensive."
            )

    ic1, ic2, ic3 = st.columns(3)
    with ic1:
        avg = data.get("avg_policy_rate")
        st.metric("Avg Policy Rate", f"{avg:.2f}%" if avg else "N/A")
        fed = data.get("fed_rate")
        ecb = data.get("ecb_rate")
        boe = data.get("boe_rate")
        parts = []
        if fed is not None:
            parts.append(f"Fed {fed}%")
        if ecb is not None:
            parts.append(f"ECB {ecb}%")
        if boe is not None:
            parts.append(f"BoE {boe}%")
        st.caption(" / ".join(parts) if parts else "Could not fetch rates")
    with ic2:
        t10 = data.get("treasury_10y")
        st.metric("10Y Treasury", f"{t10:.2f}%" if t10 else "N/A")
        trend = data.get("rate_trend", "N/A")
        st.caption(f"3-month trend: {trend}")
    with ic3:
        spread = data.get("yield_curve_spread")
        st.metric("Yield Curve (10Y-3M)", f"{spread:+.2f}%" if spread is not None else "N/A")
        if spread is not None:
            st.caption("Inverted" if spread < 0 else "Normal" if spread > 0.2 else "Flat")

    # --- Monthly Investment Calculator ---
    st.header("Monthly Investment Calculator")

    monthly_amount = st.number_input(
        "Amount available to invest this month",
        min_value=0.0,
        value=500.0,
        step=50.0,
        format="%.2f",
        key="monthly_amount",
    )

    if monthly_amount > 0:
        offence_amount = monthly_amount * (offence_override / 100)
        defence_amount = monthly_amount * (defence_override / 100)

        stocks_amount = offence_amount * (stocks_pct / 100)
        btc_amount = offence_amount * (btc_pct / 100)
        bonds_amount = defence_amount * (bonds_pct / 100)
        gold_amount = defence_amount * (gold_pct / 100)

        st.markdown("---")

        col_off, col_def = st.columns(2)

        with col_off:
            st.markdown(
                f'<div style="background:#1a2e1a; padding:1.2rem; border-radius:8px; border-left:4px solid #22c55e;">'
                f'<div style="font-size:1.1rem; font-weight:bold; color:#22c55e;">Offence — £{offence_amount:,.2f} ({offence_override}%)</div>'
                f'<div style="margin-top:0.8rem;">'
                f'<div style="display:flex; justify-content:space-between; padding:0.3rem 0;"><span>Stocks</span><span style="font-weight:bold;">£{stocks_amount:,.2f}</span></div>'
                f'<div style="display:flex; justify-content:space-between; padding:0.3rem 0;"><span>Bitcoin</span><span style="font-weight:bold;">£{btc_amount:,.2f}</span></div>'
                f"</div></div>",
                unsafe_allow_html=True,
            )

        with col_def:
            st.markdown(
                f'<div style="background:#1a1a2e; padding:1.2rem; border-radius:8px; border-left:4px solid #3b82f6;">'
                f'<div style="font-size:1.1rem; font-weight:bold; color:#3b82f6;">Defence — £{defence_amount:,.2f} ({defence_override}%)</div>'
                f'<div style="margin-top:0.8rem;">'
                f'<div style="display:flex; justify-content:space-between; padding:0.3rem 0;"><span>Bonds/Gilts</span><span style="font-weight:bold;">£{bonds_amount:,.2f}</span></div>'
                f'<div style="display:flex; justify-content:space-between; padding:0.3rem 0;"><span>Gold</span><span style="font-weight:bold;">£{gold_amount:,.2f}</span></div>'
                f"</div></div>",
                unsafe_allow_html=True,
            )

        st.markdown("")
        st.markdown(
            f"**Total: £{monthly_amount:,.2f}** — "
            f"Stocks £{stocks_amount:,.2f} · Bitcoin £{btc_amount:,.2f} · "
            f"Bonds £{bonds_amount:,.2f} · Gold £{gold_amount:,.2f}"
        )


if __name__ == "__main__":
    main()
