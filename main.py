import streamlit as st
import pandas as pd
import numpy as np
import mftool as mf
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
from datetime import date
from data_fetcher import DataFetcher

@st.cache_data(ttl=86400) #Fetching list of mutual fund names
def fetch_fund_names():
    fetcher = DataFetcher()
    return fetcher.get_all_fund_names()
    
def main():
    st.set_page_config( #1. Configuration
        page_title = "FinTrack - Mutual Fund Portfolio Tracker",
        layout = "wide",
    )
    col1, col2 = st.columns([4, 1])
    with col1:
        st.title("FinTrack - Mutual Fund Portfolio Tracker")
    with col2:
        if st.button("🔄 Refresh fund list"):
            fetch_fund_names.clear()  # clears cache
            st.success("Fund list refreshed!")
            st.rerun()

    st.markdown("Track and analyze your mutual fund investments with ease.")
    st.markdown("Note: This is a work in progress. The full portfolio analysis feature is currently under development.")

    if 'portfolio' not in st.session_state: #3. Checking Session State
        st.session_state.portfolio = []

    fund_name = fetch_fund_names()
    asset_type = st.radio("Select Asset Type", ["Stock", "Mutual Fund"], horizontal=True)
    inv_type = st.radio("Select Investment Type", ["Lumpsum", "SIP"], horizontal=True)
    with st.form(key='portfolio_form', clear_on_submit=True): #4. Gathering MF/Stock Details
        st.subheader("Add to Portfolio")
        if asset_type == "Stock":
            asset_name = st.text_input("Stock Ticker", help="e.g., RELIANCE.NS for NSE stocks")
        else: # Mutual Fund
            asset_name = st.selectbox("Search and Select Mutual Fund", options=fund_name, help="Select a mutual fund from the list")
        col1, col2 = st.columns(2)
        with col1:
            if inv_type == "SIP":
                amount_invested = st.number_input("Monthly SIP Amount (₹)", min_value=500.0, step=100.0, help="Minimum ₹500 for SIP")
            else: 
                amount_invested = st.number_input("Amount Invested (₹)", min_value=1.0, step=1000.0)
            
        with col2:
            purchase_date = st.date_input("Date of Purchase: (In case of SIP, use the date of the first installment)", value=None, max_value=date.today())
        submitted = st.form_submit_button("Add to Portfolio")

    fetcher = DataFetcher()  # Initialize the data fetcher
    if submitted:
        if not asset_name or not amount_invested or not purchase_date:
            st.warning("Please fill out all the fields.")
        else:
            with st.spinner(f"Validating {asset_name}..."):
                is_valid = fetcher.is_asset_valid(asset_type, asset_name)
            if is_valid:
                # If the asset is valid, create the dictionary
                new_asset = {
                    "Type": asset_type,
                    "Name": asset_name,
                    "Amount Invested": amount_invested,
                    "Purchase Date": purchase_date,
                    "Investment Type": inv_type 
                }
                # Append the asset to the portfolio
                st.session_state.portfolio.append(new_asset)
                st.success(f"Added {asset_name} to your portfolio!")
                st.rerun()
            else:
                # If the ticker is invalid, show an error and do not add it
                st.error(f"Invalid {asset_type}: '{asset_name}'. Please provide a valid ticker, e.g., 'RELIANCE.NS'.")

    st.subheader("Your Current Portfolio")
    if not st.session_state.portfolio:
        st.info("Your portfolio is empty. Add an asset using the form above.")
    else:
        col1, col2, col3, col4, col5, col6 = st.columns([2, 4, 1, 1, 1, 1])
        col1.write("**Asset Type**")
        col2.write("**Name**")
        col3.write("**Amount Invested**")
        col4.write("**Purchase Date**")
        col5.write("Lumpsum/SIP")
        col6.write("**Actions**")

        for i, item in reversed(list(enumerate(st.session_state.portfolio))):
            col1, col2, col3, col4, col5, col6 = st.columns([2, 4, 1, 1, 1, 1])
            
            # Display the investment details
            col1.text(item["Type"])
            col2.text(item["Name"])
            col3.text(f"₹{item['Amount Invested']:,.2f}")
            col4.text(item["Purchase Date"].strftime("%d-%b-%Y"))
            col5.text(item.get("Investment Type"))
            
            # Create a delete button in the 'Actions' column
            # A unique key is ESSENTIAL for buttons inside a loop
            if col6.button("Delete", key=f"delete_{i}"):
                # If the delete button is clicked, remove the item from the portfolio list
                st.session_state.portfolio.pop(i)
                # Rerun the app to immediately show the updated portfolio
                st.rerun()

    # --- The Main Analyze Button ---
    if st.session_state.portfolio:
        if st.button("Analyze Full Portfolio"):
            # The analysis logic will go here
            st.info("Analysis logic is the next big step!")

    #7. Analysis 
if __name__ == "__main__":
    main()