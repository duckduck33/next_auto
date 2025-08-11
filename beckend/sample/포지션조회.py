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
    """포지션 조회"""
    path = '/openApi/swap/v2/user/positions'
    method = "GET"
    paramsMap = {"symbol": symbol}
    paramsStr = parseParam(paramsMap)
    result = send_request(method, path, paramsStr, {})
    return json.loads(result)

def analyze_positions(symbol):
    """포지션 분석"""
    print(f"=== {symbol} 포지션 조회 및 분석 ===")
    
    # 포지션 조회
    positions_result = get_positions(symbol)
    print(f"전체 응답: {json.dumps(positions_result, indent=2)}")
    
    if positions_result.get('code') != 0:
        print("포지션 조회 실패:", positions_result.get('msg'))
        return
    
    positions = positions_result.get('data', [])
    
    if not positions:
        print("포지션이 없습니다.")
        return
    
    print("\n=== 포지션 상세 정보 ===")
    for position in positions:
        symbol_name = position.get('symbol', 'N/A')
        position_side = position.get('positionSide', 'N/A')  # LONG 또는 SHORT
        position_amt = position.get('positionAmt', '0')      # 포지션 수량
        unrealized_profit = position.get('unrealizedProfit', '0')  # 미실현 손익
        mark_price = position.get('markPrice', '0')          # 마크 가격 (현재가)
        
        # 진입 가격: entryPrice 또는 avgPrice 사용
        entry_price = position.get('entryPrice') or position.get('avgPrice', '0')
        
        leverage = position.get('leverage', '0')             # 레버리지
        
        print(f"심볼: {symbol_name}")
        print(f"포지션 방향: {position_side}")
        print(f"포지션 수량: {position_amt}")
        print(f"진입 가격: {entry_price} (avgPrice 사용)")
        print(f"현재 가격: {mark_price}")
        print(f"레버리지: {leverage}")
        print(f"미실현 손익: {unrealized_profit}")
        
        # 사용 가능한 모든 가격 필드 출력 (디버깅용)
        print(f"--- 가격 필드 디버깅 ---")
        print(f"entryPrice: {position.get('entryPrice', 'N/A')}")
        print(f"avgPrice: {position.get('avgPrice', 'N/A')}")
        print(f"markPrice: {position.get('markPrice', 'N/A')}")
        print(f"liquidationPrice: {position.get('liquidationPrice', 'N/A')}")
        print("-" * 50)

def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    return signature

def send_request(method, path, urlpa, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlpa, get_sign(SECRETKEY, urlpa))
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
    # XRP-USDT 포지션 조회
    symbol = "XRP-USDT"
    analyze_positions(symbol)