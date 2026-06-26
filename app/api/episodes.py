#Endpoints 
#Backend Mein API Ko Endpoint Kehte Hain
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
#Database se data lena / save karna
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.table_structure import Episode
from app.services.pdf_generator import generate_professional_pdf
from app.services.pre_screen_ser import extract_text_from_pdf, generate_production_strategy , refresh_specific_agenda_item,regenerate_single_question
import json
from sqlalchemy.orm.attributes import flag_modified # Ye top par import karein
from app import models  # Models ka error khatam karne ke liye
 # PDF function ka error khatam karne ke liye
import json # JSON load/dump ke liye
# Purane imports hata kar ye likhein:
from app.models.table_structure import Episode
from app.models.transcript import Transcript
from fastapi import Request

router = APIRouter()
#Ye API(endpoint) episode strategy banati hai
@router.post("/episodes/process-strategy")
async def process_episode_strategy(
    title: str = Form(...),
    tone: str = Form(...),
    # --- Flutter se aane wali nayi fields ---
    host_name: str = Form("Habil Ishaq"), 
    host_email: str = Form(...),        # Flutter se Host ki email
    guest_name: str = Form(...),        # Flutter se Guest ka naam
    guest_email: str = Form(...),       # Flutter se Guest ki email
    # ---------------------------------------
    pdf_file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    try:
        # 1. PDF Content Extract karna
        pdf_content = await pdf_file.read()
        raw_text = extract_text_from_pdf(pdf_content)
        
        # 2. AI se Strategy mangwana
        ai_json_str = generate_production_strategy(raw_text, tone)
        
        # 3. JSON Parsing with safety
        try:
            strategy = json.loads(ai_json_str)
        except Exception as json_err:
            print(f"AI returned invalid JSON: {ai_json_str}")
            raise HTTPException(status_code=500, detail="AI response was not valid JSON")

        # 4. DB mein save karna (Ab sab kuch dynamic hai)
        db_episode = Episode(
            title=title,
            tone=tone,
            host_name=host_name,      # Flutter se aya hua naam
            host_email=host_email,    # Flutter se ayi hui email
            guest_name=guest_name,    # Flutter se aya hua guest naam
            guest_email=guest_email,  # Flutter se ayi hui guest email
            guest_bio_text=raw_text,
            agenda=strategy.get("agenda"),
            ai_questions=strategy.get("questions"),
            status="draft"            # Initial status
        )
        
        db.add(db_episode)
        db.commit()
        db.refresh(db_episode)
        
        # 5. Response wapis bhejte waqt bhi naya data shamil karein
        return {
            "id": db_episode.id,
            "guest_name": db_episode.guest_name,
            "guest_email": db_episode.guest_email,
            "host_name": db_episode.host_name,
            "host_email": db_episode.host_email,
            "agenda": db_episode.agenda,
            "questions": db_episode.ai_questions
        }
    except Exception as e:
        print(f"ERROR in process-strategy: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

#API 2 – Toggle Question
@router.patch("/episodes/{episode_id}/toggle-question/{question_id}")
def toggle_question_selection(episode_id: int, question_id: int, db: Session = Depends(get_db)):
    #Episode database se find kar raha hai
    episode = db.query(Episode).filter(Episode.id == episode_id).first()
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")

    # Local list banana zaroori hai
    updated_questions = list(episode.ai_questions)
    
    found = False
    for q in updated_questions:
        if q['id'] == question_id:
            # Agar selected true tha to false kar do, aur vice versa
            current_status = q.get('selected', False)
            q['selected'] = not current_status
            found = True
            break
    
    if not found:
        raise HTTPException(status_code=404, detail="Question ID not found")

    episode.ai_questions = updated_questions
    # YE LINE ZAROORI HAI: SQLAlchemy ko batane ke liye ke JSON change hua hai
    flag_modified(episode, "ai_questions") 
    
    db.commit()
    db.refresh(episode)
    return {"status": "updated", "questions": episode.ai_questions}

#API 3 – Refresh Agenda Segment
@router.post("/episodes/{episode_id}/refresh-agenda")
def refresh_agenda_segment(episode_id: int, segment_index: int, db: Session = Depends(get_db)):
    episode = db.query(Episode).filter(Episode.id == episode_id).first()
    
    # AI se naya content mangwana
    segment = episode.agenda[segment_index]
    new_desc = refresh_specific_agenda_item(episode.title, segment['title'], episode.tone)
    
    # Database update karna
    new_agenda = list(episode.agenda)
    new_agenda[segment_index]['description'] = new_desc
    episode.agenda = new_agenda
    
    db.commit()
    return {"status": "refreshed", "new_description": new_desc}


from sqlalchemy.orm.attributes import flag_modified

@router.post("/episodes/{episode_id}/refresh-question/{question_id}")
def refresh_single_question(episode_id: int, question_id: int, db: Session = Depends(get_db)):
    episode = db.query(Episode).filter(Episode.id == episode_id).first()
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")

    updated_questions = list(episode.ai_questions)
    found = False

    for q in updated_questions:
        if q['id'] == question_id:
            # AI se naya sawal mangwana
            new_text = regenerate_single_question(episode.title, q['text'], episode.tone)
            q['text'] = new_text
            # Reset selection when refreshed
            q['selected'] = True 
            found = True
            break
            
    if not found:
        raise HTTPException(status_code=404, detail="Question ID not found")

    episode.ai_questions = updated_questions
    flag_modified(episode, "ai_questions")
    
    db.commit()
    return {"status": "refreshed", "new_question": new_text}
    

    from fastapi.responses import FileResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os

# 1. Mazeed Sawal Add Karne ka Endpoint
@router.post("/episodes/{episode_id}/load-more")
def load_more_questions(episode_id: int, db: Session = Depends(get_db)):
    episode = db.query(Episode).filter(Episode.id == episode_id).first()
    
    # AI se 3 naye sawal mangwana (Groq Logic)
    # Note: Yahan aap refresh_question wali logic hi use karenge mazeed questions ke liye
    new_questions = [
        "How do you see this industry evolving in the next 5 years?",
        "What was the biggest challenge in your latest project?",
        "What advice would you give to someone starting out today?"
    ]
    
    updated_questions = list(episode.ai_questions)
    last_id = max([q['id'] for q in updated_questions]) if updated_questions else 0
    
    for text in new_questions:
        last_id += 1
        updated_questions.append({"id": last_id, "text": text, "selected": True})
        
    episode.ai_questions = updated_questions
    flag_modified(episode, "ai_questions")
    db.commit()
    return {"status": "added", "questions": episode.ai_questions}

# 2. PDF Report Generate karne ka Endpoint
@router.get("/episodes/{episode_id}/download-report")
def download_episode_report(episode_id: int, db: Session = Depends(get_db)):
    episode = db.query(Episode).filter(Episode.id == episode_id).first()
    file_path = f"report_{episode_id}.pdf"
    
    c = canvas.Canvas(file_path, pagesize=letter)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, 750, f"Podcast Strategy: {episode.title}")
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(100, 720, "Agenda Overview:")
    c.setFont("Helvetica", 10)
    y = 700
    for item in episode.agenda:
        c.drawString(120, y, f"- {item['time']} {item['title']}: {item['description'][:80]}...")
        y -= 20
        
    c.setFont("Helvetica-Bold", 12)
    c.drawString(100, y-20, "Selected Interview Questions:")
    c.setFont("Helvetica", 10)
    y -= 40
    for q in episode.ai_questions:
        if q.get('selected', False):
            c.drawString(120, y, f"? {q['text'][:90]}")
            y -= 20
            
    c.save()
    return FileResponse(file_path, media_type='application/pdf', filename=f"{episode.title}_Strategy.pdf")




#(p_i_interviews endpoint) Isay interview finalize karne ke baad call kiya jayega taake AI se complete intelligence report generate ho jaye, jisme summary, fact-check, sentiment analysis, chapters, aur social media hooks sab kuch hoga. Ye report episode ke saath database mein save ho jayegi.
from app.services.analytics_ser import generate_complete_intelligence_report
from app.models.transcript import Transcript

@router.post("/{episode_id}/finalize")
async def finalize_episode(episode_id: int, db: Session = Depends(get_db)):
    """
    Interview khatam hone par ye route saari intelligence generate karega.
    """
    # 1. Episode aur uske saare transcripts fetch karna
    episode = db.query(Episode).filter(Episode.id == episode_id).first()
    if not episode:
        raise HTTPException(status_code=404, detail="Episode nahi mila")

    transcripts = db.query(Transcript).filter(Transcript.episode_id == episode_id).order_by(Transcript.id).all()

    if not transcripts:
        raise HTTPException(status_code=400, detail="Transcript empty hai, report generate nahi ho sakti.")

    # 2. Complete Master Intelligence Report generate karna
    # Yahan humne database se episode ka dynamic data pass kiya hai
    report_data = generate_complete_intelligence_report(
        transcripts, 
        {
            "title": episode.title, 
            "host": episode.host_name, 
            "guest": episode.guest_name
        },
        episode.agenda
    )

    if report_data:
        # 3. Database mein intelligence_report column update karna
        episode.intelligence_report = report_data
        episode.status = "completed"
        db.commit()

        # --- ZARURI DYNAMIC DATA ATTACH KARNA ---
        # Ye data Flutter ke 'IntelligenceProvider' aur 'FINISH' button ke liye lazmi hai
        report_data["id"] = episode.id
        report_data["guest_name"] = episode.guest_name
        report_data["guest_email"] = episode.guest_email
        report_data["host_name"] = episode.host_name
        report_data["host_email"] = episode.host_email
        # ----------------------------------------
        
        return {
            "status": "success", 
            "message": "Intelligence Report ready hai",
            "id": episode.id,
            "data": report_data # Ab is data mein emails shamil hain
        }
    
    raise HTTPException(status_code=500, detail="AI Analysis fail ho gayi.")


@router.get("/episodes/{episode_id}/export-pdf")
async def export_episode_pdf(episode_id: int, request: Request, db: Session = Depends(get_db)):
    episode = db.query(Episode).filter(Episode.id == episode_id).first()
    if not episode:
        return {"error": "Episode not found"}

    # --- ISAY AISE UPDATE KAREIN ---
    intelligence = None
    try:
        if episode.intelligence_report:
            intelligence = json.loads(episode.intelligence_report) if isinstance(episode.intelligence_report, str) else episode.intelligence_report
        transcripts = db.query(Transcript).filter(Transcript.episode_id == episode_id).all()
    except Exception as e:
        return {"error": f"Data processing error: {str(e)}"}

    if not intelligence:
        return {"error": "Intelligence report not ready yet"}
    
 # 3. PDF Generate karein
    try:
            # result dictionary hasil karein
            result = generate_professional_pdf(episode.title, intelligence, transcripts)
            
            if result.get('status') == 'success':
                # String path nikaalein taake database crash na ho
                asli_file_path = result.get('full_path') or result.get('file_path')
                
                # Database update
                episode.pdf_report_path = asli_file_path
                db.commit()

                # URL banana
                base_url = str(request.base_url).rstrip('/')
                final_filename = result.get('pdf_url') or result.get('filename')
                
                # Double URL check: Agar generator ne poora URL diya hai toh wahi bhejien
                if final_filename and str(final_filename).startswith('http'):
                    return {"pdf_url": final_filename}
                else:
                    return {"pdf_url": f"{base_url}/static/reports/{final_filename}"}
            else:
                return {"error": f"PDF Generation failed: {result.get('message')}"}

    except Exception as e:
            db.rollback()
            print(f"DEBUG ERROR: {str(e)}")
            return {"error": f"Internal Server Error: {str(e)}"}








# sary episode ki list nikalne ka endpoint, jisme har episode ke saath uski intelligence report ki accuracy percentage bhi dikhayenge taake host ko pata chale ke AI analysis kitna accurate tha.
from fastapi import APIRouter, Depends, Response


@router.get("/all-summaries")
def get_home_episodes(db: Session = Depends(get_db)):
    # 1. Database se episodes fetch karein
    episodes = db.query(Episode).order_by(Episode.id.desc()).all()
    
    home_data = []
    
    for ep in episodes:
        # Default values (Agar database mein data na ho toh ye show hongi)
        accuracy = 0
        duration = "00:00 mins"
        status = "Draft"
        
        # 2. Intelligence Report Parsing (Safe Method)
        if ep.intelligence_report:
            try:
                # Flexible parsing: Check if it's already a dict or a string
                report = ep.intelligence_report
                if isinstance(report, str):
                    report = json.loads(report)
                
                # Nested data nikalna
                accuracy = report.get('fact_check', {}).get('accuracy_percentage', 0)
                duration = report.get('metadata', {}).get('duration', "00:00 mins")
                status = "Report Ready"
            except:
                pass # Agar report kharab hai toh default values hi rahengi

        # 3. Data packing (Ensure strings for null columns)
        home_data.append({
            "id": int(ep.id),
            "title": str(ep.title) if ep.title else "Untitled Episode",
            "guest": str(ep.guest_name) if ep.guest_name else "Unknown Guest",
            "status": status,
            "accuracy": int(accuracy),
            "duration": str(duration),
            "date": f"Episode #{ep.id}"
        })
    
    # 4. CRITICAL: Response ko manually JSON mein convert karke bhejna
    # Is se FastAPI ka automatic validation (jo 422 error de raha hai) bypass ho jayega
    return Response(
        content=json.dumps(home_data),
        media_type="application/json"
    )



# ya route all episodes k lya jo in ki itelligence report ki accuracy percentage bhi dikhayega taake host ko pata chale ke AI analysis kitna accurate tha.
@router.get("/{episode_id}/data")
def get_intelligence_data(episode_id: int, db: Session = Depends(get_db)):
    # 1. Database se episode fetch karein
    episode = db.query(Episode).filter(Episode.id == episode_id).first()
    
    if not episode:
        raise HTTPException(status_code=404, detail="Episode nahi mila")

    # 2. Check karein ke kya report DB mein mojud hai
    if not episode.intelligence_report:
        raise HTTPException(status_code=400, detail="Is episode ki report abhi generate nahi hui")

    # 3. Report ko parse karein (Flexible parsing)
    report_data = episode.intelligence_report
    if isinstance(report_data, str):
        try:
            report_data = json.loads(report_data)
        except Exception as e:
            raise HTTPException(status_code=500, detail="Report format kharab hai")

    # 4. Same structure return karein jo finalize route karta hai
    # Taake Flutter UI ko lage ke ye abhi generate hui hai
    return {
        "status": "success", 
        "message": "Intelligence Report fetched from DB",
        "id": episode.id,
        "data": report_data  # Ye wahi exact JSON hai jo AI ne banaya tha
    }