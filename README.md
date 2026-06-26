# PodBot AI Backend 🚀

Professional AI-powered podcast assistant backend architecture designed to streamline pre-interview preparation, manage live transcriptions via WebSockets, and automate post-interview workflows.

## 🛠️ Tech Stack & Architecture
* **Framework:** FastAPI (Python)
* **Database:** Neon PostgreSQL (with SQLAlchemy ORM)
* **Cloud Storage:** Google Drive API Integration (Secure PDF Tracking)
* **Automation:** n8n Webhook Integration
* **Deployment Ready:** Configured for cloud environments (Hugging Face Spaces)

## 📁 Project Structure
```text
bodbot_backend/
├── app/
│   ├── api/          # Route definitions (episodes, live_studio)
│   ├── models/       # Database schemas & structures
│   ├── schemas/      # Pydantic validation schemas
│   ├── services/     # Core business logic & AI/PDF processing
│   ├── database.py   # Connection engine setup
│   └── main.py       # FastAPI application initialisation
├── .gitignore        # Environment and credential safety rules
└── requirements.txt  # Project dependencies
