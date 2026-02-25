from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


AssetClass = Literal["equity", "option", "future", "crypto", "fx"]
Side = Literal["BUY", "SELL"]
EventType = Literal["new_order", "cancel", "fill", "trade"]


class MarketEvent(BaseModel):
    event_id: str
    ts: datetime
    venue: str
    asset_class: AssetClass
    symbol: str
    account_id: str
    side: Side
    event_type: EventType
    order_id: str | None = None
    trade_id: str | None = None
    counterparty_account_id: str | None = None
    quantity: float = Field(gt=0)
    price: float = Field(gt=0)
    order_type: str = "LIMIT"
    metadata: dict[str, str | float | int] = Field(default_factory=dict)


class Alert(BaseModel):
    alert_id: str
    ts: datetime
    detector: str
    pattern: str
    tenant_id: str | None = None
    account_id: str
    symbol: str
    severity: Literal["critical", "high", "medium", "low"]
    score: float = Field(ge=0, le=1)
    reason: str
    evidence: dict[str, float | int | str]


class DetectionResult(BaseModel):
    alerts: list[Alert]


class IngestResponse(BaseModel):
    accepted: bool
    generated_alerts: int
    alert_ids: list[str]


class CaseCreateRequest(BaseModel):
    alert_id: str
    account_id: str
    symbol: str
    severity: Literal["critical", "high", "medium", "low"]
    summary: str


class CaseResponse(BaseModel):
    id: int
    tenant_id: str
    alert_id: str
    account_id: str
    symbol: str
    status: str
    severity: str
    summary: str
    created_at: datetime


class RegisterRequest(BaseModel):
    email: str
    password: str


class RegisterResponse(BaseModel):
    user_id: int
    tenant_id: str
    email: str


class TokenRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ApiKeyCreateRequest(BaseModel):
    name: str = "default"


class ApiKeyResponse(BaseModel):
    key_id: int
    name: str
    key_prefix: str
    api_key: str | None = None
