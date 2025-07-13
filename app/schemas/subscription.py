from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.db.models import UserRole

class SubscriptionStatus(BaseModel):
    tier: UserRole
    status: str
    current_period_end: Optional[datetime] = None