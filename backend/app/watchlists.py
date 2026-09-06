from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.attention_engine import calculate_attention
from app.auth import get_current_user, get_db
from app.change_detection import calculate_stock_change
from app.models import MarketSnapshot, Stock, User, UserStockState, Watchlist, WatchlistStock
from app.schemas import (
    WatchlistChangeSummary,
    WatchlistChangesResponse,
    WatchlistCreate,
    WatchlistResponse,
    WatchlistStockAdd,
    WatchlistUpdate,
)

router = APIRouter(prefix="/watchlists", tags=["Watchlists"])


def get_owned_watchlist(
    watchlist_id: int,
    user_id: int,
    db: Session,
) -> Watchlist:
    watchlist = (
        db.query(Watchlist)
        .options(joinedload(Watchlist.stocks).joinedload(WatchlistStock.stock))
        .filter(Watchlist.id == watchlist_id, Watchlist.user_id == user_id)
        .first()
    )
    if watchlist is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watchlist not found",
        )
    return watchlist


def serialize_watchlist(watchlist: Watchlist) -> dict:
    return {
        "id": watchlist.id,
        "name": watchlist.name,
        "created_at": watchlist.created_at,
        "stocks": [
            {
                "id": link.stock.id,
                "symbol": link.stock.symbol,
                "company_name": link.stock.company_name,
                "exchange": link.stock.exchange,
            }
            for link in sorted(watchlist.stocks, key=lambda item: item.stock.id)
        ],
    }


def _build_no_baseline_result(stock: Stock, latest_snapshot: MarketSnapshot | None) -> dict:
    return {
        "stock_id": stock.id,
        "symbol": stock.symbol,
        "current_price": float(latest_snapshot.close) if latest_snapshot else 0.0,
        "price_change": None,
        "price_change_percent": None,
        "direction": None,
        "attention_score": 0,
        "attention_level": "NO_NOTABLE_CHANGE",
        "volume_change_percent": None,
        "important_level_crossed": False,
        "sustained_movement": False,
        "reason": "Check this stock first to establish a baseline.",
        "status": "NO_BASELINE",
    }


def _build_no_market_data_result(stock: Stock) -> dict:
    return {
        "stock_id": stock.id,
        "symbol": stock.symbol,
        "current_price": 0.0,
        "price_change": None,
        "price_change_percent": None,
        "direction": None,
        "attention_score": 0,
        "attention_level": "NO_NOTABLE_CHANGE",
        "volume_change_percent": None,
        "important_level_crossed": False,
        "sustained_movement": False,
        "reason": "No market data is available for this stock.",
        "status": "NO_MARKET_DATA",
    }


def _build_no_new_data_result(stock: Stock, latest_snapshot: MarketSnapshot) -> dict:
    return {
        "stock_id": stock.id,
        "symbol": stock.symbol,
        "current_price": float(latest_snapshot.close),
        "price_change": None,
        "price_change_percent": None,
        "direction": None,
        "attention_score": 0,
        "attention_level": "NO_NOTABLE_CHANGE",
        "volume_change_percent": None,
        "important_level_crossed": False,
        "sustained_movement": False,
        "reason": "No new market data since your last check.",
        "status": "NO_NEW_DATA",
    }


