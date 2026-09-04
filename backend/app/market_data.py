from __future__ import annotations

from datetime import datetime
from math import isfinite
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
import yfinance as yf

from app.auth import get_current_user, get_db
from app.models import Stock, User
from app.schemas import MarketDataResponse

router = APIRouter(prefix="/market-data", tags=["Market Data"])


class MarketDataUnavailable(Exception):
    pass


def _as_number(value: Any, field_name: str) -> float | int:
    if value is None:
        raise MarketDataUnavailable(f"Missing {field_name} market data")

    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise MarketDataUnavailable(f"Invalid {field_name} market data") from exc

    if not isfinite(number):
        raise MarketDataUnavailable(f"Missing {field_name} market data")

    if field_name == "volume":
        return int(number)
    return number


def _as_timestamp(value: Any) -> datetime:
    if value is None:
        raise MarketDataUnavailable("Missing market data timestamp")

    timestamp = value.to_pydatetime() if hasattr(value, "to_pydatetime") else value
    if not isinstance(timestamp, datetime):
        raise MarketDataUnavailable("Invalid market data timestamp")
    return timestamp


def fetch_latest_market_data(symbol: str) -> dict[str, Any]:
    try:
        history = yf.Ticker(symbol).history(period="1d", interval="5m")
    except Exception as exc:
        raise MarketDataUnavailable("Market data is currently unavailable") from exc

    if history is None or history.empty:
        raise MarketDataUnavailable("Market data is currently unavailable")

    latest = history.iloc[-1]
    try:
        return {
            "symbol": symbol,
            "open": _as_number(latest.get("Open"), "open"),
            "high": _as_number(latest.get("High"), "high"),
            "low": _as_number(latest.get("Low"), "low"),
            "close": _as_number(latest.get("Close"), "close"),
            "volume": _as_number(latest.get("Volume"), "volume"),
            "timestamp": _as_timestamp(history.index[-1]),
        }
    except (KeyError, TypeError, IndexError) as exc:
        raise MarketDataUnavailable("Market data is currently unavailable") from exc


def _fetch_or_raise(symbol: str) -> dict[str, Any]:
    try:
        return fetch_latest_market_data(symbol)
    except MarketDataUnavailable as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Market data is currently unavailable",
        ) from exc


@router.get("", response_model=list[MarketDataResponse])
def get_market_data(
    symbols: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if symbols is None:
        stocks = (
            db.query(Stock)
            .filter(Stock.is_active.is_(True))
            .order_by(Stock.id)
            .all()
        )
    else:
        requested_symbols = list(
            dict.fromkeys(
                symbol.strip().upper()
                for symbol in symbols.split(",")
                if symbol.strip()
            )
        )
        if not requested_symbols:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one stock symbol is required",
            )

        stocks_by_symbol = {
            stock.symbol: stock
            for stock in db.query(Stock)
            .filter(Stock.is_active.is_(True), Stock.symbol.in_(requested_symbols))
            .all()
        }
        if len(stocks_by_symbol) != len(requested_symbols):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or more requested stocks are not active or supported",
            )
        stocks = [stocks_by_symbol[symbol] for symbol in requested_symbols]

    return [_fetch_or_raise(stock.symbol) for stock in stocks]


@router.get("/{stock_id}", response_model=MarketDataResponse)
def get_market_data_for_stock(
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

    return _fetch_or_raise(stock.symbol)
