from groq import Groq
import os
import json
from datetime import datetime

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def generate_complete_intelligence_report(transcript_data, episode_info, agenda):
    """
    Analyzes Real Transcript vs Planned Agenda and generates a deep case study.
    """
    # 1. ACTUAL DURATION CALCULATION
    try:
        if transcript_data:
            start_time = transcript_data[0].timestamp 
            end_time = transcript_data[-1].timestamp
            
            duration_delta = end_time - start_time
            minutes = duration_delta.seconds // 60
            seconds = duration_delta.seconds % 60
            actual_duration = f"{minutes:02d}:{seconds:02d} mins"
        else:
            actual_duration = "00:00 mins"
    except Exception as e:
        print(f"⚠️ Duration Calculation Error: {e}")
        actual_duration = "00:00 mins"

    # 2. TRANSCRIPT PREPARATION
    lines = []
    for t in transcript_data:
        time_str = t.timestamp.strftime('%M:%S') if t.timestamp else "00:00"
        lines.append(f"[{time_str}] {t.sender}: {t.content}")
    
    full_text = "\n".join(lines)
    word_count = len(full_text.split())

    # 3. ADVANCED AI PROMPT (Strict Real-Time Analysis)
    prompt = f"""
    You are a Lead Business Analyst and Podcast Auditor. 
    Analyze the REAL transcript against the PLANNED agenda.

    Podcast Info:
    - Host: {episode_info['host']}
    - Guest: {episode_info['guest']}
    - Main Theme: {episode_info['title']}
    - Planned Agenda Topics: {agenda}
    
    Transcript Evidence:
    {full_text}

    STRICT REPORTING RULES:
    1. REALITY CHECK: Compare the Transcript with the Planned Agenda. 
    2. DISCUSSSED TOPICS: Only provide detailed summaries for topics that were ACTUALLY mentioned in the transcript.
    3. MISSED TOPICS: Identify topics from the Agenda that were NOT discussed and list them separately.
    4. LENGTH & DEPTH: 
       - executive_summary must be at least 350 words, divided into 3 professional paragraphs.
       - Each discussed chapter must have a 150-word analytical breakdown.
    5. LANGUAGE: Return ONLY high-quality English.

    JSON Structure Required:
    {{
      "executive_summary": "3-paragraph deep analysis based ONLY on real conversation...",
      "episode_chapters": [
          {{ 
            "title": "Professional Heading", 
            "time": "MM:SS", 
            "summary": "150-word detailed breakdown of what was ACTUALLY said and the conclusions reached.",
            "status": "discussed" 
          }}
       ],
      "missed_topics": [
          {{ "title": "Topic Name", "reason": "Briefly explain that this planned topic was not reached in this session." }}
      ],
      "fact_check": {{
          "accuracy_percentage": 0-100,
          "checks": [{{ "claim": "...", "verdict": "Verified/False", "correction": "..." }}]
       }},
      "sentiment_analysis": {{
          "overall_mood": "Professional/Critical/Inspirational",
          "timeline_graph": [10 integers reflecting engagement]
       }},
      "social_media_hooks": ["Key strategic takeaway 1", "Key strategic takeaway 2"],
      "metadata": {{
          "duration": "{actual_duration}",
          "word_count": {word_count},
          "keywords": ["tag1", "tag2"]
       }}
    }}
    """

    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a professional auditor. Compare real transcript vs planned agenda. Never invent discussions that did not happen. Return VALID JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.2 
        )
        
        report = json.loads(completion.choices[0].message.content)
        
        # Metadata safety override
        if 'metadata' not in report:
            report['metadata'] = {}
        report['metadata']['duration'] = actual_duration
        report['metadata']['word_count'] = word_count
        
        return report

    except Exception as e:
        print(f"❌ Intelligence Brain Error: {e}")
        return None