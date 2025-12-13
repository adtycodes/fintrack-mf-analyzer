from datetime import date
import numpy_financial as npf


class PortfolioAnalyzer:
    def __init__(self, fetcher):
        self.fetcher = fetcher

    # ==================================================
    # Public API
    # ==================================================
    def analyze_portfolio(self, portfolio):
        analyzed_assets = []

        for asset in portfolio:
            analyzed_assets.append(self._analyze_single_asset(asset.copy()))

        summary = self._aggregate(analyzed_assets)

        return {
            "details": analyzed_assets,
            "summary": summary
        }

    # ==================================================
    # Core Analyzer
    # ==================================================
    def _analyze_single_asset(self, asset):
        asset_type = asset["Type"]
        name = asset["Name"]
        inv_type = asset.get("Investment Type", "Lumpsum")

        # ---------------- SIP (transaction-based) ----------------
        if inv_type == "SIP":
            transactions = asset.get("transactions", [])

            if not transactions:
                asset.update({
                    "error": "No SIP transactions added",
                    "Data Quality": "Incomplete",
                    "Confidence Note": "SIP requires transaction-level data"
                })
                return asset

            total_invested = sum(t["amount"] for t in transactions)
            total_units = sum(t["units"] for t in transactions)

            current_price = self.fetcher.get_current_price(asset_type, name)
            if not current_price:
                asset.update({
                    "error": "Current price unavailable",
                    "Data Quality": "Estimated",
                    "Confidence Note": "Units known, market price unavailable"
                })
                return asset

            current_value = total_units * current_price
            gain_loss = current_value - total_invested

            asset.update({
                "Total Invested": total_invested,
                "Units/Shares": total_units,
                "Current Price": current_price,
                "Current Value": current_value,
                "Gain/Loss": gain_loss,
                "Percentage Return": (gain_loss / total_invested) * 100,
                "Data Quality": "Verified",
                "Confidence Note": "Computed from transaction-level units"
            })

            # XIRR
            cash_flows = [-t["amount"] for t in transactions]
            dates = [t["date"] for t in transactions]
            cash_flows.append(current_value)
            dates.append(date.today())

            try:
                asset["XIRR"] = round(npf.xirr(cash_flows, dates) * 100, 2)
            except Exception:
                asset["XIRR"] = "N/A"

            return asset

        # ---------------- LUMPSUM ----------------
        amount = asset["Amount Invested"]
        purchase_date = asset["Purchase Date"]
        units = asset.get("Units Owned")
        purchase_nav = asset.get("Purchase NAV")

        # Determine units
        if units and units > 0:
            units_owned = units
            quality = "Verified"
            note = "Units provided by user"

        elif purchase_nav and purchase_nav > 0:
            units_owned = amount / purchase_nav
            quality = "Estimated"
            note = "Units derived from purchase NAV"

        else:
            asset.update({
                "error": "Missing units or purchase NAV",
                "Data Quality": "Incomplete",
                "Confidence Note": "Cannot value without units or NAV"
            })
            return asset

        current_price = self.fetcher.get_current_price(asset_type, name)
        if not current_price:
            asset.update({
                "error": "Current price unavailable",
                "Data Quality": quality,
                "Confidence Note": "Units known but market price unavailable"
            })
            return asset

        current_value = units_owned * current_price
        gain_loss = current_value - amount

        years = (date.today() - purchase_date).days / 365.25
        if years > 0:
            cagr = ((current_value / amount) ** (1 / years)) - 1
            cagr = round(cagr * 100, 2)
        else:
            cagr = "N/A"

        asset.update({
            "Total Invested": amount,
            "Units/Shares": units_owned,
            "Current Price": current_price,
            "Current Value": current_value,
            "Gain/Loss": gain_loss,
            "Percentage Return": (gain_loss / amount) * 100,
            "CAGR": cagr,
            "Data Quality": quality,
            "Confidence Note": note
        })

        return asset

    # ==================================================
    # Portfolio Aggregation
    # ==================================================
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
                (total_gain / total_invested) * 100 if total_invested > 0 else 0
            ),
            "Portfolio XIRR": self._portfolio_xirr(valid_assets)
        }

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
            return round(npf.xirr(cash_flows, dates) * 100, 2)
        except Exception:
            return "N/A"
