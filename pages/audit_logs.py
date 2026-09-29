# ============================================================
# SECUREVAULT - MODERN CYBERSECURITY AUDIT LOGS
# ============================================================

import streamlit as st
import datetime
from sqlalchemy import or_, and_
from html import escape
from database.connection import SessionLocal
from database import models
from utils.theme import inject_cyber_theme, render_html


def load_css():
    inject_cyber_theme()
    render_html("""
    <style>
        .audit-timeline-card {
            background: rgba(15, 23, 42, 0.72);
            border: 1px solid rgba(56, 189, 248, 0.16);
            border-radius: 12px;
            padding: 14px 18px;
            margin-bottom: 10px;
            transition: all 0.2s ease;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25);
        }
        .audit-timeline-card:hover {
            border-color: rgba(56, 189, 248, 0.35);
            background: rgba(22, 34, 60, 0.85);
            transform: translateX(3px);
        }
        .audit-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            font-size: 12px;
            font-weight: 700;
            color: #f8fafc;
            background: rgba(14, 165, 233, 0.12);
            border: 1px solid rgba(56, 189, 248, 0.25);
            border-radius: 8px;
            padding: 4px 10px;
        }
        .audit-meta-item {
            font-size: 11.5px;
            color: #94a3b8;
            display: flex;
            align-items: center;
            gap: 4px;
        }
        .audit-meta-item span {
            color: #38bdf8;
        }
    </style>
    """)


def enum_value(value):
    if value is None:
        return ""
    if hasattr(value, "value"):
        value = value.value
    value = str(value).strip().upper()
    return value.split(".")[-1] if "." in value else value


def get_user_id(user):
    if user is None:
        return None
    return user.get("id") if isinstance(user, dict) else getattr(user, "id", None)


def safe_text(value, default="-"):
    if value is None:
        return default
    value = str(value).strip()
    return value if value else default


def format_action(action):
    return safe_text(action, "Unknown").replace("_", " ").replace("-", " ").title()


def get_action_icon(action_str):
    act = str(action_str).upper()
    if "LOGIN" in act:
        return "🔐"
    elif "VIEW" in act:
        return "👁️"
    elif "UPDATE" in act or "EDIT" in act or "CHANGE" in act:
        return "✏️"
    elif "DELETE" in act or "REMOVE" in act:
        return "🗑️"
    elif "SHARE" in act:
        return "🔗"
    elif "TEAM" in act or "MEMBER" in act:
        return "👥"
    elif "SETTING" in act or "MFA" in act or "PREFERENCE" in act:
        return "⚙️"
    elif "CREATE" in act:
        return "➕"
    return "📋"


