from fastapi import APIRouter, HTTPException, Request
from typing import Dict, Any
import json
import logging
from app.services.bingx import bingx_client
from app.services.trading import TradingService
from app.services.sqlite_session_service import sqlite_session_service

logger = logging.getLogger(__name__)
router = APIRouter()

# 거래 서비스 인스턴스
trading_service = TradingService()

@router.post("/test-long-position")
async def test_long_position(request: Request) -> Dict[str, Any]:
    """테스트용 리플 롱 포지션 진입"""
    try:
        body = await request.body()
        data = json.loads(body.decode('utf-8')) if body else {}
        
        session_id = data.get('session_id')
        if not session_id:
            raise HTTPException(status_code=400, detail="세션 ID가 필요합니다.")
        
        # SQLite에서 세션 정보 가져오기
        db_session = sqlite_session_service.get_session(session_id)
        if not db_session:
            raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
        
        # 세션 설정으로 API 키 설정
        bingx_client.set_credentials(
            api_key=db_session['api_key'],
            secret_key=db_session['secret_key'],
            exchange_type=db_session['exchange_type']
        )
        
        # 테스트용 리플 롱 포지션 진입
        symbol = "XRP-USDT"
        investment_amount = float(db_session['investment'])
        leverage = int(db_session['leverage'])
        take_profit = float(db_session['take_profit'])
        stop_loss = float(db_session['stop_loss'])
        
        logger.info(f"🧪 테스트 롱 포지션 진입 시도: {symbol}")
        logger.info(f"💰 투자금액: {investment_amount}, 레버리지: {leverage}")
        logger.info(f"📈 익절: {take_profit}%, 손절: {stop_loss}%")
        
        # 롱 포지션 진입
        result = await trading_service.execute_trade(
            symbol=symbol,
            side='LONG',
            quantity=investment_amount,
            leverage=leverage,
            take_profit_percentage=take_profit,
            stop_loss_percentage=stop_loss
        )
        
        if result.get('success', False):
            # SQLite에 현재 거래 심볼 업데이트
            sqlite_session_service.update_session_status(session_id, True, symbol)
            logger.info(f"✅ 테스트 롱 포지션 진입 성공: {symbol}")
        else:
            logger.error(f"❌ 테스트 롱 포지션 진입 실패: {result}")
        
        return {
            "success": True,
            "message": "테스트 롱 포지션 진입 완료",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"테스트 롱 포지션 진입 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"테스트 거래 중 오류 발생: {str(e)}")

@router.post("/emergency-close-all")
async def emergency_close_all_positions(request: Request) -> Dict[str, Any]:
    """모든 포지션 긴급 청산"""
    try:
        body = await request.body()
        data = json.loads(body.decode('utf-8')) if body else {}
        
        session_id = data.get('session_id')
        if not session_id:
            raise HTTPException(status_code=400, detail="세션 ID가 필요합니다.")
        
        # SQLite에서 세션 정보 가져오기
        db_session = sqlite_session_service.get_session(session_id)
        if not db_session:
            raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
        
        # 세션 설정으로 API 키 설정
        bingx_client.set_credentials(
            api_key=db_session['api_key'],
            secret_key=db_session['secret_key'],
            exchange_type=db_session['exchange_type']
        )
        
        logger.info(f"🚨 긴급 청산 시작: 세션 {session_id}")
        
        # 현재 활성 포지션 조회 (모든 심볼)
        positions = await bingx_client.get_positions()
        active_positions = []
        
        if positions.get('code') == 0:
            for position in positions.get('data', []):
                if float(position.get('positionAmt', 0)) != 0:
                    active_positions.append(position)
                    logger.info(f"활성 포지션 발견: {position.get('symbol')} - {position.get('positionSide')} - {position.get('positionAmt')}")
        else:
            logger.error(f"포지션 조회 실패: {positions.get('msg')}")
            raise HTTPException(status_code=500, detail=f"포지션 조회 실패: {positions.get('msg')}")
        
        if not active_positions:
            logger.info("⚠️ 활성 포지션이 없습니다.")
            return {
                "success": True,
                "message": "활성 포지션이 없습니다.",
                "closed_count": 0
            }
        
        # 모든 활성 포지션 종료
        closed_count = 0
        for position in active_positions:
            symbol = position.get('symbol')
            position_side = position.get('positionSide')
            
            logger.info(f"🔴 포지션 종료 시도: {symbol} ({position_side})")
            
            result = await trading_service.execute_trade(
                symbol=symbol,
                is_close=True
            )
            
            if result.get('success', False):
                closed_count += 1
                logger.info(f"✅ 포지션 종료 성공: {symbol}")
            else:
                logger.error(f"❌ 포지션 종료 실패: {symbol} - {result}")
        
        # SQLite에서 현재 거래 심볼 초기화
        sqlite_session_service.update_session_status(session_id, False, None)
        
        logger.info(f"🚨 긴급 청산 완료: {closed_count}개 포지션 종료")
        
        return {
            "success": True,
            "message": f"긴급 청산 완료: {closed_count}개 포지션 종료",
            "closed_count": closed_count,
            "total_positions": len(active_positions)
        }
        
    except Exception as e:
        logger.error(f"긴급 청산 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"긴급 청산 중 오류 발생: {str(e)}")

@router.get("/check-positions/{session_id}")
async def check_positions(session_id: str) -> Dict[str, Any]:
    """현재 포지션 상태 확인"""
    try:
        # SQLite에서 세션 정보 가져오기
        db_session = sqlite_session_service.get_session(session_id)
        if not db_session:
            raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
        
        # 세션 설정으로 API 키 설정
        bingx_client.set_credentials(
            api_key=db_session['api_key'],
            secret_key=db_session['secret_key'],
            exchange_type=db_session['exchange_type']
        )
        
        # 현재 포지션 조회 (모든 심볼)
        positions = await bingx_client.get_positions()
        
        if positions.get('code') != 0:
            return {
                "success": False,
                "message": f"포지션 조회 실패: {positions.get('msg')}",
                "positions": []
            }
        
        active_positions = []
        for position in positions.get('data', []):
            if float(position.get('positionAmt', 0)) != 0:
                active_positions.append({
                    "symbol": position.get('symbol'),
                    "side": position.get('positionSide'),
                    "size": position.get('positionAmt'),
                    "entry_price": position.get('entryPrice'),
                    "unrealized_pnl": position.get('unrealizedPnl'),
                    "leverage": position.get('leverage')
                })
        
        return {
            "success": True,
            "message": f"활성 포지션 {len(active_positions)}개 발견",
            "positions": active_positions,
            "count": len(active_positions)
        }
        
    except Exception as e:
        logger.error(f"포지션 확인 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"포지션 확인 중 오류 발생: {str(e)}")
