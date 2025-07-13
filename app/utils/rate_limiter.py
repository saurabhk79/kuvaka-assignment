from fastapi import HTTPException, status
from app.db.models import UserRole
from app.services.user_service import UserService
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, date

BASIC_TIER_PROMPT_LIMIT = 5

async def check_rate_limit(user_id: int, db: AsyncSession):
    user_service = UserService(db)
    user_data = await user_service.db.get(type=type('User', (object,), {}),ident=user_id) 
    if not user_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user_data.role == UserRole.BASIC.value:
        daily_usage = await user_service.get_daily_usage(user_id)
        if daily_usage.prompt_count >= BASIC_TIER_PROMPT_LIMIT:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Daily message limit exceeded for your Basic tier. Upgrade to Pro for more."
            )
        await user_service.increment_daily_usage(user_id)