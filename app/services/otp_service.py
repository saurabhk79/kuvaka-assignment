import random
import string
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.models import OTP
from app.core.exceptions import OTPVerificationFailedException

class OTPService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_and_store_otp(self, mobile_number: str) -> str:
        otp_code = ''.join(random.choices(string.digits, k=6))
        expires_at = datetime.utcnow() + timedelta(minutes=5) 

        
        new_otp = OTP(mobile_number=mobile_number, otp_code=otp_code, expires_at=expires_at)
        self.db.add(new_otp)
        await self.db.commit()
        await self.db.refresh(new_otp)
        return otp_code

    async def verify_otp(self, mobile_number: str, otp_code: str) -> bool:
        stmt = select(OTP).where(
            OTP.mobile_number == mobile_number,
            OTP.otp_code == otp_code,
            OTP.expires_at > datetime.utcnow(),
            OTP.is_verified == False
        ).order_by(OTP.created_at.desc()) 

        result = await self.db.execute(stmt)
        otp_record = result.scalars().first()

        if otp_record:
            otp_record.is_verified = True
            await self.db.commit()
            return True
        raise OTPVerificationFailedException()