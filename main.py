import streamlit as st
import pandas as pd
from datetime import date
from data_fetcher import DataFetcher
from portfolio_analyzer import PortfolioAnalyzer
from storage import save_portfolio, load_portfolio


@st.cache_data(ttl=86400)
def fetch_fund_names():
    fetcher = DataFetcher()
    return fetcher.get_all_fund_names()


DEFAULT_DATE = date(2000, 1, 1)


def main():
    st.set_page_config(
        page_title="FinTrack - Investments Analyzer & Forecaster",
        layout="wide",
    )

    # ---------------- HEADER ----------------
    col1, col2 = st.columns([4, 1])
    with col1:
        st.title("FinTrack - Investments Analyzer & Forecaster")
    with col2:
        if st.button("🔄 Refresh fund list"):
            fetch_fund_names.clear()
            st.success("Fund list refreshed!")
            st.rerun()

    st.markdown(
        "Track and analyze your investments in **Mutual Funds and Stocks**.\n\n"
        "**If market data is unavailable, you can still proceed by entering NAV or Units manually.**"
    )

    # ---------------- LOAD PORTFOLIO ----------------
    if "portfolio" not in st.session_state:
        st.session_state.portfolio = load_portfolio()

    fetcher = DataFetcher()
    fund_names = fetch_fund_names()

    # ---------------- INPUT ----------------
    asset_type = st.radio("Select Asset Type", ["Stock", "Mutual Fund"], horizontal=True)
    inv_type = st.radio("Select Investment Type", ["Lumpsum", "SIP"], horizontal=True)

    with st.form("portfolio_form", clear_on_submit=True):
        st.subheader("➕ Add Investment")

        if asset_type == "Stock":
            asset_name = st.text_input("Stock Ticker (e.g. RELIANCE.NS)")
        else:
            asset_name = st.selectbox("Select Mutual Fund", fund_names)

        col1, col2 = st.columns(2)
        with col1:
            if inv_type == "SIP":
                amount_invested = st.number_input(
                    "Monthly SIP Amount (₹)", min_value=500.0, step=100.0
                )
            else:
                amount_invested = st.number_input(
                    "Amount Invested (₹)", min_value=1.0, step=1000.0
                )

        with col2:
            purchase_date = st.date_input(
                "Purchase Date (or SIP start date)",
                value=DEFAULT_DATE,
                max_value=date.today(),
            )

        submitted = st.form_submit_button("Add to Portfolio")

    # ---------------- ADD ASSET ----------------
    if submitted:
        if purchase_date == DEFAULT_DATE:
            st.warning("Please select a valid purchase date.")
            return

        if not asset_name or amount_invested <= 0:
            st.warning("Please fill all required fields.")
            return

        with st.spinner("Validating asset..."):
            if not fetcher.is_asset_valid(asset_type, asset_name):
                st.error(f"Invalid {asset_type}: {asset_name}")
                return

        purchase_nav = None
        units_owned = None

        # --- Try automatic price fetch for Lumpsum ---
        if inv_type == "Lumpsum":
            if asset_type == "Mutual Fund":
                purchase_nav = fetcher.get_historical_nav(asset_name, purchase_date)
            else:
                df = fetcher.get_stock_data(asset_name, purchase_date)
                if not df.empty:
                    purchase_nav = df["Close"].iloc[0]

        # --- Manual fallback ---
        if inv_type == "Lumpsum" and purchase_nav is None:
            st.warning("⚠️ Purchase price/NAV could not be fetched.")

            choice = st.radio(
                "How would you like to proceed?",
                ["I know the NAV / Buy Price", "I know the number of units / shares"],
                horizontal=True,
            )

            if choice == "I know the NAV / Buy Price":
                purchase_nav = st.number_input(
                    "Enter Purchase NAV / Buy Price", min_value=0.01
                )
                units_owned = amount_invested / purchase_nav
            else:
                units_owned = st.number_input(
                    "Enter Units / Shares Owned", min_value=0.0001
                )

        if inv_type == "SIP":
            st.info(
                "SIP added without units. Returns will be available once "
                "transaction-level data is added."
            )

        new_asset = {
            "Type": asset_type,
            "Name": asset_name,
            "Investment Type": inv_type,
            "Amount Invested": amount_invested,
            "Purchase Date": purchase_date,
            "Purchase NAV": purchase_nav,
            "Units Owned": units_owned,
        }

        st.session_state.portfolio.append(new_asset)
        save_portfolio(st.session_state.portfolio)
        st.session_state.pop("analysis_results", None)

        st.success(f"Added {asset_name} to portfolio.")
        st.rerun()

    # ---------------- PORTFOLIO LIST ----------------
    st.subheader("📂 Your Portfolio")

    if not st.session_state.portfolio:
        st.info("Portfolio is empty.")
    else:
        for i, asset in reversed(list(enumerate(st.session_state.portfolio))):
            cols = st.columns([2, 4, 2, 2, 1])
            cols[0].write(asset["Type"])
            cols[1].write(asset["Name"])
            cols[2].write(f"₹{asset['Amount Invested']:,.2f}")
            cols[3].write(asset["Purchase Date"].strftime("%d-%b-%Y"))

            if cols[4].button("🗑️", key=f"del_{i}"):
                st.session_state.portfolio.pop(i)
                save_portfolio(st.session_state.portfolio)
                st.session_state.pop("analysis_results", None)
                st.rerun()

    # ---------------- ANALYSIS ----------------
    if st.session_state.portfolio:
        if st.button("Analyze Portfolio"):
            with st.spinner("Analyzing portfolio..."):
                analyzer = PortfolioAnalyzer(fetcher)
                st.session_state.analysis_results = analyzer.analyze_portfolio(
                    st.session_state.portfolio
                )
            st.success("Analysis complete.")
            st.rerun()

    results = st.session_state.get("analysis_results")
    if results:
        st.subheader("📊 Portfolio Summary")

        summary = results["summary"]
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Invested", f"₹{summary['Total Invested']:,.2f}")
        c2.metric(
            "Current Value",
            f"₹{summary['Total Current Value']:,.2f}",
            delta=f"₹{summary['Total Gain/Loss']:,.2f}",
        )
        c3.metric("Portfolio XIRR", f"{summary.get('Portfolio XIRR', 'N/A')}%")

        st.subheader("📄 Detailed View")
        df = pd.DataFrame(results["details"])
        st.dataframe(df, use_container_width=True)


if __name__ == "__main__":
    main()
