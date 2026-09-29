import streamlit as st
from database import models


def get_client_info():
    """Best-effort real IP / browser / device from Streamlit headers."""
    ip = "127.0.0.1"
    browser = "Unknown"
    device = "Web"

    try:
        headers = st.context.headers

        forwarded = headers.get("X-Forwarded-For", "")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        else:
            ip = (
                headers.get("X-Real-Ip")
                or headers.get("Remote-Addr")
                or headers.get("Cf-Connecting-Ip")
                or "127.0.0.1"
            )

        ua = headers.get("User-Agent", "").lower()
        if "edg" in ua:
            browser = "Edge"
        elif "chrome" in ua and "chromium" not in ua:
            browser = "Chrome"
        elif "firefox" in ua:
            browser = "Firefox"
        elif "safari" in ua and "chrome" not in ua:
            browser = "Safari"
        elif "opera" in ua or "opr" in ua:
            browser = "Opera"

        if any(x in ua for x in ("mobile", "android", "iphone")):
            device = "Mobile"
        elif any(x in ua for x in ("tablet", "ipad")):
            device = "Tablet"
        else:
            device = "Desktop"

    except Exception:
        pass

    return {"ip_address": ip, "browser": browser, "device": device}


def log_action(
    db,
    user_id=None,
    organization_id=None,
    action="",
    target_type=None,
    target_id=None,
    details=None,
):

    try:

        # ----------------------------------------------------
        # Automatically get organization from user
        # ----------------------------------------------------

        if (
            organization_id is None
            and user_id is not None
        ):

            actor = (
                db.query(models.User)
                .filter(
                    models.User.id == user_id
                )
                .first()
            )

            if actor:

                organization_id = (
                    actor.organization_id
                )

        info = get_client_info()

        log = models.AuditLog(

            user_id=user_id,

            organization_id=organization_id,

            action=action,

            target_type=target_type,

            target_id=target_id,

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
            f"org={organization_id}"
        )

        return True

    except Exception as e:

        db.rollback()

        print(
            f"[AUDIT ERROR] {e}"
        )

        return False