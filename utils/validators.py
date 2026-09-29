import re
from email_validator import validate_email, EmailNotValidError

class Validators:
    @staticmethod
    def validate_email_format(email: str) -> tuple:
        try:
            validation = validate_email(email, check_deliverability=False)
            email = validation.normalized
            return True, "Valid email"
        except EmailNotValidError as e:
            return False, str(e)
    
    @staticmethod
    def validate_full_name(name: str) -> tuple:
        if not name or len(name.strip()) < 2:
            return False, "Full name must be at least 2 characters long"
        if len(name) > 100:
            return False, "Full name must be less than 100 characters"
        if not re.match(r"^[a-zA-Z\s\-']+$", name):
            return False, "Name contains invalid characters"
        return True, "Valid name"
    
    @staticmethod
    def validate_role(role: str) -> tuple:
        valid_roles = ['admin', 'manager', 'user', 'personal']
        role_lower = role.lower()
        if role_lower not in valid_roles:
            return False, f"Role must be one of: {', '.join(valid_roles)}"
        return True, "Valid role"