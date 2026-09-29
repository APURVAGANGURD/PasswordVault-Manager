# ============================================================
# SECUREVAULT - MODERN CYBERSECURITY DASHBOARD
# ============================================================

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from datetime import datetime, timedelta, date
from html import escape

import sys
import os

sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

from database.connection import get_db
from database import models

from security.encryption import VaultEncryption
from security.key_manager import KeyManager
from security.password_strength import estimate_strength
from utils.theme import (
    inject_cyber_theme,
    render_3d_shield,
    render_encryption_pipeline,
    render_security_status_widget,
    render_html
)
from utils.audit_logger import create_audit_log


# ============================================================
# ENCRYPTION KEY
# ============================================================

GLOBAL_KEY = KeyManager.derive_key(
    "FIXED_KEY_123",
    "FIXED_SALT_123"
)


# ============================================================
# CSS LOADER
# ============================================================

def load_css():
    inject_cyber_theme()
    render_html("""
    <style>
        .dash-header-card {
            background: linear-gradient(135deg, rgba(15, 23, 42, 0.8) 0%, rgba(30, 41, 59, 0.6) 100%);
            border: 1px solid rgba(56, 189, 248, 0.2);
            border-radius: 16px;
            padding: 22px 26px;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.35);
        }
        .dash-title {
            font-size: 26px;
            font-weight: 800;
            color: #f8fafc;
            letter-spacing: -0.5px;
            margin: 0 0 4px 0;
            line-height: 1.2;
        }
        .dash-subtitle {
            font-size: 13.5px;
            color: #94a3b8;
            margin: 0;
        }
        .dash-section-title {
            font-size: 15px;
            font-weight: 700;
            color: #f8fafc;
            letter-spacing: -0.2px;
            margin: 18px 0 12px 0;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .recent-table-header {
            background: rgba(15, 23, 42, 0.85);
            border: 1px solid rgba(56, 189, 248, 0.15);
            border-radius: 10px;
            padding: 10px 14px;
            margin-bottom: 8px;
            display: flex;
            font-size: 11px;
            font-weight: 700;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 0.6px;
        }
        .recent-table-row {
            background: rgba(15, 23, 42, 0.65);
            border: 1px solid rgba(56, 189, 248, 0.12);
            border-radius: 10px;
            padding: 10px 14px;
            margin-bottom: 6px;
            transition: all 0.2s ease;
        }
        .recent-table-row:hover {
            border-color: rgba(56, 189, 248, 0.3);
            background: rgba(30, 41, 59, 0.7);
        }
        .masked-pass {
            font-family: 'JetBrains Mono', monospace;
            letter-spacing: 2px;
            color: #64748b;
            font-size: 13px;
        }
    </style>
    """)


# ============================================================
# ACCOUNT TYPE HELPER
# ============================================================

def is_organization_user(user):
    return (
        str(user.get("account_type", "PERSONAL")).upper()
        == "ORGANIZATION"
    )


# ============================================================
# PERSONAL VAULT & DATA LOADERS
# ============================================================

def get_personal_vault(db, user_id):
    try:
        return (
            db.query(models.Vault)
            .filter(
                models.Vault.owner_id == user_id,
                models.Vault.vault_type == "PERSONAL"
            )
            .first()
        )
    except Exception:
        return None


def get_expiry_status(expiry):
    if not expiry:
        return False, False
    try:
        if isinstance(expiry, datetime):
            exp_dt = expiry
        elif isinstance(expiry, date):
            exp_dt = datetime.combine(expiry, datetime.min.time())
        else:
            return False, False

        now = datetime.now()
        expired = exp_dt < now
        expiring_soon = (
            not expired
            and exp_dt <= now + timedelta(days=30)
        )
        return expired, expiring_soon
    except Exception:
        return False, False


def load_passwords(db, user_id):
    vault = get_personal_vault(db, user_id)
    if not vault:
        return []

    try:
        records = (
            db.query(models.Password)
            .filter(models.Password.vault_id == vault.id)
            .order_by(models.Password.updated_at.desc())
            .all()
        )
    except Exception as e:
        st.error(f"Unable to load passwords: {e}")
        return []

    passwords = []
    for rec in records:
        try:
            plain = VaultEncryption.decrypt_data(
                rec.encrypted_password,
                rec.encryption_nonce,
                GLOBAL_KEY
            )
            if plain is None:
                continue

            strength = estimate_strength(plain)
            score = int(strength.get("score", 0))
            label = strength.get("label", "Unknown")
            expired, expiring_soon = get_expiry_status(rec.expiry_date)

            passwords.append({
                "id": rec.id,
                "title": rec.title or "Untitled",
                "username": rec.username or "-",
                "password": plain,
                "url": rec.url or "",
                "category": rec.category or "General",
                "favorite": bool(rec.favorite),
                "strength_score": score,
                "strength_label": label,
                "expiry_date": rec.expiry_date,
                "expired": expired,
                "expiring_soon": expiring_soon,
                "created_at": rec.created_at,
                "updated_at": rec.updated_at,
            })
        except Exception:
            continue

    return passwords


