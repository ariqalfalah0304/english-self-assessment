"""
Assessment Result Page (Phase 6).
Displays:
- Category & Level
- Total questions, correct answers, incorrect answers
- Score percentage & accuracy
- Completion time / duration if available
- Completed attempt saved in SQLite
- Action buttons: Try Easy, Try Medium, Try Hard, Choose Another Test, Finish Assessment
"""

import streamlit as st
from config.settings import APP_NAME
from services.user_service import get_active_user_session, is_user_authenticated
from services.quiz_engine import (
    SESSION_KEY_COMPLETED_ATTEMPT,
    reset_quiz_session,
    restart_with_difficulty,
    prepare_skill_quiz_session,
    prepare_final_exam_session,
)
from services.scoring_service import get_attempt_summary
from database.db import get_connection
from database import queries
from components.navigation import inject_custom_navigation_css
from components.ui_styles import inject_global_ui_styles

st.set_page_config(
    page_title=f"Assessment Result — {APP_NAME}",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_custom_navigation_css()
inject_global_ui_styles()

# 1. ENFORCE GUARDS
if not is_user_authenticated():
    st.error("🔒 Please provide your identity first.")
    if st.button("Go to Identity Page"):
        st.switch_page("pages/02_Identity.py")
    st.stop()

attempt_id = st.session_state.get(SESSION_KEY_COMPLETED_ATTEMPT)
if not attempt_id:
    st.warning("⚠️ No completed assessment results found in this session.")
    if st.button("Start Assessment 🎯", type="primary"):
        st.switch_page("pages/03_Test_Selection.py")
    st.stop()

active_user = get_active_user_session()

# Fetch attempt summary & question breakdown from SQLite
with get_connection() as conn:
    summary = get_attempt_summary(conn, attempt_id)
    answers = queries.get_answers_by_attempt(conn, attempt_id)
    attempt_questions = queries.get_attempt_questions(conn, attempt_id)
    audio_map = {
        q.id: queries.get_audio_file_by_question_id(conn, q.id)
        for _, q in attempt_questions
        if q.id is not None
    }

if not summary:
    st.error("Could not load attempt summary from database.")
    st.stop()

score = summary["score"]
total = summary["total_questions"]
correct = summary["correct_answers"]
incorrect = summary["incorrect_answers"]
accuracy = summary["accuracy"]
category = summary["category"]
difficulty = summary["difficulty"]
duration_sec = summary["duration_seconds"]

# Skill progression state
skill_num = st.session_state.get("skill_completed_number") or summary.get("skill_number")
if skill_num is None and difficulty and difficulty.startswith("Skill "):
    try:
        skill_num = int(difficulty.split()[1])
    except (IndexError, ValueError):
        pass

skill_name = st.session_state.get("skill_completed_name") or summary.get("skill_name") or (f"Skill {skill_num}" if skill_num else "")
is_skill_mode = bool(skill_num)

passing_threshold = float(st.session_state.get("quiz_passing_score", 70.0))
# An attempt passes if the score is >= passing threshold (70.0%), or if recorded as passed
is_passed = (score >= passing_threshold) or bool(st.session_state.get("skill_result_passed")) or (summary.get("is_passed") == 1)

# Format duration string
if duration_sec is not None:
    if duration_sec >= 60:
        minutes = duration_sec // 60
        seconds = duration_sec % 60
        duration_display = f"{minutes}m {seconds}s"
    else:
        duration_display = f"{duration_sec}s"
else:
    duration_display = "N/A"

# Determine status badge & color gradient
if is_skill_mode:
    if is_passed:
        badge_text = "🎉 SELAMAT! ANDA LOLOS PASSING GRADE"
        header_gradient = "linear-gradient(135deg, #059669 0%, #10B981 100%)"
        page_heading = f"{category} — Skill {skill_num}: {skill_name}"
    else:
        badge_text = "⚠️ BELUM LOLOS PASSING GRADE (70%)"
        header_gradient = "linear-gradient(135deg, #DC2626 0%, #EA580C 100%)"
        page_heading = f"{category} — Skill {skill_num}: {skill_name}"
else:
    if score >= 80:
        badge_text = "🌟 Excellent Mastery!"
        header_gradient = "linear-gradient(135deg, #059669 0%, #10B981 100%)"
    elif score >= 60:
        badge_text = "👍 Good Job! Competent Performance."
        header_gradient = "linear-gradient(135deg, #2563EB 0%, #3B82F6 100%)"
    else:
        badge_text = "💪 Needs Improvement. Practice Makes Perfect!"
        header_gradient = "linear-gradient(135deg, #D97706 0%, #F59E0B 100%)"
    page_heading = f"{category} — {difficulty} Result"

# Result Banner
st.markdown(
    f"""<div style="background: {header_gradient}; padding: 2.2rem 2rem; border-radius: 16px; color: white; margin-bottom: 1.5rem; text-align: center; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);">
<span style="background: rgba(255, 255, 255, 0.25); padding: 5px 18px; border-radius: 20px; font-size: 0.85rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;">
{badge_text}
</span>
<h1 style="font-size: 2.3rem; margin: 0.8rem 0 0.2rem 0; font-weight: 800;">
{page_heading}
</h1>
<p style="margin: 0; opacity: 0.95; font-size: 1.05rem;">
Peserta: <strong>{active_user['name']}</strong> ({active_user['email']})
</p>
</div>""",
    unsafe_allow_html=True,
)

# Fetch user skills status for category to check next skill availability
with get_connection() as conn:
    cat_obj = queries.get_category_by_name(conn, category)
    if is_skill_mode and is_passed and cat_obj and skill_num:
        queries.record_user_skill_attempt(
            conn=conn,
            user_id=active_user["id"],
            category_id=cat_obj.id,
            skill_number=skill_num,
            score=score,
            passing_score=passing_threshold,
        )
    user_skills = queries.get_user_skills_status(conn, active_user["id"], cat_obj.id) if cat_obj else []

max_skill_num = max((s["skill_number"] for s in user_skills), default=skill_num or 1)
has_next_skill = (skill_num is not None and skill_num < max_skill_num)

# Unlocking status banner for skill mode
if is_skill_mode:
    if is_passed:
        if has_next_skill:
            b_title = f"🔓 Skill {skill_num + 1} Sekarang Telah Terbuka!"
            b_desc = f"Skor Anda: <strong>{score}%</strong> (Passing grade: <strong>70%</strong>). Anda telah berhasil menguasai materi ini. Silakan lanjut ke skill berikutnya!"
        else:
            b_title = f"🎓 Selamat! Anda Telah Meloloskan Seluruh Skill di Kategori {category}!"
            b_desc = f"Skor Anda: <strong>{score}%</strong>. Ujian Gabungan (50 Soal Acak) dari {len(user_skills)} skill sekarang telah terbuka!"

        st.markdown(
            f"""<div style="background: #ECFDF5; border: 2px solid #10B981; border-radius: 12px; padding: 1.2rem; margin-bottom: 1.5rem; text-align: center;">
<h3 style="color: #065F46; margin: 0 0 0.3rem 0; font-size: 1.3rem;">{b_title}</h3>
<p style="color: #047857; margin: 0; font-size: 0.95rem;">
{b_desc}
</p>
</div>""",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""<div style="background: #FEF2F2; border: 2px solid #EF4444; border-radius: 12px; padding: 1.2rem; margin-bottom: 1.5rem; text-align: center;">
<h3 style="color: #991B1B; margin: 0 0 0.3rem 0; font-size: 1.3rem;">🔒 Belum Lolos Passing Grade (70%)</h3>
<p style="color: #B91C1C; margin: 0; font-size: 0.95rem;">
Skor Anda: <strong>{score}%</strong> (Passing grade minimal: <strong>70%</strong>). Anda belum lolos. Silakan ulangi pengerjaan Skill {skill_num} hingga mencapai 70%.
</p>
</div>""",
            unsafe_allow_html=True,
        )

# Metric KPI Cards
c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    st.metric(label="Score Percentage", value=f"{score}%")
with c2:
    st.metric(label="Correct Answers", value=f"{correct} / {total}")
with c3:
    st.metric(label="Incorrect Answers", value=f"{incorrect} / {total}")
with c4:
    st.metric(label="Accuracy", value=f"{accuracy}%")
with c5:
    st.metric(label="Completion Time", value=duration_display)

st.markdown("<br><hr>", unsafe_allow_html=True)

# ---------------------------------------------
# ACTION BUTTONS
# ---------------------------------------------
is_final_exam_mode = bool(st.session_state.get("is_final_exam")) or difficulty == "Ujian Gabungan"

if is_final_exam_mode:
    b1, b2, b3 = st.columns([2.5, 2, 1.2])
    with b1:
        if st.button("🔄 Ulangi Ujian Gabungan (50 Soal Acak)", type="primary", use_container_width=True):
            prepare_final_exam_session(category, cat_obj.id if cat_obj else None)
            st.switch_page("pages/04_Quiz.py")
    with b2:
        if st.button("📚 Kembali ke Pilih Skill / Kategori", use_container_width=True):
            reset_quiz_session()
            st.switch_page("pages/03_Test_Selection.py")
    with b3:
        if st.button("🏁 Selesai", use_container_width=True):
            reset_quiz_session()
            st.switch_page("pages/01_Home.py")

elif is_skill_mode:
    if is_passed:
        b1, b2, b3, b4 = st.columns([2.5, 1.8, 1.8, 1.2])
        with b1:
            if has_next_skill:
                if st.button(f"🚀 Lanjut ke Skill {skill_num + 1}", type="primary", use_container_width=True):
                    prepare_skill_quiz_session(category, skill_num + 1, f"Skill {skill_num + 1}")
                    st.switch_page("pages/04_Quiz.py")
            else:
                if st.button("🎓 Mulai Ujian Gabungan (50 Soal Acak)", type="primary", use_container_width=True):
                    prepare_final_exam_session(category, cat_obj.id if cat_obj else None)
                    st.switch_page("pages/04_Quiz.py")
        with b2:
            if st.button(f"🔄 Ulangi Skill {skill_num}", use_container_width=True):
                prepare_skill_quiz_session(category, skill_num, skill_name)
                st.switch_page("pages/04_Quiz.py")
        with b3:
            if st.button("📚 Pilih Skill / Kategori Lain", use_container_width=True):
                reset_quiz_session()
                st.switch_page("pages/03_Test_Selection.py")
        with b4:
            if st.button("🏁 Selesai", use_container_width=True):
                reset_quiz_session()
                st.switch_page("pages/01_Home.py")
    else:
        b1, b2, b3 = st.columns([2.5, 2, 1.2])
        with b1:
            if st.button(f"🔄 Ulangi Skill {skill_num}", type="primary", use_container_width=True):
                prepare_skill_quiz_session(category, skill_num, skill_name)
                st.switch_page("pages/04_Quiz.py")
        with b2:
            if st.button("📚 Kembali ke Daftar Skill", use_container_width=True):
                reset_quiz_session()
                st.switch_page("pages/03_Test_Selection.py")
        with b3:
            if st.button("🏁 Selesai", use_container_width=True):
                reset_quiz_session()
                st.switch_page("pages/01_Home.py")

else:
    b1, b2, b3 = st.columns([2, 2, 1.5])
    with b1:
        if st.button("🔄 Ulangi Assessment", type="primary", use_container_width=True):
            st.switch_page("pages/04_Quiz.py")
    with b2:
        if st.button("📚 Pilih Ujian Lain", use_container_width=True):
            reset_quiz_session()
            st.switch_page("pages/03_Test_Selection.py")
    with b3:
        if st.button("🏁 Selesai", use_container_width=True):
            reset_quiz_session()
            st.switch_page("pages/01_Home.py")

st.markdown("<br>", unsafe_allow_html=True)
c_hist, _ = st.columns([2.5, 2.5])
with c_hist:
    if st.button("📈 View My Self-Assessment Summary & History", type="primary", use_container_width=True):
        st.switch_page("pages/06_History.py")

st.markdown("<br>", unsafe_allow_html=True)

# Detailed Question Breakdown Expander
with st.expander("🔍 View Detailed Question Breakdown & Explanations", expanded=False):
    ans_map = {a.question_id: a for a in answers}

    for order, q in attempt_questions:
        ans_record = ans_map.get(q.id)
        user_choice = ans_record.user_answer if ans_record else "No Answer"
        is_corr = bool(ans_record.is_correct) if ans_record else False

        status_icon = "✅ Correct" if is_corr else "❌ Incorrect"
        border_col = "#BBF7D0" if is_corr else "#FECACA"
        bg_col = "#F0FDF4" if is_corr else "#FEF2F2"

        audio_rec = audio_map.get(q.id)
        transcript_section = ""
        if audio_rec and audio_rec.transcript:
            transcript_section = f"""<div style="font-size: 0.88rem; color: #4B5563; margin-top: 0.5rem; background: #F8FAFC; border: 1px dashed #CBD5E1; border-radius: 6px; padding: 8px 12px; white-space: pre-line;">
🎧 <strong>Spoken Audio Transcript:</strong><br>{audio_rec.transcript}
</div>"""

        explanation_section = ""
        if q.explanation:
            explanation_section = f"""<div style="font-size: 0.9rem; color: #4B5563; margin-top: 0.5rem; padding-top: 0.5rem; border-top: 1px dashed {border_col};">
<strong>Explanation:</strong> {q.explanation}
</div>"""

        card_html = f"""<div style="background: {bg_col}; border: 1px solid {border_col}; border-radius: 10px; padding: 1.2rem 1.4rem; margin-bottom: 1rem;">
<div style="font-weight: 700; color: #111827; font-size: 1.05rem; margin-bottom: 0.4rem;">
Question {order}: {q.question_text}
</div>
<div style="font-size: 0.95rem; color: #374151; margin-bottom: 0.3rem;">
Your Answer: <strong>{user_choice}</strong> • Correct Answer: <strong>{q.correct_answer}</strong> ({status_icon})
</div>
{transcript_section}
{explanation_section}
</div>"""

        st.markdown(card_html, unsafe_allow_html=True)
