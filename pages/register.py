# ============================================================
# pages/register.py
# SecureVault Manager - Modern Cybersecurity Registration
# ============================================================

import streamlit as st
import sys, os, time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth.authentication import register_user
from security.security_utils import validate_email, validate_password_strength
from security.password_strength import estimate_strength
from utils.theme import inject_cyber_theme, render_3d_shield, render_3d_lock, render_html


def show():
    inject_cyber_theme()

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    center_col_left, center_col, center_col_right = st.columns([1, 2.2, 1])

    with center_col:
        render_html(f"""
        <div style="text-align: center; margin-bottom: 24px;">
            {render_3d_shield(size=68)}
            <h1 style="font-size: 28px; font-weight: 800; color: #f8fafc; margin: 12px 0 4px 0; letter-spacing: -0.5px;">Create SecureVault Account</h1>
            <p style="font-size: 13.5px; color: #94a3b8; margin: 0;">Establish your zero-knowledge cryptographic vault</p>
        </div>
        """)

        with st.container(border=True):
            render_html("""
            <div style='font-size: 12px; font-weight: 700; color: #38bdf8; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 12px; display: flex; align-items: center; gap: 8px;'>
                <span>🗂️</span> 1. Account Architecture
            </div>
            """)
            
            account_type = st.selectbox(
                "Account Type",
                ["PERSONAL", "ORGANIZATION"],
                help="Select PERSONAL for individual private vaults, or ORGANIZATION for enterprise team collaboration."
            )

            role = "PERSONAL_USER"
            org_name = ""

            if account_type == "ORGANIZATION":
                st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
                org_col1, org_col2 = st.columns(2)
                with org_col1:
                    org_name = st.text_input("🏢 Organization Name *", placeholder="Acme Cybersec Inc.")
                with org_col2:
                    role = st.selectbox("Initial Role", ["ADMIN", "MANAGER", "EMPLOYEE"])

            st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
            render_html("""
            <div style='font-size: 12px; font-weight: 700; color: #38bdf8; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 12px; display: flex; align-items: center; gap: 8px;'>
                <span>🔐</span> 2. Cryptographic Credentials
            </div>
            """)

            with st.form("register_form"):
                name = st.text_input("👤 Full Name *", placeholder="Alice Vance")
                email = st.text_input("✉️ Email Address *", placeholder="alice@example.com")

                col1, col2 = st.columns(2)
                with col1:
                    password = st.text_input("🔑 Master Password *", type="password", placeholder="••••••••••••")
                with col2:
                    confirm_password = st.text_input("🔒 Confirm Password *", type="password", placeholder="••••••••••••")

                render_html("""
                <div style="background: rgba(13, 22, 42, 0.6); border: 1px solid rgba(56, 189, 248, 0.14); border-radius: 8px; padding: 10px 12px; margin-top: 6px; margin-bottom: 12px; font-size: 11.5px; color: #94a3b8;">
                    🛡️ <b>Zero-Knowledge Guarantee</b>: Your master password derives your encryption key via <b>Argon2id</b> and is never sent to or stored on the server.
                </div>
                """)

                submit = st.form_submit_button("Create Encrypted Vault 🛡️", use_container_width=True)

                if submit:
                    if not name.strip():
                        st.error("Full Name is required.")
                    elif not email.strip():
                        st.error("Email Address is required.")
                    elif not password:
                        st.error("Master Password is required.")
                    elif password != confirm_password:
                        st.error("Passwords do not match.")
                    elif not validate_email(email):
                        st.error("Invalid email address format.")
                    elif account_type == "ORGANIZATION" and not org_name.strip():
                        st.error("Organization Name is required for organization accounts.")
                    else:
                        mapped_role = "USER" if role == "EMPLOYEE" else role
                        user, msg = register_user(name.strip(), email.strip(), password, account_type, mapped_role, org_name.strip())
                        if user:
                            st.success("Vault account successfully initialized! Redirecting to login...")
                            time.sleep(1.2)
                            st.session_state['page'] = "login"
                            st.rerun()
                        else:
                            st.error(msg)

        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
        if st.button("Already have an account? Sign In", use_container_width=True, key="reg_back_login"):
            st.session_state['page'] = "login"
            st.rerun()