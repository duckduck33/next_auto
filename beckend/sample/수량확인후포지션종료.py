import time
import requests
import hmac
import os
import json
from hashlib import sha256
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

APIURL = "https://open-api-vst.bingx.com"  # 데모 거래소
APIKEY = os.getenv("BINGX_API_KEY")
SECRETKEY = os.getenv("BINGX_SECRET_KEY")

def get_positions(symbol):
    """현재 포지션 조회"""
    path = '/openApi/swap/v2/user/positions'
    method = "GET"
    paramsMap = {"symbol": symbol}
    paramsStr = parseParam(paramsMap)
    result = send_request(method, path, paramsStr, {})
    return json.loads(result)

def close_all_positions(symbol):
    """해당 심볼의 모든 포지션 자동 종료"""
    print(f"=== {symbol} 모든 포지션 자동 종료 시작 ===")
    
    # 1. 현재 포지션 조회
    positions_result = get_positions(symbol)
    print(f"포지션 조회 결과: {json.dumps(positions_result, indent=2)}")
    
    if positions_result.get('code') != 0:
        print("포지션 조회 실패:", positions_result.get('msg'))
        return
    
    positions = positions_result.get('data', [])
    
    if not positions:
        print(f"{symbol}에 열린 포지션이 없습니다.")
        return
    
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
        close_result = execute_close_order(symbol, position_side, abs(position_amt))
        print(f"{position_side} 포지션 종료 결과: {close_result}")

def execute_close_order(symbol, position_side, quantity):
    """특정 포지션 종료 주문 실행"""
    payload = {}
    path = '/openApi/swap/v2/trade/order'
    method = "POST"
    
    # 포지션 방향에 따른 종료 주문 방향 결정
    if position_side == "LONG":
        close_side = "SELL"  # 롱 포지션은 매도로 종료
    elif position_side == "SHORT":
        close_side = "BUY"   # 숏 포지션은 매수로 종료
    else:
        print(f"알 수 없는 포지션 방향: {position_side}")
        return None
    
    # 종료 주문 파라미터
    paramsMap = {
        "symbol": symbol,
        "side": close_side,
        "positionSide": position_side,
        "type": "MARKET",
        "quantity": str(quantity)
    }
    
    print(f"종료 주문 파라미터: {paramsMap}")
    
    paramsStr = parseParam(paramsMap)
    result = send_request(method, path, paramsStr, payload)
    
    return result

def close_specific_position(symbol, target_side):
    """특정 방향의 포지션만 종료"""
    print(f"=== {symbol} {target_side} 포지션 종료 시작 ===")
    
    # 1. 현재 포지션 조회
    positions_result = get_positions(symbol)
    print(f"포지션 조회 결과: {json.dumps(positions_result, indent=2)}")
    
    if positions_result.get('code') != 0:
        print("포지션 조회 실패:", positions_result.get('msg'))
        return
    
    # 2. 해당 방향의 포지션 찾기
    target_position = None
    positions = positions_result.get('data', [])
    
    for position in positions:
        if position.get('symbol') == symbol and position.get('positionSide') == target_side:
            target_position = position
            break
    
    if not target_position:
        print(f"{symbol} {target_side} 포지션을 찾을 수 없습니다.")
        return
    
    # 3. 포지션 수량 확인
    position_amt = float(target_position.get('positionAmt', 0))
    if position_amt == 0:
        print(f"{symbol} {target_side} 포지션 수량이 0입니다.")
        return
    
    print(f"현재 {target_side} 포지션 수량: {position_amt}")
    
    # 4. 포지션 종료 주문 실행
    result = execute_close_order(symbol, target_side, abs(position_amt))
    print(f"포지션 종료 결과: {result}")
    return result

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature

def send_request(method, path, urlpa, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlpa, get_sign(SECRETKEY, urlpa))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap):
    sortedKeys = sorted(paramsMap)
    paramsStr = "&".join(["%s=%s" % (x, paramsMap[x]) for x in sortedKeys])
    if paramsStr != "": 
        return paramsStr+"&timestamp="+str(int(time.time() * 1000))
    else:
        return paramsStr+"timestamp="+str(int(time.time() * 1000))

if __name__ == '__main__':
    symbol = "XRP-USDT"
    
    # 사용법 1: 모든 포지션 자동 종료
    close_all_positions(symbol)
    
    # 사용법 2: 특정 방향 포지션만 종료
    # close_specific_position(symbol, "LONG")   # 롱 포지션만 종료
    # close_specific_position(symbol, "SHORT")  # 숏 포지션만 종료