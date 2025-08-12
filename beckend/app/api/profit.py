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
from app.models.user_session import session_manager
from app.services.sqlite_session_service import sqlite_session_service

# .env 파일 로드
load_dotenv()

router = APIRouter()



def get_api_url(exchange_type: str) -> str:
    """거래소 타입에 따라 API URL 반환"""
    if exchange_type == "live":
        return "https://open-api.bingx.com"
    else:
        return "https://open-api-vst.bingx.com"

def get_positions(symbol: str, api_key: str, secret_key: str, exchange_type: str):
    """현재 포지션 조회"""
    api_url = get_api_url(exchange_type)
    path = '/openApi/swap/v2/user/positions'
    method = "GET"
    paramsMap = {"symbol": symbol}
    paramsStr = parseParam(paramsMap)
    result = send_request(method, path, paramsStr, {}, api_key, secret_key, api_url)
    return json.loads(result)

def get_current_price(symbol: str, api_key: str, secret_key: str, exchange_type: str):
    """현재가 조회"""
    api_url = get_api_url(exchange_type)
    path = '/openApi/swap/v2/quote/price'
    method = "GET"
    paramsMap = {"symbol": symbol}
    paramsStr = parseParam(paramsMap)
    result = send_request(method, path, paramsStr, {}, api_key, secret_key, api_url)
    return json.loads(result)

def get_account_info(api_key: str, secret_key: str, exchange_type: str):
    """계정 정보 조회"""
    api_url = get_api_url(exchange_type)
    path = '/openApi/swap/v2/user/account'
    method = "GET"
    paramsMap = {}
    paramsStr = parseParam(paramsMap)
    result = send_request(method, path, paramsStr, {}, api_key, secret_key, api_url)
    return json.loads(result)

def get_sign(api_secret: str, payload: str) -> str:
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    return signature

def send_request(method: str, path: str, urlpa: str, payload: dict, api_key: str, secret_key: str, api_url: str) -> str:
    url = "%s%s?%s&signature=%s" % (api_url, path, urlpa, get_sign(secret_key, urlpa))
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

@router.get("/balance/{session_id}")
async def get_balance_info(session_id: str) -> dict:
    """자산 정보 조회 (수익률 계산 없음)"""
    try:
        # 세션 정보 조회
        session_data = sqlite_session_service.get_session(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
        
        api_key = session_data.get('api_key')
        secret_key = session_data.get('secret_key')
        exchange_type = session_data.get('exchange_type', 'demo')
        investment = float(session_data.get('investment', 1000))
        
        if not api_key or not secret_key:
            raise HTTPException(status_code=400, detail="API 키가 설정되지 않았습니다.")
        
        print(f"자산 조회 API 호출: exchange_type={exchange_type}, session_id={session_id}")
        
        # 계정 정보 조회
        account_result = get_account_info(api_key, secret_key, exchange_type)
        current_balance = investment  # 기본값
        
        if account_result.get('code') == 0:
            account_data = account_result.get('data', {})
            current_balance = float(account_data.get('totalWalletBalance', investment))
        
        # 초기자산 조회 (세션 시작시점의 잔고)
        initial_balance = session_data.get('initial_balance')
        if initial_balance is None:
            # 초기자산이 저장되지 않은 경우 현재 잔고를 초기자산으로 설정
            initial_balance = current_balance
            # SQLite에 초기자산 저장
            sqlite_session_service.update_initial_balance(session_id, initial_balance)
        
        return {
            "initialBalance": initial_balance,
            "currentBalance": current_balance,
            "hasPosition": False,  # 자산 조회 시에는 포지션 정보 없음
            "positionSide": '',
            "positionSize": 0,
            "entryPrice": 0,
            "currentPrice": 0,
            "profitRate": 0  # 수익률 계산 없음
        }
        
    except Exception as e:
        print(f"자산 조회 중 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"자산 조회 중 오류: {str(e)}")