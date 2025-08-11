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

def get_current_price(symbol):
    """현재가 조회"""
    path = '/openApi/swap/v2/quote/price'
    method = "GET"
    paramsMap = {"symbol": symbol}
    paramsStr = parseParam(paramsMap)
    result = send_request(method, path, paramsStr, {})
    return json.loads(result)

def calculate_profit_rate(entry_price, current_price, position_side, leverage):
    """수익률 계산 (레버리지 적용)"""
    entry_price = float(entry_price)
    current_price = float(current_price)
    leverage = int(leverage)
    
    # 진입가가 0인 경우 처리
    if entry_price == 0:
        print(f"⚠️  진입가가 0입니다. entry_price: {entry_price}")
        return 0
    
    if position_side == "LONG":
        # 롱 포지션: (현재가 - 진입가) / 진입가 * 100 * 레버리지
        base_profit_rate = ((current_price - entry_price) / entry_price) * 100
        profit_rate = base_profit_rate * leverage
    elif position_side == "SHORT":
        # 숏 포지션: (진입가 - 현재가) / 진입가 * 100 * 레버리지
        base_profit_rate = ((entry_price - current_price) / entry_price) * 100
        profit_rate = base_profit_rate * leverage
    else:
        profit_rate = 0
    
    return profit_rate

def monitor_profit_rate(symbol, monitor_duration=60, interval=5):
    """수익률 모니터링"""
    print(f"=== {symbol} 수익률 모니터링 시작 (총 {monitor_duration}초, {interval}초 간격) ===")
    
    start_time = time.time()
    
    while time.time() - start_time < monitor_duration:
        try:
            # 1. 현재 포지션 조회
            positions_result = get_positions(symbol)
            
            if positions_result.get('code') != 0:
                print(f"포지션 조회 실패: {positions_result.get('msg')}")
                time.sleep(interval)
                continue
            
            positions = positions_result.get('data', [])
            active_positions = [p for p in positions if float(p.get('positionAmt', 0)) != 0]
            
            if not active_positions:
                print(f"⚠️  {symbol}에 활성 포지션이 없습니다.")
                time.sleep(interval)
                continue
            
            # 2. 현재가 조회
            price_result = get_current_price(symbol)
            if price_result.get('code') != 0:
                print(f"현재가 조회 실패: {price_result.get('msg')}")
                time.sleep(interval)
                continue
            
            current_price = float(price_result['data']['price'])
            
            # 3. 각 포지션별 수익률 계산 및 출력
            current_time = time.strftime("%H:%M:%S")
            print(f"\n📊 [{current_time}] {symbol} 수익률 현황")
            print("-" * 60)
            
            for position in active_positions:
                position_side = position.get('positionSide')
                position_amt = float(position.get('positionAmt', 0))
                
                # 진입가격: entryPrice 또는 avgPrice 사용
                entry_price = float(position.get('entryPrice') or position.get('avgPrice', 0))
                
                unrealized_profit = float(position.get('unrealizedProfit', 0))
                leverage = int(position.get('leverage', 1))
                mark_price = float(position.get('markPrice', current_price))
                
                # 현재가는 markPrice 우선 사용
                actual_current_price = mark_price if mark_price > 0 else current_price
                
                # 수익률 계산 (레버리지 적용)
                profit_rate = calculate_profit_rate(entry_price, actual_current_price, position_side, leverage)
                
                # 기본 수익률 (레버리지 제외)
                base_profit_rate = profit_rate / leverage if leverage > 0 else 0
                
                # 상태 아이콘
                if profit_rate > 0:
                    status_icon = "🟢"
                elif profit_rate < 0:
                    status_icon = "🔴"
                else:
                    status_icon = "⚪"
                
                print(f"{status_icon} {position_side} 포지션:")
                print(f"   수량: {abs(position_amt)}")
                print(f"   진입가: {entry_price:.4f}")
                print(f"   현재가: {actual_current_price:.4f}")
                print(f"   기본 수익률: {base_profit_rate:+.2f}%")
                print(f"   실제 수익률: {profit_rate:+.2f}% (레버리지 {leverage}x 적용)")
                print(f"   미실현손익: {unrealized_profit:+.4f} VST")
                print()
            
            time.sleep(interval)
            
        except Exception as e:
            print(f"❌ 모니터링 중 오류 발생: {e}")
            time.sleep(interval)
    
    print("=== 수익률 모니터링 종료 ===")

def show_current_positions(symbol):
    """현재 포지션 현황 한번만 출력"""
    print(f"=== {symbol} 현재 포지션 현황 ===")
    
    try:
        # 포지션 조회
        positions_result = get_positions(symbol)
        
        if positions_result.get('code') != 0:
            print(f"포지션 조회 실패: {positions_result.get('msg')}")
            return
        
        positions = positions_result.get('data', [])
        active_positions = [p for p in positions if float(p.get('positionAmt', 0)) != 0]
        
        if not active_positions:
            print(f"⚠️  {symbol}에 활성 포지션이 없습니다.")
            return
        
        # 현재가 조회
        price_result = get_current_price(symbol)
        if price_result.get('code') != 0:
            print(f"현재가 조회 실패: {price_result.get('msg')}")
            return
        
        current_price = float(price_result['data']['price'])
        
        print(f"현재가: {current_price:.4f}")
        print("-" * 50)
        
        for position in active_positions:
            position_side = position.get('positionSide')
            position_amt = float(position.get('positionAmt', 0))
            
            # 진입가격: entryPrice 또는 avgPrice 사용
            entry_price = float(position.get('entryPrice') or position.get('avgPrice', 0))
            
            unrealized_profit = float(position.get('unrealizedProfit', 0))
            leverage = int(position.get('leverage', 1))
            mark_price = float(position.get('markPrice', current_price))
            
            # 현재가는 markPrice 우선 사용
            actual_current_price = mark_price if mark_price > 0 else current_price
            
            # 수익률 계산 (레버리지 적용)
            profit_rate = calculate_profit_rate(entry_price, actual_current_price, position_side, leverage)
            base_profit_rate = profit_rate / leverage if leverage > 0 else 0
            
            status_icon = "🟢" if profit_rate > 0 else "🔴" if profit_rate < 0 else "⚪"
            
            print(f"{status_icon} {position_side} 포지션:")
            print(f"   수량: {abs(position_amt)}")
            print(f"   진입가: {entry_price:.4f} (avgPrice)")
            print(f"   현재가: {actual_current_price:.4f} (markPrice)")
            print(f"   기본 수익률: {base_profit_rate:+.2f}%")
            print(f"   실제 수익률: {profit_rate:+.2f}% (레버리지 {leverage}x 적용)")
            print(f"   미실현손익: {unrealized_profit:+.4f} VST")
            print()
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

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
    symbol = "XRP-USDT"
    
    print("1. 현재 포지션 현황 보기")
    print("2. 수익률 실시간 모니터링 (60초)")
    choice = input("선택하세요 (1 또는 2): ")
    
    if choice == "1":
        show_current_positions(symbol)
    elif choice == "2":
        monitor_profit_rate(symbol, monitor_duration=60, interval=5)
    else:
        print("잘못된 선택입니다.")