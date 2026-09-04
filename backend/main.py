from fastapi import FastAPI

from app.database import Base, engine
from app.models import (  # noqa: F401
    MarketSnapshot,
    Stock,
    User,
    UserStockState,
    Watchlist,
    WatchlistStock,
)

app = FastAPI(
    title="MarketLens API",
    version="1.0.0"
)


@app.on_event("startup")
def create_db_tables() -> None:
    Base.metadata.create_all(bind=engine)