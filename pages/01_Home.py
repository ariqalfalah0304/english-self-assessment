"""
English Self-Assessment Platform - Landing Page (Phase 18 UI Refinement).
Directs users to the Participant Identity page to begin assessment.
"""

import streamlit as st
from config.settings import APP_NAME, APP_TAGLINE
from components.ui_styles import inject_global_ui_styles


def render_home():
    st.set_page_config(page_title="English Self-Assessment", page_icon="🎓", layout="wide")
    inject_global_ui_styles()

    # Hero Banner Container
    st.markdown(
        f"""
        <div style="background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%); border-radius: 20px; padding: 3rem 2rem; color: #FFFFFF; text-align: center; margin-bottom: 2.5rem; box-shadow: 0 10px 25px -5px rgba(37, 99, 235, 0.25);">
            <div style="display: inline-block; background: rgba(255, 255, 255, 0.18); backdrop-filter: blur(8px); padding: 6px 18px; border-radius: 9999px; font-size: 0.85rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 1.2rem; border: 1px solid rgba(255, 255, 255, 0.3);">
                English Language Self-Assessment Platform
            </div>
            <h1 style="font-size: 3rem; margin: 0 0 0.8rem 0; font-weight: 800; letter-spacing: -0.5px; color: #FFFFFF;">
                🎓 {APP_NAME}
            </h1>
            <p style="font-size: 1.35rem; color: #DBEAFE; font-weight: 500; max-width: 680px; margin: 0 auto 1.2rem auto; line-height: 1.4;">
                {APP_TAGLINE}
            </p>
            <p style="max-width: 720px; margin: 0 auto; color: #E0E7FF; font-size: 1.05rem; line-height: 1.6; opacity: 0.95;">
                An interactive, research-grounded web application designed to help learners measure and reflect on their English competency independently across Grammar, Reading Comprehension, and Spoken Listening.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Core Competencies Preview
    st.markdown("### 📚 Assessment Pillars")
    p1, p2, p3 = st.columns(3)

    with p1:
        st.markdown(
            """
            <div style="background: #FFFFFF; border: 1.5px solid #E2E8F0; border-top: 5px solid #4F46E5; border-radius: 14px; padding: 1.6rem; min-height: 210px; height: 100%; display: flex; flex-direction: column; justify-content: space-between; box-shadow: 0 2px 4px rgba(0,0,0,0.03);">
                <div>
                    <div style="font-size: 2rem; margin-bottom: 0.5rem;">📖</div>
                    <h3 style="margin: 0 0 0.3rem 0; color: #1E293B; font-size: 1.25rem; font-weight: 700;">Grammar Mastery</h3>
                    <p style="color: #64748B; font-size: 0.9rem; line-height: 1.5; margin: 0;">
                        Structure, syntax, subject-verb agreements, and verb tenses across varying sentence complexities.
                    </p>
                </div>
                <div style="font-size: 0.78rem; font-weight: 700; color: #4F46E5; text-transform: uppercase;">Structure & Rules</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with p2:
        st.markdown(
            """
            <div style="background: #FFFFFF; border: 1.5px solid #E2E8F0; border-top: 5px solid #059669; border-radius: 14px; padding: 1.6rem; min-height: 210px; height: 100%; display: flex; flex-direction: column; justify-content: space-between; box-shadow: 0 2px 4px rgba(0,0,0,0.03);">
                <div>
                    <div style="font-size: 2rem; margin-bottom: 0.5rem;">📚</div>
                    <h3 style="margin: 0 0 0.3rem 0; color: #1E293B; font-size: 1.25rem; font-weight: 700;">Reading Comprehension</h3>
                    <p style="color: #64748B; font-size: 0.9rem; line-height: 1.5; margin: 0;">
                        Passage analysis, main ideas, vocabulary in context, analytical inference, and tone identification.
                    </p>
                </div>
                <div style="font-size: 0.78rem; font-weight: 700; color: #059669; text-transform: uppercase;">Context & Meaning</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with p3:
        st.markdown(
            """
            <div style="background: #FFFFFF; border: 1.5px solid #E2E8F0; border-top: 5px solid #D97706; border-radius: 14px; padding: 1.6rem; min-height: 210px; height: 100%; display: flex; flex-direction: column; justify-content: space-between; box-shadow: 0 2px 4px rgba(0,0,0,0.03);">
                <div>
                    <div style="font-size: 2rem; margin-bottom: 0.5rem;">🎧</div>
                    <h3 style="margin: 0 0 0.3rem 0; color: #1E293B; font-size: 1.25rem; font-weight: 700;">Listening Comprehension</h3>
                    <p style="color: #64748B; font-size: 0.9rem; line-height: 1.5; margin: 0;">
                        Natural spoken dialogues, announcements, academic lectures, and audio clue retention.
                    </p>
                </div>
                <div style="font-size: 0.78rem; font-weight: 700; color: #D97706; text-transform: uppercase;">Acoustic Understanding</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br><hr style='border: none; border-top: 1px solid #E2E8F0; margin: 1.5rem 0;'>", unsafe_allow_html=True)

    # How It Works Flow
    st.markdown("### 🗺️ Four Steps to Self-Improvement")
    s1, s2, s3, s4 = st.columns(4)

    steps = [
        {"num": "1", "title": "Participant Identity", "desc": "Provide your name and email to track your learning journey."},
        {"num": "2", "title": "Select Category", "desc": "Freely choose Grammar, Reading, or Listening without forced sequences."},
        {"num": "3", "title": "Choose Level", "desc": "Pick Easy, Medium, or Hard to match your current proficiency goals."},
        {"num": "4", "title": "Instant Explanations", "desc": "Get immediate audio/visual feedback, detailed keys, and analytics."},
    ]

    for col, st_info in zip([s1, s2, s3, s4], steps):
        with col:
            st.markdown(
                f"""
                <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 1.2rem; text-align: left; min-height: 160px; height: 100%;">
                    <div style="width: 32px; height: 32px; border-radius: 8px; background: #2563EB; color: white; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 0.95rem; margin-bottom: 0.6rem;">
                        {st_info['num']}
                    </div>
                    <h4 style="margin: 0 0 0.3rem 0; color: #0F172A; font-size: 1rem; font-weight: 700;">{st_info['title']}</h4>
                    <p style="margin: 0; color: #64748B; font-size: 0.85rem; line-height: 1.45;">{st_info['desc']}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<br><br>", unsafe_allow_html=True)

    # Call To Action Section
    c_btn1, c_btn2, c_btn3 = st.columns([1, 2, 1])
    with c_btn2:
        if st.button("🚀 START SELF-ASSESSMENT", use_container_width=True, type="primary"):
            st.switch_page("pages/02_Identity.py")

        st.markdown(
            """
            <div style="text-align: center; color: #64748B; font-size: 0.9rem; margin-top: 0.8rem;">
                <span>✨ Practice anytime. Track your progress. Build confidence.</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<hr style='margin: 2rem 0 1.2rem 0; border: none; border-top: 1px dashed #CBD5E1;'>", unsafe_allow_html=True)

        ca1, ca2, ca3 = st.columns([1, 2, 1])
        with ca2:
            if st.button("🔐 Administrator Portal", use_container_width=True):
                st.switch_page("pages/90_Admin_Login.py")


render_home()
