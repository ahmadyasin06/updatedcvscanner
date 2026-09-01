"""
ai_analyzer.py
Pure Python, rule-based CV analysis. NO AI / NO API — everything is
extracted with regex + keyword matching, and the score is a weighted
formula. Kept the same function name/signature (analyze_cv) so app.py
doesn't need to change.
"""

import re
from datetime import datetime

# ---------- Master skill list (used to find "extracted_skills" in the CV) ----------
COMMON_SKILLS = [
    # ---------- IT / Software Development ----------
    "python", "java", "javascript", "typescript", "c++", "c#", "php", "ruby", "go", "rust",
    "html", "css", "react", "angular", "vue", "next.js", "node.js", "express",
    "django", "flask", "fastapi", "spring", "laravel", ".net",
    "sql", "mysql", "postgresql", "mongodb", "sqlite", "redis", "oracle", "nosql",
    "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "linux", "cloud computing",
    "git", "github", "gitlab", "ci/cd", "jenkins", "devops",
    "machine learning", "deep learning", "tensorflow", "pytorch", "nlp", "computer vision",
    "data analysis", "data science", "data engineering", "big data", "etl",
    "pandas", "numpy", "scikit-learn", "power bi", "tableau", "excel", "looker",
    "rest api", "graphql", "microservices", "system design", "software architecture",
    "agile", "scrum", "kanban", "jira", "cybersecurity", "network security", "penetration testing",
    "mobile development", "android", "ios", "flutter", "react native", "swift", "kotlin",
    "qa testing", "manual testing", "automation testing", "selenium",

    # ---------- Human Resources (HR) ----------
    "recruitment", "talent acquisition", "onboarding", "employee relations",
    "performance management", "hr policies", "payroll management", "compensation and benefits",
    "hris", "workday", "sap successfactors", "hr analytics", "training and development",
    "organizational development", "employee engagement", "conflict resolution",
    "labor law", "diversity and inclusion", "succession planning", "exit interviews",
    "background verification", "hr operations",

    # ---------- Finance & Accounting ----------
    "financial analysis", "financial modeling", "budgeting", "forecasting",
    "accounting", "bookkeeping", "accounts payable", "accounts receivable",
    "tax preparation", "auditing", "quickbooks", "sap fico", "erp",
    "financial reporting", "risk management", "investment analysis", "valuation",
    "cost accounting", "payroll processing", "reconciliation", "gaap", "ifrs",
    "financial planning", "credit analysis", "banking operations", "excel modeling",

    # ---------- Marketing & Sales ----------
    "digital marketing", "seo", "sem", "content marketing", "social media marketing",
    "email marketing", "google ads", "facebook ads", "marketing analytics",
    "brand management", "market research", "copywriting", "campaign management",
    "influencer marketing", "affiliate marketing", "crm", "salesforce", "hubspot",
    "lead generation", "sales strategy", "negotiation", "b2b sales", "b2c sales",
    "account management", "customer relationship management", "cold calling",

    # ---------- Design (Graphic / UI-UX / Product) ----------
    "photoshop", "illustrator", "figma", "adobe xd", "sketch", "canva",
    "ui/ux design", "wireframing", "prototyping", "user research", "interaction design",
    "graphic design", "branding", "typography", "3d modeling", "after effects",
    "premiere pro", "indesign", "motion graphics", "video editing",
    "product design", "design thinking", "visual design",

    # ---------- Customer Service / Operations ----------
    "customer service", "customer support", "call center operations",
    "help desk support", "ticketing systems", "zendesk", "supply chain management",
    "logistics", "inventory management", "vendor management", "procurement",
    "quality assurance", "process improvement", "six sigma", "lean management",
    "operations management", "warehouse management",

    # ---------- Legal ----------
    "contract drafting", "legal research", "compliance", "corporate law",
    "litigation", "intellectual property", "regulatory affairs", "legal documentation",
    "negotiation", "due diligence", "risk assessment",

    # ---------- Healthcare ----------
    "patient care", "clinical research", "medical coding", "medical billing",
    "emr/ehr systems", "healthcare administration", "nursing", "pharmacy",
    "hipaa compliance", "medical terminology", "diagnostics",

    # ---------- Education / Training ----------
    "curriculum development", "lesson planning", "classroom management",
    "instructional design", "e-learning", "training delivery", "academic research",

    # ---------- Soft Skills (all domains) ----------
    "communication", "leadership", "teamwork", "project management", "time management",
    "problem solving", "critical thinking", "adaptability", "decision making",
    "presentation skills", "public speaking", "collaboration", "creativity",
    "attention to detail", "multitasking", "emotional intelligence", "mentoring",
]

