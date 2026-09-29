import streamlit as st
import sys
import os
import datetime
import secrets

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

from database.connection import get_db
from database import models

from auth.password_hash import (
    hash_password,
    verify_password
)

from auth.authentication import (
    generate_otp,
    send_mfa_email
)

from modules.notifications import (
    get_user_preferences,
    update_user_preferences,
    notify_security_alert
)

from utils.audit_logger import create_audit_log


OTP_EXPIRY_MINUTES = 5


# ============================================================
# CSS
# ============================================================

from utils.theme import inject_cyber_theme, render_html

def load_css():
    inject_cyber_theme()
    render_html("""
    <style>
        .settings-title {
            font-size: 26px;
            font-weight: 800;
            color: #f8fafc !important;
            margin-bottom: 4px;
            letter-spacing: -0.4px;
        }
        .settings-subtitle {
            color: #94a3b8 !important;
            font-size: 13.5px;
            margin-bottom: 20px;
        }
        .settings-h2 {
            font-size: 16px;
            font-weight: 700;
            color: #f8fafc !important;
            margin-top: 18px;
            margin-bottom: 4px;
        }
        .settings-caption {
            color: #94a3b8 !important;
            font-size: 12.5px;
            margin-bottom: 14px;
        }
        .profile-row {
            padding: 8px 0;
            border-bottom: 1px solid rgba(56, 189, 248, 0.1);
        }
    </style>
    """)


# ============================================================
# HELPERS
# ============================================================

def _fresh_user(user_id):
    db = next(get_db())
    try:
        return db.query(models.User).filter(models.User.id == user_id).first()
    finally:
        db.close()


def _sync_session_user(db_user):
    current = st.session_state.get("user")
    if not current or current.get("id") != db_user.id:
        return
    current.update({
        "id": db_user.id,
        "name": db_user.name,
        "email": db_user.email,
        "role": db_user.role,
        "account_type": db_user.account_type,
        "mfa_enabled": bool(db_user.mfa_enabled),
        "email_verified": bool(db_user.email_verified),
        "status": db_user.status,
        "organization_id": db_user.organization_id,
    })


def _clear_setting_otp():
    for key in ["settings_otp", "settings_otp_expires",
                "settings_otp_action", "settings_otp_email"]:
        st.session_state.pop(key, None)


# ============================================================
# MFA FLOW
# ============================================================

def _start_mfa_action(action, email):
    otp = generate_otp()
    sent = send_mfa_email(email, otp)
    if not sent:
        st.error("OTP could not be sent. Please check SMTP settings in .env.")
        return False

    st.session_state["settings_otp"] = otp
    st.session_state["settings_otp_expires"] = (
        datetime.datetime.now() + datetime.timedelta(minutes=OTP_EXPIRY_MINUTES)
    ).timestamp()
    st.session_state["settings_otp_action"] = action
    st.session_state["settings_otp_email"] = email
    return True


def _verify_mfa_action(user, code):
    expected = str(st.session_state.get("settings_otp", ""))
    expires = st.session_state.get("settings_otp_expires", 0)
    action = st.session_state.get("settings_otp_action")

    if not expected or not action:
        return (False, "No OTP request is active. Please request a new OTP.")

    if datetime.datetime.now().timestamp() > float(expires):
        _clear_setting_otp()
        return (False, "OTP expired. Please request a new OTP.")

    if not secrets.compare_digest(str(code).strip(), expected):
        return (False, "Invalid OTP. Please try again.")

    db = next(get_db())
    try:
        db_user = db.query(models.User).filter(
            models.User.id == user["id"]
        ).first()
        if not db_user:
            return (False, "User account not found.")

        if action == "enable":
            db_user.mfa_enabled = True
            message = "Email OTP MFA enabled successfully."
        else:
            db_user.mfa_enabled = False
            db_user.mfa_secret = None
            message = "Email OTP MFA disabled successfully."

        db.commit()
        db.refresh(db_user)
        _sync_session_user(db_user)

        create_audit_log(
            user_id=db_user.id,
            action="MFA_ENABLED" if action == "enable" else "MFA_DISABLED",
            target=("MFA enabled" if action == "enable" else "MFA disabled"),
            target_type="USER",
            target_id=db_user.id,
            organization_id=db_user.organization_id,
        )

        try:
            notify_security_alert(db, db_user.id, message)
        except Exception:
            pass

        _clear_setting_otp()
        return True, message

    except Exception as exc:
        db.rollback()
        return (False, f"Unable to update MFA: {exc}")
    finally:
        db.close()


