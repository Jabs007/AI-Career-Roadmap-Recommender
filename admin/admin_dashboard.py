import streamlit as st # type: ignore
import pandas as pd
import os
import subprocess
import sys
from core.auth import get_all_users, set_user_admin_status # type: ignore
from datetime import datetime

# Enforce Security for the Standalone Admin Server
if not st.session_state.get("admin_authenticated"):
    st.error("Unauthorized Access. Please login via the Secure Admin Gateway.")
    st.stop()
    
# Admin Logout
if st.sidebar.button("Logout of Command Center"):
    st.session_state["admin_authenticated"] = False
    st.rerun()

st.title("🛡️ Secure Admin Command Center")
st.markdown("Welcome to the Command Center. Manage your platform, users, and ETL pipelines below.")

tab_users, tab_etl, tab_health, tab_analytics = st.tabs(["👥 User Management", "⚙️ ETL Operations", "📊 Data Health", "📈 User Reports"])

with tab_users:
    st.subheader("Registered Users Directory")
    users = get_all_users()
    if users:
        df = pd.DataFrame(users, columns=["ID", "Username", "Email", "First Name", "Last Name", "Is Admin"])
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        st.markdown("### 🔑 Role Management")
        c1, c2 = st.columns(2)
        with c1:
            selected_user = st.selectbox("Select User", df["Username"].tolist())
        with c2:
            new_role = st.radio("Access Level", ["User", "Admin"], horizontal=True)
            
        if st.button("Update Role", type="primary"):
            is_admin_flag = True if new_role == "Admin" else False
            if set_user_admin_status(selected_user, is_admin_flag):
                st.success(f"Successfully updated '{selected_user}' to {new_role}.")
                st.rerun()
            else:
                st.error("Failed to update role. See console.")
    else:
        st.info("No users found in database.")

with tab_etl:
    st.subheader("Data Pipeline Controls")
    st.markdown("Trigger backend web scrapers and sync routines. *Note: Running scripts will block the UI until complete.*")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 1. Fetch Fresh Jobs")
        st.caption("Runs `update_jobs.py` to scrape MyJobMag and backup old files into CSV locally.")
        if st.button("🚀 Run Cloud Scraper"):
            with st.spinner("Scraping in progress... this may take a few minutes."):
                try:
                    env = os.environ.copy()
                    env["PYTHONIOENCODING"] = "utf-8"
                    result = subprocess.run([sys.executable, 'update_jobs.py'], cwd=os.path.dirname(__file__), capture_output=True, text=True, env=env)
                    st.success("Scraper executed successfully!")
                    with st.expander("View Output Log"):
                        st.code(result.stdout)
                except Exception as e:
                    st.error(f"Execution failed: {e}")
                    
    with col2:
        st.markdown("#### 2. Sync to Live PostgreSQL")
        st.caption("Runs `scripts/load_jobs_to_db.py` to securely pipe CSV data into the live PostgreSQL database.")
        if st.button("📥 Commit to Live Database", type="primary"):
            with st.spinner("Pushing to PostgreSQL..."):
                try:
                    env = os.environ.copy()
                    env["PYTHONIOENCODING"] = "utf-8"
                    result = subprocess.run([sys.executable, 'scripts/load_jobs_to_db.py'], cwd=os.path.dirname(__file__), capture_output=True, text=True, env=env)
                    st.success("Database populated!")
                    with st.expander("View Output Log"):
                        st.code(result.stdout)
                except Exception as e:
                    st.error(f"Sync failed: {e}")
                    
with tab_health:
    st.subheader("System Consistency Metrics")
    def _file_info(path: str):
        try:
            ts = os.path.getmtime(path)
            return datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            return 'File Missing ❌'

    c_files, c_db = st.columns(2)
    with c_files:
        st.markdown("#### File System Status")
        config_paths = {
            'Jobs Dataset (CSV)': 'data/myjobmag_jobs.csv',
            'Demand Cache (CSV)': 'data/job_demand_metrics.csv',
            'KUCCPS Framework': 'Kuccps/kuccps_requirements.json'
        }
        for label, path in config_paths.items():
            st.info(f"**{label}:** {_file_info(os.path.join(os.path.dirname(__file__), path))}")

    with c_db:
        st.markdown("#### Database Synchronization")
        try:
            from core.auth import get_connection # type: ignore
            conn = get_connection()
            if conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT COUNT(*) FROM jobs")
                    job_count = cur.fetchone()[0]
                    cur.execute("SELECT COUNT(*) FROM users")
                    user_count = cur.fetchone()[0]
                
                # Render beautiful metrics
                st.metric("Total Synchronized Jobs", f"{job_count:,}")
                st.metric("Total Registered Users", f"{user_count:,}")
                conn.close()
        except:
            st.error("Could not query DB health.")

with tab_analytics:
    st.subheader("Global AI Telemetry & Reports")
    try:
        from core.auth import get_activity_logs # type: ignore
        logs = get_activity_logs()
        if logs:
            df_logs = pd.DataFrame(logs, columns=["ID", "Username", "Student Vision / Query", "KCSE Grade", "Top Ranked Path", "Timestamp"])
            
            # --- GLOBAL ANALYTICS OVERVIEW ---
            st.markdown("#### 🌍 Executive Summary")
            g_col1, g_col2 = st.columns([1, 2])
            with g_col1:
                st.metric("Total Consultations", len(df_logs))
                st.metric("Unique Students", df_logs["Username"].nunique())
            with g_col2:
                top_clusters = df_logs["Top Ranked Path"].value_counts().head(5)
                st.write("**Top 5 Hot Career Clusters**")
                st.bar_chart(top_clusters, color="#6366f1", height=200)

            st.divider()

            # --- USER DRILL-DOWN SECTION ---
            st.markdown("#### 🔍 User History Lookup")
            st.caption("Select a student below to view all their AI-generated career recommendations and visions.")
            
            unique_users = sorted(df_logs["Username"].unique())
            target_user = st.selectbox("Search for User Activity", unique_users, placeholder="Type username...", index=0)

            if target_user:
                user_history = df_logs[df_logs["Username"] == target_user].sort_values("Timestamp", ascending=False)
                
                st.info(f"Showing **{len(user_history)}** reports for user: **{target_user}**")
                
                for _, row in user_history.iterrows():
                    with st.expander(f"📅 {row['Timestamp']} - {row['Top Ranked Path']}"):
                        st.markdown(f"**KCSE Grade:** `{row['KCSE Grade']}`")
                        st.markdown("**Student's Original Vision:**")
                        st.info(row['Student Vision / Query'])
                        st.markdown(f"**AI Recommendation Result:** `{row['Top Ranked Path']}`")
            
            # --- DETAILED LOGS (OPTIONAL) ---
            with st.expander("📂 View All Raw Activity Logs"):
                st.dataframe(df_logs, use_container_width=True, hide_index=True)

        else:
            st.info("No activity logged yet. Reports will appear once users generate roadmaps.")
    except Exception as e:
        st.error(f"Failed to load analytics: {e}")