EDUCATION_LEVELS = {
    "phd": ("PhD", 4), "doctorate": ("PhD", 4),
    "master's": ("Master's", 3), "masters": ("Master's", 3), "mba": ("Master's (MBA)", 3),
    "m.sc": ("Master's", 3), "msc": ("Master's", 3), "m.tech": ("Master's", 3), "ms ": ("Master's", 3),
    "bachelor's": ("Bachelor's", 2), "bachelors": ("Bachelor's", 2), "b.sc": ("Bachelor's", 2),
    "bsc": ("Bachelor's", 2), "b.tech": ("Bachelor's", 2), "btech": ("Bachelor's", 2),
    "bs ": ("Bachelor's", 2), "be ": ("Bachelor's", 2), "b.e": ("Bachelor's", 2),
    "high school": ("High School", 1), "intermediate": ("High School", 1),
    "fsc": ("High School", 1), "hssc": ("High School", 1),
}


def _word_present(needle: str, haystack_lower: str) -> bool:
    """Whole-word/phrase match so 'go' doesn't match inside 'Django'."""
    pattern = r"(?<![a-zA-Z0-9])" + re.escape(needle.lower()) + r"(?![a-zA-Z0-9])"
    return re.search(pattern, haystack_lower) is not None


class MalformedResponseError(Exception):
    """Kept for compatibility with app.py's except clauses (unused now)."""
    pass


# ---------- Contact info extraction ----------

def _extract_contact_info(text: str) -> dict:
    """Extracts email and phone number using regex."""

    # Email
    email_match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    email = email_match.group(0) if email_match else "Not found"

    # Phone number (handles +92 300 1234567, (021) 1234567, 0300-1234567, etc.)
    phone_candidates = re.findall(r"[\+\(]?\d[\d\-\.\s\(\)]{7,}\d", text)
    phone = "Not found"
    for candidate in phone_candidates:
        digits_only = re.sub(r"\D", "", candidate)
        if 7 <= len(digits_only) <= 15:
            phone = candidate.strip()
            break

    return {
        "email": email,
        "phone": phone,
    }


# ---------- Extraction helpers ----------

def _extract_candidate_name(text: str) -> str:
    lines = [l.strip() for l in text.strip().split("\n") if l.strip()]
    for line in lines[:5]:
        # Skip lines that look like contact info (contain @, digits, or are too long)
        if re.search(r"[\d@]", line):
            continue
        if "linkedin" in line.lower() or "http" in line.lower():
            continue
        if 2 <= len(line.split()) <= 4 and len(line) < 40:
            return line.title()
    return "Unknown Candidate"


def _extract_total_experience(text: str) -> float:
    text_lower = text.lower()

    matches = re.findall(r"(\d+(?:\.\d+)?)\+?\s*(?:years|yrs)\s*(?:of)?\s*experience", text_lower)
    if matches:
        return max(float(m) for m in matches)

    ranges = re.findall(r"((?:19|20)\d{2})\s*[-–—]\s*((?:19|20)\d{2}|present|current)", text_lower)
    current_year = datetime.now().year
    total = 0
    for start, end in ranges:
        start_y = int(start)
        end_y = current_year if end in ("present", "current") else int(end)
        if end_y >= start_y:
            total += (end_y - start_y)

    return round(total, 1)


