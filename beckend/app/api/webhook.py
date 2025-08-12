import json
import logging
import os
from typing import Any
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from app.services.bingx import BingXClient
from app.services.trading import TradingService

from app.services.sqlite_session_service import sqlite_session_service



# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# 전역 변수 (기본값)
bingx_client = BingXClient()
trading_service = TradingService()

# 세션별 설정을 저장할 딕셔너리
session_settings = {}
session_trading_symbols = {}

# 전역 사용자 설정 (기본값)
user_settings = {}

async def calculate_order_quantity(investment_amount: float, leverage: int, current_price: float) -> float:
    """투자금액과 레버리지를 기반으로 주문 수량 계산"""
    return (investment_amount * leverage) / current_price

async def execute_trade_for_session(session_id: str, symbol: str, action: str, user_settings: dict) -> dict:
    """세션별 매매 실행"""
    try:
        # 세션별 BingXClient 인스턴스 생성
        session_bingx_client = BingXClient()
        session_bingx_client.set_credentials(
            api_key=user_settings['apiKey'],
            secret_key=user_settings['secretKey'],
            exchange_type=user_settings.get('exchangeType', 'demo')
        )
        
        # 세션별 TradingService 인스턴스 생성
        session_trading_service = TradingService()
        
        if action == 'CLOSE':
            logger.info(f"🔴 세션 {session_id} 포지션 종료 시도")
            
            # 먼저 포지션 존재 여부 확인
            positions = await session_bingx_client.get_positions(symbol)
            active_positions = [p for p in positions['data'] if float(p.get('positionAmt', 0)) != 0]
            
            if not active_positions:
                logger.info(f"⚠️ 세션 {session_id}: 현재 활성화된 포지션이 없습니다.")
                return {
                    "success": True,
                    "message": "현재 활성화된 포지션이 없습니다."
                }
            
            # 포지션이 있는 경우에만 종료 시도
            result = await session_trading_service.execute_trade(
                symbol=symbol,
                is_close=True
            )
            logger.info(f"🔴 세션 {session_id} 포지션 종료 결과: {result}")
            return result
            
        else:
            # 현재가 조회
            price_info = await session_bingx_client.get_ticker(symbol)
            current_price = float(price_info['data']['price'])
            logger.info(f"💰 세션 {session_id} 현재가 조회: {current_price}")
            
            # 기존 포지션 확인
            positions = await session_bingx_client.get_positions(symbol)
            active_positions = [p for p in positions['data'] if float(p.get('positionAmt', 0)) != 0]
            
            # 반대 포지션이 있는지 확인
            opposite_position = None
            for position in active_positions:
                position_side = position.get('positionSide')
                if (action == 'LONG' and position_side == 'SHORT') or (action == 'SHORT' and position_side == 'LONG'):
                    opposite_position = position
                    break
            
            # 반대 포지션이 있으면 먼저 종료
            if opposite_position:
                logger.info(f"🔄 세션 {session_id} 반대 포지션 발견: {opposite_position['positionSide']} -> {action} 신호로 인한 포지션 전환")
                
                # 사용자 설정값 사용 (반대 포지션 종료용)
                leverage = int(user_settings.get('leverage', 5))
                
                # 기존 포지션 종료
                close_result = await session_trading_service.execute_trade(
                    symbol=symbol,
                    side='CLOSE',
                    quantity=0,
                    leverage=leverage,
                    take_profit_percentage=0,
                    stop_loss_percentage=0,
                    is_close=True
                )
                logger.info(f"🔄 세션 {session_id} 기존 포지션 종료 결과: {close_result}")
                
                # 잠시 대기 (주문 처리 시간)
                import asyncio
                await asyncio.sleep(1)
            
            # 사용자 설정값 사용
            investment_amount = float(user_settings.get('investment', 100))
            leverage = int(user_settings.get('leverage', 5))
            
            # 주문 수량 계산
            quantity = await calculate_order_quantity(
                investment_amount=investment_amount,
                leverage=leverage,
                current_price=current_price
            )
            logger.info(f"📊 세션 {session_id} 계산된 주문 수량: {quantity}")
            
            # 새 포지션 진입
            logger.info(f"🚀 세션 {session_id} 새 포지션 진입 시도: {action} {symbol}")
            result = await session_trading_service.execute_trade(
                symbol=symbol,
                side=action,
                quantity=quantity,
                leverage=leverage,
                take_profit_percentage=float(user_settings.get('takeProfit', 1.0)),
                stop_loss_percentage=float(user_settings.get('stopLoss', 0.5)),
                is_close=False
            )
            logger.info(f"✅ 세션 {session_id} 새 포지션 진입 결과: {result}")
            return result
            
    except Exception as e:
        logger.error(f"❌ 세션 {session_id} 매매 실행 중 오류: {str(e)}")
        return {
            "success": False,
            "message": f"매매 실행 중 오류: {str(e)}"
        }

