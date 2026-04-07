# -*- coding: utf-8 -*-
# AI Career Recommender - v2.2 (Gemini AI Enhanced)
import streamlit as st # type: ignore
from models.recommender import CareerRecommender # type: ignore
import pandas as pd # type: ignore
from datetime import datetime, date
from fpdf import FPDF # type: ignore
import sys
import os, json

# Add root directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ── Load .env and pre-populate Gemini key in session_state ─────────────────
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))
except ImportError:
    pass  # dotenv not installed — key must be entered manually in the sidebar

if "gemini_api_key" not in st.session_state:
    _env_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if _env_key and _env_key != "your_new_key_here":
        st.session_state["gemini_api_key"] = _env_key
# ───────────────────────────────────────────────────────────────────────────

from core.pdf_generator import generate_pdf_report # type: ignore
import textwrap
from accessibility.inclusive_recommender import InclusiveRecommender, AccessibilityRequirement # type: ignore
from accessibility.accessibility_settings import AccessibilityProfile, DISABILITY_ACCOMMODATION_TEMPLATES # type: ignore
from models.career_advisor import CareerAdvisor # type: ignore

# Auth handled by the router in app.py
st.sidebar.markdown("---")
if 'username' in st.session_state:
    st.sidebar.markdown(f"**👤 Connected as: {st.session_state['username']}**")
    if st.sidebar.button("Logout", type="primary"):
        st.session_state["authenticated"] = False
        del st.session_state["username"]
        st.rerun()

# Helpers: language, persistence (bookmarks), simple utilities
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
BOOKMARKS_FILE = os.path.join(DATA_DIR, 'bookmarks.json')
CATEGORY_MAP_FILE = os.path.join(DATA_DIR, 'category_mappings.json')

def _ensure_data_dir():
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
    except Exception:
        pass

_ensure_data_dir()

# Admin helpers
import io, hashlib

def _file_info(path: str):
    try:
        ts = os.path.getmtime(path)
        return datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        return 'N/A'

def _hash_job_row(title: str, company: str, desc: str) -> str:
    h = hashlib.sha256()
    h.update((str(title) + '|' + str(company) + '|' + str(desc)).encode('utf-8', errors='ignore'))
    return h.hexdigest()

