import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from dotenv import load_dotenv

from database import models

load_dotenv()


# ============================================================
# SMTP CONFIGURATION
# ============================================================

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM_EMAIL = os.getenv(
    "SMTP_FROM_EMAIL",
    SMTP_USERNAME
)


# ============================================================
# GET / CREATE USER PREFERENCES
# ============================================================

def get_user_preferences(db, user_id):
    """
    Get notification preferences for a user.

    If the user does not have a preference record yet,
    create one with all notifications enabled.
    """

    preferences = (
        db.query(models.UserPreference)
        .filter(
            models.UserPreference.user_id == user_id
        )
        .first()
    )

    if preferences:
        return preferences

    preferences = models.UserPreference(
        user_id=user_id,
        password_shared_with_me=True,
        password_shared_by_me=True,
        password_health_alerts=True,
        security_alerts=True
    )

    db.add(preferences)
    db.commit()
    db.refresh(preferences)

    return preferences


# ============================================================
# UPDATE USER PREFERENCES
# ============================================================

def update_user_preferences(
    db,
    user_id,
    password_shared_with_me=None,
    password_shared_by_me=None,
    password_health_alerts=None,
    security_alerts=None
):
    """
    Update notification preferences permanently
    in the MySQL database.
    """

    try:

        preferences = (
            db.query(models.UserPreference)
            .filter(
                models.UserPreference.user_id == user_id
            )
            .first()
        )

        # ----------------------------------------------------
        # Create preferences if missing
        # ----------------------------------------------------

        if not preferences:

            preferences = models.UserPreference(
                user_id=user_id
            )

            db.add(preferences)
            db.flush()

        # ----------------------------------------------------
        # Update values
        # ----------------------------------------------------

        if password_shared_with_me is not None:

            preferences.password_shared_with_me = bool(
                password_shared_with_me
            )

        if password_shared_by_me is not None:

            preferences.password_shared_by_me = bool(
                password_shared_by_me
            )

        if password_health_alerts is not None:

            preferences.password_health_alerts = bool(
                password_health_alerts
            )

        if security_alerts is not None:

            preferences.security_alerts = bool(
                security_alerts
            )

        db.commit()
        db.refresh(preferences)

        return True

    except Exception:

        db.rollback()

        return False


# ============================================================
# CHECK SINGLE NOTIFICATION PREFERENCE
# ============================================================

def is_notification_enabled(
    db,
    user_id,
    notification_type
):
    """
    Check whether a specific notification is enabled.
    """

    preferences = get_user_preferences(
        db,
        user_id
    )

    mapping = {
        "password_shared_with_me":
            preferences.password_shared_with_me,

        "password_shared_by_me":
            preferences.password_shared_by_me,

        "password_health_alerts":
            preferences.password_health_alerts,

        "security_alerts":
            preferences.security_alerts,
    }

    return bool(
        mapping.get(
            notification_type,
            False
        )
    )


# ============================================================
# SEND EMAIL
# ============================================================

def send_notification_email(
    recipient_email,
    subject,
    message
):
    """
    Send an email notification through SMTP.

    Returns:
        True  -> email sent
        False -> email failed
    """

    if not recipient_email:

        return False

    if not SMTP_HOST or not SMTP_USERNAME or not SMTP_PASSWORD:

        print(
            "Notification email skipped: "
            "SMTP configuration is missing."
        )

        return False

    try:

        email = MIMEMultipart()

        email["From"] = SMTP_FROM_EMAIL
        email["To"] = recipient_email
        email["Subject"] = subject

        email.attach(
            MIMEText(
                message,
                "plain",
                "utf-8"
            )
        )

        server = smtplib.SMTP(
            SMTP_HOST,
            SMTP_PORT,
            timeout=20
        )

        server.starttls()

        server.login(
            SMTP_USERNAME,
            SMTP_PASSWORD
        )

        server.sendmail(
            SMTP_FROM_EMAIL,
            recipient_email,
            email.as_string()
        )

        server.quit()

        return True

    except Exception as exc:

        print(
            f"Notification email error: {exc}"
        )

        return False


