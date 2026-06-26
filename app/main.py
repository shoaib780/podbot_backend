# app/main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.database import engine, Base
from app.api import episodes, live_studio
import logging
from fastapi.staticfiles import StaticFiles

# Sab se niche routers ke baad ye line add karein:


# Logging setup (Debug karne ke liye zaroori hai)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Neon DB mein tables auto-create karna (live_transcripts table bhi yahi banayega)
try:
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Database tables synced successfully with Neon Postgres.")
except Exception as e:
    logger.error(f"❌ Database sync error: {e}")

app = FastAPI(
    title="PodBot AI Backend",
    description="Professional AI-Powered Podcast Assistant Backend",
    version="1.0.0"
)

# --- Middleware ---
# CORS: Mobile app aur emulators ke connection ke liye zaroori hai
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],

) 
# --- Global Error Handler ---
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"message": "Internal Server Error", "detail": str(exc)},
    )

# --- Routers Registration ---
# Phase 1: Pre-Interview (Strategy, PDF, Questions)
app.include_router(episodes.router, prefix="/api/v1", tags=["Episodes & Strategy"])

# Phase 2: Live Interview (WebSockets, Transcription, Topic Tracking)
# Iska prefix aur tags add kar diye hain
app.include_router(live_studio.router, prefix="/api/v1", tags=["Live Studio (WebSockets)"])



# --- Health Check Endpoints ---
@app.get("/", tags=["Health Check"])
def read_root():
    """Server status check karne ke liye"""
    return {
        "status": "PodBot Backend is Live",
        "database": "Connected to Neon PostgreSQL",
        "api_version": "v1"
    }

# --- Startup Message ---
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 PodBot Backend has started successfully!")



import os
from fastapi import FastAPI, HTTPException
from google.oauth2 import service_account
from googleapiclient.discovery import build

# --- CONFIGURATION ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Ab ye main.py ke barabar wali hi service_account.json uthayega
SERVICE_ACCOUNT_FILE = os.path.join(CURRENT_DIR, 'service_account.json')

# Testing ke liye print karwa lein (Sirf debugging ke liye)
if not os.path.exists(SERVICE_ACCOUNT_FILE):
    print(f"❌ File abhi bhi nahi mili is path par: {SERVICE_ACCOUNT_FILE}")
else:
    print(f"✅ File mil gayi! Path: {SERVICE_ACCOUNT_FILE}")
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

# Apne folder ka ID yahan paste karein (URL se nikaal kar)
FOLDER_ID = '17gHLyK_S6PQakHguEcWjQNlG8BJbHsHw' 

def get_drive_service():
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        print(f"Error: {SERVICE_ACCOUNT_FILE} nahi mili!")
        return None
    
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return build('drive', 'v3', credentials=creds)

# --- ROUTE FOR PODCAST LIBRARY ---
@app.get("/fetch-reports")
async def fetch_reports():
    service = get_drive_service()
    if not service:
        raise HTTPException(status_code=500, detail="Credentials file missing")

    try:
        # Drive Query: Sirf PDF files, trashed na hon, aur specific folder mein hon
        query = f"'{FOLDER_ID}' in parents and mimeType='application/pdf' and trashed=false"
        
        results = service.files().list(
            q=query,
            fields="files(id, name, webViewLink, createdTime)",
            orderBy="createdTime desc" # Latest reports sab se upar
        ).execute()

        items = results.get('files', [])
        return items

    except Exception as e:
        print(f"Drive API Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

app.mount("/static", StaticFiles(directory="static"), name="static")
# Run command (Terminal ke liye):
# python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload