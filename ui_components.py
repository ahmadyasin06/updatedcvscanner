"""
ui_components.py
Minimal, self-contained UI building blocks: skill chips, a lightweight
score badge, candidate cards, and empty states.
"""

import streamlit as st
import json


# ---------- Style helpers ----------

def score_color(score: int) -> str:
    score = int(score) if score is not None else 0
    if score >= 75:
        return "#22c55e"   # green
    elif score >= 50:
        return "#eab308"   # yellow
    else:
        return "#ef4444"   # red


def recommendation_badge_style(recommendation: str):
    styles = {
        "Strongly Recommended": ("#22c55e", "#ecfdf5"),
        "Consider": ("#eab308", "#fefce8"),
        "Not Recommended": ("#ef4444", "#fef2f2"),
    }
    return styles.get(recommendation, ("#6b7280", "#f3f4f6"))


# ---------- Inject global CSS ----------

def inject_custom_css():
    st.markdown(
        """
        <style>

    /* ================= MAIN CONTENT ================= */

        .main { background-color: #f8fafc; }

        /* ---------- Reduce top spacing of main content area ---------- */
        div[data-testid="stAppViewContainer"] > div:first-child {
            padding-top: 0rem !important;
        }
        div[data-testid="stMainBlockContainer"],
        div[data-testid="block-container"],
        .block-container {
            padding-top: 2.5rem !important;
        }


        

        .candidate-card {
            background: white;
            border-radius: 12px;
            padding: 20px 24px;
            margin-bottom: 14px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.07);
            border-left: 4px solid var(--score-color, #6b7280);
        }

        /* ================= SIDEBAR ================= */

        section[data-testid="stSidebar"] {
            background-color: #111827 !important;
            border-right: 1px solid #1f2937 !important;
        }

        /* Sidebar text */
        section[data-testid="stSidebar"] .stMarkdown,
        section[data-testid="stSidebar"] .stCaption,
        section[data-testid="stSidebar"] label {
            color: #f3f4f6 !important;
        }



        /* ================= NAVIGATION BUTTONS ================= */

        section[data-testid="stSidebar"] .stButton > button {
            width: 100% !important;
            border-radius: 8px !important;
            font-weight: 500 !important;
            transition: all 0.2s ease-in-out !important;
        }

        /* Inactive button */
        section[data-testid="stSidebar"] .stButton > button[kind="secondary"] {
            background-color: #1f2937 !important;
            color: #f3f4f6 !important;
            border: 1px solid #374151 !important;
        }

        section[data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover {
            background-color: #374151 !important;
            color: #ffffff !important;
            border-color: #4b5563 !important;
        }

        /* Active button */
        section[data-testid="stSidebar"] .stButton > button[kind="primary"] {
            background-color: #FF4B4B !important;
            color: #ffffff !important;
            #border: 1px solid #3b82f6 !important;
            box-shadow: 0 4px 10px rgba(255, 255, 255, 0.25) !important;
        }

        section[data-testid="stSidebar"] .stButton > button[kind="primary"]:hover {
            background-color: #FF4B4B !important;
            color: #ffffff !important;
        }



        # /* ================= SIDEBAR TOGGLE ================= */

        # button[data-testid="stSidebarCollapseButton"],
        # [data-testid="collapsedControl"] {
        #     display: block !important;
        #     color: #f3f4f6 !important;
        #     background-color: #1f2937 !important;
        #     border: 1px solid #374151 !important;
        #     border-radius: 8px !important;
        # }




    # /* ================= HEADER ================= */

    #     header[data-testid="stHeader"] {
    #         background-color: transparent !important;
    #     }




        .card-top {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .candidate-name {
            font-size: 17px;
            font-weight: 700;
            color: #111827;
        }
        .score-circle {
            width: 46px;
            height: 46px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 15px;
            flex-shrink: 0;
        }
        .meta-text {
            color: #6b7280;
            font-size: 13px;
            margin: 6px 0 12px 0;
        }
        .section-label {
            font-size: 11px;
            font-weight: 700;
            color: #9ca3af;
            text-transform: uppercase;
            letter-spacing: .04em;
            margin: 10px 0 4px 0;
        }
        .explanation-text {
            color: #4b5563;
            font-size: 13.5px;
            margin-top: 10px;
            line-height: 1.5;
        }

        .skill-chip {
            display: inline-block;
            padding: 3px 12px;
            border-radius: 999px;
            font-size: 12.5px;
            font-weight: 600;
            margin: 3px 4px 3px 0;
        }
        .skill-chip-matched {
            background-color: #ecfdf5;
            color: #16a34a;
            border: 1px solid #86efac;
        }
        .skill-chip-missing {
            background-color: #fef2f2;
            color: #dc2626;
            border: 1px solid #fca5a5;
        }
        .skill-chip-neutral {
            background-color: #eff6ff;
            color: #2563eb;
            border: 1px solid #93c5fd;
        }

        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 999px;
            font-weight: 700;
            font-size: 12px;
        }

        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: #6b7280;
        }

        section[data-testid="stSidebar"] {
            background-color: #111827;
        }
        section[data-testid="stSidebar"] * {
            color: #f3f4f6 !important;
        }



        /* ================= SIDEBAR: Always visible, no collapse ================= */

        /* Hide the collapse/expand button — scoped to sidebar ONLY so it doesn't
        accidentally hide other buttons (like the file uploader's Browse button) */
        section[data-testid="stSidebar"] button:has(span[data-testid="stIconMaterial"]) {
            display: none !important;
        }

        /* Force sidebar to always render fully expanded */
        section[data-testid="stSidebar"] {
            min-width: 21rem !important;
            max-width: 21rem !important;
            width: 21rem !important;
            transform: none !important;
            visibility: visible !important;
            margin-left: 0px !important;
        }

        section[data-testid="stSidebar"][aria-expanded="false"] {
            display: block !important;
            transform: none !important;
            margin-left: 0px !important;
        }

        </style>
        """,
        unsafe_allow_html=True,
    )


