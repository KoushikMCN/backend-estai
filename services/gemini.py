import os
from dotenv import load_dotenv

from google import genai

load_dotenv()

class GeminiService:
    def __init__(self):
        self.client = genai.Client(
            api_key=os.getenv("GEMINI_API_KEY")
        )

    async def generate(self, prompt: str) -> str:
        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )

        text = response.text
        if text is None:
            raise RuntimeError("Gemini returned no text.")
        
        return text