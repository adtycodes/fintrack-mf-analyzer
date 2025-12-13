from datetime import date
import numpy_financial as npf


class PortfolioAnalyzer:
    def __init__(self, fetcher):
        self.fetcher = fetcher

    # --------------------------------------------------
    # Public API
    # --------------------------------------------------
    def analyze_portfolio(self, portfolio):
        analyzed_assets = []

        for asset in portfolio:
            analyzed_assets.append(self._analyze_single_asset(asset.copy()))

        summary = self._aggregate(analyzed_assets)

        return {
            "details": analyzed_assets,
            "summary": summary
        }

    # --------------------------------------------------
    # Core Logic
    # --------------------------------------------------
    def _analyze_single_asset(self, asset):
        asset_type = asset["Type"]
        name = asset["Name"]
        inv_type = asset.get("Investment Type", "Lumpsum")
        amount = asset["Amount Invested"]
        purchase_date = asset["Purchase Date"]

        units = asset.get("Units Owned")
        purchase_nav = asset.get("Purchase NAV")

        # ------------------------------
        # 1. Determine Units (TRUTH)
        # ------------------------------
        if units and units > 0:
            units_owned = units

        else:
            # Try to compute units if NAV exists
            if purchase_nav and purchase_nav > 0:
                units_owned = amount / purchase_nav
                asset["Units Owned"] = units_owned

            else:
                asset["error"] = "Missing units or purchase NAV"
                return asset

        # ------------------------------
        # 2. Fetch Current Price (NAV)
        # ------------------------------
        current_price = self.fetcher.get_current_price(asset_type, name)

        if current_price is None or current_price <= 0:
            asset["error"] = "Current price unavailable"
            return asset

        # ------------------------------
        # 3. Valuation
        # ------------------------------
        current_value = units_owned * current_price
        gain_loss = current_value - amount

        asset.update({
            "Total Invested": amount,
            "Units/Shares": units_owned,
            "Current Price": current_price,
            "Current Value": current_value,
            "Gain/Loss": gain_loss,
            "Percentage Return": (gain_loss / amount) * 100 if amount > 0 else 0
        })

        # ------------------------------
        # 4. Returns
        # ------------------------------
        if inv_type == "Lumpsum":
            years = (date.today() - purchase_date).days / 365.25
            if years > 0 and amount > 0:
                cagr = ((current_value / amount) ** (1 / years)) - 1
                asset["CAGR"] = round(cagr * 100, 2)
            else:
                asset["CAGR"] = "N/A"

        else:
            # SIP returns not faked
            asset["XIRR"] = "Requires transaction-level data"

        return asset

    # --------------------------------------------------
    # Portfolio Aggregation
    # --------------------------------------------------
    def _aggregate(self, assets):
        valid_assets = [a for a in assets if "error" not in a]

        total_invested = sum(a.get("Total Invested", 0) for a in valid_assets)
        total_current_value = sum(a.get("Current Value", 0) for a in valid_assets)
        total_gain = total_current_value - total_invested

        return {
            "Total Invested": total_invested,
            "Total Current Value": total_current_value,
            "Total Gain/Loss": total_gain,
            "Percentage Return": (
                (total_gain / total_invested) * 100
                if total_invested > 0 else 0
            ),
            "Portfolio XIRR": self._portfolio_xirr(valid_assets)
        }

    # --------------------------------------------------
    # Portfolio XIRR (Lumpsum only – honest)
    # --------------------------------------------------
    def _portfolio_xirr(self, assets):
        cash_flows = []
        dates = []

        for asset in assets:
            if asset.get("Investment Type") != "Lumpsum":
                continue

            cash_flows.append(-asset["Total Invested"])
            dates.append(asset["Purchase Date"])

        total_value = sum(a["Current Value"] for a in assets if "Current Value" in a)

        if total_value <= 0 or not cash_flows:
            return "N/A"

        cash_flows.append(total_value)
        dates.append(date.today())

        try:
            xirr = npf.xirr(cash_flows, dates)
            return round(xirr * 100, 2)
        except Exception:
            return "N/A"
