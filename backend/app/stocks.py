from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import get_current_admin, get_db
from app.models import Stock, User
from app.schemas import (
    StockCreate,
    StockResponse,
    StockStatusResponse,
    StockStatusUpdate,
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
