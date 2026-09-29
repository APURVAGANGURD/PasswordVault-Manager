# ============================================================
# pages/password_health.py
# SecureVault Manager - Modern Password Health & Analytics
# ============================================================

import streamlit as st
import sys
import os
import datetime
from collections import Counter
from io import BytesIO
from html import escape

import pandas as pd
import plotly.graph_objects as go

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import SessionLocal
from database import models
from security.encryption import VaultEncryption
from security.key_manager import KeyManager
from security.password_strength import estimate_strength
from utils.theme import inject_cyber_theme, render_3d_shield, render_html


# ============================================================
# CSS
# ============================================================

def load_css():
    inject_cyber_theme()
    render_html("""
    <style>
        .report-title {
            font-size: 26px;
            font-weight: 800;
            color: #f8fafc;
            margin-bottom: 4px;
            letter-spacing: -0.4px;
        }
        .report-subtitle {
            color: #94a3b8;
            font-size: 13.5px;
            margin-bottom: 20px;
        }
        .report-card {
            border: 1px solid rgba(56, 189, 248, 0.18);
            border-radius: 14px;
            padding: 22px;
            background: rgba(13, 22, 42, 0.78);
            backdrop-filter: blur(16px);
            margin-bottom: 14px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.35);
        }
        .report-score {
            font-size: 54px;
            font-weight: 800;
            text-align: center;
            line-height: 1;
            font-family: 'JetBrains Mono', monospace;
            letter-spacing: -0.04em;
        }
        .report-score-label {
            text-align: center;
            color: #94a3b8;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.6px;
            margin-top: 4px;
        }
        .report-status {
            text-align: center;
            font-size: 18px;
            font-weight: 700;
            margin-top: 8px;
            letter-spacing: -0.2px;
        }
        .report-info {
            border: 1px solid rgba(56, 189, 248, 0.15);
            border-radius: 12px;
            padding: 14px 16px;
            text-align: center;
            min-height: 86px;
            background: rgba(13, 22, 42, 0.65);
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25);
            transition: all 0.22s ease;
        }
        .report-info:hover {
            border-color: rgba(56, 189, 248, 0.35);
            transform: translateY(-2px);
        }
        .report-info-value {
            font-size: 26px;
            font-weight: 800;
            font-family: 'JetBrains Mono', monospace;
            line-height: 1.1;
        }
        .status-pill {
            padding: 3px 10px;
            border-radius: 999px;
            font-size: 11.5px;
            font-weight: 700;
        }
        .report-info-label {
            color: #94a3b8;
            font-size: 11.5px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-top: 4px;
        }
        .finding {
            border: 1px solid rgba(56, 189, 248, 0.14);
            border-radius: 10px;
            padding: 12px 16px;
            margin-bottom: 8px;
            font-size: 13.5px;
            background: rgba(13, 22, 42, 0.62);
            color: #cbd5e1;
            display: flex;
            align-items: center;
            gap: 10px;
            transition: all 0.2s ease;
        }
        .finding:hover {
            border-color: rgba(56, 189, 248, 0.3);
            background: rgba(20, 33, 62, 0.75);
        }
    </style>
    """, unsafe_allow_html=True)


# ============================================================
# DATETIME HELPER
# ============================================================

def normalize_datetime(value):
    if value is None:
        return None
    if isinstance(value, datetime.datetime):
        return value
    if isinstance(value, datetime.date):
        return datetime.datetime.combine(value, datetime.time.min)
    return None


# ============================================================
# COLOR / STATUS HELPERS
# ============================================================

def get_health_color(score):
    if score >= 80:
        return "#10b981"
    if score >= 60:
        return "#06b6d4"
    if score >= 40:
        return "#f59e0b"
    return "#f43f5e"


def get_health_status(score):
    if score >= 80:
        return "Very Strong"
    if score >= 60:
        return "Good"
    if score >= 40:
        return "Needs Attention"
    return "Critical"


def get_health_badge(score):
    if score >= 80:
        return "pill-secure"
    if score >= 60:
        return "pill-cyber"
    if score >= 40:
        return "pill-warning"
    return "pill-danger"


