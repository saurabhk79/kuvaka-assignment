import google.generativeai as genai
from app.core.config import settings
from typing import List, Dict

class GeminiService:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-pro')

    async def get_gemini_response(self, prompt: str, chat_history: List[Dict[str, str]]) -> str:
        try:
            formatted_history = []
            for msg in chat_history:
                formatted_history.append({'role': msg['role'], 'parts': [msg['content']]})

            convo = self.model.start_chat(history=formatted_history)
            response = await convo.send_message_async(prompt)
            return response.text
        except Exception as e:
            print(f"Gemini API error: {e}")
            return "Sorry, I'm unable to generate a response at the moment."