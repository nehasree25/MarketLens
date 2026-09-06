from __future__ import annotations

import os

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.auth import (
    create_access_token,
    get_current_admin,
    get_current_user,
    get_db,
    hash_password,
    verify_password,
)
from app.dashboard import router as dashboard_router
from app.database import Base, SessionLocal, engine
from app.models import (  # noqa: F401
    MarketSnapshot,
    Stock,
    User,
    UserStockState,
    Watchlist,
    WatchlistStock,
)
from app.schemas import LoginRequest, SignupRequest, Token, UserResponse
from app.stocks import router as stocks_router, seed_initial_stocks
from app.watchlists import router as watchlists_router
from app.market_data import router as market_data_router
from app.snapshot_collector import start_snapshot_scheduler, stop_snapshot_scheduler

app = FastAPI(
    title="MarketLens API",
    version="1.0.0"
)


def ensure_user_is_admin_column() -> None:
    with engine.begin() as conn:
        conn.execute(
            text(
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN NOT NULL DEFAULT FALSE;"
            )
        )
        conn.execute(
            text(
                "UPDATE users SET is_admin = FALSE WHERE is_admin IS NULL;"
            )
        )


def ensure_default_admin() -> None:
    admin_name = os.getenv("ADMIN_NAME")
    admin_email = os.getenv("ADMIN_EMAIL")
    admin_password = os.getenv("ADMIN_PASSWORD")

    if not admin_name or not admin_email or not admin_password:
        return

    with SessionLocal() as db:
        existing = db.query(User).filter(User.email == admin_email.lower()).first()
        if existing:
            if existing.is_admin is False:
                existing.is_admin = True
                db.commit()
            return

        user = User(
            name=admin_name.strip(),
            email=admin_email.lower(),
            password_hash=hash_password(admin_password),
            is_admin=True,
        )
        db.add(user)
        db.commit()


def ensure_market_snapshot_unique_constraint() -> None:
    constraint_name = "uq_market_snapshots_stock_timestamp"
    with engine.begin() as conn:
        constraint_exists = conn.execute(
            text(
                "SELECT 1 FROM pg_constraint "
                "WHERE conrelid = 'market_snapshots'::regclass "
                "AND conname = :constraint_name"
            ),
            {"constraint_name": constraint_name},
        ).first()
        if constraint_exists is None:
            conn.execute(
                text(
                    "ALTER TABLE market_snapshots "
                    "ADD CONSTRAINT uq_market_snapshots_stock_timestamp "
                    "UNIQUE (stock_id, timestamp)"
                )
            )


def ensure_user_stock_state_unique_constraint() -> None:
    constraint_name = "uq_user_stock_state_user_stock"
    with engine.begin() as conn:
        constraint_exists = conn.execute(
            text(
                "SELECT 1 FROM pg_constraint "
                "WHERE conrelid = 'user_stock_state'::regclass "
                "AND conname = :constraint_name"
            ),
            {"constraint_name": constraint_name},
        ).first()
        if constraint_exists is None:
            conn.execute(
                text(
                    "ALTER TABLE user_stock_state "
                    "ADD CONSTRAINT uq_user_stock_state_user_stock "
                    "UNIQUE (user_id, stock_id)"
                )
            )


@app.on_event("startup")
def create_db_tables() -> None:
    Base.metadata.create_all(bind=engine)
    ensure_user_is_admin_column()
    ensure_default_admin()
    ensure_market_snapshot_unique_constraint()
    ensure_user_stock_state_unique_constraint()
    with SessionLocal() as db:
        seed_initial_stocks(db)
    start_snapshot_scheduler()


@app.on_event("shutdown")
def stop_background_tasks() -> None:
    stop_snapshot_scheduler()


app.include_router(stocks_router)
app.include_router(watchlists_router)
app.include_router(dashboard_router)
app.include_router(market_data_router)


@app.post("/auth/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    user = User(
        name=payload.name.strip(),
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        is_admin=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/auth/login", response_model=Token)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(user.id, is_admin=user.is_admin)
    return {"access_token": token, "token_type": "bearer"}


@app.get("/auth/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    return current_user


@app.get("/auth/admin-test")
def admin_test(current_user: User = Depends(get_current_admin)):
    return {"message": "Admin access granted"}


@app.post("/auth/logout")
def logout(current_user: User = Depends(get_current_user)):
    return {"message": "Successfully logged out"}