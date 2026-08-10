from deepgram import AsyncDeepgramClient


class DeepgramSession:
    def __init__(self, client: AsyncDeepgramClient):
        self.client = client
        self.context = None
        self.connection = None

    async def connect(self):
        self.context = self.client.listen.v1.connect(
            model="nova-3",
            language="en-US",
            encoding="linear16",
            sample_rate=16000,
            channels=1,
            smart_format=True,
            interim_results=True,
            punctuate=True,
            endpointing=300,
        )

        self.connection = await self.context.__aenter__()

        return self.connection

    async def close(self):
        if self.context:
            await self.context.__aexit__(None, None, None)

        self.context = None
        self.connection = None