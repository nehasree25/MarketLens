from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.auth import get_current_user, get_db
from app.models import Stock, User, Watchlist, WatchlistStock
from app.schemas import (
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
