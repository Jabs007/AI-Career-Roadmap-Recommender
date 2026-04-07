import streamlit as st # type: ignore
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core import auth # type: ignore

# Top-level page configuration
st.set_page_config(page_title="System Command Center", layout="wide", page_icon="🛡️")

# Ensure the database tables exist
auth.init_db()

# Initialize Admin session state
if "admin_authenticated" not in st.session_state:
    st.session_state["admin_authenticated"] = False

# Pages specialized for Admin
login_page = st.Page("admin_login_page.py", title="Gateway", icon="🔒")
dashboard_page = st.Page("admin_dashboard.py", title="Terminal", icon="⚙️")

# Strict isolation routing
if st.session_state["admin_authenticated"]:
    pg = st.navigation([dashboard_page])
else:
    pg = st.navigation([login_page])

# Run the router
pg.run()
