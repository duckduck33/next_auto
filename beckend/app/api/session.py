from fastapi import APIRouter, HTTPException, Request
from typing import Dict, Any
import json
import logging
from app.models.user_session import session_manager
from app.services.database_service import database_service
from app.models.database_models import UserSessionDB
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/create-session")
async def create_session(request: Request) -> Dict[str, Any]:
    """새로운 사용자 세션을 생성합니다."""
    try:
        body = await request.body()
        data = json.loads(body.decode('utf-8'))
        
        # 필수 필드 검증
        required_fields = ['apiKey', 'secretKey', 'exchangeType', 'investment', 
                         'leverage', 'takeProfit', 'stopLoss', 'indicator']
        for field in required_fields:
            if field not in data:
                raise HTTPException(status_code=400, detail=f"필수 필드가 누락되었습니다: {field}")
        
        # 세션 생성
        session_id = session_manager.create_session(
            api_key=data['apiKey'],
            secret_key=data['secretKey'],
            exchange_type=data['exchangeType'],
            investment=float(data['investment']),
            leverage=int(data['leverage']),
            take_profit=float(data['takeProfit']),
            stop_loss=float(data['stopLoss']),
            indicator=data['indicator']
        )
        
        # 데이터베이스에 세션 저장
        session_data = UserSessionDB(
            session_id=session_id,
            api_key=data['apiKey'],
            secret_key=data['secretKey'],
            exchange_type=data['exchangeType'],
            investment=float(data['investment']),
            leverage=int(data['leverage']),
            take_profit=float(data['takeProfit']),
            stop_loss=float(data['stopLoss']),
            indicator=data['indicator'],
            is_auto_trading_enabled=False,
            current_symbol=None,
            created_at=datetime.now(),
            last_activity=datetime.now()
        )
        
        await database_service.save_user_session(session_data)
        
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
        # 메모리에서 세션 조회
        session = session_manager.get_session(session_id)
        if not session:
            # 데이터베이스에서 세션 조회
            db_session = await database_service.get_user_session(session_id)
            if not db_session:
                raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
            
            # 메모리에 세션 복원
            session = session_manager.create_session(
                api_key=db_session.api_key,
                secret_key=db_session.secret_key,
                exchange_type=db_session.exchange_type,
                investment=db_session.investment,
                leverage=db_session.leverage,
                take_profit=db_session.take_profit,
                stop_loss=db_session.stop_loss,
                indicator=db_session.indicator
            )
        
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
        
        # 세션 존재 확인
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
        
        # 업데이트할 필드들
        update_fields = {}
        if 'is_auto_trading_enabled' in data:
            update_fields['is_auto_trading_enabled'] = data['is_auto_trading_enabled']
        if 'current_symbol' in data:
            update_fields['current_symbol'] = data['current_symbol']
        
        # 메모리에서 세션 업데이트
        session_manager.update_session(session_id, **update_fields)
        
        # 데이터베이스에서 세션 업데이트
        db_session = await database_service.get_user_session(session_id)
        if db_session:
            for key, value in update_fields.items():
                setattr(db_session, key, value)
            db_session.last_activity = datetime.now()
            await database_service.save_user_session(db_session)
        
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
        # 메모리에서 세션 삭제
        session_manager.delete_session(session_id)
        
        # TODO: 데이터베이스에서도 세션 삭제 (필요시)
        
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
        sessions = []
        for session_id, session in session_manager.sessions.items():
            sessions.append({
                "session_id": session_id,
                "exchange_type": session.exchange_type,
                "indicator": session.indicator,
                "is_auto_trading_enabled": session.is_auto_trading_enabled,
                "current_symbol": session.current_symbol,
                "last_activity": session.last_activity.isoformat()
            })
        
        return {
            "success": True,
            "sessions": sessions,
            "total_count": len(sessions)
        }
        
    except Exception as e:
        logger.error(f"세션 목록 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"세션 목록 조회 중 오류 발생: {str(e)}")