def _normalize_timestamp(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


@router.post("", response_model=WatchlistResponse, status_code=status.HTTP_201_CREATED)
def create_watchlist(
    payload: WatchlistCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    watchlist = Watchlist(user_id=current_user.id, name=payload.name)
    db.add(watchlist)
    db.commit()
    db.refresh(watchlist)
    return serialize_watchlist(watchlist)


@router.get("", response_model=list[WatchlistResponse])
def list_watchlists(
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
    return [serialize_watchlist(watchlist) for watchlist in watchlists]


@router.get("/{watchlist_id}", response_model=WatchlistResponse)
def get_watchlist(
    watchlist_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return serialize_watchlist(get_owned_watchlist(watchlist_id, current_user.id, db))


@router.patch("/{watchlist_id}", response_model=WatchlistResponse)
def rename_watchlist(
    watchlist_id: int,
    payload: WatchlistUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    watchlist = get_owned_watchlist(watchlist_id, current_user.id, db)
    watchlist.name = payload.name
    db.commit()
    db.refresh(watchlist)
    return serialize_watchlist(get_owned_watchlist(watchlist_id, current_user.id, db))


@router.delete("/{watchlist_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_watchlist(
    watchlist_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    watchlist = get_owned_watchlist(watchlist_id, current_user.id, db)
    db.delete(watchlist)
    db.commit()


@router.post("/{watchlist_id}/stocks", response_model=WatchlistResponse)
def add_stock_to_watchlist(
    watchlist_id: int,
    payload: WatchlistStockAdd,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    watchlist = get_owned_watchlist(watchlist_id, current_user.id, db)
    stock = (
        db.query(Stock)
        .filter(Stock.id == payload.stock_id, Stock.is_active.is_(True))
        .first()
    )
    if stock is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active stock not found",
        )

    existing_link = (
        db.query(WatchlistStock)
        .filter(
            WatchlistStock.watchlist_id == watchlist_id,
            WatchlistStock.stock_id == payload.stock_id,
        )
        .first()
    )
    if existing_link:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stock already exists in watchlist",
        )

    db.add(WatchlistStock(watchlist_id=watchlist_id, stock_id=stock.id))
    db.commit()
    return serialize_watchlist(get_owned_watchlist(watchlist_id, current_user.id, db))


@router.delete("/{watchlist_id}/stocks/{stock_id}", response_model=WatchlistResponse)
def remove_stock_from_watchlist(
    watchlist_id: int,
    stock_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    watchlist = get_owned_watchlist(watchlist_id, current_user.id, db)
    link = (
        db.query(WatchlistStock)
        .filter(
            WatchlistStock.watchlist_id == watchlist.id,
            WatchlistStock.stock_id == stock_id,
        )
        .first()
    )
    if link is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stock is not in watchlist",
        )

    db.delete(link)
    db.commit()
    return serialize_watchlist(get_owned_watchlist(watchlist_id, current_user.id, db))


@router.get("/{watchlist_id}/changes", response_model=WatchlistChangesResponse)
def get_watchlist_changes(
    watchlist_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    watchlist = get_owned_watchlist(watchlist_id, current_user.id, db)
    links = (
        db.query(WatchlistStock)
        .options(joinedload(WatchlistStock.stock))
        .filter(WatchlistStock.watchlist_id == watchlist.id)
        .order_by(WatchlistStock.id)
        .all()
    )
    stock_results: list[dict] = []

    for link in links:
        stock = link.stock
        state = (
            db.query(UserStockState)
            .filter(
                UserStockState.user_id == current_user.id,
                UserStockState.stock_id == stock.id,
            )
            .first()
        )
        if state is None:
            latest_snapshot = (
                db.query(MarketSnapshot)
                .filter(MarketSnapshot.stock_id == stock.id)
                .order_by(MarketSnapshot.timestamp.desc())
                .first()
            )
            stock_results.append(_build_no_baseline_result(stock, latest_snapshot))
            continue

        snapshots = (
            db.query(MarketSnapshot)
            .filter(MarketSnapshot.stock_id == stock.id)
            .order_by(MarketSnapshot.timestamp.desc())
            .all()
        )
        if not snapshots:
            stock_results.append(_build_no_market_data_result(stock))
            continue

        latest_snapshot = snapshots[0]
        if _normalize_timestamp(latest_snapshot.timestamp) <= _normalize_timestamp(
            state.reference_timestamp
        ):
            stock_results.append(_build_no_new_data_result(stock, latest_snapshot))
            continue

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

        stock_results.append(
            {
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
            }
        )

    stock_results.sort(key=lambda item: (-int(item["attention_score"]), item["symbol"]))
    summary = WatchlistChangeSummary(
        total_stocks=len(stock_results),
        high_attention=sum(1 for item in stock_results if item["attention_level"] == "HIGH"),
        notable=sum(1 for item in stock_results if item["attention_level"] == "NOTABLE"),
        mild=sum(1 for item in stock_results if item["attention_level"] == "MILD"),
        no_notable_change=sum(1 for item in stock_results if item["attention_level"] == "NO_NOTABLE_CHANGE"),
    )
    return {
        "watchlist_id": watchlist.id,
        "watchlist_name": watchlist.name,
        "summary": summary,
        "stocks": stock_results,
    }
