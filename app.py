import streamlit as st # type: ignore
import sys
import os

# Ensure the core/ directory is reachable
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from core import auth # type: ignore

# Top-level page configuration MUST be the first Streamlit command
st.set_page_config(page_title="AI Career Recommender | Kenyan Edition", layout="wide", page_icon="🎓")

# Ensure the database tables exist
auth.init_db()

# Initialize session state for authentication
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

# Define our pages
login_page = st.Page("src/login.py", title="Sign In / Register", icon="🔐")
main_page = st.Page("src/main_app.py", title="Career Engine", icon="🎓")

# Configure the router based on login state
if st.session_state["authenticated"]:
    pg = st.navigation([main_page])
else:
    # Restrict to login page only
    pg = st.navigation([login_page])

# Run the selected page
pg.run()