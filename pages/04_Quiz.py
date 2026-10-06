"""
Interactive Quiz Interface for Grammar & Reading (Phase 7).
Features:
- Dual-mode: standard questions (Grammar) & passage-based questions (Reading)
- Reading passage presentation with title and formatted text
- Question type badge (Main Idea, Detail, Vocabulary, Reference, Inference, Author's Purpose)
- Configurable question count
- One question displayed at a time
- Real-time progress bar & question indicator
- Multiple-choice options A, B, C, D
- Instant feedback with positive/negative visual cue, message ("Good Job!" / "Sorry, try again.")
- Audio playback / controls for feedback sound assets (with graceful missing asset notices)
- Complete preservation of active quiz state
- Seamless transition to Result page on final question
"""

import streamlit as st
from config.settings import APP_NAME, DEFAULT_QUESTIONS_PER_TEST
from services.user_service import get_active_user_session, is_user_authenticated
from services.quiz_engine import (
    get_quiz_session,
    is_quiz_selection_ready,
    start_quiz_attempt,
    start_skill_quiz_attempt,
    start_final_exam_attempt,
    submit_current_answer,
    move_to_next_question,
    complete_current_attempt,
    reset_quiz_session,
    SESSION_KEY_ATTEMPT_ID,
)
from utils.audio import render_feedback_audio, render_listening_audio
from services.question_service import get_category_question_limit_setting
from components.navigation import inject_custom_navigation_css
from components.ui_styles import inject_global_ui_styles

