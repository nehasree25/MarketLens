from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import get_current_admin, get_current_user, get_db
from app.attention_engine import calculate_attention
from app.change_detection import calculate_stock_change
from app.models import MarketSnapshot, Stock, User, UserStockState
from app.schemas import (
    StockCreate,
    StockResponse,
    StockStatusResponse,
    StockStatusUpdate,
    StockChangeResponse,
    StockAttentionResponse,
    UserStockCheckResponse,
    UserStockStateResponse,
    PaginatedStockResponse,
    PaginatedUserStockStateResponse,
    PaginationMeta,
)

router = APIRouter(prefix="/stocks", tags=["Stocks"])

INITIAL_STOCKS = (
    ("RELIANCE.NS", "Reliance Industries", "NSE"),
    ("TCS.NS", "Tata Consultancy Services", "NSE"),
    ("INFY.NS", "Infosys", "NSE"),
    ("HDFCBANK.NS", "HDFC Bank", "NSE"),
    ("ICICIBANK.NS", "ICICI Bank", "NSE"),
    ("SBIN.NS", "State Bank of India", "NSE"),
    ("ITC.NS", "ITC", "NSE"),
    ("BHARTIARTL.NS", "Bharti Airtel", "NSE"),
    ("LT.NS", "Larsen & Toubro", "NSE"),
    ("AXISBANK.NS", "Axis Bank", "NSE"),
)


def seed_initial_stocks(db: Session) -> None:
    existing_symbols = {
        symbol for (symbol,) in db.query(Stock.symbol).filter(
            Stock.symbol.in_([symbol for symbol, _, _ in INITIAL_STOCKS])
        ).all()
    }

    for symbol, company_name, exchange in INITIAL_STOCKS:
        if symbol not in existing_symbols:
            db.add(
                Stock(
                    symbol=symbol,
                    company_name=company_name,
                    exchange=exchange,
                    is_active=True,
                )
            )

    try:
        db.commit()
    except IntegrityError:
        db.rollback()


