from typing import Any
import re
import bcrypt

BCRYPT_ROUNDS = 12

# Common weak passwords to reject
WEAK_PASSWORDS = {
    "password",
    "password123",
    "12345678",
    "qwerty123",
    "abc123456",
    "password1",
    "welcome123",
    "123456789",
    "qwertyuiop",
    "letmein",
    "admin123",
    "passw0rd",
}


def hash_password(password: str) -> str:
    try:
        # Generate salt and hash
        salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")
    except Exception as e:
        raise


def verify_password(password: str, password_hash: str) -> bool:
    try:
        is_valid = bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
        return is_valid
    except Exception as e:
        return False


def validate_password_strength(password: str) -> dict[str, Any]:
    """
    Validate password strength.

    Enforces the following policy:
    - Minimum 8 characters (configurable via MIN_PASSWORD_LENGTH)
    - Must contain at least one lowercase letter
    - Must contain at least one uppercase letter
    - Must contain at least one number
    - Must contain at least one special character (!@#$%^&*)
    - Must not be a common weak password

    Calculates a strength score (0-100) based on length and complexity.

    Args:
        password: The password to validate

    Returns:
        Dict containing:
        - valid: Boolean indicating if requirements are met
        - score: Integer score (0-100)
        - errors: List of specific validation errors
        - strength: String category ("weak", "medium", "strong")
    """
    errors: list[str] = []
    score = 0
    length = len(password)

    # Define validation rules: (pattern, error_message, score_value)
    validation_rules = [
        (r"[a-z]", "Password must contain at least one lowercase letter", 20),
        (r"[A-Z]", "Password must contain at least one uppercase letter", 20),
        (r"[0-9]", "Password must contain at least one number", 20),
        (r"[^a-zA-Z0-9]", "Password must contain at least one special character (!@#$%^&*)", 15),
    ]

    # Length validation with bonuses
    if length < 8:
        errors.append("Password must be at least 8 characters")
    else:
        score += 20
        score += 10 if length >= 12 else 0
        score += 5 if length >= 16 else 0

    # Apply validation rules
    for pattern, error_msg, score_value in validation_rules:
        if re.search(pattern, password):
            score += score_value
        else:
            errors.append(error_msg)

    # Check against common weak passwords
    if password.lower() in WEAK_PASSWORDS:
        errors.append("Password is too common and easily guessable")
        score = 0

    # Check for repeated characters (e.g., "aaaa" or "1111")
    if re.search(r"(.)\1{3,}", password):
        errors.append("Password contains too many repeated characters")
        score -= 10

    # Check for sequential characters (e.g., "1234" or "abcd")
    if re.search(r"(0123|1234|2345|3456|4567|5678|6789|abcd|bcde|cdef)", password.lower()):
        errors.append("Password contains sequential characters")
        score -= 10

    # Clamp score to 0-100
    score = max(0, min(100, score))

    # Determine strength category
    if score >= 80:
        strength = "strong"
    elif score >= 60:
        strength = "medium"
    else:
        strength = "weak"

    result = {"valid": len(errors) == 0, "score": score, "errors": errors, "strength": strength}

    return result
