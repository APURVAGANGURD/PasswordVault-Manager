# ============================================================
# pages/session_expired.py
# SecureVault Manager - Session Expired Notice
# ============================================================

import streamlit as st
from utils.theme import inject_cyber_theme, render_3d_lock, render_html


def load_css():
    inject_cyber_theme()
    render_html("""
    <style>
        .expired-wrap {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
            padding: 60px 20px 30px 20px;
        }
        .expired-title {
            font-size: 26px;
            font-weight: 800;
            color: #f8fafc;
            margin: 16px 0 8px 0;
            letter-spacing: -0.5px;
        }
        .expired-text {
            font-size: 14px;
            color: #94a3b8;
            max-width: 440px;
            line-height: 1.6;
            margin-bottom: 24px;
        }
    </style>
    """)


def show():
    load_css()
    render_html(f"""
    <div class="expired-wrap">
        {render_3d_lock(size=72)}
        <div class="expired-title">Security Session Expired</div>
        <div class="expired-text">
            For your security protection, digital vault sessions automatically timeout after 30 minutes of inactivity to safeguard cryptographic keys and master credentials.
        </div>
    </div>
    """)

    _, c, _ = st.columns([1, 1, 1])
    with c:
        if st.button("Re-authenticate & Sign In 🔐", use_container_width=True, type="primary"):
            st.session_state.clear()
            st.session_state["page"] = "login"
            st.rerun()