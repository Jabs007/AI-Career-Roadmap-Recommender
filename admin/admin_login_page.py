import streamlit as st # type: ignore
import os

st.markdown(
    """
    <div style='text-align: center; margin-top: 40px;'>
        <h1 style='color: #dc2626;'>System Administration</h1>
        <p style='color: #64748b;'>Enter standard high-clearance credentials.</p>
    </div>
    """, unsafe_allow_html=True
)

# Fetch master credentials securely
MASTER_ADMIN_USER = os.getenv("MASTER_ADMIN_USER", "admin")
MASTER_ADMIN_PASS = os.getenv("MASTER_ADMIN_PASS", "jabsadmin123")

c1, main_col, c3 = st.columns([1, 2, 1])
with main_col:
    with st.form("admin_login_form"):
        st.subheader("Gateway Authentication")
        username = st.text_input("Standard Admin Username")
        password = st.text_input("Standard Password", type="password")
        submit = st.form_submit_button("Authenticate")
        
        if submit:
            if not username or not password:
                st.warning("Please enter credentials.")
            elif username == MASTER_ADMIN_USER and password == MASTER_ADMIN_PASS:
                st.session_state["admin_authenticated"] = True
                st.session_state["admin_username"] = username
                st.success("Clearance Granted!")
                st.rerun()
            else:
                st.error("Access Denied. Invalid admin credentials.")
