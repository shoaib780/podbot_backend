from sqlalchemy import Column, Integer, Text, ForeignKey, DateTime, String
from app.database import Base
from datetime import datetime

class Transcript(Base):
    __tablename__ = "live_transcripts"
    id = Column(Integer, primary_key=True, index=True)
    episode_id = Column(Integer, ForeignKey("episodes.id"))
    sender = Column(String) # 'Host' or 'Guest'
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)