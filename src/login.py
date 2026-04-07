import streamlit as st # type: ignore
import re 
import os
import requests # type: ignore
import urllib.parse
from core.auth import authenticate_user, create_user, get_or_create_google_user, is_user_admin # type: ignore

# ---------- GOOGLE OAUTH SETTINGS ----------
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = "http://localhost:8501"

def google_login_url():
    auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent"
    }
    return f"{auth_url}?{urllib.parse.urlencode(params)}"

def get_google_user_info(code):
    token_url = "https://oauth2.googleapis.com/token"
    data = {"code": code, "client_id": GOOGLE_CLIENT_ID, "client_secret": GOOGLE_CLIENT_SECRET, "redirect_uri": REDIRECT_URI, "grant_type": "authorization_code"}
    try:
        res = requests.post(token_url, data=data)
        if not res.ok: return None
        access_token = res.json().get("access_token")
        if not access_token: return None
        res2 = requests.get("https://www.googleapis.com/oauth2/v2/userinfo", headers={"Authorization": f"Bearer {access_token}"})
        if not res2.ok: return None
        return res2.json()
    except Exception as e:
        print(f"Google Token Exchange Error: {e}")
        return None

# ---------- OAUTH REDIRECT HANDLER ----------
qp = st.query_params if hasattr(st, 'query_params') else st.experimental_get_query_params()
if "code" in qp:
    code = qp["code"]
    if isinstance(code, list): code = code[0]
    with st.spinner("Authenticating with Google..."):
        user_info = get_google_user_info(code)
        if user_info:
            email = user_info.get("email")
            first_name = user_info.get("given_name", "")
            last_name = user_info.get("family_name", "")
            username = get_or_create_google_user(email, first_name, last_name)
            if username:
                st.session_state["authenticated"] = True
                st.session_state["username"] = username
                st.session_state["is_admin"] = is_user_admin(username)
                if hasattr(st, 'query_params'): st.query_params.clear()
                else: st.experimental_set_query_params()
                st.rerun()
            else:
                st.error("Failed to login via Google database.")
        else:
            st.error("Failed to authenticate with Google API.")

# ---------- SESSION INIT ----------
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "username" not in st.session_state:
    st.session_state["username"] = None

# ---------- HELPER FUNCTIONS ----------
def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

