import json
import websocket
import gzip
import io
import time
import requests
import hmac
import os
from hashlib import sha256
from dotenv import load_dotenv

# .env 파일에서 API 키와 시크릿 키를 불러옵니다.
load_dotenv()

APIURL = "https://open-api.bingx.com"
APIKEY = os.getenv("BINGX_API_KEY")
SECRETKEY = os.getenv("BINGX_SECRET_KEY")
WEBSOCKET_BASE_URL = "wss://open-api-swap.bingx.com/swap-market"

class AccountMonitor:
    def __init__(self):
        self.listen_key = None
        self.ws = None
        
    def _get_signature(self, payload):
        """HMAC-SHA256 서명 생성"""
        return hmac.new(SECRETKEY.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()

    def _get_timestamp(self):
        """현재 시간을 밀리초 단위로 반환"""
        return str(int(time.time() * 1000))
        
    def get_listen_key(self):
        """listenKey 발급"""
        print("🔑 listenKey 발급 요청 중...")
        
        timestamp = self._get_timestamp()
        params_str = f"timestamp={timestamp}"
        signature = self._get_signature(params_str)
        
        url = f"{APIURL}/openApi/user/auth/userDataStream?{params_str}&signature={signature}"
        headers = {'X-BX-APIKEY': APIKEY}
        
        try:
            response = requests.post(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            if "listenKey" in result:
                self.listen_key = result["listenKey"]
                print(f"✅ listenKey 발급 성공: {self.listen_key}")
                return True
            else:
                print(f"❌ listenKey 발급 실패: {result}")
                return False
                
        except Exception as e:
            print(f"❌ listenKey 발급 중 오류: {e}")
            return False

    def on_open(self, ws):
        """웹소켓 연결 성공 시 호출"""
        print('✅ WebSocket connected')
        print("📡 실시간 계좌 및 포지션 업데이트 대기 중...")
        
    def on_message(self, ws, message):
        """웹소켓 메시지 수신 시 호출"""
        try:
            compressed_data = gzip.GzipFile(fileobj=io.BytesIO(message), mode='rb')
            decompressed_data = compressed_data.read()
            utf8_data = decompressed_data.decode('utf-8')

            # 서버 핑-퐁 처리
            if utf8_data == "Ping":
                ws.send("Pong")
                return
            
            data = json.loads(utf8_data)
            
            # ACCOUNT_UPDATE 메시지 처리
            if data.get("c") == "ACCOUNT_UPDATE":
                print("\n" + "=" * 50)
                print("💰 실시간 계정 잔고 업데이트")
                print("-" * 50)
                account_data = data.get('d', {}).get('a', {})
                balances = account_data.get('B', [])
                for bal in balances:
                    print(f"   자산: {bal.get('a'):<10} 잔고: {float(bal.get('wb')):.4f}")
                print("=" * 50)
            
            # POSITION_UPDATE 메시지 처리
            if data.get("c") == "POSITION_UPDATE":
                print("\n" + "=" * 50)
                print("📈 실시간 포지션 업데이트")
                print("-" * 50)
                position_data = data.get('d', {}).get('a', {})
                positions = position_data.get('P', [])
                for pos in positions:
                    side = pos.get('ps')
                    symbol = pos.get('s')
                    position_amt = float(pos.get('pa'))
                    entry_price = float(pos.get('ep'))
                    unrealized_profit = float(pos.get('up'))
                    print(f"   종목: {symbol:<10} 방향: {side:<5} 수량: {position_amt:.4f}")
                    print(f"   진입가: {entry_price:.4f} 미실현 손익: {unrealized_profit:.4f}")
                print("=" * 50)

        except json.JSONDecodeError:
            pass
        except Exception as e:
            print(f"❌ 메시지 처리 오류: {e}")

    def on_error(self, ws, error):
        """오류 발생 시 호출"""
        print(f"❌ 웹소켓 오류: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        """연결 종료 시 호출"""
        print('🔌 The connection is closed!')

    def start(self):
        """모니터링 시작"""
        if not self.get_listen_key():
            return
            
        ws_url = f"{WEBSOCKET_BASE_URL}?listenKey={self.listen_key}"
        
        self.ws = websocket.WebSocketApp(
            ws_url,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
        )
        self.ws.run_forever()

if __name__ == "__main__":
    monitor = AccountMonitor()
    
    print("🚀 실시간 계좌 및 포지션 모니터링 시작")
    print("📡 계정 정보 변동 시 즉시 업데이트됩니다.")
    print()
    
    try:
        monitor.start()
    except KeyboardInterrupt:
        print("\n👋 모니터링을 종료합니다.")