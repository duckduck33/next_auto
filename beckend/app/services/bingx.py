import time
import hmac
import json
from hashlib import sha256
from typing import Dict, Any

import aiohttp
from fastapi import HTTPException

from app.core.config import get_settings

settings = get_settings()

class BingXClient:
    def __init__(self):
        self.api_key = settings.bingx_api_key
        self.secret_key = settings.bingx_secret_key
        self.base_url = settings.bingx_url

    def set_credentials(self, api_key: str, secret_key: str, exchange_type: str = "demo"):
        """API 키와 시크릿 키를 동적으로 설정합니다."""
        self.api_key = api_key
        self.secret_key = secret_key
        
        # 거래소 타입에 따라 URL 설정
        if exchange_type == "live":
            self.base_url = "https://open-api.bingx.com"
        else:
            self.base_url = "https://open-api-vst.bingx.com"

    def _generate_signature(self, params: Dict[str, Any]) -> tuple[str, str]:
        """파라미터를 정렬하고 서명을 생성합니다. (테스트 파일과 동일한 방식)"""
        # timestamp 추가
        timestamp = str(int(time.time() * 1000))
        params['timestamp'] = timestamp
        
        # 파라미터 정렬 및 문자열 생성 (테스트 파일 방식)
        sorted_keys = sorted(params)
        params_str = "&".join(["%s=%s" % (x, params[x]) for x in sorted_keys])
        
        # 서명 생성
        signature = hmac.new(
            self.secret_key.encode("utf-8"),
            params_str.encode("utf-8"),
            sha256
        ).hexdigest()
        
        return params_str, signature

    async def _request(self, method: str, path: str, params: Dict[str, Any] = None) -> Dict:
        """API 요청을 보냅니다."""
        params = params or {}
        
        # 서명 생성
        params_str, signature = self._generate_signature(params)
        
        # URL 생성
        url = f"{self.base_url}{path}?{params_str}&signature={signature}"
        print(f"요청 URL: {url}")  # 디버깅용
        
        # API 요청
        async with aiohttp.ClientSession() as session:
            headers = {
                'X-BX-APIKEY': self.api_key,
            }
            try:
                async with session.request(method, url, headers=headers) as response:
                    result = await response.json()
                    print(f"API 응답: {result}")  # 디버깅용
                    
                    if response.status != 200 or result.get('code', 0) != 0:
                        raise HTTPException(
                            status_code=400,
                            detail=f"BingX API error: {result.get('msg', 'Unknown error')}"
                        )
                    
                    return result
                    
            except aiohttp.ClientError as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"BingX API request failed: {str(e)}"
                )

    async def get_balance(self) -> Dict:
        """계정 잔고를 조회합니다."""
        params = {}
        return await self._request('GET', '/openApi/swap/v2/user/balance', params)

    async def get_positions(self, symbol: str = None) -> Dict:
        """포지션을 조회합니다. symbol이 None이면 모든 포지션을 조회합니다."""
        params = {}
        if symbol:
            params['symbol'] = symbol
        return await self._request('GET', '/openApi/swap/v2/user/positions', params)

    async def get_ticker(self, symbol: str) -> Dict:
        """현재 시장 가격을 조회합니다."""
        params = {'symbol': symbol}
        return await self._request('GET', '/openApi/swap/v2/quote/price', params)

    async def set_leverage(self, symbol: str, leverage: int, side: str) -> Dict:
        """레버리지를 설정합니다. (테스트 파일과 동일한 파라미터 순서)"""
        params = {
            'leverage': str(leverage),
            'side': side,
            'symbol': symbol
        }
        print(f"레버리지 설정 파라미터: {params}")  # 디버깅용
        return await self._request('POST', '/openApi/swap/v2/trade/leverage', params)

    async def place_order(self, **params) -> Dict:
        """주문을 생성합니다."""
        # 디버깅용 출력
        print(f"주문 파라미터: {params}")
        return await self._request('POST', '/openApi/swap/v2/trade/order', params)

# 싱글톤 인스턴스 생성
bingx_client = BingXClient()