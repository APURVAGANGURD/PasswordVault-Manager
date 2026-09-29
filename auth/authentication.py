# ============================================================
# auth/authentication.py
# SecureVault Manager
# Authentication + Email OTP + Password Reset + Audit Logging
# ============================================================

import sys
import os
import datetime
import secrets
import smtplib
import ssl

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from dotenv import load_dotenv

sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

load_dotenv()

from database.connection import get_db
from database import models

from auth.password_hash import (
    hash_password,
    verify_password
)

from config.settings import settings


# ============================================================
# SMTP CONFIGURATION
# ============================================================

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")


# ============================================================
# AUDIT HELPER (lazy import to avoid circular loops)
# ============================================================

def _audit(user_id, action, target=None, target_type=None,
           target_id=None, organization_id=None, details=None):
    try:
        from utils.audit_logger import create_audit_log
        create_audit_log(
            user_id=user_id,
            action=action,
            target=target,
            target_type=target_type,
            target_id=target_id,
            details=details,
            organization_id=organization_id,
        )
    except Exception as exc:
        print(f"[AUDIT SKIPPED] {exc}")


# ============================================================
# SEND EMAIL
# ============================================================

def send_email(to_email, subject, body):
    if not SMTP_HOST:
        return False, "SMTP_HOST is not configured."
    if not SMTP_USERNAME:
        return False, "SMTP_USERNAME is not configured."
    if not SMTP_PASSWORD:
        return False, "SMTP_PASSWORD is not configured."

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = SMTP_USERNAME
    message["To"] = to_email
    message.attach(MIMEText(body, "html"))

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(SMTP_USERNAME, [to_email], message.as_string())
        return True, "Email sent successfully."
    except Exception as e:
        return False, f"Email sending failed: {str(e)}"


# ============================================================
# OTP
# ============================================================

def generate_otp():
    return f"{secrets.randbelow(1000000):06d}"


def send_mfa_email(receiver_email, otp):
    subject = "SecureVault Manager - Login OTP"
    body = f"""
    <!DOCTYPE html><html><body style="font-family:Arial,sans-serif;
      background:#f5f7fb;padding:30px;">
      <div style="max-width:520px;margin:auto;background:white;padding:30px;
                  border-radius:12px;border:1px solid #e5e7eb;">
        <h2 style="color:#111827;">SecureVault Manager</h2>
        <p>Your login verification code is:</p>
        <div style="font-size:32px;font-weight:bold;letter-spacing:8px;
                    text-align:center;padding:20px;background:#f3f4f6;
                    border-radius:10px;">{otp}</div>
        <p>This OTP is valid for <b>5 minutes</b>.</p>
      </div></body></html>
    """
    return send_email(receiver_email, subject, body)


def send_settings_otp(receiver_email, otp, action):
    action_text = "enable Multi-Factor Authentication" if action == "enable" \
        else "disable Multi-Factor Authentication"
    subject = "SecureVault Manager - Security Verification"
    body = f"""
    <!DOCTYPE html><html><body style="font-family:Arial,sans-serif;
      background:#f5f7fb;padding:30px;">
      <div style="max-width:520px;margin:auto;background:white;padding:30px;
                  border-radius:12px;border:1px solid #e5e7eb;">
        <h2>Security Verification</h2>
        <p>Someone requested to <b>{action_text}</b> for your SecureVault account.</p>
        <p>Your verification OTP is:</p>
        <div style="font-size:32px;font-weight:bold;letter-spacing:8px;
                    text-align:center;padding:20px;background:#f3f4f6;
                    border-radius:10px;">{otp}</div>
        <p>This OTP expires in <b>5 minutes</b>.</p>
      </div></body></html>
    """
    return send_email(receiver_email, subject, body)


# ============================================================
# REGISTER USER
# ============================================================