st.set_page_config(
    page_title=f"Assessment — {APP_NAME}",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_custom_navigation_css()
inject_global_ui_styles()

# 1. GUARDS
if not is_user_authenticated():
    st.error("🔒 Access Denied: You must complete your identity before taking a test.")
    if st.button("Go to Identity Page 👤", type="primary"):
        st.switch_page("pages/02_Identity.py")
    st.stop()

if not is_quiz_selection_ready():
    st.warning("⚠️ Silakan pilih kategori dan skill terlebih dahulu.")
    if st.button("Pilih Skill Soal 🎯", type="primary"):
        st.switch_page("pages/03_Test_Selection.py")
    st.stop()

active_user = get_active_user_session()
quiz_state = get_quiz_session()

# Check if attempt is initiated
attempt_id = st.session_state.get(SESSION_KEY_ATTEMPT_ID)

# Category styling metadata
category_icons = {"Grammar": "📖", "Reading": "📚", "Listening": "🎧"}
cat_icon = category_icons.get(quiz_state["category"], "📝")
is_skill_mode = bool(quiz_state.get("skill_number"))
skill_num = quiz_state.get("skill_number")
skill_title = quiz_state.get("skill_name") or f"Skill {skill_num}"

is_final_exam = bool(quiz_state.get("is_final_exam"))

# ========================================================
# VIEW A: QUIZ PRE-START CONFIGURATION SCREEN
# ========================================================
if attempt_id is None:
    if is_final_exam:
        st.markdown(
            f"""<div style="background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%); padding: 2rem; border-radius: 16px; color: white; margin-bottom: 2rem; box-shadow: 0 10px 25px -5px rgba(37, 99, 235, 0.25);">
<span style="background: rgba(255, 255, 255, 0.25); border: 1px solid rgba(255, 255, 255, 0.4); padding: 4px 14px; border-radius: 20px; font-size: 0.8rem; font-weight: 700; text-transform: uppercase;">
{quiz_state['category']} • Final Mastery Exam
</span>
<h1 style="margin: 0.8rem 0 0.2rem 0; font-size: 2.2rem; font-weight: 800; color: #FFFFFF;">
{cat_icon} Ujian Gabungan — {quiz_state['category']} (50 Soal Final)
</h1>
<p style="margin: 0; opacity: 0.95; font-size: 1rem;">
Peserta: <strong>{active_user['name']}</strong> ({active_user['email']})
</p>
</div>""",
            unsafe_allow_html=True,
        )

        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f"### Persiapan Ujian Gabungan {quiz_state['category']}")
            st.markdown(
                f"""<div style="background: #FFFFFF; border: 1.5px solid #E2E8F0; border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem;">
<h4 style="margin: 0 0 0.8rem 0; color: #1E3A8A; font-size: 1.15rem;">📌 Ketentuan Ujian Gabungan:</h4>
<ul style="color: #475569; font-size: 0.95rem; line-height: 1.7; margin-bottom: 0;">
<li>Ujian Gabungan ini terdiri dari <strong>50 soal acak</strong>.</li>
<li>Soal diambil secara <strong>proporsional</strong> dari setiap skill yang telah Anda meloloskan.</li>
<li>Urutan soal dan posisi pilihan jawaban (A, B, C, D) diacak secara otomatis sehingga tidak dapat dihapal.</li>
<li>Anda akan mendapatkan pembahasan lengkap di setiap nomor soal.</li>
</ul>
</div>""",
                unsafe_allow_html=True,
            )

            if st.button(f" Mulai Ujian Gabungan {quiz_state['category']} (50 Soal Acak)", type="primary", use_container_width=True):
                success, attempt, questions, notice = start_final_exam_attempt(
                    user_id=active_user["id"],
                    category_name=quiz_state["category"],
                    requested_count=50,
                )
                if not success:
                    st.error(f"❌ Tidak dapat memulai Ujian Gabungan: {notice}")
                else:
                    if notice:
                        st.toast(notice, icon="ℹ️")
                    st.rerun()

        with col2:
            st.markdown(
                """<div style="background: #F9FAFB; border: 1px solid #E5E7EB; border-radius: 12px; padding: 1.5rem;">
<h4 style="margin-top: 0; color: #1F2937;">💡 Tips Ujian Gabungan</h4>
<p style="color: #4B5563; font-size: 0.9rem; line-height: 1.6;">
Ujian ini menguji pemahaman komprehensif Anda dari seluruh materi skill. Tetap fokus dan jawab setiap soal dengan baik.
</p>
</div>""",
                unsafe_allow_html=True,
            )
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🔄 Kembali ke Daftar Skill", use_container_width=True):
                reset_quiz_session()
                st.switch_page("pages/03_Test_Selection.py")

        st.stop()

    elif is_skill_mode:
        st.markdown(
            f"""<div style="background: linear-gradient(135deg, #1E1B4B 0%, #312E81 100%); padding: 2rem; border-radius: 16px; color: white; margin-bottom: 2rem;">
<span style="background: rgba(255, 255, 255, 0.2); padding: 4px 14px; border-radius: 20px; font-size: 0.8rem; font-weight: 700; text-transform: uppercase;">
{quiz_state['category']} • Sequential Mastery
</span>
<h1 style="margin: 0.8rem 0 0.2rem 0; font-size: 2.2rem; font-weight: 800;">
{cat_icon} {quiz_state['category']} — Skill {skill_num}: {skill_title}
</h1>
<p style="margin: 0; opacity: 0.9; font-size: 1rem;">
Peserta: <strong>{active_user['name']}</strong> ({active_user['email']})
</p>
</div>""",
            unsafe_allow_html=True,
        )

        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f"### Persiapan Skill {skill_num}")
            st.markdown(
                f"""<div style="background: #FFFFFF; border: 1.5px solid #E2E8F0; border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem;">
<h4 style="margin: 0 0 0.8rem 0; color: #1E1B4B; font-size: 1.15rem;">📌 Ketentuan Pengerjaan Skill:</h4>
<ul style="color: #475569; font-size: 0.95rem; line-height: 1.7; margin-bottom: 0;">
<li>Seluruh soal dalam <strong>Skill {skill_num}</strong> akan disajikan <strong>secara berurutan</strong>.</li>
<li>Passing grade kelulusan adalah <strong>70%</strong>.</li>
<li>Jika Anda berhasil mencapai nilai minimal <strong>70%</strong>, maka <strong>Skill {skill_num + 1}</strong> akan otomatis terbuka!</li>
<li>Jika nilai Anda di bawah 70%, Skill {skill_num + 1} tetap terkunci dan Anda dapat mengulangi Skill {skill_num}.</li>
</ul>
</div>""",
                unsafe_allow_html=True,
            )

            if st.button(f" Mulai Kerjakan Skill {skill_num}", type="primary", use_container_width=True):
                success, attempt, questions, notice = start_skill_quiz_attempt(
                    user_id=active_user["id"],
                    category_name=quiz_state["category"],
                    skill_number=skill_num,
                )
                if not success:
                    st.error(f"❌ Tidak dapat memulai assessment: {notice}")
                else:
                    if notice:
                        st.toast(notice, icon="ℹ️")
                    st.rerun()

        with col2:
            st.markdown(
                """<div style="background: #F9FAFB; border: 1px solid #E5E7EB; border-radius: 12px; padding: 1.5rem;">
<h4 style="margin-top: 0; color: #1F2937;">💡 Tips Belajar</h4>
<p style="color: #4B5563; font-size: 0.9rem; line-height: 1.6;">
Kerjakan setiap butir soal dengan cermat. Setelah memilih jawaban dan menekan tombol submit, Anda akan langsung melihat kunci jawaban dan pembahasan lengkapnya.
</p>
</div>""",
                unsafe_allow_html=True,
            )
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🔄 Kembali ke Daftar Skill", use_container_width=True):
                reset_quiz_session()
                st.switch_page("pages/03_Test_Selection.py")

        st.stop()

    else:
        st.markdown(
            f"""<div style="background: linear-gradient(135deg, #1E1B4B 0%, #312E81 100%); padding: 2rem; border-radius: 16px; color: white; margin-bottom: 2rem;">
<span style="background: rgba(255, 255, 255, 0.2); padding: 4px 14px; border-radius: 20px; font-size: 0.8rem; font-weight: 700; text-transform: uppercase;">
{quiz_state['category']} Assessment
</span>
<h1 style="margin: 0.8rem 0 0.2rem 0; font-size: 2.2rem; font-weight: 800;">
{cat_icon} {quiz_state['category']}
</h1>
<p style="margin: 0; opacity: 0.9; font-size: 1rem;">
Participant: <strong>{active_user['name']}</strong> ({active_user['email']})
</p>
</div>""",
            unsafe_allow_html=True,
        )

        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown("### Assessment Configuration")
            configured_limit = get_category_question_limit_setting(quiz_state["category"])
            base_opts = {4, 5, 10, 15, 20, 25, 30, 40, 50, configured_limit}
            slider_opts = sorted([x for x in base_opts if x >= 1])

            q_count = st.select_slider(
                "Select Number of Questions:",
                options=slider_opts,
                value=configured_limit,
                help=f"Standar jumlah soal untuk kategori {quiz_state['category']} adalah {configured_limit} soal.",
            )

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🚀 Start Assessment Now", type="primary", use_container_width=True):
                success, attempt, questions, notice = start_quiz_attempt(
                    user_id=active_user["id"],
                    category_name=quiz_state["category"],
                    difficulty=quiz_state.get("difficulty", "Standard"),
                    num_questions=q_count,
                )
                if not success:
                    st.error(f"❌ Could not initialize assessment: {notice}")
                else:
                    if notice:
                        st.toast(notice, icon="ℹ️")
                    st.rerun()

        with col2:
            st.markdown(
                """
                <div style="background: #F9FAFB; border: 1px solid #E5E7EB; border-radius: 12px; padding: 1.5rem;">
                    <h4 style="margin-top: 0; color: #1F2937;">📌 Instructions</h4>
                    <p style="color: #4B5563; font-size: 0.9rem; line-height: 1.6;">
                        Questions appear one at a time with instant audio and visual feedback.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🔄 Change Selection", use_container_width=True):
                reset_quiz_session()
                st.switch_page("pages/03_Test_Selection.py")

        st.stop()

# ========================================================
# VIEW B: ACTIVE QUIZ IN PROGRESS
# ========================================================
questions = quiz_state["selected_questions"]
current_idx = quiz_state["current_question_index"]
total_q = len(questions)

if current_idx >= total_q:
    st.info("Assessment questions completed. Finalizing score...")
    complete_current_attempt()
    st.switch_page("pages/05_Result.py")
    st.stop()

current_q = questions[current_idx]

# Progress calculations
progress_fraction = (current_idx + 1) / total_q
progress_pct = int(progress_fraction * 100)

# Top Bar: Progress and Question Indicator
col_meta1, col_meta2 = st.columns([3, 1])
with col_meta1:
    st.markdown(
        f"""
        <div style="display: flex; align-items: baseline; gap: 10px;">
            <h2 style="margin: 0; color: #1E3A8A; font-size: 1.6rem; font-weight: 800;">
                Question {current_idx + 1} of {total_q}
            </h2>
            <span style="color: #6B7280; font-size: 0.95rem; font-weight: 600;">
                ({cat_icon} {quiz_state['category']} • {'Skill ' + str(skill_num) + ': ' + skill_title if is_skill_mode else quiz_state['difficulty']})
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )
with col_meta2:
    st.markdown(
        f"""
        <div style="text-align: right; color: #4F46E5; font-weight: 700; font-size: 1.1rem;">
            {progress_pct}% Completed
        </div>
        """,
        unsafe_allow_html=True,
    )

