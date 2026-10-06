"""
Navigation component for English Self-Assessment.
Ensures clean separation between public participant flows and administrator controls.
Enforces that public users do not see admin management routes.
"""

import inspect

import streamlit as st
from services.admin_service import is_admin_authenticated, get_active_admin_session, logout_admin_session


def inject_custom_navigation_css() -> None:
    """
    Inject CSS rules into the sidebar to separate public navigation
    from administrative entry points based on authentication state or caller context.
    """
    is_admin_page = False
    try:
        stack = inspect.stack()
        if len(stack) > 1:
            caller_file = stack[1].filename
            if "Admin" in caller_file or "admin" in caller_file:
                is_admin_page = True
    except Exception:
        pass

    is_admin = is_admin_authenticated() or is_admin_page

    if not is_admin:
        # USER MODE: Hide all Admin management pages from public participant sidebar
        hide_admin_css = """
        <style>
        /* Hide Admin management pages from public sidebar */
        [data-testid="stSidebarNav"] li:has(a[href*="Admin"]),
        [data-testid="stSidebarNav"] li:has(a[href*="admin"]),
        [data-testid="stSidebarNavItems"] li:has(a[href*="Admin"]),
        [data-testid="stSidebarNavItems"] li:has(a[href*="admin"]),
        div[data-testid="stSidebarNav"] li:has(a[href*="Admin"]),
        div[data-testid="stSidebarNav"] li:has(a[href*="admin"]),
        a[data-testid="stSidebarNavLink"][href*="Admin"],
        a[data-testid="stSidebarNavLink"][href*="admin"] {
            display: none !important;
        }
        </style>
        """
        st.markdown(hide_admin_css, unsafe_allow_html=True)
    else:
        # ADMIN MODE: Hide all Public Participant pages from admin sidebar
        hide_login_css = ""
        if is_admin_authenticated():
            hide_login_css = """
            [data-testid="stSidebarNav"] li:has(a[href*="Admin_Login"]),
            [data-testid="stSidebarNavItems"] li:has(a[href*="Admin_Login"]),
            a[data-testid="stSidebarNavLink"][href*="Admin_Login"] {
                display: none !important;
            }
            """

        admin_css = f"""
        <style>
        /* Emphasize admin environment with distinct border */
        [data-testid="stSidebar"] {{
            border-right: 3px solid #3B82F6;
        }}
        /* Hide public participant pages in admin mode */
        [data-testid="stSidebarNav"] li:not(:has(a[href*="Admin"])):not(:has(a[href*="admin"])),
        [data-testid="stSidebarNavItems"] li:not(:has(a[href*="Admin"])):not(:has(a[href*="admin"])),
        [data-testid="stSidebarNav"] li:has(a[href="/"]),
        [data-testid="stSidebarNav"] li:has(a[href$="app"]),
        [data-testid="stSidebarNav"] li:has(a[href*="Identity"]),
        [data-testid="stSidebarNav"] li:has(a[href*="Test_Selection"]),
        [data-testid="stSidebarNav"] li:has(a[href*="Quiz"]),
        [data-testid="stSidebarNav"] li:has(a[href$="Result"]),
        [data-testid="stSidebarNav"] li:has(a[href*="History"]),
        [data-testid="stSidebarNavItems"] li:has(a[href="/"]),
        [data-testid="stSidebarNavItems"] li:has(a[href$="app"]),
        [data-testid="stSidebarNavItems"] li:has(a[href*="Identity"]),
        [data-testid="stSidebarNavItems"] li:has(a[href*="Test_Selection"]),
        [data-testid="stSidebarNavItems"] li:has(a[href*="Quiz"]),
        [data-testid="stSidebarNavItems"] li:has(a[href$="Result"]),
        [data-testid="stSidebarNavItems"] li:has(a[href*="History"]),
        a[data-testid="stSidebarNavLink"][href="/"],
        a[data-testid="stSidebarNavLink"][href$="app"],
        a[data-testid="stSidebarNavLink"][href*="Identity"],
        a[data-testid="stSidebarNavLink"][href*="Test_Selection"],
        a[data-testid="stSidebarNavLink"][href*="Quiz"],
        a[data-testid="stSidebarNavLink"][href$="Result"],
        a[data-testid="stSidebarNavLink"][href*="History"] {{
            display: none !important;
        }}
        {hide_login_css}
        </style>
        """
        st.markdown(admin_css, unsafe_allow_html=True)


def render_admin_header(title: str = "Admin Portal", subtitle: str = "") -> None:
    """
    Render a unified administrative header with session indicator and logout action.
    """
    admin_session = get_active_admin_session()
    if not admin_session:
        return

    username = admin_session.get("username", "Admin")
    role = admin_session.get("role", "admin").upper()

    st.markdown(
        f"""
        <div style="background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%); color: white; border-radius: 12px; padding: 1.2rem 1.6rem; margin-bottom: 1.5rem; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
            <div>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 1.4rem;">🛡️</span>
                    <h3 style="margin: 0; color: white; font-weight: 700; font-size: 1.3rem;">{title}</h3>
                    <span style="background: #3B82F6; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.72rem; font-weight: 700; letter-spacing: 0.5px;">{role}</span>
                </div>
                {f'<p style="margin: 4px 0 0 0; color: #94A3B8; font-size: 0.88rem;">{subtitle}</p>' if subtitle else ''}
            </div>
            <div style="text-align: right; color: #E2E8F0; font-size: 0.88rem;">
                Logged in as <strong>{username}</strong>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
