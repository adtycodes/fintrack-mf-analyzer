# data_fetcher.py

import mftool as mf 
import yfinance as yf
import pandas as pd
from datetime import date, timedelta
import logging  # used to log errors and info messages

class DataFetcher:
    def __init__(self):  # this line sets up the mftool instance and initializes logging
        self.mf_toolkit = mf.Mftool()  # this line initializes the mftool instance
        self._scheme_codes = None  # this line starts caching process with initially None
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)  # this line sets up the logger for this class, setting up the format

    def is_asset_valid(self, asset_type, asset_name):
        max_range = 3
        for i in range(max_range):
            try:
                self.logger.info(f"Validating asset: {asset_type}: {asset_name}")
                if asset_type == "Mutual Fund":
                    return True
                elif asset_type == "Stock":
                    self.logger.info(f"Validating stock ticker: {asset_name}")
                    stock = yf.Ticker(asset_name)
                    if stock.info and 'currency' in stock.info:
                        self.logger.info(f"Stock {asset_name} is valid.")
                        return True
                    else:
                        self.logger.warning(f"Stock {asset_name} is not valid.")
                        return False
            except Exception as e:
                self.logger.error(f"Error validating asset {asset_name}: {e}")
                return False

    def _fetch_scheme_codes(self):
        try:
            self.logger.info("Fetching scheme codes...")
            scheme_codes = self.mf_toolkit.get_scheme_codes()  # attains the scheme codes from mftool
            if not scheme_codes:
                raise ValueError("No scheme codes found.")  # if no scheme codes are found, it raises an error
            return scheme_codes
        except Exception as e:
            self.logger.error(f"Error fetching scheme codes: {e}")
            return {}

    def get_all_fund_names(self):
        if self._scheme_codes is None:  # checks for cached scheme codes
            self.logger.info("Fetching scheme codes for fund names...")
            self._scheme_codes = self._fetch_scheme_codes()  # fetches scheme codes if not cached
        return list(self._scheme_codes.values()) if self._scheme_codes else []  # if not empty return list, else []

    # ------------------------------------------------------
    # FIX 1: ADD MISSING get_scheme_code (ABSOLUTELY REQUIRED)
    # ------------------------------------------------------
    def get_scheme_code(self, fund_name):
        try:
            if self._scheme_codes is None:
                self._scheme_codes = self._fetch_scheme_codes()

            for code, name in self._scheme_codes.items():
                if name.lower().strip() == fund_name.lower().strip():
                    return code

            self.logger.error(f"Scheme code not found for {fund_name}")
            return None

        except Exception as e:
            self.logger.error(f"Error fetching scheme code for {fund_name}: {e}")
            return None

    # ------------------------------------------------------
    # FIX 2: corrected get_historical_nav to use get_scheme_code
    # ------------------------------------------------------
    def get_historical_nav(self, fund_name, purchase_date):
        try:
            scheme_code = self.get_scheme_code(fund_name)
            if not scheme_code:
                self.logger.error(f"Scheme code not found for {fund_name}")
                return None

            fallback_days = [0, 1, 2, 3, 5, 7, 10, 15, 30, 45, 60]

            for days in fallback_days:
                fetch_date = purchase_date - timedelta(days=days)

                nav_list = self.mf_toolkit.get_scheme_historical_nav(
                    scheme_code, fetch_date, fetch_date
                )

                if nav_list and isinstance(nav_list, list):
                    nav_entry = nav_list[0]
                    nav = nav_entry.get("nav")

                    if nav and float(nav) > 0:
                        self.logger.info(
                            f"Fetched NAV for {fund_name} using date {fetch_date}"
                        )
                        return float(nav)

            self.logger.error(
                f"Failed NAV fetch for {fund_name} for original date {purchase_date}"
            )
            return None

        except Exception as e:
            self.logger.error(
                f"Error fetching NAV for {fund_name} on {purchase_date}: {e}"
            )
            return None

    def get_stock_data(self, symbol, date):
        try:
            start_date = date
            end_date = start_date + timedelta(days=1)

            stock_data = yf.download(symbol, start=start_date, end=end_date, progress=False)
            if stock_data.empty:
                raise ValueError(f"No stock data found for {symbol} on {date}.")
            return stock_data
        except Exception as e:
            self.logger.error(f"Error fetching stock data for {symbol}: {e}")
            return pd.DataFrame()

    def get_current_price(self, asset_type, asset_name):
        try:
            if asset_type == "Mutual Fund":
                if self._scheme_codes is None:
                    self._scheme_codes = self._fetch_scheme_codes()

                scheme_code = None
                for code, name in self._scheme_codes.items():
                    if name.lower() == asset_name.lower():
                        scheme_code = code
                        break

                if scheme_code:
                    details = self.mf_toolkit.get_scheme_details(scheme_code)
                    return float(details['nav'])
                return None

            elif asset_type == "Stock":
                ticker = yf.Ticker(asset_name)
                end = date.today()
                start = end - timedelta(days=10)
                history = ticker.history(start=start, end=end)
                if history.empty:
                    raise ValueError(f"No data found for stock {asset_name}")
                latest_price = history["Close"].iloc[-1]
                return float(latest_price)

            else:
                raise ValueError("Invalid asset type.")

        except Exception as e:
            self.logger.error(f"Error fetching current price for {asset_type} {asset_name}: {e}")
            return None
