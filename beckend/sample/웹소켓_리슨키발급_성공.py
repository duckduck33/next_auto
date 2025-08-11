
import time
import requests
import hmac
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = "Svh5Eur339xTi15d2uDu7Z7XLocXxSOvzPSnYfMPQAhTenpUVMRL4wXkdB41gUYB7VDnF0guEmXzWhVEpUOsA"
SECRETKEY = "t15d58oRpk6Z1IPCe9TQbhgKNuwCJ8dgPT4MsphHv1hqwDuu5YYP93AQZixDPlwTgC5f48d4VVBZeS12R6Q"

def demo():
    payload = {}
    path = '/openApi/user/auth/userDataStream'
    method = "POST"
    paramsMap = {}
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