# ============================================================
# PROFILE
# ============================================================

def _profile_section(user):
    st.markdown(
        '<div class="settings-h2">👤 Profile</div>'
        '<div class="settings-caption">Update your basic SecureVault account information.</div>',
        unsafe_allow_html=True
    )

    db_user = _fresh_user(user["id"])
    if not db_user:
        st.error("User account could not be loaded.")
        return

    with st.form("profile_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Full Name", value=db_user.name or "")
        with col2:
            email = st.text_input("Email Address", value=db_user.email or "")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.text_input("Account Type",
                          value=str(db_user.account_type), disabled=True)
        with col2:
            st.text_input("Role", value=str(db_user.role), disabled=True)
        with col3:
            st.text_input("Account Status",
                          value=str(db_user.status), disabled=True)

        save = st.form_submit_button("Save Profile", use_container_width=True)

    if save:
        name = name.strip()
        email = email.strip().lower()

        if not name:
            st.error("Full name is required.")
            return
        if not email or "@" not in email:
            st.error("Enter a valid email address.")
            return

        db = next(get_db())
        try:
            duplicate = db.query(models.User).filter(
                models.User.email == email,
                models.User.id != db_user.id
            ).first()
            if duplicate:
                st.error("That email address is already registered.")
                return

            db_user.name = name
            db_user.email = email
            db.commit()
            db.refresh(db_user)

            create_audit_log(
                user_id=db_user.id,
                action="PROFILE_UPDATED",
                target=f"Updated profile to {db_user.name} ({db_user.email})",
                target_type="USER",
                target_id=db_user.id,
                organization_id=db_user.organization_id,
            )

            _sync_session_user(db_user)
            st.success("Profile updated successfully.")
            st.rerun()

        except Exception as exc:
            db.rollback()
            st.error(f"Could not update profile: {exc}")
        finally:
            db.close()


# ============================================================
# PASSWORD
# ============================================================

def _password_section(user):
    st.markdown(
        '<div class="settings-h2">🔑 Change Password</div>'
        '<div class="settings-caption">Use a strong password that you do not reuse elsewhere.</div>',
        unsafe_allow_html=True
    )

    with st.form("change_password_form"):
        current = st.text_input("Current Password", type="password")
        new = st.text_input("New Password", type="password")
        confirm = st.text_input("Confirm New Password", type="password")
        change = st.form_submit_button("Change Password",
                                       use_container_width=True)

    if change:
        if not current or not new or not confirm:
            st.error("All password fields are required.")
            return
        if new != confirm:
            st.error("New password and confirmation do not match.")
            return
        if len(new) < 8:
            st.error("New password must contain at least 8 characters.")
            return
        if new == current:
            st.error("New password must be different from your current password.")
            return

        db = next(get_db())
        try:
            db_user = db.query(models.User).filter(
                models.User.id == user["id"]
            ).first()
            if not db_user:
                st.error("User account not found.")
                return

            if not verify_password(current, db_user.password_hash):
                st.error("Current password is incorrect.")
                return

            db_user.password_hash = hash_password(new)
            db.commit()

            create_audit_log(
                user_id=db_user.id,
                action="PASSWORD_CHANGED",
                target="Changed account password",
                target_type="USER",
                target_id=db_user.id,
                organization_id=db_user.organization_id,
            )

            st.success("Password changed successfully.")

        except Exception as exc:
            db.rollback()
            st.error(f"Could not change password: {exc}")
        finally:
            db.close()


# ============================================================
# MFA UI
# ============================================================

