# ============================================================
# utils/audit_logger.py
# ============================================================

from datetime import datetime

from database.connection import get_db
from database import models


# ============================================================
# CLIENT INFORMATION
# ============================================================

def get_client_info():

    info = {
        "ip_address": "127.0.0.1",
        "browser": "Unknown",
        "device": "Web",
    }

    try:

        import streamlit as st

        headers = st.context.headers

        forwarded = headers.get(
            "X-Forwarded-For",
            ""
        )

        if forwarded:

            info["ip_address"] = (
                forwarded
                .split(",")[0]
                .strip()
            )

        else:

            info["ip_address"] = (
                headers.get("X-Real-Ip")
                or headers.get("Remote-Addr")
                or headers.get("Cf-Connecting-Ip")
                or "127.0.0.1"
            )

        ua = headers.get(
            "User-Agent",
            ""
        ).lower()

        # ----------------------------------------------------
        # BROWSER
        # ----------------------------------------------------

        if "edg" in ua:

            info["browser"] = "Edge"

        elif "chrome" in ua and "chromium" not in ua:

            info["browser"] = "Chrome"

        elif "firefox" in ua:

            info["browser"] = "Firefox"

        elif (
            "safari" in ua
            and "chrome" not in ua
        ):

            info["browser"] = "Safari"

        elif (
            "opera" in ua
            or "opr" in ua
        ):

            info["browser"] = "Opera"

        # ----------------------------------------------------
        # DEVICE
        # ----------------------------------------------------

        if any(
            x in ua
            for x in (
                "mobile",
                "android",
                "iphone",
            )
        ):

            info["device"] = "Mobile"

        elif any(
            x in ua
            for x in (
                "tablet",
                "ipad",
            )
        ):

            info["device"] = "Tablet"

        elif ua:

            info["device"] = "Desktop"

    except Exception:
        pass

    return info


# ============================================================
# ENUM VALUE HELPER
# ============================================================

def _enum_value(value):
    """
    Normalise SQLAlchemy Enum values.

    Examples:
        Role.ADMIN           -> ADMIN
        UserRole.OWNER       -> OWNER
        AccountType.PERSONAL -> PERSONAL
        'ADMIN'              -> ADMIN
        None                 -> ''
    """

    if value is None:
        return ""

    if hasattr(value, "value"):
        value = value.value

    value = str(value).strip().upper()

    if "." in value:
        value = value.split(".")[-1]

    return value


# ============================================================
# CREATE AUDIT LOG
# ============================================================

def create_audit_log(
    user_id,
    action,
    target=None,
    target_type=None,
    target_id=None,
    details=None,
    organization_id=None,
):
    """
    Creates an audit log.

    IMPORTANT:
    - organization_id is always resolved from the authenticated
      user's database record (never trusted from the caller).
    - Plaintext passwords are NEVER stored in the audit log.
    """

    if user_id is None:
        return False

    db = next(get_db())

    try:

        # ----------------------------------------------------
        # LOAD ACTOR
        # ----------------------------------------------------

        actor = (
            db.query(models.User)
            .filter(
                models.User.id == user_id
            )
            .first()
        )

        if actor is None:

            print(
                f"[AUDIT] User not found: {user_id}"
            )

            return False

        # ----------------------------------------------------
        # ORGANIZATION - ALWAYS FROM DB
        # ----------------------------------------------------

        actor_organization_id = getattr(
            actor,
            "organization_id",
            None
        )

        if actor_organization_id is not None:

            organization_id = actor_organization_id

        else:

            organization_id = None

        # ----------------------------------------------------
        # DETAILS
        # ----------------------------------------------------

        if details is None and target:

            details = (
                f"{str(action).replace('_', ' ').title()}: "
                f"{target}"
            )

        # ----------------------------------------------------
        # NEVER STORE PASSWORD / SECRETS
        # ----------------------------------------------------

        if details:

            sensitive_words = (
                "password=",
                "password:",
                "plaintext",
                "decrypted_password",
                "secret=",
                "otp=",
            )

            lower_details = str(details).lower()

            if any(
                word in lower_details
                for word in sensitive_words
            ):

                details = "Password security event"

        # ----------------------------------------------------
        # CLIENT INFO
        # ----------------------------------------------------

        info = get_client_info()

        # ----------------------------------------------------
        # CREATE LOG
        # ----------------------------------------------------

        log = models.AuditLog(
            user_id=user_id,
            organization_id=organization_id,
            action=str(action),
            target_type=target_type,
            target_id=target_id,
            timestamp=datetime.utcnow(),
            ip_address=info["ip_address"],
            browser=info["browser"],
            device=info["device"],
            details=details,
        )

        db.add(log)
        db.commit()

        print(
            f"[AUDIT] {action} | "
            f"user={user_id} | "
            f"org={organization_id} | "
            f"target={target}"
        )

        return True

    except Exception as exc:

        db.rollback()

        print(f"[AUDIT ERROR] {exc}")

        return False

    finally:

        db.close()