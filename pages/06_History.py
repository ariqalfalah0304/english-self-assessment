"""
Participant Assessment History and Self-Assessment Summary Page (Phase 15).
Displays chronological attempt records, category performance breakdowns,
interactive Plotly visualizations, and descriptive progress feedback.
Maintains clear non-certification disclaimer.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from config.settings import APP_NAME
from services.user_service import get_active_user_session, is_user_authenticated
from services.history_service import (
    fetch_user_history,
    calculate_self_assessment_summary,
    CERTIFICATION_DISCLAIMER,
)
from components.navigation import inject_custom_navigation_css
from components.ui_styles import inject_global_ui_styles

st.set_page_config(
    page_title=f"My Assessment History & Summary — {APP_NAME}",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_custom_navigation_css()
inject_global_ui_styles()

# 1. ENFORCE PARTICIPANT IDENTITY GUARD
if not is_user_authenticated():
    st.error("🔒 Access Denied: Please provide your name and email to view your personal assessment history.")
    st.markdown(
        """
        Your assessment attempts are recorded under your participant profile.
        """
    )
    if st.button("👉 Provide Identity Now", type="primary", use_container_width=True):
        st.switch_page("pages/02_Identity.py")
    st.stop()

active_user = get_active_user_session()
user_id = active_user["id"]
user_name = active_user["name"]

# 2. TOP BANNER & PARTICIPANT HEADER
st.markdown(
    f"""
    <div style="background: linear-gradient(135deg, #1E3A8A 0%, #312E81 100%); color: white; padding: 1.8rem 2.2rem; border-radius: 16px; margin-bottom: 1.5rem; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
            <div>
                <span style="background: rgba(255,255,255,0.2); color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.78rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;">Self-Assessment Profile</span>
                <h1 style="margin: 0.5rem 0 0.2rem 0; font-size: 2rem; color: white; font-weight: 800;">
                    {user_name}'s Performance Summary
                </h1>
                <p style="margin: 0; color: #E0E7FF; font-size: 0.95rem;">
                    Participant Email: <strong>{active_user['email']}</strong>
                    {f" • {active_user['institution']}" if active_user.get('institution') else ""}
                </p>
            </div>
            <div style="text-align: right;">
                <span style="background: #10B981; color: white; padding: 6px 14px; border-radius: 8px; font-weight: 700; font-size: 0.9rem;">
                    Active Session
                </span>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# 3. NON-CERTIFICATION DISCLAIMER
st.info(f"ℹ️ **Notice on Assessment Results:** {CERTIFICATION_DISCLAIMER}")

# 4. LOAD ASSESSMENT HISTORY & COMPUTE SUMMARY
history_data = fetch_user_history(user_id)
summary = calculate_self_assessment_summary(history_data)

if not history_data:
    st.markdown("<br>", unsafe_allow_html=True)
    st.warning("You haven't completed any self-assessments yet. Start your first assessment to unlock detailed performance tracking!")
    c1, _ = st.columns([1.5, 3])
    with c1:
        if st.button("🚀 Start Your First Assessment", type="primary", use_container_width=True):
            st.switch_page("pages/03_Test_Selection.py")
    st.stop()

# --------------------------------------------------------
# 5. OVERALL PERFORMANCE METRICS (KPIs)
# --------------------------------------------------------
st.markdown("### Overall Performance Overview")

kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
with kpi1:
    st.metric(label="Total Completed Tests", value=summary["total_attempts"])
with kpi2:
    st.metric(label="Overall Average Score", value=f"{summary['overall_average_score']}%")
with kpi3:
    st.metric(label="Best Score Achieved", value=f"{summary['overall_best_score']}%")
with kpi4:
    st.metric(label="Overall Accuracy", value=f"{summary['overall_accuracy']}%")
with kpi5:
    st.metric(label="Strongest Category", value=summary["strongest_observed_category"] or "Pending Data")

st.markdown("<br>", unsafe_allow_html=True)

# --------------------------------------------------------
# 6. CATEGORY PERFORMANCE BREAKDOWN
# --------------------------------------------------------
st.markdown("### Category Performance Breakdown")
st.write("Observed results across individual learning domains (Grammar, Reading, and Listening):")

col_g, col_r, col_l = st.columns(3)

