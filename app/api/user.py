from fastapi import APIRouter, Depends, status
from app.db.models import User
from app.schemas.user import UserResponse
from app.api.dependencies import get_current_user

router = APIRouter()

@router.get("/user/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_current_user_details(current_user: User = Depends(get_current_user)):
    return current_user