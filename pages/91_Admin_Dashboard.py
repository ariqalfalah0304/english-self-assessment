"""
Admin Dashboard Page (Phase 10).
Displays platform overview metrics:
- Total users
- Total assessment attempts
- Total questions & active questions
- Attempts breakdown by category (Grammar, Reading, Listening)
- Interactive Plotly charts for category distribution and difficulty volume
- Quick navigation to User Management and Assessment Results
Protected by require_admin_auth().
"""

import streamlit as st
import pandas as pd
from config.settings import APP_NAME
from services.admin_service import require_admin_auth, logout_admin_session
from services.admin_dashboard_service import (
    fetch_dashboard_summary,
    build_category_distribution_chart,
    build_difficulty_distribution_chart,
)
from components.navigation import inject_custom_navigation_css, render_admin_header
from components.ui_styles import inject_global_ui_styles

st.set_page_config(
    page_title=f"Admin Dashboard — {APP_NAME}",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply route protection & navigation separation
inject_custom_navigation_css()
inject_global_ui_styles()
require_admin_auth()

# Administrative Header
render_admin_header(
    title="Administrator Dashboard",
    subtitle="Global Assessment Analytics, Volume Metrics & Performance",
)

# Fetch Aggregated Data
stats = fetch_dashboard_summary()

total_users = stats["total_users"]
total_attempts = stats["total_attempts"]
total_questions = stats["total_questions"]
active_questions = stats["active_questions"]
grammar_attempts = stats["grammar_attempts"]
reading_attempts = stats["reading_attempts"]
listening_attempts = stats["listening_attempts"]
avg_score = stats["average_score"]
category_counts = stats["category_counts"]
difficulty_counts = stats["difficulty_counts"]

# --------------------------------------------------------
# 1. PRIMARY PLATFORM METRICS
# --------------------------------------------------------
st.markdown("### Platform Overview")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(
        f"""
        <div style="background: #EFF6FF; border: 1px solid #BFDBFE; border-left: 5px solid #3B82F6; border-radius: 10px; padding: 1.2rem 1.4rem;">
            <div style="font-size: 0.85rem; font-weight: 700; color: #1E40AF; text-transform: uppercase;">Total Participants</div>
            <div style="font-size: 2.2rem; font-weight: 800; color: #1E3A8A; margin: 0.3rem 0;">{total_users:,}</div>
            <div style="font-size: 0.82rem; color: #64748B;">Registered assessment users</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        f"""
        <div style="background: #F5F3FF; border: 1px solid #DDD6FE; border-left: 5px solid #8B5CF6; border-radius: 10px; padding: 1.2rem 1.4rem;">
            <div style="font-size: 0.85rem; font-weight: 700; color: #5B21B6; text-transform: uppercase;">Total Attempts</div>
            <div style="font-size: 2.2rem; font-weight: 800; color: #4C1D95; margin: 0.3rem 0;">{total_attempts:,}</div>
            <div style="font-size: 0.82rem; color: #64748B;">Completed & active test sessions</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col3:
    st.markdown(
        f"""
        <div style="background: #ECFDF5; border: 1px solid #A7F3D0; border-left: 5px solid #10B981; border-radius: 10px; padding: 1.2rem 1.4rem;">
            <div style="font-size: 0.85rem; font-weight: 700; color: #065F46; text-transform: uppercase;">Total Questions</div>
            <div style="font-size: 2.2rem; font-weight: 800; color: #064E3B; margin: 0.3rem 0;">{total_questions:,}</div>
            <div style="font-size: 0.82rem; color: #64748B;">Stored across all categories</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col4:
    inactive_count = max(0, total_questions - active_questions)
    st.markdown(
        f"""
        <div style="background: #FEF3C7; border: 1px solid #FDE68A; border-left: 5px solid #F59E0B; border-radius: 10px; padding: 1.2rem 1.4rem;">
            <div style="font-size: 0.85rem; font-weight: 700; color: #92400E; text-transform: uppercase;">Active Questions</div>
            <div style="font-size: 2.2rem; font-weight: 800; color: #78350F; margin: 0.3rem 0;">{active_questions:,}</div>
            <div style="font-size: 0.82rem; color: #64748B;">{inactive_count} drafts / inactive</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

# --------------------------------------------------------
# 2. CATEGORY VOLUME BREAKDOWN
# --------------------------------------------------------
st.markdown("### Category Volume & Mean Performance")

c_gram, c_read, c_list, c_score = st.columns(4)

with c_gram:
    st.metric(
        label="📖 Grammar Attempts",
        value=f"{grammar_attempts:,}",
        help="Total tests initiated for Grammar",
    )

with c_read:
    st.metric(
        label="📚 Reading Attempts",
        value=f"{reading_attempts:,}",
        help="Total tests initiated for Reading",
    )

with c_list:
    st.metric(
        label="🎧 Listening Attempts",
        value=f"{listening_attempts:,}",
        help="Total tests initiated for Listening",
    )

with c_score:
    st.metric(
        label="🏆 Average Platform Score",
        value=f"{avg_score}%" if total_attempts > 0 else "N/A",
        help="Mean score across all completed assessment sessions",
    )

st.markdown("<br><hr>", unsafe_allow_html=True)

# --------------------------------------------------------
# 3. INTERACTIVE PLOTLY VISUALIZATIONS
# --------------------------------------------------------
st.markdown("### Distribution Analytics")

chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    fig_cat = build_category_distribution_chart(category_counts)
    st.plotly_chart(fig_cat, use_container_width=True, key="admin_dash_cat_chart")

with chart_col2:
    fig_diff = build_difficulty_distribution_chart(difficulty_counts)
    st.plotly_chart(fig_diff, use_container_width=True, key="admin_dash_diff_chart")

st.markdown("<br><hr>", unsafe_allow_html=True)

# --------------------------------------------------------
# 4. QUICK ACTIONS & NAVIGATION
# --------------------------------------------------------
st.markdown("### Administrative Quick Actions")

b_qbank, b_analytics, b_import, b_users, b_results, b_logout = st.columns(6)

with b_qbank:
    if st.button("📚 Question Bank", use_container_width=True, type="primary"):
        st.switch_page("pages/93_Admin_Question_Bank.py")

with b_analytics:
    if st.button("📊 Analytics", use_container_width=True):
        st.switch_page("pages/95_Admin_Analytics.py")

with b_import:
    if st.button("📥 Import (.docx)", use_container_width=True):
        st.switch_page("pages/94_Admin_Import.py")

with b_users:
    if st.button("👥 Participants", use_container_width=True):
        st.switch_page("pages/92_Admin_Users.py")

with b_results:
    if st.button("📈 Results", use_container_width=True):
        st.switch_page("pages/96_Admin_Results.py")

with b_logout:
    if st.button("🚪 Logout", use_container_width=True):
        logout_admin_session()
        st.switch_page("pages/90_Admin_Login.py")
