from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from aiortc import RTCPeerConnection, RTCSessionDescription

app = FastAPI()

peer_connections: set[RTCPeerConnection] = set()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to estai!!"}

@app.post("/webrtc/offer")
async def webrtc_offer(request: Request):
    body = await request.json()

    offer = RTCSessionDescription(
        sdp=body["sdp"],
        type=body["type"],
    )

    pc = RTCPeerConnection()
    peer_connections.add(pc)

    @pc.on("track")
    def on_track(track):
        print(f"Received track: {track.kind}")

    await pc.setRemoteDescription(offer)

    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return {
        "sdp": pc.localDescription.sdp,
        "type": pc.localDescription.type,
    }