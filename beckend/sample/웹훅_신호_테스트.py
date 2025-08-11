from fastapi import FastAPI, Request
import uvicorn
import json

app = FastAPI()

@app.post("/api/webhook")  # /api/webhook 경로로 수정
async def webhook(request: Request):
    """웹훅 신호를 받아서 출력하는 테스트용 엔드포인트"""
    try:
        # 요청 헤더 출력
        print("\n=== 웹훅 신호 수신 ===")
        print("\n[헤더 정보]")
        for header, value in request.headers.items():
            print(f"{header}: {value}")
        
        # 요청 본문 출력
        body = await request.json()
        print("\n[본문 내용]")
        print(json.dumps(body, indent=2, ensure_ascii=False))
        
        return {
            "status": "success",
            "message": "웹훅 신호가 성공적으로 수신되었습니다.",
            "received_data": body
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
    uvicorn.run(app, host="0.0.0.0", port=80)  # 80 포트로 수정