@router.post("/webhook")
async def handle_webhook(request: Request) -> dict[str, Any]:
    """트레이딩뷰 웹훅을 처리하는 엔드포인트"""
    global session_settings, session_trading_symbols
    
    logger.info("=== 웹훅 신호 수신 시작 ===")
    
    try:
        # JSON 데이터 파싱
        body = await request.body()
        data = json.loads(body.decode('utf-8'))
        logger.info(f"📥 웹훅 신호 수신: {data}")
        
        # 액션 검증
        action = data.get('action')
        if action not in ['LONG', 'SHORT', 'CLOSE']:
            logger.error(f"❌ 잘못된 액션: {action}")
            raise ValueError(f"잘못된 액션입니다: {action}")
            
        # 웹훅에서 받은 티커와 전략 정보
        symbol = data.get('symbol', 'XRP-USDT')
        strategy = data.get('strategy', 'PREMIUM')
        
        # 심볼 변환 로직 추가
        if symbol.endswith('.P'):
            # XRPUSDT.P -> XRP-USDT 변환
            symbol = symbol.replace('.P', '').replace('USDT', '-USDT')
        
        logger.info(f"🎯 웹훅 신호: 심볼={symbol}, 전략={strategy}, 액션={action}")
        
        # 모든 활성 세션 조회
        active_sessions = sqlite_session_service.get_active_sessions()
        logger.info(f"📊 활성 세션 수: {len(active_sessions)}")
        
        if not active_sessions:
            logger.info("⚠️ 활성 세션이 없습니다.")
            return {
                "success": True,
                "message": "활성 세션이 없습니다.",
                "data": None
            }
        
        # 각 활성 세션에 대해 웹훅 신호 처리
        processed_sessions = []
        for session in active_sessions:
            session_id = session['session_id']
            
            try:
                # 세션별 설정
                user_settings = {
                    'apiKey': session['api_key'],
                    'secretKey': session['secret_key'],
                    'exchangeType': session['exchange_type'],
                    'investment': session['investment'],
                    'leverage': session['leverage'],
                    'takeProfit': session['take_profit'],
                    'stopLoss': session['stop_loss'],
                    'indicator': session['indicator'],
                    'isAutoTradingEnabled': session['is_auto_trading_enabled']
                }
                
                # API 키가 설정되지 않은 경우 스킵
                if not user_settings.get('apiKey') or not user_settings.get('secretKey'):
                    logger.info(f"⚠️ 세션 {session_id}: API 키가 설정되지 않음 - 스킵")
                    continue
                
                # 사용자가 선택한 지표와 웹훅 전략이 일치하는지 확인
                selected_indicator = user_settings.get('indicator', 'PREMIUM')
                
                if strategy != selected_indicator:
                    logger.info(f"⚠️ 세션 {session_id} 지표 불일치: 웹훅 전략({strategy}) != 선택된 지표({selected_indicator}) - 스킵")
                    continue
                
                logger.info(f"✅ 세션 {session_id} 지표 일치: {strategy} == {selected_indicator} - 매매 실행")
                
                # SQLite에 현재 거래 심볼 업데이트
                sqlite_session_service.update_session_status(session_id, True, symbol)
                

                
                # 매매 실행
                result = await execute_trade_for_session(session_id, symbol, action, user_settings)
                processed_sessions.append({
                    'session_id': session_id,
                    'result': result
                })
                
            except Exception as e:
                logger.error(f"❌ 세션 {session_id} 처리 중 오류: {str(e)}")
                processed_sessions.append({
                    'session_id': session_id,
                    'result': {'success': False, 'error': str(e)}
                })
        
        logger.info(f"📈 웹훅 처리 완료: {len(processed_sessions)}개 세션 처리됨")
        
        return {
            "success": True,
            "message": f"웹훅 신호가 {len(processed_sessions)}개 세션에서 처리되었습니다.",
            "data": {
                "symbol": symbol,
                "strategy": strategy,
                "action": action,
                "processed_sessions": processed_sessions
            }
        }
        
    except Exception as e:
        logger.error(f"웹훅 처리 중 오류: {str(e)}")
        return {
            "success": False,
            "message": f"웹훅 처리 중 오류 발생: {str(e)}",
            "data": None
        }

