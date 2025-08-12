import sqlite3
import logging
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any
from app.core.sqlite_database import sqlite_db

logger = logging.getLogger(__name__)

class UserAuthService:
    def __init__(self):
        self.db = sqlite_db
    
    def _hash_password(self, password: str) -> str:
        """비밀번호 해시화"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def register_user(self, email: str, password: str) -> bool:
        """사용자 등록"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # 이메일 중복 확인
                cursor.execute("SELECT email FROM users WHERE email = ?", (email,))
                if cursor.fetchone():
                    logger.warning(f"이미 존재하는 이메일: {email}")
                    return False
                
                # 비밀번호 해시화
                hashed_password = self._hash_password(password)
                
                # 사용자 등록
                cursor.execute('''
                    INSERT INTO users (email, password, created_at, last_login)
                    VALUES (?, ?, ?, ?)
                ''', (email, hashed_password, datetime.now(), datetime.now()))
                
                conn.commit()
                logger.info(f"새 사용자 등록: {email}")
                return True
                
        except Exception as e:
            logger.error(f"사용자 등록 오류: {str(e)}")
            return False
    
    def authenticate_user(self, email: str, password: str) -> bool:
        """사용자 인증"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # 비밀번호 해시화
                hashed_password = self._hash_password(password)
                
                # 사용자 확인
                cursor.execute(
                    "SELECT email FROM users WHERE email = ? AND password = ?",
                    (email, hashed_password)
                )
                
                user = cursor.fetchone()
                if user:
                    # 마지막 로그인 시간 업데이트
                    cursor.execute(
                        "UPDATE users SET last_login = ? WHERE email = ?",
                        (datetime.now(), email)
                    )
                    conn.commit()
                    logger.info(f"사용자 로그인 성공: {email}")
                    return True
                
                logger.warning(f"로그인 실패: {email}")
                return False
                
        except Exception as e:
            logger.error(f"사용자 인증 오류: {str(e)}")
            return False
    
    def get_user_info(self, email: str) -> Optional[Dict[str, Any]]:
        """사용자 정보 조회"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT email, created_at, last_login FROM users WHERE email = ?",
                    (email,)
                )
                row = cursor.fetchone()
                
                if row:
                    return dict(row)
                return None
                
        except Exception as e:
            logger.error(f"사용자 정보 조회 오류: {str(e)}")
            return None
    
    def change_password(self, email: str, old_password: str, new_password: str) -> bool:
        """비밀번호 변경"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # 기존 비밀번호 확인
                old_hashed = self._hash_password(old_password)
                cursor.execute(
                    "SELECT email FROM users WHERE email = ? AND password = ?",
                    (email, old_hashed)
                )
                
                if not cursor.fetchone():
                    logger.warning(f"기존 비밀번호 불일치: {email}")
                    return False
                
                # 새 비밀번호로 업데이트
                new_hashed = self._hash_password(new_password)
                cursor.execute(
                    "UPDATE users SET password = ? WHERE email = ?",
                    (new_hashed, email)
                )
                
                conn.commit()
                logger.info(f"비밀번호 변경 성공: {email}")
                return True
                
        except Exception as e:
            logger.error(f"비밀번호 변경 오류: {str(e)}")
            return False
    
    def delete_user(self, email: str, password: str) -> bool:
        """사용자 삭제"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # 비밀번호 확인
                hashed_password = self._hash_password(password)
                cursor.execute(
                    "SELECT email FROM users WHERE email = ? AND password = ?",
                    (email, hashed_password)
                )
                
                if not cursor.fetchone():
                    logger.warning(f"비밀번호 불일치로 삭제 실패: {email}")
                    return False
                
                # 사용자 삭제 (세션도 함께 삭제)
                cursor.execute("DELETE FROM user_sessions WHERE user_email = ?", (email,))
                cursor.execute("DELETE FROM users WHERE email = ?", (email,))
                
                conn.commit()
                logger.info(f"사용자 삭제 성공: {email}")
                return True
                
        except Exception as e:
            logger.error(f"사용자 삭제 오류: {str(e)}")
            return False

# 전역 서비스 인스턴스
user_auth_service = UserAuthService()
