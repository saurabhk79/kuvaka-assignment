from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.db.models import User
from app.schemas.chatroom import ChatroomCreate, ChatroomListResponse, ChatroomResponse, MessageCreate, MessageResponse
from app.services.chatroom_service import ChatroomService
from app.api.dependencies import get_current_user
from app.utils.cache import get_cached_data, set_cached_data, invalidate_cache
from app.core.exceptions import ChatroomNotFoundException
from app.tasks.worker import process_gemini_message
from app.utils.rate_limiter import check_rate_limit
from app.db.models import Message

router = APIRouter()

@router.post("/chatroom", response_model=ChatroomResponse, status_code=status.HTTP_201_CREATED)
async def create_chatroom(
    chatroom_data: ChatroomCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    chatroom_service = ChatroomService(db)
    chatroom = await chatroom_service.create_chatroom(current_user.id, chatroom_data)
    await invalidate_cache(f"chatrooms_user_{current_user.id}") 
    return chatroom

@router.get("/chatroom", response_model=list[ChatroomListResponse], status_code=status.HTTP_200_OK)
async def list_chatrooms(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    cache_key = f"chatrooms_user_{current_user.id}"
    cached_chatrooms = await get_cached_data(cache_key)
    if cached_chatrooms:
        print(f"Returning cached chatrooms for user {current_user.id}")
        return [ChatroomListResponse(**c) for c in cached_chatrooms]

    chatroom_service = ChatroomService(db)
    chatrooms = await chatroom_service.get_user_chatrooms(current_user.id)
    chatrooms_data = [ChatroomListResponse.model_validate(c).model_dump() for c in chatrooms] 
    await set_cached_data(cache_key, chatrooms_data, ttl=300) 
    print(f"Fetched chatrooms from DB and cached for user {current_user.id}")
    return chatrooms

@router.get("/chatroom/{chatroom_id}", response_model=ChatroomResponse, status_code=status.HTTP_200_OK)
async def get_chatroom_details(
    chatroom_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    chatroom_service = ChatroomService(db)
    chatroom = await chatroom_service.get_chatroom_by_id(chatroom_id, current_user.id)
    if not chatroom:
        raise ChatroomNotFoundException()
    return chatroom

@router.post("/chatroom/{chatroom_id}/message", response_model=MessageResponse, status_code=status.HTTP_201_CREATED) 
async def send_message_to_chatroom(
    chatroom_id: int,
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await check_rate_limit(current_user.id, db) 

    chatroom_service = ChatroomService(db)
    chatroom = await chatroom_service.get_chatroom_by_id(chatroom_id, current_user.id)
    if not chatroom:
        raise ChatroomNotFoundException()

    
    user_message = await chatroom_service.add_message_to_chatroom(chatroom_id, "user", message_data.content)

    
    chat_history = []
    for msg in chatroom.messages:
        chat_history.append({"role": msg.sender, "content": msg.content})

    
    
    process_gemini_message.delay(chatroom_id, message_data.content, chat_history)

    return user_message