@router.get("/current-symbol/{session_id}")
async def get_current_symbol(session_id: str) -> dict[str, str]:
    """세션별 현재 거래 중인 티커 정보 반환"""
    db_session = sqlite_session_service.get_session(session_id)
    symbol = db_session.get('current_symbol', "XRP-USDT") if db_session else "XRP-USDT"
    return {"symbol": symbol}

@router.get("/check-position/{session_id}")
async def check_position(session_id: str) -> dict[str, Any]:
    """세션별 현재 활성 포지션 확인"""
    try:
        # 세션 정보 조회
        db_session = sqlite_session_service.get_session(session_id)
        if not db_session:
            return {
                "success": False,
                "hasPosition": False,
                "message": "세션을 찾을 수 없습니다."
            }
        
        # API 키가 설정되지 않은 경우 오류 반환
        if not db_session.get('api_key') or not db_session.get('secret_key'):
            return {
                "success": False,
                "hasPosition": False,
                "message": "API 키가 설정되지 않았습니다."
            }
        
        # 세션의 현재 거래 심볼 사용
        symbol = db_session.get('current_symbol', 'XRP-USDT')
        
        # 세션별 BingXClient 인스턴스 생성
        session_bingx_client = BingXClient()
        session_bingx_client.set_credentials(
            api_key=db_session['api_key'],
            secret_key=db_session['secret_key'],
            exchange_type=db_session.get('exchange_type', 'demo')
        )
        
        # 포지션 조회 (세션별 BingX 클라이언트 사용)
        positions_result = await session_bingx_client.get_positions(symbol)
        
        if positions_result.get('code') != 0:
            return {
                "success": False,
                "hasPosition": False,
                "message": f"포지션 조회 실패: {positions_result.get('msg')}"
            }
        
        positions = positions_result.get('data', [])
        active_positions = [p for p in positions if float(p.get('positionAmt', 0)) != 0]
        
        has_position = len(active_positions) > 0
        
        return {
            "success": True,
            "hasPosition": has_position,
            "symbol": symbol,
            "message": "활성 포지션이 있습니다." if has_position else "활성 포지션이 없습니다."
        }
        
    except Exception as e:
        logger.error(f"포지션 확인 중 오류: {str(e)}")
        return {
            "success": False,
            "hasPosition": False,
            "message": f"포지션 확인 중 오류 발생: {str(e)}"
        }

@router.post("/update-settings")
async def update_user_settings(request: Request) -> dict[str, Any]:
    """사용자 설정 업데이트 (세션별)"""
    global session_settings
    
    try:
        body = await request.body()
        data = json.loads(body.decode('utf-8'))
        
        # 세션 ID 추출 (기본값으로 첫 번째 세션 사용)
        session_id = data.get('session_id')
        if not session_id:
            # 세션이 없으면 새로 생성
            from app.models.user_session import session_manager
            session_id = session_manager.create_session(
                api_key=data.get('apiKey', ''),
                secret_key=data.get('secretKey', ''),
                exchange_type=data.get('exchangeType', 'demo'),
                investment=float(data.get('investment', 1000)),
                leverage=int(data.get('leverage', 10)),
                take_profit=float(data.get('takeProfit', 2)),
                stop_loss=float(data.get('stopLoss', 2)),
                indicator=data.get('indicator', 'PREMIUM')
            )
        
        # 세션별 설정 업데이트
        session_settings[session_id] = {
            'apiKey': data.get('apiKey', ''),
            'secretKey': data.get('secretKey', ''),
            'exchangeType': data.get('exchangeType', 'demo'),
            'investment': float(data.get('investment', 1000)),
            'leverage': int(data.get('leverage', 10)),
            'takeProfit': float(data.get('takeProfit', 2)),
            'stopLoss': float(data.get('stopLoss', 2)),
            'indicator': data.get('indicator', 'PREMIUM'),
            'isAutoTradingEnabled': data.get('isAutoTradingEnabled', False)
        }
        

        
        logger.info(f"세션 {session_id} 설정 업데이트: {session_settings[session_id]}")
        
        return {
            "success": True,
            "message": "설정이 업데이트되었습니다.",
            "session_id": session_id,
            "data": session_settings[session_id]
        }
        
    except Exception as e:
        logger.error(f"설정 업데이트 오류: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"설정 업데이트 중 오류 발생: {str(e)}"
        )

