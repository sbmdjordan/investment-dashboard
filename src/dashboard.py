"""Investment Allocation Dashboard — Streamlit UI."""

import streamlit as st

st.set_page_config(page_title="Investment Allocation", layout="wide")

from data_sources import fetch_all
from scoring import calculate_allocation

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
        "Direction of the 10Y Treasury yield over 3 months.\n\n"
        "This reflects where the market thinks interest rates are heading "
        "— it moves before central banks actually change rates.\n\n"
        "Rising: money getting more expensive, lean defensive.\n"
        "Falling: money getting cheaper, lean offensive.\n"
        "Flat: no clear direction."
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
        "10Y bond yield minus 3M bond yield.\n\n"
        "Above +0.5% — healthy economy, lean offensive.\n"
        "0% to +0.5% — flat, caution.\n"
        "Below 0% — inverted, recession warning, lean defensive.\n\n"
        "Inversion has predicted every US recession since the 1970s."
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


def render_gauge(label: str, pct: int, color: str, subtitle: str = ""):
    sub_html = f'<div style="font-size:0.85rem; color:#888; margin-top:0.2rem; margin-bottom:2.5rem;">{subtitle}</div>' if subtitle else ""
    st.markdown(
        f"""
        <div style="text-align:center;">
            <div style="font-size:3rem; font-weight:bold; color:{color};">{pct}%</div>
            <div style="font-size:1.1rem; color:#ccc;">{label}</div>
            {sub_html}
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
        render_gauge("Offence", result["offence_pct"], "#22c55e", "Stocks + Bitcoin")
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
        render_gauge("Defence", result["defence_pct"], "#3b82f6", "Bonds/Gilts + Gold")

    # --- Signals + Additional Indicators side by side ---
    signals_col, indicators_col = st.columns([2, 1])

    with signals_col:
        st.markdown(
            '<h2 style="font-weight:600; padding:0.6rem 0;">Signal Breakdown</h2>',
            unsafe_allow_html=True,
        )

        # Tooltip CSS (injected once)
        st.markdown(
            """<style>
            .sig-tip { position:relative; display:inline-flex; align-items:center;
                       cursor:help; margin-left:6px; }
            .sig-tip .tip-icon { font-size:0.7rem; font-style:italic; color:#666;
                                 border:1px solid #555; border-radius:50%;
                                 width:16px; height:16px; display:inline-flex;
                                 align-items:center; justify-content:center;
                                 flex-shrink:0; }
            .sig-tip .tip-text { visibility:hidden; opacity:0;
                                 background:#1e1e2e; color:#ccc; border:1px solid #333;
                                 border-radius:6px; padding:0.6rem 0.8rem;
                                 font-size:0.78rem; font-weight:400; line-height:1.4;
                                 width:280px; position:absolute; left:24px; top:50%;
                                 transform:translateY(-50%); z-index:999;
                                 transition:opacity 0.15s; pointer-events:none; }
            .sig-tip:hover .tip-text { visibility:visible; opacity:1; }
            </style>""",
            unsafe_allow_html=True,
        )

        for name, score, desc in result["signals"]:
            bar_color = signal_color(score)
            bar_width = max(abs(score) * 25, 8)
            score_color = signal_color(score)
            tip = SIGNAL_INFO.get(name, "")
            # Strip markdown for HTML tooltip (simple plain-text version)
            tip_plain = tip.replace("**", "").replace("\n\n", "<br>").replace("\n", "<br>").replace("|", " ").replace("---", "")

            row_html = (
                f'<div style="display:flex; align-items:center; padding:0.5rem 0;">'
                f'  <div style="width:190px; font-weight:600; flex-shrink:0; display:flex; align-items:center;">'
                f'    {name}'
                f'    <span class="sig-tip"><span class="tip-icon">i</span>'
                f'      <span class="tip-text">{tip_plain}</span></span>'
                f'  </div>'
                f'  <div style="flex:1; padding:0 1rem;">'
                f'    <div style="background:rgba(255,255,255,0.05); border-radius:4px; height:1.2rem;">'
                f'      <div style="width:{bar_width}%; background:{bar_color}; height:100%; border-radius:4px;'
                f'        {"margin-left:auto;" if score < 0 else ""}"></div>'
                f"    </div>"
                f'    <div style="font-size:0.78rem; color:#888; margin-top:2px;">{desc}</div>'
                f"  </div>"
                f'  <div style="width:50px; text-align:center; font-size:1.3rem; font-weight:bold; '
                f'color:{score_color}; flex-shrink:0;">{score:+d}</div>'
                f"</div>"
            )
            st.markdown(row_html, unsafe_allow_html=True)

    with indicators_col:
        st.markdown(
            '<h2 style="text-align:center; font-weight:600; padding:0.6rem 0;">Indicators</h2>',
            unsafe_allow_html=True,
        )

        avg = data.get("avg_policy_rate")
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
        rates_caption = " / ".join(parts) if parts else "Could not fetch rates"

        t10 = data.get("treasury_10y")
        trend = data.get("rate_trend", "N/A")
        spread = data.get("yield_curve_spread")
        spread_label = ""
        if spread is not None:
            spread_label = "Inverted" if spread < 0 else "Normal" if spread > 0.2 else "Flat"

        indicators_html = f"""
        <div style="text-align:center; padding-top:0.5rem;">
            <div style="margin-bottom:1.5rem;">
                <div style="font-size:0.85rem; color:#888;">Avg Policy Rate</div>
                <div style="font-size:2rem; font-weight:700;">{f'{avg:.2f}%' if avg else 'N/A'}</div>
                <div style="font-size:0.75rem; color:#666;">{rates_caption}</div>
            </div>
            <div style="margin-bottom:1.5rem;">
                <div style="font-size:0.85rem; color:#888;">10Y Treasury</div>
                <div style="font-size:2rem; font-weight:700;">{f'{t10:.2f}%' if t10 else 'N/A'}</div>
                <div style="font-size:0.75rem; color:#666;">3-month trend: {trend}</div>
            </div>
            <div>
                <div style="font-size:0.85rem; color:#888;">Yield Curve (10Y-3M)</div>
                <div style="font-size:2rem; font-weight:700;">{f'{spread:+.2f}%' if spread is not None else 'N/A'}</div>
                <div style="font-size:0.75rem; color:#666;">{spread_label}</div>
            </div>
        </div>
        """
        st.markdown(indicators_html, unsafe_allow_html=True)

    # --- Monthly Investment Calculator ---
    st.header("Monthly Investment Calculator")

    calc_left, calc_right = st.columns(2)

    with calc_left:
        amount_str = st.text_input(
            "Amount available to invest this month",
            value="",
            placeholder="",
            key="monthly_amount",
        )
        try:
            monthly_amount = float(amount_str) if amount_str.strip() else 0.0
        except ValueError:
            monthly_amount = 0.0
            st.warning("Please enter a valid number.")

    offence_amount = monthly_amount * (offence_override / 100)
    defence_amount = monthly_amount * (defence_override / 100)

    stocks_amount = offence_amount * (stocks_pct / 100)
    btc_amount = offence_amount * (btc_pct / 100)
    bonds_amount = defence_amount * (bonds_pct / 100)
    gold_amount = defence_amount * (gold_pct / 100)

    def fmt(val: float) -> str:
        return f"£{val:,.2f}" if monthly_amount > 0 else "—"

    with calc_right:
        st.markdown(
            f'<div style="display:flex; gap:1rem; padding-top:0.5rem;">'
            f'  <div style="flex:1; background:#1a2e1a; padding:1rem; border-radius:8px; border-left:4px solid #22c55e;">'
            f'    <div style="font-size:0.95rem; font-weight:bold; color:#22c55e;">Offence — {fmt(offence_amount)} ({offence_override}%)</div>'
            f'    <div style="margin-top:0.6rem;">'
            f'      <div style="display:flex; justify-content:space-between; padding:0.2rem 0;"><span>Stocks</span><span style="font-weight:bold;">{fmt(stocks_amount)}</span></div>'
            f'      <div style="display:flex; justify-content:space-between; padding:0.2rem 0;"><span>Bitcoin</span><span style="font-weight:bold;">{fmt(btc_amount)}</span></div>'
            f'    </div>'
            f'  </div>'
            f'  <div style="flex:1; background:#1a1a2e; padding:1rem; border-radius:8px; border-left:4px solid #3b82f6;">'
            f'    <div style="font-size:0.95rem; font-weight:bold; color:#3b82f6;">Defence — {fmt(defence_amount)} ({defence_override}%)</div>'
            f'    <div style="margin-top:0.6rem;">'
            f'      <div style="display:flex; justify-content:space-between; padding:0.2rem 0;"><span>Bonds/Gilts</span><span style="font-weight:bold;">{fmt(bonds_amount)}</span></div>'
            f'      <div style="display:flex; justify-content:space-between; padding:0.2rem 0;"><span>Gold</span><span style="font-weight:bold;">{fmt(gold_amount)}</span></div>'
            f'    </div>'
            f'  </div>'
            f'</div>',
            unsafe_allow_html=True,
        )


if __name__ == "__main__":
    main()
