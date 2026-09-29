import sys
import os
import datetime

# Path setup
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Imports
from database.connection import get_db
from database import models
from auth.password_hash import verify_password
from config.settings import settings

def authenticate_user(email, password):
    """
    Authenticates a user against the MySQL database.
    Returns a dictionary or an error message.
    """
    db = next(get_db())
    
    try:
        # 1. Find the user
        user = db.query(models.User).filter(models.User.email == email).first()
        
        if not user:
            return None, "Invalid email or password."
        
        if user.status == "DISABLED":
            return None, "This account has been disabled by an administrator."
        
        # Check Lockout
        if user.locked_until:
            if user.locked_until > datetime.datetime.utcnow():
                remaining = (user.locked_until - datetime.datetime.utcnow()).seconds // 60
                return None, f"Account locked. Try again in {remaining} minutes."
            else:
                user.failed_login_attempts = 0
                user.locked_until = None
                db.commit()
        
        # Verify Password
        if verify_password(password, user.password_hash):
            # Success
            user.failed_login_attempts = 0
            user.locked_until = None
            db.commit()
            
            # Log audit
            log = models.AuditLog(
                user_id=user.id, organization_id=None, action="LOGIN_SUCCESS",
                target_type="USER", target_id=user.id, ip_address="127.0.0.1",
                device="Web", browser="Streamlit"
            )
            db.add(log)
            db.commit()
            
            # **CRITICAL FIX**: Extract data into a dict BEFORE session closes
            user_data = {
                'id': user.id,
                'email': user.email,
                'role': user.role,
                'name': user.name,
                'account_type': user.account_type,
                'mfa_enabled': user.mfa_enabled,
                'status': user.status
            }
            return user_data, "Success"
        
        else:
            # Failed login
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= settings.MAX_LOGIN_ATTEMPTS:
                user.locked_until = datetime.datetime.utcnow() + datetime.timedelta(minutes=settings.LOCKOUT_DURATION_MINUTES)
            
            log = models.AuditLog(
                user_id=user.id, organization_id=None, action="LOGIN_FAILED",
                target_type="USER", target_id=user.id, ip_address="127.0.0.1",
                device="Web", browser="Streamlit"
            )
            db.add(log)
            db.commit()
            
            return None, "Invalid email or password."
            
    finally:
        db.close()  # Ensure session is always closed

def get_user_by_id(user_id):
    """Fetches a user by ID. Returns dictionary or None."""
    db = next(get_db())
    try:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if user:
            return {
                'id': user.id,
                'email': user.email,
                'role': user.role,
                'name': user.name,
                'account_type': user.account_type,
                'mfa_enabled': user.mfa_enabled,
                'status': user.status
            }
        return None
    finally:
        db.close()

def handle_mfa_verification(user_id, otp_code):
    """Verifies MFA code. Returns boolean, message."""
    from auth.mfa import verify_mfa_code
    
    db = next(get_db())
    try:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        
        if not user or not user.mfa_enabled or not user.mfa_secret:
            return False, "MFA not configured for this user."
        
        if verify_mfa_code(user.mfa_secret, otp_code):
            log = models.AuditLog(
                user_id=user.id, organization_id=None, action="MFA_SUCCESS",
                target_type="USER", target_id=user.id, ip_address="127.0.0.1",
                device="Web", browser="Streamlit"
            )
            db.add(log)
            db.commit()
            return True, "MFA verified successfully."
        else:
            log = models.AuditLog(
                user_id=user.id, organization_id=None, action="MFA_FAILED",
                target_type="USER", target_id=user.id, ip_address="127.0.0.1",
                device="Web", browser="Streamlit"
            )
            db.add(log)
            db.commit()
            return False, "Invalid MFA code."
    finally:
        db.close()