st.progress(progress_fraction)
st.markdown("<div style='margin-bottom: 1.2rem;'></div>", unsafe_allow_html=True)

# Category styling metadata
cat_accents = {
    "Grammar": {"color": "#4F46E5", "bg": "#EEF2FF", "border": "#C7D2FE"},
    "Reading": {"color": "#059669", "bg": "#ECFDF5", "border": "#A7F3D0"},
    "Listening": {"color": "#D97706", "bg": "#FFFBEB", "border": "#FDE68A"},
}
accent = cat_accents.get(quiz_state["category"], {"color": "#2563EB", "bg": "#EFF6FF", "border": "#BFDBFE"})

# --------------------------------------------------------
# READING PASSAGE DISPLAY (If associated with a passage)
# --------------------------------------------------------
has_passage = bool(current_q.get("passage_text"))
if has_passage:
    passage_title = current_q.get("passage_title", "Reading Passage")
    passage_body = current_q["passage_text"]
    st.markdown(
        f"""
        <div style="background: #FFFFFF; border: 1.5px solid #CBD5E1; border-top: 5px solid {accent['color']}; border-radius: 14px; padding: 1.6rem; margin-bottom: 1.5rem; box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04);">
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 0.8rem; padding-bottom: 0.6rem; border-bottom: 1px solid #E2E8F0;">
                <span style="font-size: 1.3rem;">📜</span>
                <h4 style="margin: 0; color: #0F172A; font-size: 1.15rem; font-weight: 700;">{passage_title}</h4>
                <span style="margin-left: auto; background: {accent['bg']}; color: {accent['color']}; padding: 2px 10px; border-radius: 6px; font-size: 0.78rem; font-weight: 700;">Reading Reference</span>
            </div>
            <div style="color: #334155; font-size: 1rem; line-height: 1.75; white-space: pre-line; max-height: 360px; overflow-y: auto; padding-right: 6px;">
{passage_body}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# --------------------------------------------------------
# LISTENING AUDIO DISPLAY (For Listening questions)
# --------------------------------------------------------
is_listening = (quiz_state.get("category", "").lower() == "listening") or bool(current_q.get("audio_file"))
if is_listening:
    audio_path = current_q.get("audio_file")
    render_listening_audio(audio_path)
    st.markdown("<div style='margin-bottom: 1rem;'></div>", unsafe_allow_html=True)

# --------------------------------------------------------
# QUESTION CARD CONTAINER
# --------------------------------------------------------
q_type = current_q.get("question_type", "Question")
subtopic = current_q.get("subtopic", quiz_state["category"])

st.markdown(
    f"""
    <div style="background: #FFFFFF; border: 1.5px solid #E2E8F0; border-left: 6px solid {accent['color']}; border-radius: 14px; padding: 1.6rem 1.8rem; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); margin-bottom: 1.5rem;">
        <div style="display: flex; gap: 8px; margin-bottom: 0.8rem; flex-wrap: wrap; align-items: center;">
            <span style="background: {accent['bg']}; color: {accent['color']}; padding: 3px 10px; border-radius: 6px; font-size: 0.78rem; font-weight: 700; text-transform: uppercase;">
                {quiz_state['category']}
            </span>
            <span style="background: #F1F5F9; color: #475569; padding: 3px 10px; border-radius: 6px; font-size: 0.78rem; font-weight: 600;">
                Type: {q_type}
            </span>
            <span style="color: #94A3B8; font-size: 0.82rem; margin-left: auto;">
                Focus: <strong>{subtopic}</strong>
            </span>
        </div>
        <h3 style="margin: 0.5rem 0 0 0; color: #0F172A; font-size: 1.3rem; line-height: 1.55; font-weight: 600;">
            {current_q['question_text']}
        </h3>
    </div>
    """,
    unsafe_allow_html=True,
)

# Options Presentation
options_dict = {
    "A": current_q["option_a"],
    "B": current_q["option_b"],
    "C": current_q["option_c"],
    "D": current_q["option_d"],
}

is_answered = quiz_state.get("question_answered", False)
feedback = quiz_state.get("feedback")

if not is_answered:
    # -----------------------------
    # 1. Answer Selection & Submit
    # -----------------------------
    options_list = [f"{k}. {v}" for k, v in options_dict.items()]
    selected_option = st.radio(
        "Select your answer:",
        options=options_list,
        index=None,
        key=f"q_{current_q['id']}_{current_idx}",
    )

    st.markdown("<br>", unsafe_allow_html=True)
    c_sub, _ = st.columns([1.5, 3])
    with c_sub:
        if st.button("Submit Answer ➔", type="primary", use_container_width=True):
            if not selected_option:
                st.warning("⚠️ Please select an option before submitting.")
            else:
                user_choice_key = selected_option[0]  # Extracts 'A', 'B', 'C', or 'D'
                submit_current_answer(user_choice_key)
                st.rerun()

else:
    # -----------------------------
    # 2. Instant Feedback & Audio
    # -----------------------------
    user_choice = feedback["user_answer"]
    correct_choice = feedback["correct_answer"]
    is_correct = feedback["is_correct"]
    explanation = feedback["explanation"]
    feedback_message = feedback.get("message", "Good Job!" if is_correct else "Sorry, try again.")

    if is_correct:
        fb_html = f"""<div style="background: #F0FDF4; border: 2px solid #86EFAC; border-radius: 12px; padding: 1.5rem; margin-bottom: 1.2rem;">
<div style="display: flex; align-items: center; gap: 10px; margin-bottom: 0.5rem;">
<span style="font-size: 1.8rem;">✅</span>
<h3 style="margin: 0; color: #15803D; font-size: 1.45rem;">
Correct! — {feedback_message}
</h3>
</div>
<p style="margin: 0.5rem 0 0.2rem 0; color: #166534; font-size: 1.05rem;">
<strong>Your Answer:</strong> {user_choice}. {options_dict.get(user_choice, '')}
</p>
<div style="margin-top: 1rem; padding-top: 0.8rem; border-top: 1px solid #BBF7D0; color: #14532D; font-size: 0.95rem;">
<strong>Explanation:</strong> {explanation}
</div>
</div>"""
        st.markdown(fb_html, unsafe_allow_html=True)
    else:
        fb_html = f"""<div style="background: #FEF2F2; border: 2px solid #FCA5A5; border-radius: 12px; padding: 1.5rem; margin-bottom: 1.2rem;">
<div style="display: flex; align-items: center; gap: 10px; margin-bottom: 0.5rem;">
<span style="font-size: 1.8rem;">❌</span>
<h3 style="margin: 0; color: #B91C1C; font-size: 1.45rem;">
Incorrect — {feedback_message}
</h3>
</div>
<p style="margin: 0.5rem 0 0.2rem 0; color: #991B1B; font-size: 1.05rem;">
<strong>Your Answer:</strong> {user_choice}. {options_dict.get(user_choice, '')}
</p>
<p style="margin: 0.3rem 0; color: #15803D; font-size: 1.05rem; font-weight: 700;">
<strong>Correct Answer:</strong> {correct_choice}. {options_dict.get(correct_choice, '')}
</p>
<div style="margin-top: 1rem; padding-top: 0.8rem; border-top: 1px solid #FECACA; color: #7F1D1D; font-size: 0.95rem;">
<strong>Explanation:</strong> {explanation}
</div>
</div>"""
        st.markdown(fb_html, unsafe_allow_html=True)

    # Audio playback / controls with graceful fallback
    render_feedback_audio(is_correct)

    st.markdown("<br>", unsafe_allow_html=True)

    # Progression Controls
    is_last = (current_idx + 1 >= total_q)
    button_label = "Finish Assessment & View Results 🏆" if is_last else "Next Question ➡️"

    col_btn, _ = st.columns([1.8, 2.2])
    with col_btn:
        if st.button(button_label, type="primary", use_container_width=True):
            if is_last:
                complete_current_attempt()
                st.switch_page("pages/05_Result.py")
            else:
                move_to_next_question()
                st.rerun()