def _load_category_mapping():
    try:
        if os.path.exists(CATEGORY_MAP_FILE):
            with open(CATEGORY_MAP_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def _save_category_mapping(mapping: dict):
    try:
        with open(CATEGORY_MAP_FILE, 'w', encoding='utf-8') as f:
            json.dump(mapping, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

# Language dictionary (basic scaffolding)
if 'lang' not in st.session_state:
    st.session_state['lang'] = 'English'

i18n = {
    'English': {
        'filters_title': 'Filters and Sorting',
        'filter_elig': 'Eligibility Status',
        'filter_show_degree': 'Show Degree',
        'filter_show_hybrid': 'Show Hybrid',
        'filter_show_diploma': 'Show Diploma',
        'filter_show_asp': 'Show Aspirational',
        'filter_show_not': 'Show Not Eligible',
        'filter_show_unknown': 'Show Unknown',
        'filter_min_market': 'Minimum Market Demand (%)',
        'filter_min_interest': 'Minimum Passion Match (%)',
        'sort_by': 'Sort by',
        'sort_final': 'Overall Score',
        'sort_passion': 'Passion',
        'sort_market': 'Market',
        'compare_btn': 'Compare Selected',
        'compare_title': 'Comparison',
        'bookmark_btn': 'Bookmark',
        'bookmarked_toast': 'Bookmarked',
        'no_selection': 'Select at least 2 to compare.',
        'language': 'Language'
    },
    'Kiswahili': {
        'filters_title': 'Vichujio na Upangaji',
        'filter_elig': 'Hali ya Ustahiki',
        'filter_show_degree': 'Onyesha Shahada',
        'filter_show_hybrid': 'Onyesha Mseto',
        'filter_show_diploma': 'Onyesha Diploma',
        'filter_show_asp': 'Onyesha ya Kutamani',
        'filter_show_not': 'Onyesha Isiyostahiki',
        'filter_show_unknown': 'Onyesha Isiyojulikana',
        'filter_min_market': 'Mahitaji ya Soko ya Chini (%)',
        'filter_min_interest': 'Ulinganifu wa Shauku wa Chini (%)',
        'sort_by': 'Panga kwa',
        'sort_final': 'Alama ya Jumla',
        'sort_passion': 'Shauku',
        'sort_market': 'Soko',
        'compare_btn': 'Linganisha Zilizochaguliwa',
        'compare_title': 'Ulinganisho',
        'bookmark_btn': 'Hifadhi Alamisho',
        'bookmarked_toast': 'Imehifadhiwa',
        'no_selection': 'Chagua angalau 2 kulinganisha.',
        'language': 'Lugha'
    }
}

def t(key: str) -> str:
    lang = st.session_state.get('lang', 'English')
    return i18n.get(lang, i18n['English']).get(key, key)

# Bookmark persistence
def _load_bookmarks():
    try:
        if os.path.exists(BOOKMARKS_FILE):
            with open(BOOKMARKS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return []

def _save_bookmarks(items):
    try:
        with open(BOOKMARKS_FILE, 'w', encoding='utf-8') as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

if 'bookmarks' not in st.session_state:
    st.session_state['bookmarks'] = _load_bookmarks()

# Compare selections
if 'compare_set' not in st.session_state:
    st.session_state['compare_set'] = set()

# Salary bands (indicative monthly KES ranges by department)
SALARY_BANDS = {
    "Information Technology": {"entry": (60000, 150000), "mid": (180000, 350000)},
    "Business": {"entry": (40000, 100000), "mid": (120000, 250000)},
    "Marketing & Sales": {"entry": (40000, 90000), "mid": (100000, 220000)},
    "Finance & Accounting": {"entry": (50000, 120000), "mid": (150000, 300000)},
    "Education": {"entry": (35000, 80000), "mid": (90000, 180000)},
    "Data Science & Analytics": {"entry": (80000, 180000), "mid": (220000, 450000)},
    "Project Management": {"entry": (60000, 150000), "mid": (180000, 350000)},
    "Agriculture & Environmental": {"entry": (40000, 90000), "mid": (100000, 220000)},
    "Law": {"entry": (70000, 160000), "mid": (200000, 400000)},
    "Real Estate & Property": {"entry": (50000, 120000), "mid": (150000, 300000)},
    "Engineering": {"entry": (60000, 150000), "mid": (180000, 350000)}
}

def get_salary_band(dept: str):
    return SALARY_BANDS.get(dept, {"entry": (40000, 100000), "mid": (120000, 250000)})

# Grades ordering and adjustment utility for sensitivity analysis
GRADE_ORDER = ["A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-", "E"]

def adjust_grade(current: str, delta: int) -> str:
    try:
        if current not in GRADE_ORDER:
            return current
        idx = GRADE_ORDER.index(current)
        idx_new = max(0, min(len(GRADE_ORDER)-1, idx + delta))
        return GRADE_ORDER[idx_new]
    except Exception:
        return current

# Micro-certification suggestions per department (indicative)
MICROCERTS = {
    "Information Technology": ["AZ-900 (Azure Fundamentals)", "AWS Certified Cloud Practitioner", "Google IT Support"],
    "Data Science & Analytics": ["Google Data Analytics", "IBM Data Science", "SQL for Data Analysis"],
    "Business": ["Excel Advanced", "Power BI Fundamentals", "QuickBooks Basics"],
    "Marketing & Sales": ["Google Analytics", "Meta Blueprint (Basics)", "HubSpot Inbound"],
    "Finance & Accounting": ["Excel for Finance", "QuickBooks", "CFA Investment Foundations"],
    "Education": ["CBC Training Modules", "Digital Pedagogy Basics"],
    "Engineering": ["AutoCAD Basics", "Project Safety / ISO Familiarization"],
    "Project Management": ["CAPM / PRINCE2 Foundation", "Agile Scrum Fundamentals"],
    "Agriculture & Environmental": ["GIS Fundamentals", "Agri-Tech and Post-Harvest Handling"],
    "Law": ["Legal Tech Tools Basics", "Advanced Legal Writing"]
}

# ═══════════════════════════════════════════════════════════════════
# PREMIUM DARK GLASSMORPHISM DESIGN SYSTEM
# ═══════════════════════════════════════════════════════════════════
st.markdown("""
<style>
    /* ── Google Fonts ── */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap');

    /* ── Global Dark Background ── */
    .stApp {
        background: linear-gradient(135deg, #0b0f1e 0%, #111827 50%, #1a1040 100%) !important;
        font-family: 'Inter', sans-serif;
        color: #e2e8f0 !important;
        font-size: 1.1rem !important; /* Boosted base font */
    }

    /* ── Animated ambient glow orbs ── */
    .stApp::before {
        content: '';
        position: fixed;
        top: -10vh; left: -10vw;
        width: 55vw; height: 55vh;
        background: radial-gradient(circle, rgba(99,102,241,0.18) 0%, transparent 70%);
        pointer-events: none; z-index: 0; animation: orbFloat 12s ease-in-out infinite;
    }
    .stApp::after {
        content: '';
        position: fixed;
        bottom: -10vh; right: -10vw;
        width: 55vw; height: 55vh;
        background: radial-gradient(circle, rgba(124,58,237,0.18) 0%, transparent 70%);
        pointer-events: none; z-index: 0; animation: orbFloat 15s ease-in-out infinite reverse;
    }
    @keyframes orbFloat {
        0%,100% { transform: translate(0, 0) scale(1); }
        50%      { transform: translate(3%, 4%) scale(1.08); }
    }

    /* ── Typography ── */
    h1 { font-size: 3.5rem !important; }
    h2 { font-size: 2.2rem !important; }
    h3 { font-size: 1.8rem !important; }
    h4 { font-size: 1.4rem !important; }
    
    h1, h2, h3, h4 {
        font-family: 'Outfit', sans-serif !important;
        font-weight: 700 !important;
        color: #ffffff !important;
        letter-spacing: -0.02em;
        text-shadow: 0 0 30px rgba(99,102,241,0.25);
    }
    label { 
        color: #cbd5e1 !important; 
        font-size: 1.05rem !important; 
        font-weight: 600 !important;
    }
    .stMarkdown p { 
        color: #cbd5e1 !important; 
        font-size: 1.1rem !important; 
        line-height: 1.7 !important;
    }
    .stCaption { 
        color: #94a3b8 !important; 
        font-size: 0.95rem !important; 
    }

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {
        background: rgba(15, 23, 42, 0.92) !important;
        backdrop-filter: blur(24px) saturate(160%) !important;
        border-right: 1px solid rgba(99,102,241,0.18) !important;
    }
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] p { color: #c7d2fe !important; }
    section[data-testid="stSidebar"] label { font-size: 1rem !important; }
    section[data-testid="stSidebar"] p { font-size: 1.05rem !important; }
    section[data-testid="stSidebar"] .stMarkdown hr { border-color: rgba(99,102,241,0.25) !important; }

    /* ── Hero Container ── */
    .hero-container {
        background: linear-gradient(135deg, #312e81 0%, #4f46e5 50%, #7c3aed 100%);
        padding: 60px 50px;
        border-radius: 32px;
        color: white;
        margin-bottom: 35px;
        box-shadow: 0 25px 50px -12px rgba(79,70,229,0.45),
                    inset 0 1px 0 rgba(255,255,255,0.15);
        position: relative;
        overflow: hidden;
        animation: fadeSlide 0.8s cubic-bezier(0.2, 0.8, 0.2, 1);
    }
    .hero-container::before {
        content: '';
        position: absolute; top: -60%; left: -40%;
        width: 200%; height: 250%;
        background: radial-gradient(ellipse, rgba(255,255,255,0.12) 0%, transparent 55%);
        transform: rotate(-15deg); pointer-events: none;
    }
    .hero-container h1 { color: #ffffff !important; text-shadow: 0 4px 20px rgba(0,0,0,0.3) !important; }

    /* ── Glass Cards ── */
    .glass-card {
        background: rgba(255,255,255,0.04) !important;
        backdrop-filter: blur(20px) saturate(150%) !important;
        -webkit-backdrop-filter: blur(20px) saturate(150%) !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        border-radius: 24px !important;
        padding: 35px !important;
        box-shadow: 0 20px 40px rgba(0,0,0,0.35),
                    inset 0 1px 0 rgba(255,255,255,0.08) !important;
        margin-bottom: 30px;
        transition: transform 0.45s cubic-bezier(0.19,1,0.22,1),
                    box-shadow 0.45s cubic-bezier(0.19,1,0.22,1),
                    border-color 0.3s ease !important;
        animation: fadeSlide 0.7s cubic-bezier(0.2, 0.8, 0.2, 1);
    }
    .glass-card:hover {
        transform: translateY(-9px) !important;
        box-shadow: 0 35px 60px rgba(0,0,0,0.45),
                    0 0 0 1px rgba(99,102,241,0.35),
                    inset 0 1px 0 rgba(255,255,255,0.12) !important;
        border-color: rgba(99,102,241,0.4) !important;
    }

    /* ── Metric Cards ── */
    div[data-testid="metric-container"] {
        background: rgba(255,255,255,0.04) !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        border-radius: 20px !important;
        padding: 24px !important;
        box-shadow: 0 10px 25px rgba(0,0,0,0.3) !important;
    }
    div[data-testid="metric-container"] label {
        color: #a5b4fc !important;
        font-family: 'Outfit', sans-serif !important;
        font-weight: 600 !important; letter-spacing: 0.03em;
        font-size: 1.15rem !important;
    }
    div[data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-size: 2.8rem !important;
        font-weight: 800 !important;
    }

    /* ── Input Fields ── */
    div.stTextInput input, div.stTextArea textarea,
    div.stNumberInput input {
        background: rgba(0,0,0,0.3) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        color: white !important; border-radius: 14px !important;
        padding: 16px 20px !important;
        transition: all 0.3s ease !important;
        font-size: 1.15rem !important; font-family: 'Inter', sans-serif !important;
    }
    div.stTextInput input:focus, div.stTextArea textarea:focus {
        background: rgba(0,0,0,0.5) !important;
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 4px rgba(99,102,241,0.2) !important;
    }

    /* ── Selectboxes (Fix for Clipped Text) ── */
    div[data-testid="stSelectbox"], div[data-baseweb="select"] {
        min-height: 55px !important;
        height: auto !important;
    }
    div[data-baseweb="select"] > div {
        background: rgba(0,0,0,0.3) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 14px !important;
        color: white !important;
        padding: 10px 15px !important;
        font-size: 1.2rem !important; /* Bold, clear text */
        min-height: 55px !important;
        display: flex !important;
        align-items: center !important;
    }
    /* Targeted fix for internal span clipping */
    div[data-baseweb="select"] span {
        color: white !important;
        font-size: 1.2rem !important;
        overflow: visible !important;
        line-height: 1.4 !important;
    }
    div[data-baseweb="popover"] {
        background: #1e293b !important;
        border: 1px solid rgba(99,102,241,0.3) !important;
        border-radius: 14px !important;
    }

    /* ── Primary Buttons ── */
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%) !important;
        color: white !important; border: none !important;
        padding: 18px 32px !important;
        font-family: 'Outfit', sans-serif !important;
        font-weight: 700 !important; font-size: 1.25rem !important; /* Larger text */
        border-radius: 16px !important;
        box-shadow: 0 10px 25px rgba(79,70,229,0.5) !important;
        transition: all 0.4s cubic-bezier(0.4,0,0.2,1) !important;
    }

    /* ── Secondary Buttons ── */
    div.stButton > button:not([kind="primary"]) {
        background: rgba(255,255,255,0.06) !important;
        color: #c7d2fe !important;
        border: 1px solid rgba(99,102,241,0.3) !important;
        border-radius: 14px !important;
        font-family: 'Outfit', sans-serif !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        transition: all 0.3s ease !important;
    }

    /* ── Tabs ── */
    div[data-baseweb="tab"] {
        font-size: 1.1rem !important;
        padding: 12px 24px !important;
    }

    /* ── Expanders ── */
    details[data-testid="stExpander"] summary p {
        font-size: 1.15rem !important;
        font-weight: 600 !important;
        color: #ffffff !important;
    }

    /* ── Glowing Score Badge ── */
    .score-badge {
        display: inline-block;
        background: linear-gradient(135deg, #4f46e5, #7c3aed);
        color: white; font-family: 'Outfit', sans-serif;
        font-weight: 800; font-size: 1.6rem !important;
        padding: 12px 26px !important; border-radius: 50px;
    }

    /* ── Entrance Animations ── */
    @keyframes fadeSlide {
        from { opacity: 0; transform: translateY(22px); }
        to   { opacity: 1; transform: translateY(0); }
    }

</style>
""", unsafe_allow_html=True)



# Initialize recommender

@st.cache_resource
def get_recommender_instance():
    return CareerRecommender()

@st.cache_resource
def get_advisor_instance():
    return CareerAdvisor(recommender=get_recommender_instance())

recommender = get_recommender_instance()
advisor = get_advisor_instance()

# Query params for admin mode and deep link state
try:
    qp = st.query_params if hasattr(st, 'query_params') else st.experimental_get_query_params()
except Exception:
    qp = {}
admin_mode = ('admin' in qp and (qp['admin'] == 'true' or qp['admin'] == ['true']))

# Data health banner: surface critical dataset issues in UI
try:
    data_health_issues = []
    # Demand data check
    if getattr(recommender, 'demand_df', None) is None or recommender.demand_df.empty:
        data_health_issues.append("Job market demand data is missing or empty. Market-weighted scores will be degraded.")
    # KUCCPS requirements check
    if not getattr(recommender, 'kuccps_requirements', {}):
        data_health_issues.append("KUCCPS academic requirements are missing. Eligibility status will show as UNKNOWN.")
    # Skill map check
    if not getattr(recommender, 'skill_map', {}):
        data_health_issues.append("Career skill map is missing. Skills/programs will fall back to defaults.")
    if data_health_issues:
        with st.container():
            for issue in data_health_issues:
                st.warning(issue)
except Exception:
    pass

# Sidebar: Core Discovery Controls
with st.sidebar:
    st.markdown("""
    <div style="padding: 20px 8px 16px;">
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:6px;">
            <img src="https://img.icons8.com/fluency/80/graduation-cap.png" width="40">
            <div>
                <div style="font-family:'Outfit',sans-serif;font-size:18px;font-weight:800;
                            color:#ffffff;letter-spacing:-0.02em;">KUCCUPS AI</div>
                <div style="font-size:11px;color:#a5b4fc;font-weight:500;letter-spacing:0.04em;">CAREER ENGINE v2.2</div>
            </div>
        </div>
        <div style="height:1px;background:linear-gradient(90deg,rgba(99,102,241,0.6),transparent);margin:6px 0 0;"></div>
    </div>
    """, unsafe_allow_html=True)
    
    # 1. Basics
    st.selectbox(t('language'), ['English', 'Kiswahili'], key='lang')
    
    # Detect target level change — clear stale results so the engine re-runs
    _prev_level = st.session_state.get('_target_level_prev', 'All')
    target_level = st.radio(
        "🎓 Target Qualification",
        ["All", "Degree", "Diploma", "Certificate"],
        index=0,
        key='target_level_radio',
        help="Filter your recommendations by academic level. Changing this will refresh your results."
    )
    if target_level != _prev_level:
        # Level changed — wipe cached results so recommender re-runs with correct target
        st.session_state.pop('recommendations', None)
        st.session_state.pop('df_viz', None)
        st.session_state['_target_level_prev'] = target_level
    st.markdown("---")
    
    # 2. Intelligence
    st.subheader("🎯 Intelligence Mode")
    mode_info = {
        "Balanced Hybrid": "⚖️ Default: Hybrid Passion & Jobs.",
        "Passion First": "❤️ Intrinsic: Focus on dreams.",
        "Market Priority": "💰 Opportunity: Focus on jobs.",
        "Custom Controls": "🎛 Manual: Fine-tune balance."
    }
    
    strategy = st.radio("Strategy:", list(mode_info.keys()), index=0, label_visibility="collapsed")
    st.caption(mode_info[strategy])
    
    if strategy == "Custom Controls":
        alpha = st.slider("Interest Weight", 0.0, 1.0, 0.70, 0.05)
        beta = 1.0 - alpha
    elif strategy == "Balanced Hybrid":
        alpha, beta = 0.70, 0.30
    elif strategy == "Passion First":
        alpha, beta = 0.90, 0.10
    else: alpha, beta = 0.30, 0.70

    st.markdown("---")
    
    # 3. Inclusion
    st.subheader("♿ Inclusion")
    inclusive_mode = st.toggle("Enable Inclusive Mode")
    
    if inclusive_mode:
        profile = st.selectbox("Profile", [p.value for p in AccessibilityProfile], index=0)
        default_needs = DISABILITY_ACCOMMODATION_TEMPLATES.get(profile, [])
        base_options = ["wheelchair_accessible", "sign_language_interpreter", "screen_reader_compatible", "remote_work", "flexible_schedule", "quiet_workspace"]
        all_options = sorted(list(set(base_options + default_needs)))
        
        custom_needs = st.multiselect("Specific Needs", 
                                     options=all_options,
                                     default=default_needs if default_needs else [],
                                     format_func=lambda x: x.replace('_', ' ').title())
        
        st.session_state['acc_requirements'] = [AccessibilityRequirement(feature=n) for n in custom_needs]
        st.session_state['disability_type'] = profile
        
    st.markdown("---")

    # 4. Resources
    with st.expander("🎓 Financial Aid", expanded=False):
        st.markdown("- **HELB**: Tuition loans.")
        st.markdown("- **County Bursaries**: Resident aid.")
        st.markdown("- **Sponsorships**: Wings to Fly, Equity.")
    
    with st.expander("🗓 Intake Info", expanded=False):
        st.markdown("- Jan / May / Sept sessions.")
        st.markdown("- Apply 2 months early.")

    st.caption(f"Job Market Sync: OK ({date.today().strftime('%Y-%m-%d')})")
    
    if admin_mode:
        st.markdown("---")
        if st.button("Full Sync (Admin Only)"):
            try:
                import subprocess, sys
                env = os.environ.copy(); env["PYTHONIOENCODING"] = "utf-8"
                subprocess.Popen([sys.executable, os.path.join(os.path.dirname(__file__), 'update_jobs.py')], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
                st.toast("Sync triggered.")
            except Exception: pass

    st.markdown("---")
    # Gemini status — key is loaded securely from .env, never shown in UI
    _has_key = bool(str(st.session_state.get("gemini_api_key", "")).strip())
    _status_dot = "🟢" if _has_key else "🔴"
    _status_txt = "Gemini AI: Connected" if _has_key else "Gemini AI: No key (using heuristic)"
    st.caption(f"{_status_dot} {_status_txt}")
    st.caption("AI v2.2.0-Premium | Gemini Enhanced")

# Admin Dashboard (hidden behind ?admin=true)
if admin_mode:
    st.markdown("---")
    st.markdown("## 🔧 Admin: Data Health Dashboard")
    try:
        # File info
        config_paths = {
            'jobs_csv': 'data/myjobmag_jobs.csv',
            'demand_csv': 'data/job_demand_metrics.csv',
            'skill_map_json': 'data/career_skill_map.json',
            'kuccps_csv': 'Kuccps/kuccps_courses.csv',
            'requirements_json': 'Kuccps/kuccps_requirements.json'
        }
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Datasets Modified**")
            for k, rel in config_paths.items():
                st.write(f"{k}: {_file_info(os.path.join(os.path.dirname(__file__), rel))}")
        with c2:
            st.markdown("**Row counts**")
            try:
                jobs_df = getattr(recommender, 'jobs_df', None)
                if jobs_df is None: jobs_df = pd.DataFrame()
                demand_df = getattr(recommender, 'demand_df', None)
                if demand_df is None: demand_df = pd.DataFrame()
                st.write(f"jobs_df rows: {len(jobs_df)}")
                st.write(f"demand_df rows: {len(demand_df)}")
                if not jobs_df.empty:
                    if 'Department' in jobs_df.columns:
                        st.write(f"Unique Department: {jobs_df['Department'].nunique()}")
                    if 'DeptNorm' in jobs_df.columns:
                        st.write(f"Unique DeptNorm: {jobs_df['DeptNorm'].nunique()}")
            except Exception:
                pass

        # Unmapped categories and reconciliation tool
        st.markdown("### Category Reconciliation")
        cat_map = _load_category_mapping()
        internal_depts = list(SALARY_BANDS.keys())
        jobs_df = getattr(recommender, 'jobs_df', None)
        if jobs_df is None:
            jobs_df = pd.DataFrame()
        raw_cats = []
        src_col = None
        if not jobs_df.empty:
            src_col = 'Department' if 'Department' in jobs_df.columns else ('Category' if 'Category' in jobs_df.columns else None)
            if src_col:
                raw_series = jobs_df[src_col].fillna('').astype(str).str.strip()
                raw_series = raw_series.replace({'': None}).dropna()
                raw_cats = sorted(set(raw_series))
                # Show counts for visibility
                with st.expander("Source category counts", expanded=False):
                    try:
                        counts = raw_series.value_counts().rename_axis('RawCategory').reset_index(name='Count')
                        st.dataframe(counts, hide_index=True, width='stretch')
                    except Exception:
                        pass
        unmapped = [c for c in raw_cats if c not in cat_map]
        if unmapped:
            st.caption("Map the following source categories to internal departments (top 50 shown):")
            new_map = {}
            for uc in unmapped[:50]:  # type: ignore
                sel = st.selectbox(f"{uc}", internal_depts, key=f"map_{uc}")
                new_map[uc] = sel
            # Manual add
            with st.expander("Add a custom mapping", expanded=False):
                raw_key = st.text_input("Raw category label (exact)")
                sel_dep = st.selectbox("Map to department", internal_depts, key="map_custom")
                if st.button("Add mapping") and raw_key:
                    new_map[raw_key] = sel_dep
                    st.success(f"Staged mapping: {raw_key} -> {sel_dep}")
            cbtn1, cbtn2, cbtn3 = st.columns(3)
            with cbtn1:
                if st.button("Save Category Mapping"):
                    cat_map.update(new_map)
                    _save_category_mapping(cat_map)
                    st.success("Category mappings saved.")
            with cbtn2:
                if st.button("Apply mapping to current data") and not jobs_df.empty and src_col:
                    try:
                        # Recompute DeptNorm in-memory using cat_map; fallback to existing DeptNorm
                        df2 = jobs_df.copy()
                        df2['DeptNorm'] = df2[src_col].map(cat_map).fillna(df2.get('DeptNorm', df2[src_col]))  # type: ignore
                        # Simple title-based override: if DeptNorm is IT but title hints other dept, keep existing recommender inference downstream
                        st.success("Applied mapping in-memory. Preview distribution:")
                        st.dataframe(df2['DeptNorm'].value_counts().rename_axis('DeptNorm').reset_index(name='Count'), hide_index=True)
                    except Exception as e:
                        st.error(f"Could not apply mapping: {e}")
            with cbtn3:
                if st.button("Persist updated DeptNorm to CSV (atomic)") and not jobs_df.empty:
                    try:
                        import tempfile
                        base_dir = os.path.dirname(__file__)
                        csv_path = os.path.join(base_dir, 'data', 'myjobmag_jobs.csv')
                        df2 = jobs_df.copy()
                        if src_col:
                            df2['DeptNorm'] = df2[src_col].map(cat_map).fillna(df2.get('DeptNorm', df2[src_col]))  # type: ignore
                        fd, tmp_path = tempfile.mkstemp(prefix='myjobmag_jobs_', suffix='.csv', dir=os.path.join(base_dir, 'data'))
                        os.close(fd)
                        df2.to_csv(tmp_path, index=False, encoding='utf-8')
                        os.replace(tmp_path, csv_path)
                        st.success("CSV updated. Background sync will pick this up on next check.")
                    except Exception as e:
                        st.error(f"Persist failed: {e}")
        else:
            st.info("No unmapped categories detected or jobs dataset is empty.")

        # Deduplication stats
        st.markdown("### Jobs Deduplication Stats")
        if not jobs_df.empty:
            if all(col in jobs_df.columns for col in ['Job Title', 'Company', 'Description']):
                try:
                    hashes = jobs_df.apply(lambda r: _hash_job_row(r['Job Title'], r['Company'], r['Description']), axis=1)
                    dup_count = int(hashes.duplicated().sum())
                    st.write(f"Potential duplicates by hash: {dup_count}")
                except Exception:
                    st.write("Could not compute duplicates hash.")
            else:
                st.write("Jobs CSV missing columns for deduplication (Job Title, Company, Description).")

        # Logs viewer
        st.markdown("### Update Logs (tail)")
        log_paths = [
            os.path.join(os.path.dirname(__file__), 'etl', 'scraper_log.txt'),
            os.path.join(os.path.dirname(__file__), 'logs', 'scrape.log')
        ]
        content = None
        for lp in log_paths:
            if os.path.exists(lp):
                try:
                    with open(lp, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                        content = ''.join(lines[-200:])  # type: ignore
                        break
                except Exception:
                    pass
        if content:
            st.code(content, language='text')
        else:
            st.caption("No logs found.")
    except Exception:
        st.warning("Admin dashboard encountered an error.")

# --- REPLACED BY ROOT MASTER STYLESHEET ---

# Main Content
st.markdown("""
<div class="hero-container">
    <div style="font-size:13px;letter-spacing:0.1em;color:rgba(255,255,255,0.6);font-weight:600;margin-bottom:10px;">🇰🇪 KENYA'S INTELLIGENT CAREER ENGINE</div>
    <h1 style="color:white;margin:0;font-size:2.6rem;line-height:1.15;">Your Future,<br><span style="background:linear-gradient(90deg,#a5b4fc,#c4b5fd);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">Architected by AI</span></h1>
    <p style="color:rgba(255,255,255,0.82);font-size:17px;margin-top:14px;max-width:600px;line-height:1.65;">
        Semantic NLP + Real-Time Kenyan Job Market Intelligence + KUCCPS Eligibility Engine.
        Enter your story — we build the roadmap.
    </p>
    <div style="display:flex;gap:16px;margin-top:22px;flex-wrap:wrap;">
        <span style="background:rgba(255,255,255,0.15);border:1px solid rgba(255,255,255,0.25);border-radius:50px;padding:6px 16px;font-size:13px;color:rgba(255,255,255,0.9);">🧠 DistilBERT Powered</span>
        <span style="background:rgba(255,255,255,0.15);border:1px solid rgba(255,255,255,0.25);border-radius:50px;padding:6px 16px;font-size:13px;color:rgba(255,255,255,0.9);">📊 Live Job Market Data</span>
        <span style="background:rgba(255,255,255,0.15);border:1px solid rgba(255,255,255,0.25);border-radius:50px;padding:6px 16px;font-size:13px;color:rgba(255,255,255,0.9);">🎓 KUCCPS 2024 Data</span>
    </div>
</div>
""", unsafe_allow_html=True)

# --- GUIDANCE SYSTEM: START ---
with st.expander("🆕 New here? Unlock the power of AI Guidance", expanded=False):
    st.markdown("""
    <div class="glass-card" style="padding: 25px; border-left: 5px solid #6366f1; margin-bottom: 20px;">
        <h4 style="margin-top:0; color: #ffffff !important;">🚀 Welcome to Your Premium Career Lab</h4>
        <p style="color: #cbd5e1 !important; margin-bottom: 0;">Our AI maps your language to 1,000+ Kenyan job roles and KUCCPS programs using BERT semantic analysis.</p>
    </div>
    """, unsafe_allow_html=True)
    
    g_col1, g_col2, g_col3 = st.columns(3)
    with g_col1:
        st.markdown("🎯 **1. Be Expressive**")
        st.caption("Tell us your favorite subjects, what you do in your free time, and what kind of problems you want to solve.")
    with g_col2:
        st.markdown("⚖️ **2. Tune Strategy**")
        st.caption("Use the sidebar to choose if you prioritize 'Passion' (Dream-focused) or 'Market' (Safety-focused).")
    with g_col3:
        st.markdown("🛤 **3. Explore Roadmaps**")
        st.caption("Each result comes with a 4-step execution plan and real-world job connections.")

st.markdown("### ✍️ Start Your Career Profile")

# Template Guidance
st.write("Not sure where to start? Try a template:")
temp_col1, temp_col2, temp_col3, temp_col4 = st.columns(4)

template_text = ""
with temp_col1:
    if st.button("💻 Tech Enthusiast"):
        template_text = "I love building software and mobile apps. I'm very good at Math and I enjoy solving complex logic puzzles in my spare time."
with temp_col2:
    if st.button("🧬 Medical/Science"):
        template_text = "I am fascinated by human biology and healthcare. I want a career where I can help patients and use science to treat diseases."
with temp_col3:
    if st.button("🎨 Creative Professional"):
        template_text = "I love digital art, design, and storytelling. I enjoy creating visual content and want to work in media or advertising."
with temp_col4:
    if st.button("💼 Business Leader"):
        template_text = "I am interested in commerce, strategy, and leading teams. I excel in business studies and want to grow companies."

# --- PHASE 1: ACADEMIC ELIGIBILITY ---

# Grade point mapper for KCSE
_GRADE_POINTS: dict[str, int] = {
    "A": 12, "A-": 11, "B+": 10, "B": 9, "B-": 8,
    "C+": 7, "C": 6, "C-": 5, "D+": 4, "D": 3, "D-": 2, "E": 1, "N/A": 0
}
_GRADE_COLORS: dict[str, str] = {
    "A": "#10b981", "A-": "#10b981",
    "B+": "#6366f1", "B": "#6366f1", "B-": "#818cf8",
    "C+": "#f59e0b", "C": "#f59e0b", "C-": "#fbbf24",
    "D+": "#f97316", "D": "#ef4444", "D-": "#ef4444",
    "E": "#dc2626", "N/A": "#64748b"
}

def _grade_badge(grade: str) -> str:
    color = _GRADE_COLORS.get(grade, "#64748b")
    return (
        f'<span style="display:inline-block;padding:3px 10px;border-radius:20px;'
        f'background:{color}25;color:{color};font-weight:700;font-size:13px;'
        f'border:1px solid {color}60;">{grade}</span>'
    )

def _cluster_badge(label: str, icon: str, color: str) -> str:
    return (
        f'<div style="display:inline-flex;align-items:center;gap:6px;padding:5px 14px;'
        f'border-radius:30px;background:{color}18;border:1px solid {color}40;'
        f'color:{color};font-size:12px;font-weight:600;">{icon} {label}</div>'
    )

with st.container():
    # ── Premium Phase Header ──────────────────────────────────────────────────
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(99,102,241,0.15) 0%, rgba(139,92,246,0.10) 100%);
        border: 1px solid rgba(99,102,241,0.35);
        border-radius: 20px;
        padding: 28px 32px;
        margin-bottom: 28px;
        position: relative;
        overflow: hidden;
    ">
        <div style="position:absolute;top:-30px;right:-30px;width:150px;height:150px;
                    background:radial-gradient(circle,rgba(139,92,246,0.18),transparent 70%);
                    border-radius:50%;"></div>
        <div style="display:flex;align-items:flex-start;gap:18px;">
            <div style="font-size:42px;line-height:1;">🎓</div>
            <div>
                <div style="font-size:11px;letter-spacing:0.12em;color:#a5b4fc;
                            font-weight:700;margin-bottom:6px;">STEP 1 OF 2 · ACADEMIC IDENTITY</div>
                <div style="font-size:24px;font-weight:800;color:#ffffff;
                            letter-spacing:-0.02em;margin-bottom:10px;">
                    Phase 1: Academic Identity
                </div>
                <p style="font-size:14.5px;color:rgba(255,255,255,0.75);
                           line-height:1.7;margin:0;max-width:680px;">
                    <b style="color:#c4b5fd;">Your grades tell a story.</b>
                    Enter your KCSE results and our AI cross-references
                    <b style="color:#e0e7ff;">1,500+ KUCCPS programs</b> to surface exactly
                    where you qualify — building your roadmap on
                    <i>academic reality</i>, not wishful thinking.
                </p>
                <div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:16px;">
                    <div style="background:rgba(16,185,129,0.15);border:1px solid rgba(16,185,129,0.35);
                                border-radius:30px;padding:4px 14px;font-size:12px;color:#6ee7b7;font-weight:600;">
                        ✅ Auto-Calculates Points
                    </div>
                    <div style="background:rgba(99,102,241,0.15);border:1px solid rgba(99,102,241,0.35);
                                border-radius:30px;padding:4px 14px;font-size:12px;color:#a5b4fc;font-weight:600;">
                        🎯 1,500+ Programs Checked
                    </div>
                    <div style="background:rgba(245,158,11,0.15);border:1px solid rgba(245,158,11,0.35);
                                border-radius:30px;padding:4px 14px;font-size:12px;color:#fcd34d;font-weight:600;">
                        ⚡ Real-Time Eligibility
                    </div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("📝 Enter Your KCSE Grades", expanded=True):

        # Mean Grade row
        mg_col1, mg_col2, mg_col3 = st.columns([1.2, 1, 1])
        with mg_col1:
            mean_grade = st.selectbox(
                "🎓 KCSE Mean Grade",
                ["A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-", "E"],
                index=5,
                help="Select your overall KCSE mean grade. This is the primary gateway for most university programs."
            )
        with mg_col2:
            mean_pts = _GRADE_POINTS.get(mean_grade, 0)
            mean_color = _GRADE_COLORS.get(mean_grade, "#64748b")
            st.markdown(f"""
            <div style="margin-top:28px;padding:10px 18px;border-radius:12px;
                        background:{mean_color}20;border:1px solid {mean_color}50;text-align:center;">
                <div style="font-size:11px;color:rgba(255,255,255,0.55);font-weight:600;
                            letter-spacing:0.08em;margin-bottom:2px;">KCSE POINTS</div>
                <div style="font-size:26px;font-weight:800;color:{mean_color};">{mean_pts}</div>
                <div style="font-size:10px;color:{mean_color}80;">out of 12</div>
            </div>
            """, unsafe_allow_html=True)
        with mg_col3:
            # Minimum grade info
            gate_map = {"Degree": "C+", "Diploma": "C", "Certificate": "D+"}
            gate = gate_map.get(target_level, "C+")
            gate_pts = _GRADE_POINTS.get(gate, 7)
            gap = mean_pts - gate_pts
            status_txt = "✅ Meets Gateway" if gap >= 0 else f"⚠️ {abs(gap)} pts below {gate}"
            status_color = "#10b981" if gap >= 0 else "#f59e0b"
            st.markdown(f"""
            <div style="margin-top:28px;padding:10px 18px;border-radius:12px;
                        background:{status_color}15;border:1px solid {status_color}40;text-align:center;">
                <div style="font-size:11px;color:rgba(255,255,255,0.55);font-weight:600;
                            letter-spacing:0.08em;margin-bottom:2px;">{target_level.upper()} GATEWAY</div>
                <div style="font-size:13px;font-weight:700;color:{status_color};
                            line-height:1.4;">{status_txt}</div>
                <div style="font-size:10px;color:{status_color}80;">Min. required: {gate}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        # ── Group I – Compulsory Core ─────────────────────────────────────
        st.markdown("""
        <div style="display:flex;align-items:center;gap:10px;margin:20px 0 12px;">
            <div style="width:4px;height:22px;background:linear-gradient(180deg,#6366f1,#a5b4fc);
                        border-radius:4px;"></div>
            <span style="font-size:13px;font-weight:700;color:#c4b5fd;letter-spacing:0.06em;">
                GROUP I — COMPULSORY CORE SUBJECTS
            </span>
        </div>
        """, unsafe_allow_html=True)
        grades_list = ["A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-", "E", "N/A"]
        s_col1, s_col2, s_col3 = st.columns(3)
        with s_col1:
            g_math = st.selectbox("📐 Mathematics (MAT)", grades_list, index=6)
        with s_col2:
            g_eng  = st.selectbox("🔤 English (ENG)", grades_list, index=6)
        with s_col3:
            g_kis  = st.selectbox("📖 Kiswahili (KIS)", grades_list, index=6)

        # ── Group II – Sciences ───────────────────────────────────────────
        st.markdown("""
        <div style="display:flex;align-items:center;gap:10px;margin:20px 0 12px;">
            <div style="width:4px;height:22px;background:linear-gradient(180deg,#06b6d4,#67e8f9);
                        border-radius:4px;"></div>
            <span style="font-size:13px;font-weight:700;color:#67e8f9;letter-spacing:0.06em;">
                GROUP II — SCIENCES
            </span>
        </div>
        """, unsafe_allow_html=True)
        s_col4, s_col5, s_col6 = st.columns(3)
        with s_col4:
            g_bio  = st.selectbox("🧬 Biology (BIO)", grades_list, index=12)
        with s_col5:
            g_chem = st.selectbox("⚗️ Chemistry (CHE)", grades_list, index=12)
        with s_col6:
            g_phys = st.selectbox("⚡ Physics (PHY)", grades_list, index=12)

        # ── Group II – Humanities ─────────────────────────────────────────
        st.markdown("""
        <div style="display:flex;align-items:center;gap:10px;margin:20px 0 12px;">
            <div style="width:4px;height:22px;background:linear-gradient(180deg,#10b981,#6ee7b7);
                        border-radius:4px;"></div>
            <span style="font-size:13px;font-weight:700;color:#6ee7b7;letter-spacing:0.06em;">
                GROUP II — HUMANITIES &amp; SOCIAL SCIENCES
            </span>
        </div>
        """, unsafe_allow_html=True)
        s_col7, s_col8, s_col9 = st.columns(3)
        with s_col7:
            g_hist = st.selectbox("📜 History (HIS)", grades_list, index=12)
        with s_col8:
            g_geo  = st.selectbox("🌍 Geography (GEO)", grades_list, index=12)
        with s_col9:
            g_cre  = st.selectbox("✝️ CRE/IRE/HRE", grades_list, index=12)

        # ── Group III & IV – Applied & Creative ───────────────────────────
        st.markdown("""
        <div style="display:flex;align-items:center;gap:10px;margin:20px 0 12px;">
            <div style="width:4px;height:22px;background:linear-gradient(180deg,#f59e0b,#fcd34d);
                        border-radius:4px;"></div>
            <span style="font-size:13px;font-weight:700;color:#fcd34d;letter-spacing:0.06em;">
                GROUP III &amp; IV — APPLIED, TECHNICAL &amp; CREATIVE
            </span>
        </div>
        """, unsafe_allow_html=True)
        s_col10, s_col11, s_col12 = st.columns(3)
        with s_col10:
            g_agri = st.selectbox("🌱 Agriculture (AGR)", grades_list, index=12)
            g_comp = st.selectbox("💻 Computer Studies (COM)", grades_list, index=12)
            g_bus  = st.selectbox("💼 Business Studies (BUS)", grades_list, index=12)
        with s_col11:
            g_hom  = st.selectbox("🍳 Home Science (HOM)", grades_list, index=12)
            g_art  = st.selectbox("🎨 Art & Design (ART)", grades_list, index=12)
            g_mus  = st.selectbox("🎵 Music (MUS)", grades_list, index=12)
        with s_col12:
            g_avi  = st.selectbox("✈️ Aviation (AVI)", grades_list, index=12)
            g_fre  = st.selectbox("🇫🇷 French (FRE)", grades_list, index=12)
            g_ger  = st.selectbox("🇩🇪 German (GER)", grades_list, index=12)

        # ── Advanced Technical (Group IV) ─────────────────────────────────
        with st.expander("🛠️ Advanced Technical Subjects (Group IV — Optional)"):
            st.caption("Include only if you sat these subjects in your KCSE examination.")
            t_col1, t_col2, t_col3 = st.columns(3)
            with t_col1:
                g_ele = st.selectbox("🔌 Electricity (ELE)", grades_list, index=12)
                g_pwr = st.selectbox("⚙️ Power Mechanics (PWR)", grades_list, index=12)
            with t_col2:
                g_met = st.selectbox("🔩 Metalwork (MET)", grades_list, index=12)
                g_wod = st.selectbox("🪵 Woodwork (WOD)", grades_list, index=12)
            with t_col3:
                g_bst = st.selectbox("🧱 Building Const (BST)", grades_list, index=12)
                g_drw = st.selectbox("📐 Drawing & Design (DRW)", grades_list, index=12)

    # ── Grade dictionary for processing ──────────────────────────────────────
    grades_dict = {
        "Mathematics": g_math, "English": g_eng, "Kiswahili": g_kis,
        "Biology": g_bio, "Chemistry": g_chem, "Physics": g_phys,
        "History": g_hist, "Geography": g_geo, "CRE": g_cre,
        "Business Studies": g_bus, "Agriculture": g_agri, "Computer Studies": g_comp,
        "Home Science": g_hom, "Art and Design": g_art, "Music": g_mus,
        "French": g_fre, "German": g_ger, "Aviation": g_avi,
        "Electricity": g_ele, "Power Mechanics": g_pwr, "Metalwork": g_met,
        "Woodwork": g_wod, "Building Construction": g_bst, "Drawing and Design": g_drw
    }

    # ── PREMIUM ACADEMIC PROFILE SUMMARY ─────────────────────────────────────
    active_grades = {k: v for k, v in grades_dict.items() if v != "N/A"}
    total_pts = sum(_GRADE_POINTS.get(v, 0) for v in active_grades.values())
    num_subjects = len(active_grades)
    avg_pts = round(total_pts / num_subjects, 1) if num_subjects else 0  # type: ignore[call-overload]
    top_subject = max(active_grades.items(), key=lambda x: _GRADE_POINTS.get(x[1], 0), default=("—", "—"))
    weak_subject = min(
        ((k, v) for k, v in active_grades.items() if _GRADE_POINTS.get(v, 0) > 0),
        key=lambda x: _GRADE_POINTS.get(x[1], 12),
        default=("—", "—")
    )

    # Strength cluster labels
    sciences_done   = [s for s in ["Biology","Chemistry","Physics"] if grades_dict.get(s,"N/A") != "N/A"]
    tech_done       = [s for s in ["Computer Studies","Agriculture","Business Studies"] if grades_dict.get(s,"N/A") != "N/A"]
    creative_done   = [s for s in ["Art and Design","Music","Home Science"] if grades_dict.get(s,"N/A") != "N/A"]

    st.markdown("""
    <div style="display:flex;align-items:center;gap:12px;margin:32px 0 20px;">
        <div style="font-size:22px;">📊</div>
        <div>
            <div style="font-size:20px;font-weight:800;color:#ffffff;letter-spacing:-0.01em;">
                Your Academic Profile Summary
            </div>
            <div style="font-size:13px;color:rgba(255,255,255,0.5);margin-top:2px;">
                Live snapshot based on grades entered above
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Stat cards row
    stat1, stat2, stat3, stat4 = st.columns(4)
    mean_color = _GRADE_COLORS.get(mean_grade, "#a5b4fc")
    with stat1:
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,{mean_color}25,{mean_color}10);
                    border:1px solid {mean_color}50;border-radius:16px;
                    padding:20px 18px;text-align:center;">
            <div style="font-size:11px;color:rgba(255,255,255,0.5);font-weight:700;
                        letter-spacing:0.1em;margin-bottom:8px;">MEAN GRADE</div>
            <div style="font-size:38px;font-weight:900;color:{mean_color};
                        line-height:1;margin-bottom:4px;">{mean_grade}</div>
            <div style="font-size:12px;color:{mean_color}90;">{mean_pts} / 12 pts</div>
        </div>
        """, unsafe_allow_html=True)
    with stat2:
        st.markdown(f"""
        <div style="background:rgba(99,102,241,0.12);border:1px solid rgba(99,102,241,0.35);
                    border-radius:16px;padding:20px 18px;text-align:center;">
            <div style="font-size:11px;color:rgba(255,255,255,0.5);font-weight:700;
                        letter-spacing:0.1em;margin-bottom:8px;">SUBJECTS ENTERED</div>
            <div style="font-size:38px;font-weight:900;color:#a5b4fc;
                        line-height:1;margin-bottom:4px;">{num_subjects}</div>
            <div style="font-size:12px;color:rgba(165,180,252,0.7);">Avg {avg_pts} pts each</div>
        </div>
        """, unsafe_allow_html=True)
    with stat3:
        _top_name: str = str(top_subject[0])
        _top_grade: str = str(top_subject[1])
        _top_name_short: str = _top_name[:14]  # type: ignore[index]
        top_color = _GRADE_COLORS.get(_top_grade, "#10b981")
        st.markdown(f"""
        <div style="background:rgba(16,185,129,0.10);border:1px solid rgba(16,185,129,0.35);
                    border-radius:16px;padding:20px 18px;text-align:center;">
            <div style="font-size:11px;color:rgba(255,255,255,0.5);font-weight:700;
                        letter-spacing:0.1em;margin-bottom:8px;">STRONGEST SUBJECT</div>
            <div style="font-size:15px;font-weight:800;color:#6ee7b7;
                        line-height:1.2;margin-bottom:6px;">{_top_name_short}</div>
            <div style="display:inline-block;padding:3px 12px;border-radius:20px;
                        background:{top_color}30;color:{top_color};font-weight:700;font-size:14px;">
                {_top_grade}
            </div>
        </div>
        """, unsafe_allow_html=True)
    with stat4:
        _weak_name: str = str(weak_subject[0])
        _weak_grade: str = str(weak_subject[1])
        _weak_name_short: str = _weak_name[:14]  # type: ignore[index]
        weak_color = _GRADE_COLORS.get(_weak_grade, "#f59e0b")
        st.markdown(f"""
        <div style="background:rgba(245,158,11,0.10);border:1px solid rgba(245,158,11,0.35);
                    border-radius:16px;padding:20px 18px;text-align:center;">
            <div style="font-size:11px;color:rgba(255,255,255,0.5);font-weight:700;
                        letter-spacing:0.1em;margin-bottom:8px;">NEEDS ATTENTION</div>
            <div style="font-size:15px;font-weight:800;color:#fcd34d;
                        line-height:1.2;margin-bottom:6px;">{_weak_name_short}</div>
            <div style="display:inline-block;padding:3px 12px;border-radius:20px;
                        background:{weak_color}30;color:{weak_color};font-weight:700;font-size:14px;">
                {_weak_grade}
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    # Strength cluster badges
    if sciences_done or tech_done or creative_done:
        cluster_html = '<div style="display:flex;flex-wrap:wrap;gap:10px;margin:16px 0 20px;">'
        if sciences_done:
            cluster_html += _cluster_badge(f"Sciences ({len(sciences_done)})", "🔬", "#06b6d4")
        if tech_done:
            cluster_html += _cluster_badge(f"Tech & Business ({len(tech_done)})", "💡", "#6366f1")
        if creative_done:
            cluster_html += _cluster_badge(f"Creative Arts ({len(creative_done)})", "🎨", "#ec4899")
        cluster_html += "</div>"
        st.markdown(cluster_html, unsafe_allow_html=True)

    # Color-coded subject grade grid
    if active_grades:
        st.markdown("""
        <div style="font-size:12px;color:rgba(255,255,255,0.45);font-weight:600;
                    letter-spacing:0.08em;margin-bottom:10px;">SUBJECT BREAKDOWN</div>
        """, unsafe_allow_html=True)

        # Group subjects by cluster for display
        _display_clusters = [
            ("📐 Core", ["Mathematics", "English", "Kiswahili"]),
            ("🔬 Sciences", ["Biology", "Chemistry", "Physics"]),
            ("🌍 Humanities", ["History", "Geography", "CRE"]),
            ("💻 Applied", ["Computer Studies", "Agriculture", "Business Studies",
                            "Home Science", "Art and Design", "Music",
                            "French", "German", "Aviation"]),
            ("🛠️ Technical", ["Electricity", "Power Mechanics", "Metalwork",
                              "Woodwork", "Building Construction", "Drawing and Design"]),
        ]
        for cluster_label, cluster_subjects in _display_clusters:
            cluster_active = [(s, active_grades[s]) for s in cluster_subjects if s in active_grades]
            if not cluster_active:
                continue
            badges_html = "".join(_grade_badge(g) for _, g in cluster_active)
            def _trunc7(val: str) -> str:
                return val[:7]  # type: ignore[index]
            labels_html = "".join(
                f'<span style="font-size:11px;color:rgba(255,255,255,0.5);'
                f'text-align:center;display:inline-block;width:52px;margin:0 1px;">'
                + _trunc7(str(s)) + '</span>'
                for s, _ in cluster_active
            )
            pts_total_cluster = sum(_GRADE_POINTS.get(g, 0) for _, g in cluster_active)
            st.markdown(f"""
            <div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);
                        border-radius:14px;padding:14px 18px;margin-bottom:10px;">
                <div style="display:flex;justify-content:space-between;align-items:center;
                            margin-bottom:10px;">
                    <span style="font-size:12px;font-weight:700;color:rgba(255,255,255,0.65);">
                        {cluster_label}
                    </span>
                    <span style="font-size:11px;color:rgba(255,255,255,0.35);">
                        {len(cluster_active)} subject(s) · {pts_total_cluster} pts
                    </span>
                </div>
                <div style="display:flex;flex-wrap:wrap;gap:6px;">{badges_html}</div>
                <div style="margin-top:6px;">{labels_html}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("ℹ️ No subjects entered yet. Select your grades above to see your profile summary.")

    kcse_data = {
        "mean_grade": mean_grade,
        "subjects": grades_dict
    }

st.markdown("---")

# --- PHASE 2: CAREER ASPIRATIONS ---
st.markdown("### Phase 2: Ambition & Interests")
col1, col2 = st.columns([2, 1])

with col1:
    # Handle template pre-fill
    if template_text:
        st.session_state['career_input'] = template_text
        
    student_text = st.text_area(
        "Articulate your professional dreams:", 
        height=150, 
        key="career_input",
        placeholder="Example: I possess a deep curiosity for how cities are built and function. I see myself designing sustainable urban infrastructure in Nairobi that solves traffic congestion while protecting green spaces."
    )

with col2:
    st.markdown("""
    <div style="background:rgba(99,102,241,0.08);padding:25px;border-radius:18px;
                border:1px solid rgba(99,102,241,0.25);backdrop-filter:blur(10px);">
        <div style="font-size:13px;font-weight:700;color:#a5b4fc;letter-spacing:0.06em;margin-bottom:8px;">✨ PRO TIPS</div>
        <p style="font-size:14px;color:#cbd5e1;line-height:1.7;margin:0;">
            <b style="color:#e0e7ff;">Be Specific:</b> Instead of "I like computers", try
            "I want to build secure mobile banking apps for Kenyan fintech."<br><br>
            <b style="color:#e0e7ff;">Highlight Interests:</b> Mentioning specific tools or goals
            helps the AI anchor your passion scores.
        </p>
    </div>
    """, unsafe_allow_html=True)

if st.button("🚀 Generate Personalized Roadmap", type="primary"):
    if student_text.strip():
        with st.spinner("🧠 AI is analyzing your career profile & eligibility..."):
            # Use data from session state if inclusive mode is on
            if 'inclusive_mode' in locals() and inclusive_mode:
                inc_recommender = InclusiveRecommender(base_recommender=recommender)
                inc_recommender.set_accessibility_requirements(st.session_state.get('acc_requirements', []))
                inc_recommender.set_disability_type(st.session_state.get('disability_type', 'Default'))
                recs = inc_recommender.recommend(student_text, top_n=8, alpha=alpha, beta=beta, kcse_results=kcse_data, target_level=target_level)
            else:
                recs = recommender.recommend(student_text, top_n=8, alpha=alpha, beta=beta, kcse_results=kcse_data, target_level=target_level)
                
            if recs:
                st.session_state['recommendations'] = recs
                st.session_state['student_query'] = student_text
                viz_data = []
                for rec in recs:
                    viz_data.append({
                        "Field": rec.get('dept', 'Unknown'),
                        "Passion": rec.get('interest_score', 0.0),
                        "Market": rec.get('demand_score', 0.0),
                        "Overall": rec.get('final_score', rec.get('match_score', 0.0))
                    })
                st.session_state['df_viz'] = pd.DataFrame(viz_data).set_index("Field")
                st.session_state.messages = [{"role": "ai", "content": f"I've analyzed your profile and found **{recs[0]['dept']}** to be your top match. Ask me anything about these paths!"}]
                
                # Silent Telemetry Tracker
                if 'username' in st.session_state:
                    try:
                        from core.auth import log_user_activity # type: ignore
                        log_user_activity(st.session_state['username'], student_text, mean_grade, recs[0]['dept'])
                    except Exception:
                        pass
            else:
                 st.error("Could not generate recommendations. Please try describing your interests differently.")
    else:
        st.warning("Please enter your career interests to begin.")

# PERSISTENT RESULTS UI (Accessed via Session State)
if 'recommendations' in st.session_state:
    recommendations = st.session_state['recommendations']
    df_viz = st.session_state['df_viz']
    student_text = st.session_state.get('student_query', '')

    st.markdown("---")

    # PDF Download Button - Placed at the top for easy access
    pdf_buffer = generate_pdf_report(recommendations)
    st.download_button(
        label="📥 Download Full Report as PDF",
        data=pdf_buffer,
        file_name=f"AI_Career_Report_{datetime.now().strftime('%Y%m%d')}.pdf",
        mime="application/pdf",
        width='stretch',
        type="primary"
    )

    tabs = st.tabs(["Recommendations", "Market Analysis", "Skill Bridge"])
    
    with tabs[0]:
        st.markdown("### Your Tailored Career Roadmaps")
        
        # Smart Bridge Alert (Dynamic, Context-aware Feedback)
        if target_level == "Degree":
            all_not_degree = all(r.get('dept_status') in ["ELIGIBLE (DIPLOMA)", "ASPIRATIONAL", "NOT ELIGIBLE"] for r in recommendations)
            any_aspirational = any(r.get('dept_status') == "ASPIRATIONAL" for r in recommendations)
            if all_not_degree:
                if any_aspirational:
                    st.warning("⚠️ **Almost There!** Your grades are close to Degree entry requirements for some programs below. See 'ASPIRATIONAL' cards for the gap and what you need to improve.")
                else:
                    st.error("🎓 **Degree Entry Gap Detected.** Your current KCSE Mean Grade (C) does not meet the minimum C+ required by most Bachelor's programs. The system has shown each Degree program below alongside the exact requirements you are missing. Eligible **Diploma bridge paths** are also listed to help you get there.")
        elif target_level == "Diploma":
            st.info("📋 **Diploma Mode Active.** Showing all Diploma & TVET programs aligned to your interests and eligibility.")
        elif target_level == "Certificate":
            st.info("📋 **Certificate Mode Active.** Showing Certificate programs matched to your academic profile.")

        # Filters & Sorting UI
        with st.expander(t('filters_title'), expanded=False):
            c1, c2, c3 = st.columns(3)
            with c1:
                st.caption(t('filter_elig'))
                f_degree = st.checkbox(t('filter_show_degree'), value=True, key='f_degree')
                f_hybrid = st.checkbox(t('filter_show_hybrid'), value=True, key='f_hybrid')
            with c2:
                f_diploma = st.checkbox(t('filter_show_diploma'), value=True, key='f_diploma')
                f_asp = st.checkbox(t('filter_show_asp'), value=True, key='f_asp')
            with c3:
                f_not = st.checkbox(t('filter_show_not'), value=True, key='f_not')
                f_unknown = st.checkbox(t('filter_show_unknown'), value=False, key='f_unknown')
            c4, c5 = st.columns(2)
            with c4:
                min_market = st.slider(t('filter_min_market'), 0, 100, 0, 5)
            with c5:
                min_interest = st.slider(t('filter_min_interest'), 0, 100, 0, 5)
            sort_choice = st.selectbox(t('sort_by'), [t('sort_final'), t('sort_passion'), t('sort_market')], index=0)

        # Apply filters
        status_allow = set()
        if st.session_state.get('f_degree', True):
            status_allow.add('ELIGIBLE')
            status_allow.add('ELIGIBLE (SPECIAL)')  # inclusive pathways
        if st.session_state.get('f_hybrid', True): status_allow.add('ELIGIBLE (HYBRID)')
        if st.session_state.get('f_diploma', True): status_allow.add('ELIGIBLE (DIPLOMA)')
        if st.session_state.get('f_asp', True): status_allow.add('ASPIRATIONAL')
        if st.session_state.get('f_not', True): status_allow.add('NOT ELIGIBLE')
        if st.session_state.get('f_unknown', False): status_allow.add('UNKNOWN')

        recs_view = [r for r in recommendations
                     if r.get('dept_status') in status_allow
                     and int((r.get('demand_score', 0.0) or 0.0) * 100) >= min_market
                     and int((r.get('interest_score', 0.0) or 0.0) * 100) >= min_interest]

        # Sorting
        if sort_choice == t('sort_passion'):
            recs_view.sort(key=lambda x: x.get('interest_score', 0.0), reverse=True)
        elif sort_choice == t('sort_market'):
            recs_view.sort(key=lambda x: x.get('demand_score', 0.0), reverse=True)
        else:
            recs_view.sort(key=lambda x: x.get('final_score', 0.0), reverse=True)

        # Export
        try:
            df_export = pd.DataFrame([{
                'Department': r['dept'],
                'Status': r.get('dept_status','UNKNOWN'),
                'FinalScore': r.get('final_score',0.0),
                'Passion': r.get('interest_score',0.0),
                'Market': r.get('demand_score',0.0),
                'Jobs': r.get('job_count','N/A')
            } for r in recs_view])
            col_exp1, col_exp2 = st.columns(2)
            with col_exp1:
                csv_bytes = df_export.to_csv(index=False).encode('utf-8')
                st.download_button("Export CSV", csv_bytes, file_name="recommendations.csv", mime="text/csv", width='stretch')
            with col_exp2:
                xls_buf = io.BytesIO()
                with pd.ExcelWriter(xls_buf, engine='xlsxwriter') as writer:
                    df_export.to_excel(writer, index=False, sheet_name='Recs')
                st.download_button("Export Excel", xls_buf.getvalue(), file_name="recommendations.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", width='stretch')
        except Exception:
            pass

        # Compare panel
        st.markdown(f"#### {t('compare_title')}")
        if st.button(t('compare_btn')):
            if len(st.session_state['compare_set']) < 2:
                st.info(t('no_selection'))
            else:
                pass  # selection persists below
        if st.session_state['compare_set']:
            cmp_depts = list(st.session_state['compare_set'])[:3]  # type: ignore
            cols = st.columns(len(cmp_depts))
            for i, dept in enumerate(cmp_depts):
                with cols[i]:
                    match = next((r for r in recs_view if r['dept'] == dept), None)
                    if not match:
                        match = next((r for r in recommendations if r['dept'] == dept), None)
                    if match:
                        st.markdown(f"**{match['dept']}**")
                        st.caption(f"Status: {match.get('dept_status','UNKNOWN')}")
                        st.metric("Overall", f"{match['final_score']:.0%}")
                        st.metric("Passion", f"{match['interest_score']:.0%}")
                        st.metric("Market", f"{match['demand_score']:.0%}")
                        st.caption(f"Jobs: {match.get('job_count','N/A')}")

        # Grouping Logic on filtered view — context-aware group labels
        special_recs      = [r for r in recs_view if r.get('dept_status') == "ELIGIBLE (SPECIAL)"]
        eligible_recs     = [r for r in recs_view if r.get('dept_status') == "ELIGIBLE"]
        hybrid_recs       = [r for r in recs_view if r.get('dept_status') == "ELIGIBLE (HYBRID)"]
        diploma_recs      = [r for r in recs_view if r.get('dept_status') == "ELIGIBLE (DIPLOMA)"]
        aspirational_recs = [r for r in recs_view if r.get('dept_status') == "ASPIRATIONAL"]
        ineligible_recs   = [r for r in recs_view if r.get('dept_status') == "NOT ELIGIBLE"]
        unknown_recs      = [r for r in recs_view if r.get('dept_status') == "UNKNOWN"]

        # Build context-aware group display names
        if target_level == "Degree":
            eligible_label    = "✅ Degree — ELIGIBLE (Direct Entry)"
            hybrid_label      = "🔀 Degree — ELIGIBLE via Hybrid Program"
            diploma_label     = "🪜 Diploma Bridge (Step toward your Degree goal)"
            aspirational_label= "🎯 Degree — ASPIRATIONAL (Almost Qualify — See Gap Below)"
            ineligible_label  = "❌ Degree — NOT ELIGIBLE (Requirements Not Met)"
        elif target_level == "Diploma":
            eligible_label    = "✅ Diploma — ELIGIBLE"
            hybrid_label      = "🔀 Diploma — Hybrid Option"
            diploma_label     = "✅ Diploma / TVET — ELIGIBLE"
            aspirational_label= "🎯 Diploma — ASPIRATIONAL (Close Match)"
            ineligible_label  = "❌ Diploma — NOT ELIGIBLE"
        elif target_level == "Certificate":
            eligible_label    = "✅ Certificate — ELIGIBLE"
            hybrid_label      = "🔀 Certificate — Hybrid Option"
            diploma_label     = "🪜 Diploma Bridge Available"
            aspirational_label= "🎯 Certificate — ASPIRATIONAL"
            ineligible_label  = "❌ Certificate — NOT ELIGIBLE"
        else:  # All
            eligible_label    = "✅ Eligible & Recommended (Degree)"
            hybrid_label      = "🔀 Eligible via Hybrid Programs"
            diploma_label     = "📜 Diploma / TVET Pathways"
            aspirational_label= "🎯 Aspirational Options"
            ineligible_label  = "❌ Currently Not Eligible"

        groups = [
            ("🌟 Specialized Inclusive Pathways (Disability-Tailored)", special_recs,     "#7c3aed"),
            (eligible_label,                                           eligible_recs,    "#10b981"),
            (hybrid_label,                                             hybrid_recs,      "#06b6d4"),
            (diploma_label,                                            diploma_recs,     "#0ea5e9"),
            (aspirational_label,                                       aspirational_recs,"#f59e0b"),
            (ineligible_label,                                         ineligible_recs,  "#ef4444"),
            ("Status Pending",                                         unknown_recs,     "#64748b")
        ]

        global_idx = 1
        for group_name, group_list, group_color in groups:
            if group_list:
                st.markdown(f"""
                <div style="padding: 10px; border-radius: 8px; background: {group_color}15; border-left: 5px solid {group_color}; margin: 20px 0 10px 0;">
                    <h4 style="margin:0; color: {group_color};">{group_name}</h4>
                </div>
                """, unsafe_allow_html=True)
                
                for rec in group_list:
                    
                    e_status = rec.get('dept_status', 'UNKNOWN')
                    e_icon = group_name.split()[0]

                    acc_fit_str = f'<span class="chip" style="background: #eef2ff; color: #4f46e5;">♿ Fit: {rec["accessibility_fit"]:.0%}</span>' if "accessibility_fit" in rec else ""

                    with st.container():
                        st.markdown(f"""
                        <div class="glass-card" style="margin-bottom: 25px; border-top: 4px solid {group_color};">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                                <div>
                                    <h2 style="margin:0; font-size: 24px;">{global_idx}. {rec['dept']}</h2>
                                    <div style="font-size: 12px; color: {group_color}; font-weight: 700; margin-top: 4px;">{e_icon} {e_status} PATHWAY</div>
                                </div>
                                <div style="display: flex; gap: 8px;">
                                    <span class="chip" style="background: rgba(79, 70, 229, 0.1); color: var(--primary);">Match: {rec['final_score']:.0%}</span>{acc_fit_str}
                                </div>
                            </div>
                        """, unsafe_allow_html=True)

                    # Actions: Compare & Bookmark
                        act1, act2 = st.columns([1,1])
                        with act1:
                            chk_key = f"cmp_{rec['dept']}"
                            checked = st.checkbox(f"Add to compare", key=chk_key, value=(rec['dept'] in st.session_state['compare_set']))
                            if checked:
                                st.session_state['compare_set'].add(rec['dept'])
                            else:
                                st.session_state['compare_set'].discard(rec['dept'])
                        with act2:
                            if st.button(t('bookmark_btn'), key=f"bm_{global_idx}"):
                                bm = {
                                    'dept': rec['dept'],
                                    'timestamp': datetime.now().isoformat(timespec='seconds'),
                                    'status': rec.get('dept_status','UNKNOWN'),
                                    'final_score': rec.get('final_score',0.0),
                                    'interest_score': rec.get('interest_score',0.0),
                                    'demand_score': rec.get('demand_score',0.0)
                                }
                                # avoid duplicates by dept+status+score signature
                                if bm not in st.session_state['bookmarks']:
                                    st.session_state['bookmarks'].append(bm)
                                    _save_bookmarks(st.session_state['bookmarks'])
                                    st.toast(t('bookmarked_toast'))
                        
                        c_left, c_right = st.columns([2, 1])
                        dept_status = rec.get('dept_status', 'UNKNOWN')
                        eligibility_map = rec.get('eligibility', {})
                        uni_mapping = rec.get('university_mapping', {})
                        
                        with c_left:
                            if dept_status == "NOT ELIGIBLE":
                                # --- DEFENSIVE UI FOR INELIGIBLE STUDENTS ---
                                st.markdown("#### 🧠 Interest Alignment")
                                st.write(f"Your interests strongly align with **{rec['dept']}** (Match Score: {rec['interest_score']:.0%}). The NLP engine detected consistent semantic signals related to your goals, but academic constraints currently block direct entry.")
                                
                                st.markdown("#### 🚫 Academic Constraint (Hard Gate)")
                                # Find first failing reason
                                fail_reason = "Requirements not met."
                                for p, data in eligibility_map.items():
                                    if data['status'] == "NOT ELIGIBLE":
                                        fail_reason = data['reason']
                                        break
                                st.error(f"**Blocking Factor**: {fail_reason}")
                                
                                st.markdown("#### 🎓 Immediate Viable Routes")
                                st.info("This is where your strategy shifts from Degree to **Recovery & Redirection**. Consider these Diploma pathways that align with your current KCSE profile.")
                                
                                # Show Eligible Diplomas if any, otherwise general advice
                                viable = [p for p, d in eligibility_map.items() if d['status'] == "ELIGIBLE" and ("Diploma" in p or "TVET" in p)]
                                if viable:
                                    for v in viable: st.markdown(f"- ✅ **{v}**")
                                else:
                                    st.markdown("- **Pre-University Certificate** in relevant field")
                                    st.markdown("- **TVET Foundation Level 5**")
                                
                                st.markdown("#### 🔗 Upgrade Pathway (Bridge Logic)")
                                st.success("Successful completion of a Diploma enables **Lateral Entry** into a degree later and improves your future KUCCPS competitiveness.")
                                
                                st.markdown("#### System Verdict")
                                st.caption("This pathway reflects strong interest alignment but requires academic upgrading before degree-level entry.")

                            else:
                                # --- STANDARD PREMIUM UI FOR ELIGIBLE/ASPIRATIONAL ---
                                if rec.get('dept_status') in ["NOT ELIGIBLE", "ASPIRATIONAL"]:
                                    st.markdown("#### Academic Reality & Strategy")
                                elif rec.get('dept_status') == "ELIGIBLE (DIPLOMA)":
                                    st.markdown("#### Your Diploma Pathway Strategy")
                                elif rec.get('dept_status') == "ELIGIBLE (HYBRID)":
                                    st.markdown("#### Your Hybrid Program Strategy")
                                else:
                                    st.markdown("#### Strategic Fit & Rationale")
                                    
                                st.write(rec.get('comprehensive_rationale') or rec.get('why_best', ''))

                                # Bridging Planner for Aspirational / Not Eligible
                                if rec.get('dept_status') in ["ASPIRATIONAL", "NOT ELIGIBLE"]:
                                    try:
                                        missing_subjects = []
                                        mean_missing = False
                                        # Collate missing across programs for a concise plan
                                        for p_name, p_info in rec.get('eligibility', {}).items():
                                            for d in p_info.get('details', []):
                                                if d.get('criterion') == 'Mean Grade' and d.get('status') == 'MISSING':
                                                    mean_missing = True
                                                elif d.get('status') == 'MISSING' and d.get('criterion') != 'Mean Grade':
                                                    missing_subjects.append((d.get('criterion'), d.get('actual'), d.get('required')))
                                        st.markdown("#### 🧩 Bridging Planner")
                                        if mean_missing:
                                            st.info("Your mean grade is below the minimum. Consider a Pre-University/TVET foundation term to strengthen your academic baseline.")
                                        if missing_subjects:
                                            st.caption("Subjects to bridge (target the required grade or better):")
                                            for sub, actual, reqd in missing_subjects[:8]:  # type: ignore
                                                st.markdown(f"- {sub}: raise from {actual} to at least {reqd}")
                                        st.caption("Recommended bridging routes (indicative durations):")
                                        st.markdown("- University bridging modules (8–12 weeks)")
                                        st.markdown("- TVET foundational certificates (3–6 months)")
                                        st.markdown("- Private college short courses (4–8 weeks)")
                                        st.success("Completing bridging improves degree eligibility and future competitiveness.")
                                    except Exception:
                                        pass
                                
                                # --- EXPERT ADVISORY SECTION ---
                                st.markdown("#### 🧭 Expert Career Advisory")
                                adv_map = {
                                    "Information Technology": "Your journey in tech is a marathon of building.\n\n**🚀 Action Plan:**\n* **Showcase:** Create a standout GitHub project solving a local problem.\n* **Cloud:** Get certified in AWS Cloud Practitioner or Azure AZ-900.\n* **Network:** Join hackathons by iHub or Moringa School.",
                                    "Data Science & Analytics": "Data tells a story; learn to be its best narrator.\n\n**🚀 Action Plan:**\n* **SQL:** Master complex SQL queries first.\n* **Portfolio:** Compete in a beginner-friendly Kaggle competition.\n* **Focus:** Frame projects around solving real business problems.",
                                    "Engineering": "Engineering is about solving problems at scale and safety.\n\n**🚀 Action Plan:**\n* **Logbook:** Start your EBK logbook from Year 1.\n* **Mentorship:** Connect with a registered engineer on LinkedIn.\n* **Project Management:** Seek PRINCE2 or PMP foundation awareness.",
                                    "Healthcare & Medical": "Compassion is as critical as clinical knowledge.\n\n**🚀 Action Plan:**\n* **Experience:** Volunteer at both busy public and small local clinics.\n* **Soft Skills:** Take courses on patient communication.\n* **Research:** Stay current with KEMRI and Ministry of Health updates.",
                                    "Business": "In a crowded market, specialization is your superpower.\n\n**🚀 Action Plan:**\n* **Analytics:** Learn Power BI or Tableau for visualization.\n* **Niche:** Aim for specialized fields like FinTech or Green Finance.\n* **Professional:** Join ICPAK or MSK as a student member.",
                                    "Law": "The future of law is at the intersection of tradition and tech.\n\n**🚀 Action Plan:**\n* **Writing:** Start a blog or write for your university law journal.\n* **Legal Tech:** Understand how AI is used for document review.\n* **Debate:** Non-negotiable: build confidence through moot courts.",
                                    "Agriculture & Environmental": "Soil is gold; technology and logistics are the new gold.\n\n**🚀 Action Plan:**\n* **Value Chain:** Intern at processing plants or digital marketplaces.\n* **Agri-Tech:** Learn about drone monitoring and IoT sensors.\n* **Business:** Develop a plan focusing on post-harvest value addition.",
                                    "Education": "The classroom of the future is a blend of physical and digital.\n\n**🚀 Action Plan:**\n* **Digital Tools:** Master Canva, Google Classroom, and video editing.\n* **Specialization:** Become a CBC expert in a specific learning area.\n* **Readiness:** Start the TSC registration process early.",
                                    "Arts & Media": "Your personal brand is your most valuable asset.\n\n**🚀 Action Plan:**\n* **Portfolio:** Build a multimedia site showcasing writing and video.\n* **Analytics:** Learn to prove your impact via social media insights.\n* **Network:** Offer to help journalists or PR pros with projects.",
                                    "Project Management": "Effective execution is as crucial as brilliant strategy.\n\n**🚀 Action Plan:**\n* **Agile/Scrum:** Get familiar with Jira or Trello, and understand agile frameworks.\n* **Certifications:** Look into CAPM or Prince2 foundations.\n* **Leadership:** Volunteer to lead university projects to build a track record.",
                                    "Aviation & Logistics": "The world runs on supply chains.\n\n**🚀 Action Plan:**\n* **Operations Planning:** Understand how goods move globally through courses or internships.\n* **Tech in Logistics:** Learn about ERP systems like SAP.\n* **Specialization:** Aim for niches like cold-chain or drone logistics."
                                }
                                advice = adv_map.get(rec['dept'], "Focus on gaining practical skills and relevant certifications to stand out in this competitive field. Networking with professionals is key.")
                                st.markdown(f"""
                                <div style="background: rgba(255, 255, 255, 0.04); border: 1px solid rgba(255, 255, 255, 0.1); padding: 22px; border-radius: 16px; margin-bottom: 25px;">
                                    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 15px;">
                                        <span style="font-size: 20px;">🧭</span>
                                        <div style="font-weight: 700; color: #a5b4fc; font-size: 15px; letter-spacing: 0.02em;">EXPERT STRATEGIC ADVISORY</div>
                                    </div>
                                    <div style="font-size: 14.5px; line-height: 1.7; color: #e2e8f0; font-family: 'Outfit', sans-serif;">
                                        {advice.replace('\n', '<br>')}
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)


                                # Eligibility Sensitivity (What-if)
                                with st.expander("Eligibility Sensitivity (What-if)"):
                                    try:
                                        subject_options = list(grades_dict.keys())
                                        sel_sub = st.selectbox("Subject to adjust", subject_options, key=f"sens_sub_{global_idx}")
                                        step = st.slider("Adjust grade (steps)", -1, 1, 0, key=f"sens_step_{global_idx}")
                                        # Build adjusted KCSE results
                                        adj_subjects = dict(grades_dict)
                                        current = adj_subjects.get(sel_sub, "E")
                                        current = "E" if current == "N/A" else current
                                        adj_subjects[sel_sub] = adjust_grade(current, step)
                                        adj_kcse = {"mean_grade": mean_grade, "subjects": adj_subjects}
                                        st.caption(f"New {sel_sub} grade: {adj_subjects[sel_sub]}")
                                        # Show impact on first few programs
                                        cols_wh = st.columns(2)
                                        with cols_wh[0]:
                                            st.markdown("**Original status**")
                                        with cols_wh[1]:
                                            st.markdown("**What-if status**")
                                        for p_name in rec.get('programs', [])[:3]:
                                            orig = rec.get('eligibility', {}).get(p_name, {}).get('status', 'UNKNOWN')
                                            new_status, _, _ = recommender.check_eligibility(p_name, adj_kcse)
                                            cols = st.columns(2)
                                            with cols[0]: st.write(f"{p_name[:40]}…: {orig}")
                                            with cols[1]: st.write(f"{p_name[:40]}…: {new_status}")
                                    except Exception:
                                        st.caption("Sensitivity analysis unavailable.")

                                st.markdown("#### Explainable Match Logic (XAI)")
                                st.caption("Your recommendation is a blend of your stated interests and real-world job market data. Here's the breakdown:")
                                i_weight = rec.get('interest_contribution', rec.get('interest_score', 0.0) * alpha)
                                m_weight = rec.get('market_contribution', rec.get('demand_score', 0.0) * beta)
                                total_c = i_weight + m_weight
                                i_pct = (i_weight / total_c) * 100 if total_c > 0 else 0
                                m_pct = (m_weight / total_c) * 100 if total_c > 0 else 0

                                xai_html = "".join([
                                    f'<div style="background:rgba(255,255,255,0.04);border-radius:16px;padding:20px;border:1px solid rgba(255,255,255,0.1);">',
                                    f'<div style="font-weight:700;font-size:14px;color:#c7d2fe;margin-bottom:14px;letter-spacing:0.03em;">⚡ Match Score Composition</div>',

                                    # Passion bar
                                    f'<div style="margin-bottom:14px;">',
                                    f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:5px;">',
                                    f'<span style="font-size:12px;color:#a5b4fc;font-weight:600;">● Your Passion</span>',
                                    f'<span style="font-size:12px;font-weight:800;color:#a5b4fc;">{i_pct:.1f}%</span>',
                                    f'</div>',
                                    f'<div style="height:8px;background:rgba(99,102,241,0.2);border-radius:10px;overflow:hidden;">',
                                    f'<div style="width:{i_pct}%;background:linear-gradient(90deg,#6366f1,#a78bfa);height:100%;border-radius:10px;"></div>',
                                    f'</div>',
                                    f'<div style="font-size:11px;color:#64748b;margin-top:4px;">Based on your stated interests and semantic analysis.</div>',
                                    f'</div>',

                                    # Market bar
                                    f'<div>',
                                    f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:5px;">',
                                    f'<span style="font-size:12px;color:#6ee7b7;font-weight:600;">● Market Demand</span>',
                                    f'<span style="font-size:12px;font-weight:800;color:#6ee7b7;">{m_pct:.1f}%</span>',
                                    f'</div>',
                                    f'<div style="height:8px;background:rgba(16,185,129,0.2);border-radius:10px;overflow:hidden;">',
                                    f'<div style="width:{m_pct}%;background:linear-gradient(90deg,#10b981,#6ee7b7);height:100%;border-radius:10px;"></div>',
                                    f'</div>',
                                    f'<div style="font-size:11px;color:#64748b;margin-top:4px;">Based on {rec.get("job_count","N/A")} live Kenyan job vacancies.</div>',
                                    f'</div>',
                                    f'</div>'
                                ])
                                st.markdown(xai_html, unsafe_allow_html=True)

                                st.markdown("---")
                                st.markdown("#### Strategic Career Roadmap")
                                st.caption("Follow this structured 4-step plan to systematically build your career from the ground up.")

                                # ... (networking_hub and foundation_path logic remains the same)
                                networking_hub = {
                                    "Finance & Accounting": "ICPAK (Institute of Certified Public Accountants of Kenya)", 
                                    "Engineering": "IEK (Institution of Engineers of Kenya) & EBK",
                                    "Information Technology": "Computer Society of Kenya (CSK) & iHub Nairobi",
                                    "Healthcare & Medical": "KMA (Kenya Medical Association) & Nursing Council", 
                                    "Law": "LSK (Law Society of Kenya)",
                                    "Agriculture & Agribusiness": "ASK (Agricultural Society of Kenya)",
                                    "Education": "TSC (Teachers Service Commission) Registration",
                                    "Media & Communications": "MCK (Media Council of Kenya)"
                                }.get(rec['dept'], "relevant global and local professional bodies")

                                # Logic to pick the BEST FOUNDATION path (Preserve Recommender Order)
                                programs_list = rec.get('programs', [])
                                foundation_path = 'Specialized Degree Track'
                                
                                if programs_list:
                                    foundation_path = programs_list[0]
                                    # Force search for an ELIGIBLE diploma if entry to degree is unmet
                                    if "DIPLOMA" in dept_status:
                                        # Improved logic: Ensure it's not a Bachelor course (like Diplomacy) and check status properly
                                        eligible_diplomas = [
                                            p for p in programs_list 
                                            if ("ELIGIBLE" in eligibility_map.get(p, {}).get('status', '')) and 
                                            ("DIPLOMA" in p.upper() or "TVET" in p.upper() or "CERTIFICATE" in p.upper()) and
                                            ("BACHELOR" not in p.upper())
                                        ]
                                        if eligible_diplomas:
                                            foundation_path = eligible_diplomas[0]
                                
                                elif dept_status in ["ASPIRATIONAL", "ELIGIBLE (SPECIAL)"]:
                                    foundation_path = "Bridging Certificate or TVET Diploma Foundation"

                                skills_list = rec.get('skills', [])
                                skill_focus_primary = skills_list[0] if skills_list else 'Core Competencies'
                                skill_focus_secondary = skills_list[1] if len(skills_list) > 1 else 'Industry Tools'

                                steps = [
                                    (
                                        "1. Academic Foundation (Year 1-2)", 
                                        f"Your primary goal is to excel in **{foundation_path}**. Aim for high grades, but more importantly, understand the core principles. "
                                        f"Connect with lecturers; their recommendations are invaluable. Supplement your learning with online resources like Khan Academy for foundational concepts."
                                    ),
                                    (
                                        "2. Practical Skill Building (Year 2-3)", 
                                        f"This is where you differentiate yourself. Dedicate time to mastering **{skill_focus_primary}** and **{skill_focus_secondary}**. "
                                        f"Create a GitHub/Behance/personal portfolio to showcase your projects. Contribute to open-source or volunteer for a local NGO to get real-world experience."
                                    ),
                                    (
                                        "3. Industry Immersion & Networking (Year 3-4)", 
                                        f"Join **{networking_hub}** as a student member. Attend their webinars and events. "
                                        f"Seek an industrial attachment or internship, focusing on companies that are leaders in the **{rec['dept']}** sector. Use LinkedIn to connect with professionals in roles you admire."
                                    ),
                                    (
                                        "4. Career Launch & Specialization (Graduation & Beyond)", 
                                        f"Refine your CV and portfolio. Practice interviewing, focusing on articulating the value you bring. "
                                        f"Your first job is a launchpad, not a destination. After 1-2 years, identify a niche area within {rec['dept']} to specialize in, potentially through professional certifications or a Master's degree."
                                    )
                                ]
                                
                                for step_title, step_desc in steps:
                                    st.markdown(f"""
                                    <div class="roadmap-step" style="border-left: 3px solid #a5b4fc; padding-left: 15px; margin-bottom: 12px; background: rgba(255,255,255,0.02); padding-top: 8px; padding-bottom: 8px; border-radius: 0 8px 8px 0;">
                                        <div style="font-weight: 700; color: #a5b4fc; font-size: 14px; margin-bottom: 4px;">{step_title}</div>
                                        <div style="font-size: 13px; color: #cbd5e1;  line-height: 1.6;">{step_desc}</div>
                                    </div>
                                    """, unsafe_allow_html=True)

                        with c_right:
                            st.markdown(f"""
                            <div style="background: rgba(255, 255, 255, 0.05); padding: 15px; border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.1); margin-bottom: 20px; backdrop-filter: blur(5px);">
                                <div style="display: flex; justify-content: space-around; text-align: center;">
                                    <div><div style="font-size: 18px; font-weight: 800; color: #a5b4fc;">{rec['interest_score']:.0%}</div><div style="font-size: 11px; color: #cbd5e1; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">Passion</div></div>
                                    <div><div style="font-size: 18px; font-weight: 800; color: #6ee7b7;">{rec['demand_score']:.0%}</div><div style="font-size: 11px; color: #cbd5e1; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">Market</div></div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

                            st.markdown("### 🎓 Academic Eligibility")
                            st.caption("A multi-dimensional mapping of your KCSE profile against institutional cluster points.")

                            # Show top 5 programs, using the order determined by the recommender (Eligible first)
                            for prog in rec.get('programs', [])[:5]:
                                elig = eligibility_map.get(prog, {"status": "UNKNOWN", "reason": "N/A", "details": []})
                                is_diploma = "Diploma" in prog or "TVET" in prog or "Qualify for Diploma" in elig['reason']
                                
                                # Comprehensive Status Mapping
                                status_map = {
                                    "ELIGIBLE": ("#10b981", "rgba(16, 185, 129, 0.1)"),
                                    "ELIGIBLE (INCLUSIVE)": ("#7c3aed", "rgba(124, 58, 237, 0.1)"),
                                    "ELIGIBLE (SPECIAL)": ("#7c3aed", "rgba(124, 58, 237, 0.1)"),
                                    "ELIGIBLE (HYBRID)": ("#06b6d4", "rgba(6, 182, 212, 0.1)"),
                                    "ELIGIBLE (DIPLOMA)": ("#0ea5e9", "rgba(14, 165, 233, 0.1)"),
                                    "ASPIRATIONAL": ("#f59e0b", "rgba(245, 158, 11, 0.1)"),
                                    "NOT ELIGIBLE": ("#f43f5e", "rgba(244, 63, 94, 0.1)"),
                                    "UNKNOWN": ("#64748b", "rgba(100, 116, 139, 0.1)")
                                }
                                
                                status_label = elig['status']
                                e_tag_color, e_tag_bg = status_map.get(status_label, ("#64748b", "rgba(255,255,255,0.05)"))
                                
                                # Special override for diplomas if status was generic ELIGIBLE
                                if is_diploma and status_label == "ELIGIBLE":
                                    e_tag_color, e_tag_bg = status_map["ELIGIBLE (DIPLOMA)"]

                                unis = uni_mapping.get(prog, ["Consult KUCCPS Portal"])
                                uni_list = ", ".join(unis[:2])

                                # Extract cut-off information
                                cutoff_map = rec.get('cutoff_mapping', {})
                                cutoff_str = cutoff_map.get(prog, "N/A")
                                cutoff_display = f"📊 Cut-off: {cutoff_str}" if cutoff_str != "N/A" else "📊 Cut-off: Consult Portal"

                                # Build the entire card HTML block to avoid rendering issues
                                req_rows_html = ""
                                if elig.get('details'):
                                    for d in elig['details']:
                                        row_status_label = "✅" if d.get('status') == "MET" else ("❌" if d.get('status') == "MISSING" else "🟡")
                                        row_color = "#10b981" if d.get('status') == "MET" else ("#f43f5e" if d.get('status') == "MISSING" else "#64748b")
                                        req_rows_html += f"""
<tr style="border-top:1px solid rgba(255,255,255,0.05); font-size:12px; color:#ffffff;">
<td style="padding:6px 10px; color:#cbd5e1; font-weight:500;">{d.get('criterion')}</td>
<td style="padding:6px 10px; color:#94a3b8;">{d.get('required')}</td>
<td style="padding:6px 10px; color:#ffffff; font-weight:800;">{d.get('actual')}</td>
<td style="padding:6px 10px; color:{row_color}; font-weight:900;">{row_status_label} {d.get('status')}</td>
</tr>"""

                                card_html = f"""
<div style="background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.1); padding:15px; border-radius:14px; border-left:4px solid {e_tag_color}; margin-bottom:12px; backdrop-filter:blur(12px);">
<div style="font-weight:700; color:#ffffff; font-size:1rem; margin-bottom:6px; line-height:1.2;">{prog}</div>
<div style="display:flex; gap:8px; align-items:center; margin-bottom:10px;">
<span style="background:{e_tag_bg}; color:{e_tag_color}; padding:2px 10px; border-radius:30px; font-size:10px; font-weight:800; text-transform:uppercase; border:1px solid {e_tag_color}44;">{status_label}</span>
</div>
<div style="display:flex; gap:10px; align-items:center; flex-wrap:wrap; margin-bottom:4px;">
    <div style="font-size:0.9rem; color:#6ee7b7; font-weight:700; background:rgba(110, 231, 183, 0.08); padding:6px 12px; border-radius:8px; border:1px solid rgba(110, 231, 183, 0.15);">
        🏫 {uni_list}
    </div>
    <div style="font-size:0.85rem; color:#fba8a4; font-weight:700; background:rgba(251, 168, 164, 0.08); padding:6px 12px; border-radius:8px; border:1px solid rgba(251, 168, 164, 0.15);">
        {cutoff_display}
    </div>
</div>
<div style="margin-top:12px; border:1px solid rgba(255,255,255,0.08); border-radius:8px; overflow:hidden; background:rgba(0,0,0,0.1);">
<table style="width:100%; border-collapse:collapse; text-align:left;">
<thead>
<tr style="background:rgba(255,255,255,0.05); color:#a5b4fc; font-size:11px; text-transform:uppercase; letter-spacing:0.05em;">
<th style="padding:10px;">Subject / Req</th>
<th style="padding:10px;">Min</th>
<th style="padding:10px;">You</th>
<th style="padding:10px;">Result</th>
</tr>
</thead>
<tbody>
{req_rows_html}
</tbody>
</table>
</div>
<div style="margin-top:10px; font-size:12px; color:#94a3b8; font-style:italic; line-height:1.3;">
💡 {elig['reason']}
</div>
</div>"""
                                st.markdown(card_html, unsafe_allow_html=True)
                                    
                                st.markdown('<div style="margin-bottom: 10px;"></div>', unsafe_allow_html=True)

                            if any(elig['status'] == "ASPIRATIONAL" for elig in eligibility_map.values()):
                                st.info("💡 **Pro Tip**: For 'Aspirational' paths, consider a Diploma or Certificate as a strategic bridge to a Degree.", icon="ℹ️")

                        st.markdown("#### 📡 Market Pulse: Active Opportunities")
                        st.caption("Click on any role below to unlock a detailed breakdown of skills and academic alignment.")

                        jobs = recommender.get_top_jobs(rec['dept'], top_n=3)
                        if jobs:
                            for idx, job in enumerate(jobs):
                                # Unique key for expander
                                with st.expander(f"📌 {job['Job Title']} @ {job['Company']}"):
                                    
                                    # Layout: 2 Cols (Description vs Analysis)
                                    j_col1, j_col2 = st.columns([2, 1])
                                    
                                    with j_col1:
                                        st.markdown("##### 📝 Role Overview")
                                        raw_desc = job.get('Description', 'Detailed description unavailable.')
                                        # Clean description if it's too raw (often from scraping)
                                        desc_text = str(raw_desc)
                                        st.write(desc_text[:600] + "..." if len(desc_text) > 600 else desc_text)  # type: ignore
                                        
                                        st.markdown("##### 🛠 Key Competencies")
                                        skills_req = job.get('Skillmentequired', 'Core Industry Standard Skills')
                                        st.code(str(skills_req), language="text")
                                    
                                    with j_col2:
                                        st.markdown("##### 🎯 Strategic Fit")
                                        _progs = rec.get('programs', [])
                                        degree_ref = _progs[0] if _progs else rec.get('dept', 'this program')
                                        st.info(
                                            f"**Why this fits {rec['dept']}**:\n\n"
                                            f"This role represents a direct market application of your study path. "
                                            f"It naturally extends the curriculum of **{degree_ref}**, requiring the exact analytical skills you will develop."
                                        )
                                        
                                        st.markdown("##### 🚀 Action")
                                        query = f"{job['Job Title']} {job['Company']} Kenya".replace(" ", "+")
                                        st.markdown(f"""
                                        <a href="https://www.google.com/search?q={query}" target="_blank">
                                            <button style="width: 100%; background-color: #4f46e5; color: white; border: none; padding: 10px; border-radius: 6px; font-weight: bold; cursor: pointer;">
                                                Find Application Page ↗
                                            </button>
                                        </a>
                                        """, unsafe_allow_html=True)

                            st.caption(f"Showing top {len(jobs)} live matches.")

                            # Top employers (based on all jobs for this department)
                            try:
                                df_jobs = getattr(recommender, 'jobs_df', None)
                                if df_jobs is not None and 'DeptNorm' in df_jobs.columns and 'Company' in df_jobs.columns:
                                    dept_norm = rec['dept'] if rec['dept'] != 'IT' else 'Information Technology'
                                    df_d = df_jobs[df_jobs['DeptNorm'] == dept_norm]
                                    top_companies = df_d['Company'].dropna().value_counts().head(5)
                                    if not top_companies.empty:
                                        st.markdown("##### Top employers")
                                        for comp, cnt in top_companies.items():
                                            st.markdown(f"- {comp} ({cnt})")

                                    # Regional demand removed per user request
                                    pass
                                
                            except Exception:
                                pass
                        else:
                            st.warning("No jobs available currently. Check later.")
                        
                        st.markdown("</div>", unsafe_allow_html=True)
                        st.markdown("---")
                        global_idx += 1

    with tabs[1]:
        import plotly.express as px  # type: ignore
        import plotly.graph_objects as go

        st.markdown(
            '<div class="glass-card"><h3 style="margin-top:0;">📊 Strategic Market Analysis</h3>'
            '<p style="color:var(--secondary);">Live Kenyan job market intelligence cross-matched with your passion scores. '
            'Use this to validate your career choice with real economic data.</p></div>',
            unsafe_allow_html=True
        )

        # ── KPI Row ──────────────────────────────────────────────────────────
        top_passion  = df_viz.sort_values("Passion",  ascending=False).index[0]
        top_market   = df_viz.sort_values("Market",   ascending=False).index[0]
        top_balanced = df_viz.sort_values("Overall",  ascending=False).index[0]
        total_jobs   = sum(r.get('job_count', 0) for r in recommendations)

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("❤️ Passion Leader",   top_passion,  f"{df_viz.loc[top_passion]['Passion']:.0%} match")
        k2.metric("💼 Market Leader",    top_market,   f"{df_viz.loc[top_market]['Market']:.0%} demand")
        k3.metric("⚖️ Best Balance",     top_balanced, f"{df_viz.loc[top_balanced]['Overall']:.0%} score")
        k4.metric("🏢 Live Kenyan Jobs", f"{total_jobs:,}", "across all paths")

        st.divider()

        # ── 1. Opportunity Matrix ─────────────────────────────────────────────
        st.markdown("### 1. 🎯 Opportunity Matrix")
        st.caption("Fields in the **top-right** corner are your 'Sweet Spots' — high passion AND high market demand.")

        df_scatter = df_viz.reset_index()
        fig_scatter = px.scatter(
            df_scatter, x="Passion", y="Market", text="Field",
            size="Overall", color="Overall",
            color_continuous_scale="Viridis",
            labels={"Passion": "Interest Alignment →", "Market": "Job Market Demand →"},
            height=520, template="plotly_dark",
            hover_data={"Overall": ":.1%", "Passion": ":.1%", "Market": ":.1%"},
        )
        fig_scatter.update_traces(
            textposition='top center',
            marker={"line": {"width": 1.5, "color": "white"}, "opacity": 0.9}
        )
        fig_scatter.update_layout(
            xaxis={"range": [0, 1.05], "gridcolor": "rgba(255,255,255,0.08)"},
            yaxis={"range": [0, 1.05], "gridcolor": "rgba(255,255,255,0.08)"},
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(15,15,30,0.6)',
            font={"color": "white"},
            coloraxis_showscale=False,
        )
        # Quadrant reference lines
        fig_scatter.add_hline(y=0.5, line_dash="dot", line_color="rgba(255,255,255,0.2)")
        fig_scatter.add_vline(x=0.5, line_dash="dot", line_color="rgba(255,255,255,0.2)")
        # Quadrant labels
        for txt, x, y, col in [
            ("🌟 Sweet Spot", 0.78, 0.97, "#10b981"),
            ("📚 Passion Only", 0.78, 0.03, "#f59e0b"),
            ("💰 Market Only", 0.02, 0.97, "#6366f1"),
            ("⚠️ Reconsider",  0.02, 0.03, "#ef4444"),
        ]:
            fig_scatter.add_annotation(x=x, y=y, text=txt, showarrow=False,
                                       font={"size": 10, "color": col}, xref="x", yref="y")
        st.plotly_chart(fig_scatter, use_container_width=True)

        st.divider()

        # ── 2. Side-by-side: Market Volume + Radar ──────────────────────────
        st.markdown("### 2. 📈 Deep-Dive Analysis")
        col_l, col_r = st.columns([1, 1])

        with col_l:
            st.markdown("##### 📉 Market Demand by Field")
            fig_vol = px.bar(
                df_viz.reset_index().sort_values("Market", ascending=True),
                y="Field", x="Market", orientation='h',
                color="Market", color_continuous_scale="Teal",
                text_auto='.0%', template="plotly_dark",
                height=360,
            )
            fig_vol.update_layout(
                yaxis_title=None, xaxis_title="Relative Demand Score",
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(15,15,30,0.6)',
                font={"color": "white"}, coloraxis_showscale=False,
                margin={"l": 0, "r": 10, "t": 10, "b": 30},
            )
            st.plotly_chart(fig_vol, use_container_width=True)
            st.caption("🏆 Top bar = easiest to find jobs. Bottom bar = more competitive niche.")

        with col_r:
            st.markdown("##### 🕸 Multi-Dimensional Fit (Top 3)")
            top_3_df = df_viz.head(3).reset_index()
            fig_radar = go.Figure()
            _colors = ["#6366f1", "#10b981", "#f59e0b"]
            for i, (_, row) in enumerate(top_3_df.iterrows()):
                fig_radar.add_trace(go.Scatterpolar(
                    r=[row['Passion'], row['Market'], row['Overall'], row['Passion']],
                    theta=['Passion', 'Market', 'Balance', 'Passion'],
                    fill='toself', name=str(row['Field']),
                    line={"color": _colors[i % 3], "width": 2},
                    fillcolor=_colors[i % 3].replace('#', 'rgba(') + ',0.15)' if False else _colors[i % 3],
                    opacity=0.75,
                ))
            fig_radar.update_layout(
                polar={
                    "radialaxis": {"visible": True, "range": [0, 1], "color": "rgba(255,255,255,0.3)"},
                    "bgcolor": "rgba(15,15,30,0.6)",
                    "angularaxis": {"color": "white"},
                },
                showlegend=True, height=360,
                paper_bgcolor='rgba(0,0,0,0)',
                font={"color": "white"},
                legend={"orientation": "h", "y": -0.15},
                margin={"t": 10, "b": 30, "l": 30, "r": 30},
            )
            st.plotly_chart(fig_radar, use_container_width=True)

        st.divider()

        # ── 3. Live Kenyan Hiring Intelligence ──────────────────────────────
        st.markdown("### 3. 🇰🇪 Live Kenyan Hiring Intelligence")
        st.caption("Top employers actively hiring in each of your recommended career fields.")

        try:
            df_jobs_global = getattr(recommender, 'jobs_df', None)
            if df_jobs_global is not None and not df_jobs_global.empty:
                hire_cols = st.columns(min(3, len(recommendations[:3])))
                for ci, rec in enumerate(recommendations[:3]):
                    with hire_cols[ci]:
                        dept_norm = rec['dept'] if rec['dept'] != 'IT' else 'Information Technology'
                        is_top_field = ci == 0
                        border_col = "#10b981" if is_top_field else "#6366f1"
                        st.markdown(
                            f'<div style="border:2px solid {border_col};border-radius:12px;padding:14px;'
                            f'background:rgba(15,15,30,0.5);">'
                            f'<div style="font-weight:700;font-size:14px;color:{border_col};">'
                            f'{"🥇 " if is_top_field else ""}#{ci+1} {rec["dept"]}</div>'
                            f'<div style="font-size:12px;color:#a5b4fc;margin-bottom:8px;">'
                            f'{rec.get("job_count",0):,} live vacancies</div>',
                            unsafe_allow_html=True
                        )
                        if hasattr(df_jobs_global, 'columns') and 'DeptNorm' in getattr(df_jobs_global, 'columns', []) and 'Company' in getattr(df_jobs_global, 'columns', []):
                            df_d = df_jobs_global[df_jobs_global['DeptNorm'] == dept_norm]  # type: ignore
                            top_co = df_d['Company'].dropna().value_counts().head(5)
                            if not top_co.empty:
                                for comp, cnt in top_co.items():
                                    st.markdown(
                                        f'<div style="display:flex;justify-content:space-between;'
                                        f'font-size:12px;padding:3px 0;border-bottom:1px solid rgba(255,255,255,0.05);">'
                                        f'<span>🏢 {comp}</span>'
                                        f'<span style="color:#10b981;font-weight:600;">{cnt} jobs</span></div>',
                                        unsafe_allow_html=True
                                    )
                            else:
                                st.caption("No employer data for this field.")
                        st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.info("Employer data not loaded. Run a market sync to populate this section.")
        except Exception:
            st.info("Live employer data unavailable. Your recommendations are still valid.")

        st.divider()

        # ── 4. Salary Bands Comparison ──────────────────────────────────────
        st.markdown("### 4. 💰 Salary Bands & ROI Calculator")

        # Show salary comparison for top 3 fields side by side
        _sal_cols = st.columns(min(3, len(recommendations[:3])))
        for ci, rec in enumerate(recommendations[:3]):
            bands   = get_salary_band(rec['dept'])
            e_lo, e_hi = bands['entry']
            m_lo, m_hi = bands['mid']
            with _sal_cols[ci]:
                st.markdown(
                    f'<div style="background:rgba(99,102,241,0.12);border:1px solid rgba(99,102,241,0.3);'
                    f'border-radius:10px;padding:12px;text-align:center;">'
                    f'<div style="font-weight:700;font-size:13px;color:#a5b4fc;margin-bottom:6px;">#{ci+1} {rec["dept"]}</div>'
                    f'<div style="font-size:11px;color:#94a3b8;">Entry Level</div>'
                    f'<div style="font-size:15px;font-weight:700;color:#10b981;">KES {e_lo:,}–{e_hi:,}</div>'
                    f'<div style="font-size:11px;color:#94a3b8;margin-top:4px;">Mid Level</div>'
                    f'<div style="font-size:15px;font-weight:700;color:#6366f1;">KES {m_lo:,}–{m_hi:,}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )

        st.markdown(" ")

        # ROI Calculator for top recommendation
        if recommendations:
            target_dept  = recommendations[0]['dept']
            bands        = get_salary_band(target_dept)
            entry_lo, entry_hi = bands['entry']
            st.markdown(f"**📐 ROI Calculator** — *{target_dept}*")
            c_roi1, c_roi2, c_roi3, c_roi4 = st.columns(4)
            with c_roi1:
                tuition_cost = st.number_input("Tuition estimate (KES)", 0, 5_000_000, 600_000, 50_000)
            with c_roi2:
                study_years  = st.number_input("Study years", 1.0, 8.0, 4.0, 0.5)
            with c_roi3:
                default_start = int((entry_lo + entry_hi) / 2)
                start_salary  = st.number_input("Starting salary (KES/mo)", 0, 1_000_000, default_start, 5_000)
            with c_roi4:
                monthly_alloc = st.number_input("Monthly tuition payback (KES)", 0, 500_000, 20_000, 1_000)
            if monthly_alloc > 0:
                months = int(tuition_cost / monthly_alloc)
                years  = months / 12
                color  = "#10b981" if years <= 5 else "#f59e0b" if years <= 10 else "#ef4444"
                st.markdown(
                    f'<div style="background:rgba(16,185,129,0.1);border:1px solid {color};'
                    f'border-radius:10px;padding:12px;margin-top:8px;text-align:center;">'
                    f'<span style="font-size:18px;font-weight:700;color:{color};">Break-even: {months} months (~{years:.1f} years)</span>'
                    f'<div style="font-size:12px;color:#94a3b8;margin-top:4px;">'
                    f'Based on KES {monthly_alloc:,}/month repayment on KES {tuition_cost:,} total tuition</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
            else:
                st.warning("Set a positive monthly payback amount to compute ROI.")

        # Why hybrid matters
        st.markdown(" ")
        st.markdown("""
        <div style="background:rgba(30,58,138,0.2);padding:18px;border-radius:12px;
                    border:1px solid rgba(99,102,241,0.3);margin-top:8px;">
            <h5 style="color:#a5b4fc;margin-top:0;">🧠 Why We Use a Hybrid Market Model</h5>
            <p style="font-size:13px;color:#cbd5e1;margin-bottom:0;">
                In the Kenyan economy, passion alone can be financially risky.
                Our <b>Hybrid Recommender</b> balances your dreams with economic reality by weighing:<br>
                1. <b>Job Stability</b> — consistent hiring trends from MyJobMag & BrighterMonday.<br>
                2. <b>Salary Potential</b> — higher demand reliably correlates with more competitive packages.<br>
                3. <b>Future-Proofing</b> — we flag roles at risk from automation, so your investment holds.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with tabs[2]:
        # Skills readiness and micro-certifications (for top 1–3)
        st.markdown("### Skills Readiness & Micro-Certifications")
        top_for_skills = recommendations[:1]
        for rec in top_for_skills:
            dept = rec['dept']
            owned_key = f"skills_owned_{dept}"
            if owned_key not in st.session_state:
                st.session_state[owned_key] = []
            st.markdown(f"**{dept}** — mark skills you already have:")
            cols = st.columns(3)
            for i, s in enumerate(rec.get('skills', [])[:9]):  # type: ignore
                with cols[i % 3]:
                    checked = s in st.session_state[owned_key]
                    val = st.checkbox(s, value=checked, key=f"own_{dept}_{i}")
                    if val and s not in st.session_state[owned_key]:
                        st.session_state[owned_key].append(s)
                    if (not val) and s in st.session_state[owned_key]:
                        st.session_state[owned_key].remove(s)
            gaps = [s for s in rec.get('skills', [])[:9] if s not in st.session_state[owned_key]]  # type: ignore
            if gaps:
                st.caption("Gap skills to prioritize:")
                st.markdown("".join([f"- {g}\n" for g in gaps]))
            sugg = MICROCERTS.get(dept, MICROCERTS.get("Business", []))
            st.info("Suggested micro-certifications: " + ", ".join(sugg))
        st.markdown('<div class="glass-card"><h3 style="margin-top:0;">🛠️ Competency Roadmap</h3><p style="color: var(--secondary);">To move from "Student" to "Market Leader", you must layer these three skill sets. This is your blueprint for the next 4 years.</p></div>', unsafe_allow_html=True)
        
        for idx, rec in enumerate(recommendations[:3]):
            with st.container():
                st.markdown(f"#### {idx+1}. Roadmap for {rec['dept']}")
                
                c1, c2, c3 = st.columns(3)
                
                # Phase 1: Foundation
                with c1:
                    header_html = "".join([
                        '<div style="text-align: center; border: 1px solid #e2e8f0; border-radius: 10px; padding: 15px; height: 100%;">',
                        '<div style="font-size: 24px; margin-bottom: 10px;">📚</div>',
                        '<div style="font-weight: 700; color: #1e293b; margin-bottom: 5px;">Year 1-2: Foundation</div>',
                        '<div style="font-size: 12px; color: #64748b; margin-bottom: 15px;">Focus on core academic principles found in your degree curriculum.</div>',
                        '<div style="display: flex; flex-wrap: wrap; gap: 5px; justify-content: center;">'
                    ])
                    st.markdown(header_html, unsafe_allow_html=True)
                    
                    for s in rec.get('skills', [])[:3]:
                        st.markdown(f'<span style="background:#e0f2fe; color:#0369a1; padding: 4px 10px; border-radius: 15px; font-size: 11px; font-weight: 600;">{s}</span>', unsafe_allow_html=True)
                    st.markdown("</div></div>", unsafe_allow_html=True)

                # Phase 2: Market Differentiation
                with c2:
                    header_html = "".join([
                        '<div style="text-align: center; border: 1px solid #d1fae5; background: #f0fdfa; border-radius: 10px; padding: 15px; height: 100%;">',
                        '<div style="font-size: 24px; margin-bottom: 10px;">⚡</div>',
                        '<div style="font-weight: 700; color: #065f46; margin-bottom: 5px;">Year 3: Market Edge</div>',
                        '<div style="font-size: 12px; color: #047857; margin-bottom: 15px;">Self-taught skills that employers are actively hiring for right now.</div>',
                        '<div style="display: flex; flex-wrap: wrap; gap: 5px; justify-content: center;">'
                    ])
                    st.markdown(header_html, unsafe_allow_html=True)
                    
                    _all_skills = rec.get('skills', [])
                    m_skills = _all_skills[3:6] if len(_all_skills) > 3 else ["Data Analysis", "Project Tools"]
                    for s in m_skills:
                        st.markdown(f'<span style="background:#d1fae5; color:#047857; padding: 4px 10px; border-radius: 15px; font-size: 11px; font-weight: 600;">{s}</span>', unsafe_allow_html=True)
                    st.markdown("</div></div>", unsafe_allow_html=True)

                # Phase 3: Leadership
                with c3:
                    header_html = "".join([
                        '<div style="text-align: center; border: 1px solid #f3e8ff; border-radius: 10px; padding: 15px; height: 100%;">',
                        '<div style="font-size: 24px; margin-bottom: 10px;">🚀</div>',
                        '<div style="font-weight: 700; color: #6b21a8; margin-bottom: 5px;">Year 4+: Leadership</div>',
                        '<div style="font-size: 12px; color: #7e22ce; margin-bottom: 15px;">Traits that will get you promoted to Management.</div>',
                        '<div style="display: flex; flex-wrap: wrap; gap: 5px; justify-content: center;">'
                    ])
                    st.markdown(header_html, unsafe_allow_html=True)
                    
                    l_skills = ["Strategic Thinking", "Communication", "Agile Leadership"]
                    for s in l_skills:
                        st.markdown(f'<span style="background:#f3e8ff; color:#7e22ce; padding: 4px 10px; border-radius: 15px; font-size: 11px; font-weight: 600;">{s}</span>', unsafe_allow_html=True)
                    st.markdown("</div></div>", unsafe_allow_html=True)

                st.markdown(" ")
                _tip_skills = rec.get('skills', ['your core subject'])
                st.info(f"**Pro Tip**: To stand out in *{rec.get('dept', 'this field')}*, build a portfolio project that demonstrates **{_tip_skills[0]}** before you graduate.", icon="🎓")
                
                st.divider()


    # E. AI ADVISORY CHATBOT (Gemini-powered or Local Heuristic fallback)
    st.markdown("---")
    
    # Detect which engine is active
    _gemini_key: str = str(st.session_state.get("gemini_api_key", "")).strip()
    _gemini_active = bool(_gemini_key)

    # Header with engine badge
    _badge = (
        '<span style="background:#10b981;color:#fff;font-size:11px;padding:2px 8px;'
        'border-radius:12px;font-weight:700;margin-left:8px;">✨ Gemini AI</span>'
        if _gemini_active else
        '<span style="background:#6366f1;color:#fff;font-size:11px;padding:2px 8px;'
        'border-radius:12px;font-weight:600;margin-left:8px;">⚡ Heuristic Mode</span>'
    )
    st.markdown(
        f'<h3 style="display:flex;align-items:center;gap:4px;">💬 Career Advisor Chat {_badge}</h3>',
        unsafe_allow_html=True
    )

    if not _gemini_active:
        st.caption("💡 Paste your free **Gemini API key** in the sidebar to unlock full AI chat.")

    if "messages" not in st.session_state:
        intro = (
            "✨ **Gemini AI is active!** I've read your full profile and recommendations. "
            "Ask me anything — from salaries to specific university admission requirements!"
            if _gemini_active else
            "I've analyzed your results. I'm here to help you strategize. "
            "Click a topic below or type your own question!"
        )
        st.session_state.messages = [{"role": "ai", "content": intro}]

    # Chat Container
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.messages:
            m_class = "chat-ai" if msg["role"] == "ai" else "chat-user"
            st.markdown(f'<div class="chat-bubble {m_class}">{msg["content"]}</div>', unsafe_allow_html=True)

    # Quick Actions
    st.markdown("###### 💡 Quick Topics:")
    q1, q2, q3, q4 = st.columns(4)
    b_prompt = None
    with q1:
        if st.button("💰 Salary?", width='stretch'): b_prompt = "What is the salary outlook for my top career path?"
    with q2:
        if st.button("🎓 Universities?", width='stretch'): b_prompt = "Which universities and colleges offer courses relevant to my results?"
    with q3:
        if st.button("🤖 AI Risk?", width='stretch'): b_prompt = "Will AI replace this job in the next 10 years?"
    with q4:
        if st.button("🚀 Success Tip?", width='stretch'): b_prompt = "What is the single most important thing I can do to succeed quickly in this field?"

    u_input = st.chat_input("Ask your own question...")
    prompt = b_prompt if b_prompt else u_input

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Build student context dict for Gemini
        _student_context: dict = {
            "grades":               st.session_state.get("kcse_grades", {}),
            "interests":            st.session_state.get("user_profile_text", "Not specified"),
            "mean_grade":           st.session_state.get("mean_grade_letter", "N/A"),
            "kcse_points":          st.session_state.get("total_points", "N/A"),
            "target_qualification": st.session_state.get("_target_level_prev", "All"),
        }

        # ── GEMINI PATH ─────────────────────────────────────────────────────
        if _gemini_active:
            with st.spinner("✨ Gemini is thinking…"):
                try:
                    from models.gemini_advisor import GeminiAdvisor  # type: ignore
                    advisor = GeminiAdvisor(_gemini_key)
                    # Pass history excluding the latest user message (already appended)
                    _history = [m for m in st.session_state.messages[:-1]]
                    response = advisor.chat(
                        user_message=str(prompt),
                        history=_history,
                        recommendations=recommendations,
                        student_context=_student_context,
                    )
                except Exception as _gem_err:
                    response = f"⚠️ Gemini error: {_gem_err}. Falling back to heuristic advice."
                    _gemini_active = False  # will drop to heuristic next time

        # ── HEURISTIC FALLBACK PATH ─────────────────────────────────────────
        if not _gemini_active:
            # Heuristic Logic Variables
            top_rec = recommendations[0]
            p_low = str(prompt).lower()

            # Default coaching response
            response = "That's a sophisticated question! As your AI Career Advisor, I can help you with:\n\n1. **Economic Clarity**: Ask about *salaries, marketability, or job availability*.\n2. **Learning Path**: Ask about *skills, certificates, or difficulty*.\n3. **Academic Guidance**: Ask about *university courses or KUCCPS programs*.\n4. **Future-Proofing**: Ask about *AI impact or long-term growth*.\nWhat would you like to dive into first?"
            # 1. WHY THIS CAREER?
            if any(w in p_low for w in ["why", "reason", "because", "fit"]):
                skills_0 = top_rec['skills'][0] if top_rec.get('skills') else "Core Skills"
                match_pct = str(int(top_rec['final_score'] * 100)) + "%"
                response = f"Excellent question. I recommended **{top_rec['dept']}** as your #1 match based on a 360-degree analysis:\n\n- **Passion Alignment**: Your interests show a **{match_pct} semantic match** with the core curriculum of this field. This suggests you'll find the work intrinsically motivating.\n- **Market Demand**: With **{top_rec['job_count']} live vacancies** in Kenya, this field has strong hiring momentum. It's a career with a future.\n- **Skill Synergy**: Your profile indicates a potential aptitude for **{skills_0}**, a critical skill for success in this domain."
            # 2. MARKETABILITY & JOBS
            elif any(w in p_low for w in ["market", "demand", "job", "vacancy", "available"]):
                response = f"Let's talk about market dynamics. **{top_rec['dept']}** is currently a high-demand field in Kenya for a few key reasons:\n\n- **Economic Sector Growth**: This area is seeing significant investment, driving companies to expand their teams.\n- **Talent Scarcity**: There are fewer qualified professionals than available roles, which gives you, the candidate, more leverage.\n- **The Verdict**: With **{top_rec['job_count']} active roles**, your skills are highly marketable. I recommend focusing your job search on major urban hubs to start."

            # 3. SALARY & MONEY
            elif any(w in p_low for w in ["salary", "money", "pay", "earn", "income", "compensation"]):
                demand_pct = str(int(top_rec['demand_score'] * 100)) + "%"
                response = f"You're right to consider the financial aspect. The outlook for **{top_rec['dept']}** is strong, primarily due to 'demand-pull' inflation on wages:\n\n- **High Demand Premium**: The market demand score is **{demand_pct}**. In simple terms, when demand outstrips supply, salaries are forced upwards.\n- **Strategic Advice**: To maximize your earning potential, focus on mastering the 'Salary Booster' skills mentioned in the roadmap. A strong portfolio of practical projects can help you command a top-tier starting salary."

            # 4. SKILLS & CERTIFICATES
            elif any(w in p_low for w in ["skill", "learn", "study", "certificate", "master"]):
                s_list = top_rec.get('skills', [])
                f_skill = s_list[0] if len(s_list) > 0 else "Fundamentals"
                i_skill = s_list[3] if len(s_list) > 3 else "Advanced Industry Tools"
                response = f"To become a top-tier candidate in **{top_rec['dept']}**, you need a 'T-shaped' skill set—deep expertise in one area, broad knowledge in others. Here's your learning path:\n\n- **Foundational Pillar (The 'Must-Have')**: You must be proficient in **{f_skill}**. This is the non-negotiable entry ticket.\n- **Competitive Edge (The 'Salary Booster')**: To truly stand out and increase your value, master **{i_skill}**. This skill is frequently requested in job descriptions for senior roles."

            # 5. KUCCPS, UNIVERSITY & PROGRAM QUERIES
            elif any(w in p_low for w in ["university", "universit", "course", "program", "kuccps",
                                           "degree", "diploma", "where", "college", "institute",
                                           "institution", "offer"]):
                all_prog_details: list[tuple[str, str, str]] = []
                seen_progs: set[str] = set()
                for rec in recommendations:
                    uni_map_h: dict = rec.get('university_mapping', {})  # type: ignore[annotation-unchecked]
                    for prog, unis in uni_map_h.items():
                        prog_str = str(prog)
                        if prog_str in seen_progs or prog_str.startswith('__'):
                            continue
                        seen_progs.add(prog_str)
                        if unis:
                            unis_sub = list(unis)[:3] if isinstance(unis, list) else [str(unis)]  # type: ignore
                            uni_list = ', '.join([str(u) for u in unis_sub if u])
                            all_prog_details.append((prog_str, uni_list, str(rec['dept'])))
                    elig_map_h: dict = rec.get('eligibility', {})  # type: ignore[annotation-unchecked]
                    for prog, elig_data in elig_map_h.items():
                        prog_str = str(prog)
                        if prog_str in seen_progs or prog_str.startswith('__'):
                            continue
                        elig_dict_h: dict = elig_data if isinstance(elig_data, dict) else {}  # type: ignore[annotation-unchecked]
                        if elig_dict_h.get('status') == 'ELIGIBLE':
                            seen_progs.add(prog_str)
                            unis_fb: list = uni_map_h.get(prog_str, [])  # type: ignore[annotation-unchecked]
                            unis_sub2 = list(unis_fb)[:3]  # type: ignore
                            uni_str2 = ', '.join(str(u) for u in unis_sub2) if unis_fb else 'Multiple TVET Institutions (confirm on kuccps.net)'
                            all_prog_details.append((prog_str, uni_str2, str(rec['dept'])))

                if not all_prog_details:
                    response = "I couldn't find specific institution data for your eligible programs. Please visit **[kuccps.net](https://www.kuccps.net)** and use the program search to get the most up-to-date listings and cluster points."
                else:
                    prog_uni_detail = ""
                    top_8_h = list(all_prog_details)[:8]  # type: ignore
                    for prog_item, uni_item, dept_item in top_8_h:  # type: ignore
                        prog_uni_detail += f"- **{prog_item}** *(under {dept_item})*: {uni_item}\n"
                    if len(all_prog_details) > 8:
                        prog_uni_detail += f"\n*...and {len(all_prog_details) - 8} more. See 🎓 Academic Eligibility above.*"
                    response = f"Here are the institutions offering your **eligible programs** across all recommended career paths:\n\n{prog_uni_detail}\n💡 *For TVET/Diploma courses, verify at **kuccps.net** for the latest intake and cluster points.*"

            # 6. AI IMPACT & FUTURE-PROOFING
            elif any(w in p_low for w in ["ai", "future", "automation", "replace", "robot"]):
                s_strat = top_rec['skills'][2] if len(top_rec.get('skills', [])) > 2 else 'Strategic Thinking'
                response = f"A very forward-thinking question. Here's my analysis of AI's impact on **{top_rec['dept']}**:\n\n- **Role Evolution, Not Replacement**: AI handles repetitive tasks, freeing you for complex problem-solving and client management—areas where humans excel.\n- **Your Strategic Advantage**: By mastering **{s_strat}**, you become an 'AI-augmented' professional, making you more valuable, not less."

            # 7. DIFFICULTY & EFFORT
            elif any(w in p_low for w in ["hard", "difficult", "easy", "challenge", "tough"]):
                s_core = top_rec['skills'][0] if top_rec.get('skills') else "Core Concepts"
                response = f"The difficulty for **{top_rec['dept']}** is manageable with the right strategy:\n\n- **The Core Challenge**: Mastering **{s_core}** requires consistent effort and a logical mindset.\n- **Your Potential**: Based on your profile, you have the foundational aptitude. This path is 'Challenging, but Rewarding'."

            # 8. NETWORKING & INTERNSHIPS
            elif any(w in p_low for w in ["network", "internship", "attachment", "body", "society"]):
                networking_hub = {
                    "Finance & Accounting": "ICPAK", "Engineering": "IEK & EBK",
                    "Information Technology": "CSK & iHub", "Healthcare & Medical": "KMA",
                    "Law": "LSK", "Agriculture & Agribusiness": "ASK",
                    "Education": "TSC", "Media & Communications": "MCK"
                }.get(top_rec['dept'], "a relevant professional body")
                first_skill = top_rec['skills'][0] if top_rec.get('skills') else "domain knowledge"
                response = f"Building your professional network is just as important as your skills. For **{top_rec['dept']}**:\n\n- **Key Professional Body**: Connect with **{networking_hub}**. Look for student membership options.\n- **Internship Strategy**: In your cover letter, highlight your expertise in **{first_skill}** to show you are ready to contribute."

            # 9. ALTERNATIVES
            elif any(w in p_low for w in ["another", "else", "alternative", "other", "instead"]):
                if len(recommendations) > 1:
                    alt = recommendations[1]
                    alt_skill = alt['skills'][0] if alt.get('skills') else "Technical Skills"
                    alt_match = str(int(alt['final_score'] * 100)) + "%"
                    response = f"Your #2 recommendation is **{alt['dept']}** with a **{alt_match} match**.\n\nThis is a strong alternative if you have interest in **{alt_skill}** and want to explore a different career path."
                else:
                    response = "Your profile has a uniquely strong alignment with your top recommendation. I advise focusing your energy on the primary path for now."

            # 10. BRIDGING & UPGRADING
            elif any(w in p_low for w in ["bridge", "upgrade", "tvet", "foundation"]):
                status = top_rec.get('dept_status', 'ELIGIBLE')
                if status == "ASPIRATIONAL":
                    response = "For an 'Aspirational' path, a **Diploma or Pre-University Certificate** in a related field is the best bridge strategy. It builds the academic foundation needed for Degree entry."
                elif status == "ELIGIBLE (DIPLOMA)":
                    response = "Your Diploma eligibility is the perfect launchpad! Excel in your Diploma program, then use **lateral entry** to progress into a Degree program later."
                else:
                    response = "While you qualify for a Degree directly, specialized Diplomas or certifications *after* graduation can make you a niche expert and significantly boost your earning potential."

            # 11. POLITE CLOSING — whole-word match to avoid 'hi' in 'which' false-positive
            elif any(f' {w} ' in f' {p_low} ' or p_low.startswith(w) or p_low.endswith(w)
                     for w in ["thank", "thanks", "bye", "goodbye", "hello", "hi"]):
                response = "You're welcome! Feel free to ask anything — salary expectations, best skills, university options, or how to bridge into your dream degree!"

        st.session_state.messages.append({"role": "ai", "content": response})
        st.rerun()

st.markdown("---")
st.caption(f"© {date.today().year} AI Career Recommender | Kenyan Edition")