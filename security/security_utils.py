import re

def validate_email(email: str) -> bool:
    return re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email) is not None

def validate_password_strength(password: str) -> list:
    errors = []
    if len(password) < 12: errors.append("Password must be at least 12 characters.")
    if not re.search(r"[A-Z]", password): errors.append("Must contain uppercase.")
    if not re.search(r"[a-z]", password): errors.append("Must contain lowercase.")
    if not re.search(r"\d", password): errors.append("Must contain a number.")
    if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]", password): errors.append("Must contain special char.")
    return errors