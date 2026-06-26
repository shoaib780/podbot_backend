# app/services/ai_service.py
import fitz  # PyMuPDF
from groq import Groq
import os
import json

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def extract_text_from_pdf(pdf_content):
    doc = fitz.open(stream=pdf_content, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def generate_production_strategy(research_text: str, tone: str):
    # Prompt ko update kiya gaya hai guest_name extract karne ke liye
    prompt = f"""
    You are a Senior Podcast Producer. Style: {tone}.
    Research Context: {research_text[:3000]} 

    Task: Analyze the research text and generate a complete interview strategy in JSON format.
    CRITICAL: You must extract the Full Name of the guest from the provided research context.

    Response Format (Strict JSON):
    {{
        "guest_name": "Full Name of Guest extracted from text",
        "agenda": [
            {{"time": "0:00", "title": "Introduction", "description": "...", "is_covered": false}},
            {{"time": "10:00", "title": "Main Core", "description": "...", "is_covered": false}},
            {{"time": "25:00", "title": "Closing", "description": "...", "is_covered": false}}
        ],
        "questions": [
            {{"id": 1, "text": "Question 1", "intent": "Why asking this?", "selected": true, "is_asked": false}},
            {{"id": 2, "text": "Question 2", "intent": "...", "selected": true, "is_asked": false}},
            {{"id": 3, "text": "Question 3", "intent": "...", "selected": true, "is_asked": false}},
            {{"id": 4, "text": "Question 4", "intent": "...", "selected": true, "is_asked": false}},
            {{"id": 5, "text": "Question 5", "intent": "...", "selected": true, "is_asked": false}}
        ]
    }}
    """
    
    completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.1-8b-instant",
        response_format={ "type": "json_object" }
    )
    return completion.choices[0].message.content

# --- Specific Item Refresh Logic ---

def refresh_specific_agenda_item(topic: str, segment_title: str, tone: str):
    prompt = f"""
    Context: The podcast is about {topic}. 
    Current Segment: {segment_title}.
    Tone: {tone}.
    
    Task: Regenerate a fresh, engaging description for this specific segment of the podcast.
    Keep it concise (1-2 sentences).
    """
    completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.1-8b-instant",
    )
    return completion.choices[0].message.content.strip()

def regenerate_single_question(topic: str, previous_question: str, tone: str):
    prompt = f"""
    Podcast Topic: {topic}
    Previous Question: {previous_question}
    Tone: {tone}
    
    Task: Generate a completely new and different interview question for this topic. 
    Make it high-impact and engaging. 
    Return only the question text, nothing else.
    """
    completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.1-8b-instant",
    )
    return completion.choices[0].message.content.strip()