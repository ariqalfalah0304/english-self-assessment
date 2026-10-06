"""
Validation utilities for English Self-Assessment input forms.
Uses email-validator for RFC-compliant email validation.
"""

from typing import Optional
from email_validator import validate_email, EmailNotValidError


def validate_name(name: Optional[str]) -> tuple[bool, str]:
    """
    Validate that user full name is non-empty and has at least 2 characters.
    Returns (is_valid, error_message).
    """
    if not name or not name.strip():
        return False, "Full Name is required. Please enter your name."
    
    cleaned = name.strip()
    if len(cleaned) < 2:
        return False, "Full Name must be at least 2 characters long."
    
    return True, ""


def validate_email_address(email: Optional[str]) -> tuple[bool, str, Optional[str]]:
    """
    Validate email address using email-validator library.
    Returns (is_valid, error_message, normalized_email).
    """
    if not email or not email.strip():
        return False, "Email address is required.", None

    cleaned = email.strip()
    try:
        # check_deliverability=False allows valid syntax checking without external DNS lookups
        email_info = validate_email(cleaned, check_deliverability=False)
        return True, "", email_info.normalized
    except EmailNotValidError as e:
        return False, f"Invalid email format: {str(e)}", None


def validate_identity_form(
    name: Optional[str],
    email: Optional[str],
) -> tuple[bool, dict[str, str], Optional[str]]:
    """
    Validate all fields of the identity form.
    Returns (is_all_valid, field_errors_dict, normalized_email).
    """
    errors: dict[str, str] = {}
    normalized_email = None

    name_valid, name_err = validate_name(name)
    if not name_valid:
        errors["name"] = name_err

    email_valid, email_err, norm_email = validate_email_address(email)
    if not email_valid:
        errors["email"] = email_err
    else:
        normalized_email = norm_email

    return len(errors) == 0, errors, normalized_email
