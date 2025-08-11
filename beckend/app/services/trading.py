from typing import Dict, Optional
import json

from app.services.bingx import bingx_client
from fastapi import HTTPException

class TradingService:
    def __init__(self):
        self.client = bingx_client

    async def get_current_price(self, symbol: str) -> float:
        """현재가 조회"""
        try:
            ticker = await self.client.get_ticker(symbol)
            print(f"현재가 응답: {ticker}")
            return float(ticker['data']['price'])
        except Exception as e:
            print(f"현재가 조회 실패: {e}")
            raise

    async def execute_trade(
        self,
        symbol: str,
        side: Optional[str] = None,
        quantity: Optional[float] = None,
        leverage: int = 20,
        take_profit_percentage: Optional[float] = None,
        stop_loss_percentage: Optional[float] = None,
        is_close: bool = False
    ) -> Dict:
        """
        트레이딩뷰 신호에 따라 거래를 실행합니다.
        """
        try:
            if is_close:
                # 포지션 종료 - 테스트 파일의 close_all_positions 로직
                return await self._close_all_positions(symbol)
            else:
                # 포지션 진입
                if not side or quantity is None:
                    raise Exception("포지션 진입시 side와 quantity는 필수입니다.")
                return await self._open_position(
                    symbol, side, quantity, leverage, 
                    take_profit_percentage, stop_loss_percentage
                )

        except Exception as e:
            raise Exception(f"Trading execution failed: {str(e)}")

    async def _close_all_positions(self, symbol: str) -> Dict:
        """해당 심볼의 모든 포지션 자동 종료 (테스트 파일과 동일한 로직)"""
        print(f"=== {symbol} 모든 포지션 자동 종료 시작 ===")
        
        # 1. 현재 포지션 조회
        positions_result = await self.client.get_positions(symbol)
        print(f"포지션 조회 결과: {positions_result}")
        
        if positions_result.get('code') != 0:
            raise Exception(f"포지션 조회 실패: {positions_result.get('msg')}")
        
        positions = positions_result.get('data', [])
        
        if not positions:
            raise Exception(f"{symbol}에 열린 포지션이 없습니다.")
        
        close_results = []
        
        # 2. 각 포지션별로 종료 처리
        for position in positions:
            position_side = position.get('positionSide')  # LONG 또는 SHORT
            position_amt = float(position.get('positionAmt', 0))  # 포지션 수량
            entry_price = position.get('entryPrice', '0')
            unrealized_profit = position.get('unrealizedProfit', '0')
            
            print(f"\n--- 포지션 정보 ---")
            print(f"방향: {position_side}")
            print(f"수량: {position_amt}")
            print(f"진입가: {entry_price}")
            print(f"미실현손익: {unrealized_profit}")
            
            # 포지션 수량이 0이면 건너뛰기
            if position_amt == 0:
                print(f"{position_side} 포지션 수량이 0입니다. 건너뛰기.")
                continue
            
            # 3. 포지션 종료 주문 실행
            try:
                close_result = await self._execute_close_order(symbol, position_side, abs(position_amt))
                close_results.append({
                    "position_side": position_side,
                    "quantity": abs(position_amt),
                    "result": close_result
                })
                print(f"{position_side} 포지션 종료 성공")
            except Exception as e:
                print(f"{position_side} 포지션 종료 실패: {e}")
                close_results.append({
                    "position_side": position_side,
                    "quantity": abs(position_amt),
                    "error": str(e)
                })
        
        return {
            "message": f"{symbol} 포지션 종료 완료",
            "closed_positions": close_results
        }

    async def _execute_close_order(self, symbol: str, position_side: str, quantity: float) -> Dict:
        """특정 포지션 종료 주문 실행 (테스트 파일과 동일한 로직)"""
        # 포지션 방향에 따른 종료 주문 방향 결정
        if position_side == "LONG":
            close_side = "SELL"  # 롱 포지션은 매도로 종료
        elif position_side == "SHORT":
            close_side = "BUY"   # 숏 포지션은 매수로 종료
        else:
            raise Exception(f"알 수 없는 포지션 방향: {position_side}")
        
        # 종료 주문 파라미터
        params = {
            "symbol": symbol,
            "side": close_side,
            "positionSide": position_side,
            "type": "MARKET",
            "quantity": str(quantity)
        }
        
        print(f"종료 주문 파라미터: {params}")
        
        # 주문 실행
        order_result = await self.client.place_order(**params)
        return order_result

    async def _open_position(
        self, 
        symbol: str, 
        side: str, 
        quantity: float, 
        leverage: int,
        take_profit_percentage: Optional[float] = None,
        stop_loss_percentage: Optional[float] = None
    ) -> Dict:
        """포지션 진입 처리"""
        # 1. 레버리지 설정
        await self.client.set_leverage(symbol, leverage, side)

        # 2. 주문 방향 설정
        order_side = "BUY" if side == "LONG" else "SELL"

        # 3. 기본 주문 파라미터 설정
        params = {
            "symbol": symbol,
            "side": order_side,
            "positionSide": side,
            "type": "MARKET",
            "quantity": str(quantity)
        }

        # 4. 익절/손절 설정
        if take_profit_percentage or stop_loss_percentage:
            current_price = await self.get_current_price(symbol)
            print(f"현재가: {current_price}")

            if take_profit_percentage:
                # LONG: 현재가 * (1 + tp%), SHORT: 현재가 * (1 - tp%)
                tp_multiplier = (1 + take_profit_percentage/100) if side == "LONG" else (1 - take_profit_percentage/100)
                tp_price = str(round(current_price * tp_multiplier, 4))
                print(f"익절가: {tp_price}")

                tp_params = {
                    "type": "TAKE_PROFIT_MARKET",
                    "stopPrice": float(tp_price),
                    "price": float(tp_price),
                    "workingType": "MARK_PRICE"
                }
                params["takeProfit"] = json.dumps(tp_params, separators=(',', ':'))

            if stop_loss_percentage:
                # LONG: 현재가 * (1 - sl%), SHORT: 현재가 * (1 + sl%)
                sl_multiplier = (1 - stop_loss_percentage/100) if side == "LONG" else (1 + stop_loss_percentage/100)
                sl_price = str(round(current_price * sl_multiplier, 4))
                print(f"손절가: {sl_price}")

                sl_params = {
                    "type": "STOP_MARKET",
                    "stopPrice": float(sl_price),
                    "price": float(sl_price),
                    "workingType": "MARK_PRICE"
                }
                params["stopLoss"] = json.dumps(sl_params, separators=(',', ':'))

        # 5. 주문 실행
        print(f"진입 주문 파라미터: {params}")
        order_result = await self.client.place_order(**params)
        return order_result

# 싱글톤 인스턴스 생성
trading_service = TradingService()