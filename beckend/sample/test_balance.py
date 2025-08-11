import asyncio
import os
from dotenv import load_dotenv
import json

# .env 파일 로드
load_dotenv()

async def get_balance():
    import time
    import hmac
    from hashlib import sha256
    import aiohttp

    # API 설정
    API_KEY = os.getenv("BINGX_API_KEY")
    SECRET_KEY = os.getenv("BINGX_SECRET_KEY")
    BASE_URL = "https://open-api.bingx.com"

    # 파라미터 설정
    timestamp = str(int(time.time() * 1000))

    # 파라미터 정렬
    params = {
        "timestamp": timestamp
    }
    sorted_params = sorted(params.items())
    params_str = "&".join([f"{key}={value}" for key, value in sorted_params])

    # 서명 생성
    signature = hmac.new(
        SECRET_KEY.encode('utf-8'),
        params_str.encode('utf-8'),
        sha256
    ).hexdigest()

    # URL 생성
    url = f"{BASE_URL}/openApi/swap/v2/user/balance?{params_str}&signature={signature}"

    # API 요청
    async with aiohttp.ClientSession() as session:
        headers = {
            'X-BX-APIKEY': API_KEY,
            'Content-Type': 'application/json'
        }
        async with session.get(url, headers=headers) as response:
            data = await response.json()
            print(json.dumps(data, indent=2))

if __name__ == "__main__":
    asyncio.run(get_balance())