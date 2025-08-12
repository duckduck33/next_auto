import sqlite3
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from app.core.sqlite_database import sqlite_db

logger = logging.getLogger(__name__)

class SQLiteSessionService:
    def __init__(self):
        self.db = sqlite_db
    
    def save_session(self, session_data: Dict[str, Any]) -> bool:
        """세션 저장 또는 업데이트"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # 기존 세션 확인
                cursor.execute(
                    "SELECT session_id FROM user_sessions WHERE session_id = ?",
                    (session_data['session_id'],)
                )
                existing = cursor.fetchone()
                
                if existing:
                    # 기존 세션 업데이트
                    cursor.execute('''
                        UPDATE user_sessions SET
                            api_key = ?, secret_key = ?, exchange_type = ?,
                            investment = ?, leverage = ?, take_profit = ?, stop_loss = ?,
                            indicator = ?, is_auto_trading_enabled = ?, current_symbol = ?,
                            last_activity = ?
                        WHERE session_id = ?
                    ''', (
                        session_data['api_key'], session_data['secret_key'], session_data['exchange_type'],
                        session_data['investment'], session_data['leverage'], session_data['take_profit'],
                        session_data['stop_loss'], session_data['indicator'], session_data['is_auto_trading_enabled'],
                        session_data.get('current_symbol'), datetime.now(), session_data['session_id']
                    ))
                    logger.info(f"세션 업데이트: {session_data['session_id']}")
                else:
                    # 새 세션 생성
                    cursor.execute('''
                        INSERT INTO user_sessions (
                            session_id, user_email, api_key, secret_key, exchange_type,
                            investment, leverage, take_profit, stop_loss, indicator,
                            is_auto_trading_enabled, current_symbol, created_at, last_activity
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        session_data['session_id'], session_data['user_email'], session_data['api_key'],
                        session_data['secret_key'], session_data['exchange_type'], session_data['investment'],
                        session_data['leverage'], session_data['take_profit'], session_data['stop_loss'],
                        session_data['indicator'], session_data['is_auto_trading_enabled'],
                        session_data.get('current_symbol'), datetime.now(), datetime.now()
                    ))
                    logger.info(f"새 세션 생성: {session_data['session_id']}")
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"세션 저장 오류: {str(e)}")
            return False
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """세션 조회"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM user_sessions WHERE session_id = ?",
                    (session_id,)
                )
                row = cursor.fetchone()
                
                if row:
                    return dict(row)
                return None
                
        except Exception as e:
            logger.error(f"세션 조회 오류: {str(e)}")
            return None
    
    def get_user_sessions(self, user_email: str) -> List[Dict[str, Any]]:
        """사용자의 모든 세션 조회"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM user_sessions WHERE user_email = ? ORDER BY created_at DESC",
                    (user_email,)
                )
                rows = cursor.fetchall()
                
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"사용자 세션 조회 오류: {str(e)}")
            return []
    
    def update_session_status(self, session_id: str, is_auto_trading_enabled: bool, current_symbol: str = None) -> bool:
        """세션 상태 업데이트"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                if current_symbol:
                    cursor.execute('''
                        UPDATE user_sessions SET
                            is_auto_trading_enabled = ?, current_symbol = ?, last_activity = ?
                        WHERE session_id = ?
                    ''', (is_auto_trading_enabled, current_symbol, datetime.now(), session_id))
                else:
                    cursor.execute('''
                        UPDATE user_sessions SET
                            is_auto_trading_enabled = ?, last_activity = ?
                        WHERE session_id = ?
                    ''', (is_auto_trading_enabled, datetime.now(), session_id))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"세션 상태 업데이트 오류: {str(e)}")
            return False
    
    def delete_session(self, session_id: str) -> bool:
        """세션 삭제"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM user_sessions WHERE session_id = ?", (session_id,))
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"세션 삭제 오류: {str(e)}")
            return False
    
    def get_active_sessions(self) -> List[Dict[str, Any]]:
        """활성 자동매매 세션 조회"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM user_sessions WHERE is_auto_trading_enabled = TRUE"
                )
                rows = cursor.fetchall()
                
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"활성 세션 조회 오류: {str(e)}")
            return []

# 전역 서비스 인스턴스
sqlite_session_service = SQLiteSessionService()
