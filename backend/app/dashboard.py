from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from app.attention_engine import calculate_attention
from app.auth import get_current_user, get_db
from app.change_detection import calculate_stock_change
from app.models import MarketSnapshot, Stock, User, UserStockState, Watchlist, WatchlistStock
from app.schemas import DashboardSummaryResponse

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def _normalize_timestamp(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _base_result(stock: Stock, current_price: float, reason: str, status: str) -> dict:
    return {
        "stock_id": stock.id,
        "symbol": stock.symbol,
        "current_price": current_price,
        "price_change": None,
        "price_change_percent": None,
        "direction": None,
        "attention_score": 0,
        "attention_level": "NO_NOTABLE_CHANGE",
        "volume_change_percent": None,
        "important_level_crossed": False,
        "sustained_movement": False,
        "reason": reason,
        "status": status,
        "watchlists": [],
    }


def _build_no_baseline_result(stock: Stock, latest_snapshot: MarketSnapshot | None) -> dict:
    return _base_result(
        stock=stock,
        current_price=float(latest_snapshot.close) if latest_snapshot else 0.0,
        reason="Check this stock first to establish a baseline.",
        status="NO_BASELINE",
    )


def _build_no_market_data_result(stock: Stock) -> dict:
    return _base_result(
        stock=stock,
        current_price=0.0,
        reason="No market data is available for this stock.",
        status="NO_MARKET_DATA",
    )


def _build_no_new_data_result(stock: Stock, latest_snapshot: MarketSnapshot) -> dict:
    return _base_result(
        stock=stock,
        current_price=float(latest_snapshot.close),
        reason="No new market data since your last check.",
        status="NO_NEW_DATA",
    )


def _calculate_dashboard_result(
    stock: Stock,
    current_user_id: int,
    db: Session,
    watchlist_entries: list[dict[str, int | str]],
) -> dict:
    state = (
        db.query(UserStockState)
        .filter(
            UserStockState.user_id == current_user_id,
            UserStockState.stock_id == stock.id,
        )
        .first()
    )

    snapshots = (
        db.query(MarketSnapshot)
        .filter(MarketSnapshot.stock_id == stock.id)
        .order_by(MarketSnapshot.timestamp.desc())
        .all()
    )
    if not snapshots:
        result = _build_no_market_data_result(stock)
        result["watchlists"] = watchlist_entries
        return result

    latest_snapshot = snapshots[0]
    if state is None:
        result = _build_no_baseline_result(stock, latest_snapshot)
        result["watchlists"] = watchlist_entries
        return result

    if _normalize_timestamp(latest_snapshot.timestamp) <= _normalize_timestamp(
        state.reference_timestamp
    ):
        result = _build_no_new_data_result(stock, latest_snapshot)
        result["watchlists"] = watchlist_entries
        return result

    previous_snapshot = snapshots[1] if len(snapshots) > 1 else None
    current_date = latest_snapshot.timestamp.date()
    prior_days: dict[object, list[MarketSnapshot]] = {}
    for snapshot in snapshots:
        snapshot_date = snapshot.timestamp.date()
        if snapshot_date < current_date:
            prior_days.setdefault(snapshot_date, []).append(snapshot)

    previous_day_high = previous_day_low = None
    if prior_days:
        previous_day = max(prior_days)
        previous_day_snapshots = prior_days[previous_day]
        previous_day_high = max(snapshot.high for snapshot in previous_day_snapshots)
        previous_day_low = min(snapshot.low for snapshot in previous_day_snapshots)

    price_change = latest_snapshot.close - state.reference_price
    price_change_percent = None if state.reference_price == 0 else (
        price_change / state.reference_price * 100
    )
    direction = "UP" if price_change > 0 else "DOWN" if price_change < 0 else "UNCHANGED"

    reference_snapshot = (
        db.query(MarketSnapshot)
        .filter(
            MarketSnapshot.stock_id == stock.id,
            MarketSnapshot.timestamp == state.reference_timestamp,
        )
        .first()
    )
    change = calculate_stock_change(
        reference_price=state.reference_price,
        reference_timestamp=state.reference_timestamp,
        current_price=latest_snapshot.close,
        current_timestamp=latest_snapshot.timestamp,
        reference_volume=reference_snapshot.volume if reference_snapshot else None,
        current_volume=latest_snapshot.volume,
    )
    attention = calculate_attention(
        reference_price=state.reference_price,
        current_price=latest_snapshot.close,
        price_change_percent=price_change_percent,
        current_volume=latest_snapshot.volume,
        previous_volume=previous_snapshot.volume if previous_snapshot else None,
        previous_day_high=previous_day_high,
        previous_day_low=previous_day_low,
        recent_snapshots=list(reversed(snapshots[:4])),
    )

    result = {
        "stock_id": stock.id,
        "symbol": stock.symbol,
        "current_price": float(latest_snapshot.close),
        "price_change": float(change["price_change"]) if change["price_change"] is not None else None,
        "price_change_percent": float(change["price_change_percent"]) if change["price_change_percent"] is not None else None,
        "direction": change["direction"],
        "attention_score": int(attention["attention_score"]),
        "attention_level": attention["attention_level"],
        "volume_change_percent": attention["volume_change_percent"],
        "important_level_crossed": bool(attention["important_level_crossed"]),
        "sustained_movement": bool(attention["sustained_movement"]),
        "reason": attention["reason"],
        "status": change["status"],
        "watchlists": watchlist_entries,
    }
    return result


@router.get("/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    watchlists = (
        db.query(Watchlist)
        .options(joinedload(Watchlist.stocks).joinedload(WatchlistStock.stock))
        .filter(Watchlist.user_id == current_user.id)
        .order_by(Watchlist.id)
        .all()
    )

    unique_stocks: dict[int, dict[str, object]] = {}
    for watchlist in watchlists:
        for link in watchlist.stocks:
            stock = link.stock
            if stock is None or not stock.is_active:
                continue
            existing = unique_stocks.setdefault(
                stock.id,
                {
                    "stock": stock,
                    "watchlists": [],
                },
            )
            existing["watchlists"].append({
                "watchlist_id": watchlist.id,
                "watchlist_name": watchlist.name,
            })

    stock_results = []
    for stock_data in unique_stocks.values():
        stock = stock_data["stock"]
        watchlist_entries = stock_data["watchlists"]
        result = _calculate_dashboard_result(stock, current_user.id, db, watchlist_entries)
        stock_results.append(result)

    stock_results.sort(key=lambda item: (-int(item["attention_score"]), item["symbol"]))

    summary = {
        "total_stocks": len(stock_results),
        "high_attention": sum(1 for item in stock_results if item["attention_level"] == "HIGH"),
        "notable": sum(1 for item in stock_results if item["attention_level"] == "NOTABLE"),
        "mild": sum(1 for item in stock_results if item["attention_level"] == "MILD"),
        "no_notable_change": sum(
            1 for item in stock_results if item["attention_level"] == "NO_NOTABLE_CHANGE"
        ),
        "stocks": stock_results,
    }
    return summary