def password_distribution(passwords):
    strong = 0
    medium = 0
    weak = 0

    for p in passwords:
        score = int(p.get("strength_score", 0))
        if score >= 70:
            strong += 1
        elif score >= 40:
            medium += 1
        else:
            weak += 1

    total = strong + medium + weak
    if total > 0:
        strong_pct = round(strong / total * 100)
        medium_pct = round(medium / total * 100)
        weak_pct = round(weak / total * 100)
    else:
        strong_pct = medium_pct = weak_pct = 0

    return (
        strong, medium, weak, total,
        strong_pct, medium_pct, weak_pct
    )


def calculate_health_score(passwords):
    if not passwords:
        return 100, "Very Strong", "pill-secure"
    total_score = sum(int(p.get("strength_score", 0)) for p in passwords)
    avg = round(total_score / len(passwords))
    weak_count = sum(1 for p in passwords if int(p.get("strength_score", 0)) < 40)
    expired_count = sum(1 for p in passwords if p.get("expired"))
    penalty = (weak_count * 5) + (expired_count * 10)
    score = max(0, min(100, avg - penalty))
    
    if score >= 80:
        label = "Very Strong"
        badge = "pill-secure"
    elif score >= 60:
        label = "Good"
        badge = "pill-cyber"
    elif score >= 40:
        label = "Needs Attention"
        badge = "pill-warning"
    else:
        label = "Critical"
        badge = "pill-danger"
    return score, label, badge


# ============================================================
# ORGANIZATION STATS
# ============================================================

def get_org_stats(db, user):
    stats = {"vaults": 1, "teams": 0, "members": 0, "shared": 0}
    org_id = user.get("organization_id")
    if not org_id:
        return stats

    try:
        stats["vaults"] = max(1, db.query(models.Vault).filter(models.Vault.organization_id == org_id).count())
    except Exception:
        stats["vaults"] = 1

    try:
        stats["teams"] = (
            db.query(models.Team)
            .filter(models.Team.organization_id == org_id)
            .count()
        )
    except Exception:
        stats["teams"] = 0

    try:
        team_ids = [
            team.id
            for team in (
                db.query(models.Team)
                .filter(models.Team.organization_id == org_id)
                .all()
            )
        ]
        if team_ids:
            stats["members"] = (
                db.query(models.TeamMember)
                .filter(models.TeamMember.team_id.in_(team_ids))
                .count()
            )
    except Exception:
        stats["members"] = 0

    try:
        stats["shared"] = (
            db.query(models.Share)
            .filter(models.Share.sender_id == user["id"])
            .count()
        )
    except Exception:
        stats["shared"] = 0

    return stats


# ============================================================
# RENDER METRIC CARDS
# ============================================================

def render_metric_card(label, value, icon):
    render_html(f"""
    <div class="metric-card">
        <div class="metric-header">
            <span class="metric-label">{escape(str(label))}</span>
            <span class="metric-icon">{icon}</span>
        </div>
        <div class="metric-value">{escape(str(value))}</div>
    </div>
    """)


# ============================================================
# MAIN DASHBOARD VIEW
# ============================================================

