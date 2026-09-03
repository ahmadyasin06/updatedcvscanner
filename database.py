"""
database.py
SQLite operations for the CV Screening System.
Handles table creation, saving analysis results, and fetching history.
"""

import sqlite3
import json
from datetime import datetime
from contextlib import contextmanager

DB_PATH = "cv_screening.db"


@contextmanager
def get_connection():
    """Context-managed SQLite connection so we never leak open handles."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    """Create the analyses table if it doesn't already exist."""
    with get_connection() as conn:
        conn.execute(
            """
             CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                candidate_name TEXT,
                email TEXT,
                phone TEXT,
                job_title TEXT,
                job_description TEXT,
                required_skills TEXT,
                experience_required TEXT,
                education_requirement TEXT,
                employment_type TEXT,
                total_experience_years TEXT,
                extracted_skills TEXT,
                matched_skills TEXT,
                missing_skills TEXT,
                education TEXT,
                match_score INTEGER,
                recommendation TEXT,
                explanation TEXT,
                source_filename TEXT,
                date_analyzed TEXT
            )
            """
        )
        existing_columns = [row["name"] for row in conn.execute("PRAGMA table_info(analyses)").fetchall()]
        if "email" not in existing_columns:
            conn.execute("ALTER TABLE analyses ADD COLUMN email TEXT")
        if "phone" not in existing_columns:
            conn.execute("ALTER TABLE analyses ADD COLUMN phone TEXT")

def save_analysis(job_info: dict, result: dict, source_filename: str = ""):
    """
    Persist one candidate's analysis result tied to the job it was scored against.

    job_info: dict with job_title, job_description, required_skills,
              experience_required, education_requirement, employment_type
    result:   dict returned by cv_analyzer.analyze_cv (already validated)
    """
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO analyses (
                candidate_name, email, phone, job_title, job_description, required_skills,
                experience_required, education_requirement, employment_type,
                total_experience_years, extracted_skills, matched_skills,
                missing_skills, education, match_score, recommendation,
                explanation, source_filename, date_analyzed
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                result.get("candidate_name", "Unknown Candidate"),
                result.get("email", "Not found"),
                result.get("phone", "Not found"),
                job_info.get("job_title", ""),
                job_info.get("job_description", ""),
                json.dumps(job_info.get("required_skills", [])),
                job_info.get("experience_required", ""),
                job_info.get("education_requirement", ""),
                job_info.get("employment_type", ""),
                str(result.get("total_experience_years", "")),
                json.dumps(result.get("extracted_skills", [])),
                json.dumps(result.get("matched_skills", [])),
                json.dumps(result.get("missing_skills", [])),
                result.get("education", ""),
                int(result.get("match_score", 0)),
                result.get("recommendation", ""),
                result.get("explanation", ""),
                source_filename,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ),
        )

def fetch_history(search_term: str = "", search_field: str = "Both"):
    """
    Return all past analyses, newest first, optionally filtered by
    candidate name and/or job title.
    """
    query = "SELECT * FROM analyses"
    params = []

    if search_term:
        if search_field == "Job Title":
            query += " WHERE job_title LIKE ?"
            params.append(f"%{search_term}%")
        elif search_field == "Candidate Name":
            query += " WHERE candidate_name LIKE ?"
            params.append(f"%{search_term}%")
        else:  # Both
            query += " WHERE job_title LIKE ? OR candidate_name LIKE ?"
            params.extend([f"%{search_term}%", f"%{search_term}%"])

    query += " ORDER BY date_analyzed DESC"

    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]


def fetch_analysis_by_id(analysis_id: int):
    """Fetch a single analysis row by id (used to expand a history row)."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM analyses WHERE id = ?", (analysis_id,)
        ).fetchone()
        return dict(row) if row else None


def get_history_count() -> int:
    with get_connection() as conn:
        row = conn.execute("SELECT COUNT(*) as c FROM analyses").fetchone()
        return row["c"]

def clear_history():
    """Delete ALL analysis records. This cannot be undone."""
    with get_connection() as conn:
        conn.execute("DELETE FROM analyses")
