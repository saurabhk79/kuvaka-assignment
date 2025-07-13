from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.models import User, UserRole
from app.schemas.auth import UserRegister, PasswordChange, ResetPasswordRequest
from app.core.security import get_password_hash, verify_password
from app.core.exceptions import UserAlreadyExistsException, InvalidCredentialsException
from app.services.otp_service import OTPService
from app.db.models import DailyUsage
from datetime import datetime, date

class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.otp_service = OTPService(db)

    async def get_user_by_mobile(self, mobile_number: str) -> User:
        stmt = select(User).where(User.mobile_number == mobile_number)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def create_user(self, user_data: UserRegister) -> User:
        existing_user = await self.get_user_by_mobile(user_data.mobile_number)
        if existing_user:
            raise UserAlreadyExistsException()

        hashed_password = get_password_hash(user_data.password)
        new_user = User(
            mobile_number=user_data.mobile_number,
            hashed_password=hashed_password,
            role=UserRole.BASIC.value
        )
        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)

        await self.db.commit()

        return new_user

    async def authenticate_user(self, mobile_number: str, password: str) -> User:
        user = await self.get_user_by_mobile(mobile_number)
        if not user or not verify_password(password, user.hashed_password):
            raise InvalidCredentialsException()
        return user

    async def change_password(self, user_id: int, password_change: PasswordChange) -> User:
        user = await self.db.get(User, user_id)
        if not user or not verify_password(password_change.old_password, user.hashed_password):
            raise InvalidCredentialsException()

        user.hashed_password = get_password_hash(password_change.new_password)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def reset_password_with_otp(self, reset_request: ResetPasswordRequest) -> User:
        is_otp_valid = await self.otp_service.verify_otp(reset_request.mobile_number, reset_request.otp_code)
        if not is_otp_valid:
            raise InvalidCredentialsException()

        user = await self.get_user_by_mobile(reset_request.mobile_number)
        if not user:
            raise InvalidCredentialsException()

        user.hashed_password = get_password_hash(reset_request.new_password)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def get_daily_usage(self, user_id: int) -> DailyUsage:
        today = datetime.utcnow().date()
        stmt = select(DailyUsage).where(
            DailyUsage.user_id == user_id,
            func.date(DailyUsage.date) == today
        )
        result = await self.db.execute(stmt)
        usage = result.scalars().first()
        if not usage:
            usage = DailyUsage(user_id=user_id, date=today, prompt_count=0)
            self.db.add(usage)
            await self.db.commit()
            await self.db.refresh(usage)
        return usage

    async def increment_daily_usage(self, user_id: int):
        usage = await self.get_daily_usage(user_id)
        usage.prompt_count += 1
        await self.db.commit()
        await self.db.refresh(usage)