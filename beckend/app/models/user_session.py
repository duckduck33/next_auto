from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
import uuid

class UserSession(BaseModel):
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
    created_at: datetime
    last_activity: datetime
    current_symbol: Optional[str] = None

class CalendarData(BaseModel):
    session_id: str
    date: str  # YYYY-MM-DD format
    profit: float
    profit_rate: float
    created_at: datetime

class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, UserSession] = {}
    
    def create_session(self, api_key: str, secret_key: str, exchange_type: str, 
                      investment: float, leverage: int, take_profit: float, 
                      stop_loss: float, indicator: str) -> str:
        """새로운 사용자 세션을 생성합니다."""
        session_id = str(uuid.uuid4())
        now = datetime.now()
        
        session = UserSession(
            session_id=session_id,
            api_key=api_key,
            secret_key=secret_key,
            exchange_type=exchange_type,
            investment=investment,
            leverage=leverage,
            take_profit=take_profit,
            stop_loss=stop_loss,
            indicator=indicator,
            is_auto_trading_enabled=False,
            created_at=now,
            last_activity=now
        )
        
        self.sessions[session_id] = session
        return session_id
    
    def get_session(self, session_id: str) -> Optional[UserSession]:
        """세션 ID로 세션을 조회합니다."""
        return self.sessions.get(session_id)
    
    def update_session(self, session_id: str, **kwargs) -> bool:
        """세션 정보를 업데이트합니다."""
        if session_id not in self.sessions:
            return False
        
        session = self.sessions[session_id]
        for key, value in kwargs.items():
            if hasattr(session, key):
                setattr(session, key, value)
        
        session.last_activity = datetime.now()
        return True
    
    def delete_session(self, session_id: str) -> bool:
        """세션을 삭제합니다."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False
    
    def cleanup_inactive_sessions(self, max_inactive_hours: int = 24):
        """비활성 세션을 정리합니다."""
        now = datetime.now()
        to_delete = []
        
        for session_id, session in self.sessions.items():
            inactive_hours = (now - session.last_activity).total_seconds() / 3600
            if inactive_hours > max_inactive_hours:
                to_delete.append(session_id)
        
        for session_id in to_delete:
            del self.sessions[session_id]

# 전역 세션 매니저 인스턴스
session_manager = SessionManager()
