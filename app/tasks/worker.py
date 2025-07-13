from celery import Celery
from app.core.config import settings
from app.services.gemini_service import GeminiService
from app.db.session import async_session
from app.services.chatroom_service import ChatroomService

celery_app = Celery('tasks', broker=settings.CELERY_BROKER_URL, backend=settings.CELERY_RESULT_BACKEND)

@celery_app.task
async def process_gemini_message(chatroom_id: int, user_message_content: str, chat_history: list):
    gemini_service = GeminiService()
    async with async_session() as db:
        chatroom_service = ChatroomService(db)
        try:
            gemini_response = await gemini_service.get_gemini_response(user_message_content, chat_history)
            await chatroom_service.add_message_to_chatroom(chatroom_id, "ai", gemini_response)
        except Exception as e:
            print(f"Error processing Gemini message for chatroom {chatroom_id}: {e}")
            await chatroom_service.add_message_to_chatroom(
                chatroom_id,
                "ai",
                "Sorry, I couldn't process your request right now. Please try again later."
            )