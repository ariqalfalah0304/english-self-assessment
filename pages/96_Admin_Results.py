"""
Admin Assessment Results Page (Phase 10).
Features:
- Filter attempts by category (Grammar, Reading, Listening, All)
- Filter attempts by difficulty (Easy, Medium, Hard, All)
- Filter attempts by date range (From Date, To Date)
- Display score percentage, correct answers, incorrect answers, and attempt timestamps
- Aggregate summary metrics for filtered results
- Strict read-only presentation (administrators cannot modify user scores)
Protected by require_admin_auth().
"""

import streamlit as st
import pandas as pd
from datetime import date
from config.settings import APP_NAME
from services.admin_service import require_admin_auth
from services.admin_dashboard_service import fetch_assessment_results
from utils.excel_parser import export_assessment_results_to_excel
from database.db import get_connection
from components.navigation import inject_custom_navigation_css, render_admin_header
from components.ui_styles import inject_global_ui_styles

st.set_page_config(
    page_title=f"Assessment Results — {APP_NAME}",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply route protection & navigation separation
inject_custom_navigation_css()
inject_global_ui_styles()
require_admin_auth()

# Administrative Header
render_admin_header(
    title="Assessment Results Ledger",
    subtitle="Audit Logs, Category Breakdowns & Participant Performance Records",
)

# --------------------------------------------------------
# 1. FILTER CONTROLS
# --------------------------------------------------------
st.markdown("###  Filter Assessment Results")

f_col1, f_col2, f_col3, f_col4 = st.columns(4)

with f_col1:
    category_filter = st.selectbox(
        "Filter by Category:",
        options=["All", "Grammar", "Reading", "Listening"],
        index=0,
    )

with f_col2:
    # Dynamically retrieve distinct skills/modes from attempts
    distinct_skills = []
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT difficulty FROM attempts WHERE difficulty IS NOT NULL AND TRIM(difficulty) != ''")
            distinct_skills = [row[0] for row in cursor.fetchall() if row[0]]
    except Exception:
        pass

    def _skill_sort_key(s: str):
        if s.startswith("Skill "):
            parts = s.split()
            if len(parts) > 1 and parts[1].isdigit():
                return (0, int(parts[1]))
        return (1, s)

    sorted_skills = sorted(distinct_skills, key=_skill_sort_key) if distinct_skills else ["Skill 1", "Skill 2", "Skill 3", "Ujian Gabungan"]
    skill_filter = st.selectbox(
        "Filter by Skill:",
        options=["All"] + sorted_skills,
        index=0,
    )

with f_col3:
    start_date_val = st.date_input("From Date:", value=None)

with f_col4:
    end_date_val = st.date_input("To Date:", value=None)

# Format dates to string
start_str = start_date_val.strftime("%Y-%m-%d") if start_date_val else None
end_str = end_date_val.strftime("%Y-%m-%d") if end_date_val else None

# Fetch filtered records
results = fetch_assessment_results(
    category=category_filter,
    difficulty=skill_filter,
    start_date=start_str,
    end_date=end_str,
    limit=300,
)

# --------------------------------------------------------
# 2. FILTERED AGGREGATE SUMMARY
# --------------------------------------------------------
total_count = len(results)
if total_count > 0:
    scores = [r["score"] for r in results if r.get("score") is not None]
    avg_score = round(sum(scores) / len(scores), 1) if scores else 0.0
    total_correct = sum(r.get("correct_answers", 0) for r in results)
    total_incorrect = sum(r.get("incorrect_answers", 0) for r in results)
else:
    avg_score = 0.0
    total_correct = 0
    total_incorrect = 0

st.markdown("<br>", unsafe_allow_html=True)
m1, m2, m3, m4 = st.columns(4)

with m1:
    st.metric(label="Matching Sessions", value=f"{total_count:,}")
with m2:
    st.metric(label="Mean Score", value=f"{avg_score}%" if total_count > 0 else "N/A")
with m3:
    st.metric(label="Total Correct Answers", value=f"{total_correct:,}")
with m4:
    st.metric(label="Total Incorrect Answers", value=f"{total_incorrect:,}")

st.markdown("<br><hr>", unsafe_allow_html=True)

# --------------------------------------------------------
# 3. RESULTS TABLE (READ-ONLY)
# --------------------------------------------------------
col_tbl_title, col_tbl_exp = st.columns([3, 1])
with col_tbl_title:
    st.markdown("###  Historical Attempt Records")
with col_tbl_exp:
    if results:
        results_excel = export_assessment_results_to_excel(results)
        st.download_button(
            label="📥 Export Results (.xlsx)",
            data=results_excel,
            file_name="assessment_results.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            key="export_results_excel_btn",
        )

if not results:
    st.info("No assessment records found matching the chosen filters.")
else:
    table_rows = []
    for r in results:
        dur = r.get("duration_seconds")
        dur_str = f"{dur // 60}m {dur % 60}s" if dur else "N/A"
        started_str = r["started_at"][:19] if r.get("started_at") else "-"
        completed_str = r["completed_at"][:19] if r.get("completed_at") else "In Progress"

        table_rows.append({
            "Attempt ID": r["id"],
            "Participant Name": r["user_name"],
            "Email Address": r["user_email"],
            "Institution": r["institution"],
            "Category": r["category"],
            "Skill": r["difficulty"],
            "Score": f"{r['score']}%",
            "Correct": f"{r['correct_answers']} / {r['total_questions']}",
            "Incorrect": r["incorrect_answers"],
            "Duration": dur_str,
            "Started": started_str,
            "Completed": completed_str,
        })

    df_results = pd.DataFrame(table_rows)
    st.dataframe(df_results, use_container_width=True, hide_index=True)

st.markdown(
    """
    <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 10px 14px; margin-top: 1rem; font-size: 0.82rem; color: #64748B;">
        🔒 <strong>Read-Only Audit Trail:</strong> In accordance with security requirements, assessment logs, answers, and scores cannot be edited or modified directly from administrative views.
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("<br><hr>", unsafe_allow_html=True)

# --------------------------------------------------------
# 4. NAVIGATION
# --------------------------------------------------------
c_dash, c_users, _ = st.columns([1.5, 1.5, 3])
with c_dash:
    if st.button("📊 Back to Dashboard", use_container_width=True):
        st.switch_page("pages/91_Admin_Dashboard.py")
with c_users:
    if st.button("👥 Participant Directory", use_container_width=True):
        st.switch_page("pages/92_Admin_Users.py")
