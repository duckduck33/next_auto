from fastapi import APIRouter, HTTPException, Request
from typing import Dict, Any
import json
import logging
from app.models.user_session import session_manager
from app.services.sqlite_session_service import sqlite_session_service
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/create-or-update-session")
async def create_or_update_session(request: Request) -> Dict[str, Any]:
    """API 키 기준으로 세션을 생성하거나 업데이트합니다."""
    try:
        body = await request.body()
        data = json.loads(body.decode('utf-8'))
        
        # 필수 필드 검증
        required_fields = ['apiKey', 'secretKey', 'exchangeType', 'investment', 
                         'leverage', 'takeProfit', 'stopLoss', 'indicator']
        for field in required_fields:
            if field not in data or data[field] is None:
                raise HTTPException(status_code=400, detail=f"필수 필드가 누락되었습니다: {field}")
        
        # 안전한 숫자 변환 함수
        def safe_float(value, default=0.0):
            if value is None or value == '':
                return default
            try:
                return float(value)
            except (ValueError, TypeError):
                return default
        
        def safe_int(value, default=0):
            if value is None or value == '':
                return default
            try:
                return int(value)
            except (ValueError, TypeError):
                return default
        
        # 이메일 + 거래소 타입으로 세션 ID 생성
        user_email = data.get('userEmail', 'unknown')
        session_id = f"{user_email}_{data['exchangeType']}"
        existing_session = session_manager.get_session(session_id)
        
        is_new = False
        if existing_session:
            # 기존 세션 업데이트
            session_manager.update_session(
                session_id=session_id,
                secret_key=data['secretKey'],
                exchange_type=data['exchangeType'],
                investment=safe_float(data['investment']),
                leverage=safe_int(data['leverage']),
                take_profit=safe_float(data['takeProfit']),
                stop_loss=safe_float(data['stopLoss']),
                indicator=data['indicator']
            )
            logger.info(f"기존 세션 업데이트: {session_id}")
        else:
            # 새 세션 생성
            session_manager.create_session(
                api_key=data['apiKey'],
                secret_key=data['secretKey'],
                exchange_type=data['exchangeType'],
                investment=safe_float(data['investment']),
                leverage=safe_int(data['leverage']),
                take_profit=safe_float(data['takeProfit']),
                stop_loss=safe_float(data['stopLoss']),
                indicator=data['indicator']
            )
            is_new = True
            logger.info(f"새 세션 생성: {session_id}")
        
        # SQLite에 세션 저장
        session_data = {
            'session_id': session_id,
            'user_email': user_email,
            'api_key': data['apiKey'],
            'secret_key': data['secretKey'],
            'exchange_type': data['exchangeType'],
            'investment': safe_float(data['investment']),
            'leverage': safe_int(data['leverage']),
            'take_profit': safe_float(data['takeProfit']),
            'stop_loss': safe_float(data['stopLoss']),
            'indicator': data['indicator'],
            'is_auto_trading_enabled': data.get('isAutoTradingEnabled', False)
        }
        
        logger.info(f"자동매매 상태 업데이트: session_id={session_id}, is_auto_trading_enabled={data.get('isAutoTradingEnabled', False)}")
        
        if sqlite_session_service.save_session(session_data):
            logger.info(f"세션 정보를 SQLite에 저장: {session_id}")
        else:
            logger.error(f"세션 저장 실패: {session_id}")
            raise HTTPException(status_code=500, detail="세션 저장 중 오류가 발생했습니다.")
        
        return {
            "success": True,
            "session_id": session_id,
            "is_new": is_new,
            "message": "새 세션이 생성되었습니다." if is_new else "기존 세션이 업데이트되었습니다."
        }
        
    except Exception as e:
        logger.error(f"세션 생성/업데이트 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"세션 생성/업데이트 중 오류 발생: {str(e)}")

@router.post("/create-session")
async def create_session(request: Request) -> Dict[str, Any]:
    """새로운 사용자 세션을 생성합니다. (기존 호환성 유지)"""
    try:
        body = await request.body()
        data = json.loads(body.decode('utf-8'))
        
        # 필수 필드 검증
        required_fields = ['apiKey', 'secretKey', 'exchangeType', 'investment', 
                         'leverage', 'takeProfit', 'stopLoss', 'indicator']
        for field in required_fields:
            if field not in data or data[field] is None:
                raise HTTPException(status_code=400, detail=f"필수 필드가 누락되었습니다: {field}")
        
        # 안전한 숫자 변환 함수
        def safe_float(value, default=0.0):
            if value is None or value == '':
                return default
            try:
                return float(value)
            except (ValueError, TypeError):
                return default
        
        def safe_int(value, default=0):
            if value is None or value == '':
                return default
            try:
                return int(value)
            except (ValueError, TypeError):
                return default
        
        # 세션 생성
        session_id = session_manager.create_session(
            api_key=data['apiKey'],
            secret_key=data['secretKey'],
            exchange_type=data['exchangeType'],
            investment=safe_float(data['investment']),
            leverage=safe_int(data['leverage']),
            take_profit=safe_float(data['takeProfit']),
            stop_loss=safe_float(data['stopLoss']),
            indicator=data['indicator']
        )
        
        # SQLite에 세션 저장
        session_data = {
            'session_id': session_id,
            'user_email': data.get('userEmail', 'unknown'),
            'api_key': data['apiKey'],
            'secret_key': data['secretKey'],
            'exchange_type': data['exchangeType'],
            'investment': safe_float(data['investment']),
            'leverage': safe_int(data['leverage']),
            'take_profit': safe_float(data['takeProfit']),
            'stop_loss': safe_float(data['stopLoss']),
            'indicator': data['indicator'],
            'is_auto_trading_enabled': False
        }
        
        if sqlite_session_service.save_session(session_data):
            logger.info(f"세션 정보를 SQLite에 저장: {session_id}")
        else:
            logger.error(f"세션 저장 실패: {session_id}")
            raise HTTPException(status_code=500, detail="세션 저장 중 오류가 발생했습니다.")
        
        logger.info(f"새 세션 생성: {session_id}")
        
        return {
            "success": True,
            "session_id": session_id,
            "message": "세션이 성공적으로 생성되었습니다."
        }
        
    except Exception as e:
        logger.error(f"세션 생성 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"세션 생성 중 오류 발생: {str(e)}")

@router.get("/session/{session_id}")
async def get_session(session_id: str) -> Dict[str, Any]:
    """세션 정보를 조회합니다."""
    try:
        # SQLite에서 세션 조회
        db_session = sqlite_session_service.get_session(session_id)
        if not db_session:
            raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
        
        # 세션 정보 반환
        session = {
            "session_id": db_session['session_id'],
            "exchange_type": db_session['exchange_type'],
            "investment": db_session['investment'],
            "leverage": db_session['leverage'],
            "take_profit": db_session['take_profit'],
            "stop_loss": db_session['stop_loss'],
            "indicator": db_session['indicator'],
            "is_auto_trading_enabled": db_session['is_auto_trading_enabled'],
            "current_symbol": db_session['current_symbol'],
            "created_at": db_session['created_at'],
            "last_activity": db_session['last_activity']
        }
        
        return {
            "success": True,
            "session": {
                "session_id": session.session_id,
                "exchange_type": session.exchange_type,
                "investment": session.investment,
                "leverage": session.leverage,
                "take_profit": session.take_profit,
                "stop_loss": session.stop_loss,
                "indicator": session.indicator,
                "is_auto_trading_enabled": session.is_auto_trading_enabled,
                "current_symbol": session.current_symbol,
                "created_at": session.created_at.isoformat(),
                "last_activity": session.last_activity.isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"세션 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"세션 조회 중 오류 발생: {str(e)}")

@router.put("/session/{session_id}")
async def update_session(session_id: str, request: Request) -> Dict[str, Any]:
    """세션 정보를 업데이트합니다."""
    try:
        body = await request.body()
        data = json.loads(body.decode('utf-8'))
        
        # SQLite에서 세션 존재 확인
        db_session = sqlite_session_service.get_session(session_id)
        if not db_session:
            raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
        
        # 업데이트할 필드들
        update_fields = {}
        if 'is_auto_trading_enabled' in data:
            update_fields['is_auto_trading_enabled'] = data['is_auto_trading_enabled']
        if 'current_symbol' in data:
            update_fields['current_symbol'] = data['current_symbol']
        
        # SQLite에서 세션 업데이트
        if update_fields:
            sqlite_session_service.update_session_status(
                session_id, 
                update_fields.get('is_auto_trading_enabled', db_session['is_auto_trading_enabled']),
                update_fields.get('current_symbol', db_session.get('current_symbol'))
            )
        
        return {
            "success": True,
            "message": "세션이 성공적으로 업데이트되었습니다."
        }
        
    except Exception as e:
        logger.error(f"세션 업데이트 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"세션 업데이트 중 오류 발생: {str(e)}")

@router.delete("/session/{session_id}")
async def delete_session(session_id: str) -> Dict[str, Any]:
    """세션을 삭제합니다."""
    try:
        # SQLite에서 세션 삭제
        if sqlite_session_service.delete_session(session_id):
            logger.info(f"세션 삭제 성공: {session_id}")
        else:
            logger.warning(f"세션 삭제 실패: {session_id}")
        
        return {
            "success": True,
            "message": "세션이 성공적으로 삭제되었습니다."
        }
        
    except Exception as e:
        logger.error(f"세션 삭제 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"세션 삭제 중 오류 발생: {str(e)}")

@router.get("/sessions")
async def list_sessions() -> Dict[str, Any]:
    """모든 활성 세션을 조회합니다."""
    try:
        # SQLite에서 모든 활성 세션 조회
        active_sessions = sqlite_session_service.get_active_sessions()
        
        sessions = []
        for session in active_sessions:
            sessions.append({
                "session_id": session['session_id'],
                "exchange_type": session['exchange_type'],
                "indicator": session['indicator'],
                "is_auto_trading_enabled": session['is_auto_trading_enabled'],
                "current_symbol": session['current_symbol'],
                "last_activity": session['last_activity']
            })
        
        return {
            "success": True,
            "sessions": sessions,
            "total_count": len(sessions)
        }
        
    except Exception as e:
        logger.error(f"세션 목록 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"세션 목록 조회 중 오류 발생: {str(e)}")
