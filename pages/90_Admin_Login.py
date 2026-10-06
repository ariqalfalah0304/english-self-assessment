"""
Admin Login and Authentication Portal (Phase 9).
Provides secure administrator login using bcrypt password verification,
session-based authentication, logout capabilities, role-based protection,
and safe initial admin account creation if no accounts exist yet.
"""

import streamlit as st
from config.settings import APP_NAME
from services.admin_service import (
    authenticate_admin,
    login_admin_session,
    logout_admin_session,
    is_admin_authenticated,
    get_active_admin_session,
    has_any_admin,
    init_first_admin,
    update_admin_account_credentials,
)
from components.navigation import inject_custom_navigation_css, render_admin_header
from components.ui_styles import inject_global_ui_styles

st.set_page_config(
    page_title=f"Admin Portal — {APP_NAME}",
    page_icon="🔐",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Apply navigation styling to separate public and admin interfaces
inject_custom_navigation_css()
inject_global_ui_styles()

# ========================================================
# SCENARIO 1: CURRENTLY AUTHENTICATED ADMINISTRATOR
# ========================================================
if is_admin_authenticated():
    render_admin_header(
        title="Admin Portal",
        subtitle="Secure Administrative Management Center",
    )

    admin_session = get_active_admin_session()
    username = admin_session["username"]
    role = admin_session["role"].upper()
    login_time = admin_session.get("login_time", "Active Session")

    st.markdown(
        f"""
<div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 2rem; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); margin-bottom: 1.5rem;">
    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 1.2rem;">
        <span style="font-size: 2.2rem;">✅</span>
        <div>
            <h3 style="margin: 0; color: #0F172A; font-size: 1.35rem; font-weight: 700;">Active Administrator Session</h3>
            <p style="margin: 2px 0 0 0; color: #64748B; font-size: 0.88rem;">Authenticated via secure bcrypt session token</p>
        </div>
    </div>
    <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 1.2rem 1.4rem; margin-bottom: 1.2rem;">
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; font-size: 0.95rem;">
            <div><strong style="color: #475569;">Username:</strong> <span style="color: #0F172A; font-weight: 600;">{username}</span></div>
            <div><strong style="color: #475569;">Role:</strong> <span style="background: #DBEAFE; color: #1E40AF; padding: 3px 10px; border-radius: 6px; font-weight: 700; font-size: 0.8rem;">{role}</span></div>
            <div><strong style="color: #475569;">Status:</strong> <span style="color: #16A34A; font-weight: 700;">● Online</span></div>
            <div><strong style="color: #475569;">Session Started:</strong> <span style="color: #334155;">{login_time[:19] if len(login_time) >= 19 else login_time}</span></div>
        </div>
    </div>
    <div style="background: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 8px; padding: 12px 16px; color: #1E40AF; font-size: 0.9rem; line-height: 1.5;">
        ℹ️ <strong>Admin Authentication Verified:</strong> You are currently logged in with full administrative privileges. Use the dashboard button below to manage questions, view student results, or import test banks.
    </div>
</div>
""",
        unsafe_allow_html=True,
    )

    if st.session_state.get("cred_update_success_msg"):
        st.success(st.session_state.pop("cred_update_success_msg"))
        st.toast("🎉 Username dan Password baru berhasil disimpan!", icon="✅")

    with st.expander("🔐 Ubah Username & Password Administrator", expanded=False):
        st.write("Perbarui kredensial akun administrator Anda:")
        with st.form("form_change_admin_credentials_logged_in"):
            change_new_user = st.text_input(
                "Username Baru *",
                value=username,
            )
            change_cur_pass = st.text_input(
                "Password Saat Ini *",
                type="password",
                help="Masukkan password Anda saat ini untuk mengonfirmasi perubahan.",
            )
            change_new_pass = st.text_input(
                "Password Baru (Kosongkan jika tidak ingin diubah)",
                type="password",
            )
            change_confirm_pass = st.text_input(
                "Konfirmasi Password Baru",
                type="password",
            )
            submit_change_session = st.form_submit_button("💾 Simpan Perubahan Kredensial", type="primary", use_container_width=True)

            if submit_change_session:
                up_ok, up_msg = update_admin_account_credentials(
                    admin_id=admin_session["id"],
                    current_password=change_cur_pass,
                    new_username=change_new_user,
                    new_password=change_new_pass if change_new_pass.strip() else None,
                    confirm_password=change_confirm_pass if change_confirm_pass.strip() else None,
                )
                if up_ok:
                    st.session_state["cred_update_success_msg"] = f"🎉 Kredensial akun ({up_msg}) berhasil disimpan!"
                    st.rerun()
                else:
                    st.error(f"❌ {up_msg}")

    st.markdown("<br>", unsafe_allow_html=True)

    c_dash, c_logout, c_home = st.columns([1.5, 1.2, 1.2])
    with c_dash:
        if st.button("📊 Go to Admin Dashboard", type="primary", use_container_width=True):
            st.rerun()

    with c_logout:
        if st.button("🚪 Logout Administrator", use_container_width=True):
            logout_admin_session()
            st.toast("You have been logged out successfully.", icon="👋")
            st.rerun()

    with c_home:
        if st.button("🌐 Public Assessment Site", use_container_width=True):
            st.session_state["admin_portal_mode"] = False
            st.rerun()

    st.stop()


# ========================================================
# SCENARIO 2: FIRST-TIME SETUP (NO ADMIN ACCOUNTS EXIST)
# ========================================================
if not has_any_admin():
    st.markdown(
        """
        <div style="text-align: center; margin-bottom: 1.5rem;">
            <div style="font-size: 3rem; margin-bottom: 0.5rem;">🛡️</div>
            <h2 style="margin: 0; color: #0F172A; font-size: 1.8rem; font-weight: 800;">First-Time Admin Setup</h2>
            <p style="color: #64748B; margin-top: 0.4rem; font-size: 0.95rem;">
                No administrator accounts currently exist in the database.<br>
                Define your primary Superadmin credentials to initialize administration.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("first_time_admin_form"):
        st.markdown("##### 🔑 Superadmin Account Details")
        new_username = st.text_input(
            "Username",
            placeholder="e.g. admin or administrator",
            help="At least 3 characters. Alphanumeric, dot, or underscore.",
        )
        new_password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter secure password (min 8 characters)",
            help="Must include both letters and at least one number or symbol.",
        )
        confirm_password = st.text_input(
            "Confirm Password",
            type="password",
            placeholder="Re-enter password to verify",
        )

        st.markdown("<br>", unsafe_allow_html=True)
        submit_init = st.form_submit_button("🛡️ Initialize First Superadmin", type="primary", use_container_width=True)

        if submit_init:
            if not new_username or not new_password:
                st.warning("⚠️ Please fill in all required fields.")
            elif new_password != confirm_password:
                st.error("❌ Passwords do not match. Please re-enter identical passwords.")
            else:
                success, admin, msg = init_first_admin(new_username, new_password)
                if success and admin:
                    login_admin_session(admin)
                    st.session_state["admin_portal_mode"] = False
                    st.success(f"🎉 Superadmin account '{admin.username}' created successfully!")
                    st.rerun()
                else:
                    st.error(f"❌ Initialization failed: {msg}")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("⬅️ Return to Public Self-Assessment", use_container_width=True, key="ret_first_time"):
        st.session_state["admin_portal_mode"] = False
        st.rerun()
    st.stop()


# ========================================================
# SCENARIO 3: STANDARD ADMIN LOGIN FORM
# ========================================================
st.markdown(
    """
    <div style="text-align: center; margin-bottom: 2rem;">
        <div style="display: inline-block; background: #EEF2FF; border: 2px solid #C7D2FE; border-radius: 50%; width: 72px; height: 72px; line-height: 72px; font-size: 2rem; margin-bottom: 0.8rem;">
            🔐
        </div>
        <h2 style="margin: 0; color: #0F172A; font-size: 1.85rem; font-weight: 800;">Administrator Portal</h2>
        <p style="color: #64748B; margin-top: 0.4rem; font-size: 0.95rem;">
            Sign in with verified administrator credentials to access management controls.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.form("admin_login_form"):
    username_input = st.text_input(
        "Username or Email:",
        placeholder="Enter your administrator username",
        autocomplete="username",
    )
    password_input = st.text_input(
        "Password:",
        type="password",
        placeholder="Enter your administrator password",
        autocomplete="current-password",
    )

    st.markdown("<br>", unsafe_allow_html=True)
    login_btn = st.form_submit_button("🔓 Log In to Admin Portal", type="primary", use_container_width=True)

    if login_btn:
        if not username_input or not password_input:
            st.warning("⚠️ Please provide both your username and password.")
        else:
            success, admin, msg = authenticate_admin(username_input, password_input)
            if success and admin:
                login_admin_session(admin)
                st.session_state["admin_portal_mode"] = False
                st.success(f"✅ Authentication successful! Welcome, {admin.username}.")
                st.rerun()
            else:
                st.error("❌ Invalid username or password. Please verify your credentials and try again.")

st.markdown("<br><hr>", unsafe_allow_html=True)
c_back, _ = st.columns([2, 1])
with c_back:
    if st.button("⬅️ Return to Public Self-Assessment", use_container_width=True, key="ret_public_login"):
        st.switch_page("pages/01_Home.py")
