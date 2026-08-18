import os
import asyncio

from aiortc import MediaStreamError, MediaStreamTrack
from av.audio.frame import AudioFrame
from av.audio.resampler import AudioResampler
from deepgram import AsyncDeepgramClient
from deepgram.core.events import EventType
from dotenv import load_dotenv

from services.deepgram import DeepgramSession
from services.gemini import GeminiService
from services.voice_session import VoiceSession

from rich.console import Console
from rich.markdown import Markdown

gemini = GeminiService()

load_dotenv()

deepgram_client = AsyncDeepgramClient(
    api_key=os.getenv("DEEPGRAM_API_KEY")
)

async def process_audio(track: MediaStreamTrack):
    session = DeepgramSession(deepgram_client)
    voice_session = VoiceSession(gemini.client)

    connection = await session.connect()

    send_task = asyncio.create_task(
        send_audio(track, connection)
    )

    receive_task = asyncio.create_task(
        receive_transcripts(connection, voice_session)
    )

    try:
        # The audio task represents the lifetime of the call.
        await send_task

    except Exception as e:
        print(f"Audio processing error: {e}")

    finally:
        receive_task.cancel()

        try:
            await receive_task
        except asyncio.CancelledError:
            pass

        await session.close()


async def send_audio(track: MediaStreamTrack, connection):
    resampler = AudioResampler(
        format="s16",
        layout="mono",
        rate=16000,
    )

    try:
        while True:
            frame = await track.recv()

            if not isinstance(frame, AudioFrame):
                continue

            resampled_frames = resampler.resample(frame)

            if not isinstance(resampled_frames, list):
                resampled_frames = [resampled_frames]

            for resampled_frame in resampled_frames:
                audio_bytes = bytes(resampled_frame.planes[0])


                await connection.send_media(audio_bytes)

    except MediaStreamError:
        print("Audio track ended")


async def receive_transcripts(connection, voice_session: VoiceSession):

    def on_open(event):
        print("Deepgram connection opened")

    def on_close(event):
        print("Deepgram connection closed:", event)

    def on_error(error):
        print("Deepgram error:", error)

    def on_message(message):
        if message.type != "Results":
            return

        transcript = message.channel.alternatives[0].transcript

        if not transcript:
            return

        if message.is_final:
            voice_session.add_transcript(transcript)

        if message.speech_final:
            full_transcript = voice_session.get_transcript()

            if full_transcript:
                print(f"USER: {full_transcript}")

                asyncio.create_task(
                    handle_user_message(
                        full_transcript,
                        voice_session,
                    )
                )

            voice_session.clear_transcript()


    connection.on(EventType.OPEN, on_open)
    connection.on(EventType.CLOSE, on_close)
    connection.on(EventType.ERROR, on_error)
    connection.on(EventType.MESSAGE, on_message)

    await connection.start_listening()


async def handle_user_message(message: str, voice_session: VoiceSession):
    response = await voice_session.generate_response(message)

    print(f"AI: {response}")