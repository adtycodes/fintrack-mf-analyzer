import streamlit as st
import pandas as pd
from datetime import date
from data_fetcher import DataFetcher
from portfolio_analyzer import PortfolioAnalyzer
from storage import save_portfolio, load_portfolio


@st.cache_data(ttl=86400)
def fetch_fund_names():
    return DataFetcher().get_all_fund_names()


DEFAULT_DATE = date(2000, 1, 1)


def main():
    st.set_page_config("FinTrack", layout="wide")

    st.title("FinTrack — Investment Tracker")

    st.caption(
        "🟢 Verified = unit-based | 🟡 Estimated = NAV-derived | 🔴 Incomplete = missing data"
    )

    if "portfolio" not in st.session_state:
        st.session_state.portfolio = load_portfolio()

    fetcher = DataFetcher()
    fund_names = fetch_fund_names()

    asset_type = st.radio("Asset Type", ["Stock", "Mutual Fund"], horizontal=True)
    inv_type = st.radio("Investment Type", ["Lumpsum", "SIP"], horizontal=True)

    with st.form("add_asset", clear_on_submit=True):
        st.subheader("Add Investment")

        name = (
            st.text_input("Stock Ticker")
            if asset_type == "Stock"
            else st.selectbox("Mutual Fund", fund_names)
        )

        amount = st.number_input("Amount Invested (₹)", min_value=1.0)
        pdate = st.date_input("Purchase Date", value=DEFAULT_DATE)

        submitted = st.form_submit_button("Add")

    if submitted:
        asset = {
            "Type": asset_type,
            "Name": name,
            "Investment Type": inv_type,
            "Amount Invested": amount,
            "Purchase Date": pdate,
        }

        st.session_state.portfolio.append(asset)
        save_portfolio(st.session_state.portfolio)
        st.success("Asset added")
        st.rerun()

    st.subheader("Portfolio")

    if not st.session_state.portfolio:
        st.info("No assets added")
        return

    for i, a in reversed(list(enumerate(st.session_state.portfolio))):
        cols = st.columns([2, 4, 2, 2, 2, 1])
        cols[0].write(a["Type"])
        cols[1].write(a["Name"])
        cols[2].write(f"₹{a['Amount Invested']:,.0f}")
        cols[3].write(a["Investment Type"])

        badge = a.get("Data Quality", "—")
        cols[4].write(badge)

        if cols[5].button("🗑️", key=f"del_{i}"):
            st.session_state.portfolio.pop(i)
            save_portfolio(st.session_state.portfolio)
            st.rerun()

    if st.button("Analyze Portfolio"):
        analyzer = PortfolioAnalyzer(fetcher)
        st.session_state.results = analyzer.analyze_portfolio(
            st.session_state.portfolio
        )
        st.rerun()

    results = st.session_state.get("results")
    if results:
        st.subheader("Summary")
        s = results["summary"]

        c1, c2, c3 = st.columns(3)
        c1.metric("Total Invested", f"₹{s['Total Invested']:,.0f}")
        c2.metric(
            "Current Value",
            f"₹{s['Total Current Value']:,.0f}",
            delta=f"₹{s['Total Gain/Loss']:,.0f}",
        )
        c3.metric("Portfolio XIRR", f"{s['Portfolio XIRR']}%")

        st.subheader("Details")
        df = pd.DataFrame(results["details"])
        st.dataframe(df, use_container_width=True)


if __name__ == "__main__":
    main()
