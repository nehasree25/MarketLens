from __future__ import annotations

from decimal import Decimal
from typing import Literal

ChangeDirection = Literal["UP", "DOWN", "UNCHANGED"]


def calculate_stock_change(
    reference_price: Decimal | float,
    reference_timestamp: object,
    current_price: Decimal | float,
    current_timestamp: object,
    reference_volume: int | None = None,
    current_volume: int | None = None,
) -> dict[str, object]:
    """Calculate the deterministic change between two stored observations."""
    if current_timestamp <= reference_timestamp:
        return {
            "status": "NO_NEW_DATA",
            "message": "No new market data since your last check.",
            "reference_price": reference_price,
            "reference_timestamp": reference_timestamp,
            "current_price": current_price,
            "current_timestamp": current_timestamp,
            "reference_volume": reference_volume,
            "current_volume": current_volume,
            "price_change": None,
            "price_change_percent": None,
            "direction": None,
        }

    price_change = current_price - reference_price
    if price_change > 0:
        direction: ChangeDirection = "UP"
    elif price_change < 0:
        direction = "DOWN"
    else:
        direction = "UNCHANGED"

    price_change_percent = None
    if reference_price != 0:
        price_change_percent = round((price_change / reference_price) * 100, 2)

    return {
        "status": "CHANGED",
        "message": "Market data changed since your last check.",
        "reference_price": reference_price,
        "reference_timestamp": reference_timestamp,
        "current_price": current_price,
        "current_timestamp": current_timestamp,
        "reference_volume": reference_volume,
        "current_volume": current_volume,
        "price_change": price_change,
        "price_change_percent": price_change_percent,
        "direction": direction,
    }