def _mfa_section(user):
    st.markdown(
        '<div class="settings-h2">🛡️ Email OTP Multi-Factor Authentication</div>'
        '<div class="settings-caption">Secure your login with a 6-digit OTP sent to your registered email.</div>',
        unsafe_allow_html=True
    )

    if st.session_state.get("mfa_disabled_popup", False):
        st.warning(
            "⚠️ Multi-Factor Authentication is now DISABLED. "
            "Your account is less secure. We strongly recommend re-enabling MFA."
        )
        if st.button("OK, I understand",
                     key="mfa_popup_dismiss", use_container_width=True):
            st.session_state.pop("mfa_disabled_popup", None)
            st.rerun()
        st.divider()

    db_user = _fresh_user(user["id"])
    if not db_user:
        st.error("User account could not be loaded.")
        return

    enabled = bool(db_user.mfa_enabled)

    if enabled:
        st.success(f"MFA is enabled. Login OTPs are sent to {db_user.email}.")
    else:
        st.warning("MFA is currently disabled.")

    action = st.session_state.get("settings_otp_action")

    if not action:
        button_label = "Disable Email OTP MFA" if enabled else "Enable Email OTP MFA"
        if st.button(button_label, use_container_width=True):
            requested_action = "disable" if enabled else "enable"
            if _start_mfa_action(requested_action, db_user.email):
                st.info(f"A 6-digit OTP was sent to {db_user.email}.")
                st.rerun()
        return

    expected_action = "enable" if not enabled else "disable"
    if action != expected_action:
        _clear_setting_otp()
        st.rerun()

    masked_email = db_user.email
    if "@" in masked_email:
        local, domain = masked_email.split("@", 1)
        masked_email = (local[:2] + "***@" + domain) if len(local) > 2 else "***@" + domain

    st.info(f"Enter the OTP sent to {masked_email}. The code expires in 5 minutes.")

    with st.form("settings_mfa_otp_form"):
        code = st.text_input("6-digit OTP", max_chars=6, placeholder="123456")
        c1, c2 = st.columns(2)
        with c1:
            verify = st.form_submit_button("Verify OTP", use_container_width=True)
        with c2:
            cancel = st.form_submit_button("Cancel", use_container_width=True)

    if cancel:
        _clear_setting_otp()
        st.rerun()

    if verify:
        if not code.isdigit() or len(code) != 6:
            st.error("Enter the 6-digit OTP.")
            return

        was_disabling = (action == "disable")
        ok, message = _verify_mfa_action(user, code)

        if ok:
            if was_disabling:
                st.session_state["mfa_disabled_popup"] = True
            st.success(message)
            st.rerun()
        else:
            st.error(message)

    if st.button("Resend OTP", use_container_width=True):
        if _start_mfa_action(action, db_user.email):
            st.success("A new OTP has been sent.")
            st.rerun()


# ============================================================
# NOTIFICATIONS
# ============================================================

def _notifications_section(user):
    st.markdown(
        '<div class="settings-h2">🔔 Notifications</div>'
        '<div class="settings-caption">Choose which SecureVault notifications you want to receive.</div>',
        unsafe_allow_html=True
    )

    db = next(get_db())
    try:
        preferences = get_user_preferences(db, user["id"])
        if not preferences:
            st.error("Notification preferences could not be loaded.")
            return

        with st.form("notification_preferences_form"):
            shared_received = st.toggle(
                "Password shared with me",
                value=bool(preferences.password_shared_with_me)
            )
            shared_sent = st.toggle(
                "Password shared by me",
                value=bool(preferences.password_shared_by_me)
            )
            health_alerts = st.toggle(
                "Password health alerts",
                value=bool(preferences.password_health_alerts)
            )
            security_alerts = st.toggle(
                "Security alerts",
                value=bool(preferences.security_alerts)
            )
            save_notifications = st.form_submit_button(
                "Save Notification Preferences", use_container_width=True
            )

        if save_notifications:
            success = update_user_preferences(
                db=db,
                user_id=user["id"],
                password_shared_with_me=shared_received,
                password_shared_by_me=shared_sent,
                password_health_alerts=health_alerts,
                security_alerts=security_alerts
            )
            if success:
                st.success("Notification preferences saved successfully.")
                st.rerun()
            else:
                st.error("Could not save notification preferences.")

    except Exception as exc:
        db.rollback()
        st.error(f"Notification settings error: {exc}")
    finally:
        db.close()


# ============================================================
# SECURITY OVERVIEW
# ============================================================

