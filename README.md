# Next Auto - TradingView 자동매매 시스템

TradingView의 기술적 분석 신호를 자동으로 거래소에 전달하여 자동매매를 수행하는 시스템입니다.

## 🚀 주요 기능

- **TradingView 웹훅 연동**: TradingView에서 신호를 받아 자동으로 거래 실행
- **다중세션 지원**: 여러 사용자가 동시에 사용 가능
- **데모/실제 거래소 선택**: BingX 데모(VST) 및 실제(USDT) 거래소 지원
- **실시간 수익률 모니터링**: 포지션별 실시간 수익률 및 차트 표시
- **수익률 캘린더**: 사용자별 일별 수익 데이터 관리
- **자동 익절/손절**: 설정 가능한 익절/손절 비율

## 🏗️ 프로젝트 구조

```
next_auto/
├── beckend/                 # 백엔드 (FastAPI)
│   ├── app/
│   │   ├── api/            # API 엔드포인트
│   │   ├── core/           # 설정 및 데이터베이스
│   │   ├── models/         # 데이터 모델
│   │   └── services/       # 비즈니스 로직
│   ├── sample/             # 테스트 및 샘플 파일
│   └── requirements.txt    # Python 의존성
├── frontend/               # 프론트엔드 (Next.js)
│   ├── ProfitMonitor.js    # 수익률 모니터링
│   ├── SettingsForm.js     # 설정 관리
│   └── SessionManager.js   # 세션 관리
└── README.md
```

## 🛠️ 설치 및 실행

### 백엔드 설정

1. **Python 가상환경 생성**
```bash
cd beckend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

2. **의존성 설치**
```bash
pip install -r requirements.txt
```

3. **환경변수 설정**
```bash
# .env 파일 생성
BINGX_API_KEY=your_api_key
BINGX_SECRET_KEY=your_secret_key
MONGO_URI=mongodb://localhost:27017
```

4. **서버 실행**
```bash
cd app
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 프론트엔드 설정

1. **의존성 설치**
```bash
cd frontend
npm install
```

2. **개발 서버 실행**
```bash
npm run dev
```

## 📊 API 엔드포인트

### 웹훅 API
- `POST /api/webhook`: TradingView 웹훅 신호 처리

### 세션 관리 API
- `POST /api/create-session`: 새 세션 생성
- `GET /api/sessions`: 모든 세션 조회
- `GET /api/session/{session_id}`: 특정 세션 조회
- `PUT /api/session/{session_id}`: 세션 업데이트
- `DELETE /api/session/{session_id}`: 세션 삭제

### 수익률 API
- `GET /api/profit/{symbol}`: 수익률 정보 조회



## 🔧 설정

### 거래소 설정
- **데모 거래소**: VST (테스트용)
- **실제 거래소**: USDT (실제 거래)

### 거래 설정
- **투자금액**: 거래당 투자할 금액
- **레버리지**: 거래 레버리지 설정
- **익절**: 수익 실현 비율 (%)
- **손절**: 손실 제한 비율 (%)

### 지표 설정
- **프리미엄지표**: PREMIUM 전략
- **콘볼지표**: CONBOL 전략

## 🔒 보안

- API 키 암호화 저장
- 웹훅 신호 검증
- 세션별 데이터 격리
- 에러 처리 및 로깅

## 📝 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 🤝 기여

버그 리포트나 기능 제안은 이슈를 통해 해주세요.

## ⚠️ 면책 조항

이 소프트웨어는 교육 및 연구 목적으로만 제공됩니다. 실제 거래에 사용할 경우 발생하는 손실에 대해 개발자는 책임을 지지 않습니다.