def show(user):
    load_css()

    user_id = get_user_id(user)
    if user_id is None:
        st.error("Your login session is invalid.")
        return

    db = SessionLocal()
    try:
        current_user = db.query(models.User).filter(models.User.id == user_id).first()
        if current_user is None:
            st.error("User account was not found.")
            return

        account_type = enum_value(current_user.account_type)
        role = enum_value(current_user.role)
        organization_id = current_user.organization_id
        organization_admin = (
            account_type == "ORGANIZATION"
            and role in {"ADMIN", "OWNER"}
            and organization_id is not None
        )

        render_html("""
        <div style="margin-bottom: 20px;">
            <div style="display:flex;align-items:center;gap:10px;">
                <h1 style="font-size: 26px; font-weight: 800; color: #f8fafc; margin: 0;">📋 Security Audit Logs</h1>
                <div class="status-pill pill-secure">
                    <span class="pill-dot dot-green"></span> Tamper-Resistant Stream
                </div>
            </div>
            <p style="font-size: 13.5px; color: #94a3b8; margin-top: 4px;">Track authentication, credential accesses, and vault modifications.</p>
        </div>
        """)

        scope_text = "Organization Events" if organization_admin else "Your Events"

        # LOAD LOGS
        if organization_admin:
            logs = (
                db.query(models.AuditLog)
                .outerjoin(models.User, models.AuditLog.user_id == models.User.id)
                .filter(or_(
                    models.AuditLog.organization_id == organization_id,
                    and_(
                        models.AuditLog.organization_id.is_(None),
                        models.User.organization_id == organization_id,
                    ),
                ))
                .order_by(models.AuditLog.timestamp.desc())
                .limit(1000)
                .all()
            )
        else:
            logs = (
                db.query(models.AuditLog)
                .filter(models.AuditLog.user_id == user_id)
                .order_by(models.AuditLog.timestamp.desc())
                .limit(500)
                .all()
            )

        actions = sorted({str(log.action) for log in logs if log.action})

        organization_users = {}
        if organization_admin:
            for log in logs:
                if log.user is None:
                    continue
                if log.user.organization_id not in (None, organization_id):
                    continue
                organization_users[log.user.id] = (
                    log.user.name or log.user.email or f"User {log.user.id}"
                )

        # FILTERS CARD
        with st.container(border=True):
            st.markdown("<div style='font-size:12px;font-weight:700;color:#38bdf8;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:8px;'>🔍 Event Filters</div>", unsafe_allow_html=True)
            c1, c2, c3 = st.columns([1.25, 1.25, 1.8])

            with c1:
                selected_action = st.selectbox(
                    "Action", ["All Actions"] + actions, key="audit_action_filter"
                )

            with c2:
                if organization_admin:
                    selected_user = st.selectbox(
                        "User",
                        ["All Users"] + sorted(organization_users.values()),
                        key="audit_user_filter",
                    )
                else:
                    selected_user = st.text_input(
                        "User",
                        value=(current_user.email or ""),
                        disabled=True,
                        key="audit_current_user",
                    )

            with c3:
                selected_dates = st.date_input(
                    "Date Range",
                    value=(
                        datetime.date.today() - datetime.timedelta(days=365),
                        datetime.date.today(),
                    ),
                    key="audit_date_filter",
                )

        start_date = end_date = None
        if isinstance(selected_dates, (tuple, list)):
            if len(selected_dates) >= 1:
                start_date = selected_dates[0]
            if len(selected_dates) >= 2:
                end_date = selected_dates[1]
        elif selected_dates:
            start_date = end_date = selected_dates

        # FILTER LOGS
        filtered_logs = []
        for log in logs:
            if organization_admin:
                if log.organization_id is not None:
                    if log.organization_id != organization_id:
                        continue
                else:
                    if log.user is None or log.user.organization_id != organization_id:
                        continue
            else:
                if log.user_id != user_id:
                    continue

            if selected_action != "All Actions" and str(log.action) != selected_action:
                continue

            if organization_admin and selected_user != "All Users":
                if log.user is None:
                    continue
                log_name = log.user.name or log.user.email or f"User {log.user.id}"
                if log_name != selected_user:
                    continue

            if log.timestamp:
                log_date = log.timestamp.date()
                if start_date is not None and log_date < start_date:
                    continue
                if end_date is not None and log_date > end_date:
                    continue

            filtered_logs.append(log)

        st.caption(
            f"Showing {len(filtered_logs)} of {len(logs)} events · Scope: {scope_text.upper()}"
        )

        st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

        if not filtered_logs:
            st.info("No audit events match the selected filters.")
            return

        # TIMELINE DISPLAY
        for log in filtered_logs:
            if log.user:
                username = log.user.name or log.user.email or f"User {log.user.id}"
                email = log.user.email or "-"
            else:
                username = f"User {log.user_id}" if log.user_id else "-"
                email = "-"

            action = format_action(log.action)
            action_icon = get_action_icon(log.action)
            timestamp = log.timestamp.strftime("%d %b %Y, %I:%M %p") if log.timestamp else "-"
            ip_address = safe_text(getattr(log, "ip_address", None))
            device = safe_text(getattr(log, "device", None))
            browser = safe_text(getattr(log, "browser", None))
            target_type = safe_text(getattr(log, "target_type", None))
            target_desc = safe_text(getattr(log, "target", None), default="")

            org_name = "-"
            if log.user and getattr(log.user, "organization", None):
                org_name = log.user.organization.name or "-"

            render_html(f"""
            <div class="audit-timeline-card">
                <div style="display:flex;align-items:flex-start;justify-content:space-between;flex-wrap:wrap;gap:8px;margin-bottom:8px;">
                    <div style="display:flex;align-items:center;gap:10px;">
                        <span class="audit-badge">{action_icon} {escape(action)}</span>
                        <span style="font-size:13.5px;font-weight:600;color:#f8fafc;">{escape(target_desc or target_type)}</span>
                    </div>
                    <div class="audit-meta-item">
                        <span>🕒</span> <span>{timestamp}</span>
                    </div>
                </div>
                <div style="display:flex;align-items:center;gap:16px;flex-wrap:wrap;font-size:12px;color:#94a3b8;padding-top:6px;border-top:1px solid rgba(56,189,248,0.08);">
                    <div class="audit-meta-item"><span>👤</span> <b style="color:#e2e8f0;">{escape(username)}</b> ({escape(email)})</div>
                    {f'<div class="audit-meta-item"><span>🏢 Org:</span> <span style="color:#cbd5e1;">{escape(org_name)}</span></div>' if org_name != '-' else ''}
                    <div class="audit-meta-item"><span>🌐 IP:</span> <span style="font-family:'JetBrains Mono',monospace;color:#38bdf8;">{escape(ip_address)}</span></div>
                    <div class="audit-meta-item"><span>💻 Device:</span> {escape(device)}</div>
                    <div class="audit-meta-item"><span>🌐 Browser:</span> {escape(browser)}</div>
                </div>
            </div>
            """)

    except Exception as exc:
        st.error("Unable to load audit logs.")
        st.exception(exc)
    finally:
        db.close()