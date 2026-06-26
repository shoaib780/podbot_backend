from fpdf import FPDF
import os
import re
import json
import time


def clean_text(text):
    """Urdu ya non-ASCII characters ko ignore karke sirf English text filter karta hai"""
    if not text:
        return ""
    # Standard fonts (Arial) ke liye ASCII cleaning lazmi hai taake crash na ho
    return text.encode('ascii', 'ignore').decode('ascii')

class PodBotProfessionalReport(FPDF):
    def header(self):
        # Cover page (Page 1) par blue header nahi dikhana
        if self.page_no() > 1:
            self.set_fill_color(0, 51, 102)  # Professional Navy Blue
            self.rect(0, 0, 210, 15, 'F')
            self.set_font('Arial', 'B', 10)
            self.set_text_color(255, 255, 255)
            self.set_y(5)
            self.cell(0, 5, 'PODBOT INTELLIGENCE CASE STUDY', 0, 1, 'C')
            self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        # Footer Page Number
        self.cell(0, 10, f'Page {self.page_no()} | Confidential Analysis - PodBot AI', 0, 0, 'C')

def generate_professional_pdf(episode_title, intelligence, transcripts):
    # Directory ensure karein
    os.makedirs('static/reports', exist_ok=True)
    
    # PDF Setup
    pdf = PodBotProfessionalReport()
    pdf.set_left_margin(20)
    pdf.set_right_margin(20)
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    
    # Usable width calculate karein
    eff_w = pdf.w - pdf.l_margin - pdf.r_margin

    # --- 1. COVER PAGE ---
    pdf.set_fill_color(0, 51, 102)
    pdf.rect(0, 0, 210, 60, 'F') 
    
    pdf.set_y(100)
    pdf.set_font('Arial', 'B', 32)
    pdf.set_text_color(0, 51, 102)
    pdf.multi_cell(eff_w, 15, clean_text(episode_title).upper(), align='C')
    
    pdf.ln(10)
    pdf.set_font('Arial', '', 16)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(eff_w, 10, "Comprehensive Episode Intelligence & Strategic Report", ln=True, align='C')
    
    meta = intelligence.get('metadata', {})
    pdf.set_y(-60)
    pdf.set_font('Arial', 'B', 10)
    pdf.set_text_color(50, 50, 50)
    pdf.cell(eff_w, 5, f"Duration: {meta.get('duration', 'N/A')} | Analyzed by PodBot AI Engine", ln=True, align='C')
    
    keywords_list = meta.get('keywords', [])
    if keywords_list:
        pdf.ln(2)
        pdf.set_font('Arial', 'I', 9)
        pdf.multi_cell(eff_w, 5, f"Key Discussion Areas: {', '.join(keywords_list)}", align='C')

    # --- 2. EXECUTIVE INTELLIGENCE SUMMARY (Based on Real Data) ---
    pdf.add_page()
    pdf.set_font('Arial', 'B', 18)
    pdf.set_text_color(0, 51, 102)
    pdf.cell(eff_w, 15, "1. Executive Intelligence Summary", ln=True)
    pdf.set_draw_color(0, 51, 102)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(8)
    
    pdf.set_font('Arial', '', 12)
    pdf.set_text_color(0, 0, 0)
    summary = intelligence.get('executive_summary', 'Detailed summary not available.')
    pdf.multi_cell(eff_w, 9, clean_text(summary), align='J')

    # --- 3. DEEP DISCUSSION BREAKDOWN (Only Discussed Topics) ---
    pdf.add_page()
    pdf.set_font('Arial', 'B', 18)
    pdf.set_text_color(0, 51, 102)
    pdf.cell(eff_w, 15, "2. Deep Discussion Analysis & Breakdown", ln=True)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(8)
    
    discussed_chapters = intelligence.get('episode_chapters', [])
    if discussed_chapters:
        for chapter in discussed_chapters:
            # Topic Header Box
            pdf.set_fill_color(240, 245, 250)
            pdf.set_font('Arial', 'B', 14)
            pdf.set_text_color(0, 51, 102)
            pdf.multi_cell(eff_w, 10, f"Topic: {clean_text(chapter.get('title'))}", fill=True)
            
            pdf.set_font('Arial', 'I', 9)
            pdf.set_text_color(100, 100, 100)
            pdf.cell(eff_w, 6, f"Context Segment: {chapter.get('time', 'N/A')}", ln=True)
            
            pdf.set_font('Arial', '', 11)
            pdf.set_text_color(0, 0, 0)
            topic_summary = chapter.get('summary', "Analysis available in transcript.")
            pdf.multi_cell(eff_w, 7, clean_text(topic_summary), align='J')
            pdf.ln(10)
    else:
        pdf.set_font('Arial', 'I', 12)
        pdf.cell(eff_w, 10, "No major topics were deeply discussed in this session.", ln=True)

    # --- 4. MISSED / PENDING TOPICS (The Reality Comparison) ---
    missed = intelligence.get('missed_topics', [])
    if missed:
        pdf.ln(5)
        pdf.set_font('Arial', 'B', 16)
        pdf.set_text_color(150, 0, 0) # Reddish color for missed items
        pdf.cell(eff_w, 10, "3. Planned Topics Not Discussed", ln=True)
        pdf.ln(3)
        
        for item in missed:
            pdf.set_font('Arial', 'B', 11)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(eff_w, 7, f"- {clean_text(item.get('title'))}", ln=True)
            pdf.set_font('Arial', '', 10)
            pdf.set_text_color(80, 80, 80)
            pdf.multi_cell(eff_w, 6, f"Note: {clean_text(item.get('reason'))}")
            pdf.ln(3)

    # --- 5. FACT-CHECK & ACCURACY ---
    fact_check = intelligence.get('fact_check', {})
    if fact_check and fact_check.get('checks'):
        pdf.add_page()
        pdf.set_font('Arial', 'B', 18)
        pdf.set_text_color(0, 51, 102)
        pdf.cell(eff_w, 15, "4. Fact-Check & Verification Analysis", ln=True)
        pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
        pdf.ln(8)
        
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(eff_w, 10, f"Analysis Accuracy Score: {fact_check.get('accuracy_percentage', 'N/A')}%", ln=True)
        
        for check in fact_check.get('checks', []):
            pdf.set_font('Arial', 'B', 10)
            pdf.set_text_color(0, 0, 0)
            pdf.multi_cell(eff_w, 6, f"Analyzed Claim: {clean_text(check.get('claim'))}")
            
            color = (0, 120, 0) if check.get('verdict') == "Verified" else (180, 0, 0)
            pdf.set_text_color(*color)
            pdf.cell(30, 6, f"Verdict: {check.get('verdict')}", ln=False)
            
            pdf.set_text_color(50, 50, 50)
            pdf.set_font('Arial', 'I', 10)
            pdf.multi_cell(eff_w - 30, 6, f"| Correction: {clean_text(check.get('correction', 'N/A'))}")
            pdf.ln(4)

    # --- 6. FINAL VERDICT & STRATEGIC TAKEAWAYS ---
    pdf.add_page()
    pdf.set_font('Arial', 'B', 18)
    pdf.set_text_color(0, 51, 102)
    pdf.cell(eff_w, 15, "5. Final Strategic Verdict", ln=True)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(8)
    
    sentiment = intelligence.get('sentiment_analysis', {})
    pdf.set_font('Arial', 'B', 12)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(eff_w, 10, f"Overall Session Sentiment: {sentiment.get('overall_mood', 'Professional')}", ln=True)
    
    hooks = intelligence.get('social_media_hooks', [])
    if hooks:
        pdf.ln(5)
        pdf.set_font('Arial', 'B', 14)
        pdf.set_text_color(0, 51, 102)
        pdf.cell(eff_w, 10, "Key Strategic Takeaways:", ln=True)
        pdf.set_font('Arial', '', 11)
        pdf.set_text_color(0, 0, 0)
        for hook in hooks:
            pdf.multi_cell(eff_w, 8, f"- {clean_text(hook)}")
            pdf.ln(2)

    # Filename logic
 # Filename logic
    safe_title = re.sub(r'[^a-zA-Z0-9]', '_', episode_title)
    timestamp = int(time.time())
    filename = f"report_{safe_title}_{timestamp}.pdf"
    file_path = f"static/reports/{filename}"

    # 1. PDF save karein
    pdf.output(file_path)

    # 2. Response return karein
    if os.path.exists(file_path):
        # ⚠️ Local IP ko badal kar Hugging Face ka domain kar diya
        # Protocol ko 'http' se 'https' lazmi karna hai
        base_url = "https://shoaibmobeen-pobbot-backend.hf.space" 
        
        full_pdf_url = f"{base_url}/static/reports/{filename}"
        
        print(f"DEBUG: PDF Link Created: {full_pdf_url}")
        
        return {
            "status": "success",
            "pdf_url": full_pdf_url,
            "full_path": file_path 
        }
    else:
        return {"status": "error", "message": "PDF creation failed"}