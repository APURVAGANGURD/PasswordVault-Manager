import sys, os, secrets, datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_db
from database import models
from auth.password_hash import hash_password
from security.security_utils import validate_email, validate_password_strength

def register_user(name, email, password, account_type, org_name=None):
    db = next(get_db())
    
    # Validate
    if not validate_email(email):
        return None, "Invalid Email"
    if validate_password_strength(password):
        return None, "Password does not meet requirements"

    # Check existing
    existing = db.query(models.User).filter(models.User.email == email).first()
    if existing:
        return None, "Email already registered."

    role = "PERSONAL_USER"
    if account_type == "ORGANIZATION":
        role = "OWNER"

    user = models.User(name=name, email=email, password_hash=hash_password(password), 
                       account_type=account_type, role=role, email_verified=True) # Dev mode
    db.add(user)
    db.commit()
    db.refresh(user)

    if account_type == "ORGANIZATION" and org_name:
        org = models.Organization(name=org_name, owner_id=user.id)
        db.add(org)
        db.commit()

    return user, "Registration successful"