def register_user(name, email, password, account_type, role, org_name=None):
    db = next(get_db())
    try:
        existing = db.query(models.User).filter(
            models.User.email == email.strip()
        ).first()
        if existing:
            return None, "Email already registered."

        email = email.strip().lower()

        if account_type == "PERSONAL":
            role = "PERSONAL_USER"
        elif account_type == "ORGANIZATION":
            if not role:
                role = "USER"

        user = models.User(
            name=name.strip(),
            email=email,
            password_hash=hash_password(password),
            account_type=account_type,
            role=role,
            email_verified=True,
            mfa_enabled=False,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        if account_type == "ORGANIZATION" and org_name:
            existing_org = db.query(models.Organization).filter(
                models.Organization.name == org_name.strip()
            ).first()

            if existing_org:
                user.organization_id = existing_org.id
            else:
                org = models.Organization(
                    name=org_name.strip(), owner_id=user.id
                )
                db.add(org)
                db.commit()
                db.refresh(org)
                user.organization_id = org.id

            existing_depts = db.query(models.Department).filter(
                models.Department.organization_id == user.organization_id
            ).count()

            if existing_depts == 0:
                for department_name in ["IT", "HR", "Finance",
                                        "Engineering", "Marketing"]:
                    db.add(models.Department(
                        organization_id=user.organization_id,
                        name=department_name,
                    ))
            db.commit()

        # -------- AUDIT --------
        _audit(
            user_id=user.id,
            action="USER_CREATED",
            target=f"Account created: {user.email}",
            target_type="USER",
            target_id=user.id,
            organization_id=user.organization_id,
        )

        return user, "Registration successful!"

    except Exception as e:
        db.rollback()
        return None, f"Registration failed: {str(e)}"
    finally:
        db.close()


# ============================================================
# AUTHENTICATE USER
# ============================================================

def authenticate_user(email, password):
    db = next(get_db())
    try:
        email = email.strip().lower()
        user = db.query(models.User).filter(
            models.User.email == email
        ).first()

        if not user:
            return None, "Invalid email or password."

        if user.status == "DISABLED":
            return None, "This account has been disabled by an administrator."

        if user.locked_until:
            if user.locked_until > datetime.datetime.utcnow():
                remaining = (
                    user.locked_until - datetime.datetime.utcnow()
                ).seconds // 60
                return None, f"Account locked. Try again in {remaining} minutes."
            else:
                user.failed_login_attempts = 0
                user.locked_until = None
                db.commit()

        if verify_password(password, user.password_hash):
            user.failed_login_attempts = 0
            user.locked_until = None
            db.commit()

            # -------- AUDIT --------
            _audit(
                user_id=user.id,
                action="LOGIN_SUCCESS",
                target=f"Signed in as {user.email}",
                target_type="USER",
                target_id=user.id,
                organization_id=user.organization_id,
            )

            user_data = {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "role": user.role,
                "account_type": user.account_type,
                "mfa_enabled": bool(user.mfa_enabled),
                "email_verified": bool(user.email_verified),
                "status": user.status,
                "organization_id": user.organization_id,
            }
            return user_data, "Success"

        # -------- FAILED --------
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= settings.MAX_LOGIN_ATTEMPTS:
            user.locked_until = datetime.datetime.utcnow() + datetime.timedelta(
                minutes=settings.LOCKOUT_DURATION_MINUTES
            )
        db.commit()

        _audit(
            user_id=user.id,
            action="LOGIN_FAILED",
            target=f"Failed login for {user.email}",
            target_type="USER",
            target_id=user.id,
            organization_id=user.organization_id,
        )

        return None, "Invalid email or password."

    except Exception as e:
        db.rollback()
        return None, f"Login failed: {str(e)}"
    finally:
        db.close()


# ============================================================
# GET USER BY ID
# ============================================================

def get_user_by_id(user_id):
    db = next(get_db())
    try:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            return None
        return {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "account_type": user.account_type,
            "mfa_enabled": bool(user.mfa_enabled),
            "email_verified": bool(user.email_verified),
            "status": user.status,
            "organization_id": user.organization_id,
        }
    finally:
        db.close()


# ============================================================
# CHANGE PASSWORD
# ============================================================

def change_password(user_id, current_password, new_password):
    db = next(get_db())
    try:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            return False, "User not found."

        if not verify_password(current_password, user.password_hash):
            return False, "Current password is incorrect."

        user.password_hash = hash_password(new_password)
        user.updated_at = datetime.datetime.utcnow()
        db.commit()

        _audit(
            user_id=user.id,
            action="PASSWORD_CHANGED",
            target=f"Changed account password",
            target_type="USER",
            target_id=user.id,
            organization_id=user.organization_id,
        )
        return True, "Password changed successfully."
    except Exception as e:
        db.rollback()
        return False, str(e)
    finally:
        db.close()


# ============================================================
# UPDATE PROFILE NAME
# ============================================================

def update_profile(user_id, name):
    db = next(get_db())
    try:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            return False, "User not found."
        if not name or not name.strip():
            return False, "Name cannot be empty."

        user.name = name.strip()
        user.updated_at = datetime.datetime.utcnow()
        db.commit()

        _audit(
            user_id=user.id,
            action="PROFILE_UPDATED",
            target=f"Updated profile name to {user.name}",
            target_type="USER",
            target_id=user.id,
            organization_id=user.organization_id,
        )
        return True, "Profile updated successfully."
    except Exception as e:
        db.rollback()
        return False, str(e)
    finally:
        db.close()


# ============================================================
# UPDATE MFA STATUS
# ============================================================

def update_mfa_status(user_id, enabled):
    db = next(get_db())
    try:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            return False, "User not found."

        user.mfa_enabled = bool(enabled)
        user.mfa_secret = None
        user.updated_at = datetime.datetime.utcnow()
        db.commit()

        _audit(
            user_id=user.id,
            action="MFA_ENABLED" if enabled else "MFA_DISABLED",
            target=("MFA enabled" if enabled else "MFA disabled"),
            target_type="USER",
            target_id=user.id,
            organization_id=user.organization_id,
        )
        return True, ("Email OTP MFA enabled." if enabled
                      else "Email OTP MFA disabled.")
    except Exception as e:
        db.rollback()
        return False, str(e)
    finally:
        db.close()


# ============================================================
# PASSWORD RESET TOKEN
# ============================================================

def generate_reset_token(email):
    db = next(get_db())
    try:
        email = email.strip().lower()
        user = db.query(models.User).filter(models.User.email == email).first()
        if not user:
            return False, "Email not found."

        token = secrets.token_urlsafe(32)
        reset_token = models.ResetToken(
            user_id=user.id,
            token_hash=token,
            expires_at=datetime.datetime.utcnow() + datetime.timedelta(hours=1),
        )
        db.add(reset_token)
        db.commit()

        subject = "SecureVault Password Reset"
        body = f"""
        <html><body>
            <h2>SecureVault Password Reset</h2>
            <p>Hello {user.name},</p>
            <p>Your password reset token is:</p>
            <h3>{token}</h3>
            <p>This token expires in 1 hour.</p>
        </body></html>
        """
        success, msg = send_email(email, subject, body)
        if success:
            _audit(
                user_id=user.id,
                action="PASSWORD_RESET_REQUESTED",
                target="Requested password reset",
                target_type="USER",
                target_id=user.id,
                organization_id=user.organization_id,
            )
            return True, "Password reset token sent to your email."
        return False, msg
    except Exception as e:
        db.rollback()
        return False, str(e)
    finally:
        db.close()


# ============================================================
# RESET PASSWORD
# ============================================================

def reset_password_with_token(token, new_password):
    db = next(get_db())
    try:
        reset_token = db.query(models.ResetToken).filter(
            models.ResetToken.token_hash == token,
            models.ResetToken.used == False,
            models.ResetToken.expires_at > datetime.datetime.utcnow(),
        ).first()

        if not reset_token:
            return False, "Invalid or expired reset token."

        user = db.query(models.User).filter(
            models.User.id == reset_token.user_id
        ).first()
        if not user:
            return False, "User not found."

        user.password_hash = hash_password(new_password)
        reset_token.used = True
        db.commit()

        _audit(
            user_id=user.id,
            action="PASSWORD_RESET",
            target="Reset password using token",
            target_type="USER",
            target_id=user.id,
            organization_id=user.organization_id,
        )
        return True, "Password reset successful."
    except Exception as e:
        db.rollback()
        return False, str(e)
    finally:
        db.close()