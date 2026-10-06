"""
Admin Question Performance Analytics Page (Phase 16).
Provides empirical question analytics derived from participant attempts:
- Attempts, Correct count, Incorrect count, and Accuracy percentage
- Most frequently attempted questions
- Highest and lowest accuracy questions
- Multi-dimensional filtering by Category, Topic, and Difficulty
- Separate display of Assigned Difficulty vs Observed Performance
- Descriptive admin review notes ("Observed performance may justify reviewing the assigned difficulty.")
- Interactive Plotly visualizations
Protected by require_admin_auth().
"""

import streamlit as st
import pandas as pd

from config.settings import APP_NAME
from services.admin_service import require_admin_auth
from services.analytics_service import (
    fetch_question_analytics,
    get_top_frequently_attempted,
    get_highest_accuracy_questions,
    get_lowest_accuracy_questions,
    build_accuracy_distribution_chart,
    build_attempts_vs_accuracy_scatter,
)
from utils.excel_parser import (
    export_performance_highlights_to_excel,
    export_question_performance_to_excel,
)
from services.question_service import fetch_distinct_skill_numbers
from database.db import get_connection
from database import queries
from components.navigation import inject_custom_navigation_css, render_admin_header
from components.ui_styles import inject_global_ui_styles

st.set_page_config(
    page_title=f"Question Analytics — {APP_NAME}",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Enforce Route Guard & Admin Navigation
inject_custom_navigation_css()
inject_global_ui_styles()
require_admin_auth()

render_admin_header(
    title="Question Performance Analytics",
    subtitle="Empirical Response Statistics, Item Discrimination & Skill Mastery Analysis",
)

# --------------------------------------------------------
# 1. FILTER CONTROLS
# --------------------------------------------------------
st.markdown("###  Filter Performance Data")

with get_connection() as conn:
    available_topics = queries.get_distinct_topics(conn)

f_cat_col, f_top_col, f_skill_col = st.columns(3)

with f_cat_col:
    selected_category = st.selectbox(
        "Category",
        options=["All", "Grammar", "Reading", "Listening"],
        index=0,
    )

with f_top_col:
    topic_options = ["All"] + available_topics
    selected_topic = st.selectbox(
        "Topic / Subtopic",
        options=topic_options,
        index=0,
    )

with f_skill_col:
    distinct_skills = fetch_distinct_skill_numbers(category_name=selected_category if selected_category != "All" else None)
    max_num = max(distinct_skills) if distinct_skills else 25
    limit_num = max(max_num, 25)
    skill_options = ["All"] + [f"Skill {i}" for i in range(1, limit_num + 1)]
    selected_skill_str = st.selectbox(
        "Skill Filter",
        options=skill_options,
        index=0,
    )
    selected_skill_num = int(selected_skill_str.replace("Skill ", "")) if selected_skill_str != "All" else None

# Fetch filtered question analytics data
analytics_items = fetch_question_analytics(
    category=selected_category,
    topic=selected_topic,
    skill_number=selected_skill_num,
    status="Active",
)

total_qs = len(analytics_items)
total_attempts = sum(x["attempts"] for x in analytics_items)
attempted_qs = [x for x in analytics_items if x["attempts"] > 0]
overall_avg_acc = round(sum(x["accuracy"] for x in attempted_qs) / len(attempted_qs), 1) if attempted_qs else 0.0
flagged_qs = [x for x in analytics_items if x["needs_review"]]

st.markdown("<br>", unsafe_allow_html=True)

# --------------------------------------------------------
# 2. HIGH-LEVEL KPI METRICS
# --------------------------------------------------------
k1, k2, k3, k4 = st.columns(4)
with k1:
    st.metric(label="Active Questions Analyzed", value=total_qs)
with k2:
    st.metric(label="Total Responses Logged", value=f"{total_attempts:,}")
with k3:
    st.metric(label="Mean Observed Accuracy", value=f"{overall_avg_acc}%" if attempted_qs else "N/A")
with k4:
    st.metric(
        label="Items Needing Attention (<40%)",
        value=len(flagged_qs),
        help="Questions where participant accuracy is below 40% with multiple attempts",
    )

st.markdown("<br><hr>", unsafe_allow_html=True)

# --------------------------------------------------------
# 3. INTERACTIVE VISUALIZATIONS (PLOTLY)
# --------------------------------------------------------
st.markdown("###  Visual Distribution Analytics")

c_plot1, c_plot2 = st.columns(2)
with c_plot1:
    fig_scatter = build_attempts_vs_accuracy_scatter(analytics_items)
    st.plotly_chart(fig_scatter, use_container_width=True, key="analytics_scatter_chart")

with c_plot2:
    fig_hist = build_accuracy_distribution_chart(analytics_items)
    st.plotly_chart(fig_hist, use_container_width=True, key="analytics_hist_chart")

st.markdown("<br><hr>", unsafe_allow_html=True)

# --------------------------------------------------------
# 4. HIGHLIGHT SECTIONS: FREQUENT, HIGHEST & LOWEST ACCURACY
# --------------------------------------------------------
col_hl_title, col_hl_exp = st.columns([2.8, 1.2])
with col_hl_title:
    st.markdown("### Performance Highlights")
with col_hl_exp:
    if analytics_items:
        hl_dict = {
            "Frequently Attempted": get_top_frequently_attempted(analytics_items, limit=20),
            "Highest Accuracy": get_highest_accuracy_questions(analytics_items, min_attempts=1, limit=20),
            "Lowest Accuracy": get_lowest_accuracy_questions(analytics_items, min_attempts=1, limit=20),
            "Attention Needed": flagged_qs,
        }
        hl_excel_bytes = export_performance_highlights_to_excel(hl_dict)
        st.download_button(
            label="📥 Export Highlights (.xlsx)",
            data=hl_excel_bytes,
            file_name="performance_highlights.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            key="export_highlights_excel_btn",
        )

tab_freq, tab_high, tab_low, tab_flagged = st.tabs([
    "🔥 Most Frequently Attempted",
    "🎯 Highest Accuracy Items",
    "⚠️ Lowest Accuracy Items",
    f"🚩 Attention Needed ({len(flagged_qs)})",
])

def render_summary_mini_table(item_list: list[dict], empty_msg: str):
    if not item_list:
        st.info(empty_msg)
        return

    rows = []
    for x in item_list:
        skill_str = f"Skill {x.get('skill_number', 1)}: {x.get('skill_name', '')}"
        rows.append({
            "ID": x["id"],
            "Question Text": x["question_text"][:75] + ("..." if len(x["question_text"]) > 75 else ""),
            "Category": x["category"],
            "Skill": skill_str,
            "Urutan": f"#{x.get('question_order', 1)}",
            "Attempts": x["attempts"],
            "Accuracy": f"{x['accuracy']}%",
            "Observation": x["admin_note"],
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

with tab_freq:
    st.caption("Questions with the highest exposure to test participants:")
    top_freq = get_top_frequently_attempted(analytics_items, limit=6)
    render_summary_mini_table(top_freq, "No questions with attempts logged yet.")

with tab_high:
    st.caption("Questions answered correctly with the highest frequency (high mastery):")
    top_high = get_highest_accuracy_questions(analytics_items, min_attempts=1, limit=6)
    render_summary_mini_table(top_high, "No questions with attempts logged yet.")

with tab_low:
    st.caption("Questions where participants experienced the highest error rate (lower mastery):")
    top_low = get_lowest_accuracy_questions(analytics_items, min_attempts=1, limit=6)
    render_summary_mini_table(top_low, "No questions with attempts logged yet.")

with tab_flagged:
    st.caption("Questions with low participant accuracy (< 40%) that may require prompt or option review:")
    if not flagged_qs:
        st.success("✅ No low-accuracy items detected. Student response performance is healthy.")
    else:
        st.warning("⚠️ **Notice:** The following questions have high error rates among participants. You may review question wording or distractor clarity in the Question Bank.")
        render_summary_mini_table(flagged_qs, "No flagged questions.")

st.markdown("<br><hr>", unsafe_allow_html=True)

# --------------------------------------------------------
# 5. COMPREHENSIVE QUESTION PERFORMANCE TABLE
# --------------------------------------------------------
col_tbl_title, col_tbl_exp = st.columns([2.8, 1.2])
with col_tbl_title:
    st.markdown("### Complete Question Performance Table")
    st.write("Examine response statistics, accuracy, and skill distribution across all active questions:")
with col_tbl_exp:
    if analytics_items:
        complete_excel_bytes = export_question_performance_to_excel(analytics_items)
        st.download_button(
            label="📥 Export Questions (.xlsx)",
            data=complete_excel_bytes,
            file_name="complete_question_performance.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            key="export_complete_questions_excel_btn",
        )

if not analytics_items:
    st.info("No active questions found matching the selected filters.")
else:
    table_data = []
    for q in analytics_items:
        note_display = q["admin_note"]
        if q["needs_review"]:
            note_display = f"⚠️ {note_display}"

        skill_str = f"Skill {q.get('skill_number', 1)}: {q.get('skill_name', '')}"

        table_data.append({
            "ID": q["id"],
            "Question Prompt": q["question_text"][:85] + ("..." if len(q["question_text"]) > 85 else ""),
            "Category": q["category"],
            "Skill": skill_str,
            "Urutan": f"#{q.get('question_order', 1)}",
            "Attempts": q["attempts"],
            "Correct": q["correct_count"],
            "Incorrect": q["incorrect_count"],
            "Observed Accuracy": f"{q['accuracy']}%",
            "Admin Observation": note_display,
        })

    df_analytics = pd.DataFrame(table_data)
    st.dataframe(df_analytics, use_container_width=True, hide_index=True)

st.markdown("<br><hr>", unsafe_allow_html=True)

# --------------------------------------------------------
# 6. ACTION NAVIGATION BUTTONS
# --------------------------------------------------------
c_dash, c_qbank, _ = st.columns([1.5, 1.5, 3])
with c_dash:
    if st.button("📊 Back to Dashboard", use_container_width=True):
        st.switch_page("pages/91_Admin_Dashboard.py")
with c_qbank:
    if st.button("📚 Manage Question Bank", use_container_width=True):
        st.switch_page("pages/93_Admin_Question_Bank.py")