# ---------- HEADER / PREMIUM UI ----------
st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Inter:wght@300;400;500;700&display=swap');

        /* Global Background */
        .stApp {
            background: linear-gradient(135deg, #0f172a 0%, #4338ca 100%);
            font-family: 'Inter', sans-serif;
        }

        /* Animated Header */
        @keyframes fadeInDown {
            from { opacity: 0; transform: translateY(-30px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .login-header {
            text-align: center;
            margin-top: 5vh;
            margin-bottom: 40px;
            animation: fadeInDown 0.8s cubic-bezier(0.2, 0.8, 0.2, 1);
        }
        
        .title-glow {
            font-family: 'Outfit', sans-serif !important;
            font-weight: 800 !important;
            color: #ffffff !important;
            font-size: 3.5rem;
            margin-bottom: 10px;
            background: linear-gradient(to right, #ffffff, #a5b4fc);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-shadow: 0 10px 30px rgba(99, 102, 241, 0.4);
        }

        .subtitle {
            color: #c7d2fe;
            font-size: 1.15rem;
            font-weight: 300;
        }

        /* Glassmorphism Forms */
        div[data-testid="stForm"] {
            background: rgba(255, 255, 255, 0.03) !important;
            backdrop-filter: blur(20px) saturate(160%) !important;
            -webkit-backdrop-filter: blur(20px) saturate(160%) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 24px !important;
            padding: 40px 30px !important;
            box-shadow: 0 30px 60px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255,255,255,0.1) !important;
            animation: fadeInDown 1s cubic-bezier(0.2, 0.8, 0.2, 1);
        }

        /* Input Fields */
        div.stTextInput input {
            background: rgba(0, 0, 0, 0.2) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            color: white !important;
            border-radius: 12px !important;
            padding: 14px 16px !important;
            transition: all 0.3s ease !important;
            font-size: 1rem !important;
        }
        
        div.stTextInput input:focus {
            background: rgba(0, 0, 0, 0.4) !important;
            border-color: #818cf8 !important;
            box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.2) !important;
            transform: translateY(-2px);
        }
        
        /* Input Labels */
        .stTextInput label p {
            color: #94a3b8 !important;
            font-weight: 500 !important;
            font-size: 0.9rem !important;
            letter-spacing: 0.5px;
            text-transform: uppercase;
        }

        /* Forms Headers */
        div[data-testid="stForm"] h3 {
            color: white !important;
            font-family: 'Outfit', sans-serif !important;
            font-weight: 600 !important;
            text-align: center !important;
            margin-bottom: 25px !important;
            font-size: 1.8rem !important;
        }

        /* Animated Premium Buttons */
        div.stButton > button {
            background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%) !important;
            color: white !important;
            border: none !important;
            padding: 16px 24px !important;
            font-family: 'Outfit', sans-serif !important;
            font-weight: 600 !important;
            font-size: 1.1rem !important;
            border-radius: 14px !important;
            width: 100% !important;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
            box-shadow: 0 10px 20px -5px rgba(79, 70, 229, 0.5) !important;
            margin-top: 15px !important;
            position: relative;
            overflow: hidden;
        }
        
        div.stButton > button:hover {
            transform: translateY(-4px) scale(1.02);
            box-shadow: 0 20px 30px -10px rgba(124, 58, 237, 0.7) !important;
        }

        /* Tabs Styling */
        div[data-baseweb="tab-list"] {
            gap: 15px;
            background: rgba(0, 0, 0, 0.2);
            padding: 8px;
            border-radius: 16px;
            backdrop-filter: blur(10px);
            margin-bottom: 20px;
        }
        
        div[data-baseweb="tab"] {
            background: transparent !important;
            border: none !important;
            color: #94a3b8 !important;
            font-family: 'Outfit', sans-serif !important;
            font-weight: 500 !important;
            font-size: 1.05rem !important;
            transition: all 0.3s ease !important;
        }
        
        div[aria-selected="true"] {
            background: rgba(255, 255, 255, 0.1) !important;
            color: white !important;
            border-radius: 10px !important;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2) !important;
        }
        
        /* Floating particles effect placeholder */
        .particles {
            position: fixed;
            top: 0; left: 0; width: 100vw; height: 100vh;
            pointer-events: none;
            z-index: -1;
            background: radial-gradient(circle at 15% 50%, rgba(99, 102, 241, 0.15), transparent 25%),
                        radial-gradient(circle at 85% 30%, rgba(168, 85, 247, 0.15), transparent 25%);
        }
    </style>
    
    <div class="particles"></div>
    <div class='login-header'>
        <h1 class='title-glow'>AI Career Success Engine</h1>
        <p class='subtitle'>Unlock the blueprint to your professional future.</p>
    </div>
    """,
    unsafe_allow_html=True
)

# ---------- MAIN LAYOUT ----------
c1, main_col, c3 = st.columns([1, 2, 1])

with main_col:
    tab1, tab2 = st.tabs(["🔐 Sign In", "🆕 Sign Up"])

    # ---------- LOGIN ----------
    with tab1:
        with st.form("login_form"):
            st.subheader("Login")

            login_username = st.text_input("Username", key="login_username_input")
            login_password = st.text_input("Password", type="password", key="login_password_input")

            submit = st.form_submit_button("Sign In")

            if submit:
                if not login_username or not login_password:
                    st.warning("Please enter both username and password.")
                else:
                    is_valid = authenticate_user(login_username, login_password)

                    if is_valid:
                        st.session_state["authenticated"] = True
                        st.session_state["username"] = login_username
                        st.session_state["is_admin"] = is_user_admin(login_username)
                        st.success(f"Welcome back, {login_username}!")
                        st.rerun()
                    else:
                        st.error("Invalid credentials. Please try again.")

    # ---------- SIGNUP ----------
    with tab2:
        with st.form("signup_form"):
            st.subheader("Create Account")

            col1, col2 = st.columns(2)
            with col1:
                first_name = st.text_input("First Name")
            with col2:
                last_name = st.text_input("Last Name")

            email = st.text_input("Email Address", key="signup_email")
            signup_username = st.text_input("Username", key="signup_username_input")
            signup_password = st.text_input("Password", type="password", key="signup_password_input")

            submit_signup = st.form_submit_button("Sign Up")

            if submit_signup:
                # VALIDATION
                if not all([first_name, last_name, email, signup_username, signup_password]):
                    st.error("All fields are required.")

                elif not is_valid_email(email):
                    st.error("Invalid email format.")

                elif len(signup_username) < 3:
                    st.error("Username must be at least 3 characters.")

                elif len(signup_password) < 6:
                    st.error("Password must be at least 6 characters.")

                else:
                    success = create_user(
                        signup_username, signup_password, email, first_name, last_name
                    )

                    if success:
                        st.success("Account created successfully! Please log in.")
                    else:
                        st.error("Username already exists.")

    st.markdown("---")
    st.markdown("<div style='text-align: center; color: #94a3b8; font-weight: 500;'>OR</div>", unsafe_allow_html=True)
    if GOOGLE_CLIENT_ID:
        st.link_button("🌐 Continue with Google", google_login_url(), use_container_width=True)
    else:
        st.warning("Google Auth not configured (.env missing)")
