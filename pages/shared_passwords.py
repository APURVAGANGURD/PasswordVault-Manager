# ============================================================
# pages/shared_passwords.py
# SecureVault Manager - Modern Shared Passwords UI
# ============================================================

import streamlit as st
import sys, os
from html import escape

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import SessionLocal
from database import models
from modules.team_backend import (
    get_user_organization,
    get_user_teams,
    find_user_by_email,
    share_password_with_user,
    share_password_with_team,
    get_shared_passwords_for_user,
    get_sent_passwords_for_user,
    update_shared_password,
    remove_share,
    is_admin, is_manager
)
from utils.theme import inject_cyber_theme


# ============================================================
# CSS
# ============================================================

from utils.theme import inject_cyber_theme, render_html

def load_css():
    inject_cyber_theme()
    render_html("""
    <style>
        .sp-title {
            font-size: 26px;
            font-weight: 800;
            color: #f8fafc;
            margin-bottom: 4px;
            letter-spacing: -0.4px;
        }
        .sp-subtitle {
            color: #94a3b8 !important;
            font-size: 13.5px;
            margin-bottom: 20px;
        }
        .sp-card {
            background: rgba(13, 22, 42, 0.75);
            border: 1px solid rgba(56, 189, 248, 0.16);
            border-radius: 12px;
            padding: 14px 18px;
            margin-bottom: 10px;
            box-shadow: 0 4px 18px rgba(0, 0, 0, 0.3);
            transition: all 0.22s ease;
        }
        .sp-card:hover {
            border-color: rgba(56, 189, 248, 0.4);
            box-shadow: 0 8px 24px rgba(6, 182, 212, 0.18);
        }
        .sp-header {
            font-size: 11px;
            font-weight: 700;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 0.6px;
            padding-bottom: 6px;
        }
        .sp-pwd-box {
            height: 38px;
            border: 1px solid rgba(56, 189, 248, 0.2);
            border-radius: 8px;
            background: rgba(13, 22, 42, 0.85);
            padding: 7px 10px;
            display: flex;
            align-items: center;
            overflow: hidden;
        }
        .sp-pwd-text {
            color: #cbd5e1;
            font-family: 'JetBrains Mono', monospace;
            font-size: 13px;
            letter-spacing: 1.5px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
    </style>
    """)


# ============================================================
# SHARE FORM
# ============================================================

def show_share_form(db, user, organization):
    with st.container(border=True):
        st.markdown("<div style='font-size:14px;font-weight:700;color:#f8fafc;margin-bottom:12px;'>🔗 Share a Vault Credential</div>", unsafe_allow_html=True)

        user_vault = db.query(models.Vault).filter(models.Vault.owner_id == user['id']).first()
        if not user_vault and is_admin(user):
            user_vault = db.query(models.Vault).first()
        if not user_vault:
            st.warning("No vault credentials found to share. Please add a password first.")
            return

        passwords = db.query(models.Password).filter(models.Password.vault_id == user_vault.id).all()
        if not passwords:
            st.warning("No passwords found in your vault.")
            return

        password_options = {p.title: p.id for p in passwords}
        c1, c2 = st.columns(2)
        with c1:
            selected_password = st.selectbox("Select Password *", list(password_options.keys()), key="sp_select_pw")
            password_id = password_options[selected_password]
        with c2:
            share_type = st.radio("Recipient Type", ["Individual User", "Team"], horizontal=True, key="sp_share_type")

        if share_type == "Individual User":
            sc1, sc2 = st.columns([3, 1])
            with sc1:
                target_email = st.text_input("User Email Address *", placeholder="colleague@example.com", key="sp_target_email")
            with sc2:
                permission = st.selectbox("Access Level", ["View", "Edit"], key="sp_user_perm")
            if st.button("Share Password 🔗", key="share_password_to_user", type="primary", use_container_width=True):
                if not target_email.strip():
                    st.error("Please enter a recipient email address.")
                else:
                    success, msg = share_password_with_user(db, user, password_id, target_email.strip().lower(), permission)
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
        else:
            teams = get_user_teams(db, user, organization.id)
            if not teams:
                st.warning("No teams available in this organization.")
            else:
                team_options = {t.team_name: t.id for t in teams}
                tc1, tc2 = st.columns([3, 1])
                with tc1:
                    selected_team = st.selectbox("Select Team *", list(team_options.keys()), key="sp_team_select")
                    team_id = team_options[selected_team]
                with tc2:
                    permission = st.selectbox("Access Level", ["View", "Edit"], key="team_perm")
                if st.button("Share With Team 👥", key="share_password_to_team", type="primary", use_container_width=True):
                    success, msg = share_password_with_team(db, user, password_id, team_id, permission)
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)


# ============================================================
# PASSWORD CARD / ROW
# ============================================================