# ============================================================
# GENERATE PDF REPORT (100% PRESERVED)
# ============================================================

def generate_pdf_report(user, decrypted_passwords, total, strong_count, medium_count,
                        weak_count, reused_count, expiring_soon_count, expired_count,
                        health_score, status_label, now, thirty_days_from_now):

    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontSize=22,
        leading=26,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#111827"),
        spaceAfter=8
    )

    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#6b7280"),
        spaceAfter=15
    )

    heading_style = ParagraphStyle(
        "Heading",
        parent=styles["Heading2"],
        fontSize=15,
        leading=19,
        textColor=colors.HexColor("#111827"),
        spaceBefore=12,
        spaceAfter=8
    )

    normal_style = ParagraphStyle(
        "NormalReport",
        parent=styles["Normal"],
        fontSize=9,
        leading=13
    )

    center_style = ParagraphStyle(
        "Center",
        parent=normal_style,
        alignment=TA_CENTER
    )

    story = []

    # HEADER
    story.append(Paragraph("SecureVault", title_style))
    story.append(Paragraph("Password Health Security Audit", ParagraphStyle("ReportName", parent=title_style, fontSize=17, textColor=colors.HexColor("#0284c7"))))

    user_name = user.get("name", "User")
    generated_date = datetime.datetime.now().strftime("%d %B %Y, %I:%M %p")
    story.append(Paragraph(f"User: {user_name}<br/>Audit Date: {generated_date}", subtitle_style))
    story.append(Spacer(1, 5 * mm))

    # HEALTH SCORE
    score_table = Table(
        [[
            Paragraph(f"<font size='30'><b>{health_score}</b></font><br/><font size='10'>out of 100</font>", center_style),
            Paragraph(f"<font size='16'><b>{status_label}</b></font><br/><font size='9'>Security Evaluation</font>", center_style)
        ]],
        colWidths=[85 * mm, 85 * mm]
    )
    story.append(score_table)
    story.append(Spacer(1, 5 * mm))

    # RECOMMENDATIONS
    story.append(Paragraph("Security Recommendations", heading_style))
    recommendations = []
    if weak_count > 0:
        recommendations.append("Replace weak passwords with 16+ character high-entropy credentials.")
    if reused_count > 0:
        recommendations.append("Enforce unique credentials across all applications to mitigate credential stuffing.")
    if expired_count > 0:
        recommendations.append("Rotate expired credentials immediately.")
    if expiring_soon_count > 0:
        recommendations.append("Review credentials scheduled to expire within the next 30 days.")
    if not recommendations:
        recommendations.append("Continue adhering to zero-knowledge master credential hygiene.")

    rec_data = [[str(idx), Paragraph(r, normal_style)] for idx, r in enumerate(recommendations, start=1)]
    rec_table = Table(rec_data, colWidths=[12 * mm, 158 * mm])
    rec_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f0f9ff")),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6)
    ]))
    story.append(rec_table)

    # DETAILED ANALYSIS
    story.append(Paragraph("Detailed Credential Analysis", heading_style))
    detail_data = [["Title", "Username", "Strength", "Score", "Reused", "Status"]]
    pwd_counter = Counter(p["password"] for p in decrypted_passwords)

    for p in decrypted_passwords:
        expiry = p["expiry_date"]
        if not expiry:
            exp_status = "No Expiry"
        elif expiry < now:
            exp_status = "Expired"
        elif expiry <= thirty_days_from_now:
            exp_status = "Expiring Soon"
        else:
            exp_status = "Valid"

        reused = "Yes" if pwd_counter[p["password"]] > 1 else "No"
        detail_data.append([
            str(p["title"] or ""),
            str(p["username"] or ""),
            str(p["strength_label"]),
            str(p["strength_score"]),
            reused,
            exp_status
        ])

    detail_table = Table(detail_data, colWidths=[35 * mm, 40 * mm, 30 * mm, 18 * mm, 20 * mm, 27 * mm], repeatRows=1)
    detail_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d1d5db")),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (2, 1), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5)
    ]))
    story.append(detail_table)

    story.append(Spacer(1, 8 * mm))
    security_note = "<b>Zero-Knowledge Security Assurance:</b> This report intentionally excludes all plaintext cryptographic secrets, master keys, and passwords."
    note_table = Table([[Paragraph(security_note, normal_style)]], colWidths=[170 * mm])
    note_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fef3c7")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#f59e0b")),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8)
    ]))
    story.append(note_table)
    story.append(Spacer(1, 8 * mm))
    story.append(Paragraph("Generated by SecureVault Enterprise Suite", subtitle_style))

    document.build(story)
    buffer.seek(0)
    return buffer


