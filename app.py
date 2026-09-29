import streamlit as st
from database.connection import init_db
init_db()

from pages.router import render

from utils.theme import render_html

def main():
    # CRITICAL: Set initial_page and disable automatic sidebar navigation
    st.set_page_config(
        page_title="SecureVault Manager", 
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={}
    )
    
    # Hide Streamlit's automatic sidebar pages
    render_html("""
    <style>
        [data-testid="stSidebarNav"] {display: none;}
    </style>
    """)
    
    render()

if __name__ == "__main__":
    main()