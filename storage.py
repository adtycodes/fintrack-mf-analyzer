import json
from datetime import date
from pathlib import Path

PORTFOLIO_FILE = Path("portfolio.json")


def serialize_asset(asset: dict) -> dict:
    asset = asset.copy()
    if isinstance(asset.get("Purchase Date"), date):
        asset["Purchase Date"] = asset["Purchase Date"].isoformat()
    return asset


def deserialize_asset(asset: dict) -> dict:
    asset = asset.copy()
    if isinstance(asset.get("Purchase Date"), str):
        asset["Purchase Date"] = date.fromisoformat(asset["Purchase Date"])
    return asset


def save_portfolio(portfolio: list):
    data = [serialize_asset(a) for a in portfolio]
    PORTFOLIO_FILE.write_text(json.dumps(data, indent=2))


def load_portfolio() -> list:
    if not PORTFOLIO_FILE.exists():
        return []
    data = json.loads(PORTFOLIO_FILE.read_text())
    return [deserialize_asset(a) for a in data]