def show(user):
    load_css()

    if not user or not user.get("id"):
        st.error("Session invalid. Please log in again.")
        return

    user_id = user["id"]
    is_org = is_organization_user(user)
    db = next(get_db())

    try:
        user_name = escape(str(user.get("name", "User")))

        # ----------------------------------------------------
        # 1. WELCOME HEADER (Requirement 3)
        # ----------------------------------------------------
        shield_html = render_3d_shield(size=58)
        render_html(f"""
        <div class="dash-header-card">
            <div>
                <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;">
                    <h1 class="dash-title">Welcome back, {user_name}</h1>
                    <div class="status-pill pill-secure">
                        <span class="pill-dot dot-green"></span> Vault Secure
                    </div>
                </div>
                <p class="dash-subtitle">Your digital security is protected by SecureVault.</p>
            </div>
            <div>
                {shield_html}
            </div>
        </div>
        """)

        # ----------------------------------------------------
        # 2. SECURITY STATUS WIDGET (Requirement 9)
        # ----------------------------------------------------
        render_html(render_security_status_widget())

        # Load data
        passwords = load_passwords(db, user_id)
        total_passwords = len(passwords)

        # ----------------------------------------------------
        # 3. STATISTICS CARDS (Requirement 4)
        # ----------------------------------------------------
        if not is_org:
            # Personal User: Display ONLY Total Passwords
            render_metric_card("Total Passwords", total_passwords, "🔐")
        else:
            # Organization User: Display Total Passwords, Total Vaults, Teams, Shared Passwords
            org_stats = get_org_stats(db, user)
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                render_metric_card("Total Passwords", total_passwords, "🔐")
            with c2:
                render_metric_card("Total Vaults", org_stats["vaults"], "🗄️")
            with c3:
                render_metric_card("Teams", org_stats["teams"], "👥")
            with c4:
                render_metric_card("Shared Passwords", org_stats["shared"], "🔗")

        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

        # ----------------------------------------------------
        # 4. QUICK ACTIONS (Requirement 5)
        # ----------------------------------------------------
        st.markdown('<div class="dash-section-title">⚡ Quick Actions</div>', unsafe_allow_html=True)
        if not is_org:
            # Personal User: Show ONLY Add Password
            if st.button("➕  Add Password", key="quick_add_pwd", type="primary", use_container_width=True):
                st.session_state["nav"] = "Add Password"
                st.rerun()
        else:
            # Organization User: Show Add Password and Share Password
            qa1, qa2 = st.columns(2)
            with qa1:
                if st.button("➕  Add Password", key="quick_add_pwd", type="primary", use_container_width=True):
                    st.session_state["nav"] = "Add Password"
                    st.rerun()
            with qa2:
                if st.button("🔗  Share Password", key="quick_share_pwd", use_container_width=True):
                    st.session_state["nav"] = "Shared Passwords"
                    st.rerun()

        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

        # ----------------------------------------------------
        # 5. PASSWORD HEALTH VISUALIZATION & ARCHITECTURE (Req 6 & 10)
        # ----------------------------------------------------
        left_health_col, right_arch_col = st.columns([1.3, 1])

        with left_health_col:
            st.markdown('<div class="dash-section-title">🛡️ Password Health & Distribution</div>', unsafe_allow_html=True)
            with st.container(border=True):
                (strong, medium, weak, total, s_pct, m_pct, w_pct) = password_distribution(passwords)
                health_score, health_label, health_badge = calculate_health_score(passwords)

                # Top score header inside container
                render_html(f"""
                <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;">
                    <div>
                        <div style="font-size:12px;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:0.5px;">Health Score</div>
                        <div style="font-size:28px;font-weight:800;color:#f8fafc;font-family:'JetBrains Mono',monospace;">{health_score}<span style="font-size:14px;color:#64748b;">/100</span></div>
                    </div>
                    <div class="status-pill {health_badge}">
                        <span class="pill-dot dot-green"></span> {health_label}
                    </div>
                </div>
                """)

                chart_col, legend_col = st.columns([1.3, 1])
                with chart_col:
                    if total == 0:
                        render_html("""
                        <div style="height:210px;display:flex;align-items:center;justify-content:center;color:#64748b;font-size:13px;">
                            No passwords saved in vault
                        </div>
                        """)
                    else:
                        fig = go.Figure()
                        fig.add_trace(
                            go.Pie(
                                labels=["Strong", "Medium", "Weak"],
                                values=[strong, medium, weak],
                                hole=0.68,
                                sort=False,
                                textinfo="none",
                                hovertemplate="<b>%{label} Passwords</b><br>Count: %{value}<br>Ratio: %{percent}<extra></extra>",
                                marker=dict(
                                    colors=["#10b981", "#f59e0b", "#f43f5e"],
                                    line=dict(color="#080d1a", width=2.5)
                                )
                            )
                        )
                        fig.add_annotation(
                            x=0.5, y=0.5,
                            text=f"<b>{total}</b><br><span style='font-size:11px;color:#94a3b8;'>Total</span>",
                            showarrow=False,
                            font=dict(size=22, color="#f8fafc", family="Inter")
                        )
                        fig.update_layout(
                            height=210,
                            margin=dict(l=0, r=0, t=0, b=0),
                            showlegend=False,
                            paper_bgcolor="rgba(0,0,0,0)",
                            plot_bgcolor="rgba(0,0,0,0)"
                        )
                        st.plotly_chart(
                            fig,
                            use_container_width=True,
                            config={"displayModeBar": False, "responsive": True},
                            key="dashboard_health_donut"
                        )

                with legend_col:
                    render_html(f"""
                    <div style="padding-top:14px;display:flex;flex-direction:column;gap:10px;">
                        <div style="background:rgba(16,185,129,0.08);border:1px solid rgba(16,185,129,0.25);border-radius:8px;padding:8px 10px;">
                            <div style="font-size:11px;color:#94a3b8;font-weight:600;">Strong Passwords</div>
                            <div style="font-size:16px;font-weight:700;color:#34d399;">{strong} <span style="font-size:12px;color:#94a3b8;">({s_pct}%)</span></div>
                        </div>
                        <div style="background:rgba(245,158,11,0.08);border:1px solid rgba(245,158,11,0.25);border-radius:8px;padding:8px 10px;">
                            <div style="font-size:11px;color:#94a3b8;font-weight:600;">Medium Passwords</div>
                            <div style="font-size:16px;font-weight:700;color:#fbbf24;">{medium} <span style="font-size:12px;color:#94a3b8;">({m_pct}%)</span></div>
                        </div>
                        <div style="background:rgba(244,63,94,0.08);border:1px solid rgba(244,63,94,0.25);border-radius:8px;padding:8px 10px;">
                            <div style="font-size:11px;color:#94a3b8;font-weight:600;">Weak Passwords</div>
                            <div style="font-size:16px;font-weight:700;color:#fb7185;">{weak} <span style="font-size:12px;color:#94a3b8;">({w_pct}%)</span></div>
                        </div>
                    </div>
                    """)

        with right_arch_col:
            st.markdown('<div class="dash-section-title">🔐 Cryptographic Security Flow</div>', unsafe_allow_html=True)
            render_html(render_encryption_pipeline())

            # Expiring soon check
            expiring = [p for p in passwords if p["expiring_soon"]]
            if expiring:
                render_html(f"""
                <div style="margin-top:12px;background:rgba(245,158,11,0.12);border:1px solid rgba(245,158,11,0.3);border-radius:10px;padding:12px 14px;">
                    <div style="font-size:12px;font-weight:700;color:#fbbf24;margin-bottom:4px;">⏰ Passwords Expiring Soon</div>
                    <div style="font-size:12px;color:#cbd5e1;">You have {len(expiring)} password(s) due for renewal in the next 30 days.</div>
                </div>
                """)

        st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

        # ----------------------------------------------------
        # 6. RECENT PASSWORDS TABLE (Requirement 7)
        # ----------------------------------------------------
        st.markdown('<div class="dash-section-title">🕐 Recent Passwords</div>', unsafe_allow_html=True)

        # Handle pending delete confirmation if active
        pending_delete_id = st.session_state.get("dashboard_delete_id")
        if pending_delete_id:
            del_target = next((p for p in passwords if p["id"] == pending_delete_id), None)
            if del_target:
                render_html(f"""
                <div style="background:rgba(244,63,94,0.12);border:1px solid rgba(244,63,94,0.35);border-radius:12px;padding:14px 18px;margin-bottom:14px;">
                    <div style="font-size:13.5px;font-weight:700;color:#fb7185;margin-bottom:6px;">⚠️ Confirm Deletion</div>
                    <div style="font-size:13px;color:#cbd5e1;margin-bottom:12px;">Are you sure you want to delete <b>{escape(del_target['title'])}</b>? This action cannot be undone.</div>
                </div>
                """)
                dc1, dc2 = st.columns(2)
                with dc1:
                    if st.button("Yes, Delete Password", key=f"confirm_del_{pending_delete_id}", type="primary", use_container_width=True):
                        try:
                            rec = db.query(models.Password).filter(models.Password.id == pending_delete_id).first()
                            if rec:
                                db.delete(rec)
                                db.commit()
                                create_audit_log(
                                    user_id=user["id"],
                                    action="PASSWORD_DELETED",
                                    target=f"Deleted password: {del_target['title']}",
                                    target_type="PASSWORD",
                                    target_id=pending_delete_id,
                                    organization_id=user.get("organization_id")
                                )
                                st.session_state.pop("dashboard_delete_id", None)
                                st.success("Password permanently removed.")
                                st.rerun()
                        except Exception as e:
                            db.rollback()
                            st.error(f"Deletion failed: {e}")
                with dc2:
                    if st.button("Cancel", key=f"cancel_del_{pending_delete_id}", use_container_width=True):
                        st.session_state.pop("dashboard_delete_id", None)
                        st.rerun()
            else:
                st.session_state.pop("dashboard_delete_id", None)

        def _safe_dt(value):
            if value is None:
                return datetime.min
            if isinstance(value, datetime):
                return value.replace(tzinfo=None) if value.tzinfo is not None else value
            if isinstance(value, date):
                return datetime(value.year, value.month, value.day)
            return datetime.min

        recent_passwords = sorted(
            passwords,
            key=lambda x: _safe_dt(x.get("updated_at") or x.get("created_at")),
            reverse=True
        )[:6]

        if not recent_passwords:
            render_html("""
            <div style="background:rgba(15,23,42,0.5);border:1px dashed rgba(56,189,248,0.2);border-radius:12px;padding:32px;text-align:center;color:#64748b;font-size:13.5px;">
                No passwords found in your vault. Click <b>Add Password</b> above to get started.
            </div>
            """)
        else:
            # Table Header
            col_t, col_u, col_p, col_s, col_a = st.columns([2.2, 2.0, 1.8, 1.6, 1.8])
            with col_t:
                st.markdown("<div style='font-size:11px;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:0.5px;'>Title</div>", unsafe_allow_html=True)
            with col_u:
                st.markdown("<div style='font-size:11px;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:0.5px;'>Username</div>", unsafe_allow_html=True)
            with col_p:
                st.markdown("<div style='font-size:11px;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:0.5px;'>Password</div>", unsafe_allow_html=True)
            with col_s:
                st.markdown("<div style='font-size:11px;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:0.5px;'>Status</div>", unsafe_allow_html=True)
            with col_a:
                st.markdown("<div style='font-size:11px;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:0.5px;'>Actions</div>", unsafe_allow_html=True)

            # Table Rows
            for p in recent_passwords:
                pid = p["id"]
                title = escape(p["title"])
                username = escape(p["username"])
                is_secure = p["strength_score"] >= 60 and not p["expired"]
                status_html = (
                    '<span class="status-pill pill-secure">✅ Secure</span>'
                    if is_secure else
                    '<span class="status-pill pill-warning">⚠️ Attention</span>'
                )

                r_col_t, r_col_u, r_col_p, r_col_s, r_col_a = st.columns([2.2, 2.0, 1.8, 1.6, 1.8])
                with r_col_t:
                    st.markdown(f"<div style='font-size:13.5px;font-weight:600;color:#f8fafc;padding-top:6px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;'>🔑 {title}</div>", unsafe_allow_html=True)
                with r_col_u:
                    st.markdown(f"<div style='font-size:13px;color:#94a3b8;padding-top:6px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;'>{username}</div>", unsafe_allow_html=True)
                with r_col_p:
                    st.markdown("<div class='masked-pass' style='padding-top:7px;'>••••••••••••</div>", unsafe_allow_html=True)
                with r_col_s:
                    st.markdown(f"<div style='padding-top:6px;'>{status_html}</div>", unsafe_allow_html=True)
                with r_col_a:
                    act1, act2, act3 = st.columns(3)
                    with act1:
                        if st.button("👁️", key=f"view_password_{pid}", help="View Password"):
                            st.session_state["current_view_id"] = pid
                            st.session_state["nav"] = "View Password"
                            st.rerun()
                    with act2:
                        if st.button("✏️", key=f"edit_password_{pid}", help="Edit Password"):
                            st.session_state["editing_password_id"] = pid
                            st.session_state["nav"] = "My Vault"
                            st.rerun()
                    with act3:
                        if st.button("🗑️", key=f"delete_password_{pid}", help="Delete Password"):
                            st.session_state["dashboard_delete_id"] = pid
                            st.rerun()

                st.markdown("<div style='height:1px;background:rgba(56,189,248,0.08);margin:4px 0 8px 0;'></div>", unsafe_allow_html=True)

        # ----------------------------------------------------
        # 7. FAVORITES SECTION
        # ----------------------------------------------------
        favorites = [p for p in passwords if p["favorite"]]
        if favorites:
            st.markdown('<div class="dash-section-title">⭐ Starred Favorites</div>', unsafe_allow_html=True)
            fav_rows = []
            for p in favorites:
                expiry = p.get("expiry_date")
                if isinstance(expiry, (datetime, date)):
                    expiry_text = expiry.strftime("%d %b %Y")
                else:
                    expiry_text = "No expiry"

                fav_rows.append({
                    "Title": p["title"],
                    "Username": p["username"],
                    "Category": p["category"],
                    "Strength": p["strength_label"],
                    "Expiry": expiry_text
                })

            st.dataframe(
                pd.DataFrame(fav_rows),
                use_container_width=True,
                hide_index=True
            )

    except Exception as e:
        st.error(f"Dashboard error: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    st.warning("Dashboard module loaded. Open it through SecureVault Manager.")