# ---------- Skill chips ----------

def _skill_chips_html(skills, kind="neutral") -> str:
    """Build the chip HTML as a string (used inside a single card block)."""
    if not skills:
        return '<span style="color:#9ca3af; font-size:13px;">None</span>'
    css_class = f"skill-chip-{kind}"
    return "".join(f'<span class="skill-chip {css_class}">{s}</span>' for s in skills)


def render_skill_tags(skills, kind="neutral"):
    """Standalone version for use outside a single-block card (e.g. History page)."""
    st.markdown(_skill_chips_html(skills, kind), unsafe_allow_html=True)


# ---------- Score badge ----------

def render_score_gauge(score: int, key: str = None):
    """Lightweight standalone score circle (no charting library needed)."""
    score = int(score) if score is not None else 0 
    color = score_color(score)
    st.markdown(
        f"""
        <div style="display:flex; justify-content:center;">
            <div class="score-circle" style="width:72px;height:72px;font-size:22px;
                background:{color}1a; color:{color}; border:2px solid {color};">
                {score}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------- Candidate card ----------

def render_candidate_card(result: dict, job_required_skills=None, is_best_match=False, key_prefix=""):
    """Renders the full candidate card as a single HTML block."""
    score = int(result.get("match_score", 0))
    color = score_color(score)
    badge_color, badge_bg = recommendation_badge_style(result.get("recommendation", ""))

    best_match_tag = (
        '<span style="color:#f59e0b; font-weight:700; font-size:12px; margin-left:8px;">🏆 Best Match</span>'
        if is_best_match else ""
    )

    card_html = f"""
    <div class="candidate-card" style="--score-color:{color};">
        <div class="card-top">
            <span class="candidate-name">{result.get('candidate_name', 'Unknown Candidate')}{best_match_tag}</span>
            <div class="score-circle" style="background:{color}1a; color:{color}; border:2px solid {color};">{score}</div>
        </div>
        <div class="meta-text">
            <span class="badge" style="background-color:{badge_bg}; color:{badge_color};">{result.get('recommendation', 'N/A')}</span>
            &nbsp;&nbsp;{result.get('total_experience_years', 'N/A')} yrs exp &nbsp;•&nbsp; {result.get('education', 'N/A')}
        </div>
            <div class="meta-text" style="margin-top:-6px;">
    📧      {result.get('email', 'Not found')} &nbsp;•&nbsp; 📱 {result.get('phone', 'Not found')}
        </div>
        <div class="section-label">Matched Skills</div>
        <div>{_skill_chips_html(result.get('matched_skills', []), 'matched')}</div>
        <div class="section-label">Missing Skills</div>
        <div>{_skill_chips_html(result.get('missing_skills', []), 'missing')}</div>
        <div class="explanation-text">{result.get('explanation', '')}</div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)


# ---------- Empty states ----------

def render_empty_state(icon: str, title: str, subtitle: str):
    st.markdown(
        f"""
        <div class="empty-state">
            <div style="font-size: 44px;">{icon}</div>
            <h3>{title}</h3>
            <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------- Skill input preview (upload page) ----------

def render_skill_input_preview(raw_skills_text: str):
    skills = [s.strip() for s in raw_skills_text.split(",") if s.strip()]
    if skills:
        render_skill_tags(skills, kind="neutral")
    return skills


def safe_json_list(value):
    """Parse a JSON-encoded list stored in SQLite back into a Python list."""
    if isinstance(value, list):
        return value
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, list) else []
    except (TypeError, json.JSONDecodeError):
        return []
