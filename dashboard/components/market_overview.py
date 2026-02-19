"""Market Overview component."""

import streamlit as st
import pandas as pd
from utils.helpers import format_price, format_percentage, format_large_number


def render_market_overview(services, watchlist):
    """Render the Market Overview tab."""

    if not watchlist:
        st.info("👆 Add stocks to your watchlist using the sidebar")
        return

    with st.spinner("Fetching market data…"):
        stocks_data = services['market'].get_multiple_stocks(watchlist)

    if not stocks_data:
        st.error("Unable to fetch market data. Please check your internet connection.")
        return

    # ── Summary bar ───────────────────────────────────────────────────────────
    total  = len(stocks_data)
    gainers = sum(1 for s in stocks_data.values() if s.change_percent > 0)
    losers  = sum(1 for s in stocks_data.values() if s.change_percent < 0)
    flat    = total - gainers - losers
    avg_chg = sum(s.change_percent for s in stocks_data.values()) / total

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Tracked",    total)
    c2.metric("🟢 Gainers", gainers)
    c3.metric("🔴 Losers",  losers)
    c4.metric("⬜ Flat",    flat)
    c5.metric("Avg Change", format_percentage(avg_chg),
              delta_color="normal" if avg_chg >= 0 else "inverse")

    st.divider()

    # ── Sortable summary table ────────────────────────────────────────────────
    rows = []
    for sym, s in stocks_data.items():
        rows.append({
            "Symbol":     sym,
            "Price":      s.current_price,
            "Change %":   round(s.change_percent, 2),
            "Volume":     s.volume,
            "Market Cap": s.market_cap,
            "P/E":        round(s.pe_ratio, 2) if s.pe_ratio else None,
        })

    df = pd.DataFrame(rows)

    # Colour the Change % column
    def _colour_change(val):
        color = "#00c853" if val > 0 else ("#d32f2f" if val < 0 else "#888")
        return f"color: {color}; font-weight: bold"

    st.dataframe(
        df.style.applymap(_colour_change, subset=["Change %"])
               .format({
                   "Price":      lambda v: format_price(v) if v else "—",
                   "Change %":   lambda v: f"{v:+.2f}%",
                   "Volume":     lambda v: format_large_number(v) if v else "—",
                   "Market Cap": lambda v: format_large_number(v) if v else "—",
                   "P/E":        lambda v: f"{v:.1f}" if v else "—",
               }),
        use_container_width=True,
        hide_index=True,
        height=min(42 + 35 * total, 500),
    )

    st.divider()

    # ── Expanded detail cards (collapsible per stock) ─────────────────────────
    st.subheader("Stock Detail")
    for sym, stock in stocks_data.items():
        chg_emoji = "🟢" if stock.change_percent >= 0 else "🔴"
        with st.expander(
            f"{chg_emoji} **{sym}** — {format_price(stock.current_price)}  "
            f"({stock.change_percent:+.2f}%)",
            expanded=False,
        ):
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Price",      format_price(stock.current_price),
                      f"{stock.change_percent:+.2f}%",
                      delta_color="normal" if stock.change_percent >= 0 else "inverse")
            c2.metric("Volume",     format_large_number(stock.volume))
            c3.metric("Market Cap", format_large_number(stock.market_cap))
            c4.metric("P/E Ratio",  f"{stock.pe_ratio:.1f}" if stock.pe_ratio else "—")

            if stock.moving_averages:
                ma_cols = st.columns(len(stock.moving_averages))
                for col, (key, value) in zip(ma_cols, stock.moving_averages.items()):
                    if value:
                        col.caption(f"**{key.upper()}:** {format_price(value)}")

