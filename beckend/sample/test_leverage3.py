import time
import requests
import hmac
import os
from hashlib import sha256
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

APIURL = "https://open-api-vst.bingx.com"  # 데모 거래소
APIKEY = os.getenv("BINGX_API_KEY")
SECRETKEY = os.getenv("BINGX_SECRET_KEY")

def demo():
    payload = {}
    path = '/openApi/swap/v2/trade/leverage'
    method = "POST"
    paramsMap = {
        "leverage": "10",
        "side": "LONG",
        "symbol": "XRP-USDT"
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
    print("demo:", demo())