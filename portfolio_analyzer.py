# portfolio_analyzer.py
from datetime import date
import calendar
import numpy_financial as npf
from data_fetcher import DataFetcher

class PortfolioAnalyzer:
    def __init__(self, fetcher: DataFetcher):
        self.fetcher = fetcher

    @staticmethod
    def last_day_of_month(year, month):
        return calendar.monthrange(year, month)[1]

    def analyze_portfolio(self, portfolio):
        detailed_results = []
        for asset in portfolio:
            analyzed_asset = self._analyze_single_asset(asset.copy())
            detailed_results.append(analyzed_asset)
        
        summary_results = self.aggregate_portfolio_results(detailed_results)
        
        return {
            "details": detailed_results,
            "summary": summary_results
        }

    def _analyze_single_asset(self, asset):
        purchase_date = asset["Purchase Date"]
        purchase_price = None
        current_price = None
        
        if asset["Type"] == "Mutual Fund":
            purchase_price = self.fetcher.get_historical_nav(asset["Name"], purchase_date)
            current_price = self.fetcher.get_current_price("Mutual Fund", asset["Name"])
        
        elif asset["Type"] == "Stock":
            purchase_price_df = self.fetcher.get_stock_data(asset["Name"], purchase_date)
            if not purchase_price_df.empty:
                purchase_price = purchase_price_df['Close'].iloc[0]
            current_price = self.fetcher.get_current_price("Stock", asset["Name"])
        
        if purchase_price is None or current_price is None:
            asset["error"] = "Could not fetch price/NAV data."
            return asset
        
        is_sip = asset["Type"] == "Mutual Fund" and asset.get("Investment Type") == "SIP"
        
        if is_sip:
            number_of_months = (date.today().year - purchase_date.year) * 12 + (date.today().month - purchase_date.month) + 1
            monthly_investment = asset["Amount Invested"]
            total_invested = monthly_investment * number_of_months
            
            units_or_shares = 0
            cash_flows = []
            dates = []
            all_installments_valid = True

            for i in range(number_of_months):
                current_month = purchase_date.month + i
                current_year = purchase_date.year + (current_month - 1) // 12
                installment_month = (current_month - 1) % 12 + 1
                day = min(purchase_date.day, self.last_day_of_month(current_year, installment_month))
                installment_date = date(current_year, installment_month, day)
                
                monthly_nav = self.fetcher.get_historical_nav(asset["Name"], installment_date)
                if monthly_nav:
                    units_or_shares += monthly_investment / monthly_nav
                    cash_flows.append(-monthly_investment)
                    dates.append(installment_date)
                else:
                    all_installments_valid = False
                    break
            
            purchase_price = total_invested / units_or_shares if units_or_shares > 0 else 0
        
        else:
            total_invested = asset["Amount Invested"]
            units_or_shares = total_invested / purchase_price
        
        current_value = units_or_shares * current_price
        gain_loss = current_value - total_invested

        asset["Total Invested"] = total_invested
        asset["Purchase Price"] = purchase_price
        asset["Current Price"] = current_price
        asset["Units/Shares"] = units_or_shares
        asset["Current Value"] = current_value
        asset["Gain/Loss"] = gain_loss
        asset["Percentage Return"] = (gain_loss / total_invested) * 100 if total_invested > 0 else 0
        
        if is_sip:
            if all_installments_valid and current_value > 0:
                cash_flows.append(current_value)
                dates.append(date.today())
                try:
                    xirr_value = npf.xirr(cash_flows, dates)
                    asset["XIRR"] = round(xirr_value * 100, 2)
                except Exception:
                    asset["XIRR"] = "N/A"
            else:
                asset["XIRR"] = "N/A"
        else: # Lumpsum
            years_held = (date.today() - purchase_date).days / 365.25
            if years_held > 0 and total_invested > 0:
                cagr_value = ((current_value / total_invested) ** (1 / years_held)) - 1
                asset["CAGR"] = round(cagr_value * 100, 2)
            else:
                asset["CAGR"] = "N/A"
        
        return asset
    
    def aggregate_portfolio_results(self, detailed_results):
        valid_assets = [asset for asset in detailed_results if "error" not in asset]
        
        total_invested = sum(asset.get("Total Invested", 0) for asset in valid_assets)
        total_current_value = sum(asset.get("Current Value", 0) for asset in valid_assets)
        total_gain_loss = total_current_value - total_invested
        percentage_return = (total_gain_loss / total_invested) * 100 if total_invested > 0 else 0

        portfolio_xirr = self.calculate_portfolio_xirr(detailed_results)
        
        return {
            "Total Invested": total_invested,
            "Total Current Value": total_current_value,
            "Total Gain/Loss": total_gain_loss,
            "Percentage Return": percentage_return
        }
    
    def calculate_portfolio_xirr(self, detailed_results):

        cash_flows = []
        dates = []

        for asset in detailed_results:
            if "error" in asset:
                continue 

            if asset.get("Investment Type") != "SIP":
                cash_flows.append(-asset["Total Invested"])
                dates.append(asset["Purchase Date"])
        
            else:
                purchase_date = asset["Purchase Date"]
                number_of_months = (date.today().year - purchase_date.year) * 12 + (date.today().month - purchase_date.month) + 1
                monthly_investment = asset["Amount Invested"]
            
                for i in range(number_of_months):
                    current_month = purchase_date.month + i
                    current_year = purchase_date.year + (current_month - 1) // 12
                    installment_month = (current_month - 1) % 12 + 1
                    day = min(purchase_date.day, self.last_day_of_month(current_year, installment_month))
                    installment_date = date(current_year, installment_month, day)
                
                    cash_flows.append(-monthly_investment)
                    dates.append(installment_date)

        total_current_value = sum(asset.get("Current Value", 0) for asset in detailed_results if "error" not in asset)

        if total_current_value > 0:
            cash_flows.append(total_current_value)
            dates.append(date.today())

        try:
            sorted_flows = sorted(zip(dates, cash_flows))
            sorted_dates, sorted_cash_flows = zip(*sorted_flows)
            xirr_value = npf.xirr(sorted_cash_flows, sorted_dates)
            return round(xirr_value * 100, 2) if xirr_value is not None else "N/A"
        
        except Exception:
            return "N/A"