# ============================================================
# GET USER EMAIL
# ============================================================

def _get_user_email(db, user_id):

    user = (
        db.query(models.User)
        .filter(
            models.User.id == user_id
        )
        .first()
    )

    if not user:
        return None

    return user.email


# ============================================================
# PASSWORD SHARED WITH ME
# ============================================================

def notify_password_shared_with_me(
    db,
    receiver_id,
    sender_name,
    password_title
):
    """
    Notify receiver that a password was shared with them.
    """

    if not is_notification_enabled(
        db,
        receiver_id,
        "password_shared_with_me"
    ):

        return False

    email = _get_user_email(
        db,
        receiver_id
    )

    if not email:
        return False

    subject = (
        "SecureVault - Password Shared With You"
    )

    message = f"""
Hello,

A password has been shared with you in SecureVault.

Shared by:
{sender_name}

Password:
{password_title}

Please log in to SecureVault to view the shared password.

SecureVault Manager
"""

    return send_notification_email(
        email,
        subject,
        message
    )


# ============================================================
# PASSWORD SHARED BY ME
# ============================================================

def notify_password_shared_by_me(
    db,
    sender_id,
    receiver_name,
    password_title
):
    """
    Notify sender that their password was shared.
    """

    if not is_notification_enabled(
        db,
        sender_id,
        "password_shared_by_me"
    ):

        return False

    email = _get_user_email(
        db,
        sender_id
    )

    if not email:
        return False

    subject = (
        "SecureVault - Password Shared Successfully"
    )

    message = f"""
Hello,

Your password was successfully shared from SecureVault.

Shared with:
{receiver_name}

Password:
{password_title}

SecureVault Manager
"""

    return send_notification_email(
        email,
        subject,
        message
    )


# ============================================================
# SECURITY ALERT
# ============================================================

def notify_security_alert(
    db,
    user_id,
    message
):
    """
    Send security-related notification.
    """

    if not is_notification_enabled(
        db,
        user_id,
        "security_alerts"
    ):

        return False

    email = _get_user_email(
        db,
        user_id
    )

    if not email:
        return False

    subject = (
        "SecureVault - Security Alert"
    )

    body = f"""
Hello,

A security-related change was made to your SecureVault account.

Details:
{message}

If you did not make this change, please
log in and secure your account immediately.

SecureVault Manager
"""

    return send_notification_email(
        email,
        subject,
        body
    )


# ============================================================
# PASSWORD HEALTH ALERT
# ============================================================

def notify_password_health_alert(
    db,
    user_id,
    message
):
    """
    Send password health notification.
    """

    if not is_notification_enabled(
        db,
        user_id,
        "password_health_alerts"
    ):

        return False

    email = _get_user_email(
        db,
        user_id
    )

    if not email:
        return False

    subject = (
        "SecureVault - Password Health Alert"
    )

    body = f"""
Hello,

SecureVault has detected a password health issue.

Details:
{message}

Please open SecureVault Password Health
to review and update your passwords.

SecureVault Manager
"""

    return send_notification_email(
        email,
        subject,
        body
    )


# ============================================================
# TEAM PASSWORD SHARED
# ============================================================

def notify_team_password_shared(
    db,
    user_id,
    team_name,
    sender_name,
    password_title
):
    """
    Notify a user when a password is shared
    with one of their teams.
    """

    if not is_notification_enabled(
        db,
        user_id,
        "password_shared_with_me"
    ):

        return False

    email = _get_user_email(
        db,
        user_id
    )

    if not email:
        return False

    subject = (
        "SecureVault - Team Password Shared"
    )

    body = f"""
Hello,

A password has been shared with your SecureVault team.

Team:
{team_name}

Shared by:
{sender_name}

Password:
{password_title}

Please log in to SecureVault to access the password
according to your assigned permission.

SecureVault Manager
"""

    return send_notification_email(
        email,
        subject,
        body
    )