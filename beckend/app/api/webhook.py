import json
import logging
import os
from typing import Any
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from app.services.bingx import BingXClient
from app.services.trading import TradingService
from app.api.profit import set_credentials
from app.services.sqlite_session_service import sqlite_session_service

# 하드코딩된 심볼을 상수로 통합관리
HARDCODED_SYMBOL = "XRP-USDT"

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
        
        # 세션 ID 추출 (웹훅에서 session_id를 포함하도록 수정 필요)
        session_id = data.get('session_id')
        if not session_id:
            logger.error("❌ 세션 ID가 없습니다.")
            return {
                "success": False,
                "message": "세션 ID가 필요합니다.",
                "data": None
            }
        
        # SQLite에서 세션 설정 가져오기
        db_session = sqlite_session_service.get_session(session_id)
        if not db_session:
            logger.error(f"❌ 세션 {session_id}를 찾을 수 없습니다.")
            return {
                "success": False,
                "message": "세션을 찾을 수 없습니다.",
                "data": None
            }
        
        user_settings = {
            'apiKey': db_session['api_key'],
            'secretKey': db_session['secret_key'],
            'exchangeType': db_session['exchange_type'],
            'investment': db_session['investment'],
            'leverage': db_session['leverage'],
            'takeProfit': db_session['take_profit'],
            'stopLoss': db_session['stop_loss'],
            'indicator': db_session['indicator'],
            'isAutoTradingEnabled': db_session['is_auto_trading_enabled']
        }
        current_trading_symbol = db_session.get('current_symbol')
        
        # 자동매매가 비활성화된 경우 웹훅 무시
        if not user_settings.get('isAutoTradingEnabled', False):
            logger.info(f"❌ 세션 {session_id}의 자동매매가 비활성화되어 있어 웹훅을 무시합니다.")
            return {
                "success": True,
                "message": "자동매매가 비활성화되어 있습니다.",
                "data": None
            }
        
        # API 키가 설정되지 않은 경우 웹훅 무시
        if not user_settings.get('apiKey') or not user_settings.get('secretKey'):
            logger.info(f"❌ 세션 {session_id}의 API 키가 설정되지 않아 웹훅을 무시합니다.")
            return {
                "success": True,
                "message": "API 키가 설정되지 않았습니다.",
                "data": None
            }
        
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
        
        # SQLite에 현재 거래 심볼 업데이트
        sqlite_session_service.update_session_status(session_id, True, symbol)
        logger.info(f"🎯 세션 {session_id} 거래 심볼: {symbol}, 전략: {strategy}, 액션: {action}")
        
        # 사용자가 선택한 지표와 웹훅 전략이 일치하는지 확인
        selected_indicator = user_settings.get('indicator', 'PREMIUM')
        
        if strategy != selected_indicator:
            logger.info(f"⚠️ 세션 {session_id} 지표 불일치: 웹훅 전략({strategy}) != 선택된 지표({selected_indicator}) - 매매 무시")
            return {
                "success": True,
                "message": f"지표 불일치로 매매 무시: {strategy} != {selected_indicator}",
                "data": None
            }
        
        logger.info(f"✅ 세션 {session_id} 지표 일치: {strategy} == {selected_indicator} - 매매 실행")
        
        # BingX 클라이언트에 API 키 설정 (거래소 타입 포함)
        bingx_client.set_credentials(
            api_key=user_settings['apiKey'],
            secret_key=user_settings['secretKey'],
            exchange_type=user_settings.get('exchangeType', 'demo')
        )
        
        # 수익률 API에도 API 키 설정
        set_credentials(
            api_key=user_settings['apiKey'],
            secret_key=user_settings['secretKey']
        )
        
        if action == 'CLOSE':
            logger.info("🔴 포지션 종료 시도")
            
            # 먼저 포지션 존재 여부 확인
            positions = await bingx_client.get_positions(symbol)
            active_positions = [p for p in positions['data'] if float(p.get('positionAmt', 0)) != 0]
            
            if not active_positions:
                logger.info("⚠️ 현재 활성화된 포지션이 없습니다.")
                return {
                    "success": True,
                    "message": "현재 활성화된 포지션이 없습니다.",
                    "data": None
                }
            
            # 포지션이 있는 경우에만 종료 시도
            result = await trading_service.execute_trade(
                symbol=symbol,
                is_close=True
            )
            logger.info(f"🔴 포지션 종료 결과: {result}")
        else:
            # 현재가 조회
            price_info = await bingx_client.get_ticker(symbol)
            current_price = float(price_info['data']['price'])
            logger.info(f"💰 현재가 조회: {current_price}")
            
            # 기존 포지션 확인
            positions = await bingx_client.get_positions(symbol)
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
                logger.info(f"🔄 반대 포지션 발견: {opposite_position['positionSide']} -> {action} 신호로 인한 포지션 전환")
                
                # 사용자 설정값 사용 (반대 포지션 종료용)
                leverage = int(user_settings.get('leverage', 5))
                
                # 기존 포지션 종료
                close_result = await trading_service.execute_trade(
                    symbol=symbol,
                    side='CLOSE',
                    quantity=0,
                    leverage=leverage,
                    take_profit_percentage=0,
                    stop_loss_percentage=0,
                    is_close=True
                )
                logger.info(f"🔄 기존 포지션 종료 결과: {close_result}")
                
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
            logger.info(f"📊 계산된 주문 수량: {quantity}")
            
            # 새 포지션 진입
            logger.info(f"🚀 새 포지션 진입 시도: {action} {symbol}")
            result = await trading_service.execute_trade(
                symbol=symbol,
                side=action,
                quantity=quantity,
                leverage=leverage,
                take_profit_percentage=float(user_settings.get('takeProfit', 1.0)),
                stop_loss_percentage=float(user_settings.get('stopLoss', 0.5)),
                is_close=False
            )
            logger.info(f"✅ 새 포지션 진입 결과: {result}")
        
        # 포지션 진입 성공 시 SQLite에 거래 심볼 업데이트
        if result.get('success', False):
            sqlite_session_service.update_session_status(session_id, True, symbol)
            logger.info(f"🎯 세션 {session_id} 현재 거래 심볼 업데이트: {symbol}")
        
        logger.info("=== 웹훅 신호 처리 완료 ===")
        return {
            "success": True,
            "message": "Order executed successfully",
            "data": result
        }
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON 파싱 오류: {str(e)}")
        logger.error(f"수신된 데이터: {body.decode('utf-8')}")
        raise HTTPException(
            status_code=400,
            detail="JSON 형식이 아닌 데이터가 수신되었습니다"
        )
        
    except ValueError as e:
        logger.error(f"값 오류: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
        
    except Exception as e:
        logger.error(f"예상치 못한 오류: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=400,
            detail=f"웹훅 처리 중 오류 발생: {str(e)}"
        )

@router.get("/current-symbol/{session_id}")
async def get_current_symbol(session_id: str) -> dict[str, str]:
    """세션별 현재 거래 중인 티커 정보 반환"""
    db_session = sqlite_session_service.get_session(session_id)
    symbol = db_session.get('current_symbol', "XRP-USDT") if db_session else "XRP-USDT"
    return {"symbol": symbol}

@router.get("/check-position")
async def check_position() -> dict[str, Any]:
    """현재 활성 포지션 확인"""
    global user_settings
    
    try:
        # API 키가 설정되지 않은 경우 오류 반환
        if not user_settings.get('apiKey') or not user_settings.get('secretKey'):
            return {
                "success": False,
                "hasPosition": False,
                "message": "API 키가 설정되지 않았습니다."
            }
        
        # 하드코딩된 심볼 사용
        symbol = HARDCODED_SYMBOL
        
        # BingX 클라이언트에 API 키 설정
        bingx_client.set_credentials(
            api_key=user_settings['apiKey'],
            secret_key=user_settings['secretKey']
        )
        
        # 수익률 API에도 API 키 설정
        set_credentials(
            api_key=user_settings['apiKey'],
            secret_key=user_settings['secretKey']
        )
        
        # 포지션 조회 (하드코딩된 심볼 사용)
        from app.api.profit import get_positions
        positions_result = get_positions(symbol)
        
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
        
        # 수익률 API에도 API 키 설정
        if session_settings[session_id].get('apiKey') and session_settings[session_id].get('secretKey'):
            set_credentials(
                api_key=session_settings[session_id]['apiKey'],
                secret_key=session_settings[session_id]['secretKey']
            )
        
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
        
        # 수익률 API에도 API 키 설정
        set_credentials(
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