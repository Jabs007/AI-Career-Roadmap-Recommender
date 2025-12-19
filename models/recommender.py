# Career Recommender Engine - v2.1
import pandas as pd
import json
from .interest_classifier import InterestClassifier

class CareerRecommender:
    GRADE_POINTS = {
        "A": 12, "A-": 11, "B+": 10, "B": 9, "B-": 8, "C+": 7, "C": 6, "C-": 5, "D+": 4, "D": 3, "D-": 2, "E": 1, "N/A": 0
    }

    def __init__(self, demand_csv="data/job_demand_metrics.csv", skill_map_json="data/career_skill_map.json", jobs_csv="data/myjobmag_jobs.csv", kuccps_csv="Kuccps/kuccps_courses.csv", requirements_json="Kuccps/kuccps_requirements.json"):
        self.classifier = InterestClassifier()

        # Load demand metrics
        self.demand_df = pd.read_csv(demand_csv)
        self.demand_df.set_index('Department', inplace=True)
        self.max_demand = self.demand_df['job_count'].max()

        # Load skill map
        with open(skill_map_json, 'r') as f:
            self.skill_map = json.load(f)

        # Load scraped jobs
        try:
            self.jobs_df = pd.read_csv(jobs_csv)
        except Exception as e:
            print(f"Warning: Could not load jobs CSV: {e}")
            self.jobs_df = pd.DataFrame(columns=['Job Title', 'Company', 'Department'])

        # Load KUCCPS University Mapping
        try:
            kuccps_df = pd.read_csv(kuccps_csv)
            # Remove duplicates and group
            self.university_map = kuccps_df.groupby('Programme_Name')['Institution_Name'].apply(lambda x: list(set(x))).to_dict()
        except Exception as e:
            print(f"Warning: Could not load KUCCPS CSV: {e}")
            self.university_map = {}

        # Load KUCCPS Academic Requirements
        try:
            with open(requirements_json, 'r') as f:
                self.kuccps_requirements = json.load(f)
        except Exception as e:
            print(f"Warning: Could not load KUCCPS requirements: {e}")
            self.kuccps_requirements = {}

    def check_eligibility(self, program_name: str, student_results: dict):
        """
        Validate student eligibility for a specific program.
        """
        # Find requirement (Exact or fuzzy match)
        req = None
        for key in self.kuccps_requirements:
            if key.lower() in program_name.lower() or program_name.lower() in key.lower():
                req = self.kuccps_requirements[key]
                break
        
        if not req:
            return "UNKNOWN", "No requirement data available for this program."

        status = "ELIGIBLE"
        reasons = []

        # 1. Mean Grade Check
        student_mean = student_results.get("mean_grade", "E")
        if self.GRADE_POINTS.get(student_mean, 0) < self.GRADE_POINTS.get(req['min_mean_grade'], 0):
            status = "NOT ELIGIBLE"
            reasons.append(f"Mean Grade {student_mean} is below required {req['min_mean_grade']}")

        # 2. Subject Check
        for sub, min_g in req.get('required_subjects', {}).items():
            s_grade = "E"
            
            # Handle Logical OR subjects (e.g., English_or_Kiswahili)
            if "_or_" in sub:
                options = sub.split("_or_")
                s_grade = "E"
                max_pts = 0
                for opt in options:
                    current_g = student_results.get("subjects", {}).get(opt, "E")
                    current_pts = self.GRADE_POINTS.get(current_g, 0)
                    if current_pts > max_pts:
                        max_pts = current_pts
                        s_grade = current_g
            
            # Handle Generic "Teaching Subjects" (Heuristic: Top 2 non-core)
            elif "Teaching_Subject" in sub:
                all_subject_pts = sorted([self.GRADE_POINTS.get(g, 0) for g in student_results.get("subjects", {}).values()], reverse=True)
                # We assume teaching subjects are found among student's top electives
                idx = 0 if "1" in sub else 1
                if len(all_subject_pts) > idx:
                    # Map back to grade string
                    pts = all_subject_pts[idx]
                    s_grade = [g for g, p in self.GRADE_POINTS.items() if p == pts][0]
            else:
                s_grade = student_results.get("subjects", {}).get(sub, "E")

            if self.GRADE_POINTS.get(s_grade, 0) < self.GRADE_POINTS.get(min_g, 0):
                # Aspirational if only missing by 1 grade point in subjects
                if status == "ELIGIBLE" and self.GRADE_POINTS.get(s_grade, 0) == self.GRADE_POINTS.get(min_g, 0) - 1:
                    status = "ASPIRATIONAL"
                    reasons.append(f"Subject {sub.replace('_', ' ')} grade {s_grade} is slightly below {min_g}")
                else:
                    status = "NOT ELIGIBLE"
                    reasons.append(f"Subject {sub.replace('_', ' ')} grade {s_grade} does not meet {min_g}")

        if status == "ELIGIBLE":
            reasons.append(f"Meets all criteria for {req.get('level', 'Degree')}")
        
        # Add the specific note from the JSON if it exists
        if req.get('note'):
            reasons.append(f"Note: {req['note']}")

        return status, " | ".join(reasons)

    def get_top_jobs(self, department: str, top_n: int = 3):
        """
        Get sample jobs for a department.
        """
        # Handle IT naming conventions
        lookup_dept = "Information Technology" if department == "IT" else department
        
        # Filter jobs
        try:
            filtered_jobs = self.jobs_df[self.jobs_df['Department'] == lookup_dept]
            if filtered_jobs.empty and department == "Information Technology":
                 filtered_jobs = self.jobs_df[self.jobs_df['Department'] == "IT"]
            
            # Select relevant columns including description
            cols = ['Job Title', 'Company', 'Description']
            if 'Skillmentequired' in self.jobs_df.columns:
                cols.append('Skillmentequired')
            
            return filtered_jobs[cols].head(top_n).to_dict('records')
        except Exception:
            return []

    def recommend(self, student_text: str, top_n: int = 5, alpha: float = 0.75, beta: float = 0.25, kcse_results: dict = None):
        """
        Recommend careers based on student interests and market demand.
        Enhanced with better scoring and detailed comparative analysis.
        """
        from .interest_vectorizer import department_keywords
        from .nlp_preprocessing import preprocess_text
        
        # Get interest scores
        interest_scores = self.classifier.classify(student_text)
        
        # Preprocess user text for explanation generation
        user_tokens = set(preprocess_text(student_text).split())

        recommendations = []
        
        # Map Vectorizer/Demand keys to Skill Map keys
        dept_mapping = {
            "Information Technology": "IT",
            "Healthcare & Medical": "Health Sciences",
            "Finance & Accounting": "Business",
            "Marketing & Sales": "Business",
            "Human Resources": "Business",
            "Administration & Support": "Business",
            "Law": "Law",
            "Arts & Media": "Arts & Humanities",
            "Agriculture & Environmental": "Agriculture",
            "Architecture & Construction": "Architecture & Built Environment",
            "Social Sciences & Community": "Arts & Humanities",
            "Security & Protective Services": "Arts & Humanities",
            "Data Science & Analytics": "IT",
            "Project Management": "Business",
            "Renewable Energy & Environment": "Environmental Studies",
            "Real Estate & Property": "Business",
            "Aviation & Logistics": "Engineering"
        }
        
        # Reverse mapping for demand metrics if names differ
        demand_mapping = {
            "Law": "Legal & Compliance"
        }

        # Calculate variance to detect Mixed/Uncertain interests
        scores_list = list(interest_scores.values())
        top_scores = sorted(scores_list, reverse=True)[:3]
        
        # Detection Flags
        is_mixed_interest = (top_scores[0] - top_scores[1]) < 0.05 if len(top_scores) > 1 else False
        is_low_signal = top_scores[0] < 0.15
        
        # Calculate confidence score
        avg_interest = sum(top_scores) / len(top_scores) if top_scores else 0
        if is_low_signal:
            confidence = "Low"
            conf_reason = "Input contains sparse career-specific keywords."
        elif avg_interest > 0.4:
            confidence = "High"
            conf_reason = "Strong alignment between input and career taxonomies."
        else:
            confidence = "Medium"
            conf_reason = "Moderate keyword signal detected."

        # BASELINE COMPARISON (Calculated for Evaluation Tab)
        # Interest-only ranking
        interest_baseline = sorted(interest_scores.items(), key=lambda x: x[1], reverse=True)[:5]
        interest_baseline_names = [d[0] for d in interest_baseline]
        
        # Market-only ranking (pre-computed from self.demand_df)
        market_baseline = self.demand_df.sort_values('job_count', ascending=False).head(5).index.tolist()

        for dept in interest_scores:
            interest_score = interest_scores[dept]
            
            # INTEREST FILTERING: 
            # If low signal, we lower the bar significantly (0.02) to ensure some results
            threshold = 0.02 if is_low_signal else 0.08
            if interest_score < threshold:
                continue

            # Resolve demand key
            demand_key = demand_mapping.get(dept, dept)
            job_count = int(self.demand_df.loc[demand_key, 'job_count']) if demand_key in self.demand_df.index else 0
            demand_score = job_count / self.max_demand if self.max_demand > 0 else 0
            
            # FINAL SCORE Calculation
            effective_alpha = 0.3 if is_low_signal else alpha
            effective_beta = 0.7 if is_low_signal else beta
            
            final_score = (effective_alpha * interest_score) + (effective_beta * demand_score)
            
            # XAI: Contribution Calculation
            # This shows exactly how many points came from which side
            interest_contribution = effective_alpha * interest_score
            market_contribution = effective_beta * demand_score

            # DATA RETRIEVAL (Skills & Programs)
            lookup_dept = dept_mapping.get(dept, dept)
            if lookup_dept not in self.skill_map and dept == "Information Technology":
                 lookup_dept = "IT"

            skills = self.skill_map.get(lookup_dept, {}).get('skills', [])
            programs = self.skill_map.get(lookup_dept, {}).get('programs', [])
            
            if len(skills) < 2:
                fallback_skills = {
                    "IT": ["Software Development", "Systems Analysis", "Cybersecurity", "Database Management", "AI/ML"],
                    "Health Sciences": ["Clinical Diagnosis", "Patient Care", "Anatomy", "Physiology", "Medical Ethics"],
                    "Business": ["Strategic Management", "Financial Accounting", "Marketing", "Operations", "Leadership"],
                    "Law": ["Legal Research", "Jurisprudence", "Litigation", "Civil Law", "Drafting"],
                    "Engineering": ["Structural Design", "Technical Problem Solving", "CAD", "Project Engineering"],
                    "Environmental Studies": ["Ecology", "Environmental Impact Assessment", "Conservation", "GIS"]
                }
                skills = fallback_skills.get(lookup_dept, ["Analytical Thinking", "Critical Problem Solving", "Effective Communication"])

            # Market context
            if job_count > 30:
                market_advice = f"🔥 **High Demand**: We found over {job_count} active job listings in this field recently."
                market_outlook = "Excellent. The industry is rapidly expanding with high volumes of entry-level and senior roles."
            elif job_count > 0:
                market_advice = f"📈 **Steady Growth**: There are {job_count} current openings matching this field."
                market_outlook = "Stable. There is a consistent need for professionals, providing reliable career progression."
            else:
                market_advice = "🔍 **Niche Field**: Opportunities may be specialized or emerging."
                market_outlook = "Competitive/Specialized. Roles may require higher specialization or are emerging in the local market."

            # PHASE 4: ELIGIBILITY PROCESSING (Integrated for Tone-Aware Rationale)
            dept_status = "UNKNOWN"
            eligibility_map = {}
            if kcse_results:
                has_degree_eligible = False
                has_aspirational = False
                diploma_options = []

                for prog in programs:
                    status, reason = self.check_eligibility(prog, kcse_results)
                    eligibility_map[prog] = {"status": status, "reason": reason}
                    if status == "ELIGIBLE": has_degree_eligible = True
                    if status == "ASPIRATIONAL": has_aspirational = True
                
                if not has_degree_eligible:
                    dept_kw = dept.lower().split()
                    for req_name, req_data in self.kuccps_requirements.items():
                        if req_data.get('level') == "Diploma" and any(kw in req_name.lower() for kw in dept_kw):
                            d_status, d_reason = self.check_eligibility(req_name, kcse_results)
                            if d_status == "ELIGIBLE":
                                eligibility_map[req_name] = {"status": "ELIGIBLE", "reason": f"Qualify for Diploma Pathway: {d_reason}"}
                                diploma_options.append(req_name)

                if has_degree_eligible: dept_status = "ELIGIBLE"
                elif diploma_options: dept_status = "ELIGIBLE (DIPLOMA)"
                elif has_aspirational: dept_status = "ASPIRATIONAL"
                else: dept_status = "NOT ELIGIBLE"

            # PHASE 5: ELIGIBILITY-AWARE RATIONALE
            primary_skill = skills[0] if skills else "specialized techniques"
            matched_keywords = [kw for kw in department_keywords.get(dept, []) if kw in user_tokens]
            
            if dept_status == "NOT ELIGIBLE":
                academic_layer = (
                    f"**1. Academic Reality Check**: Although your interests align {interest_score:.0%} with {dept} concepts, your current KCSE profile does not yet meet the Degree entry threshold. "
                    f"Pursuing this path directly through a Degree is currently blocked, but your passion suggests you should consider TVET foundations first."
                )
                market_layer = (
                    f"**2. Strategic Pivot**: With {job_count} jobs in this sector, the demand is real. However, to access these roles, you'll need to focus on skill-based certifications "
                    f"rather than traditional academic routes until you qualify for advanced bridging."
                )
                trajectory_layer = (
                    f"**3. Alternative Entry**: Don't lose heart—many sector leaders started with technical certificates. Focus on mastering {primary_skill} via short courses to enter the market while planning your academic progression."
                )
            elif dept_status == "ELIGIBLE (DIPLOMA)":
                academic_layer = (
                    f"**1. Practical Path Forward**: You qualify for a **Diploma** in {dept}! This is a massive advantage as it allows you to gain industry skills faster than a degree student. "
                    f"You have the semantic foundation to excel in {primary_skill} at a technical level."
                )
                market_layer = (
                    f"**2. Fast-Track to Employment**: The market for Diploma holders in {dept} is strong. Companies value the 'hands-on' expertise you will gain. "
                    f"With {job_count} roles active, your specialized technical training will make you a prime candidate for operational roles."
                )
                trajectory_layer = (
                    f"**3. The Ladder Strategy**: Use your Diploma as a launchpad. After two years of work, most Kenyan universities will allow you to enroll in a Degree via 'Credit Transfer', often shortening the degree path significantly."
                )
            elif dept_status == "ASPIRATIONAL":
                academic_layer = (
                    f"**1. Narrow Academic Gap**: You are **very close** to qualifying for a Degree in {dept}. Your interest match is excellent, and you likely only need a single grade "
                    f"improvement or a short pre-university bridge to unlock this path."
                )
                market_layer = (
                    f"**2. High Stakes Match**: Because your interest in {dept} is so strong, it is worth the extra effort to bridge the academic gap. The {job_count} "
                    f"vacancies represent a future where your passion meets significant economic opportunity."
                )
                trajectory_layer = (
                    f"**3. Persistence Strategy**: Consider a 'Bridging Course' in your weakest cluster subject. This small investment now could unlock a {dept} career that aligns with your highest cognitive strengths."
                )
            else: # ELIGIBLE or UNKNOWN
                if matched_keywords:
                    m_str = ", ".join(matched_keywords[:3])
                    academic_layer = f"**1. Direct Academic Alignment**: Your deep interest in **{m_str}** makes you a perfect fit for {dept} modules like {primary_skill}."
                else:
                    academic_layer = f"**1. Holistic Fit**: Your conceptual approach aligns with the analytical framework of {dept}, particularly for mastering **{primary_skill}**."
                
                market_layer = f"**2. Market Symbiosis**: We've found **{job_count} active vacancies** in {dept}. Your skills in {skills[1] if len(skills)>1 else 'industry tools'} will be in high demand."
                trajectory_layer = f"**3. Strategic Growth**: This path offers a clear bridge to leadership, leveraging your capacity for {skills[2] if len(skills)>2 else 'strategic thinking'}."

            comprehensive_rationale = f"{academic_layer}\n\n{market_layer}\n\n{trajectory_layer}"

            # WHY BEST (Dynamic Strategy Context)
            if alpha > 0.8:
                why_best = f"**Passion-First Priority**: This is ranked highly because it matches your intrinsic motivations perfectly."
            elif beta > 0.6:
                why_best = f"**Market-First Priority**: This sector is prioritized for job security with {job_count} current openings."
            elif is_mixed_interest and interest_score in top_scores:
                why_best = f"**Interdisciplinary Fit**: Since you have diverse interests, {dept} is a great anchor."
            elif interest_score > demand_score + 0.3:
                why_best = f"**Personal Strength**: Your passion for this field significantly outweighs general market trends."
            elif demand_score > interest_score + 0.3:
                why_best = f"**Strategic Choice**: This field offers massive growth opportunities in the current Kenyan economy."
            else:
                why_best = f"**The Sweet Spot**: An ideal balance between your personal interests and healthy market demand."

            recommendations.append({
                'dept': dept,
                'final_score': final_score,
                'interest_score': interest_score,
                'demand_score': demand_score,
                'interest_contribution': interest_contribution,
                'market_contribution': market_contribution,
                'confidence': confidence,
                'conf_reason': conf_reason,
                'skills': skills,
                'programs': programs,
                'university_mapping': {p: self.university_map.get(p, ["Consult KUCCPS Portal for Institutions"])[:5] for p in programs},
                'comprehensive_rationale': comprehensive_rationale,
                'why_best': why_best,
                'market_advice': market_advice,
                'market_outlook': market_outlook,
                'job_count': job_count,
                'is_mixed': is_mixed_interest,
                'is_low_signal': is_low_signal,
                'dept_status': dept_status,
                'eligibility': eligibility_map,
                'baselines': {
                    'interest_only': interest_baseline_names,
                    'market_only': market_baseline,
                    'hybrid': []
                }
            })

        # FALLBACK: If still empty, return top 3 absolute fits ignoring threshold
        if not recommendations:
            sorted_depts = sorted(interest_scores.items(), key=lambda x: x[1], reverse=True)[:3]
            for dept, interest_score in sorted_depts:
                demand_key = demand_mapping.get(dept, dept)
                job_count = int(self.demand_df.loc[demand_key, 'job_count']) if demand_key in self.demand_df.index else 0
                lookup_dept = dept_mapping.get(dept, dept)
                recommendations.append({
                    'dept': dept,
                    'final_score': interest_score,
                    'interest_score': interest_score,
                    'demand_score': 0,
                    'interest_contribution': interest_score,
                    'market_contribution': 0,
                    'confidence': "Low",
                    'conf_reason': "Analysis of exploratory interest only.",
                    'skills': self.skill_map.get(lookup_dept, {}).get('skills', ["Interdisciplinary Skills"]),
                    'programs': self.skill_map.get(lookup_dept, {}).get('programs', []),
                    'explanation': "A suggested exploratory path based on your general aspirations.",
                    'comprehensive_rationale': "This field offers a versatile starting point for students identifying their core strengths.",
                    'why_best': "This is suggested as an entry-point to help you discover where your true career passion lies.",
                    'market_advice': "🔍 Reliable Market Demand",
                    'market_outlook': "Stable",
                    'job_count': job_count,
                    'is_mixed': True,
                    'is_low_signal': True,
                    'baselines': {
                        'interest_only': interest_baseline_names,
                        'market_only': market_baseline,
                        'hybrid': []
                    }
                })

                # Fallback Eligibility
                if kcse_results:
                    prog_info = self.skill_map.get(lookup_dept, {}).get('programs', [])
                    prog_eligibility = {}
                    has_deg = False
                    has_asp = False
                    diplomas = []

                    for p in prog_info:
                        status, reason = self.check_eligibility(p, kcse_results)
                        prog_eligibility[p] = {"status": status, "reason": reason}
                        if status == "ELIGIBLE": has_deg = True
                        if status == "ASPIRATIONAL": has_asp = True
                    
                    if not has_deg:
                        for req_name, req_data in self.kuccps_requirements.items():
                            if req_data.get('level') == "Diploma" and any(kw in req_name.lower() for kw in dept.lower().split()):
                                d_status, d_reason = self.check_eligibility(req_name, kcse_results)
                                if d_status == "ELIGIBLE":
                                    prog_eligibility[req_name] = {"status": "ELIGIBLE", "reason": f"Qualify for Diploma Pathway: {d_reason}"}
                                    diplomas.append(req_name)

                    recommendations[-1]['eligibility'] = prog_eligibility
                    if has_deg: recommendations[-1]['dept_status'] = "ELIGIBLE"
                    elif diplomas: recommendations[-1]['dept_status'] = "ELIGIBLE (DIPLOMA)"
                    elif has_asp: recommendations[-1]['dept_status'] = "ASPIRATIONAL"
                    else: recommendations[-1]['dept_status'] = "NOT ELIGIBLE"
                else:
                    recommendations[-1]['dept_status'] = "UNKNOWN"
                    recommendations[-1]['eligibility'] = {}

        # Final Sort and Return
        recommendations.sort(key=lambda x: x['final_score'], reverse=True)
        top_recommendations = recommendations[:top_n]
        
        # Inject current hybrid ranking into the baseline comparison for display
        hybrid_ranking = [r['dept'] for r in top_recommendations]
        for r in top_recommendations:
            r['baselines']['hybrid'] = hybrid_ranking
            
        return top_recommendations

    def get_kuccps_programs(self, department: str):
        """
        Get KUCCPS programs for a department.

        Args:
            department (str): Department name

        Returns:
            list: List of programs
        """
        return self.skill_map.get(department, {}).get("programs", [])