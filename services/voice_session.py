from google import genai


class VoiceSession:
    def __init__(self, gemini_client: genai.Client):
        self.transcript_buffer: list[str] = []

        self.chat = gemini_client.aio.chats.create(
            model="gemini-2.5-flash",
        )

    def add_transcript(self, transcript: str):
        self.transcript_buffer.append(transcript)

    def get_transcript(self) -> str:
        return " ".join(self.transcript_buffer)

    def clear_transcript(self):
        self.transcript_buffer.clear()

    async def generate_response(self, message: str) -> str:
        response = await self.chat.send_message(message)

        if response.text is None:
            raise RuntimeError("Gemini returned no text.")

        return response.text