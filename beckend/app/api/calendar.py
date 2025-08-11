from fastapi import APIRouter, HTTPException, Request
from typing import Dict, Any, List
import json
import logging
from datetime import datetime, date
from app.services.database_service import database_service
from app.models.user_session import session_manager

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/calendar/{session_id}")
async def get_calendar_data(session_id: str) -> Dict[str, Any]:
    """사용자별 캘린더 데이터를 조회합니다."""
    try:
        # 세션 존재 확인
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
        
        # 데이터베이스에서 캘린더 데이터 조회
        calendar_data = await database_service.get_calendar_data(session_id)
        
        return {
            "success": True,
            "session_id": session_id,
            "data": calendar_data
        }
        
    except Exception as e:
        logger.error(f"캘린더 데이터 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"캘린더 데이터 조회 중 오류 발생: {str(e)}")

@router.post("/calendar/{session_id}")
async def save_calendar_data(session_id: str, request: Request) -> Dict[str, Any]:
    """사용자별 캘린더 데이터를 저장합니다."""
    try:
        # 세션 존재 확인
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
        
        body = await request.body()
        data = json.loads(body.decode('utf-8'))
        
        # 데이터베이스에 캘린더 데이터 저장
        success = await database_service.save_calendar_data(session_id, data)
        
        if success:
            return {
                "success": True,
                "message": "캘린더 데이터가 성공적으로 저장되었습니다."
            }
        else:
            raise HTTPException(status_code=500, detail="캘린더 데이터 저장에 실패했습니다.")
        
    except Exception as e:
        logger.error(f"캘린더 데이터 저장 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"캘린더 데이터 저장 중 오류 발생: {str(e)}")

@router.get("/calendar/{session_id}/daily/{date}")
async def get_daily_profit(session_id: str, date: str) -> Dict[str, Any]:
    """특정 날짜의 수익 요약을 조회합니다."""
    try:
        # 세션 존재 확인
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
        
        # 날짜 형식 검증
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="잘못된 날짜 형식입니다. YYYY-MM-DD 형식을 사용해주세요.")
        
        # 일별 수익 요약 조회
        daily_summary = await database_service.get_daily_profit_summary(session_id, date)
        
        return {
            "success": True,
            "session_id": session_id,
            "date": date,
            "summary": daily_summary
        }
        
    except Exception as e:
        logger.error(f"일별 수익 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"일별 수익 조회 중 오류 발생: {str(e)}")

@router.get("/calendar/{session_id}/monthly/{year}/{month}")
async def get_monthly_calendar(session_id: str, year: int, month: int) -> Dict[str, Any]:
    """월별 캘린더 데이터를 생성합니다."""
    try:
        # 세션 존재 확인
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
        
        # 데이터베이스에서 해당 월의 모든 캘린더 데이터 조회
        calendar_data = await database_service.get_calendar_data(session_id)
        
        # 해당 월의 데이터만 필터링
        monthly_data = {}
        target_month = f"{year:04d}-{month:02d}"
        
        for date_str, data in calendar_data.items():
            if date_str.startswith(target_month):
                monthly_data[date_str] = data
        
        # 캘린더 그리드 생성
        import calendar
        cal = calendar.monthcalendar(year, month)
        
        calendar_grid = []
        for week in cal:
            week_data = []
            for day in week:
                if day == 0:
                    week_data.append({"day": "", "profit": None, "profit_rate": None})
                else:
                    date_str = f"{year:04d}-{month:02d}-{day:02d}"
                    day_data = monthly_data.get(date_str, {})
                    week_data.append({
                        "day": day,
                        "profit": day_data.get('profit', 0),
                        "profit_rate": day_data.get('profit_rate', 0),
                        "symbol": day_data.get('symbol'),
                        "position_side": day_data.get('position_side'),
                        "trade_count": day_data.get('trade_count', 0)
                    })
            calendar_grid.append(week_data)
        
        # 월별 통계 계산
        total_profit = sum(data.get('profit', 0) for data in monthly_data.values())
        total_trades = sum(data.get('trade_count', 0) for data in monthly_data.values())
        profitable_days = sum(1 for data in monthly_data.values() if data.get('profit', 0) > 0)
        total_days = len(monthly_data)
        
        return {
            "success": True,
            "session_id": session_id,
            "year": year,
            "month": month,
            "calendar_grid": calendar_grid,
            "monthly_stats": {
                "total_profit": total_profit,
                "total_trades": total_trades,
                "profitable_days": profitable_days,
                "total_days": total_days,
                "win_rate": (profitable_days / total_days * 100) if total_days > 0 else 0
            }
        }
        
    except Exception as e:
        logger.error(f"월별 캘린더 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"월별 캘린더 조회 중 오류 발생: {str(e)}")

@router.post("/calendar/{session_id}/trade-record")
async def record_trade(session_id: str, request: Request) -> Dict[str, Any]:
    """거래 기록을 저장합니다."""
    try:
        # 세션 존재 확인
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
        
        body = await request.body()
        data = json.loads(body.decode('utf-8'))
        
        # 필수 필드 검증
        required_fields = ['symbol', 'position_side', 'entry_price', 'quantity', 'leverage']
        for field in required_fields:
            if field not in data:
                raise HTTPException(status_code=400, detail=f"필수 필드가 누락되었습니다: {field}")
        
        # 거래 히스토리 저장
        from app.models.database_models import TradingHistoryDB
        
        trade_record = TradingHistoryDB(
            session_id=session_id,
            symbol=data['symbol'],
            position_side=data['position_side'],
            entry_price=float(data['entry_price']),
            exit_price=data.get('exit_price'),
            quantity=float(data['quantity']),
            leverage=int(data['leverage']),
            profit=data.get('profit'),
            profit_rate=data.get('profit_rate'),
            entry_time=datetime.now(),
            exit_time=datetime.now() if data.get('exit_price') else None,
            status="CLOSED" if data.get('exit_price') else "OPEN",
            created_at=datetime.now()
        )
        
        success = await database_service.save_trading_history(trade_record)
        
        if success:
            return {
                "success": True,
                "message": "거래 기록이 성공적으로 저장되었습니다."
            }
        else:
            raise HTTPException(status_code=500, detail="거래 기록 저장에 실패했습니다.")
        
    except Exception as e:
        logger.error(f"거래 기록 저장 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"거래 기록 저장 중 오류 발생: {str(e)}")
