# data_fetcher.py

import mftool as mf 
import yfinance as yf
import pandas as pd
from datetime import date, timedelta
import logging 

class DataFetcher:
    def __init__(self):
        self.mf_toolkit = mf.Mftool()
        self._scheme_codes = None
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

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
            scheme_codes = self.mf_toolkit.get_scheme_codes()
            if not scheme_codes:
                raise ValueError("No scheme codes found.")
            return scheme_codes
        except Exception as e:
            self.logger.error(f"Error fetching scheme codes: {e}")
            return {}

    def get_all_fund_names(self):
        if self._scheme_codes is None:
            self.logger.info("Fetching scheme codes for fund names...")
            self._scheme_codes = self._fetch_scheme_codes()
        return list(self._scheme_codes.values()) if self._scheme_codes else []

    # FIX 1: get_scheme_code centralized
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

    # FIX 2: get_historical_nav for Lumpsum (with fallbacks)
    def get_historical_nav(self, fund_name, purchase_date):
        try:
            scheme_code = self.get_scheme_code(fund_name)
            if not scheme_code:
                self.logger.error(f"Scheme code not found for {fund_name}")
                return None

            fallback_days = [0, 1, 2, 3, 5, 7, 10, 15, 30, 45, 60]

            for days in fallback_days:
                fetch_date = purchase_date - timedelta(days=days)
                fetch_date_str = fetch_date.strftime("%d-%m-%Y")

                nav_list = self.mf_toolkit.get_scheme_historical_nav(
                    scheme_code, fetch_date_str, fetch_date_str
                )

                if nav_list and isinstance(nav_list, list):
                    nav_entry = nav_list[0]
                    nav = nav_entry.get("nav")

                    if nav and float(nav) > 0:
                        self.logger.info(
                            f"Fetched NAV for {fund_name} using date {fetch_date_str}"
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

    # FIX 3a: New method for efficient batch fetching for SIP
    def get_nav_range(self, fund_name, start_date, end_date):
        scheme_code = self.get_scheme_code(fund_name)
        if not scheme_code:
            self.logger.error(f"Scheme code not found for {fund_name}")
            return {}

        try:
            start_str = start_date.strftime("%d-%m-%Y")
            end_str = end_date.strftime("%d-%m-%Y")
            
            self.logger.info(f"Fetching NAV range for {fund_name} from {start_str} to {end_str}")
            
            nav_data = self.mf_toolkit.get_scheme_historical_nav(
                scheme_code, start_str, end_str
            )

            nav_dict = {}
            if nav_data and isinstance(nav_data, list):
                for item in nav_data:
                    try:
                        # mftool returns 'date' in YYYY-MM-DD format, convert to date object
                        nav_date = date.fromisoformat(item["date"]) 
                        nav = float(item["nav"])
                        if nav > 0:
                            nav_dict[nav_date] = nav
                    except (ValueError, KeyError, TypeError) as e:
                        self.logger.warning(f"Skipping invalid NAV entry: {item} due to {e}")

            self.logger.info(f"Fetched {len(nav_dict)} NAV entries for {fund_name}.")
            return nav_dict
        except Exception as e:
            self.logger.error(f"Error fetching NAV range for {fund_name}: {e}")
            return {}

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

    # FIX: Corrected get_current_price (fixed the issue in your screenshot)
    def get_current_price(self, asset_type, asset_name):
        try:
            if asset_type == "Mutual Fund":
                scheme_code = self.get_scheme_code(asset_name) 
                
                if scheme_code:
                    details = self.mf_toolkit.get_scheme_details(scheme_code)
                    nav = (
                        details.get("nav")
                        or details.get("scheme_nav")
                        or details.get("last_nav")
                    )
                    
                    if nav is not None and str(nav).strip() and float(nav) > 0:
                        self.logger.info(f"Successfully fetched current NAV for {asset_name}: {nav}")
                        return float(nav)
                        
                    self.logger.error(
                        f"NAV not found in scheme details for {asset_name} (Code: {scheme_code}). "
                        f"Details keys: {list(details.keys()) if isinstance(details, dict) else 'N/A'}"
                    )
                    return None
                else:
                    self.logger.error(f"Scheme code lookup failed for Mutual Fund: {asset_name}")
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