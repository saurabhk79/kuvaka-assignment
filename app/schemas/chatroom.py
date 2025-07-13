from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional

class ChatroomCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)

class MessageCreate(BaseModel):
    content: str = Field(min_length=1)

class MessageResponse(BaseModel):
    id: int
    chatroom_id: int
    sender: str
    content: str
    sent_at: datetime

    class Config:
        from_attributes = True

class ChatroomResponse(BaseModel):
    id: int
    name: str
    user_id: int
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse] = []

    class Config:
        from_attributes = True

class ChatroomListResponse(BaseModel):
    id: int
    name: str
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True