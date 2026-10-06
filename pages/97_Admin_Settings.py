"""
Admin Account & Security Settings Page.
Allows authenticated administrators to update their username and password.
"""

import streamlit as st
from config.settings import APP_NAME
from services.admin_service import (
    require_admin_auth,
    get_active_admin_session,
    update_admin_account_credentials,
)
from components.navigation import inject_custom_navigation_css, render_admin_header
from components.ui_styles import inject_global_ui_styles

st.set_page_config(
    page_title=f"Account Settings — {APP_NAME}",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply route protection & global UI styles
inject_custom_navigation_css()
inject_global_ui_styles()
require_admin_auth()

render_admin_header(
    title="Pengaturan Akun & Keamanan",
    subtitle="Kelola Kredensial Administrator, Ubah Username, dan Perbarui Password",
)

admin_session = get_active_admin_session()
if not admin_session:
    st.error("Sesi administrator tidak ditemukan. Silakan login kembali.")
    st.stop()

current_admin_id = admin_session["id"]
current_username = admin_session.get("username", "admin")
current_role = admin_session.get("role", "admin").upper()

# -------------------------------------------------------------
# 1. PROFILE OVERVIEW CARD
# -------------------------------------------------------------
st.markdown("### 👤 Informasi Akun Aktif")
col_info1, col_info2, col_info3 = st.columns(3)

with col_info1:
    st.info(f"**Username Saat Ini:**\n### `{current_username}`")

with col_info2:
    st.success(f"**Peran (Role):**\n### `{current_role}`")

with col_info3:
    st.warning("**Status Keamanan:**\n### `Dilindungi Bcrypt`")

st.markdown("<br><hr>", unsafe_allow_html=True)

# -------------------------------------------------------------
# 2. CHANGE CREDENTIALS FORM
# -------------------------------------------------------------
st.markdown("### 🔐 Ubah Username & Password")
st.markdown("Gunakan formulir di bawah ini untuk memperbarui username atau mengganti password akun Anda.")

with st.container(border=True):
    with st.form("form_admin_settings_credentials"):
        col_left, col_right = st.columns(2)

        with col_left:
            st.markdown("##### 1. Data Akun")
            new_username = st.text_input(
                "Username Baru *",
                value=current_username,
                help="Minimal 3 karakter alfanumerik. Boleh menggunakan titik, garis bawah, strip.",
            )
            current_pass = st.text_input(
                "Password Saat Ini *",
                type="password",
                help="Wajib memasukkan password saat ini untuk verifikasi keamanan sebelum perubahan disimpan.",
            )

        with col_right:
            st.markdown("##### 2. Password Baru (Opsional)")
            new_pass = st.text_input(
                "Password Baru",
                type="password",
                help="Kosongkan kolom ini jika Anda HANYA ingin mengganti username.",
            )
            confirm_new_pass = st.text_input(
                "Konfirmasi Password Baru",
                type="password",
                help="Ketik ulang password baru Anda untuk memastikan tidak ada salah ketik.",
            )

        st.markdown("<br>", unsafe_allow_html=True)
        btn_submit = st.form_submit_button("💾 Simpan Perubahan Kredensial", type="primary", use_container_width=True)

        if btn_submit:
            if not current_pass.strip():
                st.error("❌ Password saat ini wajib diisi untuk mengonfirmasi perubahan kredensial.")
            else:
                ok, message = update_admin_account_credentials(
                    admin_id=current_admin_id,
                    current_password=current_pass,
                    new_username=new_username,
                    new_password=new_pass if new_pass.strip() else None,
                    confirm_password=confirm_new_pass if confirm_new_pass.strip() else None,
                )

                if ok:
                    st.success(f"🎉 Berhasil: {message}")
                    st.toast("Kredensial berhasil diperbarui!", icon="✅")
                    st.rerun()
                else:
                    st.error(f"❌ {message}")
