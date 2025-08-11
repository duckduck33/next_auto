from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class CalendarDataDB(BaseModel):
    session_id: str
    date: str  # YYYY-MM-DD format
    profit: float
    profit_rate: float
    symbol: Optional[str] = None
    position_side: Optional[str] = None
    entry_price: Optional[float] = None
    exit_price: Optional[float] = None
    quantity: Optional[float] = None
    leverage: Optional[int] = None
    created_at: datetime
    updated_at: datetime

class UserSessionDB(BaseModel):
    session_id: str
    api_key: str
    secret_key: str
    exchange_type: str  # "demo" or "live"
    investment: float
    leverage: int
    take_profit: float
    stop_loss: float
    indicator: str
    is_auto_trading_enabled: bool
    current_symbol: Optional[str] = None
    created_at: datetime
    last_activity: datetime

class TradingHistoryDB(BaseModel):
    session_id: str
    symbol: str
    position_side: str  # "LONG" or "SHORT"
    entry_price: float
    exit_price: Optional[float] = None
    quantity: float
    leverage: int
    profit: Optional[float] = None
    profit_rate: Optional[float] = None
    entry_time: datetime
    exit_time: Optional[datetime] = None
    status: str  # "OPEN", "CLOSED"
    created_at: datetime
