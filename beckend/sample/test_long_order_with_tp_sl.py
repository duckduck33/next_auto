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

def get_current_price(symbol):
    """현재가 조회"""
    path = '/openApi/swap/v2/quote/price'
    method = "GET"
    paramsMap = {"symbol": symbol}
    paramsStr = parseParam(paramsMap)
    result = send_request(method, path, paramsStr, {})
    price_data = json.loads(result)
    print(f"현재가 응답: {price_data}")  # 디버깅용
    return float(price_data['data']['price'])

def long_order_with_tp_sl():
    payload = {}
    path = '/openApi/swap/v2/trade/order'
    method = "POST"
    
    # 현재가 조회
    symbol = "XRP-USDT"
    current_price = get_current_price(symbol)
    print(f"현재가: {current_price}")
    
    take_profit_price = str(round(current_price * 1.02, 4))  # 2% 높게 익절
    stop_loss_price = str(round(current_price * 0.98, 4))    # 2% 낮게 손절
    print(f"익절가: {take_profit_price}")
    print(f"손절가: {stop_loss_price}")
    
    # 익절 설정
    tp_params = {
        "type": "TAKE_PROFIT_MARKET",
        "stopPrice": float(take_profit_price),
        "price": float(take_profit_price),
        "workingType": "MARK_PRICE"
    }
    
    # 손절 설정
    sl_params = {
        "type": "STOP_MARKET",
        "stopPrice": float(stop_loss_price),
        "price": float(stop_loss_price),
        "workingType": "MARK_PRICE"
    }
    
    # 시장가 롱 주문 파라미터
    paramsMap = {
        "symbol": symbol,
        "side": "BUY",          # BUY: 매수
        "positionSide": "LONG", # LONG: 롱
        "type": "MARKET",       # MARKET: 시장가
        "quantity": "10",       # 수량
        "takeProfit": json.dumps(tp_params),  # 익절 설정
        "stopLoss": json.dumps(sl_params)     # 손절 설정
    }
    
    paramsStr = parseParam(paramsMap)
    return send_request(method, path, paramsStr, payload)

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
    print("롱 포지션 주문 (익절/손절 포함):", long_order_with_tp_sl())