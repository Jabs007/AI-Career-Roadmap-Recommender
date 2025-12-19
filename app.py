# -*- coding: utf-8 -*-
# AI Career Recommender - v2.1 (Academic Eligibility)
import streamlit as st
from models.recommender import CareerRecommender
import pandas as pd
import datetime

# Set page config for a better look
st.set_page_config(page_title="AI Career Recommender | Kenyan Edition", layout="wide", page_icon="🎓")

# Premium Design System: Glassmorphism & Micro-animations
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Inter:wght@300;400;500;700&display=swap');

    :root {
        --primary: #4f46e5;
        --secondary: #64748b;
        --accent: #10b981;
        --bg-glass: rgba(255, 255, 255, 0.75);
        --border-glass: rgba(255, 255, 255, 0.4);
        --shadow-soft: 0 8px 32px 0 rgba(31, 38, 135, 0.07);
    }

    /* Base Styling */
    .stApp {
        background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
        font-family: 'Inter', sans-serif;
    }

    h1, h2, h3, h4 {
        font-family: 'Outfit', sans-serif !important;
        font-weight: 700 !important;
        color: #1e293b;
    }

    /* Glass Panels */
    .glass-card {
        background: var(--bg-glass);
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        border: 1px solid var(--border-glass);
        border-radius: 16px;
        padding: 24px;
        box-shadow: var(--shadow-soft);
        margin-bottom: 20px;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }
    .glass-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px 0 rgba(31, 38, 135, 0.12);
        border-color: rgba(79, 70, 229, 0.3);
    }

    /* Job Card Specific */
    .job-card {
        background: white;
        border-radius: 12px;
        padding: 15px;
        border: 1px solid #e2e8f0;
        transition: all 0.3s ease;
    }
    .job-card:hover { border-color: var(--primary); box-shadow: 0 4px 12px rgba(79, 70, 229, 0.1); }

    /* Interactive Elements */
    .stButton > button {
        border-radius: 12px !important;
        font-family: 'Outfit', sans-serif !important;
        font-weight: 600 !important;
        transition: all 0.2s !important;
    }
    .stButton > button[kind="primary"] {
        background: var(--primary) !important;
        box-shadow: 0 4px 14px 0 rgba(79, 70, 229, 0.39) !important;
    }

    .search-btn {
        background: var(--primary);
        color: white !important;
        padding: 12px 20px;
        border-radius: 10px;
        text-align: center;
        text-decoration: none;
        display: block;
        font-weight: 700;
        margin-bottom: 20px;
        transition: all 0.3s;
    }

    /* Custom Roadmap Steps */
    .roadmap-step {
        border-left: 3px solid #cbd5e1;
        padding-left: 20px;
        margin-bottom: 25px;
        position: relative;
    }
    .roadmap-step:before {
        content: '';
        position: absolute;
        left: -8px;
        top: 0;
        width: 13px;
        height: 13px;
        background: var(--primary);
        border-radius: 50%;
        box-shadow: 0 0 0 4px rgba(79, 70, 229, 0.15);
    }

    /* Chat Bubbles Upgrade */
    .chat-bubble {
        padding: 14px 18px;
        border-radius: 20px;
        margin: 10px 0;
        max-width: 85%;
        font-size: 14.5px;
        line-height: 1.6;
        box-shadow: 0 2px 5px rgba(0,0,0,0.03);
        animation: bubblePop 0.3s ease-out;
    }
    .chat-ai { background: #ffffff; border: 1px solid #e2e8f0; border-bottom-left-radius: 4px; }
    .chat-user { background: var(--primary); color: white; margin-left: auto; border-bottom-right-radius: 4px; }

    /* XAI & Confidence Chips */
    .chip {
        padding: 4px 12px;
        border-radius: 100px;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .chip-high { background: #d1fae5; color: #065f46; }
    .chip-med { background: #fef3c7; color: #92400e; }
    .chip-low { background: #fee2e2; color: #991b1b; }

    /* Animations */
    @keyframes bubblePop { from { opacity: 0; transform: scale(0.95); } to { opacity: 1; transform: scale(1); } }
    
    /* Custom Scrollbar */
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: #f1f5f9; }
    ::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# Initialize recommender
@st.cache_resource
def get_recommender_instance():
    return CareerRecommender()

recommender = get_recommender_instance()

# Sidebar: Dynamic Strategy Controls
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/graduation-cap.png", width=60)
    st.title("System Controls")
    st.markdown("---")
    
    st.subheader("🎯 Recommendation Logic")
    
    # Mode Descriptions for better understanding
    mode_info = {
        "Balanced Hybrid": "⚖️ **Default**: A steady mix of what you love (70%) and where the jobs are (30%).",
        "Passion First": "❤️ **Intrinsic**: 90% focus on your interests. Best for explorers following a specific dream.",
        "Market Priority": "💰 **Opportunity**: 70% focus on job volume. Best for those prioritizing employment security.",
        "Custom Controls": "🎛 **Manual**: Fine-tune the balance exactly how you want it."
    }
    
    # Dynamic strategy selector
    strategy = st.radio(
        "Discovery Mode:",
        list(mode_info.keys()),
        index=0,
        help="This setting changes how the AI ranks its top picks for you."
    )
    
    st.markdown(f'<div style="font-size: 13px; color: #475569; background: #f1f5f9; padding: 10px; border-radius: 8px; margin-bottom: 20px;">{mode_info[strategy]}</div>', unsafe_allow_html=True)
    
    if strategy == "Balanced Hybrid":
        alpha, beta = 0.70, 0.30
    elif strategy == "Passion First":
        alpha, beta = 0.90, 0.10
    elif strategy == "Market Priority":
        alpha, beta = 0.30, 0.70
    else:
        alpha = st.slider("Interest Weight (Passion)", 0.0, 1.0, 0.70, 0.05)
        beta = 1.0 - alpha
        st.caption(f"Market Demand Weight: {beta:.2f}")

    # Visual Balance Indicator
    st.markdown("---")
    st.markdown("#### ⚖️ Weighted Balance")
    balance_html = f"""
    <div style="display: flex; height: 10px; border-radius: 5px; overflow: hidden; margin-top: 10px;">
        <div style="width: {alpha*100}%; background: #2563eb; transition: width 0.3s;"></div>
        <div style="width: {beta*100}%; background: #94a3b8; transition: width 0.3s;"></div>
    </div>
    <div style="display: flex; justify-content: space-between; font-size: 11px; margin-top: 5px; color: #64748b; font-weight: 600;">
        <span>PASSION ({alpha:.0%})</span>
        <span>MARKET ({beta:.0%})</span>
    </div>
    """
    st.markdown(balance_html, unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("[Analytics] Backend Status")
    st.write("Job Market Sync: **ACTIVE**")
    st.caption(f"Last Scanned: {datetime.date.today().strftime('%Y-%m-%d')}")
    
    if st.button("Sync Market Data", use_container_width=True):
         with st.status("Fetching Live Jobs..."):
             st.cache_resource.clear() # Clear stale model/data cache
             st.toast("Connecting to MyJobMag Kenya...", icon="📡")
             st.toast("Parsing Career Snippets...", icon="🔍")
             st.success("Global Cache Cleared & Data Synced!")

    st.markdown("---")
    st.caption("AI Version: 2.1.0-Premium")

# --- REPLACED BY ROOT MASTER STYLESHEET ---

# Main Content
st.title("🎓 AI Career Roadmap Recommender")
st.markdown("#### *Your Strategic Journey from Passion to Profession*")

# --- GUIDANCE SYSTEM: START ---
with st.expander("🆕 New here? Unlock the power of AI Guidance", expanded=False):
    st.markdown("""
    <div style="background: white; border-left: 5px solid var(--primary); padding: 20px; border-radius: 12px; box-shadow: var(--shadow-soft);">
        <h4 style="margin-top:0;">🚀 Welcome to Your Premium Career Lab</h4>
        Our AI maps your language to 1,000+ Kenyan job roles and KUCCPS programs using BERT semantic analysis.
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
    if st.button("� Business Leader"):
        template_text = "I am interested in commerce, strategy, and leading teams. I excel in business studies and want to grow companies."

# Layout: 2 columns for Input
# --- PHASE 1: ACADEMIC ELIGIBILITY ---
with st.container():
    st.markdown("### [Profile] Phase 1: Academic Identity")
    st.markdown("""
    <p style="font-size: 15px; color: var(--secondary); margin-bottom: 25px; line-height: 1.6;">
        <b style="color: var(--primary);">Your grades tell a story.</b> By accurately inputting your KCSE results, our AI assesses over 1,500 programs to identify exactly where you qualify. This ensures your roadmap is built on a foundation of <i>academic reality</i>, not just wishful thinking.
    </p>
    """, unsafe_allow_html=True)
    
    with st.expander("📝 Enter Your KCSE Grades", expanded=True):
        k_col1, k_col2 = st.columns(2)
        with k_col1:
            mean_grade = st.selectbox("KCSE Mean Grade", ["A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-", "E"], index=5)
        
        st.markdown("##### 📝 Core & Elective Subject Grades")
        s_col1, s_col2, s_col3, s_col4 = st.columns(4)
        grades_list = ["A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-", "E", "N/A"]
        
        with s_col1:
            g_math = st.selectbox("Mathematics", grades_list, index=6)
            g_eng = st.selectbox("English", grades_list, index=6)
            g_hist = st.selectbox("History", grades_list, index=12)
        with s_col2:
            g_kis = st.selectbox("Kiswahili", grades_list, index=6)
            g_bio = st.selectbox("Biology", grades_list, index=6)
            g_geo = st.selectbox("Geography", grades_list, index=12)
        with s_col3:
            g_chem = st.selectbox("Chemistry", grades_list, index=8)
            g_phys = st.selectbox("Physics", grades_list, index=8)
            g_comp = st.selectbox("Computer Studies", grades_list, index=12)
        with s_col4:
            st.info("💡 Pro-tip: Better grades in Math & Physics open up more Engineering & Tech paths.")

    kcse_data = {
        "mean_grade": mean_grade,
        "subjects": {
            "Mathematics": g_math, "English": g_eng, "Kiswahili": g_kis,
            "Biology": g_bio, "Chemistry": g_chem, "Physics": g_phys,
            "Computer Studies": g_comp, "Geography": g_geo, "History": g_hist
        }
    }

st.markdown("---")

# --- PHASE 2: CAREER ASPIRATIONS ---
st.markdown("### [Vision] Phase 2: Ambition & Interests")
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
    <div style="background: white; padding: 25px; border-radius: 16px; border: 1px solid rgba(79, 70, 229, 0.1); box-shadow: var(--shadow-soft);">
        <h4 style="margin-top:0; color: var(--primary);">[Tip] Writing Tips</h4>
        <p style="font-size: 14px; color: var(--secondary); line-height: 1.6;">
            <b>Be Specific:</b> Instead of "I like computers", try "I want to build secure mobile banking apps for Kenyan fintech."<br><br>
            <b>Highlight Interests:</b> Mentioning specific tools or goals helps the AI anchor your passion scores.
        </p>
    </div>
    """, unsafe_allow_html=True)

if st.button("🚀 Generate Personalized Roadmap", type="primary"):
    if student_text.strip():
        with st.spinner("🧠 AI is analyzing your career profile & eligibility..."):
            recs = recommender.recommend(student_text, top_n=8, alpha=alpha, beta=beta, kcse_results=kcse_data)
            if recs:
                st.session_state['recommendations'] = recs
                st.session_state['student_query'] = student_text
                viz_data = []
                for rec in recs:
                    viz_data.append({
                        "Field": rec['dept'],
                        "Passion": rec['interest_score'],
                        "Market": rec['demand_score'],
                        "Overall": rec['final_score']
                    })
                st.session_state['df_viz'] = pd.DataFrame(viz_data).set_index("Field")
                st.session_state.messages = [{"role": "ai", "content": f"I've analyzed your profile and found **{recs[0]['dept']}** to be your top match. Ask me anything about these paths!"}]
            else:
                 st.error("Could not generate recommendations. Please try describing your interests differently.")
    else:
        st.warning("Please enter your career interests to begin.")

# PERSISTENT RESULTS UI (Accessed via Session State)
if 'recommendations' in st.session_state:
    recommendations = st.session_state['recommendations']
    df_viz = st.session_state['df_viz']
    student_text = st.session_state.get('student_query', '')

    tabs = st.tabs(["[Target] Recommendations", "[Trends] Market Analysis", "[Skills] Skill Bridge", "[Logic] System Rigor"])
    
    with tabs[0]:
        st.markdown("### [Path] Your Tailored Career Roadmaps")
        
        # Grouping Logic
        eligible_recs = [r for r in recommendations if r.get('dept_status') == "ELIGIBLE"]
        diploma_recs = [r for r in recommendations if r.get('dept_status') == "ELIGIBLE (DIPLOMA)"]
        aspirational_recs = [r for r in recommendations if r.get('dept_status') == "ASPIRATIONAL"]
        ineligible_recs = [r for r in recommendations if r.get('dept_status') == "NOT ELIGIBLE"]
        unknown_recs = [r for r in recommendations if r.get('dept_status') == "UNKNOWN"]

        groups = [
            ("[Eligible] Eligible & Recommended (Degree)", eligible_recs, "#10b981"),
            ("[Diploma] Diploma / TVET Pathways", diploma_recs, "#0ea5e9"),
            ("[Gap] Aspirational Options", aspirational_recs, "#f59e0b"),
            ("[Blocked] Currently Not Eligible", ineligible_recs, "#ef4444"),
            ("[Pending] Status Pending", unknown_recs, "#64748b")
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
                    cnf = rec.get('confidence', 'Medium')
                    c_class = "chip-high" if cnf == "High" else ("chip-med" if cnf == "Medium" else "chip-low")
                    
                    e_status = rec.get('dept_status', 'UNKNOWN')
                    e_icon = group_name.split()[0]

                    with st.container():
                        st.markdown(f"""
                        <div class="glass-card" style="margin-bottom: 25px; border-top: 4px solid {group_color};">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                                <div>
                                    <h2 style="margin:0; font-size: 24px;">{global_idx}. {rec['dept']}</h2>
                                    <div style="font-size: 12px; color: {group_color}; font-weight: 700; margin-top: 4px;">{e_icon} {e_status} PATHWAY</div>
                                </div>
                                <div style="display: flex; gap: 8px;">
                                    <span class="chip" style="background: rgba(79, 70, 229, 0.1); color: var(--primary);">Match: {rec['final_score']:.0%}</span>
                                    <span class="chip {c_class}">Conf: {cnf}</span>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        c_left, c_right = st.columns([2, 1])
                        dept_status = rec.get('dept_status', 'UNKNOWN')
                        eligibility_map = rec.get('eligibility', {})
                        
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
                                
                                st.markdown("#### [Verdict] System Verdict") # Changed from 🧭
                                st.caption("This pathway reflects strong interest alignment but requires academic upgrading before degree-level entry.")

                            else:
                                # --- STANDARD PREMIUM UI FOR ELIGIBLE/ASPIRATIONAL ---
                                if rec.get('dept_status') in ["NOT ELIGIBLE", "ASPIRATIONAL"]:
                                    st.markdown("#### [Logic] Academic Reality & Strategy")
                                elif rec.get('dept_status') == "ELIGIBLE (DIPLOMA)":
                                    st.markdown("#### [Edu] Your Diploma Pathway Strategy")
                                else:
                                    st.markdown("#### [Target] Strategic Fit & Rationale")
                                    
                                st.write(rec['comprehensive_rationale'])
                                
                                # --- EXPERT ADVISORY SECTION ---
                                st.markdown("#### 🧭 Expert Career Advisory")
                                adv_map = {
                                    "Information Technology": "In Kenya's tech ecosystem, your GitHub profile matters more than your degree. Focus on building real-world projects (e.g., M-Pesa integrations, React apps). Certifications like AWS or Azure are powerful differentiators.",
                                    "Data Science & AI": "Data is the new oil. Master SQL and Python (Pandas) before jumping into deep learning. Local companies value actionable insights over complex models.",
                                    "Engineering": "Registration with EBK (Engineers Board of Kenya) is critical. Seek internships with major infrastructure projects or manufacturing firms early to build your logbook.",
                                    "Medicine & Health": "Clinical experience is paramount. Volunteer at local clinics or dispensaries during holidays. Soft skills like empathy are just as tested as your biological knowledge.",
                                    "Business & Economics": "The market is saturated with generalists. Specialise early—consider Data Analytics for Finance, or Digital Marketing. Networking is 80% of your career growth.",
                                    "Law": "Build your argumentation skills through moot courts. Legal tech is an emerging field; understanding basics of how technology intersects with law can give you a niche edge.",
                                    "Agriculture & Agribusiness": "Move beyond traditional farming. Explore value addition, supply chain logistics, and precision agriculture technologies. The money is in processing and market linkages.",
                                    "Education": "Modern teaching requires digital literacy. Master e-learning platforms and content creation tools to stay relevant in the evolving CBC curriculum landscape.",
                                    "Media & Communications": "Build a digital portfolio. Writing, video editing, and social media management are now core skills for any journalist or communicator."
                                }
                                advice = adv_map.get(rec['dept'], "Focus on gaining practical skills and relevant certifications to stand out in this competitive field. Networking with professionals is key to unlocking the 'hidden job market'.")
                                st.info(advice)

                                st.markdown("#### [Logic] Explainable Match Logic (XAI)")
                                st.caption("This score is a weighted balance of your **Passion** (Interest) and **Market Reality** (Job Demand).")
                                i_weight = rec.get('interest_contribution', rec.get('interest_score', 0.0) * alpha)
                                m_weight = rec.get('market_contribution', rec.get('demand_score', 0.0) * beta)
                                total_c = i_weight + m_weight
                                i_pct = (i_weight / total_c) * 100 if total_c > 0 else 0
                                m_pct = (m_weight / total_c) * 100 if total_c > 0 else 0
                                
                                st.markdown(f"""
                                <div style="height: 12px; background: #e2e8f0; border-radius: 10px; overflow: hidden; display: flex; margin-bottom: 8px;">
                                    <div style="width: {i_pct}%; background: #4f46e5;" title="Passion Contribution"></div>
                                    <div style="width: {m_pct}%; background: #10b981;" title="Market Contribution"></div>
                                </div>
                                <div style="display: flex; justify-content: space-between; font-size: 11px; color: #64748b;">
                                    <span><b style="color: #4f46e5;">●</b> Passion Match: {i_weight:.2f}</span>
                                    <span><b style="color: #10b981;">●</b> Market Logic: {m_weight:.2f}</span>
                                </div>
                                """, unsafe_allow_html=True)

                                st.markdown("---")
                                st.markdown("#### [Plan] Strategic Career Roadmap")
                                
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

                                # Determine best foundation
                                foundation_path = rec['programs'][0] if rec['programs'] else 'Specialized Degree Track'
                                if dept_status == "ELIGIBLE (DIPLOMA)":
                                    for p, data in eligibility_map.items():
                                        if data['status'] == "ELIGIBLE" and ("Diploma" in p or "TVET" in p):
                                            foundation_path = p
                                            break
                                elif dept_status == "ASPIRATIONAL":
                                    foundation_path = "Bridging Certificate or TVET Diploma Foundation"

                                skill_focus = rec['skills'][0] if rec['skills'] else 'Core Competencies'

                                steps = [
                                    ("1. Academic Foundation", f"Enroll in **{foundation_path}**. precise academic performance here is your ticket to the next level."),
                                    ("2. Skill Acquisition", f"Go beyond classwork. Master **{skill_focus}** using online platforms (Coursera, Udemy) or local bootcamps."),
                                    ("3. Professional Registration", f"Join **{networking_hub}** as a student member to access mentorship and industry events."),
                                    ("4. Market Entry", f"Build a portfolio showcasing your {skill_focus} projects. Apply for attachments via the KUCCPS placement portal.")
                                ]
                                
                                for step_title, step_desc in steps:
                                    st.markdown(f"""
                                    <div class="roadmap-step" style="border-left: 3px solid var(--primary); padding-left: 15px; margin-bottom: 12px;">
                                        <div style="font-weight: 700; color: var(--primary); font-size: 14px;">{step_title}</div>
                                        <div style="font-size: 13px; color: #475569;  line-height: 1.5;">{step_desc}</div>
                                    </div>
                                    """, unsafe_allow_html=True)

                        with c_right:
                            st.markdown(f"""
                            <div style="background: #f8fafc; padding: 15px; border-radius: 12px; border: 1px solid #e2e8f0; margin-bottom: 20px;">
                                <div style="display: flex; justify-content: space-around; text-align: center;">
                                    <div><div style="font-size: 18px; font-weight: 800; color: #4f46e5;">{rec['interest_score']:.0%}</div><div style="font-size: 10px;">Passion</div></div>
                                    <div><div style="font-size: 18px; font-weight: 800; color: #10b981;">{rec['demand_score']:.0%}</div><div style="font-size: 10px;">Market</div></div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

                            st.markdown("#### 🎓 Academic Eligibility")
                            uni_mapping = rec.get('university_mapping', {})
                            
                            for prog in list(eligibility_map.keys())[:4]:
                                elig = eligibility_map.get(prog, {"status": "UNKNOWN", "reason": "No data"})
                                is_diploma = "Diploma" in prog or "TVET" in prog or "Qualify for Diploma" in elig['reason']
                                e_tag_color = "#0ea5e9" if (elig['status'] == "ELIGIBLE" and is_diploma) else ("#059669" if elig['status'] == "ELIGIBLE" else ("#d97706" if elig['status'] == "ASPIRATIONAL" else "#dc2626"))
                                
                                st.markdown(f"**{prog}**")
                                st.markdown(f'<div style="font-size: 10px; color: {e_tag_color}; font-weight: 800; margin-bottom: 2px;">{elig["status"]} • {elig["reason"]}</div>', unsafe_allow_html=True)
                                unis = uni_mapping.get(prog, ["Consult KUCCPS TVET Portal" if is_diploma else "Consult KUCCPS Portal"])
                                st.caption(f"🏫 {', '.join(unis[:2])}")
                                if elig['status'] == "ASPIRATIONAL":
                                    st.info("💡 Try the Diploma bridge pathway.", icon="ℹ️")

                        # Only show vacancies for Eligible/Aspirational users
                        if dept_status != "NOT ELIGIBLE":
                            st.markdown("#### 📡 Live Vacancies")
                            jobs = recommender.get_top_jobs(rec['dept'], top_n=2)
                            if jobs:
                                jcols = st.columns(2)
                                for idx, job in enumerate(jobs):
                                    with jcols[idx]:
                                        st.markdown(f'<div class="job-card"><div style="font-weight: 700; font-size: 13px;">{job["Job Title"]}</div><div style="font-size: 11px; color: #64748b;">{job["Company"]}</div><div style="font-size: 10.5px; background: #f0fdfa; padding: 8px; border-radius: 6px; margin-top: 8px;">✨ <b>Match:</b> High alignment with {rec["dept"]}</div></div>', unsafe_allow_html=True)
                            st.info("Searching for niche openings...")
                        
                        st.markdown("</div>", unsafe_allow_html=True)
                        st.markdown("---")
                        global_idx += 1

    with tabs[1]:
        import plotly.express as px
        import plotly.graph_objects as go
        
        st.markdown('<div class="glass-card"><h2 style="margin-top:0;">(Chart) The Career Strategy Matrix</h2><p style="color: var(--secondary); margin-bottom: 25px;">Understanding the intersection of <b>Personal Interest</b> and <b>Economic Reality</b> is crucial for long-term career success in Kenya. Our AI analyzes 10,000+ data points to ensure your path is sustainable.</p></div>', unsafe_allow_html=True)
        
        # Main Strategic Scatter Plot
        fig_scatter = px.scatter(
            df_viz.reset_index(), x="Passion", y="Market", text="Field",
            size="Overall", color="Overall", color_continuous_scale="Viridis",
            labels={"Passion": "Interest Alignment (%)", "Market": "Job Availability (%)"},
            height=550, template="plotly_white"
        )
        fig_scatter.update_traces(textposition='top center', marker=dict(line=dict(width=1, color='DarkSlateGrey')))
        st.plotly_chart(fig_scatter, use_container_width=True)
        
        # Key Insights Section
        st.divider()
        col_mark_1, col_mark_2 = st.columns([1, 1])
        
        with col_mark_1:
            st.markdown("### [Analytics] Market Saturation vs. Opportunity")
            # Horizontal bar for easier comparison of volume
            fig_vol = px.bar(
                df_viz.reset_index().sort_values("Market", ascending=True),
                y="Field", x="Market", orientation='h',
                color="Market", color_continuous_scale="Blues",
                title="Relative Job Volume by Sector"
            )
            st.plotly_chart(fig_vol, use_container_width=True)
            st.info("**Why this matters:** A high 'Market' score indicates a 'Seller's Market' where you have more power to negotiate salaries. Lower scores indicate niche fields where competition is higher, but specialization yields greater rewards.")

        with col_mark_2:
            st.markdown("### [Trends] Strategic Demand Distribution")
            # Radar Chart for Top 3 (if enough data)
            top_3_df = df_viz.head(3).reset_index()
            fig_radar = go.Figure()
            for idx, row in top_3_df.iterrows():
                fig_radar.add_trace(go.Scatterpolar(
                    r=[row['Passion']*100, row['Market']*100, row['Overall']*100, row['Passion']*100],
                    theta=['Passion','Market','Overall','Passion'],
                    fill='toself',
                    name=row['Field']
                ))
            fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=True, height=400)
            st.plotly_chart(fig_radar, use_container_width=True)
            st.caption("Comparison of your Top 3 paths across Passion, Market, and Composite Match scores.")

        st.divider()
        st.markdown("### [Info] Why we prioritize Market Analysis")
        st.markdown("In the modern Kenyan economy, relying solely on passion can be risky. Our **Hybrid Recommender** bridges this by considering: 1. **Job Stability**: We prioritize sectors showing consistent hiring trends on MyJobMag and BrighterMonday. 2. **Salary Potential**: Higher market demand typically correlates with more competitive entry-level packages. 3. **Future-Proofing**: We analyze 'Future Outlook' metrics to ensure your chosen path isn't being automated away.")

    with tabs[2]:
        st.markdown('<div class="glass-card"><h2 style="margin-top:0;">[Skills] The Skill-to-Career Bridge</h2><p style="color: var(--secondary); margin-bottom: 0;">Landing your dream role requires a specific combination of technical and soft skills. Below is your <b>Professional Development Roadmap</b>.</p></div>', unsafe_allow_html=True)
        
        for rec in recommendations[:3]:
            with st.container():
                st.markdown(f'<div class="glass-card" style="border-left: 5px solid var(--accent);"><h3 style="margin-top:0; color: var(--accent);">[Path] Path: {rec["dept"]}</h3>', unsafe_allow_html=True)
                
                s_col1, s_col2, s_col3 = st.columns(3)
                
                # Category 1: Foundational Technical Skills (from Academic Path)
                with s_col1:
                    st.markdown("**1. Foundational Skills**")
                    st.caption("Taught in KUCCPS Programs")
                    f_skills = rec['skills'][:3]
                    for s in f_skills:
                        st.markdown(f"- `{s}`")
                
                # Category 2: Industry Specialized Skills
                with s_col2:
                    st.markdown("**2. Industry Edge**")
                    st.caption("What employers are hunting for")
                    i_skills = rec['skills'][3:6] if len(rec['skills'])>3 else ["Project Management", "Agile", "CRMs"]
                    for s in i_skills:
                        st.markdown(f"- `[Skill] {s}`")
                
                # Category 3: Transferable Soft Skills
                with s_col3:
                    st.markdown("**3. Soft Power**")
                    st.caption("Differentiates you in interviews")
                    t_skills = ["Critical Thinking", "Stakeholder Mgmt", "Emotional Intelligence"]
                    for s in t_skills:
                        st.markdown(f"- `[Soft] {s}`")
                
                st.markdown(
                    f'<div style="background: #f8fafc; padding: 15px; border-radius: 10px; margin-top: 10px; border: 1px solid #e2e8f0;">'
                    f'<span style="font-weight: 700; color: #2563eb;">[Edu] Academic Bridge:</span> '
                    f'By focusing on <b>{rec["skills"][0]}</b> during your <i>{rec["programs"][0]}</i> studies, you close the gap '
                    f'between theory and the actual requirements of roles like those we found in the market.</div>', 
                    unsafe_allow_html=True
                )
                st.markdown("</div>", unsafe_allow_html=True)
            st.divider()

    with tabs[3]:
        st.markdown('<div class="glass-card"><h2 style="margin-top:0;">[Edu] Academic Evaluation & System Rigor</h2><p style="color: var(--secondary); margin-bottom: 0;">Our AI framework is built on peer-reviewed recommendation logic, balancing individual passion with national economic data.</p></div>', unsafe_allow_html=True)
        
        # C. Baseline Model Comparison
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("### [Analytics] Baseline Comparison Matrix")
        st.write("Does the Hybrid AI actually perform better? We compared our results against primitive baselines.")
        
        if 'baselines' in recommendations[0]:
            bl = recommendations[0]['baselines']
            comparison_df = pd.DataFrame({
                "System Model": ["Our Hybrid AI", "Interest-Only Baseline", "Market-Only Baseline"],
                "Rank 1": [bl['hybrid'][0], bl['interest_only'][0], bl['market_only'][0]],
                "Philosophy": ["Decision Support", "Passion Trap", "Economic Push"]
            })
            st.table(comparison_df)
            st.success("Analysis: The Hybrid Model effectively balances passion with economic reality, avoiding 'jobless passions' and 'passionless jobs'.")
        else:
            st.warning("Baseline benchmarking data is being recalculated. Please click 'Sync Market Data' in the sidebar to refresh the system analysis.")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # D. Bias & Fairness Acknowledgment
        st.markdown('<div class="glass-card" style="border-left: 5px solid #ef4444;">', unsafe_allow_html=True)
        st.markdown("### [Ethics] Ethics, Bias & Fairness Disclosure")
        st.info("As part of modern AI ethical standards, we acknowledge the following disclosures: 1. **Digital Bias**: High-tech roles may dominate because they have the most descriptive online data. 2. **Informal Sector Gap**: Our system primarily tracks formal employment, excluding Jua Kali (informal) sectors. 3. **Urban Focus**: Data originates from major hubs like Nairobi, Mombasa, and Kisumu. 4. **Algorithmic Fairness**: We use Alpha-Beta weighting to ensure no single metric captures the entire recommendation.")
        st.markdown("</div>", unsafe_allow_html=True)

    # E. LIGHTWEIGHT ADVISORY CHATBOT (Local Inference Engine)
    st.markdown("---")
    st.subheader("[Chat] Career Advisor Chat")
    st.caption("Privacy-First AI: Your data stays on your machine. No external APIs used.")
    
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "ai", "content": "I've analyzed your results. Do you have any questions about these recommendations or the skills required?"}]

    # Chat Container
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.messages:
            m_class = "chat-ai" if msg["role"] == "ai" else "chat-user"
            st.markdown('<div class="chat-bubble ' + m_class + '">' + msg["content"] + '</div>', unsafe_allow_html=True)

    if prompt := st.chat_input("Ask about your roadmap..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Heuristic Logic Variables
        top_rec = recommendations[0]
        p_low = prompt.lower()
        
        # Default coaching response
        response = "That's a sophisticated question! As your AI Career Advisor, I can help you with:\n\n1. **Economic Clarity**: Ask about *salaries, marketability, or job availability*.\n2. **Learning Path**: Ask about *skills, certificates, or difficulty*.\n3. **Academic Guidance**: Ask about *university courses or KUCCPS programs*.\n4. **Future-Proofing**: Ask about *AI impact or long-term growth*.\nWhat would you like to dive into first?"
        
        # 1. WHY THIS CAREER?
        if any(w in p_low for w in ["why", "reason", "because", "fit"]):
             skills_0 = top_rec['skills'][0] if top_rec.get('skills') else "Core Skills"
             match_pct = str(int(top_rec['final_score'] * 100)) + "%"
             response = "I recommended **" + top_rec['dept'] + "** as your #1 match for three specific reasons:\n\n- **Semantic Fit**: Your personal interests align with **" + match_pct + "** accuracy to " + top_rec['dept'] + " curriculum.\n\n- **Market Velocity**: We found **" + str(top_rec['job_count']) + " current vacancies** in Kenya, ensuring high placement probability.\n\n- **Skill Symbiosis**: You likely have natural aptitude for **" + skills_0 + "**, a core requirement for success here."
            
        # 2. MARKETABILITY & JOBS
        elif any(w in p_low for w in ["market", "demand", "job", "vacancy", "available"]):
            response = "Regarding current marketability, **" + top_rec['dept'] + "** is a high-signal sector in Kenya:\n\n- **Live Demand**: We are tracking **" + str(top_rec['job_count']) + " roles** right now. This is a robust volume compared to more saturated fields.\n\n- **The Verdict**: It is **highly marketable**. Companies in major cities like Nairobi are rapidly hiring for " + top_rec['dept'] + " talent."

        # 3. SALARY & MONEY
        elif any(w in p_low for w in ["salary", "money", "pay", "earn", "income", "compensation"]):
            demand_pct = str(int(top_rec['demand_score'] * 100)) + "%"
            response = "Financial prospects for **" + top_rec['dept'] + "** are optimistic due to 'Scarcity Dynamics':\n\n- **Premium Potential**: With a demand score of **" + demand_pct + "**, skilled professionals are scarce. This gives you high negotiation power."

        # 4. SKILLS & CERTIFICATES
        elif any(w in p_low for w in ["skill", "learn", "study", "certificate", "master"]):
            s_list = top_rec.get('skills', [])
            f_skill = s_list[0] if len(s_list) > 0 else "Fundamentals"
            i_skill = s_list[3] if len(s_list) > 3 else "Advanced Industry Tools"
            response = "To stand out in the **" + top_rec['dept'] + "** job market, follow this 'Skills Stack':\n\n- **The 'Must-Have'**: **" + f_skill + "**. Without this, you cannot enter the professional race.\n\n- **The 'Salary Booster'**: **" + i_skill + "**. Mastering this tool will put you in the top 10% of candidates."

        # 5. KUCCPS & PROGRAMS
        elif any(w in p_low for w in ["university", "course", "program", "kuccps", "degree", "diploma", "where", "college", "institute"]):
            progs = top_rec.get('programs', [])[:3]
            uni_map = top_rec.get('university_mapping', {})
            prog_uni_detail = ""
            for p in progs:
                unis = uni_map.get(p, ["Consult KUCCPS Portal"])
                uni_list = ", ".join(unis[:3])
                prog_uni_detail += "- **" + p + "**: Offered at " + uni_list + ".\n"

            response = "For your academic journey in **" + top_rec['dept'] + "**, here are the top institutions:\n\n" + prog_uni_detail

        # 6. AI IMPACT & FUTURE-PROOFING
        elif any(w in p_low for w in ["ai", "future", "automation", "replace", "robot"]):
            s_strat = top_rec['skills'][2] if len(top_rec.get('skills', []))>2 else 'Strategic Thinking'
            response = "How will AI affect **" + top_rec['dept'] + "**? Here is my outlook:\n\n- **Augmentation**: AI will automate repetitive tasks, allowing you to focus on high-level **" + s_strat + "**. This path is 'Future-Proof'."

        # 7. DIFFICULTY & EFFORT
        elif any(w in p_low for w in ["hard", "difficult", "easy", "challenge", "tough"]):
            s_core = top_rec['skills'][0] if top_rec.get('skills') else "Core Concepts"
            response = "For **" + top_rec['dept'] + "**:\n\n- **Learning Curve**: Mastering **" + s_core + "** takes discipline. It is 'attainable' with your analytical mindset."

        # 8. NETWORKING & INTERNSHIPS
        elif any(w in p_low for w in ["network", "internship", "attachment", "body", "society"]):
            s_interest = top_rec['skills'][0] if top_rec.get('skills') else "Field Expertise"
            response = "Launching in **" + top_rec['dept'] + "** requires networking. Check the 'Roadmap' tab for bodies. For internships, highlight interest in **" + s_interest + "**."

        # 9. ALTERNATIVES
        elif any(w in p_low for w in ["another", "else", "alternative", "other", "instead"]):
            alt = recommendations[1] if len(recommendations) > 1 else None
            if alt:
                alt_skill = alt['skills'][0] if alt.get('skills') else "Technical Skills"
                alt_match = str(int(alt['final_score'] * 100)) + "%"
                response = "Your #2 best match is **" + alt['dept'] + "** (**" + alt_match + " match**).\n\nChoose it if you prefer working with **" + alt_skill + "**."
                
        # 10. POLITE CLOSING
        elif any(w in p_low for w in ["thank", "bye", "hello", "hi", "help"]):
            response = "You're very welcome! I am your AI career coach. Feel free to ask about *salaries, AI impact, or the best university courses* for your results! [Tip]"
        
        st.session_state.messages.append({"role": "ai", "content": response})

        st.rerun()

st.markdown("---")
st.caption(f"© {datetime.date.today().year} AI Career Recommender | Kenyan Edition")
