#Frontend (Flutter) se jo data aayega, usko validate karne ke liye Pydantic use karenge.
from pydantic import BaseModel
from typing import Optional, List

class EpisodeCreate(BaseModel):
    title: str
    guest_linkedin: Optional[str] = None
    agenda: Optional[List[str]] = None
    # Inhein add karein taake FastAPI data accept kare
    guest_name: Optional[str] = None
    guest_email: Optional[str] = None
    host_name: Optional[str] = None
    host_email: Optional[str] = None

class EpisodeResponse(EpisodeCreate):
    id: int
    status: str
    
    class Config:
        from_attributes = True