def _security_overview(user):
    st.markdown(
        '<div class="settings-h2">🛡️ Security Overview</div>'
        '<div class="settings-caption">Comprehensive security telemetry and posture assessment.</div>',
        unsafe_allow_html=True
    )

    db_user = _fresh_user(user["id"])
    if not db_user:
        st.error("User account could not be loaded.")
        return

    mfa_active = bool(db_user.mfa_enabled)
    email_ver = bool(db_user.email_verified)
    failed_attempts = int(db_user.failed_login_attempts or 0)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_html(f"""
        <div class="metric-card">
            <div class="metric-header">
                <span class="metric-label">MFA Authentication</span>
                <span class="metric-icon">🛡️</span>
            </div>
            <div style="margin-top:6px;">
                <span class="status-pill {'pill-secure' if mfa_active else 'pill-warning'}">
                    <span class="pill-dot {'dot-green' if mfa_active else 'dot-amber'}"></span>
                    {'Active (Email OTP)' if mfa_active else 'Disabled'}
                </span>
            </div>
        </div>
        """)
    with c2:
        render_html(f"""
        <div class="metric-card">
            <div class="metric-header">
                <span class="metric-label">Email Verification</span>
                <span class="metric-icon">✉️</span>
            </div>
            <div style="margin-top:6px;">
                <span class="status-pill {'pill-secure' if email_ver else 'pill-warning'}">
                    <span class="pill-dot {'dot-green' if email_ver else 'dot-amber'}"></span>
                    {'Verified' if email_ver else 'Unverified'}
                </span>
            </div>
        </div>
        """)
    with c3:
        render_html(f"""
        <div class="metric-card">
            <div class="metric-header">
                <span class="metric-label">Vault Status</span>
                <span class="metric-icon">🔐</span>
            </div>
            <div style="margin-top:6px;">
                <span class="status-pill pill-secure">
                    <span class="pill-dot dot-green"></span> {str(db_user.status)}
                </span>
            </div>
        </div>
        """)
    with c4:
        render_html(f"""
        <div class="metric-card">
            <div class="metric-header">
                <span class="metric-label">Failed Logins</span>
                <span class="metric-icon">⚠️</span>
            </div>
            <div style="margin-top:6px;">
                <span class="status-pill {'pill-secure' if failed_attempts == 0 else 'pill-danger'}">
                    {failed_attempts} Attempts
                </span>
            </div>
        </div>
        """)

    if db_user.created_at:
        render_html(f"""
        <div style="margin-top:14px;background:rgba(13,22,42,0.6);border:1px solid rgba(56,189,248,0.14);border-radius:10px;padding:12px 16px;font-size:12px;color:#94a3b8;">
            🕒 <b>Account Initialized:</b> {db_user.created_at.strftime("%d %B %Y, %I:%M %p")} &nbsp; • &nbsp; <b>Cryptographic Scope:</b> Zero-Knowledge AES-256-GCM
        </div>
        """)


# ============================================================
# MAIN
# ============================================================

def show(user):
    load_css()

    st.markdown(
        '<div class="settings-title">⚙️ Settings</div>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<div class="settings-subtitle">'
        'Manage your SecureVault profile, password, email OTP security and preferences.'
        '</div>',
        unsafe_allow_html=True
    )

    if not user or not user.get("id"):
        st.error("Please login again.")
        return

    tab1, tab2, tab3, tab4 = st.tabs([
        "👤 Profile",
        "🔐 Security",
        "🔔 Notifications",
        "🛡️ Security Overview"
    ])

    with tab1:
        _profile_section(user)

    with tab2:
        _password_section(user)
        st.divider()
        _mfa_section(user)

    with tab3:
        _notifications_section(user)

    with tab4:
        _security_overview(user)

    st.divider()
    if st.button("🚪 Logout", type="secondary", use_container_width=True):
        try:
            create_audit_log(
                user_id=user["id"],
                action="LOGOUT",
                target=f"Signed out from {user.get('email','account')}",
                target_type="USER",
                target_id=user["id"],
                organization_id=user.get("organization_id"),
            )
        except Exception:
            pass

        st.session_state.clear()
        st.rerun()