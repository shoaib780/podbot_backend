from groq import Groq
import os

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def suggest_follow_up(history_text, guest_bio):
    """
    Sirf Follow-up Suggestion par focus hai taake speed fast miley.
    Language: ROMAN URDU
    """
    if not history_text or len(history_text) < 10:
        return None

    prompt = f"""
    Guest Bio: {guest_bio}
    Current Speech: {history_text}

    Task: Based on the current speech, suggest ONE short and smart follow-up question for the Host.
    Constraint: Keep it under 15 words.
    Language: ROMAN URDU (Urdu written in English alphabets).
    Example: "Is point ko thora mazeed explain karein?"
    
    Output: Return ONLY the question text.
    """
    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant", # Sab se fast model
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=50 # Speed barhane ke liye tokens limit kar diye
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"Follow-up Error: {e}")
        return None

# Baki extra functions (Topic Match, Tone Analysis) nikaal diye hain 
# taake live recording mein delay na aaye.