from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.auth import UserRegister, SendOTPRequest, VerifyOTPRequest, Token, PasswordChange, ForgotPasswordRequest, ResetPasswordRequest
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService
from app.api.dependencies import get_current_user
from app.db.models import User

router = APIRouter()

@router.post("/auth/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(user_data: UserRegister, db: AsyncSession = Depends(get_db)):
    auth_service = AuthService(db)
    user = await auth_service.register_user(user_data)
    return user

@router.post("/auth/send-otp", status_code=status.HTTP_200_OK)
async def send_otp(request: SendOTPRequest, db: AsyncSession = Depends(get_db)):
    auth_service = AuthService(db)
    otp_code = await auth_service.send_otp_for_login(request.mobile_number)
    return {"message": "OTP sent successfully (mocked)", "otp_code": otp_code}

@router.post("/auth/verify-otp", response_model=Token, status_code=status.HTTP_200_OK)
async def verify_otp(request: VerifyOTPRequest, db: AsyncSession = Depends(get_db)):
    auth_service = AuthService(db)
    token = await auth_service.verify_otp_and_login(request)
    return token

@router.post("/auth/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(request: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    auth_service = AuthService(db)
    otp_code = await auth_service.forgot_password_send_otp(request)
    return {"message": "OTP sent for password reset (mocked)", "otp_code": otp_code}

@router.post("/auth/reset-password", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def reset_password(request: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    auth_service = AuthService(db)
    user = await auth_service.reset_password_forgot(request)
    return user

@router.post("/auth/change-password", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def change_password(
    password_change: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    auth_service = AuthService(db)
    user = await auth_service.change_password_logged_in(current_user.id, password_change)
    return user