# ============================================================
# MAIN
# ============================================================

def show(user):
    load_css()
    db = SessionLocal()

    try:
        render_html("""
        <div style="margin-bottom: 20px;">
            <div style="display:flex;align-items:center;gap:12px;">
                <h1 class="report-title">❤️ Password Health & Security Posture</h1>
                <div class="status-pill pill-cyber">
                    <span class="pill-dot dot-blue"></span> Live Vault Diagnostics
                </div>
            </div>
            <p class="report-subtitle">Dynamic vulnerability analysis, entropy distribution, and health telemetry for your digital vault.</p>
        </div>
        """)

        user_vault = db.query(models.Vault).filter(models.Vault.owner_id == user["id"]).first()
        if not user_vault:
            st.info("No vault found. Please create or access passwords first.")
            return

        passwords = db.query(models.Password).filter(models.Password.vault_id == user_vault.id).all()
        if not passwords:
            st.info("No passwords found in your vault. Add credentials to generate health telemetry.")
            return

        GLOBAL_KEY = KeyManager.derive_key("FIXED_KEY_123", "FIXED_SALT_123")

        decrypted_passwords = []
        for p in passwords:
            try:
                plain_pw = VaultEncryption.decrypt_data(p.encrypted_password, p.encryption_nonce, GLOBAL_KEY)
                strength = estimate_strength(plain_pw)
                expiry_datetime = normalize_datetime(p.expiry_date)
                decrypted_passwords.append({
                    "id": p.id, "title": p.title, "username": p.username,
                    "password": plain_pw, "strength_score": strength["score"],
                    "strength_label": strength["label"], "expiry_date": expiry_datetime,
                    "category": p.category,
                })
            except Exception:
                continue

        if not decrypted_passwords:
            st.warning("Could not decrypt any passwords for health evaluation.")
            return

        total = len(decrypted_passwords)
        strong_count = sum(1 for p in decrypted_passwords if p["strength_score"] >= 70)
        medium_count = sum(1 for p in decrypted_passwords if 40 <= p["strength_score"] < 70)
        weak_count = sum(1 for p in decrypted_passwords if p["strength_score"] < 40)

        password_counter = Counter(p["password"] for p in decrypted_passwords)
        reused_count = sum(1 for p in decrypted_passwords if password_counter[p["password"]] > 1)

        now = datetime.datetime.now()
        thirty_days_from_now = now + datetime.timedelta(days=30)

        expired_count = sum(1 for p in decrypted_passwords if p["expiry_date"] and p["expiry_date"] < now)
        expiring_soon_count = sum(1 for p in decrypted_passwords if p["expiry_date"] and now <= p["expiry_date"] <= thirty_days_from_now)

        strong_pct = round((strong_count / total) * 100) if total else 0
        medium_pct = round((medium_count / total) * 100) if total else 0
        weak_pct = round((weak_count / total) * 100) if total else 0
        reused_pct = round((reused_count / total) * 100) if total else 0
        expired_pct = round((expired_count / total) * 100) if total else 0
        expiring_pct = round((expiring_soon_count / total) * 100) if total else 0

        # Exact dynamic calculation preserved
        health_score = 100
        health_score -= weak_pct * 0.45
        health_score -= reused_pct * 0.25
        health_score -= expired_pct * 0.20
        health_score -= expiring_pct * 0.10
        health_score = max(0, min(100, round(health_score)))

        status_label = get_health_status(health_score)
        score_color = get_health_color(health_score)
        status_badge = get_health_badge(health_score)

        # --------------------------------------------------------
        # 1. TOP TELEMETRY METRICS CARDS
        # --------------------------------------------------------
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f'<div class="report-info"><div class="report-info-value" style="color:#f8fafc;">{total}</div><div class="report-info-label">🔐 Total Passwords</div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="report-info"><div class="report-info-value" style="color:#10b981;">{strong_count}</div><div class="report-info-label">🛡️ Strong Passwords</div></div>', unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div class="report-info"><div class="report-info-value" style="color:#f59e0b;">{medium_count}</div><div class="report-info-label">⚠️ Medium Passwords</div></div>', unsafe_allow_html=True)
        with c4:
            st.markdown(f'<div class="report-info"><div class="report-info-value" style="color:#f43f5e;">{weak_count}</div><div class="report-info-label">🚨 Weak Passwords</div></div>', unsafe_allow_html=True)

        st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

        c5, c6, c7 = st.columns(3)
        with c5:
            st.markdown(f'<div class="report-info"><div class="report-info-value" style="color:#f97316;">{reused_count}</div><div class="report-info-label">🔄 Reused Passwords</div></div>', unsafe_allow_html=True)
        with c6:
            st.markdown(f'<div class="report-info"><div class="report-info-value" style="color:#eab308;">{expiring_soon_count}</div><div class="report-info-label">⏰ Expiring Soon (30d)</div></div>', unsafe_allow_html=True)
        with c7:
            st.markdown(f'<div class="report-info"><div class="report-info-value" style="color:#ef4444;">{expired_count}</div><div class="report-info-label">❌ Expired Passwords</div></div>', unsafe_allow_html=True)

        st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)

        # --------------------------------------------------------
        # 2. INTERACTIVE DONUT CHART & SCORE (Requirement 6)
        # --------------------------------------------------------
        score_col, chart_col = st.columns([1, 1.3], gap="medium")

        with score_col:
            st.markdown('<div class="section-title">🛡️ Password Health Score</div>', unsafe_allow_html=True)
            render_html(f"""
            <div class="report-card">
                <div style="display:flex;justify-content:center;margin-bottom:12px;">
                    {render_3d_shield(size=56)}
                </div>
                <div class="report-score" style="color:{score_color};">{health_score}</div>
                <div class="report-score-label">Health Score out of 100</div>
                <div style="display:flex;justify-content:center;margin-top:10px;">
                    <span class="status-pill {status_badge}">
                        <span class="pill-dot dot-green"></span> {status_label}
                    </span>
                </div>
                <div style="margin-top:20px; background:rgba(15,23,42,0.8); height:10px; border-radius:10px; overflow:hidden; border:1px solid rgba(56,189,248,0.2);">
                    <div style="width:{health_score}%; height:100%; background:linear-gradient(90deg, #0284c7, {score_color}); border-radius:10px;"></div>
                </div>
            </div>
            """)

        with chart_col:
            st.markdown('<div class="section-title">📊 Interactive Distribution</div>', unsafe_allow_html=True)
            with st.container(border=True):
                fig = go.Figure()
                fig.add_trace(
                    go.Pie(
                        labels=["Strong", "Medium", "Weak"],
                        values=[strong_count, medium_count, weak_count],
                        hole=0.68,
                        sort=False,
                        textinfo="none",
                        hovertemplate="<b>%{label} Passwords</b><br>Count: %{value}<br>Proportion: %{percent}<extra></extra>",
                        marker=dict(
                            colors=["#10b981", "#f59e0b", "#f43f5e"],
                            line=dict(color="#060a14", width=3)
                        )
                    )
                )
                fig.add_annotation(
                    x=0.5, y=0.5,
                    text=f"<b>{total}</b><br><span style='font-size:11px;color:#94a3b8;'>Credentials</span>",
                    showarrow=False,
                    font=dict(size=22, color="#f8fafc", family="Inter")
                )
                fig.update_layout(
                    height=240,
                    margin=dict(l=0, r=0, t=10, b=10),
                    showlegend=True,
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=-0.15,
                        xanchor="center",
                        x=0.5,
                        font=dict(size=12, color="#cbd5e1")
                    ),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)"
                )
                st.plotly_chart(
                    fig,
                    use_container_width=True,
                    config={"displayModeBar": False, "responsive": True},
                    key="plotly_health_chart"
                )

        st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

        # --------------------------------------------------------
        # 3. SECURITY FINDINGS
        # --------------------------------------------------------
        st.markdown('<div class="section-title">🔍 Security Findings & Automated Diagnostics</div>', unsafe_allow_html=True)
        findings = []
        if strong_count > 0:
            findings.append((f"{strong_count} password(s) have verified strong cryptographic entropy.", "pill-secure", "🛡️"))
        if medium_count > 0:
            findings.append((f"{medium_count} password(s) have medium strength and could be hardened.", "pill-warning", "⚠️"))
        if weak_count > 0:
            findings.append((f"{weak_count} password(s) are weak and vulnerable to brute-force or dictionary attacks.", "pill-danger", "🚨"))
        if reused_count > 0:
            findings.append((f"{reused_count} credential(s) share identical passwords. Reusing credentials invites credential stuffing attacks.", "pill-warning", "🔄"))
        if expiring_soon_count > 0:
            findings.append((f"{expiring_soon_count} credential(s) expire within the next 30 days.", "pill-cyber", "⏰"))
        if expired_count > 0:
            findings.append((f"{expired_count} credential(s) have passed their validity window and should be updated.", "pill-danger", "❌"))
        if not findings:
            findings.append(("All vault credentials currently meet baseline security policies.", "pill-secure", "✅"))

        for text, badge, icon in findings:
            render_html(f"""
            <div class="finding">
                <span style="font-size:16px;">{icon}</span>
                <span style="color:#f1f5f9;font-weight:500;">{escape(text)}</span>
            </div>
            """)

        st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

        # --------------------------------------------------------
        # 4. DETAILED CREDENTIAL TABLE
        # --------------------------------------------------------
        st.markdown('<div class="section-title">📋 Credential Audit Records</div>', unsafe_allow_html=True)

        table_data = []
        for p in decrypted_passwords:
            expiry = p["expiry_date"]
            if not expiry:
                expiry_status = "No Expiry"
            elif expiry < now:
                expiry_status = "Expired"
            elif expiry <= thirty_days_from_now:
                expiry_status = "Expiring Soon"
            else:
                expiry_status = "Safe"

            reused_status = "Yes" if password_counter[p["password"]] > 1 else "No"
            table_data.append({
                "Title": p["title"],
                "Username": p["username"],
                "Strength": p["strength_label"],
                "Score": f"{p['strength_score']}/100",
                "Reused": reused_status,
                "Expiry Status": expiry_status,
            })

        st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)

        st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

        # --------------------------------------------------------
        # 5. PDF EXPORT
        # --------------------------------------------------------
        st.markdown('<div class="section-title">📄 Export Security Audit Report</div>', unsafe_allow_html=True)
        with st.container(border=True):
            render_html("""
            <div style="font-size:13.5px;color:#cbd5e1;margin-bottom:12px;">
                Download an immutable cryptographic security posture audit in PDF format. This report compiles your health score, credential statistics, entropy distribution, and findings. Plaintext passwords are never included.
            </div>
            """)

            pdf_data = generate_pdf_report(
                user=user, decrypted_passwords=decrypted_passwords, total=total,
                strong_count=strong_count, medium_count=medium_count, weak_count=weak_count,
                reused_count=reused_count, expiring_soon_count=expiring_soon_count,
                expired_count=expired_count, health_score=health_score,
                status_label=status_label, now=now, thirty_days_from_now=thirty_days_from_now
            )

            filename_date = datetime.datetime.now().strftime("%Y-%m-%d")
            st.download_button(
                label="📄 Download Password Health PDF Report",
                data=pdf_data,
                file_name=f"SecureVault_Health_Report_{filename_date}.pdf",
                mime="application/pdf",
                use_container_width=True
            )

    except Exception as exc:
        st.error(f"Error generating password health report: {exc}")
    finally:
        db.close()