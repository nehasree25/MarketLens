import os
from datetime import datetime, timezone

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("JWT_SECRET_KEY", "phase8-test-secret")

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import stocks
from app.auth import hash_password
from app.database import Base
from app.models import MarketSnapshot, Stock, User, UserStockState


def _create_test_context():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    db = session_factory()

    user = User(
        name="User One",
        email="one@example.com",
        password_hash=hash_password("Password1!"),
        is_admin=False,
    )
    other_user = User(
        name="User Two",
        email="two@example.com",
        password_hash=hash_password("Password1!"),
        is_admin=False,
    )
    active_stock = Stock(
        symbol="RELIANCE.NS",
        company_name="Reliance Industries",
        exchange="NSE",
        is_active=True,
    )
    no_snapshot_stock = Stock(
        symbol="TCS.NS",
        company_name="Tata Consultancy Services",
        exchange="NSE",
        is_active=True,
    )
    inactive_stock = Stock(
        symbol="INFY.NS",
        company_name="Infosys",
        exchange="NSE",
        is_active=False,
    )
    db.add_all([user, other_user, active_stock, no_snapshot_stock, inactive_stock])
    db.flush()
    db.add_all(
        [
            MarketSnapshot(
                stock_id=active_stock.id,
                open=1320,
                high=1330,
                low=1315,
                close=1329,
                volume=1000,
                timestamp=datetime(2026, 9, 4, 15, 10, tzinfo=timezone.utc),
            ),
            MarketSnapshot(
                stock_id=active_stock.id,
                open=1330,
                high=1340,
                low=1325,
                close=1339,
                volume=1100,
                timestamp=datetime(2026, 9, 4, 15, 15, tzinfo=timezone.utc),
            ),
        ]
    )
    db.commit()

    app = FastAPI()
    app.include_router(stocks.router)
    current_user = {"value": user}

    def override_db():
        yield db

    def override_current_user():
        return current_user["value"]

    app.dependency_overrides[stocks.get_db] = override_db
    app.dependency_overrides[stocks.get_current_user] = override_current_user
    return engine, db, app, current_user, user, other_user, active_stock, no_snapshot_stock, inactive_stock


def test_phase8_check_state_and_user_isolation():
    engine, db, app, current_user, user, other_user, active_stock, _, _ = _create_test_context()
    try:
        with TestClient(app) as client:
            response = client.post(f"/stocks/{active_stock.id}/check")
            assert response.status_code == 200
            assert response.json()["message"] == "Baseline established"
            assert response.json()["reference_price"] == 1339.0

            assert db.query(UserStockState).count() == 1
            state = db.query(UserStockState).one()
            assert state.user_id == user.id
            assert state.reference_timestamp == datetime(2026, 9, 4, 15, 15)
            assert state.last_checked_at is not None

            response = client.get(f"/stocks/{active_stock.id}/state")
            assert response.status_code == 200
            assert response.json()["symbol"] == "RELIANCE.NS"

            response = client.get("/stocks/states")
            assert response.status_code == 200
            assert len(response.json()) == 1

            current_user["value"] = other_user
            response = client.get(f"/stocks/{active_stock.id}/state")
            assert response.status_code == 404
            assert response.json()["detail"] == "No check history found for this stock"
    finally:
        db.close()
        Base.metadata.drop_all(engine)


def test_phase8_second_check_updates_existing_state():
    engine, db, app, _, user, _, active_stock, _, _ = _create_test_context()
    try:
        with TestClient(app) as client:
            assert client.post(f"/stocks/{active_stock.id}/check").status_code == 200
            db.add(
                MarketSnapshot(
                    stock_id=active_stock.id,
                    open=1340,
                    high=1350,
                    low=1335,
                    close=1345,
                    volume=1200,
                    timestamp=datetime(2026, 9, 4, 15, 20, tzinfo=timezone.utc),
                )
            )
            db.commit()

            response = client.post(f"/stocks/{active_stock.id}/check")
            assert response.status_code == 200
            assert response.json()["message"] == "Baseline updated"
            assert response.json()["reference_price"] == 1345.0
            assert db.query(UserStockState).filter(UserStockState.user_id == user.id).count() == 1
    finally:
        db.close()
        Base.metadata.drop_all(engine)


def test_phase8_rejects_missing_snapshot_and_inactive_stock():
    engine, db, app, _, _, _, _, no_snapshot_stock, inactive_stock = _create_test_context()
    try:
        with TestClient(app) as client:
            response = client.post(f"/stocks/{no_snapshot_stock.id}/check")
            assert response.status_code == 404
            assert response.json()["detail"] == "No market snapshot found for this stock"

            response = client.post(f"/stocks/{inactive_stock.id}/check")
            assert response.status_code == 404
            assert response.json()["detail"] == "Stock not found"
    finally:
        db.close()
        Base.metadata.drop_all(engine)


def test_phase8_requires_authentication():
    engine, db, app, _, _, _, active_stock, _, _ = _create_test_context()
    try:
        app.dependency_overrides.pop(stocks.get_current_user)
        with TestClient(app) as client:
            response = client.post(f"/stocks/{active_stock.id}/check")
            assert response.status_code == 401
            assert response.json()["detail"] == "Not authenticated"
    finally:
        db.close()
        Base.metadata.drop_all(engine)