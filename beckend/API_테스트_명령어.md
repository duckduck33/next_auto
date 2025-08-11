# FastAPI 거래 시스템 테스트 명령어 모음

## 1. 잔고 조회
```powershell
curl -Uri "http://127.0.0.1:8000/api/balance" -Method Get
```

## 2. 레버리지 설정
```powershell
# 숏 포지션 레버리지 20배 설정 (포지션방향과 배수는 옵션으로 설정가능)
curl -Uri "http://127.0.0.1:8000/api/leverage?symbol=XRP-USDT&leverage=20&side=SHORT" -Method Post
```

## 3. 포지션 진입 (익절/손절 포함)

### 롱 포지션 진입
```powershell
curl -Uri "http://127.0.0.1:8000/api/webhook" -Method Post -Headers @{"Content-Type"="application/json"} -Body '{"symbol":"XRP-USDT","side":"LONG","quantity":10,"leverage":20,"take_profit_percentage":2.0,"stop_loss_percentage":2.0}'
```

### 숏 포지션 진입
```powershell
curl -Uri "http://127.0.0.1:8000/api/webhook" -Method Post -Headers @{"Content-Type"="application/json"} -Body '{"symbol":"XRP-USDT","side":"SHORT","quantity":10,"leverage":20,"take_profit_percentage":2.0,"stop_loss_percentage":2.0}'
```

## 4. 포지션 진입 (익절/손절 없이)

### 롱 포지션 진입 (기본)
```powershell
curl -Uri "http://127.0.0.1:8000/api/webhook" -Method Post -Headers @{"Content-Type"="application/json"} -Body '{"symbol":"XRP-USDT","side":"LONG","quantity":10,"leverage":20}'
```

### 숏 포지션 진입 (기본)
```powershell
curl -Uri "http://127.0.0.1:8000/api/webhook" -Method Post -Headers @{"Content-Type"="application/json"} -Body '{"symbol":"XRP-USDT","side":"SHORT","quantity":10,"leverage":20}'
```

## 5. 포지션 종료 (모든 포지션 자동 감지하여 종료)
```powershell
curl -Uri "http://127.0.0.1:8000/api/webhook" -Method Post -Headers @{"Content-Type"="application/json"} -Body '{"symbol":"XRP-USDT","is_close":true}'
```

## 6. 파라미터 설명

### 잔고 조회
- 파라미터 없음

### 레버리지 설정
| 파라미터 | 설명 | 예시 |
|---------|------|------|
| symbol | 거래 심볼 | XRP-USDT |
| leverage | 레버리지 배수 | 10, 20 |
| side | 포지션 방향 | LONG, SHORT |

### 포지션 진입/종료
| 파라미터 | 설명 | 예시 | 필수여부 |
|---------|------|------|----------|
| symbol | 거래 심볼 | "XRP-USDT" | 필수 |
| side | 포지션 방향 | "LONG", "SHORT" | 진입시 필수 |
| quantity | 거래 수량 | 10 | 진입시 필수 |
| leverage | 레버리지 | 20 | 선택 |
| take_profit_percentage | 익절 퍼센트 | 2.0 (2%) | 선택 |
| stop_loss_percentage | 손절 퍼센트 | 2.0 (2%) | 선택 |
| is_close | 포지션 종료 여부 | true | 종료시 필수 |

### 수익률 조회
| 파라미터 | 설명 | 예시 |
|---------|------|------|
| symbol | 거래 심볼 | XRP-USDT |

## 7. 서버 실행 명령어
```powershell
# 가상환경 활성화
.\venv\Scripts\activate

# 서버 실행
uvicorn app.main:app --reload
```

## 8. 수익률 조회
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/profit/XRP-USDT" -Method Get
```

## 9. 예상 응답 형태

### 잔고 조회 성공
```json
{
  "success": true,
  "message": "Balance retrieved successfully",
  "data": {
    "code": 0,
    "msg": "",
    "data": {
      "balance": {
        "userId": "1258132074245095424",
        "asset": "VST",
        "balance": "102377.0961",
        "equity": "102377.0961"
      }
    }
  }
}
```

### 레버리지 설정 성공
```json
{
  "success": true,
  "message": "Leverage set successfully",
  "data": {
    "code": 0,
    "msg": "",
    "data": {}
  }
}
```

### 포지션 진입 성공 (익절/손절 없이)
```json
{
  "success": true,
  "message": "Order executed successfully",
  "data": {
    "code": 0,
    "msg": "",
    "data": {
      "order": {
        "orderId": "1952424217036201984",
        "symbol": "XRP-USDT",
        "positionSide": "LONG"
      }
    }
  }
}
```

### 포지션 진입 성공 (익절/손절 포함)
```json
{
  "success": true,
  "message": "Order executed successfully",
  "data": {
    "code": 0,
    "msg": "",
    "data": {
      "order": {
        "orderId": "1952424217036201984",
        "symbol": "XRP-USDT",
        "positionSide": "LONG"
      }
    }
  }
}
```

### 포지션 종료 성공
```json
{
  "success": true,
  "message": "Order executed successfully",
  "data": {
    "message": "XRP-USDT 포지션 종료 완료",
    "closed_positions": [
      {
        "position_side": "LONG",
        "quantity": 10.0,
        "result": {
          "code": 0,
          "msg": "",
          "data": {
            "order": {
              "orderId": "1952426462498791424",
              "symbol": "XRP-USDT",
              "positionSide": "LONG"
            }
          }
        }
      }
    ]
  }
}
```

### 수익률 조회 성공
```json
[
  {
    "symbol": "XRP-USDT",
    "position_side": "LONG",
    "position_amt": 32969.0,
    "entry_price": 3.0491,
    "current_price": 3.0451,
    "base_profit_rate": -0.13,
    "actual_profit_rate": -0.66,
    "unrealized_profit": -132.0327,
    "leverage": 5
  }
]
```

### 오류 응답
```json
{
  "detail": "Trading execution failed: 400: BingX API error: ..."
}
```

우분투서버 백엔드 실행 명령어 가상환경에서
sudo /home/ubuntu/tv_auto/venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 80