def render_password_card(db, user, item, mode="sent", row_index=0):
    password_id = item.get("password_id")
    share_id = item.get("share_id")
    unique_id = f"{mode}_{share_id}_{password_id}_{row_index}"

    state_key = f"show_sp_{unique_id}"
    edit_state_key = f"edit_sp_{unique_id}"

    if state_key not in st.session_state:
        st.session_state[state_key] = False
    if edit_state_key not in st.session_state:
        st.session_state[edit_state_key] = False

    show_password = st.session_state[state_key]
    password_value = item.get("password") or ""
    password_display = password_value if show_password else "••••••••••"

    title = escape(str(item.get("title", "-")))
    username = escape(str(item.get("username", "-")))
    url = escape(str(item.get("url") or "-"))
    permission = escape(str(item.get("permission", "View")))
    shared_person = escape(str(item.get("shared_with") if mode == "sent" else item.get("shared_from", "-")))

    can_edit = (True if mode == "sent" else item.get("can_edit", False))
    can_remove = (True if mode == "sent" else (item.get("sender_id") == user["id"] or is_admin(user)))

    render_html(f"""
    <div class="sp-card">
        <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;margin-bottom:8px;">
            <div style="font-size:14px;font-weight:700;color:#f8fafc;display:flex;align-items:center;gap:6px;">
                <span>🔑</span> <span>{title}</span>
            </div>
            <div style="display:flex;align-items:center;gap:8px;">
                <span class="status-pill pill-cyber" style="font-size:11px;">{permission}</span>
                <span style="font-size:11.5px;color:#94a3b8;">{'Shared with' if mode == 'sent' else 'Shared by'}: <b style="color:#cbd5e1;">{shared_person}</b></span>
            </div>
        </div>
    </div>
    """)

    c_user, c_url, c_pwd, c_act = st.columns([2.0, 2.0, 2.8, 1.2], gap="small")
    with c_user:
        st.markdown(f"<div style='font-size:11px;font-weight:700;color:#94a3b8;text-transform:uppercase;'>Username</div><div style='font-size:13px;color:#cbd5e1;padding-top:4px;'>{username}</div>", unsafe_allow_html=True)
    with c_url:
        st.markdown(f"<div style='font-size:11px;font-weight:700;color:#94a3b8;text-transform:uppercase;'>Website / URL</div><div style='font-size:13px;color:#38bdf8;padding-top:4px;overflow:hidden;text-overflow:ellipsis;'>{url}</div>", unsafe_allow_html=True)
    with c_pwd:
        st.markdown("<div style='font-size:11px;font-weight:700;color:#94a3b8;text-transform:uppercase;'>Password</div>", unsafe_allow_html=True)
        pc1, pc2 = st.columns([4.8, 1.2], gap="small")
        with pc1:
            st.markdown(f"<div class='sp-pwd-box'><span class='sp-pwd-text'>{escape(password_display)}</span></div>", unsafe_allow_html=True)
        with pc2:
            eye_icon = "🙈" if show_password else "👁️"
            if st.button(eye_icon, key=f"view_sp_{unique_id}", help="Toggle view"):
                st.session_state[state_key] = not show_password
                st.rerun()
    with c_act:
        st.markdown("<div style='font-size:11px;font-weight:700;color:#94a3b8;text-transform:uppercase;'>Actions</div>", unsafe_allow_html=True)
        a1, a2 = st.columns(2)
        with a1:
            if can_edit:
                if st.button("✏️", key=f"edit_sp_{unique_id}", help="Edit Password"):
                    st.session_state[edit_state_key] = not st.session_state[edit_state_key]
                    st.rerun()
        with a2:
            if can_remove:
                if st.button("🗑️", key=f"remove_sp_{unique_id}", help="Remove Share"):
                    success, msg = remove_share(db, user, share_id)
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

    # Inline Edit Form
    if st.session_state.get(edit_state_key, False):
        with st.container(border=True):
            st.markdown(f"<div style='font-size:13px;font-weight:700;color:#f8fafc;margin-bottom:8px;'>✏️ Edit Shared Password: {title}</div>", unsafe_allow_html=True)
            ef1, ef2 = st.columns(2)
            with ef1:
                new_t = st.text_input("Title", value=item.get("title", ""), key=f"title_{unique_id}")
                new_u = st.text_input("Username", value=item.get("username", ""), key=f"usr_{unique_id}")
            with ef2:
                new_p = st.text_input("Password", value=item.get("password", ""), type="password", key=f"pwd_{unique_id}")

            bf1, bf2 = st.columns(2)
            with bf1:
                if st.button("💾 Save Update", key=f"save_{unique_id}", type="primary"):
                    if not new_p.strip():
                        st.error("Password cannot be empty.")
                    else:
                        ok, msg = update_shared_password(db, user, password_id, new_p, new_u, new_t)
                        if ok:
                            st.session_state[edit_state_key] = False
                            st.session_state[state_key] = False
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
            with bf2:
                if st.button("Cancel", key=f"cnl_{unique_id}"):
                    st.session_state[edit_state_key] = False
                    st.rerun()

    st.markdown("<div style='height:1px;background:rgba(56,189,248,0.08);margin:8px 0 12px 0;'></div>", unsafe_allow_html=True)


# ============================================================
# MAIN
# ============================================================

def show(user):
    load_css()
    db = SessionLocal()
    try:
        st.markdown('<div class="sp-title">🔗 Shared Passwords</div>', unsafe_allow_html=True)
        st.markdown('<div class="sp-subtitle">Safely distribute and collaborate on encrypted credentials.</div>', unsafe_allow_html=True)

        organization = get_user_organization(db, user)

        tab_recv, tab_sent, tab_new = st.tabs([
            "📥 Received Passwords",
            "📤 Sent Passwords",
            "➕ Share Password"
        ])

        with tab_recv:
            shared_passwords = get_shared_passwords_for_user(db, user)
            if not shared_passwords:
                st.info("No credentials have been shared with your account yet.")
            else:
                for idx, item in enumerate(shared_passwords):
                    render_password_card(db, user, item, mode="received", row_index=idx)

        with tab_sent:
            sent_passwords = get_sent_passwords_for_user(db, user)
            if not sent_passwords:
                st.info("You have not shared any credentials yet.")
            else:
                for idx, item in enumerate(sent_passwords):
                    render_password_card(db, user, item, mode="sent", row_index=idx)

        with tab_new:
            if organization:
                show_share_form(db, user, organization)
            else:
                st.warning("Organization context required to share credentials.")

    except Exception as exc:
        st.error(f"Error loading shared passwords: {exc}")
    finally:
        db.close()