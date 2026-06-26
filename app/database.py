import os
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# --- Optimized Engine for Neon ---
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    connect_args={"sslmode": "require"}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- LIVE PHASE FUNCTIONS (New Additions) --- live studio ke liye kuch helper functions jo real-time transcription aur agenda tracking mein madad karenge

def save_live_transcript(episode_id: int, sender: str, content: str):
    """Real-time transcript ko Neon DB mein save karna"""
    db = SessionLocal()
    try:
        query = text("""
            INSERT INTO live_transcripts (episode_id, sender, content) 
            VALUES (:ep_id, :sd, :ct)
        """)
        db.execute(query, {"ep_id": episode_id, "sd": sender, "ct": content})
        db.commit()
    except Exception as e:
        print(f"Error saving transcript: {e}")
        db.rollback()
    finally:
        db.close()

def get_pending_agenda(episode_id: int):
    """Wo topics uthana jo abhi tak cover nahi huye"""
    db = SessionLocal()
    try:
        query = text("""
            SELECT id, topic_name FROM agenda_items 
            WHERE episode_id = :ep_id AND is_covered = False
        """)
        result = db.execute(query, {"ep_id": episode_id})
        return result.fetchall()
    finally:
        db.close()

def update_topic_status(topic_id: int):
    """Topic ko 'Covered' mark karna taake UI meter update ho"""
    db = SessionLocal()
    try:
        query = text("UPDATE agenda_items SET is_covered = True WHERE id = :t_id")
        db.execute(query, {"t_id": topic_id})
        db.commit()
    except Exception as e:
        print(f"Error updating agenda: {e}")
        db.rollback()
    finally:
        db.close()

def get_coverage_percentage(episode_id: int):
    """Flutter UI ke liye percentage nikalna"""
    db = SessionLocal()
    try:
        query = text("""
            SELECT 
                COUNT(*) FILTER (WHERE is_covered = True) * 100.0 / COUNT(*) as percentage 
            FROM agenda_items WHERE episode_id = :ep_id
        """)
        result = db.execute(query, {"ep_id": episode_id}).fetchone()
        return round(result[0], 2) if result[0] else 0
    finally:
        db.close()