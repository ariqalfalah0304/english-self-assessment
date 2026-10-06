"""
English Self-Assessment Platform - Main Entry Point & Navigation Router.
Provides dynamic, strict separation between User Flow and Administrator Flow using st.navigation.
"""

import sys
import importlib

# Ensure fresh navigation component and exporter logic are loaded in long-running processes
if "components.navigation" in sys.modules:
    importlib.reload(sys.modules["components.navigation"])
if "utils.excel_parser" in sys.modules:
    importlib.reload(sys.modules["utils.excel_parser"])
if "services.scoring_service" in sys.modules:
    importlib.reload(sys.modules["services.scoring_service"])
if "services.question_service" in sys.modules:
    importlib.reload(sys.modules["services.question_service"])

import streamlit as st
# Always use the ORIGINAL function from its source module. The `st` module is shared
# across reruns in the server process, so `st.set_page_config` may already be patched.
from streamlit.commands.page_config import set_page_config as _real_set_page_config

# Configure page settings once at application root
_real_set_page_config(
    page_title="English Self-Assessment",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)


def _safe_set_page_config(*args, **kwargs):
    """Child pages may call st.set_page_config; always force the wide layout."""
    kwargs["layout"] = "wide"
    kwargs.pop("initial_sidebar_state", None)
    try:
        _real_set_page_config(*args, **kwargs)
    except Exception:
        pass


st.set_page_config = _safe_set_page_config

from config.settings import ensure_directories
from database.db import init_db
from services.admin_service import is_admin_authenticated, get_active_admin_session, logout_admin_session
from components.ui_styles import inject_global_ui_styles

ensure_directories()
init_db()
inject_global_ui_styles()

# -------------------------------------------------------------
# 1. DEFINE ROUTE SPECIFICATIONS
# -------------------------------------------------------------
# User Visible Pages
p_home = st.Page("pages/01_Home.py", title="Home", icon="🏠", default=True)
p_identity = st.Page("pages/02_Identity.py", title="Identity", icon="👤")
p_test_selection = st.Page("pages/03_Test_Selection.py", title="Test Selection", icon="📝")
p_quiz = st.Page("pages/04_Quiz.py", title="Quiz", icon="⏱️")
p_result = st.Page("pages/05_Result.py", title="Result", icon="📊")
p_history = st.Page("pages/06_History.py", title="History", icon="📜")

# Admin Login (Hidden from public sidebar, but switchable via button/URL)
p_login = st.Page("pages/90_Admin_Login.py", title="Admin Login", icon="🔐", visibility="hidden")

# Admin Visible Pages
p_dashboard = st.Page("pages/91_Admin_Dashboard.py", title="Dashboard", icon="🛡️", default=True)
p_users = st.Page("pages/92_Admin_Users.py", title="Users", icon="👥")
p_qbank = st.Page("pages/93_Admin_Question_Bank.py", title="Question Bank", icon="📚")
p_import = st.Page("pages/94_Admin_Import.py", title="Import Questions", icon="📥")
p_analytics = st.Page("pages/95_Admin_Analytics.py", title="Analytics", icon="📈")
p_results = st.Page("pages/96_Admin_Results.py", title="Results", icon="📋")
p_settings = st.Page("pages/97_Admin_Settings.py", title="Settings", icon="⚙️")

user_nav = [p_home, p_identity, p_test_selection, p_quiz, p_result, p_history, p_login]
admin_nav = [p_dashboard, p_users, p_qbank, p_import, p_analytics, p_results, p_settings]

# -------------------------------------------------------------
# 2. DYNAMIC NAVIGATION SELECTION
# -------------------------------------------------------------
if is_admin_authenticated():
    # ADMIN MODE: built-in nav hidden so the admin badge can sit above the menu
    pg = st.navigation(admin_nav, position="hidden")

    admin_info = get_active_admin_session()
    username = admin_info.get("username", "Admin") if admin_info else "Admin"
    role = admin_info.get("role", "admin").upper() if admin_info else "ADMIN"

    with st.sidebar:
        # 1) Admin badge at the very top
        st.markdown(
            f"""
            <div style="background: #1E293B; color: #F8FAFC; padding: 10px 12px; border-radius: 8px; margin-bottom: 14px; border-left: 4px solid #3B82F6; font-family: sans-serif;">
                <div style="font-size: 0.7rem; color: #94A3B8; text-transform: uppercase; font-weight: 700; letter-spacing: 0.5px;">Panel Administrator</div>
                <div style="font-size: 0.9rem; color: #F8FAFC; font-weight: 600; margin-top: 2px;">🛡️ {username} <span style="background: #3B82F6; color: white; padding: 1px 6px; border-radius: 4px; font-size: 0.65rem;">{role}</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # 2) Admin menu
        for admin_page in admin_nav:
            st.page_link(admin_page, use_container_width=True)

        # 3) Logout
        st.markdown("<hr style='margin: 12px 0; border-color: #E2E8F0;'>", unsafe_allow_html=True)
        if st.button("🚪 Keluar Admin", use_container_width=True, key="app_sidebar_logout_btn"):
            logout_admin_session()
            st.rerun()

else:
    # USER MODE: Only user pages visible (p_login is hidden from sidebar)
    pg = st.navigation(user_nav)

    st.sidebar.markdown("<br><hr style='margin: 12px 0; border-color: #E2E8F0;'>", unsafe_allow_html=True)
    if st.sidebar.button("🔐 Administrator Portal", use_container_width=True, key="user_sidebar_admin_btn"):
        st.switch_page("pages/90_Admin_Login.py")

# -------------------------------------------------------------
# 3. RUN CURRENT ROUTE
# -------------------------------------------------------------
pg.run()
