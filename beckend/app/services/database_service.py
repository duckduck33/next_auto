from typing import List, Optional, Dict, Any
from datetime import datetime, date
from app.core.database import db
from app.models.database_models import CalendarDataDB, UserSessionDB, TradingHistoryDB
import json

class DatabaseService:
    def __init__(self):
        self.db = db
    
    async def save_calendar_data(self, session_id: str, calendar_data: Dict[str, Any]) -> bool:
        """사용자별 캘린더 데이터를 저장합니다."""
        try:
            collection = self.db.client[self.db.database_name].calendar_data
            
            # 기존 데이터 삭제
            await collection.delete_many({"session_id": session_id})
            
            # 새 데이터 저장
            for date_str, data in calendar_data.items():
                calendar_entry = CalendarDataDB(
                    session_id=session_id,
                    date=date_str,
                    profit=data.get('profit', 0),
                    profit_rate=data.get('profit_rate', 0),
                    symbol=data.get('symbol'),
                    position_side=data.get('position_side'),
                    entry_price=data.get('entry_price'),
                    exit_price=data.get('exit_price'),
                    quantity=data.get('quantity'),
                    leverage=data.get('leverage'),
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                
                await collection.insert_one(calendar_entry.dict())
            
            return True
        except Exception as e:
            print(f"캘린더 데이터 저장 오류: {e}")
            return False
    
    async def get_calendar_data(self, session_id: str) -> Dict[str, Any]:
        """사용자별 캘린더 데이터를 조회합니다."""
        try:
            collection = self.db.client[self.db.database_name].calendar_data
            cursor = collection.find({"session_id": session_id})
            
            calendar_data = {}
            async for doc in cursor:
                calendar_data[doc['date']] = {
                    'profit': doc['profit'],
                    'profit_rate': doc['profit_rate'],
                    'symbol': doc.get('symbol'),
                    'position_side': doc.get('position_side'),
                    'entry_price': doc.get('entry_price'),
                    'exit_price': doc.get('exit_price'),
                    'quantity': doc.get('quantity'),
                    'leverage': doc.get('leverage')
                }
            
            return calendar_data
        except Exception as e:
            print(f"캘린더 데이터 조회 오류: {e}")
            return {}
    
    async def save_user_session(self, session_data: UserSessionDB) -> bool:
        """사용자 세션 정보를 저장합니다."""
        try:
            collection = self.db.client[self.db.database_name].user_sessions
            
            # 기존 세션 업데이트 또는 새로 생성
            await collection.replace_one(
                {"session_id": session_data.session_id},
                session_data.dict(),
                upsert=True
            )
            
            return True
        except Exception as e:
            print(f"사용자 세션 저장 오류: {e}")
            return False
    
    async def get_user_session(self, session_id: str) -> Optional[UserSessionDB]:
        """사용자 세션 정보를 조회합니다."""
        try:
            collection = self.db.client[self.db.database_name].user_sessions
            doc = await collection.find_one({"session_id": session_id})
            
            if doc:
                return UserSessionDB(**doc)
            return None
        except Exception as e:
            print(f"사용자 세션 조회 오류: {e}")
            return None
    
    async def save_trading_history(self, trading_data: TradingHistoryDB) -> bool:
        """거래 히스토리를 저장합니다."""
        try:
            collection = self.db.client[self.db.database_name].trading_history
            await collection.insert_one(trading_data.dict())
            return True
        except Exception as e:
            print(f"거래 히스토리 저장 오류: {e}")
            return False
    
    async def update_trading_history(self, session_id: str, symbol: str, 
                                   exit_price: float, profit: float, 
                                   profit_rate: float) -> bool:
        """거래 히스토리를 업데이트합니다 (포지션 종료 시)."""
        try:
            collection = self.db.client[self.db.database_name].trading_history
            
            await collection.update_one(
                {
                    "session_id": session_id,
                    "symbol": symbol,
                    "status": "OPEN"
                },
                {
                    "$set": {
                        "exit_price": exit_price,
                        "profit": profit,
                        "profit_rate": profit_rate,
                        "exit_time": datetime.now(),
                        "status": "CLOSED"
                    }
                }
            )
            
            return True
        except Exception as e:
            print(f"거래 히스토리 업데이트 오류: {e}")
            return False
    
    async def get_daily_profit_summary(self, session_id: str, target_date: str) -> Dict[str, Any]:
        """특정 날짜의 수익 요약을 조회합니다."""
        try:
            collection = self.db.client[self.db.database_name].trading_history
            
            # 해당 날짜의 모든 거래 조회
            start_date = datetime.strptime(target_date, "%Y-%m-%d")
            end_date = datetime.strptime(target_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
            
            cursor = collection.find({
                "session_id": session_id,
                "entry_time": {"$gte": start_date, "$lte": end_date},
                "status": "CLOSED"
            })
            
            total_profit = 0
            total_profit_rate = 0
            trade_count = 0
            
            async for doc in cursor:
                if doc.get('profit') is not None:
                    total_profit += doc['profit']
                    total_profit_rate += doc.get('profit_rate', 0)
                    trade_count += 1
            
            return {
                'date': target_date,
                'total_profit': total_profit,
                'total_profit_rate': total_profit_rate,
                'trade_count': trade_count,
                'average_profit_rate': total_profit_rate / trade_count if trade_count > 0 else 0
            }
        except Exception as e:
            print(f"일별 수익 요약 조회 오류: {e}")
            return {
                'date': target_date,
                'total_profit': 0,
                'total_profit_rate': 0,
                'trade_count': 0,
                'average_profit_rate': 0
            }

# 전역 데이터베이스 서비스 인스턴스
database_service = DatabaseService()
