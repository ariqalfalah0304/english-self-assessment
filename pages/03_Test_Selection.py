"""
Test Category and Difficulty Selection Page (Phase 4).
Allows authenticated users to select any Category (Grammar, Reading, Listening)
and Difficulty (Easy, Medium, Hard) without a forced sequence.
Prepares quiz session state and navigates to Quiz Ready view.
"""

import streamlit as st
from config.settings import APP_NAME
from services.user_service import get_active_user_session, is_user_authenticated, clear_active_user_session
from services.quiz_engine import prepare_quiz_session, prepare_skill_quiz_session, prepare_final_exam_session, reset_quiz_session
from database.db import get_connection
from database import queries
from components.navigation import inject_custom_navigation_css
from components.ui_styles import inject_global_ui_styles

st.set_page_config(
    page_title=f"Choose Assessment — {APP_NAME}",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_custom_navigation_css()
inject_global_ui_styles()

# 1. ENFORCE IDENTITY GUARD
if not is_user_authenticated():
    st.error("🔒 Access Denied: You must complete your identity before selecting a test.")
    st.markdown(
        """
        Please enter your name and email on the identity page to start your self-assessment.
        """
    )
    if st.button("👉 Go to Identity Form", type="primary", use_container_width=True):
        st.switch_page("pages/02_Identity.py")
    st.stop()

active_user = get_active_user_session()

# Top Header Card
meta_parts = []
if active_user.get("institution"):
    meta_parts.append(str(active_user["institution"]))
if active_user.get("program"):
    meta_parts.append(str(active_user["program"]))
meta_text = f" • {' • '.join(meta_parts)}" if meta_parts else ""

st.markdown(
    f"""<div style="background: linear-gradient(135deg, #EFF6FF 0%, #F5F3FF 100%); padding: 1.5rem 2rem; border-radius: 16px; border: 1px solid #DBEAFE; margin-bottom: 2rem;">
<div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
<div>
<span style="background: #3B82F6; color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;">Active Participant</span>
<h2 style="margin: 0.5rem 0 0.2rem 0; font-size: 1.75rem; color: #1E3A8A; font-weight: 800;">
Welcome, {active_user['name']}!
</h2>
<p style="margin: 0; color: #4B5563; font-size: 0.95rem;">
Email: <strong>{active_user['email']}</strong>{meta_text}
</p>
</div>
</div>
</div>""",
    unsafe_allow_html=True,
)

c_nav_left, c_nav_right = st.columns([3.5, 1.5])
with c_nav_right:
    if st.button("View My Assessment Summary", use_container_width=True):
        st.switch_page("pages/06_History.py")

# Category selection state tracker
if "chosen_category" not in st.session_state:
    st.session_state.chosen_category = None

CATEGORY_CARDS = [
    {
        "name": "Grammar",
        "icon": "📖",
        "tagline": "Structure & Rules",
        "description": "Measures understanding of English grammar structures, tenses, agreements, and syntax patterns.",
        "color": "#4F46E5",
        "bg": "#EEF2FF",
        "border": "#C7D2FE",
    },
    {
        "name": "Reading",
        "icon": "📚",
        "tagline": "Comprehension & Analysis",
        "description": "Measures passage comprehension, identifying main ideas, vocabulary in context, and analytical inference.",
        "color": "#059669",
        "bg": "#ECFDF5",
        "border": "#A7F3D0",
    },
    {
        "name": "Listening",
        "icon": "🎧",
        "tagline": "Audio Understanding",
        "description": "Measures comprehension from spoken dialogues, short talks, conversations, and audio clues.",
        "color": "#D97706",
        "bg": "#FFFBEB",
        "border": "#FDE68A",
    },
]



# Fetch DB Category IDs mapping
category_id_map = {}
try:
    with get_connection() as conn:
        db_cats = queries.get_all_categories(conn)
        category_id_map = {c.name.lower(): c.id for c in db_cats}
except Exception:
    pass

# STEP 1: CATEGORY SELECTION (Free to choose any category first)
if not st.session_state.chosen_category:
    st.markdown("### Step 1: Select Your Test Category")
    st.write("You are completely free to start with any category. There is no forced sequence.")

    cols = st.columns(3)
    for idx, card in enumerate(CATEGORY_CARDS):
        with cols[idx]:
            st.markdown(
                f"""<div style="background: #FFFFFF; border: 1.5px solid {card['border']}; border-top: 6px solid {card['color']}; border-radius: 16px; padding: 1.6rem; text-align: center; min-height: 260px; display: flex; flex-direction: column; justify-content: space-between; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);">
<div>
<div style="display: inline-block; background: {card['bg']}; width: 60px; height: 60px; line-height: 60px; border-radius: 50%; font-size: 2.2rem; margin-bottom: 0.8rem;">{card['icon']}</div>
<h3 style="margin: 0 0 0.2rem 0; color: #0F172A; font-size: 1.45rem; font-weight: 700;">{card['name']}</h3>
<p style="margin: 0 0 0.8rem 0; font-size: 0.8rem; font-weight: 700; color: {card['color']}; text-transform: uppercase; letter-spacing: 0.5px;">{card['tagline']}</p>
<p style="color: #475569; font-size: 0.88rem; line-height: 1.5; margin: 0;">{card['description']}</p>
</div>
</div>""",
                unsafe_allow_html=True,
            )
            st.markdown("<div style='margin-top: 0.6rem;'></div>", unsafe_allow_html=True)
            if st.button(f"Choose {card['name']} ➔", key=f"btn_cat_{card['name']}", use_container_width=True, type="primary"):
                st.session_state.chosen_category = card['name']
                st.rerun()

else:
    # STEP 2: SKILL PROGRESSION FOR CHOSEN CATEGORY
    chosen_cat_name = st.session_state.chosen_category
    matched_cat = next((c for c in CATEGORY_CARDS if c['name'] == chosen_cat_name), CATEGORY_CARDS[0])
    cat_id = category_id_map.get(chosen_cat_name.lower())

    col_title, col_change = st.columns([3, 1])
    with col_title:
        st.markdown(f"### Step 2: Pilih Skill / Materi untuk **{chosen_cat_name}**")
        st.write("Selesaikan skill secara bertahap. Capai nilai kelulusan minimal **70%** untuk membuka (*unlock*) skill berikutnya!")
    with col_change:
        if st.button("Ganti Kategori", use_container_width=True):
            st.session_state.chosen_category = None
            st.rerun()

    with get_connection() as conn:
        user_skills = queries.get_user_skills_status(conn, active_user["id"], cat_id)

    if not user_skills:
        st.info(f"Belum ada paket skill yang tersedia untuk kategori {chosen_cat_name}.")
    else:
        # Build Dropdown options
        skill_options = []
        for s in user_skills:
            s_num = s["skill_number"]
            s_name = s["skill_name"]
            if s["is_passed"]:
                tag = f"✅ Lolos ({s['highest_score']:.0f}%)"
            elif s["is_unlocked"]:
                tag = "🟢 Terbuka"
            else:
                tag = "🔒 Terkunci"
            skill_options.append(f"Skill {s_num}: {s_name} [{tag}]")

        # Pick default index: first unlocked and not yet passed skill, or first unlocked, or 0
        default_idx = 0
        for i, s in enumerate(user_skills):
            if s["is_unlocked"] and not s["is_passed"]:
                default_idx = i
                break
            elif s["is_unlocked"]:
                default_idx = i

        st.markdown("<div style='margin-bottom: 0.5rem;'></div>", unsafe_allow_html=True)
        col_drop, _ = st.columns([3.5, 0.5])
        with col_drop:
            selected_skill_idx = st.selectbox(
                "Pilih Materi / Skill dari Menu Dropdown:",
                options=range(len(user_skills)),
                format_func=lambda i: skill_options[i],
                index=default_idx,
                key="skill_dropdown_selector",
                help="Pilih skill untuk melihat rincian materi. Skill berikutnya akan terbuka otomatis setelah Anda lolos skill sebelumnya.",
            )

        selected_s = user_skills[selected_skill_idx]
        s_num = selected_s["skill_number"]
        s_name = selected_s["skill_name"]
        is_unlocked = selected_s["is_unlocked"]
        is_passed = selected_s["is_passed"]
        high_score = selected_s["highest_score"]
        attempts = selected_s["attempts_count"]
        active_q = selected_s["active_question_count"]
        passing_score = selected_s.get("passing_score", 70.0)

        # Highlight Card for Selected Skill
        if is_passed:
            card_bg = "#F0FDF4"
            card_border = "#86EFAC"
            icon_badge = "✅"
            status_label = f"Lolos Passing Grade (Skor Tertinggi: {high_score:.1f}%)"
            badge_bg = "#DCFCE7"
            badge_color = "#15803D"
        elif is_unlocked:
            card_bg = "#FFFFFF"
            card_border = "#93C5FD"
            icon_badge = "🟢"
            status_label = "Terbuka — Siap Dikerjakan" if attempts == 0 else f"Belum Lolos (Skor: {high_score:.1f}%)"
            badge_bg = "#EFF6FF"
            badge_color = "#1D4ED8"
        else:
            card_bg = "#F8FAFC"
            card_border = "#E2E8F0"
            icon_badge = "🔒"
            status_label = f"Terkunci (Syarat: Loloskan Skill {s_num - 1} min. {passing_score:.0f}%)"
            badge_bg = "#F1F5F9"
            badge_color = "#64748B"

        st.markdown(
            f"""<div style="background: {card_bg}; border: 2px solid {card_border}; border-radius: 14px; padding: 1.5rem 1.8rem; margin: 1rem 0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
    <span style="font-size: 0.85rem; font-weight: 800; color: #4338CA; background: #EEF2FF; padding: 4px 12px; border-radius: 8px; letter-spacing: 0.5px;">
        SKILL {s_num}
    </span>
    <span style="background: {badge_bg}; color: {badge_color}; font-size: 0.85rem; font-weight: 700; padding: 4px 12px; border-radius: 8px;">
        {icon_badge} {status_label}
    </span>
</div>
<h3 style="margin: 0.4rem 0 0.6rem 0; color: {'#0F172A' if is_unlocked else '#94A3B8'}; font-size: 1.35rem; font-weight: 800;">
    {s_name}
</h3>
<div style="display: flex; gap: 1.5rem; flex-wrap: wrap; font-size: 0.92rem; color: #475569; margin-top: 0.5rem;">
    <span>📚 Tersedia: <strong>{active_q} Soal Aktif</strong></span>
    <span>🎯 Passing Grade: <strong>{passing_score:.0f}%</strong></span>
    <span>🔄 Telah Dikerjakan: <strong>{attempts} kali</strong></span>
    <span>🏆 Skor Terbaik: <strong>{high_score:.1f}%</strong></span>
</div>
</div>""",
            unsafe_allow_html=True,
        )

        # Action Button Area for Selected Skill
        if is_unlocked:
            c_btn1, c_btn2 = st.columns([2.5, 2.5])
            with c_btn1:
                btn_action_text = f"Mulai Kerjakan Skill {s_num} ➔" if attempts == 0 else f"Ulangi Skill {s_num} ➔"
                if st.button(btn_action_text, key=f"main_btn_skill_{s_num}", use_container_width=True, type="primary"):
                    prepare_skill_quiz_session(
                        category=chosen_cat_name,
                        skill_number=s_num,
                        skill_name=s_name,
                        category_id=cat_id,
                    )
                    st.switch_page("pages/04_Quiz.py")
        else:
            st.warning(
                f"🔒 **Skill {s_num} Masih Terkunci!** "
                f"Materi ini tidak dapat dikerjakan sekarang. Anda harus menyelesaikan **Skill {s_num - 1}** dengan nilai minimal **{passing_score:.0f}%** untuk membuka materi ini.",
                icon="⚠️"
            )
            st.button(
                f"🔒 Skill {s_num} Terkunci (Selesaikan Skill {s_num - 1} Terlebih Dahulu)",
                key=f"locked_btn_skill_{s_num}",
                use_container_width=True,
                disabled=True
            )

        # Roadmap Overview of All Skills
        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander(f"🗺️ Lihat Ringkasan Seluruh Skill di Kategori {chosen_cat_name}", expanded=True):
            for s in user_skills:
                sn = s["skill_number"]
                unlocked = s["is_unlocked"]
                passed = s["is_passed"]
                h_score = s["highest_score"]
                q_count = s["active_question_count"]
                
                if passed:
                    st_icon = "✅"
                    st_text = f"Lolos ({h_score:.1f}%)"
                    border_c = "#86EFAC"
                    bg_c = "#F0FDF4"
                elif unlocked:
                    st_icon = "🟢"
                    st_text = "Terbuka"
                    border_c = "#93C5FD"
                    bg_c = "#EFF6FF"
                else:
                    st_icon = "🔒"
                    st_text = f"Terkunci (Perlu Skill {sn-1})"
                    border_c = "#E2E8F0"
                    bg_c = "#F8FAFC"

                st.markdown(
                    f"""<div style="background: {bg_c}; border: 1px solid {border_c}; border-radius: 8px; padding: 10px 14px; margin-bottom: 6px; display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <strong>Skill {sn}:</strong> {s['skill_name']} 
                            <span style="color: #64748B; font-size: 0.85rem; margin-left: 8px;">({q_count} soal)</span>
                        </div>
                        <div>
                            <span style="font-weight: 700; font-size: 0.85rem;">{st_icon} {st_text}</span>
                        </div>
                    </div>""",
                    unsafe_allow_html=True,
                )

        # FINAL MASTERY EXAM (UJIAN GABUNGAN) CARD
        passed_count = sum(1 for s in user_skills if s["is_passed"])
        total_skills_count = len(user_skills)
        all_skills_passed = (passed_count == total_skills_count and total_skills_count > 0)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### Ujian Gabungan (Final Mastery Assessment)")

        if all_skills_passed:
            st.markdown(
                f"""<div style="background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%); border-radius: 16px; padding: 1.6rem 2rem; color: #FFFFFF; margin-bottom: 1rem; box-shadow: 0 10px 25px -5px rgba(37, 99, 235, 0.25);">
<div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 0.8rem;">
    <span style="background: rgba(255, 255, 255, 0.25); border: 1px solid rgba(255, 255, 255, 0.4); padding: 4px 14px; border-radius: 9999px; font-size: 0.82rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.8px;">
        🎉 UNLOCKED & READY!
    </span>
    <span style="font-size: 0.9rem; opacity: 0.95;">
        {total_skills_count} Skill Terdeteksi • Proporsional & Acak
    </span>
</div>
<h3 style="margin: 0 0 0.4rem 0; font-size: 1.6rem; font-weight: 800; color: #FFFFFF;">
     Ujian Gabungan — {chosen_cat_name}
</h3>
<p style="margin: 0; opacity: 0.95; font-size: 0.98rem; line-height: 1.55;">
Selamat! Anda telah meloloskan seluruh <strong>{total_skills_count} Skill</strong> di kategori {chosen_cat_name}. Ujian Gabungan ini akan mengambil sampel soal secara proporsional dari setiap skill ({round(100/total_skills_count, 1)}% per skill) dan mengacaknya secara keseluruhan.
</p>
</div>""",
                unsafe_allow_html=True,
            )
            c_final1, _ = st.columns([3, 2])
            with c_final1:
                if st.button(f"Mulai Ujian Gabungan {chosen_cat_name} (50 Soal Acak)", type="primary", use_container_width=True, key="btn_start_final_exam"):
                    prepare_final_exam_session(chosen_cat_name, cat_id)
                    st.switch_page("pages/04_Quiz.py")
        else:
            st.markdown(
                f"""<div style="background: #F8FAFC; border: 1.5px solid #CBD5E1; border-radius: 16px; padding: 1.5rem 1.8rem; margin-bottom: 1rem;">
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.6rem;">
    <span style="background: #F1F5F9; color: #475569; padding: 4px 12px; border-radius: 8px; font-size: 0.85rem; font-weight: 700;">
        🔒 TERKUNCI (Progress: {passed_count}/{total_skills_count} Skill Lolos)
    </span>
</div>
<h4 style="margin: 0 0 0.4rem 0; color: #334155; font-size: 1.2rem; font-weight: 700;">
    Ujian Gabungan — {chosen_cat_name}
</h4>
<p style="margin: 0; color: #64748B; font-size: 0.92rem; line-height: 1.5;">
Selesaikan dan loloskan seluruh {total_skills_count} Skill di kategori {chosen_cat_name} dengan nilai minimal 70% untuk membuka Ujian Gabungan 50 soal acak.
</p>
</div>""",
                unsafe_allow_html=True,
            )

st.markdown("<br><hr>", unsafe_allow_html=True)
c_back, c_empty, c_logout = st.columns([1.5, 3, 1.5])
with c_back:
    if st.button("Back to Identity", use_container_width=True):
        st.switch_page("pages/02_Identity.py")
with c_logout:
    if st.button("Logout Participant", use_container_width=True):
        clear_active_user_session()
        reset_quiz_session()
        st.switch_page("pages/02_Identity.py")
