import numpy as np
import io
import wave
import json
import os
import asyncio  # Background tasks ke liye lazmi hai
from groq import Groq
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import SessionLocal, get_db
from app.models.table_structure import Episode
from app.models.transcript import Transcript 
from app.services.live_screen_ser import suggest_follow_up 

router = APIRouter()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

class ConnectionManager:
    def __init__(self):
        self.host_socket = None
        self.last_h_energy = 0
        self.last_g_energy = 0

    async def send_to_host(self, data):
        if self.host_socket:
            try:
                await self.host_socket.send_json(data)
            except:
                self.host_socket = None

manager = ConnectionManager()

# --- Helper Functions ---
def get_energy(audio_np):
    return np.sqrt(np.mean(audio_np**2)) if len(audio_np) > 0 else 0

def create_wav_buffer(audio_bytes):
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(audio_bytes)
    buf.seek(0)
    return buf

# --- Background Processing Wrapper ---
async def handle_async_processing(audio_data, episode_id, sender, websocket):
    """
    Ye function background mein chalega taake main loop block na ho.
    """
    db = SessionLocal()
    try:
        # 1. Transcription Call (Whisper)
        wav_file = create_wav_buffer(audio_data)
        raw_text = client.audio.transcriptions.create(
            file=("audio.wav", wav_file.read()),
            model="whisper-large-v3",
            language="ur",
            response_format="text"
        ).strip()

        if raw_text and len(raw_text) >= 3:
            # 2. Database mein foran save karein
            new_entry = Transcript(episode_id=episode_id, sender=sender, content=raw_text)
            db.add(new_entry)
            db.commit()

            # 3. Flutter UI ko foran text bhejien
            update_packet = {
                "type": "TRANSCRIPTION",
                "sender": sender, 
                "text": raw_text
            }
            await manager.send_to_host(update_packet)
            if sender == "Guest": # Guest ka text guest screen par bhi dikhayein
                await websocket.send_json(update_packet)

            # 4. Sirf Guest ke liye Follow-up mangwayen (Agar text lamba ho)
            if sender == "Guest" and len(raw_text) > 15:
                episode = db.query(Episode).filter(Episode.id == episode_id).first()
                if episode:
                    bio = episode.guest_bio_text if episode.guest_bio_text else "No bio available"
                    # Llama API call (Roman Urdu Suggestion)
                    follow_up = suggest_follow_up(raw_text, bio)
                    
                    if follow_up:
                        await manager.send_to_host({
                            "type": "SUGGESTION",
                            "text": follow_up
                        })
    except Exception as e:
        print(f"Async Processing Error: {e}")
    finally:
        db.close()

# --- WebSocket Endpoints ---

@router.websocket("/ws/host-mic/{episode_id}")
async def host_mic(websocket: WebSocket, episode_id: int):
    await websocket.accept()
    manager.host_socket = websocket
    audio_buffer = bytearray()
    
    try:
        while True:
            data = await websocket.receive_bytes()
            audio_buffer.extend(data)
            
            # 5 Seconds audio block
            if len(audio_buffer) >= 160000:
                current_chunk = bytes(audio_buffer)
                audio_buffer = bytearray() # Buffer foran khali karein taake audio skip na ho
                
                audio_np = np.frombuffer(current_chunk, dtype=np.int16).astype(np.float32) / 32768.0
                manager.last_h_energy = get_energy(audio_np)
                
                # Voice Activity Detection
                if manager.last_h_energy > 0.008:
                    # Background task create karein (Blocking khatam)
                    asyncio.create_task(handle_async_processing(current_chunk, episode_id, "Host", websocket))
                    
    except Exception as e:
        print(f"Host WebSocket Error: {e}")

@router.websocket("/ws/guest-mic/{episode_id}")
async def guest_mic(websocket: WebSocket, episode_id: int):
    await websocket.accept()
    audio_buffer = bytearray()
    
    try:
        while True:
            data = await websocket.receive_bytes()
            audio_buffer.extend(data)
            
            if len(audio_buffer) >= 160000:
                current_chunk = bytes(audio_buffer)
                audio_buffer = bytearray() # Buffer reset
                
                audio_np = np.frombuffer(current_chunk, dtype=np.int16).astype(np.float32) / 32768.0
                manager.last_g_energy = get_energy(audio_np)
                
                if manager.last_g_energy > 0.008:
                    # Background task for Guest
                    asyncio.create_task(handle_async_processing(current_chunk, episode_id, "Guest", websocket))
                    
    except Exception as e:
        print(f"Guest WebSocket Error: {e}")

# --- Sync Endpoints (In mein koi tabdeeli nahi ki) ---
@router.get("/episodes/latest/active")
def get_latest_episode_id(db: Session = Depends(get_db)):
    latest = db.query(Episode).order_by(Episode.id.desc()).first()
    return {"id": latest.id if latest else 1}

@router.get("/episodes/{episode_id}")
def get_episode_details(episode_id: int, db: Session = Depends(get_db)):
    episode = db.query(Episode).filter(Episode.id == episode_id).first()
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")
    return {
        "id": episode.id,
        "title": episode.title,
        "agenda": episode.agenda,
        "ai_questions": episode.ai_questions,
        "guest_bio": episode.guest_bio_text
    }