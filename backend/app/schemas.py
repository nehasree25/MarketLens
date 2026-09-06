from __future__ import annotations

import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class SignupRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, max_length=150)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r"[A-Z]", value):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", value):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", value):
            raise ValueError("Password must contain at least one number")
        if not re.search(r"[^A-Za-z0-9]", value):
            raise ValueError("Password must contain at least one special character")
        return value


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    is_admin: bool = False
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class StockCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    symbol: str = Field(..., min_length=1, max_length=20)
    company_name: str = Field(..., min_length=1, max_length=255)
    exchange: str = Field(..., min_length=1, max_length=100)

    @field_validator("symbol", mode="before")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        if not isinstance(value, str):
            raise ValueError("Symbol must be text")
        value = value.strip().upper()
        if not value:
            raise ValueError("Symbol cannot be empty")
        return value

    @field_validator("company_name", "exchange", mode="before")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        if not isinstance(value, str):
            raise ValueError("Value must be text")
        value = value.strip()
        if not value:
            raise ValueError("Value cannot be empty")
        return value


class StockResponse(BaseModel):
    id: int
    symbol: str
    company_name: str
    exchange: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class StockStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    is_active: bool


class StockStatusResponse(BaseModel):
    message: str
    is_active: bool


class UserStockStateResponse(BaseModel):
    stock_id: int
    symbol: str
    reference_price: float
    reference_timestamp: datetime
    last_checked_at: datetime


class UserStockCheckResponse(UserStockStateResponse):
    message: str


class StockChangeResponse(BaseModel):
    status: str
    message: str
    stock_id: int
    symbol: str
    reference_price: float
    reference_timestamp: datetime
    current_price: float
    current_timestamp: datetime
    reference_volume: int | None = None
    current_volume: int | None = None
    price_change: float | None = None
    price_change_percent: float | None = None
    direction: str | None = None


class AttentionFactors(BaseModel):
    price_movement: int
    volume_change: int
    important_level: int
    sustained_movement: int


class StockAttentionResponse(BaseModel):
    stock_id: int
    symbol: str
    reference_price: float
    reference_timestamp: datetime
    current_price: float
    current_timestamp: datetime
    price_change: float | None = None
    price_change_percent: float | None = None
    direction: str | None = None
    attention_score: int
    attention_level: str
    factors: AttentionFactors
    volume_change_percent: float | None = None
    important_level_crossed: bool
    sustained_movement: bool
    reason: str


class WatchlistCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, max_length=150)

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        if not isinstance(value, str):
            raise ValueError("Watchlist name must be text")
        value = value.strip()
        if not value:
            raise ValueError("Watchlist name cannot be empty")
        return value


class WatchlistUpdate(WatchlistCreate):
    pass


class WatchlistStockAdd(BaseModel):
    model_config = ConfigDict(extra="forbid")

    stock_id: int = Field(..., gt=0)


class WatchlistStockResponse(BaseModel):
    id: int
    symbol: str
    company_name: str
    exchange: str


class WatchlistResponse(BaseModel):
    id: int
    name: str
    stocks: list[WatchlistStockResponse]
    created_at: datetime


class WatchlistChangeSummary(BaseModel):
    total_stocks: int
    high_attention: int
    notable: int
    mild: int
    no_notable_change: int


class WatchlistChangeStock(BaseModel):
    stock_id: int
    symbol: str
    current_price: float
    price_change: float | None = None
    price_change_percent: float | None = None
    direction: str | None = None
    attention_score: int
    attention_level: str
    volume_change_percent: float | None = None
    important_level_crossed: bool
    sustained_movement: bool
    reason: str
    status: str


class WatchlistChangesResponse(BaseModel):
    watchlist_id: int
    watchlist_name: str
    summary: WatchlistChangeSummary
    stocks: list[WatchlistChangeStock]


class DashboardWatchlistInfo(BaseModel):
    watchlist_id: int
    watchlist_name: str


class DashboardStockSummary(BaseModel):
    stock_id: int
    symbol: str
    current_price: float
    price_change: float | None = None
    price_change_percent: float | None = None
    direction: str | None = None
    attention_score: int
    attention_level: str
    volume_change_percent: float | None = None
    important_level_crossed: bool
    sustained_movement: bool
    reason: str
    status: str
    watchlists: list[DashboardWatchlistInfo] = []


class DashboardSummaryResponse(BaseModel):
    total_stocks: int
    high_attention: int
    notable: int
    mild: int
    no_notable_change: int
    stocks: list[DashboardStockSummary]


class MarketDataResponse(BaseModel):
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    timestamp: datetime
