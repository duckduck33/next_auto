from fastapi import APIRouter, HTTPException, Request
from typing import Dict, Any
import json
import logging
from app.services.user_auth_service import user_auth_service

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/register")
async def register_user(request: Request) -> Dict[str, Any]:
    """사용자 등록"""
    try:
        body = await request.body()
        data = json.loads(body.decode('utf-8'))
        
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        
        # 입력 검증
        if not email or not password:
            raise HTTPException(status_code=400, detail="이메일과 비밀번호를 입력해주세요.")
        
        # 이메일 형식 검증
        if '@' not in email or '.' not in email:
            raise HTTPException(status_code=400, detail="올바른 이메일 형식을 입력해주세요.")
        
        # 사용자 등록
        if user_auth_service.register_user(email, password):
            return {
                "success": True,
                "message": "회원가입이 완료되었습니다."
            }
        else:
            raise HTTPException(status_code=400, detail="이미 존재하는 이메일입니다.")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"사용자 등록 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="회원가입 중 오류가 발생했습니다.")

@router.post("/login")
async def login_user(request: Request) -> Dict[str, Any]:
    """사용자 로그인"""
    try:
        body = await request.body()
        data = json.loads(body.decode('utf-8'))
        
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        
        # 입력 검증
        if not email or not password:
            raise HTTPException(status_code=400, detail="이메일과 비밀번호를 입력해주세요.")
        
        # 사용자 인증
        if user_auth_service.authenticate_user(email, password):
            return {
                "success": True,
                "message": "로그인 성공",
                "user_email": email
            }
        else:
            raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다.")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"사용자 로그인 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="로그인 중 오류가 발생했습니다.")

@router.get("/user/{email}")
async def get_user_info(email: str) -> Dict[str, Any]:
    """사용자 정보 조회"""
    try:
        user_info = user_auth_service.get_user_info(email)
        if user_info:
            return {
                "success": True,
                "user": user_info
            }
        else:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"사용자 정보 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="사용자 정보 조회 중 오류가 발생했습니다.")

@router.post("/change-password")
async def change_password(request: Request) -> Dict[str, Any]:
    """비밀번호 변경"""
    try:
        body = await request.body()
        data = json.loads(body.decode('utf-8'))
        
        email = data.get('email', '').strip()
        old_password = data.get('oldPassword', '').strip()
        new_password = data.get('newPassword', '').strip()
        
        # 입력 검증
        if not email or not old_password or not new_password:
            raise HTTPException(status_code=400, detail="모든 필드를 입력해주세요.")
        
        # 비밀번호 변경
        if user_auth_service.change_password(email, old_password, new_password):
            return {
                "success": True,
                "message": "비밀번호가 변경되었습니다."
            }
        else:
            raise HTTPException(status_code=400, detail="기존 비밀번호가 올바르지 않습니다.")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"비밀번호 변경 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="비밀번호 변경 중 오류가 발생했습니다.")

@router.delete("/user")
async def delete_user(request: Request) -> Dict[str, Any]:
    """사용자 삭제"""
    try:
        body = await request.body()
        data = json.loads(body.decode('utf-8'))
        
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        
        # 입력 검증
        if not email or not password:
            raise HTTPException(status_code=400, detail="이메일과 비밀번호를 입력해주세요.")
        
        # 사용자 삭제
        if user_auth_service.delete_user(email, password):
            return {
                "success": True,
                "message": "계정이 삭제되었습니다."
            }
        else:
            raise HTTPException(status_code=400, detail="비밀번호가 올바르지 않습니다.")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"사용자 삭제 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="계정 삭제 중 오류가 발생했습니다.")
