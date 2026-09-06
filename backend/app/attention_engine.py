from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal
from typing import Any


def calculate_price_movement_score(price_change_percent: Decimal | float | None) -> int:
    if price_change_percent is None:
        return 0
    magnitude = abs(float(price_change_percent))
    if magnitude >= 5:
        return 40
    if magnitude >= 3:
        return 30
    if magnitude >= 2:
        return 20
    if magnitude >= 1:
        return 10
    return 0


def calculate_volume_change(
    current_volume: int | None,
    previous_volume: int | None,
) -> float | None:
    if previous_volume in (None, 0) or current_volume is None:
        return None
    return abs((current_volume - previous_volume) / previous_volume * 100)


def calculate_volume_change_score(volume_change_percent: float | None) -> int:
    if volume_change_percent is None:
        return 0
    if volume_change_percent >= 100:
        return 25
    if volume_change_percent >= 50:
        return 18
    if volume_change_percent >= 20:
        return 10
    return 0


def detect_important_level_crossing(
    reference_price: Decimal | float,
    current_price: Decimal | float,
    previous_day_high: Decimal | float | None,
    previous_day_low: Decimal | float | None,
) -> bool:
    crossed_high = (
        previous_day_high is not None
        and reference_price <= previous_day_high
        and current_price > previous_day_high
    )
    crossed_low = (
        previous_day_low is not None
        and reference_price >= previous_day_low
        and current_price < previous_day_low
    )
    return crossed_high or crossed_low


def detect_sustained_movement(snapshots: Sequence[Any]) -> bool:
    if len(snapshots) < 4:
        return False
    closes = [snapshot.close for snapshot in snapshots[-4:]]
    movements = [right - left for left, right in zip(closes, closes[1:])]
    return all(movement > 0 for movement in movements) or all(
        movement < 0 for movement in movements
    )


def get_attention_level(attention_score: int) -> str:
    if attention_score >= 75:
        return "HIGH"
    if attention_score >= 50:
        return "NOTABLE"
    if attention_score >= 25:
        return "MILD"
    return "NO_NOTABLE_CHANGE"


def build_attention_reason(
    price_movement_score: int,
    volume_change_score: int,
    important_level_crossed: bool,
    sustained_movement: bool,
) -> str:
    factors = []
    if price_movement_score:
        factors.append("significant price movement")
    if volume_change_score:
        factors.append("increased volume")
    if important_level_crossed:
        factors.append("an important level crossed")
    if sustained_movement:
        factors.append("sustained movement")
    if not factors:
        return "No notable change detected."
    if len(factors) == 1:
        return factors[0].capitalize() + "."
    return ", ".join(factors[:-1]) + ", and " + factors[-1] + "."


def calculate_attention(
    reference_price: Decimal | float,
    current_price: Decimal | float,
    price_change_percent: Decimal | float | None,
    current_volume: int | None,
    previous_volume: int | None,
    previous_day_high: Decimal | float | None,
    previous_day_low: Decimal | float | None,
    recent_snapshots: Sequence[Any],
) -> dict[str, object]:
    volume_change_percent = calculate_volume_change(current_volume, previous_volume)
    price_score = calculate_price_movement_score(price_change_percent)
    volume_score = calculate_volume_change_score(volume_change_percent)
    level_crossed = detect_important_level_crossing(
        reference_price, current_price, previous_day_high, previous_day_low
    )
    sustained = detect_sustained_movement(recent_snapshots)
    level_score = 20 if level_crossed else 0
    sustained_score = 15 if sustained else 0
    attention_score = max(0, min(100, price_score + volume_score + level_score + sustained_score))
    return {
        "attention_score": attention_score,
        "attention_level": get_attention_level(attention_score),
        "factors": {
            "price_movement": price_score,
            "volume_change": volume_score,
            "important_level": level_score,
            "sustained_movement": sustained_score,
        },
        "volume_change_percent": (
            round(volume_change_percent, 2) if volume_change_percent is not None else None
        ),
        "important_level_crossed": level_crossed,
        "sustained_movement": sustained,
        "reason": build_attention_reason(
            price_score, volume_score, level_crossed, sustained
        ),
    }