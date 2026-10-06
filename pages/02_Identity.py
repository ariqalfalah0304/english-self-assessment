"""
User Identity Page (Phase 3).
Collects and validates user name, email, institution, and program.
Stores identity in SQLite and initializes active session before navigating to Test Selection.
"""

import streamlit as st
from config.settings import APP_NAME
from services.user_service import (
    process_user_identity,
    login_user_by_email,
    set_active_user_session,
    get_active_user_session,
    clear_active_user_session,
)
from components.navigation import inject_custom_navigation_css
from components.ui_styles import inject_global_ui_styles

st.set_page_config(
    page_title=f"Identity & Login — {APP_NAME}",
    page_icon="👤",
    layout="centered",
    initial_sidebar_state="collapsed",
)

inject_custom_navigation_css()
inject_global_ui_styles()

st.markdown(
    """
    <div style="text-align: center; margin-bottom: 1.8rem;">
        <h1 style="font-size: 2.2rem; margin-bottom: 0.2rem; color: #1E3A8A; font-weight: 800;">👤 Portal Peserta Ujian</h1>
        <p style="color: #6B7280; font-size: 1.05rem;">Masuk dengan akun terdaftar atau registrasi peserta baru untuk memulai asesmen.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Check if user is already logged in for this session
existing_session = get_active_user_session()
if existing_session:
    st.markdown(
        f"""
        <div style="background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%); border: 1.5px solid #93C5FD; border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem;">
            <div style="font-size: 0.82rem; font-weight: 700; color: #1D4ED8; text-transform: uppercase;">Sesi Aktif</div>
            <h3 style="margin: 0.3rem 0; color: #1E3A8A;">Halo, {existing_session['name']}! </h3>
            <p style="margin: 0; color: #4B5563; font-size: 0.92rem;">
                Anda saat ini telah masuk dengan email: <strong>{existing_session['email']}</strong>
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("➡️ Lanjutkan ke Pilihan Ujian", use_container_width=True, type="primary"):
            st.switch_page("pages/03_Test_Selection.py")
    with col_b:
        if st.button("🔄 Ganti Akun / Logout", use_container_width=True):
            clear_active_user_session()
            st.rerun()

    st.stop()

# Two Tabs: Login and Register
tab_login, tab_register = st.tabs(["🔑 Masuk (Akun Terdaftar)", "📝 Daftar Akun Baru"])

with tab_login:
    st.markdown(
        """
        <div style="background: #F0FDF4; border: 1px solid #BBF7D0; border-radius: 10px; padding: 12px 16px; margin-bottom: 1.2rem; color: #166534; font-size: 0.92rem;">
            💡 <strong>Sudah pernah mendaftar?</strong><br>
            Cukup masukkan alamat email Anda untuk melanjutkan progres ujian dan mengakses skill yang telah terbuka.
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.form("login_participant_form", clear_on_submit=False):
        login_email = st.text_input(
            "Alamat Email Terdaftar *",
            placeholder="contoh: yuni@gmail.com",
            help="Masukkan email yang Anda gunakan saat pertama kali mendaftar.",
        )
        st.markdown("<br>", unsafe_allow_html=True)
        login_submitted = st.form_submit_button(
            "🔑 Masuk & Lanjutkan Ujian ➔",
            use_container_width=True,
            type="primary",
        )

    if login_submitted:
        if not login_email:
            st.error("⚠️ Silakan masukkan alamat email Anda.")
        else:
            success, user, msg = login_user_by_email(login_email)
            if not success or user is None:
                st.error(f"❌ {msg}")
            else:
                set_active_user_session(user)
                st.toast(f"Selamat datang kembali, {user.name}!", icon="🎉")
                st.switch_page("pages/03_Test_Selection.py")

with tab_register:
    st.markdown(
        """
        <div style="background: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 10px; padding: 12px 16px; margin-bottom: 1.2rem; color: #1E40AF; font-size: 0.92rem;">
            📝 <strong>Peserta Baru?</strong><br>
            Lengkapi data diri Anda di bawah ini untuk memulai asesmen mandiri. Akun dan progres pengerjaan akan otomatis tersimpan.
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.form("register_participant_form", clear_on_submit=False):
        full_name = st.text_input(
            "Nama Lengkap *",
            placeholder="contoh: Yuni Rahmawati",
            help="Nama asli peserta asesmen.",
        )
        email = st.text_input(
            "Alamat Email *",
            placeholder="contoh: yuni@gmail.com",
            help="Digunakan untuk menyimpan riwayat dan progres kelulusan skill Anda.",
        )
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("##### Informasi Tambahan (Opsional)")
        institution = st.text_input(
            "Institusi / Sekolah / Kampus",
            placeholder="contoh: Universitas Negeri Jakarta",
        )
        program = st.text_input(
            "Jurusan / Bidang Studi / Pekerjaan",
            placeholder="contoh: Pendidikan Bahasa Inggris",
        )
        st.markdown("<br>", unsafe_allow_html=True)
        reg_submitted = st.form_submit_button(
            "🚀 Daftar & Mulai Ujian ➔",
            use_container_width=True,
            type="primary",
        )

    if reg_submitted:
        success, user, errors = process_user_identity(
            name=full_name,
            email=email,
            institution=institution,
            program=program,
        )
        if not success or user is None:
            st.error("⚠️ Silakan periksa isian data Anda:")
            for field, err in errors.items():
                st.markdown(f"- **{field.capitalize()}**: {err}")
        else:
            set_active_user_session(user)
            st.toast(f"Selamat datang, {user.name}!", icon="🎉")
            st.switch_page("pages/03_Test_Selection.py")

