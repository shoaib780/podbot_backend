#table ka structure define karte hain jo Neon mein "Episodes" ke naam se banega.
#SQLAlchemy is data ko SQL query mein convert kar ke Neon Postgres mein insert kar deta hai.
#Database ko "Smart" banaya taake wo Tone aur AI Strategy save kar sakay.
#sqlalchemy akk toolkit hy  jis min pathon code sy database sy rabta kiya jata hy
from sqlalchemy import Column, Integer, String, JSON, Text, Boolean
from app.database import Base

class Episode(Base):
    __tablename__ = "episodes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    
    # Names
    guest_name = Column(String, nullable=True)
    guest_email = Column(String, nullable=True)
    host_name = Column(String, nullable=True)
    host_email = Column(String, nullable=True)

    
    # Flexible Inputs
    guest_linkedin = Column(String, nullable=True)
    guest_bio_text = Column(Text, nullable=True) # PDF ka text yahan jayega
    
    # Strategy Fields
    tone = Column(String, default="Professional")
    agenda = Column(JSON, nullable=True)           
    ai_questions = Column(JSON, nullable=True)     
    
    # Phase 3: AI Intelligence Report
    intelligence_report = Column(JSON, nullable=True)
    
    # Status & Files
    script_pdf_path = Column(String, nullable=True) # Guest ki upload ki hui PDF
    
    # --- YAHAN NAYA COLUMN ADD KIYA HAI ---
    pdf_report_path = Column(String, nullable=True) # AI ki generate ki hui Professional Report
    # --------------------------------------

    status = Column(String, default="draft") # draft, active, completed