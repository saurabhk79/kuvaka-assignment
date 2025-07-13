from pydantic import BaseModel
from datetime import datetime
from app.db.models import UserRole

class UserResponse(BaseModel):
    id: int
    mobile_number: str
    role: UserRole
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True