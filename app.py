"""
app.py
Main Streamlit application: navigation + the three pages
(Post Job & Upload, Results, History).
"""

import streamlit as st
from datetime import datetime

import database
import cv_parser
import cv_analyzer
import ui_components as ui

# ---------- Page config ----------
st.set_page_config(
    page_title="CV Scanning System",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

ui.inject_custom_css()
database.init_db()

# ---------- Session state defaults ----------
if "page" not in st.session_state:
    st.session_state.page = "upload"
if "results" not in st.session_state:
    st.session_state.results = []          # list of analysis dicts for last run
if "job_info" not in st.session_state:
    st.session_state.job_info = {}
if "expanded_history_id" not in st.session_state:
    st.session_state.expanded_history_id = None

EXPERIENCE_OPTIONS = ["1 Year", "2-3 Years", "3-5 Years", "5+ Years"]
EDUCATION_OPTIONS = ["School", "Intermediate", "Bachelor's", "Master's", "PhD", "Any"]
EMPLOYMENT_OPTIONS = ["Full-time", "Part-time", "Remote", "Hybrid", "Internship", "Contract"]


# ---------- Sidebar navigation ----------
def sidebar_nav():
    st.sidebar.markdown(
    '<h1 style="font-size: 50px; padding-top: 0px; margin-bottom: 0px; '
    'background: linear-gradient(90deg, #FF4B4B, #FFFFFF); '
    '-webkit-background-clip: text; -webkit-text-fill-color: transparent; '
    'background-clip: text; font-weight: 800; letter-spacing: -1px;">CV Scanner</h1>',
    unsafe_allow_html=True,
    )

    st.sidebar.markdown("---")

    nav_items = {
        "upload": "📋 Upload CVs",
        "results": "📊 Results",
        "history": "🕘 History",
    }

    for key, label in nav_items.items():
        button_type = (
            "primary"
            if st.session_state.page == key
            else "secondary"
        )

        if st.sidebar.button(
            label,
            use_container_width=True,
            type=button_type,
            key=f"nav_{key}",
        ):
            st.session_state.page = key
            st.rerun()

    st.sidebar.markdown("---")

    st.sidebar.caption(
        f"📁 {database.get_history_count()} candidates analyzed so far"
    )


# ---------- PAGE 1: Post Job & Upload ----------
def page_upload():
    st.title("Upload CVs")
    st.caption("Fill the details, upload candidate CVs, and analyze them.")

    with st.form("job_form"):
        col1, col2 = st.columns(2)
        with col1:
            job_title = st.text_input("Job Title *", placeholder="Senior Backend Engineer")
            required_skills_raw = st.text_input(
                "Required Skills (comma-separated) *",
                placeholder="Python, Django, PostgreSQL, Docker",
            )
            experience_required = st.selectbox("Experience Required *", EXPERIENCE_OPTIONS)
        with col2:
            education_requirement = st.selectbox("Education Requirement *", EDUCATION_OPTIONS);
            employment_type = st.selectbox("Employment Type *", EMPLOYMENT_OPTIONS)

        job_description = st.text_area(
            "Job Description *",
            height=200,
            placeholder="Paste the full job description here...",
        )

        if required_skills_raw:
            st.markdown("**Skills preview:**")
            ui.render_skill_input_preview(required_skills_raw)

        uploaded_files = st.file_uploader(
            "Upload CV(s) — PDF or DOCX *",
            type=["pdf", "docx"],
            accept_multiple_files=True,
        )

        submitted = st.form_submit_button("Analyze Candidates", use_container_width=True, type="primary")

    if submitted:
        errors = []
        if not job_title.strip():
            errors.append("Job Title is required.")
        if not job_description.strip():
            errors.append("Job Description is requicd.")
        if not required_skills_raw.strip():
            errors.append("Required Skills field is required.")
        if not uploaded_files:
            errors.append("Please upload at least one CV.")

        if errors:
            for e in errors:
                st.error(e)
            return

        required_skills = [s.strip() for s in required_skills_raw.split(",") if s.strip()]
        job_info = {
            "job_title": job_title.strip(),
            "job_description": job_description.strip(),
            "required_skills": required_skills,
            "experience_required": experience_required,
            "education_requirement": education_requirement,
            "employment_type": employment_type,
        }
        st.session_state.job_info = job_info

        results = []
        progress_bar = st.progress(0, text="Starting analysis...")
        total = len(uploaded_files)

        for i, uploaded_file in enumerate(uploaded_files):
            progress_bar.progress(
                (i) / total, text=f"Analyzing {uploaded_file.name} ({i + 1}/{total})..."
            )
            try:
                cv_text = cv_parser.extract_text(uploaded_file)
            except cv_parser.UnsupportedFileTypeError as e:
                st.warning(f"⚠️ Skipped: {e}")
                continue
            except cv_parser.EmptyDocumentError as e:
                st.warning(f"⚠️ Skipped: {e}")
                continue
            except Exception as e:
                st.warning(f"⚠️ Could not read '{uploaded_file.name}': {e}")
                continue

            try:
                result = cv_analyzer.analyze_cv(cv_text, job_info)
            except Exception as e:
                st.warning(f"⚠️ Analysis failed for '{uploaded_file.name}': {e}")
                continue

            is_empty_result = (
                result.get("candidate_name") == "Unknown Candidate"
                and not result.get("extracted_skills")
                and result.get("total_experience_years", 0) == 0
            )
            if is_empty_result:
                st.warning(
                    f"⚠️ Skipped '{uploaded_file.name}': could not extract any "
                    "usable info (file may be a scanned image or badly formatted)."
                )
                continue

            result["_source_filename"] = uploaded_file.name
            results.append(result)

            try:
                database.save_analysis(job_info, result, source_filename=uploaded_file.name)
            except Exception as e:
                st.warning(f"⚠️ Analyzed but failed to save '{uploaded_file.name}' to history: {e}")

        progress_bar.progress(1.0, text="Done!")
        progress_bar.empty()

        if not results:
            st.error("No candidates could be analyzed. Please check your files and try again.")
            return

        # Sort by match score, highest first
        results.sort(key=lambda r: r.get("match_score", 0), reverse=True)
        st.session_state.results = results
        st.session_state.page = "results"
        st.success(f"✅ Analyzed {len(results)} candidate(s) successfully!")
        st.rerun()


# ---------- PAGE 2: Results ----------
def page_results():
    st.title("Screening Results")

    job_info = st.session_state.job_info
    results = st.session_state.results

    if not results:
        ui.render_empty_state(
            "🗂️",
            "No results yet",
            "Head over to 'Upload CVs' to analyze your first batch of candidates.",
        )
        return

    if job_info:
        st.caption(
            f"Results for **{job_info.get('job_title', 'this role')}** "
            f"· {job_info.get('experience_required', '')} · "
            f"{job_info.get('education_requirement', '')} · "
            f"{job_info.get('employment_type', '')}"
        )

    strongly, consider, not_rec = 0, 0, 0
    for r in results:
        rec = r.get("recommendation")
        if rec == "Strongly Recommended":
            strongly += 1
        elif rec == "Consider":
            consider += 1
        else:
            not_rec += 1

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Candidates", len(results))
    m2.metric("🟢 Strongly Recommended", strongly)
    m3.metric("🟡 Consider", consider)
    m4.metric("🔴 Not Recommended", not_rec)

    st.markdown("---")

    for idx, result in enumerate(results):
        ui.render_candidate_card(
            result,
            job_info.get("required_skills", []),
            is_best_match=(idx == 0 and result.get("match_score", 0) > 0),
            key_prefix=f"res_{idx}",
        )


# ---------- PAGE 3: History ----------
def page_history():
    st.title("Analysis History")

    total_count = database.get_history_count()
    if total_count == 0:
        ui.render_empty_state(
            "🕘",
            "No history yet",
            "Once you analyze candidates, they'll show up here for future reference.",
        )
        return
    with st.expander("Clear all history"):
        st.warning("This will permanently delete all saved analyses. This cannot be undone.")
        if st.button("Yes, delete everything", type="primary"):
            database.clear_history()
            st.session_state.expanded_history_id = None
            st.success("History cleared.")
            st.rerun()   

    col1, col2 = st.columns([3, 1])
    with col1:
        search_term = st.text_input("🔍 Search by Job Title or Candidate Name", "")
    with col2:
        search_field = st.selectbox("Search in", ["Both", "Job Title", "Candidate Name"], placeholder="Search by Title or Candidate Name")

    records = database.fetch_history(search_term, search_field)

    if not records:
        st.info("No matching records found.")
        return

    st.caption(f"Showing {len(records)} of {total_count} record(s)")

    # Table header
    header_cols = st.columns([2.2, 2.2, 1.2, 1.8, 1.8, 1])
    headers = ["Candidate Name", "Job Title", "Score", "Recommendation", "Date Analyzed", ""]
    for c, h in zip(header_cols, headers):
        c.markdown(f"**{h}**")

    st.markdown("---")

    for record in records:
        score = record.get("match_score", 0) or 0
        color = ui.score_color(score)
        row_cols = st.columns([2.2, 2.2, 1.2, 1.8, 1.8, 1])
        row_cols[0].write(record.get("candidate_name", "—"))
        row_cols[1].write(record.get("job_title", "—"))
        row_cols[2].markdown(
            f'<span style="color:{color}; font-weight:700;">{score}</span>',
            unsafe_allow_html=True,
        )
        row_cols[3].write(record.get("recommendation", "—"))
        row_cols[4].write(record.get("date_analyzed", "—"))

        is_expanded = st.session_state.expanded_history_id == record["id"]
        if row_cols[5].button("👁️" if not is_expanded else "✖️", key=f"expand_{record['id']}"):
            st.session_state.expanded_history_id = (
                None if is_expanded else record["id"]
            )
            st.rerun()

        if is_expanded:
            with st.container():
                st.markdown(
                    f'<div class="candidate-card" style="--score-color:{color};">',
                    unsafe_allow_html=True,
                )
                c1, c2 = st.columns([2, 1])
                with c1:
                    st.markdown(f"### {record.get('candidate_name')}")
                    st.markdown(f"📧 **Email:** {record.get('email', 'Not found')} &nbsp;&nbsp; 📱 **Phone:** {record.get('phone', 'Not found')}")
                    st.markdown(f"**Job:** {record.get('job_title')}")
                    st.markdown(f"**Experience:** {record.get('total_experience_years')} years")
                    st.markdown(f"**Education:** {record.get('education')}")
                    st.markdown(f"**Employment Type:** {record.get('employment_type')}")
                with c2:
                    ui.render_score_gauge(score, key=f"hist_gauge_{record['id']}")

                st.markdown("**✅ Matched Skills**")
                ui.render_skill_tags(ui.safe_json_list(record.get("matched_skills")), "matched")
                st.markdown("**❌ Missing Skills**")
                ui.render_skill_tags(ui.safe_json_list(record.get("missing_skills")), "missing")

                st.markdown("**Explanation:**")
                st.info(record.get("explanation", "—"))
                st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("---")


# ---------- Router ----------
def main():
    sidebar_nav()

    if st.session_state.page == "upload":
        page_upload()
    elif st.session_state.page == "results":
        page_results()
    elif st.session_state.page == "history":
        page_history()


if __name__ == "__main__":
    main()