@router.get("", response_model=PaginatedStockResponse)
def list_stocks(
    skip: int = Query(0, ge=0),
    limit: int = Query(5, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = db.query(Stock).filter(Stock.is_active.is_(True))
    total = query.count()
    
    stocks = (
        query
        .order_by(Stock.id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    pagination = PaginationMeta(
        total=total,
        skip=skip,
        limit=limit,
        has_more=(skip + limit) < total
    )
    
    return {
        "data": stocks,
        "pagination": pagination
    }


@router.get("/search", response_model=PaginatedStockResponse)
def search_stocks(
    q: str = Query(..., min_length=1),
    skip: int = Query(0, ge=0),
    limit: int = Query(5, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query_str = q.strip()
    if not query_str:
        return {
            "data": [],
            "pagination": PaginationMeta(total=0, skip=skip, limit=limit, has_more=False)
        }

    search_term = f"%{query_str}%"
    query = (
        db.query(Stock)
        .filter(
            Stock.is_active.is_(True),
            (Stock.symbol.ilike(search_term) | Stock.company_name.ilike(search_term)),
        )
    )
    total = query.count()
    
    stocks = (
        query
        .order_by(Stock.id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    pagination = PaginationMeta(
        total=total,
        skip=skip,
        limit=limit,
        has_more=(skip + limit) < total
    )
    
    return {
        "data": stocks,
        "pagination": pagination
    }


def _state_response(stock: Stock, state: UserStockState) -> dict[str, object]:
    return {
        "stock_id": stock.id,
        "symbol": stock.symbol,
        "reference_price": state.reference_price,
        "reference_timestamp": state.reference_timestamp,
        "last_checked_at": state.last_checked_at,
    }


def _timestamp_for_comparison(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=timezone.utc)
    return value


@router.post("/{stock_id}/check", response_model=UserStockCheckResponse)
def check_stock(
    stock_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stock = (
        db.query(Stock)
        .filter(Stock.id == stock_id, Stock.is_active.is_(True))
        .first()
    )
    if stock is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stock not found",
        )

    latest_snapshot = (
        db.query(MarketSnapshot)
        .filter(MarketSnapshot.stock_id == stock_id)
        .order_by(MarketSnapshot.timestamp.desc())
        .first()
    )
    if latest_snapshot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No market snapshot found for this stock",
        )

    state = (
        db.query(UserStockState)
        .filter(
            UserStockState.user_id == current_user.id,
            UserStockState.stock_id == stock_id,
        )
        .first()
    )
    message = "Baseline established" if state is None else "Baseline updated"
    if state is None:
        state = UserStockState(
            user_id=current_user.id,
            stock_id=stock_id,
        )
        db.add(state)

    state.reference_price = latest_snapshot.close
    state.reference_timestamp = latest_snapshot.timestamp
    state.last_checked_at = datetime.now(timezone.utc)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Stock check could not be saved; please try again",
        ) from exc
    db.refresh(state)

    response = _state_response(stock, state)
    response["message"] = message
    return response


@router.get("/{stock_id}/state", response_model=UserStockStateResponse)
def get_stock_state(
    stock_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stock = db.query(Stock).filter(Stock.id == stock_id).first()
    if stock is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stock not found",
        )

    state = (
        db.query(UserStockState)
        .filter(
            UserStockState.user_id == current_user.id,
            UserStockState.stock_id == stock_id,
        )
        .first()
    )
    if state is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No check history found for this stock",
        )
    return _state_response(stock, state)


@router.get("/states", response_model=PaginatedUserStockStateResponse)
def get_all_stock_states(
    skip: int = Query(0, ge=0),
    limit: int = Query(5, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = (
        db.query(UserStockState, Stock)
        .join(Stock, Stock.id == UserStockState.stock_id)
        .filter(UserStockState.user_id == current_user.id)
    )
    total = query.count()
    
    states = (
        query
        .order_by(UserStockState.last_checked_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    data = [_state_response(stock, state) for state, stock in states]
    
    pagination = PaginationMeta(
        total=total,
        skip=skip,
        limit=limit,
        has_more=(skip + limit) < total
    )
    
    return {
        "data": data,
        "pagination": pagination
    }


@router.get("/{stock_id}/changes", response_model=StockChangeResponse)
def get_stock_changes(
    stock_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stock = (
        db.query(Stock)
        .filter(Stock.id == stock_id, Stock.is_active.is_(True))
        .first()
    )
    if stock is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stock not found",
        )

    state = (
        db.query(UserStockState)
        .filter(
            UserStockState.user_id == current_user.id,
            UserStockState.stock_id == stock_id,
        )
        .first()
    )
    if state is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No previous check found for this stock",
        )

    latest_snapshot = (
        db.query(MarketSnapshot)
        .filter(MarketSnapshot.stock_id == stock_id)
        .order_by(MarketSnapshot.timestamp.desc())
        .first()
    )
    if latest_snapshot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No market snapshot found for this stock",
        )

    reference_snapshot = (
        db.query(MarketSnapshot)
        .filter(
            MarketSnapshot.stock_id == stock_id,
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
    return {"stock_id": stock.id, "symbol": stock.symbol, **change}


@router.get("/{stock_id}/attention", response_model=StockAttentionResponse)
def get_stock_attention(
    stock_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stock = (
        db.query(Stock)
        .filter(Stock.id == stock_id, Stock.is_active.is_(True))
        .first()
    )
    if stock is None:
        raise HTTPException(status_code=404, detail="Stock not found")

    state = (
        db.query(UserStockState)
        .filter(
            UserStockState.user_id == current_user.id,
            UserStockState.stock_id == stock_id,
        )
        .first()
    )
    if state is None:
        raise HTTPException(
            status_code=404,
            detail="No baseline found. Check this stock first to establish a baseline.",
        )

    snapshots = (
        db.query(MarketSnapshot)
        .filter(MarketSnapshot.stock_id == stock_id)
        .order_by(MarketSnapshot.timestamp.desc())
        .all()
    )
    if not snapshots:
        raise HTTPException(status_code=404, detail="No market snapshot found for this stock")

    latest_snapshot = snapshots[0]
    base_response = {
        "stock_id": stock.id,
        "symbol": stock.symbol,
        "reference_price": state.reference_price,
        "reference_timestamp": state.reference_timestamp,
        "current_price": latest_snapshot.close,
        "current_timestamp": latest_snapshot.timestamp,
    }
    if _timestamp_for_comparison(latest_snapshot.timestamp) <= _timestamp_for_comparison(
        state.reference_timestamp
    ):
        return {
            **base_response,
            "price_change": None,
            "price_change_percent": None,
            "direction": None,
            "attention_score": 0,
            "attention_level": "NO_NOTABLE_CHANGE",
            "factors": {
                "price_movement": 0,
                "volume_change": 0,
                "important_level": 0,
                "sustained_movement": 0,
            },
            "volume_change_percent": None,
            "important_level_crossed": False,
            "sustained_movement": False,
            "reason": "No new market data since your last check.",
        }

    price_change = latest_snapshot.close - state.reference_price
    price_change_percent = None if state.reference_price == 0 else (
        price_change / state.reference_price * 100
    )
    direction = "UP" if price_change > 0 else "DOWN" if price_change < 0 else "UNCHANGED"
    previous_snapshot = snapshots[1] if len(snapshots) > 1 else None
    local_current_date = _timestamp_for_comparison(latest_snapshot.timestamp).date()
    prior_days = {}
    for snapshot in snapshots:
        snapshot_date = _timestamp_for_comparison(snapshot.timestamp).date()
        if snapshot_date < local_current_date:
            prior_days.setdefault(snapshot_date, []).append(snapshot)
    previous_day_high = previous_day_low = None
    if prior_days:
        previous_day = max(prior_days)
        previous_day_snapshots = prior_days[previous_day]
        previous_day_high = max(snapshot.high for snapshot in previous_day_snapshots)
        previous_day_low = min(snapshot.low for snapshot in previous_day_snapshots)
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
    return {
        **base_response,
        "price_change": price_change,
        "price_change_percent": round(price_change_percent, 2) if price_change_percent is not None else None,
        "direction": direction,
        **attention,
    }


@router.post("", response_model=StockResponse, status_code=status.HTTP_201_CREATED)
def create_stock(
    payload: StockCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    existing_stock = db.query(Stock).filter(Stock.symbol == payload.symbol).first()
    if existing_stock:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stock already exists",
        )

    stock = Stock(
        symbol=payload.symbol,
        company_name=payload.company_name,
        exchange=payload.exchange,
        is_active=True,
    )
    db.add(stock)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stock already exists",
        ) from exc

    db.refresh(stock)
    return stock


@router.patch("/{stock_id}/status", response_model=StockStatusResponse)
def update_stock_status(
    stock_id: int,
    payload: StockStatusUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    stock = db.query(Stock).filter(Stock.id == stock_id).first()
    if stock is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stock not found",
        )

    stock.is_active = payload.is_active
    db.commit()
    return {
        "message": "Stock status updated successfully",
        "is_active": stock.is_active,
    }


@router.get("/{stock_id}", response_model=StockResponse)
def get_stock(stock_id: int, db: Session = Depends(get_db)):
    stock = (
        db.query(Stock)
        .filter(Stock.id == stock_id, Stock.is_active.is_(True))
        .first()
    )
    if stock is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stock not found",
        )
    return stock
