# Text Summarizer (Flask + SQLite + HTML/JS)

Extractive summarizer using TF-IDF and sentence scoring.

- Frontend: static/index.html, style.css, app.js
- Backend:  app.py (Flask REST API) + summarizer.py (TF-IDF algorithm)
- Database: SQLite file data/summaries.db (created automatically)

## Run

Windows:
    python -m venv venv
    venv\Scripts\activate
    pip install -r requirements.txt
    python app.py

Mac / Linux:
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    python3 app.py

Open http://127.0.0.1:5000

If port 5000 is busy:  PORT=5001 python3 app.py   (Windows: set PORT=5001 then python app.py)

## API
POST /api/summarize   {"text": "...", "ratio": 0.3}
GET  /api/history
GET  /api/history/<id>
DELETE /api/history/<id>
DELETE /api/history
GET  /api/health
