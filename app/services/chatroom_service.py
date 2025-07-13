from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.db.models import Chatroom, Message, User
from app.schemas.chatroom import ChatroomCreate, MessageCreate
from app.core.exceptions import ChatroomNotFoundException
from typing import List, Optional
from datetime import datetime

class ChatroomService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_chatroom(self, user_id: int, chatroom_data: ChatroomCreate) -> Chatroom:
        new_chatroom = Chatroom(name=chatroom_data.name, user_id=user_id)
        self.db.add(new_chatroom)
        await self.db.commit()
        await self.db.refresh(new_chatroom)
        return new_chatroom

    async def get_user_chatrooms(self, user_id: int) -> List[Chatroom]:
        stmt = select(Chatroom).where(Chatroom.user_id == user_id).order_by(Chatroom.created_at.desc())
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_chatroom_by_id(self, chatroom_id: int, user_id: int) -> Chatroom  :
        stmt = select(Chatroom).options(selectinload(Chatroom.messages)).where(
            Chatroom.id == chatroom_id, Chatroom.user_id == user_id
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def add_message_to_chatroom(self, chatroom_id: int, sender: str, content: str) -> Message:
        new_message = Message(chatroom_id=chatroom_id, sender=sender, content=content)
        self.db.add(new_message)
        await self.db.commit()
        await self.db.refresh(new_message)
        return new_message