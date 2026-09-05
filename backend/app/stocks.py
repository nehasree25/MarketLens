from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import get_current_admin, get_current_user, get_db
from app.models import MarketSnapshot, Stock, User, UserStockState
from app.schemas import (
    StockCreate,
    StockResponse,
    StockStatusResponse,
    StockStatusUpdate,
    UserStockCheckResponse,
    UserStockStateResponse,
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


@router.get("", response_model=list[StockResponse])
def list_stocks(db: Session = Depends(get_db)):
    return (
        db.query(Stock)
        .filter(Stock.is_active.is_(True))
        .order_by(Stock.id)
        .all()
    )


@router.get("/search", response_model=list[StockResponse])
def search_stocks(
    q: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
):
    query = q.strip()
    if not query:
        return []

    search_term = f"%{query}%"
    return (
        db.query(Stock)
        .filter(
            Stock.is_active.is_(True),
            (Stock.symbol.ilike(search_term) | Stock.company_name.ilike(search_term)),
        )
        .order_by(Stock.id)
        .all()
    )


def _state_response(stock: Stock, state: UserStockState) -> dict[str, object]:
    return {
        "stock_id": stock.id,
        "symbol": stock.symbol,
        "reference_price": state.reference_price,
        "reference_timestamp": state.reference_timestamp,
        "last_checked_at": state.last_checked_at,
    }


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


@router.get("/states", response_model=list[UserStockStateResponse])
def get_all_stock_states(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    states = (
        db.query(UserStockState, Stock)
        .join(Stock, Stock.id == UserStockState.stock_id)
        .filter(UserStockState.user_id == current_user.id)
        .order_by(UserStockState.last_checked_at.desc())
        .all()
    )
    return [_state_response(stock, state) for state, stock in states]


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
