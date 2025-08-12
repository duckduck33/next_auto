import sqlite3
import os
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

class SQLiteDatabase:
    def __init__(self, db_path: str = "sessions.db"):
        """SQLite 데이터베이스 초기화"""
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """데이터베이스 연결 반환"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row  # 딕셔너리 형태로 결과 반환
        return conn
    
    def init_database(self):
        """데이터베이스 및 테이블 초기화"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 사용자 세션 테이블 생성
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_sessions (
                        session_id TEXT PRIMARY KEY,
                        user_email TEXT NOT NULL,
                        api_key TEXT NOT NULL,
                        secret_key TEXT NOT NULL,
                        exchange_type TEXT NOT NULL,
                        investment REAL DEFAULT 1000,
                        leverage INTEGER DEFAULT 10,
                        take_profit REAL DEFAULT 2,
                        stop_loss REAL DEFAULT 2,
                        indicator TEXT DEFAULT 'PREMIUM',
                        is_auto_trading_enabled BOOLEAN DEFAULT FALSE,
                        current_symbol TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 사용자 계정 테이블 생성
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        email TEXT PRIMARY KEY,
                        password TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 인덱스 생성
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_email ON user_sessions(user_email)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_exchange_type ON user_sessions(exchange_type)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_auto_trading ON user_sessions(is_auto_trading_enabled)')
                
                conn.commit()
                logger.info("SQLite 데이터베이스 초기화 완료")
                
        except Exception as e:
            logger.error(f"데이터베이스 초기화 오류: {str(e)}")
            raise

# 전역 데이터베이스 인스턴스
sqlite_db = SQLiteDatabase()
