import streamlit as st
import sys, os, pandas as pd
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.team_management import get_shared_passwords_for_user, decrypt_shared_password

def show(user):
    st.title("Shared Passwords")
    
    shares = get_shared_passwords_for_user(user)
    if not shares:
        st.info("No passwords have been shared with you.")
        return
    
    st.dataframe(pd.DataFrame([{"Title": s['title'], "Team": s['team'], "Shared By": s['shared_by'], "Permission": s['permission']} for s in shares]), use_container_width=True)
    
    selected = st.selectbox("Select Password to View", [s['id'] for s in shares])
    if selected and st.button("👁️ View Password"):
        decrypted, permission = decrypt_shared_password(user, selected)
        if decrypted:
            st.success(f"Password: {decrypted}")
        else:
            st.error(permission)