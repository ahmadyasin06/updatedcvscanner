# AI CV Screening System

A Streamlit app that parses candidate CVs (PDF/DOCX) and stores results in SQLite for later review.

## Setup

1. **Create a virtual environment (recommended)**
   ```bash
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the app**
   ```bash
   streamlit run app.py
   ```

The app will open at `http://localhost:8501`. A `cv_screening.db` SQLite
file is created automatically on first run.

## Project Structure

| File | Purpose |
|---|---|
| `app.py` | Main app, navigation, and all three pages |
| `cv_parser.py` | Extracts text from PDF/DOCX files |
| `database.py` | SQLite schema + save/fetch functions |
| `ui_components.py` | Styled cards, chips, gauges, empty states |
| `requirements.txt` | Python dependencies |
