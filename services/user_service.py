"""
User identity management and session handling service.
Separates business logic from UI components.
"""

from typing import Optional, Any
from pathlib import Path
import streamlit as st

from database.db import get_connection
from database.models import User
from database import queries
from utils.validators import validate_identity_form


SESSION_KEY_USER_ID = "active_user_id"
SESSION_KEY_USER_NAME = "active_user_name"
SESSION_KEY_USER_EMAIL = "active_user_email"
SESSION_KEY_USER_INSTITUTION = "active_user_institution"
SESSION_KEY_USER_PROGRAM = "active_user_program"


def process_user_identity(
    name: str,
    email: str,
    institution: Optional[str] = None,
    program: Optional[str] = None,
    db_path: Optional[str | Path] = None,
) -> tuple[bool, Optional[User], dict[str, str]]:
    """
    Validate identity form fields, store or retrieve user in SQLite,
    and return (is_success, user_instance, error_dict).
    """
    is_valid, errors, normalized_email = validate_identity_form(name, email)
    if not is_valid or normalized_email is None:
        return False, None, errors

    clean_name = name.strip()
    clean_inst = institution.strip() if institution and institution.strip() else None
    clean_prog = program.strip() if program and program.strip() else None

    with get_connection(db_path) as conn:
        user = queries.get_or_create_user(
            conn=conn,
            name=clean_name,
            email=normalized_email,
            institution=clean_inst,
            program=clean_prog,
        )

    return True, user, {}


def login_user_by_email(
    email: str,
    db_path: Optional[str | Path] = None,
) -> tuple[bool, Optional[User], str]:
    """
    Authenticate an existing participant by their registered email address.
    Returns (success, user_instance, message).
    """
    clean_email = email.strip().lower() if email else ""
    if not clean_email or "@" not in clean_email or "." not in clean_email:
        return False, None, "Silakan masukkan alamat email yang valid."

    with get_connection(db_path) as conn:
        user = queries.get_user_by_email(conn, clean_email)

    if not user:
        return False, None, f"Email '{clean_email}' belum terdaftar. Silakan daftar terlebih dahulu di tab 'Daftar Baru'."

    return True, user, f"Selamat datang kembali, {user.name}!"



def set_active_user_session(user: User) -> None:
    """Store the authenticated user in Streamlit session state."""
    st.session_state[SESSION_KEY_USER_ID] = user.id
    st.session_state[SESSION_KEY_USER_NAME] = user.name
    st.session_state[SESSION_KEY_USER_EMAIL] = user.email
    st.session_state[SESSION_KEY_USER_INSTITUTION] = user.institution
    st.session_state[SESSION_KEY_USER_PROGRAM] = user.program


def get_active_user_session() -> Optional[dict[str, Any]]:
    """Retrieve active user dictionary from Streamlit session state if present."""
    user_id = st.session_state.get(SESSION_KEY_USER_ID)
    if user_id is None:
        return None

    return {
        "id": user_id,
        "name": st.session_state.get(SESSION_KEY_USER_NAME, ""),
        "email": st.session_state.get(SESSION_KEY_USER_EMAIL, ""),
        "institution": st.session_state.get(SESSION_KEY_USER_INSTITUTION),
        "program": st.session_state.get(SESSION_KEY_USER_PROGRAM),
    }


def is_user_authenticated() -> bool:
    """Check whether a user identity has been verified in the current session."""
    return st.session_state.get(SESSION_KEY_USER_ID) is not None


def clear_active_user_session() -> None:
    """Clear active user session data."""
    st.session_state.pop(SESSION_KEY_USER_ID, None)
    st.session_state.pop(SESSION_KEY_USER_NAME, None)
    st.session_state.pop(SESSION_KEY_USER_EMAIL, None)
    st.session_state.pop(SESSION_KEY_USER_INSTITUTION, None)
    st.session_state.pop(SESSION_KEY_USER_PROGRAM, None)