def render_category_card(cat_name: str, icon: str, border_color: str, cat_data: dict):
    attempts = cat_data["number_of_attempts"]
    avg = cat_data["average_score"]
    best = cat_data["best_score"]
    latest = f"{cat_data['latest_score']}%" if cat_data['latest_score'] is not None else "None"
    acc = cat_data["accuracy"]

    st.markdown(
        f"""
        <div style="background: white; border: 2px solid {border_color}; border-radius: 12px; padding: 1.2rem; box-shadow: 0 2px 4px rgba(0,0,0,0.04); height: 100%;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <h4 style="margin: 0; color: #1E293B; font-weight: 700; font-size: 1.15rem;">{icon} {cat_name}</h4>
                <span style="background: {border_color}22; color: {border_color}; font-weight: 700; padding: 2px 10px; border-radius: 10px; font-size: 0.8rem;">
                    {attempts} attempt(s)
                </span>
            </div>
            <div style="margin-bottom: 8px; font-size: 0.95rem; color: #475569;">
                <strong>Average Score:</strong> <span style="font-size: 1.1rem; font-weight: 700; color: #0F172A;">{avg}%</span>
            </div>
            <div style="font-size: 0.88rem; color: #64748B; line-height: 1.6;">
                <div>🎯 <strong>Accuracy:</strong> {acc}%</div>
                <div>⭐ <strong>Best Score:</strong> {best}%</div>
                <div>⏱️ <strong>Latest Score:</strong> {latest}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_g:
    render_category_card("Grammar", "📝", "#3B82F6", summary["categories"]["Grammar"])
with col_r:
    render_category_card("Reading", "📖", "#10B981", summary["categories"]["Reading"])
with col_l:
    render_category_card("Listening", "🎧", "#8B5CF6", summary["categories"]["Listening"])

st.markdown("<br><hr>", unsafe_allow_html=True)

# --------------------------------------------------------
# 7. INTERACTIVE VISUAL SUMMARIES (PLOTLY CHARTS)
# --------------------------------------------------------
st.markdown("### Visual Performance Summaries")

chart_col1, chart_col2 = st.columns(2)

# Chart 1: Category Comparison (Average vs Best)
with chart_col1:
    st.markdown("##### Category Score Comparison")
    cats = ["Grammar", "Reading", "Listening"]
    avg_vals = [summary["categories"][c]["average_score"] for c in cats]
    best_vals = [summary["categories"][c]["best_score"] for c in cats]

    fig_cat = go.Figure(data=[
        go.Bar(name="Average Score", x=cats, y=avg_vals, marker_color="#3B82F6"),
        go.Bar(name="Best Score", x=cats, y=best_vals, marker_color="#10B981"),
    ])
    fig_cat.update_layout(
        barmode="group",
        yaxis=dict(range=[0, 105], title="Score (%)"),
        xaxis=dict(title="Category"),
        margin=dict(l=20, r=20, t=30, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=320,
    )
    st.plotly_chart(fig_cat, use_container_width=True, key="history_cat_chart")

# Chart 2: Progress Over Time
with chart_col2:
    st.markdown("##### Score Progression Over Time")
    chron_items = summary["chronological_attempts"]

    if len(chron_items) >= 1:
        df_chron = pd.DataFrame(chron_items)
        fig_time = px.line(
            df_chron,
            x="date",
            y="score",
            color="category",
            markers=True,
            hover_data=["difficulty", "accuracy", "number_of_questions"],
            color_discrete_map={"Grammar": "#3B82F6", "Reading": "#10B981", "Listening": "#8B5CF6"},
        )
        fig_time.update_layout(
            yaxis=dict(range=[0, 105], title="Score (%)"),
            xaxis=dict(title="Assessment Date"),
            margin=dict(l=20, r=20, t=30, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            height=320,
        )
        st.plotly_chart(fig_time, use_container_width=True, key="history_time_chart")
    else:
        st.info("Complete more assessments to view your score trend line.")

st.markdown("<br>", unsafe_allow_html=True)

# --------------------------------------------------------
# 8. DESCRIPTIVE OBSERVATIONS & FEEDBACK
# --------------------------------------------------------
with st.container():
    feedback_html = "".join([f"<li style='margin-bottom: 8px; color: #1E293B;'>{pt}</li>" for pt in summary["descriptive_feedback"]])
    feedback_box_html = f"""<div style="background: #F8FAFC; border-left: 4px solid #3B82F6; padding: 1.2rem 1.6rem; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
<ul style="margin: 0; padding-left: 1.2rem; font-size: 0.96rem; line-height: 1.6;">
{feedback_html}
</ul>
</div>"""
    st.markdown(feedback_box_html, unsafe_allow_html=True)

st.markdown("<br><hr>", unsafe_allow_html=True)

# --------------------------------------------------------
# 9. DETAILED ASSESSMENT HISTORY TABLE
# --------------------------------------------------------
st.markdown("### Detailed Assessment History")
st.write("Browse and filter your individual test records:")

f_col1, f_col2, _ = st.columns([1.5, 1.5, 3])
with f_col1:
    filter_category = st.selectbox("Filter Category", options=["All", "Grammar", "Reading", "Listening"], index=0)
with f_col2:
    filter_difficulty = st.selectbox("Filter Difficulty", options=["All", "Easy", "Medium", "Hard"], index=0)

filtered_history = history_data
if filter_category != "All":
    filtered_history = [h for h in filtered_history if h["category"].lower() == filter_category.lower()]
if filter_difficulty != "All":
    filtered_history = [h for h in filtered_history if h["difficulty"].lower() == filter_difficulty.lower()]

if filtered_history:
    table_rows = []
    for idx, h in enumerate(filtered_history):
        table_rows.append({
            "No": idx + 1,
            "Date": h["date"],
            "Category": h["category"],
            "Difficulty": h["difficulty"],
            "Score (%)": f"{h['score']}%",
            "Correct": h["correct"],
            "Incorrect": h["incorrect"],
            "Questions": h["number_of_questions"],
            "Accuracy": f"{h['accuracy']}%",
            "Duration": h["duration"],
        })

    df_table = pd.DataFrame(table_rows)
    st.dataframe(df_table, use_container_width=True, hide_index=True)
else:
    st.info("No attempts match the selected filters.")

st.markdown("<br><hr>", unsafe_allow_html=True)

# --------------------------------------------------------
# 10. ACTION NAVIGATION BUTTONS
# --------------------------------------------------------
b_col1, b_col2, _ = st.columns([1.8, 1.8, 3])
with b_col1:
    if st.button("🎯 Choose Another Assessment", type="primary", use_container_width=True):
        st.switch_page("pages/03_Test_Selection.py")
with b_col2:
    if st.button("🏠 Back to Home", use_container_width=True):
        st.switch_page("pages/01_Home.py")
