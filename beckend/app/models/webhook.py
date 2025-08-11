from pydantic import BaseModel
from typing import Optional

class WebhookData(BaseModel):
    symbol: str
    side: Optional[str] = None  # is_close일 때는 side 무시
    quantity: Optional[float] = None  # is_close일 때는 quantity 무시
    leverage: Optional[int] = 20
    take_profit_percentage: Optional[float] = None
    stop_loss_percentage: Optional[float] = None
    is_close: bool = False