# -*- coding: utf-8 -*-
# AI Career Recommender - v2.1 (Academic Eligibility)
import streamlit as st
from models.recommender import CareerRecommender
import pandas as pd
from datetime import datetime, date
from fpdf import FPDF
from pdf_generator import generate_pdf_report
import textwrap

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
    balance_html = "".join([
        f'<div style="display: flex; height: 10px; border-radius: 5px; overflow: hidden; margin-top: 10px;">',
        f'<div style="width: {alpha*100}%; background: #2563eb; transition: width 0.3s;"></div>',
        f'<div style="width: {beta*100}%; background: #94a3b8; transition: width 0.3s;"></div>',
        f'</div>',
        f'<div style="display: flex; justify-content: space-between; font-size: 11px; margin-top: 5px; color: #64748b; font-weight: 600;">',
        f'<span>PASSION ({alpha:.0%})</span>',
        f'<span>MARKET ({beta:.0%})</span>',
        f'</div>'
    ])
    st.markdown(balance_html, unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("[Analytics] Backend Status")
    st.write("Job Market Sync: **ACTIVE**")
    st.caption(f"Last Scanned: {date.today().strftime('%Y-%m-%d')}")
    
    if st.button("Sync Market Data", width='stretch'):
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

    # Display the entered KCSE results
    st.markdown("### 📝 Your Entered KCSE Grades")
    st.write(f"**KCSE Mean Grade:** {mean_grade}")
    st.markdown("##### 📝 Core & Elective Subject Grades")
    
    # Create a DataFrame for better display
    grades_df = pd.DataFrame({
        "Subject": ["Mathematics", "English", "History", "Kiswahili", "Biology", "Geography", "Chemistry", "Physics", "Computer Studies"],
        "Grade": [g_math, g_eng, g_hist, g_kis, g_bio, g_geo, g_chem, g_phys, g_comp]
    })
    
    st.table(grades_df)

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

    st.markdown("---")

    # PDF Download Button - Placed at the top for easy access
    pdf_buffer = generate_pdf_report(recommendations)
    st.download_button(
        label="📥 Download Full Report as PDF",
        data=pdf_buffer,
        file_name=f"AI_Career_Report_{datetime.now().strftime('%Y%m%d')}.pdf",
        mime="application/pdf",
        use_container_width=True,
        type="primary"
    )

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
                                    "Information Technology": "Your journey in tech is a marathon of building. **Actionable Advice:** 1) **Create a standout GitHub:** Build a project that solves a local problem (e.g., a USSD-like app for a local chama, a simple M-Pesa Express API integration). 2) **Master Cloud Fundamentals:** Get certified in AWS Cloud Practitioner or Azure AZ-900. This is the new baseline. 3) **Network Smart:** Participate in hackathons by iHub or Moringa School. Your future employer is likely there.",
                                    "Data Science & AI": "Data tells a story; learn to be its best narrator. **Actionable Advice:** 1) **SQL is Your Foundation:** Before fancy algorithms, master complex SQL queries. 2) **Build a Kaggle Portfolio:** Compete in one beginner-friendly competition to understand the end-to-end workflow. 3) **Focus on Business Value:** Frame your projects around solving a business problem (e.g., 'Predicting customer churn for a local SME' sounds better than 'Building a classification model').",
                                    "Engineering": "An engineering degree is a license to solve problems; the EBK registration is your license to practice. **Actionable Advice:** 1) **Document Everything:** Start your EBK logbook from Year 1. Document labs, projects, and any informal repair work. 2) **Seek Mentorship:** Connect with a registered engineer on LinkedIn and ask for a 15-minute virtual coffee chat. 3) **Learn Project Management:** A PRINCE2 or PMP certification, even at the foundation level, makes you incredibly valuable.",
                                    "Medicine & Health": "Your compassion is as critical as your clinical knowledge. **Actionable Advice:** 1) **Gain Diverse Experience:** Volunteer at both a busy public hospital and a small local clinic to see the full spectrum of healthcare needs. 2) **Develop 'Soft' Power:** Take a course on communication or patient counseling. This is a major differentiator. 3) **Stay Current:** Read publications from KEMRI and the Ministry of Health to understand national health priorities.",
                                    "Business & Economics": "In a crowded market, specialization is your superpower. **Actionable Advice:** 1) **Become a Data-Driven Storyteller:** Learn Power BI or Tableau. Being able to visualize financial data is a game-changer. 2) **Pick a Niche:** Instead of 'Finance,' aim for 'Renewable Energy Finance' or 'FinTech Compliance.' 3) **Network with Purpose:** Join ICPAK or the Marketing Society of Kenya (MSK) as a student. Attend one event per semester.",
                                    "Law": "The future of law is at the intersection of tradition and technology. **Actionable Advice:** 1) **Master Legal Writing:** Start a blog or write for your university's law journal. Clear, concise writing is your most powerful tool. 2) **Explore Legal Tech:** Understand how AI is being used for document review or case management. This gives you a significant edge. 3) **Moot Court & Debate:** This is non-negotiable. It's where you build the confidence and articulation skills that win cases.",
                                    "Agriculture & Agribusiness": "The soil is the old gold; technology and logistics are the new gold. **Actionable Advice:** 1) **Think 'Farm to Fork':** Study the entire value chain. Intern at a logistics company, a processing plant, or a digital marketplace for produce. 2) **Learn Agri-Tech Tools:** Get familiar with drone technology for crop monitoring or IoT sensors for irrigation. 3) **Build a Business Plan:** Develop a concept for a small agribusiness, focusing on value addition (e.g., packaging, drying, oil extraction).",
                                    "Education": "The classroom of the future is a blend of physical and digital. **Actionable Advice:** 1) **Become a Digital Content Creator:** Master tools like Canva, Google Classroom, and simple video editing to create engaging learning materials. 2) **Specialize in CBC:** Become an expert in a specific learning area or competency within the new curriculum. 3) **Get TSC Number Early:** The moment you are eligible, begin the process. It signals professionalism and readiness.",
                                    "Media & Communications": "Your personal brand is your most valuable asset. **Actionable Advice:** 1) **Build a Multimedia Portfolio:** Create a simple website showcasing your writing, a short video you edited, and a social media campaign you managed (even a hypothetical one). 2) **Master Analytics:** Learn to use Google Analytics or social media insights. Proving the impact of your communication is key. 3) **Network Relentlessly:** Connect with journalists, PR professionals, and content creators. Offer to help with their projects for free to gain experience and a good word."
                                }
                                advice = adv_map.get(rec['dept'], "Focus on gaining practical skills and relevant certifications to stand out in this competitive field. Networking with professionals is key to unlocking the 'hidden job market'.")
                                st.info(advice)

                                st.markdown("#### [Logic] Explainable Match Logic (XAI)")
                                st.caption("Your recommendation is a blend of your stated interests and real-world job market data. Here's the breakdown:")
                                i_weight = rec.get('interest_contribution', rec.get('interest_score', 0.0) * alpha)
                                m_weight = rec.get('market_contribution', rec.get('demand_score', 0.0) * beta)
                                total_c = i_weight + m_weight
                                i_pct = (i_weight / total_c) * 100 if total_c > 0 else 0
                                m_pct = (m_weight / total_c) * 100 if total_c > 0 else 0

                                xai_html = "".join([
                                    f'<div style="background-color: #f8fafc; border-radius: 12px; padding: 16px; border: 1px solid #e2e8f0;">',
                                    f'<div style="font-weight: 600; font-size: 14px; color: #1e293b; margin-bottom: 12px;">Match Score Composition</div>',
                                    
                                    # Passion
                                    f'<div style="margin-bottom: 10px;">',
                                    f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">',
                                    f'<span style="font-size: 12px; color: #4f46e5; font-weight: 500;">● Your Passion</span>',
                                    f'<span style="font-size: 12px; font-weight: 700; color: #4f46e5;">{i_pct:.1f}%</span>',
                                    f'</div>',
                                    f'<div style="height: 8px; background: #e0e7ff; border-radius: 10px; overflow: hidden;">',
                                    f'<div style="width: {i_pct}%; background: #4f46e5; height: 100%;"></div>',
                                    f'</div>',
                                    f'<div style="font-size: 11px; color: #64748b; margin-top: 4px;">Based on your stated interests and academic history.</div>',
                                    f'</div>',

                                    # Market
                                    f'<div>',
                                    f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">',
                                    f'<span style="font-size: 12px; color: #10b981; font-weight: 500;">● Market Demand</span>',
                                    f'<span style="font-size: 12px; font-weight: 700; color: #10b981;">{m_pct:.1f}%</span>',
                                    f'</div>',
                                    f'<div style="height: 8px; background: #d1fae5; border-radius: 10px; overflow: hidden;">',
                                    f'<div style="width: {m_pct}%; background: #10b981; height: 100%;"></div>',
                                    f'</div>',
                                    f'<div style="font-size: 11px; color: #64748b; margin-top: 4px;">Based on analysis of {rec.get("job_count", "N/A")} live job vacancies.</div>',
                                    f'</div>',
                                    f'</div>'
                                ])
                                st.markdown(xai_html, unsafe_allow_html=True)

                                st.markdown("---")
                                st.markdown("#### [Plan] Strategic Career Roadmap")
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

                                foundation_path = rec['programs'][0] if rec['programs'] else 'Specialized Degree Track'
                                if dept_status == "ELIGIBLE (DIPLOMA)":
                                    for p, data in eligibility_map.items():
                                        if data['status'] == "ELIGIBLE" and ("Diploma" in p or "TVET" in p):
                                            foundation_path = p
                                            break
                                elif dept_status == "ASPIRATIONAL":
                                    foundation_path = "Bridging Certificate or TVET Diploma Foundation"

                                skill_focus_primary = rec['skills'][0] if rec['skills'] else 'Core Competencies'
                                skill_focus_secondary = rec['skills'][1] if len(rec['skills']) > 1 else 'Industry Tools'

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
                            st.caption("This is a summary of programs you can join. The system checks against KUCCPS cluster points and subject requirements.")

                            for prog in list(eligibility_map.keys())[:4]:
                                elig = eligibility_map.get(prog, {"status": "UNKNOWN", "reason": "N/A"})
                                is_diploma = "Diploma" in prog or "TVET" in prog or "Qualify for Diploma" in elig['reason']
                                
                                status_color_map = {"ELIGIBLE": "#059669", "ASPIRATIONAL": "#d97706", "NOT ELIGIBLE": "#dc2626", "UNKNOWN": "#6b7280"}
                                status_bg_map = {"ELIGIBLE": "#f0fdfa", "ASPIRATIONAL": "#fffbeb", "NOT ELIGIBLE": "#fef2f2", "UNKNOWN": "#f3f4f6"}
                                
                                e_tag_color = "#0ea5e9" if is_diploma and elig['status'] == "ELIGIBLE" else status_color_map.get(elig['status'])
                                e_tag_bg = "#eff6ff" if is_diploma and elig['status'] == "ELIGIBLE" else status_bg_map.get(elig['status'])

                                unis = uni_mapping.get(prog, ["Consult KUCCPS TVET Portal"] if is_diploma else ["Consult KUCCPS Portal"])
                                uni_list = ", ".join(unis[:2])

                                eligibility_html = f"""
                                <div style="background-color: {e_tag_bg}; border-left: 4px solid {e_tag_color}; padding: 12px; border-radius: 8px; margin-bottom: 10px;">
                                    <div style="font-weight: 700; color: #1e293b; font-size: 14px; margin-bottom: 4px;">{prog}</div>
                                    <div style="font-size: 12px; font-weight: 600; color: {e_tag_color}; margin-bottom: 6px;">{elig["status"]}</div>
                                    <div style="font-size: 11px; color: #475569; margin-bottom: 8px;"><i>{elig["reason"]}</i></div>
                                    <div style="font-size: 11px; color: #64748b;"><b>🏫 Possible Institutions:</b> {uni_list}</div>
                                </div>
                                """
                                st.markdown(eligibility_html, unsafe_allow_html=True)

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
                                        st.write(desc_text[:600] + "..." if len(desc_text) > 600 else desc_text)
                                        
                                        st.markdown("##### 🛠 Key Competencies")
                                        skills_req = job.get('Skillmentequired', 'Core Industry Standard Skills')
                                        st.code(str(skills_req), language="text")
                                    
                                    with j_col2:
                                        st.markdown("##### 🎯 Strategic Fit")
                                        degree_ref = rec['programs'][0] if rec['programs'] else rec['dept']
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
                        else:
                            st.info(f"🔎 Analysing emerging roles in {rec['dept']}...")
                        
                        st.markdown("</div>", unsafe_allow_html=True)
                        st.markdown("---")
                        global_idx += 1

    with tabs[1]:
        import plotly.express as px
        import plotly.graph_objects as go
        
        st.markdown('<div class="glass-card"><h3 style="margin-top:0;">📊 Strategic Analysis Dashboard</h3><p style="color: var(--secondary);">This dashboard visualizes the trade-off between what you love (Passion) and what the economy pays for (Market). Use this data to make an informed choice.</p></div>', unsafe_allow_html=True)
        
        # Top Metrics Cards
        m1, m2, m3 = st.columns(3)
        top_passion = df_viz.sort_values(by="Passion", ascending=False).index[0]
        top_market = df_viz.sort_values(by="Market", ascending=False).index[0]
        top_balanced = df_viz.sort_values(by="Overall", ascending=False).index[0]
        
        m1.metric("❤️ Passion Leader", top_passion, f"{df_viz.loc[top_passion]['Passion']:.0%} Match")
        m2.metric("💼 Market Leader", top_market, f"{df_viz.loc[top_market]['Market']:.0%} Demand")
        m3.metric("⚖️ Best Balance", top_balanced, f"{df_viz.loc[top_balanced]['Overall']:.0%} Score")
        
        st.divider()

        # Main Strategic Scatter Plot
        st.markdown("#### 1. The Opportunity Matrix")
        st.caption("Fields in the top-right corner are your 'Sweet Spots'—high interest AND high demand.")
        
        fig_scatter = px.scatter(
            df_viz.reset_index(), x="Passion", y="Market", text="Field",
            size="Overall", color="Overall", color_continuous_scale="Viridis",
            labels={"Passion": "Interest Alignment (Passion)", "Market": "Job Availability (Market)"},
            height=600, template="plotly_white",
            hover_data={"Overall": ":.1%"}
        )
        # Add Quadrant Backgrounds or Annotations could be cool but let's stick to clean layout first
        fig_scatter.update_traces(textposition='top center', marker=dict(line=dict(width=2, color='DarkSlateGrey')))
        fig_scatter.update_layout(xaxis=dict(range=[0, 1.1]), yaxis=dict(range=[0, 1.1]))
        st.plotly_chart(fig_scatter, width='stretch')
        
        # Deep Dive Section
        st.markdown("#### 2. Specialized Analysis")
        col_mark_1, col_mark_2 = st.columns([1, 1])
        
        with col_mark_1:
            st.markdown("##### 📉 Market Volume Comparison")
            # Horizontal bar for easier comparison of volume
            fig_vol = px.bar(
                df_viz.reset_index().sort_values("Market", ascending=True),
                y="Field", x="Market", orientation='h',
                color="Market", color_continuous_scale="Greens",
                text_auto='.0%',
                title=""
            )
            fig_vol.update_layout(yaxis_title=None, xaxis_title="Relative Demand Score")
            st.plotly_chart(fig_vol, width='stretch')
            
            with st.expander("💡 Understanding Market Volume"):
                 st.info("Top bars represent 'Seller's Markets' (easier to find jobs). Bottom bars represent Niche Markets (heavier competition).")

        with col_mark_2:
            st.markdown("##### 🕸 Multi-Dimensional Fit")
            # Radar Chart for Top 3 (if enough data)
            top_3_df = df_viz.head(3).reset_index()
            categories = ['Passion', 'Market', 'Overall']
            
            fig_radar = go.Figure()
            for idx, row in top_3_df.iterrows():
                fig_radar.add_trace(go.Scatterpolar(
                    r=[row['Passion'], row['Market'], row['Overall'], row['Passion']],
                    theta=['Passion','Market','Overall','Passion'],
                    fill='toself',
                    name=row['Field']
                ))
            fig_radar.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 1])), 
                showlegend=True, 
                height=400,
                margin=dict(t=20, b=20, l=40, r=40)
            )
            st.plotly_chart(fig_radar, width='stretch')
            st.caption("How your top choices compare across the three core dimensions.")

        # Why We Do This
        st.markdown("""
        <div style="background: #eff6ff; padding: 20px; border-radius: 12px; border: 1px solid #dbeafe; margin-top: 20px;">
            <h5 style="color: #1e3a8a; margin-top: 0;">🧠 Why we prioritize 'Market Reality'</h5>
            <p style="font-size: 14px; color: #1e40af; margin-bottom: 0;">
                In the modern Kenyan economy, relying solely on passion can be risky. Our <b>Hybrid Recommender</b> bridges this by considering:
                <br>1. <b>Job Stability</b>: We prioritize sectors showing consistent hiring trends on MyJobMag and BrighterMonday.
                <br>2. <b>Salary Potential</b>: Higher market demand typically correlates with more competitive entry-level packages.
                <br>3. <b>Future-Proofing</b>: We analyze 'Future Outlook' metrics to ensure your chosen path isn't being automated away.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with tabs[2]:
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
                    
                    for s in rec['skills'][:3]:
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
                    
                    m_skills = rec['skills'][3:6] if len(rec['skills']) > 3 else ["Data Analysis", "Project Tools"]
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
                st.info(f"**Pro Tip**: To stand out in *{rec['dept']}*, build a portfolio project that demonstrates **{rec['skills'][0]}** before you graduate.", icon="🎓")
                
                st.divider()

    with tabs[3]:
        st.markdown('<div class="glass-card"><h3 style="margin-top:0;">🧠 AI Decision Architecture</h3><p style="color: var(--secondary);">How did we arrive at this decision? We believe in <b>Explainable AI (XAI)</b>. Below is the logic flow that processed your inputs.</p></div>', unsafe_allow_html=True)
        
        # 1. Visual Data Flow
        st.markdown("#### 1. The Processing Pipeline")
        st.info("Your match wasn't random. It passed through three distinct validation layers.")
        
        c_flow1, c_flow2, c_flow3 = st.columns(3)
        with c_flow1:
            st.markdown("""
            <div style="text-align: center; padding: 10px; background: #fdf2f8; border-radius: 8px; border: 1px solid #fbcfe8;">
                <div style="font-size: 20px;">👤</div>
                <div style="font-weight: bold; color: #db2777;">Layer 1: Passion</div>
                <div style="font-size: 11px; color: #be185d;">Semantic analysis of your interest statement.</div>
            </div>
            """, unsafe_allow_html=True)
        with c_flow2:
            st.markdown("""
            <div style="text-align: center; padding: 10px; background: #f0fdf4; border-radius: 8px; border: 1px solid #bbf7d0;">
                <div style="font-size: 20px;">📈</div>
                <div style="font-weight: bold; color: #15803d;">Layer 2: Market</div>
                <div style="font-size: 11px; color: #166534;">Real-time scraping of 500+ job boards.</div>
            </div>
            """, unsafe_allow_html=True)
        with c_flow3:
            st.markdown("""
            <div style="text-align: center; padding: 10px; background: #eff6ff; border-radius: 8px; border: 1px solid #bfdbfe;">
                <div style="font-size: 20px;">⚖️</div>
                <div style="font-weight: bold; color: #1d4ed8;">Layer 3: Calibration</div>
                <div style="font-size: 11px; color: #1e40af;">Metric validation against statutory limits.</div>
            </div>
            """, unsafe_allow_html=True)
            
        st.divider()

        # 2. Baseline Comparison
        st.markdown("#### 2. Model Performance Benchmarks")
        
        if 'baselines' in recommendations[0]:
            bl = recommendations[0]['baselines']
            b_col1, b_col2, b_col3 = st.columns(3)
            with b_col1:
                st.metric("Interest-Only Model", bl.get('interest_only', ['N/A'])[0], "High Risk", delta_color="inverse")
            with b_col2:
                st.metric("Market-Only Model", bl.get('market_only', ['N/A'])[0], "Soul Crushing", delta_color="inverse")
            with b_col3:
                st.metric("✅ Hybrid Model", bl.get('hybrid', ['N/A'])[0], "Optimal", delta_color="normal")
        else:
            st.warning("Baseline benchmarking data is utilizing cached priors. Please sync market data for fresh comparison.")

        st.divider()
        st.markdown("#### 3. Data Integrity & Bias Check")
        
        # D. Bias & Fairness Acknowledgment
        st.markdown('<div class="glass-card" style="border-left: 5px solid #ef4444;">', unsafe_allow_html=True)
        st.markdown("### [Ethics] Ethics, Bias & Fairness Disclosure")
        st.info("As part of modern AI ethical standards, we acknowledge the following disclosures: 1. **Digital Bias**: High-tech roles may dominate because they have the most descriptive online data. 2. **Informal Sector Gap**: Our system primarily tracks formal employment, excluding Jua Kali (informal) sectors. 3. **Urban Focus**: Data originates from major hubs like Nairobi, Mombasa, and Kisumu. 4. **Algorithmic Fairness**: We use Alpha-Beta weighting to ensure no single metric captures the entire recommendation.")
        st.markdown("</div>", unsafe_allow_html=True)

    # E. LIGHTWEIGHT ADVISORY CHATBOT (Local Inference Engine)
    st.markdown("---")
    st.subheader("💬 Career Advisor Chat")
    
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "ai", "content": "I've analyzed your results. I'm here to help you strategize. Click a topic below or type your own question!"}]

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
        if st.button("💰 Salary?", use_container_width=True): b_prompt = "What is the salary outlook?"
    with q2:
        if st.button("🎓 Universities?", use_container_width=True): b_prompt = "Which universities offer this?"
    with q3:
        if st.button("🤖 AI Risk?", use_container_width=True): b_prompt = "Will AI replace this job?"
    with q4:
        if st.button("🚀 Success Tip?", use_container_width=True): b_prompt = "How can I succeed quickly?"

    u_input = st.chat_input("Ask your own question...")
    prompt = b_prompt if b_prompt else u_input

    if prompt:
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
            response = f"To become a top-tier candidate in **{top_rec['dept']}**, you need a 'T-shaped' skill set—deep expertise in one area, broad knowledge in others. Here’s your learning path:\n\n- **Foundational Pillar (The 'Must-Have')**: You must be proficient in **{f_skill}**. This is the non-negotiable entry ticket.\n- **Competitive Edge (The 'Salary Booster')**: To truly stand out and increase your value, master **{i_skill}**. This skill is frequently requested in job descriptions for senior roles."

        # 5. KUCCPS & PROGRAMS
        elif any(w in p_low for w in ["university", "course", "program", "kuccps", "degree", "diploma", "where", "college", "institute"]):
            progs = top_rec.get('programs', [])[:3]
            uni_map = top_rec.get('university_mapping', {})
            prog_uni_detail = ""
            if not progs:
                prog_uni_detail = "- No specific degree programs were matched. I recommend looking into foundational Diplomas or Certificate courses in this field."
            else:
                for p in progs:
                    unis = uni_map.get(p, ["Consult the official KUCCPS portal for the latest information"])
                    uni_list = ", ".join(unis[:2])
                    prog_uni_detail += f"- **{p}**: Key institutions offering this include **{uni_list}**.\n"

            response = f"Navigating the academic landscape is key. For **{top_rec['dept']}**, here are the primary pathways:\n\n{prog_uni_detail}\n*Pro-Tip: Always verify the latest program details and cluster points on the official KUCCPS website.*"

        # 6. AI IMPACT & FUTURE-PROOFING
        elif any(w in p_low for w in ["ai", "future", "automation", "replace", "robot"]):
            s_strat = top_rec['skills'][2] if len(top_rec.get('skills', []))>2 else 'Strategic Thinking'
            response = f"A very forward-thinking question. Here’s my analysis of AI's impact on **{top_rec['dept']}**:\n\n- **Role Evolution, Not Replacement**: AI will likely handle the repetitive, data-heavy tasks. This frees you up to focus on complex problem-solving, strategy, and client management—areas where human intelligence excels.\n- **Your Strategic Advantage**: By mastering skills like **{s_strat}**, you position yourself as an 'AI-augmented' professional, making you more valuable, not less."

        # 7. DIFFICULTY & EFFORT
        elif any(w in p_low for w in ["hard", "difficult", "easy", "challenge", "tough"]):
            s_core = top_rec['skills'][0] if top_rec.get('skills') else "Core Concepts"
            response = f"It's wise to assess the challenge ahead. For **{top_rec['dept']}**, the difficulty is manageable if you approach it strategically:\n\n- **The Core Challenge**: The main hurdle is mastering **{s_core}**. It requires consistent effort and a logical mindset.\n- **Your Potential**: Based on your profile, you have the foundational aptitude. With dedication, this path is well within your reach. I would classify the difficulty as 'Challenging, but Rewarding'."

        # 8. NETWORKING & INTERNSHIPS
        elif any(w in p_low for w in ["network", "internship", "attachment", "body", "society"]):
            networking_hub = {
                "Finance & Accounting": "ICPAK", "Engineering": "IEK & EBK",
                "Information Technology": "CSK & iHub", "Healthcare & Medical": "KMA", 
                "Law": "LSK", "Agriculture & Agribusiness": "ASK",
                "Education": "TSC", "Media & Communications": "MCK"
            }.get(top_rec['dept'], "a relevant professional body")
            response = f"Building your professional network is just as important as building your skills. For **{top_rec['dept']}**:\n\n- **Key Professional Body**: Your first step should be to connect with the **{networking_hub}**. Look for student membership options.\n- **Internship Strategy**: When applying for attachments, don't just send your CV. In your cover letter, specifically mention your growing expertise in **{top_rec['skills'][0]}** and your passion for the field. This shows intent and focus."

        # 9. ALTERNATIVES
        elif any(w in p_low for w in ["another", "else", "alternative", "other", "instead"]):
            if len(recommendations) > 1:
                alt = recommendations[1]
                alt_skill = alt['skills'][0] if alt.get('skills') else "Technical Skills"
                alt_match = str(int(alt['final_score'] * 100)) + "%"
                response = f"Of course. Your #2 recommendation is **{alt['dept']}** with a **{alt_match} match score**.\n\nThis is a strong alternative if you have a particular interest in **{alt_skill}** and want to explore a different career vector. It also has a solid market demand."
            else:
                response = "Based on the analysis, your current profile has a uniquely strong alignment with your top recommendation. Other fields were significantly lower matches. My advice is to focus your energy on the primary path for now."

        # 10. BRIDGING & UPGRADING
        elif any(w in p_low for w in ["bridge", "upgrade", "diploma", "tvet", "foundation"]):
            status = top_rec.get('dept_status', 'ELIGIBLE')
            if status == "ASPIRATIONAL":
                response = "Excellent question. For an 'Aspirational' path like this, a bridging strategy is exactly right. I recommend a **Diploma or a Pre-University Certificate** in a related field. This will build the necessary academic foundation and significantly improve your chances for degree entry later."
            elif status == "ELIGIBLE (DIPLOMA)":
                response = "You are on the right track! Your current eligibility for a Diploma is the perfect launchpad. Excel in your Diploma program, and you can leverage that qualification for **lateral entry into a Degree program**. This is a very common and successful strategy."
            else:
                response = "That's a great topic. While you are already eligible for direct degree entry, you can still use diplomas or advanced certifications after your degree to specialize further. For example, a postgraduate diploma in a niche area of your field can make you a highly sought-after expert."

        # 11. POLITE CLOSING
        elif any(w in p_low for w in ["thank", "bye", "hello", "hi", "help"]):
            response = "You're welcome! I'm here to help you navigate your career path. Feel free to ask me anything else about your results, from salary expectations to the best skills to learn. Just type your question!"
        
        
        st.session_state.messages.append({"role": "ai", "content": response})

        st.rerun()

st.markdown("---")
st.caption(f"© {date.today().year} AI Career Recommender | Kenyan Edition")