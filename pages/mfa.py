# ============================================================
# pages/mfa.py
# SecureVault Manager - Email OTP Verification
# ============================================================

import streamlit as st
import sys
import os
import time
import datetime

sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

from auth.mfa import (
    generate_otp,
    verify_otp
)

from auth.authentication import (
    send_mfa_email
)
from utils.theme import inject_cyber_theme, render_3d_shield, render_html


OTP_EXPIRY_SECONDS = 300
MAX_ATTEMPTS = 5


def show():
    inject_cyber_theme()

    st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)

    _, col_center, _ = st.columns([1, 1.8, 1])

    with col_center:
        pending_user = st.session_state.get("pending_user")
        pending_otp = st.session_state.get("pending_otp")
        otp_created = st.session_state.get("pending_otp_created")

        # --------------------------------------------------------
        # SAFETY CHECK
        # --------------------------------------------------------
        if not pending_user or not pending_otp:
            st.error("No active OTP verification session.")
            if st.button("← Back to Login", use_container_width=True):
                st.session_state.clear()
                st.session_state["page"] = "login"
                st.rerun()
            return

        render_html(f"""
        <div style="text-align: center; margin-bottom: 24px;">
            {render_3d_shield(size=64)}
            <h1 style="font-size: 26px; font-weight: 800; color: #f8fafc; margin: 12px 0 4px 0;">Two-Factor Authentication</h1>
            <p style="font-size: 13.5px; color: #94a3b8; margin: 0;">Identity verification for digital vault access</p>
        </div>
        """)

        with st.container(border=True):
            # --------------------------------------------------------
            # OTP EXPIRATION
            # --------------------------------------------------------
            elapsed = time.time() - otp_created
            remaining = max(0, OTP_EXPIRY_SECONDS - int(elapsed))

            if remaining <= 0:
                st.error("Your verification OTP has expired.")
                if st.button("Send New OTP", type="primary", use_container_width=True):
                    new_otp = generate_otp()
                    success, message = send_mfa_email(pending_user["email"], new_otp)
                    if success:
                        st.session_state["pending_otp"] = new_otp
                        st.session_state["pending_otp_created"] = time.time()
                        st.session_state["mfa_attempts"] = 0
                        st.rerun()
                    else:
                        st.error(message)

                if st.button("Cancel Login", use_container_width=True):
                    st.session_state.clear()
                    st.session_state["page"] = "login"
                    st.rerun()
                return

            # --------------------------------------------------------
            # MASK EMAIL
            # --------------------------------------------------------
            email = pending_user["email"]
            if "@" in email:
                username, domain = email.split("@", 1)
                masked_email = (username[:2] + "***@" + domain) if len(username) > 2 else ("***@" + domain)
            else:
                masked_email = "***"

            render_html(f"""
            <div style="background: rgba(13, 22, 42, 0.6); border: 1px solid rgba(56, 189, 248, 0.16); border-radius: 9px; padding: 12px 14px; margin-bottom: 14px;">
                <div style="font-size: 13px; color: #cbd5e1;">A 6-digit security OTP was sent to:</div>
                <div style="font-size: 14px; font-weight: 700; color: #38bdf8; font-family: 'JetBrains Mono', monospace; margin-top: 2px;">{masked_email}</div>
                <div style="font-size: 11px; color: #94a3b8; margin-top: 6px;">⏱️ Code expires in <b>{remaining // 60}:{remaining % 60:02d}</b></div>
            </div>
            """)

            with st.form("email_otp_form"):
                code = st.text_input(
                    "6-Digit Verification Code",
                    max_chars=6,
                    placeholder="123456",
                    help="Enter the 6-digit code received via email"
                )
                verify_button = st.form_submit_button("Verify & Open Vault 🔓", use_container_width=True)

            if verify_button:
                attempts = st.session_state.get("mfa_attempts", 0)
                if attempts >= MAX_ATTEMPTS:
                    st.error("Too many incorrect attempts. Please request a new OTP.")
                    return

                if not code:
                    st.error("Please enter the verification code.")
                    return

                if len(code.strip()) != 6 or not code.strip().isdigit():
                    st.error("OTP must contain exactly 6 numeric digits.")
                    return

                if verify_otp(code, pending_otp):
                    st.session_state.pop("mfa_pending", None)
                    st.session_state.pop("pending_otp", None)
                    st.session_state.pop("pending_otp_created", None)
                    st.session_state.pop("mfa_attempts", None)
                    st.session_state["user"] = pending_user
                    st.session_state["login_time"] = datetime.datetime.now()
                    st.success("Identity verified. Opening digital vault...")
                    time.sleep(0.7)
                    st.rerun()
                else:
                    attempts += 1
                    st.session_state["mfa_attempts"] = attempts
                    rem = MAX_ATTEMPTS - attempts
                    st.error("Invalid verification code.")
                    if rem > 0:
                        st.caption(f"{rem} attempt(s) remaining.")

            st.write("")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Resend Code", use_container_width=True):
                    new_otp = generate_otp()
                    success, message = send_mfa_email(pending_user["email"], new_otp)
                    if success:
                        st.session_state["pending_otp"] = new_otp
                        st.session_state["pending_otp_created"] = time.time()
                        st.session_state["mfa_attempts"] = 0
                        st.success("New OTP has been dispatched.")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error(message)
            with col2:
                if st.button("Cancel", use_container_width=True):
                    st.session_state.clear()
                    st.session_state["page"] = "login"
                    st.rerun()