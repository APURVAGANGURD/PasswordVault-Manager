# ============================================================
# pages/login.py
# SecureVault Manager - Modern Cybersecurity Login
# ============================================================

import streamlit as st
import sys
import os
import datetime
import time

sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

from auth.authentication import (
    authenticate_user,
    generate_otp,
    send_mfa_email
)
from utils.theme import inject_cyber_theme, render_3d_shield, render_html


def load_css():
    inject_cyber_theme()
    render_html("""
    <style>
        .login-hero-container {
            padding: 20px 0;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        .login-brand-title {
            font-size: 38px;
            font-weight: 900;
            color: #f8fafc;
            letter-spacing: -1px;
            margin: 14px 0 6px 0;
            line-height: 1.15;
            background: linear-gradient(135deg, #f8fafc 0%, #38bdf8 50%, #06b6d4 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .login-tagline {
            font-size: 17px;
            font-weight: 600;
            color: #38bdf8;
            margin-bottom: 12px;
            letter-spacing: -0.2px;
        }
        .login-description {
            font-size: 13.5px;
            color: #94a3b8;
            line-height: 1.6;
            margin-bottom: 24px;
        }
        .login-feature-item {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 13px;
            color: #cbd5e1;
            margin-bottom: 10px;
        }
        .feature-icon-badge {
            background: rgba(6, 182, 212, 0.12);
            border: 1px solid rgba(6, 182, 212, 0.3);
            border-radius: 8px;
            padding: 4px 8px;
            font-size: 14px;
        }
        .login-card {
            background: rgba(15, 23, 42, 0.78) !important;
            backdrop-filter: blur(20px) !important;
            border: 1px solid rgba(56, 189, 248, 0.22) !important;
            border-radius: 16px !important;
            padding: 28px 26px !important;
            box-shadow: 0 16px 40px rgba(0, 0, 0, 0.45), inset 0 0 16px rgba(56, 189, 248, 0.05) !important;
        }
    </style>
    """)


def show():
    load_css()

    st.markdown("<div style='height: 40px;'></div>", unsafe_allow_html=True)

    col_brand, col_form = st.columns([1.1, 1.0], gap="large")

    with col_brand:
        render_html(f"""
        <div class="login-hero-container">
            {render_3d_shield(size=84)}
            <div class="login-brand-title">SecureVault</div>
            <div class="login-tagline">Secure. Simple. Protected.</div>
            <p class="login-description">
                Next-generation zero-knowledge credential orchestration designed for personal users and security-conscious enterprise teams.
            </p>
            <div class="login-feature-item">
                <span class="feature-icon-badge">🛡️</span>
                <span>Zero-Knowledge AES-256-GCM Vault Encryption</span>
            </div>
            <div class="login-feature-item">
                <span class="feature-icon-badge">🔑</span>
                <span>Argon2id Memory-Hard Key Derivation</span>
            </div>
            <div class="login-feature-item">
                <span class="feature-icon-badge">👥</span>
                <span>Role-Based Access Control & Department Isolation</span>
            </div>
            <div class="login-feature-item">
                <span class="feature-icon-badge">📜</span>
                <span>Tamper-Resistant Security Audit Logging</span>
            </div>
        </div>
        """)

    with col_form:
        render_html("""
        <div class="login-card">
            <div style="font-size: 22px; font-weight: 800; color: #f8fafc; margin-bottom: 4px;">Sign In</div>
            <div style="font-size: 13px; color: #94a3b8; margin-bottom: 20px;">Access your encrypted digital vault</div>
        </div>
        """)

        with st.form("login_form"):
            email = st.text_input(
                "Email Address",
                placeholder="you@company.com",
                key="login_email_input"
            )

            password = st.text_input(
                "Master Password",
                type="password",
                placeholder="••••••••••••",
                key="login_pwd_input"
            )

            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            with col1:
                login_button = st.form_submit_button(
                    "Sign In 🔓",
                    use_container_width=True
                )
            with col2:
                forgot_button = st.form_submit_button(
                    "Forgot Password?",
                    use_container_width=True
                )

        # ====================================================
        # AUTHENTICATION LOGIC (100% PRESERVED)
        # ====================================================
        if login_button:
            if not email or not password:
                st.error("Please enter both email and password.")
            else:
                user, message = authenticate_user(email, password)

                if user:
                    # MFA Enabled
                    if user.get("mfa_enabled", False):
                        otp = generate_otp()
                        success, email_message = send_mfa_email(user["email"], otp)

                        if not success:
                            st.error("Unable to dispatch OTP verification email.")
                            st.caption(email_message)
                        else:
                            st.session_state["pending_user"] = user
                            st.session_state["pending_otp"] = otp
                            st.session_state["pending_otp_created"] = time.time()
                            st.session_state["mfa_attempts"] = 0
                            st.session_state["mfa_pending"] = True
                            st.session_state["page"] = "mfa"
                            st.rerun()
                    # MFA Disabled
                    else:
                        st.session_state["user"] = user
                        st.session_state["login_time"] = datetime.datetime.now()
                        st.session_state["mfa_pending"] = False
                        st.rerun()
                else:
                    st.error(message)

        if forgot_button:
            st.session_state["page"] = "forgot"
            st.rerun()

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        st.markdown("<div style='text-align: center; color: #64748b; font-size: 13px;'>Don't have an account yet?</div>", unsafe_allow_html=True)
        st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)

        if st.button("Create SecureVault Account", use_container_width=True, key="login_create_acc"):
            st.session_state["page"] = "register"
            st.rerun()