@router.get("/settings")
async def get_user_settings() -> dict[str, Any]:
    """현재 사용자 설정 조회"""
    global session_settings
    return {
        "success": True,
        "data": session_settings
    }

@router.post("/close-position")
async def close_position(request: Request) -> dict[str, Any]:
    """현재 활성 포지션 종료"""
    global current_trading_symbol, session_settings
    
    try:
        # 요청 본문에서 세션 ID와 심볼 정보 가져오기
        body = await request.body()
        data = json.loads(body.decode('utf-8')) if body else {}
        session_id = data.get('session_id')
        symbol = data.get('symbol', 'XRP-USDT')
        
        if not session_id:
            raise HTTPException(status_code=400, detail="세션 ID가 필요합니다.")
        
        # 세션별 설정 가져오기
        user_settings = session_settings.get(session_id, {})
        
        # API 키가 설정되지 않은 경우 오류 반환
        if not user_settings.get('apiKey') or not user_settings.get('secretKey'):
            raise HTTPException(status_code=400, detail="API 키가 설정되지 않았습니다.")
        
        # BingX 클라이언트에 API 키 설정
        bingx_client.set_credentials(
            api_key=user_settings['apiKey'],
            secret_key=user_settings['secretKey']
        )
        

        
        logger.info(f"포지션 종료 요청: {symbol}")
        
        # 포지션 종료 로직
        result = await trading_service.execute_trade(
            symbol=symbol,
            side='CLOSE',
            quantity=0,  # 종료 시에는 수량이 0
            leverage=int(user_settings.get('leverage', 10)),
            take_profit_percentage=0,
            stop_loss_percentage=0,
            is_close=True
        )
        
        logger.info(f"포지션 종료 결과: {result}")
        
        # 포지션 종료 후 현재 거래 심볼 초기화
        current_trading_symbol = None
        
        return {
            "success": True,
            "message": "포지션이 종료되었습니다.",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"포지션 종료 중 오류: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"포지션 종료 중 오류 발생: {str(e)}"
        )

@router.get("/calendar-data")
async def get_calendar_data() -> dict[str, Any]:
    """캘린더 데이터 조회"""
    try:
        # 간단한 파일 기반 저장 (실제로는 데이터베이스 사용 권장)
        import json
        import os
        
        calendar_file = "calendar_data.json"
        if os.path.exists(calendar_file):
            with open(calendar_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = {}
        
        return {
            "success": True,
            "data": data
        }
        
    except Exception as e:
        logger.error(f"캘린더 데이터 조회 중 오류: {str(e)}")
        return {
            "success": False,
            "message": f"캘린더 데이터 조회 중 오류: {str(e)}"
        }

@router.post("/calendar-data")
async def save_calendar_data(request: Request) -> dict[str, Any]:
    """캘린더 데이터 저장"""
    try:
        body = await request.body()
        data = json.loads(body.decode('utf-8'))
        
        # 간단한 파일 기반 저장 (실제로는 데이터베이스 사용 권장)
        import json
        import os
        
        calendar_file = "calendar_data.json"
        with open(calendar_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return {
            "success": True,
            "message": "캘린더 데이터가 저장되었습니다."
        }
        
    except Exception as e:
        logger.error(f"캘린더 데이터 저장 중 오류: {str(e)}")
        return {
            "success": False,
            "message": f"캘린더 데이터 저장 중 오류: {str(e)}"
        }