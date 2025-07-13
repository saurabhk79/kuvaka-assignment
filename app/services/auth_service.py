from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from app.core.security import create_access_token
from app.schemas.auth import UserRegister, SendOTPRequest, VerifyOTPRequest, PasswordChange, ForgotPasswordRequest, ResetPasswordRequest, Token
from app.db.models import User
from app.services.user_service import UserService
from app.services.otp_service import OTPService
from app.core.exceptions import InvalidCredentialsException, OTPVerificationFailedException

class AuthService:
    def __init__(self, db: AsyncSession):
        self.user_service = UserService(db)
        self.otp_service = OTPService(db)

    async def register_user(self, user_data: UserRegister) -> User:
        return await self.user_service.create_user(user_data)

    async def send_otp_for_login(self, mobile_number: str) -> str:
        user = await self.user_service.get_user_by_mobile(mobile_number)
        if not user:
            pass
        return await self.otp_service.generate_and_store_otp(mobile_number)

    async def verify_otp_and_login(self, otp_request: VerifyOTPRequest) -> Token:
        is_otp_valid = await self.otp_service.verify_otp(otp_request.mobile_number, otp_request.otp_code)
        if not is_otp_valid:
            raise OTPVerificationFailedException()

        user = await self.user_service.get_user_by_mobile(otp_request.mobile_number)
        if not user:
            raise InvalidCredentialsException()

        access_token = create_access_token(data={"sub": str(user.id)})
        return Token(access_token=access_token)

    async def forgot_password_send_otp(self, request: ForgotPasswordRequest) -> str:
        user = await self.user_service.get_user_by_mobile(request.mobile_number)
        if not user:
            pass
        return await self.otp_service.generate_and_store_otp(request.mobile_number)

    async def change_password_logged_in(self, user_id: int, password_change: PasswordChange) -> User:
        return await self.user_service.change_password(user_id, password_change)

    async def reset_password_forgot(self, reset_request: ResetPasswordRequest) -> User:
        return await self.user_service.reset_password_with_otp(reset_request)