def _extract_education(text: str) -> str:
    text_lower = text.lower()
    best_label, best_level = "Not specified", 0
    for keyword, (label, level) in EDUCATION_LEVELS.items():
        if keyword in text_lower and level > best_level:
            best_level = level
            best_label = label
    return best_label


def _education_level(label: str) -> int:
    levels = {"phd": 4, "master's": 3, "bachelor's": 2, "high school": 1}
    for keyword, level in levels.items():
        if keyword in label.lower():
            return level
    return 0


def _required_education_level(requirement: str) -> int:
    mapping = {"high school": 1, "bachelor's": 2, "master's": 3, "phd": 4, "any": 0}
    return mapping.get(requirement.strip().lower(), 0)


def _required_min_experience(requirement: str) -> float:
    """'0-1 years' -> 0, '1-3 years' -> 1, '5+ years' -> 5"""
    match = re.search(r"(\d+(?:\.\d+)?)", requirement)
    return float(match.group(1)) if match else 0


def _extract_all_skills(text: str) -> list:
    text_lower = text.lower()
    return [s for s in COMMON_SKILLS if _word_present(s, text_lower)]


def _match_required_skills(text: str, required_skills: list):
    text_lower = text.lower()
    matched, missing = [], []
    for skill in required_skills:
        if _word_present(skill.strip(), text_lower):
            matched.append(skill.strip())
        else:
            missing.append(skill.strip())
    return matched, missing


# ---------- Main entry point ----------

def analyze_cv(cv_text: str, job_info: dict) -> dict:
    """
    Rule-based analysis — no AI involved. Extracts name, contact info,
    experience, education, and skills with regex/keyword matching,
    then scores the candidate with a weighted formula.
    """
    required_skills = job_info.get("required_skills", [])

    candidate_name = _extract_candidate_name(cv_text)
    contact_info = _extract_contact_info(cv_text)
    total_experience = _extract_total_experience(cv_text)
    education = _extract_education(cv_text)
    extracted_skills = _extract_all_skills(cv_text)
    matched_skills, missing_skills = _match_required_skills(cv_text, required_skills)

    # --- Skill score (55% weight) ---
    skill_score = (len(matched_skills) / len(required_skills) * 100) if required_skills else 100

    # --- Experience score (25% weight) ---
    min_required_exp = _required_min_experience(job_info.get("experience_required", "0"))
    if min_required_exp <= 0:
        experience_score = 100
    else:
        experience_score = min(100, (total_experience / min_required_exp) * 100)

    # --- Education score (20% weight) ---
    required_edu_level = _required_education_level(job_info.get("education_requirement", "Any"))
    candidate_edu_level = _education_level(education)
    if required_edu_level == 0:
        education_score = 100
    elif candidate_edu_level >= required_edu_level:
        education_score = 100
    else:
        education_score = max(0, (candidate_edu_level / required_edu_level) * 100)

    match_score = round(0.55 * skill_score + 0.25 * experience_score + 0.20 * education_score)
    match_score = max(0, min(100, match_score))

    if match_score >= 75:
        recommendation = "Strongly Recommended"
    elif match_score >= 50:
        recommendation = "Consider"
    else:
        recommendation = "Not Recommended"

    explanation = (
        f"Matched {len(matched_skills)} of {len(required_skills)} required skills. "
        f"Candidate has ~{total_experience} years of experience "
        f"(requirement: {job_info.get('experience_required', 'N/A')}). "
        f"Highest education found: {education} "
        f"(requirement: {job_info.get('education_requirement', 'N/A')})."
    )

    return {
        "candidate_name": candidate_name,
        "email": contact_info["email"],
        "phone": contact_info["phone"],
        "total_experience_years": total_experience,
        "extracted_skills": extracted_skills,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "education": education,
        "match_score": match_score,
        "recommendation": recommendation,
        "explanation": explanation,
    }