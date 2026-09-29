# ============================================================
# pages/teams.py
# SecureVault Manager - Modern Enterprise Team Collaboration
# ============================================================

import streamlit as st
import pandas as pd
import sys, os
from html import escape

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import SessionLocal
from database import models
from modules.team_backend import (
    is_admin, is_manager, get_user_organization, get_departments,
    get_user_teams, create_team, add_team_member, remove_team_member,
    update_member_role, delete_team, get_team_vault_passwords,
    update_shared_password, remove_share
)

from utils.theme import inject_cyber_theme, render_3d_team, render_html


# ============================================================
# CSS
# ============================================================

def load_css():
    inject_cyber_theme()
    render_html("""
    <style>
        .team-title {
            font-size: 26px;
            font-weight: 800;
            color: #f8fafc;
            margin-bottom: 4px;
            letter-spacing: -0.4px;
        }
        .team-subtitle {
            color: #94a3b8 !important;
            font-size: 13.5px;
            margin-bottom: 20px;
        }
        .team-card {
            border: 1px solid rgba(56, 189, 248, 0.18);
            border-radius: 14px;
            padding: 20px 22px;
            margin-bottom: 12px;
            background: rgba(13, 22, 42, 0.78);
            backdrop-filter: blur(16px);
            box-shadow: 0 8px 30px rgba(0, 0, 0, 0.35);
            transition: all 0.25s ease;
        }
        .team-card:hover {
            border-color: rgba(56, 189, 248, 0.45);
            box-shadow: 0 12px 36px rgba(6, 182, 212, 0.22);
        }
        .team-card-name {
            font-size: 19px;
            font-weight: 700;
            color: #f8fafc;
            margin-bottom: 2px;
        }
        .team-card-department {
            color: #38bdf8 !important;
            font-size: 12.5px;
            font-weight: 600;
        }
        .team-meta-row {
            display: flex;
            align-items: center;
            gap: 16px;
            flex-wrap: wrap;
            margin-top: 12px;
            padding-top: 10px;
            border-top: 1px solid rgba(56, 189, 248, 0.1);
            font-size: 12px;
            color: #94a3b8;
        }
        .vault-table-header {
            font-size: 11px;
            font-weight: 700;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 0.6px;
            padding-bottom: 6px;
        }
        .vault-pwd-box {
            height: 38px;
            border: 1px solid rgba(56, 189, 248, 0.18);
            border-radius: 8px;
            background: rgba(13, 22, 42, 0.75);
            padding: 8px 10px;
            display: flex;
            align-items: center;
            overflow: hidden;
        }
        .vault-pwd-text {
            color: #38bdf8;
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
# SESSION STATE
# ============================================================

def initialize_state():
    if "team_page_mode" not in st.session_state:
        st.session_state.team_page_mode = "list"
    if "pending_team_members" not in st.session_state:
        st.session_state.pending_team_members = []
    if "selected_team_id" not in st.session_state:
        st.session_state.selected_team_id = None
    if "team_add_mode" not in st.session_state:
        st.session_state.team_add_mode = False


def reset_team_page():
    st.session_state.team_page_mode = "list"
    st.session_state.pending_team_members = []
    st.session_state.selected_team_id = None
    st.session_state.team_add_mode = False


def add_pending_member(email, role):
    email = (email or "").strip().lower()
    if not email:
        st.error("Enter member email address.")
        return
    if "@" not in email:
        st.error("Enter a valid email address.")
        return
    for member in st.session_state.pending_team_members:
        if member["email"] == email:
            st.error("This member is already added.")
            return
    st.session_state.pending_team_members.append({"email": email, "role": role})


# ============================================================
# CREATE TEAM
# ============================================================

def show_create_team(db, user, organization):
    if not is_admin(user):
        st.error("Only administrators can create teams.")
        if st.button("← Back to Teams", key="create_team_back"):
            reset_team_page()
            st.rerun()
        return

    st.markdown('<div class="team-title">Create Team</div>', unsafe_allow_html=True)
    st.markdown('<div class="team-subtitle">Create a departmental team and assign members.</div>', unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown('<div class="section-title">Team Configuration</div>', unsafe_allow_html=True)
        team_name = st.text_input("Team Name *", placeholder="e.g. Security Operations Center", key="create_team_name")

        try:
            departments = get_departments(db, organization.id)
        except Exception as exc:
            departments = []
            st.error(f"Unable to load departments: {exc}")

        department_options = {"No Department": None}
        for d in departments or []:
            if d is not None:
                department_options[str(d.name)] = d.id

        selected_department_name = st.selectbox(
            "Department",
            options=list(department_options.keys()),
            key="create_team_department",
        )
        department_id = department_options[selected_department_name]

        description = st.text_area("Description (optional)", key="create_team_description", placeholder="Team scope and access privileges")

        st.markdown('<div class="section-title">Initial Members</div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns([4, 2, 1.2])
        with c1:
            member_email = st.text_input("Member Email", placeholder="employee@example.com", key="create_member_email")
        with c2:
            member_role = st.selectbox("Role", ["EMPLOYEE", "MANAGER"], key="create_member_role")
        with c3:
            st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
            if st.button("Add", key="create_member_add", use_container_width=True):
                add_pending_member(member_email, member_role)
                st.rerun()

        if st.session_state.pending_team_members:
            st.markdown("<div style='font-size:12px;font-weight:700;color:#94a3b8;text-transform:uppercase;margin:10px 0 6px 0;'>Pending Members</div>", unsafe_allow_html=True)
            for idx, member in enumerate(st.session_state.pending_team_members):
                mc1, mc2, mc3 = st.columns([5, 2, 1])
                with mc1:
                    st.markdown(f'<div style="background:rgba(13,22,42,0.6);border:1px solid rgba(56,189,248,0.15);border-radius:8px;padding:8px 12px;font-size:13px;color:#f8fafc;">{member["email"]}</div>', unsafe_allow_html=True)
                with mc2:
                    st.markdown(f'<div style="padding-top:8px;"><span class="status-pill pill-cyber">{member["role"]}</span></div>', unsafe_allow_html=True)
                with mc3:
                    if st.button("✕", key=f"pending_remove_{idx}", help="Remove from list"):
                        st.session_state.pending_team_members.pop(idx)
                        st.rerun()

        st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Cancel", key="create_team_cancel", use_container_width=True):
                reset_team_page()
                st.rerun()
        with c2:
            if st.button("Create Team 👥", key="create_team_submit", type="primary", use_container_width=True):
                if not team_name.strip():
                    st.error("Team name is required.")
                    return

                success, result = create_team(
                    db=db,
                    user=user,
                    team_name=team_name.strip(),
                    department_id=department_id,
                    description=description,
                )

                if not success:
                    st.error(f"CREATE TEAM ERROR: {result}")
                    return

                team_id = result.id
                errors = []
                for member in st.session_state.pending_team_members:
                    ok, msg = add_team_member(
                        db=db, user=user, team_id=team_id,
                        email=member["email"], role=member["role"],
                    )
                    if not ok:
                        errors.append(f'{member["email"]}: {msg}')

                if errors:
                    st.warning("Team created, but some members could not be added.")
                    for e in errors:
                        st.error(e)
                else:
                    st.success("Team created successfully.")
                    reset_team_page()
                    st.rerun()


# ============================================================
# TEAM LIST
# ============================================================

def show_team_list(db, user, organization):
    c1, c2 = st.columns([7, 2])
    with c1:
        st.markdown('<div class="team-title">👥 Team Vaults & Collaboration</div>', unsafe_allow_html=True)
        st.markdown('<div class="team-subtitle">Manage organization teams, members, and shared departmental vaults.</div>', unsafe_allow_html=True)
    with c2:
        if is_admin(user):
            if st.button("➕ Create Team", key="team_list_create", type="primary", use_container_width=True):
                st.session_state.team_page_mode = "create"
                st.session_state.pending_team_members = []
                st.rerun()

    teams = get_user_teams(db, user, organization.id)

    if not teams:
        st.info("You are not a member of any team yet. Organization administrators can create and assign teams.")
        return

    for team in teams:
        department_name = team.department.name if team.department else "No Department"
        member_count = len(team.members)
        created_date = team.created_at.strftime("%d %b %Y") if team.created_at else "-"

        # Determine user's role in this team
        if is_admin(user):
            user_team_role = "ADMIN / OWNER"
            role_badge_class = "pill-secure"
        else:
            member_record = next((m for m in team.members if m.user_id == user["id"]), None)
            if member_record and str(member_record.role).upper() == "MANAGER":
                user_team_role = "MANAGER"
                role_badge_class = "pill-warning"
            else:
                user_team_role = "EMPLOYEE"
                role_badge_class = "pill-cyber"

        # Subtle 3D Team Icon
        team_3d_icon = render_3d_team(size=44)

        render_html(f"""
        <div class="team-card">
            <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;">
                <div style="display:flex;align-items:center;gap:14px;">
                    {team_3d_icon}
                    <div>
                        <div class="team-card-name">{escape(team.team_name)}</div>
                        <div class="team-card-department">🏢 {escape(department_name)}</div>
                    </div>
                </div>
                <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
                    <span class="status-pill pill-cyber">
                        👥 {member_count} Members
                    </span>
                    <span class="status-pill {role_badge_class}">
                        🛡️ Your Role: {user_team_role}
                    </span>
                </div>
            </div>
            <div class="team-meta-row">
                <div>📅 Created: <b>{created_date}</b></div>
                {f"<div>📝 Description: {escape(team.description)}</div>" if getattr(team, 'description', None) else ""}
            </div>
        </div>
        """)

        # ------------------------------------------------------------
        # 1. EXPANDABLE SECTION: VIEW MEMBERS (Requirement 12)
        # ------------------------------------------------------------
        with st.expander(f"👥 View Members ({member_count})"):
            members = list(team.members)
            if not members:
                st.info("No members have been added to this team.")
            else:
                m_header_cols = st.columns([3, 3, 2, 2])
                with m_header_cols[0]: st.markdown("<div class='vault-table-header'>Name</div>", unsafe_allow_html=True)
                with m_header_cols[1]: st.markdown("<div class='vault-table-header'>Email</div>", unsafe_allow_html=True)
                with m_header_cols[2]: st.markdown("<div class='vault-table-header'>Role</div>", unsafe_allow_html=True)
                with m_header_cols[3]: st.markdown("<div class='vault-table-header'>Joined</div>", unsafe_allow_html=True)

                for m in members:
                    mc1, mc2, mc3, mc4 = st.columns([3, 3, 2, 2])
                    m_name = m.user.name if m.user else "-"
                    m_email = m.email or (m.user.email if m.user else "-")
                    m_role = m.role
                    m_joined = m.joined_at.strftime("%d %b %Y") if m.joined_at else "-"
                    with mc1: st.markdown(f"<div style='padding-top:6px;font-size:13px;font-weight:600;color:#f8fafc;'>{escape(m_name)}</div>", unsafe_allow_html=True)
                    with mc2: st.markdown(f"<div style='padding-top:6px;font-size:12.5px;color:#94a3b8;'>{escape(m_email)}</div>", unsafe_allow_html=True)
                    with mc3: st.markdown(f"<div style='padding-top:4px;'><span class='status-pill pill-cyber' style='font-size:10.5px;'>{escape(str(m_role))}</span></div>", unsafe_allow_html=True)
                    with mc4: st.markdown(f"<div style='padding-top:6px;font-size:12px;color:#64748b;'>{m_joined}</div>", unsafe_allow_html=True)

                # Member management if Admin or Manager
                if is_admin(user) or is_manager(user):
                    st.divider()
                    st.markdown("<div style='font-size:12px;font-weight:700;color:#38bdf8;text-transform:uppercase;margin-bottom:8px;'>Manage Member Permissions</div>", unsafe_allow_html=True)
                    for m in members:
                        m_ident = m.email or (m.user.email if m.user else f"Member {m.id}")
                        mm1, mm2, mm3, mm4 = st.columns([3, 2, 1.2, 1.2])
                        with mm1:
                            st.markdown(f"<div style='padding-top:8px;font-size:13px;color:#cbd5e1;'>{escape(m_ident)}</div>", unsafe_allow_html=True)
                        with mm2:
                            current_role = "MANAGER" if m.role == "MANAGER" else "EMPLOYEE"
                            new_role = st.selectbox(
                                "Role", ["EMPLOYEE", "MANAGER"],
                                index=(1 if current_role == "MANAGER" else 0),
                                key=f"inline_role_{team.id}_{m.id}",
                                label_visibility="collapsed"
                            )
                        with mm3:
                            if st.button("Save", key=f"inline_save_{team.id}_{m.id}", use_container_width=True):
                                ok, msg = update_member_role(db, user, team.id, m.id, new_role)
                                if ok:
                                    st.success("Role updated.")
                                    st.rerun()
                                else:
                                    st.error(msg)
                        with mm4:
                            if st.button("Remove", key=f"inline_rem_{team.id}_{m.id}", use_container_width=True):
                                ok, msg = remove_team_member(db, user, team.id, m.id)
                                if ok:
                                    st.success("Member removed.")
                                    st.rerun()
                                else:
                                    st.error(msg)

        # ------------------------------------------------------------
        # 2. EXPANDABLE SECTION: ADD MEMBER (Requirement 12)
        # ------------------------------------------------------------
        if is_admin(user) or is_manager(user):
            with st.expander("➕ Add Member"):
                am1, am2, am3 = st.columns([4, 2, 1.5])
                with am1:
                    new_mem_email = st.text_input("Member Email", placeholder="colleague@example.com", key=f"quick_mem_email_{team.id}")
                with am2:
                    new_mem_role = st.selectbox("Role", ["EMPLOYEE", "MANAGER"], key=f"quick_mem_role_{team.id}")
                with am3:
                    st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
                    if st.button("Add to Team", key=f"quick_add_btn_{team.id}", type="primary", use_container_width=True):
                        if not new_mem_email.strip():
                            st.error("Member email is required.")
                        else:
                            ok, msg = add_team_member(db=db, user=user, team_id=team.id, email=new_mem_email.strip(), role=new_mem_role)
                            if ok:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)

        # ------------------------------------------------------------
        # 3. EXPANDABLE SECTION: TEAM VAULT (Requirement 12)
        # ------------------------------------------------------------
        team_passwords = get_team_vault_passwords(db, team.id, user)
        vault_count = len(team_passwords) if team_passwords else 0

        with st.expander(f"🔐 Team Vault - {team.team_name} ({vault_count})"):
            if not team_passwords:
                st.info("No passwords shared with this team vault yet.")
            else:
                header_cols = st.columns([1.8, 1.8, 2.0, 2.6, 1.8, 1.2, 1.4], gap="small")
                headers = ["Title", "Username", "URL", "Password", "Shared From", "Access", "Action"]
                for col, header in zip(header_cols, headers):
                    with col:
                        st.markdown(f"<div class='vault-table-header'>{header}</div>", unsafe_allow_html=True)

                st.markdown("<div style='height:1px;background:rgba(56,189,248,0.1);margin-bottom:8px;'></div>", unsafe_allow_html=True)

                for row_index, p in enumerate(team_passwords):
                    password_id = p.get("password_id")
                    share_id = p.get("share_id")
                    unique_id = f"tv_{team.id}_{share_id}_{password_id}_{row_index}"

                    show_key = f"team_show_{unique_id}"
                    if show_key not in st.session_state:
                        st.session_state[show_key] = False

                    show_password = st.session_state[show_key]
                    display_password = (p.get("password") or "") if show_password else "••••••••••"

                    r_cols = st.columns([1.8, 1.8, 2.0, 2.6, 1.8, 1.2, 1.4], gap="small")
                    with r_cols[0]:
                        st.markdown(f"<div style='font-size:13.5px;font-weight:600;color:#f8fafc;padding-top:8px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;'>🔑 {escape(p.get('title', '-'))}</div>", unsafe_allow_html=True)
                    with r_cols[1]:
                        st.markdown(f"<div style='font-size:13px;color:#94a3b8;padding-top:8px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;'>{escape(p.get('username', '-'))}</div>", unsafe_allow_html=True)
                    with r_cols[2]:
                        st.markdown(f"<div style='font-size:13px;color:#38bdf8;padding-top:8px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;'>{escape(p.get('url', '-'))}</div>", unsafe_allow_html=True)
                    with r_cols[3]:
                        pw_col, eye_col = st.columns([4.8, 1.2], gap="small")
                        with pw_col:
                            st.markdown(f"<div class='vault-pwd-box'><span class='vault-pwd-text'>{escape(display_password)}</span></div>", unsafe_allow_html=True)
                        with eye_col:
                            eye_lbl = "🙈" if show_password else "👁️"
                            if st.button(eye_lbl, key=f"eye_{unique_id}", help="Toggle view"):
                                st.session_state[show_key] = not show_password
                                st.rerun()
                    with r_cols[4]:
                        st.markdown(f"<div style='font-size:12.5px;color:#cbd5e1;padding-top:8px;'>{escape(p.get('shared_from', '-'))}</div>", unsafe_allow_html=True)
                    with r_cols[5]:
                        st.markdown(f"<div style='padding-top:6px;'><span class='status-pill pill-cyber' style='font-size:11px;'>{escape(p.get('permission', 'View'))}</span></div>", unsafe_allow_html=True)
                    with r_cols[6]:
                        can_edit = bool(p.get("can_edit", False))
                        can_remove = (p.get("sender_id") == user["id"] or is_admin(user))
                        act1, act2 = st.columns(2)
                        with act1:
                            if can_edit:
                                if st.button("✏️", key=f"edit_{unique_id}", help="Edit Password"):
                                    st.session_state[f"tv_editing_{unique_id}"] = True
                                    st.rerun()
                        with act2:
                            if can_remove:
                                if st.button("🗑️", key=f"rem_{unique_id}", help="Remove from Team"):
                                    ok, msg = remove_share(db, user, share_id)
                                    if ok:
                                        st.success(msg)
                                        st.rerun()
                                    else:
                                        st.error(msg)

                    # Inline edit form if active
                    if st.session_state.get(f"tv_editing_{unique_id}", False):
                        with st.container(border=True):
                            st.markdown(f"<div style='font-size:13px;font-weight:700;color:#f8fafc;margin-bottom:8px;'>✏️ Edit {escape(p.get('title', 'Password'))}</div>", unsafe_allow_html=True)
                            ed1, ed2 = st.columns(2)
                            with ed1:
                                new_t = st.text_input("Title", value=p.get("title", ""), key=f"ed_t_{unique_id}")
                                new_u = st.text_input("Username", value=p.get("username", ""), key=f"ed_u_{unique_id}")
                            with ed2:
                                new_pwd = st.text_input("Password", value=p.get("password", ""), type="password", key=f"ed_p_{unique_id}")
                            sc1, sc2 = st.columns(2)
                            with sc1:
                                if st.button("Save Changes", key=f"ed_save_{unique_id}", type="primary"):
                                    ok, msg = update_shared_password(db, user, password_id, new_t, new_u, new_pwd)
                                    if ok:
                                        st.session_state.pop(f"tv_editing_{unique_id}", None)
                                        st.success(msg)
                                        st.rerun()
                                    else:
                                        st.error(msg)
                            with sc2:
                                if st.button("Cancel", key=f"ed_cancel_{unique_id}"):
                                    st.session_state.pop(f"tv_editing_{unique_id}", None)
                                    st.rerun()

                    st.markdown("<div style='height:1px;background:rgba(56,189,248,0.06);margin:4px 0;'></div>", unsafe_allow_html=True)

        # Admin delete option
        if is_admin(user):
            del_exp = st.expander(f"⚙️ Team Administration ({team.team_name})")
            with del_exp:
                if st.button(f"🗑️ Delete Team '{team.team_name}'", key=f"del_{team.id}", type="secondary"):
                    st.session_state[f"confirm_delete_{team.id}"] = True

                if st.session_state.get(f"confirm_delete_{team.id}", False):
                    st.warning(f"Are you sure you want to permanently remove team '{team.team_name}'?")
                    dc1, dc2 = st.columns(2)
                    with dc1:
                        if st.button("Yes, Confirm Delete", key=f"yes_{team.id}", type="primary", use_container_width=True):
                            ok, msg = delete_team(db, user, team.id)
                            if ok:
                                st.session_state[f"confirm_delete_{team.id}"] = False
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)
                    with dc2:
                        if st.button("Cancel", key=f"no_{team.id}", use_container_width=True):
                            st.session_state[f"confirm_delete_{team.id}"] = False
                            st.rerun()

        st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)


# ============================================================
# MAIN
# ============================================================

def show(user):
    load_css()
    initialize_state()
    db = SessionLocal()
    try:
        organization = get_user_organization(db, user)
        if not organization:
            st.error("You are not associated with an organization.")
            return

        if st.session_state.team_page_mode == "create":
            show_create_team(db, user, organization)
            return

        show_team_list(db, user, organization)
    except Exception as exc:
        st.error(f"TEAMS PAGE ERROR: {exc}")
    finally:
        db.close()