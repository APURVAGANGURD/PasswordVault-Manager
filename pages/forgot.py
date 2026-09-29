# ============================================================
# pages/forgot.py
# SecureVault Manager - Password Recovery
# ============================================================

import streamlit as st
import sys, os, time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth.authentication import generate_reset_token, reset_password_with_token
from security.security_utils import validate_password_strength
from utils.theme import inject_cyber_theme, render_3d_lock, render_html

def show():
    inject_cyber_theme()
    
    st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)
    
    _, col_center, _ = st.columns([1, 1.8, 1])
    
    with col_center:
        render_html(f"""
        <div style="text-align: center; margin-bottom: 24px;">
            {render_3d_lock(size=64)}
            <h1 style="font-size: 26px; font-weight: 800; color: #f8fafc; margin: 12px 0 4px 0;">Credential Recovery</h1>
            <p style="font-size: 13.5px; color: #94a3b8; margin: 0;">Reset your SecureVault master access key</p>
        </div>
        """)
        
        with st.container(border=True):
            tab1, tab2 = st.tabs(["✉️ Request Token", "🔑 Reset Password"])
            
            with tab1:
                st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
                with st.form("forgot_form"):
                    email = st.text_input("Registered Email Address", placeholder="you@company.com")
                    submit = st.form_submit_button("Send Recovery Token", use_container_width=True)
                    if submit:
                        if not email.strip():
                            st.error("Please enter your email address.")
                        else:
                            success, msg = generate_reset_token(email.strip())
                            if success:
                                st.success(msg)
                            else:
                                st.error(msg)
            
            with tab2:
                st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
                with st.form("reset_form"):
                    token = st.text_input("Reset Token (from email)", placeholder="Paste token here")
                    new_pw = st.text_input("New Master Password", type="password", placeholder="••••••••••••")
                    confirm_pw = st.text_input("Confirm New Password", type="password", placeholder="••••••••••••")
                    reset_btn = st.form_submit_button("Reset Master Password 🛡️", use_container_width=True)
                    if reset_btn:
                        if not token.strip():
                            st.error("Reset token is required.")
                        elif not new_pw:
                            st.error("New master password is required.")
                        elif new_pw != confirm_pw:
                            st.error("Passwords do not match.")
                        else:
                            success, msg = reset_password_with_token(token.strip(), new_pw)
                            if success:
                                st.success(msg)
                                time.sleep(1.5)
                                st.session_state['page'] = "login"
                                st.rerun()
                            else:
                                st.error(msg)
        
        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
        if st.button("← Back to Sign In", use_container_width=True, key="forgot_back_login"):
            st.session_state['page'] = "login"
            st.rerun()