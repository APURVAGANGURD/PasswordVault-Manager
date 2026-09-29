import streamlit as st
import datetime
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pages.login import show as show_login
from pages.register import show as show_register
from pages.forgot import show as show_forgot
from pages.dashboard import show as show_dashboard
from pages.my_vault import show as show_my_vault
from pages.settings import show as show_settings
from pages.password_health import show as show_password_health


SESSION_TIMEOUT_MINUTES = 30


def _log_event(user, action, target):
    """Best-effort audit logging — never crashes the router."""
    if not user or not user.get("id"):
        return
    try:
        from utils.audit_logger import create_audit_log
        create_audit_log(
            user_id=user["id"],
            action=action,
            target=target,
            target_type="USER",
            target_id=user["id"],
            organization_id=user.get("organization_id"),
        )
    except Exception as exc:
        print(f"[ROUTER AUDIT SKIP] {exc}")


from utils.theme import inject_cyber_theme, render_3d_shield, render_html

def render():
    # Inject Centralized Theme
    inject_cyber_theme()

    # ========================================================
    # SESSION EXPIRED PAGE
    # ========================================================
    if st.session_state.get("session_expired", False):
        from pages.session_expired import show as show_session_expired
        show_session_expired()
        return

    # ========================================================
    # INIT
    # ========================================================
    if "page" not in st.session_state:
        st.session_state["page"] = "login"

    user = st.session_state.get("user")

    # ========================================================
    # SESSION TIMEOUT CHECK
    # ========================================================
    if user:
        login_time = st.session_state.get("login_time")
        if login_time:
            elapsed = (
                datetime.datetime.now() - login_time
            ).total_seconds() / 60

            if elapsed > SESSION_TIMEOUT_MINUTES:
                # Log BEFORE clearing session
                _log_event(
                    user,
                    "SESSION_EXPIRED",
                    f"Session expired for {user.get('email', 'account')}",
                )

                st.session_state.clear()
                st.session_state["session_expired"] = True
                st.rerun()

    # ========================================================
    # MFA ROUTING
    # ========================================================
    if st.session_state.get("mfa_pending", False):
        from pages.mfa import show as show_mfa
        show_mfa()
        return

    # ========================================================
    # AUTH ROUTING
    # ========================================================
    if not user:
        page = st.session_state.get("page", "login")
        if page == "register":
            show_register()
        elif page == "forgot":
            show_forgot()
        else:
            show_login()
        return

    # ========================================================
    # SIDEBAR
    # ========================================================
    with st.sidebar:
        render_html("""
        <style>
            div[data-testid="stSidebar"] {
                background: #070c18 !important;
                border-right: 1px solid rgba(56, 189, 248, 0.14) !important;
            }
            div[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
                gap: 0.35rem !important;
            }
            div[data-testid="stSidebar"] button {
                background: rgba(13, 22, 42, 0.65) !important;
                color: #cbd5e1 !important;
                border: 1px solid rgba(56, 189, 248, 0.12) !important;
                border-radius: 9px !important;
                text-align: left !important;
                font-size: 13.5px !important;
                font-weight: 500 !important;
                padding: 9px 14px !important;
                min-height: 42px !important;
                justify-content: flex-start !important;
                transition: all 0.22s cubic-bezier(0.16, 1, 0.3, 1) !important;
            }
            div[data-testid="stSidebar"] button:hover {
                background: rgba(26, 38, 64, 0.9) !important;
                color: #38bdf8 !important;
                border-color: rgba(56, 189, 248, 0.4) !important;
                box-shadow: 0 4px 16px rgba(6, 182, 212, 0.22) !important;
                transform: translateX(3px);
            }
            div[data-testid="stSidebar"] button[kind="primary"] {
                background: linear-gradient(135deg, rgba(14, 165, 233, 0.22) 0%, rgba(2, 132, 199, 0.35) 100%) !important;
                color: #38bdf8 !important;
                border: 1px solid #38bdf8 !important;
                border-left: 3.5px solid #06b6d4 !important;
                box-shadow: 0 0 18px rgba(56, 189, 248, 0.25), inset 0 0 10px rgba(56, 189, 248, 0.08) !important;
                font-weight: 700 !important;
            }
        </style>
        """)

        # Brand Header with 3D Shield
        shield_html = render_3d_shield(size=36)
        render_html(f"""
        <div style="display:flex;align-items:center;gap:12px;padding:8px 0 16px 0;">
            {shield_html}
            <div>
                <div style="font-size:18px;font-weight:800;color:#f8fafc;letter-spacing:-0.5px;line-height:1.2;">SecureVault</div>
                <div style="font-size:11px;font-weight:700;color:#06b6d4;letter-spacing:1px;text-transform:uppercase;">Cyber Vault Manager</div>
            </div>
        </div>
        """)

        # User Profile & Badges Card
        account_type = str(user.get("account_type", "PERSONAL")).upper()
        role = str(user.get("role", "USER")).upper()
        user_name = user.get("name", "User")
        user_email = user.get("email", "")

        is_org = account_type == "ORGANIZATION"
        acc_badge_class = "pill-cyber" if not is_org else "pill-warning"

        render_html(f"""
        <div style="background:rgba(15,23,42,0.7);border:1px solid rgba(56,189,248,0.15);border-radius:12px;padding:12px 14px;margin-bottom:12px;">
            <div style="font-size:13px;font-weight:700;color:#f8fafc;display:flex;align-items:center;gap:6px;">
                <span>👤</span> <span style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{user_name}</span>
            </div>
            <div style="font-size:11px;color:#94a3b8;margin-top:2px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">
                {user_email}
            </div>
            <div style="display:flex;gap:6px;margin-top:8px;flex-wrap:wrap;">
                <span class="status-pill {acc_badge_class}" style="font-size:10px;padding:2px 8px;">
                    {account_type}
                </span>
                <span class="status-pill pill-secure" style="font-size:10px;padding:2px 8px;">
                    {role}
                </span>
            </div>
        </div>
        """)

        if not bool(user.get("mfa_enabled", False)):
            st.markdown(
                '<div style="background:rgba(245,158,11,0.12);border:1px solid rgba(245,158,11,0.3);'
                'border-radius:8px;padding:8px 10px;font-size:11px;color:#fbbf24;margin-bottom:12px;">'
                '⚠️ MFA Disabled. Enable in Settings.</div>',
                unsafe_allow_html=True,
            )

        if "nav" not in st.session_state:
            st.session_state["nav"] = "Dashboard"

        current_nav = st.session_state["nav"]

        # Navigation Section
        st.markdown(
            '<div style="color:#64748b;font-size:10px;font-weight:700;'
            'letter-spacing:1px;text-transform:uppercase;padding:4px 4px 6px 4px;">'
            'Navigation</div>',
            unsafe_allow_html=True,
        )

        if st.button("🏠  Dashboard", key="nav_dashboard", type="primary" if current_nav == "Dashboard" else "secondary", use_container_width=True):
            st.session_state["nav"] = "Dashboard"
            st.rerun()

        if st.button("🔐  Passwords", key="nav_passwords", type="primary" if current_nav in ["My Vault", "Passwords"] else "secondary", use_container_width=True):
            st.session_state["nav"] = "My Vault"
            st.rerun()

        if st.button("🗂️  Vaults", key="nav_vaults", type="primary" if current_nav == "Vaults" else "secondary", use_container_width=True):
            st.session_state["nav"] = "My Vault"
            st.rerun()

        # -------- Organization navigation --------
        if is_org:
            st.markdown(
                '<div style="color:#64748b;font-size:10px;font-weight:700;'
                'letter-spacing:1px;text-transform:uppercase;padding:10px 4px 6px 4px;">'
                'Organization</div>',
                unsafe_allow_html=True,
            )
            if st.button("👥  Teams", key="nav_teams", type="primary" if current_nav == "Teams" else "secondary", use_container_width=True):
                st.session_state["nav"] = "Teams"
                st.rerun()

            if st.button("🔗  Shared Passwords", key="nav_shared", type="primary" if current_nav == "Shared Passwords" else "secondary", use_container_width=True):
                st.session_state["nav"] = "Shared Passwords"
                st.rerun()

        st.markdown(
            '<div style="color:#64748b;font-size:10px;font-weight:700;'
            'letter-spacing:1px;text-transform:uppercase;padding:10px 4px 6px 4px;">'
            'Security & System</div>',
            unsafe_allow_html=True,
        )

        if st.button("❤️  Password Health", key="nav_health", type="primary" if current_nav == "Password Health" else "secondary", use_container_width=True):
            st.session_state["nav"] = "Password Health"
            st.rerun()

        if st.button("📋  Audit Logs", key="nav_audit", type="primary" if current_nav == "Audit Logs" else "secondary", use_container_width=True):
            st.session_state["nav"] = "Audit Logs"
            st.rerun()

        if st.button("⚙️  Settings", key="nav_settings", type="primary" if current_nav == "Settings" else "secondary", use_container_width=True):
            st.session_state["nav"] = "Settings"
            st.rerun()

        st.write("")
        # -------- Logout --------
        if st.button("🚪  Logout", key="nav_logout", use_container_width=True):
            _log_event(
                user,
                "LOGOUT",
                f"Signed out from {user.get('email', 'account')}",
            )
            st.session_state.clear()
            st.session_state["page"] = "login"
            st.rerun()

    # ========================================================
    # MAIN ROUTES
    # ========================================================
    nav = st.session_state.get("nav", "Dashboard")

    if nav == "Dashboard":
        show_dashboard(user)

    elif nav in ["My Vault", "Passwords", "Vaults"]:
        show_my_vault(user)

    elif nav == "Password Health":
        show_password_health(user)

    elif nav == "Audit Logs":
        from pages.audit_logs import show as show_audit_logs
        show_audit_logs(user)

    elif nav == "Settings":
        show_settings(user)

    elif nav == "Add Password":
        from pages.add_password import show as show_add_password
        show_add_password(user)

    elif nav == "View Password":
        from pages.view_password import show as show_view_password
        show_view_password(user, st.session_state.get("current_view_id"))

    elif nav == "Teams":
        from pages.teams import show as show_teams
        show_teams(user)

    elif nav == "Shared Passwords":
        from pages.shared_passwords import show as show_shared
        show_shared(user)