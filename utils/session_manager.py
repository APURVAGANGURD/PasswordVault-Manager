import streamlit as st
import logging

logger = logging.getLogger(__name__)

class SessionManager:
    @staticmethod
    def initialize_session():
        """Initialize session state variables"""
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
        if 'user_data' not in st.session_state:
            st.session_state.user_data = None
        if 'mfa_verified' not in st.session_state:
            st.session_state.mfa_verified = False
        if 'page' not in st.session_state:
            st.session_state.page = 'login'
    
    @staticmethod
    def is_authenticated():
        return st.session_state.get('authenticated', False)
    
    @staticmethod
    def is_mfa_verified():
        return st.session_state.get('mfa_verified', False)
    
    @staticmethod
    def get_user():
        return st.session_state.get('user_data', None)
    
    @staticmethod
    def get_user_role():
        user = st.session_state.get('user_data', None)
        return user['role'] if user else None
    
    @staticmethod
    def set_user(user_data):
        st.session_state.user_data = user_data
        st.session_state.authenticated = True
    
    @staticmethod
    def set_mfa_verified(status=True):
        st.session_state.mfa_verified = status
    
    @staticmethod
    def set_page(page):
        st.session_state.page = page
    
    @staticmethod
    def get_current_page():
        return st.session_state.get('page', 'login')
    
    @staticmethod
    def clear_session():
        keys_to_clear = ['authenticated', 'user_data', 'mfa_verified', 'page']
        for key in keys_to_clear:
            if key in st.session_state:
                if key == 'authenticated':
                    st.session_state[key] = False
                elif key == 'user_data':
                    st.session_state[key] = None
                elif key == 'mfa_verified':
                    st.session_state[key] = False
                elif key == 'page':
                    st.session_state[key] = 'login'
        logger.info("Session cleared successfully")
        return True