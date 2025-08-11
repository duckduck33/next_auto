from fastapi import FastAPI, Request
import uvicorn
import json

app = FastAPI()

@app.post("/api/webhook")
async def webhook(request: Request):
    """웹훅 신호를 받아서 출력하는 테스트용 엔드포인트"""
    try:
        print("\n=== 웹훅 신호 수신 ===")
        print("\n[헤더 정보]")
        for header, value in request.headers.items():
            print(f"{header}: {value}")
        
        body = await request.body()
        try:
            data = json.loads(body.decode('utf-8'))
            print("\n[트레이딩뷰 신호]")
            print(f"티커: {data['symbol']}")
            print(f"액션: {data['action']}")
            print(f"전략: {data['strategy']}")
            
            # 액션 검증
            if data['action'] not in ['LONG', 'SHORT', 'CLOSE']:
                raise ValueError(f"잘못된 액션입니다: {data['action']}")
            
            # 전략 검증
            if data['strategy'] not in ['PREMIUM', 'CONBOL']:
                raise ValueError(f"잘못된 전략입니다: {data['strategy']}")
            
            # 사용자가 선택한 지표와 웹훅 전략이 일치하는지 확인
            # (실제로는 프론트엔드에서 전송한 indicator 값과 비교)
            selected_indicator = data.get('indicator', 'PREMIUM')  # 기본값
            if data['strategy'] == selected_indicator:
                print(f"✅ 지표 일치: {data['strategy']} == {selected_indicator}")
                print("매매 신호를 처리합니다.")
            else:
                print(f"❌ 지표 불일치: {data['strategy']} != {selected_indicator}")
                print("매매 신호를 무시합니다.")
            
            return {
                "status": "success",
                "message": "웹훅 신호가 성공적으로 수신되었습니다.",
                "data": {
                    "symbol": data['symbol'],
                    "action": data['action'],
                    "strategy": data['strategy'],
                    "indicator_match": data['strategy'] == selected_indicator
                }
            }
        except json.JSONDecodeError:
            print("\n⚠️ 오류: JSON 형식이 아닌 데이터가 수신되었습니다")
            print(f"수신된 데이터: {body.decode('utf-8')}")
            return {
                "status": "error",
                "message": "JSON 형식이 아닌 데이터가 수신되었습니다"
            }
            
    except Exception as e:
        print(f"\n⚠️ 오류 발생: {str(e)}")
        return {
            "status": "error",
            "message": f"웹훅 처리 중 오류 발생: {str(e)}"
        }

if __name__ == "__main__":
    print("웹훅 신호 테스트 서버를 시작합니다...")
    print("Ctrl+C를 누르면 종료됩니다.")
    uvicorn.run(app, host="0.0.0.0", port=80)