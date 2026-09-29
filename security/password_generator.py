import secrets
import string

def generate_password(length: int = 16, upper: bool = True, lower: bool = True, digits: bool = True, special: bool = True) -> str:
    chars = ""
    if upper: chars += string.ascii_uppercase
    if lower: chars += string.ascii_lowercase
    if digits: chars += string.digits
    if special: chars += "!@#$%^&*()_+-=[]{}|;:,.<>?"
    if not chars: return ""
    return ''.join(secrets.choice(chars) for _ in range(length))