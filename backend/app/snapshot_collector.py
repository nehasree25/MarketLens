from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from datetime import datetime, time
from zoneinfo import ZoneInfo

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.market_data import MarketDataUnavailable, fetch_latest_market_data
from app.models import MarketSnapshot, Stock

logger = logging.getLogger(__name__)

COLLECTION_INTERVAL_SECONDS = 5 * 60
_scheduler_started = False
_scheduler_lock = threading.Lock()
_scheduler_stop = threading.Event()
NSE_TIMEZONE = ZoneInfo("Asia/Kolkata")
NSE_MARKET_OPEN = time(9, 15)
NSE_MARKET_CLOSE = time(15, 30)


def is_nse_market_open(current_time: datetime) -> bool:
    """Return whether an aware datetime falls within normal NSE hours."""
    if current_time.tzinfo is None or current_time.utcoffset() is None:
        raise ValueError("Market-hours comparison requires a timezone-aware datetime")

    market_time = current_time.astimezone(NSE_TIMEZONE)
    return (
        market_time.weekday() < 5
        and NSE_MARKET_OPEN <= market_time.time() <= NSE_MARKET_CLOSE
    )


def _valid_market_observation_timestamp(
    timestamp: datetime,
    current_time: datetime,
) -> bool:
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        return False

    observation_time = timestamp.astimezone(NSE_TIMEZONE)
    current_market_time = current_time.astimezone(NSE_TIMEZONE)
    return (
        observation_time.date() == current_market_time.date()
        and NSE_MARKET_OPEN <= observation_time.time() <= NSE_MARKET_CLOSE
        and observation_time <= current_market_time
    )


def collect_market_snapshots(
    session_factory: Callable[[], Session] = SessionLocal,
) -> int:
    """Fetch and persist one latest observation for every active stock."""
    current_time = datetime.now(NSE_TIMEZONE)
    if not is_nse_market_open(current_time):
        logger.info("NSE market is closed; skipping market snapshot collection")
        return 0

    logger.info("Starting market snapshot collection")
    db = session_factory()
    collected_count = 0
    try:
        active_stocks = (
            db.query(Stock)
            .filter(Stock.is_active.is_(True))
            .order_by(Stock.id)
            .all()
        )

        for stock in active_stocks:
            market_data = {}
            try:
                market_data = fetch_latest_market_data(stock.symbol)
                timestamp = market_data.get("timestamp")
                if not isinstance(timestamp, datetime):
                    raise MarketDataUnavailable("Invalid market data timestamp")
                    
                if not _valid_market_observation_timestamp(timestamp, current_time):
                    raise MarketDataUnavailable(
                        "Market data timestamp is stale or outside NSE market hours"
                    )

                snapshot = MarketSnapshot(
                    stock_id=stock.id,
                    open=market_data["open"],
                    high=market_data["high"],
                    low=market_data["low"],
                    close=market_data["close"],
                    volume=market_data["volume"],
                    timestamp=timestamp,
                )
                db.add(snapshot)
                db.commit()
                collected_count += 1
                logger.info("Collected snapshot for %s", stock.symbol)
            except IntegrityError:
                db.rollback()
                logger.info(
                    "Snapshot already exists for %s at %s",
                    stock.symbol,
                    market_data.get("timestamp", "unknown"),
                )
            except (MarketDataUnavailable, KeyError, TypeError, ValueError) as exc:
                db.rollback()
                logger.warning("Failed to collect snapshot for %s: %s", stock.symbol, exc)
            except Exception:
                db.rollback()
                logger.exception("Failed to collect snapshot for %s", stock.symbol)
    finally:
        db.close()

    logger.info(
        "Market snapshot collection completed: %s new snapshots",
        collected_count,
    )
    return collected_count


def _scheduler_loop() -> None:
    while not _scheduler_stop.is_set():
        try:
            collect_market_snapshots()
        except Exception:
            logger.exception("Market snapshot collection failed unexpectedly")
        _scheduler_stop.wait(COLLECTION_INTERVAL_SECONDS)


def start_snapshot_scheduler() -> None:
    global _scheduler_started
    with _scheduler_lock:
        if _scheduler_started:
            return
        _scheduler_started = True
        threading.Thread(
            target=_scheduler_loop,
            name="market-snapshot-collector",
            daemon=True,
        ).start()
        logger.info(
            "Market snapshot scheduler started with a %s-minute interval",
            COLLECTION_INTERVAL_SECONDS // 60,
        )


def stop_snapshot_scheduler() -> None:
    _scheduler_stop.set()
