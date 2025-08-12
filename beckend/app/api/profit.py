from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import time
import requests
import hmac
import os
import json
from hashlib import sha256
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

APIURL = "https://open-api-vst.bingx.com"
# API 키는 동적으로 설정됨
APIKEY = ""
SECRETKEY = ""

router = APIRouter()

# 하드코딩된 심볼을 상수로 통합관리
HARDCODED_SYMBOL = "XRP-USDT"

# 전역 API 키 변수
global_api_key = ""
global_secret_key = ""

def set_credentials(api_key: str, secret_key: str):
    """API 키 설정"""
    global global_api_key, global_secret_key
    global_api_key = api_key
    global_secret_key = secret_key

class ProfitResponse(BaseModel):
    symbol: str
    position_side: str
    position_amt: float
    entry_price: float
    current_price: float
    base_profit_rate: float
    actual_profit_rate: float
    unrealized_profit: float
    leverage: int

def get_positions(symbol: str):
    """현재 포지션 조회"""
    path = '/openApi/swap/v2/user/positions'
    method = "GET"
    paramsMap = {"symbol": symbol}
    paramsStr = parseParam(paramsMap)
    result = send_request(method, path, paramsStr, {}, global_api_key, global_secret_key)
    return json.loads(result)

def get_current_price(symbol: str):
    """현재가 조회"""
    path = '/openApi/swap/v2/quote/price'
    method = "GET"
    paramsMap = {"symbol": symbol}
    paramsStr = parseParam(paramsMap)
    result = send_request(method, path, paramsStr, {}, global_api_key, global_secret_key)
    return json.loads(result)

def get_account_info():
    """계정 정보 조회"""
    path = '/openApi/swap/v2/user/account'
    method = "GET"
    paramsMap = {}
    paramsStr = parseParam(paramsMap)
    result = send_request(method, path, paramsStr, {}, global_api_key, global_secret_key)
    return json.loads(result)

def get_sign(api_secret: str, payload: str) -> str:
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    return signature

def send_request(method: str, path: str, urlpa: str, payload: dict, api_key: str = "", secret_key: str = "") -> str:
    # API 키가 설정되지 않은 경우 기본값 사용
    if not api_key:
        api_key = APIKEY
    if not secret_key:
        secret_key = SECRETKEY
    
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlpa, get_sign(secret_key, urlpa))
    headers = {
        'X-BX-APIKEY': api_key,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response.text

def parseParam(paramsMap: dict) -> str:
    sortedKeys = sorted(paramsMap)
    paramsStr = "&".join(["%s=%s" % (x, paramsMap[x]) for x in sortedKeys])
    if paramsStr != "": 
        return paramsStr+"&timestamp="+str(int(time.time() * 1000))
    else:
        return paramsStr+"timestamp="+str(int(time.time() * 1000))

@router.get("/profit/{symbol}")
async def get_profit_info(symbol: str) -> dict:
    """수익률 및 자산 정보 조회"""
    global global_api_key, global_secret_key
    
    # API 키가 설정되지 않은 경우
    if not global_api_key or not global_secret_key:
        raise HTTPException(status_code=404, detail="API 키가 설정되지 않았습니다.")
    
    try:
        # 하드코딩된 심볼 사용
        symbol = HARDCODED_SYMBOL
        print(f"수익률 API 호출: 하드코딩 symbol={symbol}, API_KEY={global_api_key[:10]}...")
        
        # 1. 계정 정보 조회 (초기자산, 현재자산)
        account_result = get_account_info()
        initial_balance = 1000  # 기본값
        current_balance = 1000  # 기본값
        
        if account_result.get('code') == 0:
            account_data = account_result.get('data', {})
            current_balance = float(account_data.get('totalWalletBalance', 1000))
            initial_balance = float(account_data.get('totalInitialMargin', 1000))
        
        # 2. 현재 포지션 조회
        positions_result = get_positions(symbol)
        print(f"포지션 조회 결과: {positions_result}")
        
        has_position = False
        position_side = ''
        position_size = 0
        entry_price = 0
        
        if positions_result.get('code') == 0:
            positions = positions_result.get('data', [])
            active_positions = [p for p in positions if float(p.get('positionAmt', 0)) != 0]
            
            if active_positions:
                has_position = True
                position = active_positions[0]  # 첫 번째 활성 포지션
                position_side = position.get('positionSide', 'LONG')
                position_size = float(position.get('positionAmt', 0))
                entry_price = float(position.get('avgPrice', 0))
        
        # 3. 현재가 조회
        price_result = get_current_price(symbol)
        current_price = 0
        
        if price_result.get('code') == 0:
            current_price = float(price_result.get('data', {}).get('price', 0))
        
        # 4. 수익률 계산
        profit_rate = 0
        if initial_balance > 0:
            profit_rate = ((current_balance - initial_balance) / initial_balance) * 100
        
        # 통합 응답
        return {
            "initialBalance": initial_balance,
            "currentBalance": current_balance,
            "hasPosition": has_position,
            "positionSide": position_side,
            "positionSize": position_size,
            "entryPrice": entry_price,
            "currentPrice": current_price,
            "profitRate": profit_rate
        }
        
    except Exception as e:
        print(f"수익률 조회 중 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"수익률 조회 중 오류: {str(e)}")