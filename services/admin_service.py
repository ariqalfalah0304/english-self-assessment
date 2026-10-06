"""
Admin Authentication and Session Service for English Self-Assessment.
Handles:
- Secure bcrypt password hashing and verification
- Admin credential validation
- Administrator login authentication
- Session-based admin state management
- Logout functionality
- Role-based access control (admin, superadmin)
- Route protection guards for admin operations
"""

from typing import Optional, Any
from pathlib import Path
from datetime import datetime, timezone
import re
import bcrypt
import streamlit as st

from database.db import get_connection
from database.models import Admin
from database import queries


# Session State Keys
SESSION_KEY_ADMIN_ID = "admin_id"
SESSION_KEY_ADMIN_USERNAME = "admin_username"
SESSION_KEY_ADMIN_ROLE = "admin_role"
SESSION_KEY_ADMIN_AUTH = "is_admin_authenticated"
SESSION_KEY_ADMIN_LOGIN_TIME = "admin_login_time"

VALID_ADMIN_ROLES = {"admin", "superadmin"}


# ==========================================
# 1. PASSWORD HASHING & VERIFICATION (BCRYPT)
# ==========================================

def hash_password(plain_password: str) -> str:
    """
    Hash a plaintext password using bcrypt with a secure salt.
    Never stores or logs plaintext passwords.
    """
    if not plain_password:
        raise ValueError("Password cannot be empty.")
    
    password_bytes = plain_password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=12)
    hashed_bytes = bcrypt.hashpw(password_bytes, salt)
    return hashed_bytes.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plaintext password against a bcrypt hash.
    Gracefully handles malformed hashes without raising uncaught exceptions.
    """
    if not plain_password or not hashed_password:
        return False

    try:
        password_bytes = plain_password.encode("utf-8")
        hashed_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception:
        return False


def validate_admin_credentials_format(username: str, plain_password: str) -> tuple[bool, str]:
    """
    Validate username and password format before account creation.
    - Username: 3 to 50 chars, alphanumeric, underscore, dot, hyphen, or email.
    - Password: min 8 chars, at least one letter and one number or special char.
    """
    clean_user = username.strip() if username else ""
    if len(clean_user) < 3:
        return False, "Username must be at least 3 characters long."
    if len(clean_user) > 50:
        return False, "Username must not exceed 50 characters."
    if not re.match(r"^[a-zA-Z0-9_.@-]{3,50}$", clean_user):
        return False, "Username contains invalid characters. Use letters, numbers, dot, underscore, or hyphens."

    if len(plain_password) < 8:
        return False, "Password must be at least 8 characters long."

    has_letter = any(c.isalpha() for c in plain_password)
    has_digit_or_symbol = any(not c.isalpha() for c in plain_password)
    if not (has_letter and has_digit_or_symbol):
        return False, "Password must include both letters and at least one number or symbol."

    return True, ""


# ==========================================
# 2. ADMIN ACCOUNT MANAGEMENT
# ==========================================

def create_admin_account(
    username: str,
    plain_password: str,
    role: str = "admin",
    db_path: Optional[str | Path] = None,
) -> tuple[bool, Optional[Admin], str]:
    """
    Create a new administrator account with bcrypt hashed password.
    Enforces uniqueness and credential constraints.
    """
    is_valid, msg = validate_admin_credentials_format(username, plain_password)
    if not is_valid:
        return False, None, msg

    norm_role = role.strip().lower()
    if norm_role not in VALID_ADMIN_ROLES:
        return False, None, f"Invalid role '{role}'. Allowed: {', '.join(VALID_ADMIN_ROLES)}"

    clean_user = username.strip()
    pw_hash = hash_password(plain_password)

    with get_connection(db_path) as conn:
        existing = queries.get_admin_by_username(conn, clean_user)
        if existing:
            return False, None, f"An administrator account with username '{clean_user}' already exists."

        try:
            admin_id = queries.create_admin(
                conn=conn,
                username=clean_user,
                password_hash=pw_hash,
                role=norm_role,
            )
            admin = queries.get_admin_by_id(conn, admin_id)
            return True, admin, "Administrator account created successfully."
        except Exception as e:
            return False, None, f"Database error during admin creation: {str(e)}"


def has_any_admin(db_path: Optional[str | Path] = None) -> bool:
    """Check if any administrator accounts exist in the database."""
    with get_connection(db_path) as conn:
        return queries.count_admins(conn) > 0


def init_first_admin(
    username: str,
    plain_password: str,
    db_path: Optional[str | Path] = None,
) -> tuple[bool, Optional[Admin], str]:
    """
    Safe utility to initialize the very first administrator account (superadmin).
    Only proceeds if the admin table is completely empty.
    """
    with get_connection(db_path) as conn:
        if queries.count_admins(conn) > 0:
            return False, None, "Admin initialization refused: administrator accounts already exist."

    return create_admin_account(
        username=username,
        plain_password=plain_password,
        role="superadmin",
        db_path=db_path,
    )


def update_admin_account_credentials(
    admin_id: int,
    current_password: str,
    new_username: str,
    new_password: Optional[str] = None,
    confirm_password: Optional[str] = None,
    db_path: Optional[str | Path] = None,
) -> tuple[bool, str]:
    """
    Update administrator credentials (username and/or password).
    Requires current password verification for security.
    Updates session state upon success.
    """
    if not current_password:
        return False, "Current password is required to save changes."

    clean_new_username = new_username.strip() if new_username else ""
    if len(clean_new_username) < 3:
        return False, "New username must be at least 3 characters long."
    if len(clean_new_username) > 50:
        return False, "New username must not exceed 50 characters."
    if not re.match(r"^[a-zA-Z0-9_.@-]{3,50}$", clean_new_username):
        return False, "Username contains invalid characters. Use letters, numbers, dot, underscore, or hyphens."

    with get_connection(db_path) as conn:
        admin = queries.get_admin_by_id(conn, admin_id)
        if not admin:
            return False, "Administrator account not found."

        # Verify current password
        if not verify_password(current_password, admin.password_hash):
            return False, "Incorrect current password."

        # Check username uniqueness if changed
        if clean_new_username.lower() != admin.username.lower():
            existing = queries.get_admin_by_username(conn, clean_new_username)
            if existing and existing.id != admin_id:
                return False, f"Username '{clean_new_username}' is already taken by another administrator."

        # Process new password if provided
        final_hash = admin.password_hash
        if new_password or confirm_password:
            if new_password != confirm_password:
                return False, "New password and confirmation password do not match."

            is_valid_pw, pw_msg = validate_admin_credentials_format(clean_new_username, new_password or "")
            if not is_valid_pw:
                return False, pw_msg

            final_hash = hash_password(new_password or "")

        updated = queries.update_admin_credentials(
            conn=conn,
            admin_id=admin_id,
            new_username=clean_new_username,
            new_password_hash=final_hash,
        )

        if updated:
            # Update active Streamlit session if editing the logged-in admin
            if st.session_state.get(SESSION_KEY_ADMIN_ID) == admin_id:
                st.session_state[SESSION_KEY_ADMIN_USERNAME] = clean_new_username
            return True, "Administrator credentials updated successfully!"
        else:
            return False, "Failed to update administrator credentials."


# ==========================================
# 3. AUTHENTICATION & VERIFICATION
# ==========================================

def authenticate_admin(
    username: str,
    plain_password: str,
    db_path: Optional[str | Path] = None,
) -> tuple[bool, Optional[Admin], str]:
    """
    Authenticate an administrator by verifying username and bcrypt password hash.
    Returns: (is_authenticated, admin_record, message)
    """
    clean_user = username.strip() if username else ""
    if not clean_user or not plain_password:
        return False, None, "Username and password are required."

    with get_connection(db_path) as conn:
        admin = queries.get_admin_by_username(conn, clean_user)

    if not admin:
        return False, None, "Invalid username or password."

    if not verify_password(plain_password, admin.password_hash):
        return False, None, "Invalid username or password."

    return True, admin, "Authentication successful."


# ==========================================
# 4. SESSION STATE MANAGEMENT
# ==========================================

def login_admin_session(admin: Admin) -> None:
    """Store authenticated administrator details in Streamlit session state."""
    st.session_state[SESSION_KEY_ADMIN_ID] = admin.id
    st.session_state[SESSION_KEY_ADMIN_USERNAME] = admin.username
    st.session_state[SESSION_KEY_ADMIN_ROLE] = admin.role
    st.session_state[SESSION_KEY_ADMIN_AUTH] = True
    st.session_state[SESSION_KEY_ADMIN_LOGIN_TIME] = datetime.now(timezone.utc).isoformat()


def logout_admin_session() -> None:
    """Purge all administrator session state keys."""
    for key in [
        SESSION_KEY_ADMIN_ID,
        SESSION_KEY_ADMIN_USERNAME,
        SESSION_KEY_ADMIN_ROLE,
        SESSION_KEY_ADMIN_AUTH,
        SESSION_KEY_ADMIN_LOGIN_TIME,
    ]:
        st.session_state.pop(key, None)


def is_admin_authenticated() -> bool:
    """Check if an administrator is currently authenticated in the active session."""
    return bool(
        st.session_state.get(SESSION_KEY_ADMIN_AUTH) is True
        and st.session_state.get(SESSION_KEY_ADMIN_ID) is not None
        and st.session_state.get(SESSION_KEY_ADMIN_USERNAME) is not None
    )


def get_active_admin_session() -> Optional[dict[str, Any]]:
    """Retrieve active administrator session dictionary or None."""
    if not is_admin_authenticated():
        return None

    return {
        "id": st.session_state.get(SESSION_KEY_ADMIN_ID),
        "username": st.session_state.get(SESSION_KEY_ADMIN_USERNAME),
        "role": st.session_state.get(SESSION_KEY_ADMIN_ROLE, "admin"),
        "login_time": st.session_state.get(SESSION_KEY_ADMIN_LOGIN_TIME),
    }


def check_admin_role(required_role: str = "admin") -> bool:
    """
    Check if the authenticated admin has the required role or superadmin privileges.
    """
    admin_session = get_active_admin_session()
    if not admin_session:
        return False

    current_role = admin_session.get("role", "admin").lower()
    if current_role == "superadmin":
        return True
    return current_role == required_role.lower()


# ==========================================
# 5. ADMIN ROUTE PROTECTION GUARD
# ==========================================

def require_admin_auth(required_role: str = "admin") -> bool:
    """
    Enforce security guard on admin views.
    If the caller is not authenticated as an admin or lacks the required role:
    - Renders an unauthorized access alert
    - Halts execution with st.stop()
    Returns True if successfully authorized.
    """
    if not is_admin_authenticated():
        st.error("⛔ Unauthorized Access: Administrator Authentication Required")
        st.markdown(
            """
            <div style="background: #FEF2F2; border: 2px solid #FCA5A5; border-radius: 12px; padding: 1.5rem; margin: 1rem 0;">
                <h3 style="margin: 0 0 0.5rem 0; color: #991B1B;">🔒 Admin Access Restricted</h3>
                <p style="margin: 0 0 1rem 0; color: #7F1D1D; font-size: 0.95rem; line-height: 1.5;">
                    This section contains sensitive administrator controls and is protected. 
                    Public participants and unauthenticated users are not permitted to access this area.
                </p>
                <div style="font-size: 0.85rem; color: #6B7280;">
                    Please log in with verified administrator credentials to proceed.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        c1, c2 = st.columns([1.5, 3])
        with c1:
            if st.button("🔐 Go to Admin Login", type="primary", use_container_width=True):
                st.switch_page("pages/90_Admin_Login.py")
        st.stop()
        return False

    if not check_admin_role(required_role):
        st.error(f"⛔ Access Denied: Insufficient Privileges. Required role: '{required_role}'.")
        st.stop()
        return False

    return True
