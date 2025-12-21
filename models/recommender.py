# Career Recommender Engine - v2.1
import pandas as pd
import json
import configparser
from .interest_classifier import InterestClassifier

class CareerRecommender:
    GRADE_POINTS = {
        "A": 12, "A-": 11, "B+": 10, "B": 9, "B-": 8, "C+": 7, "C": 6, "C-": 5, "D+": 4, "D": 3, "D-": 2, "E": 1, "N/A": 0
    }

    def __init__(self, config_file="config.ini"):
        config = configparser.ConfigParser()
        config.read(config_file)
        paths = config['paths']

        self.classifier = InterestClassifier()

        # Load demand metrics
        self.demand_df = pd.read_csv(paths['demand_csv'])
        self.demand_df.set_index('Department', inplace=True)
        self.max_demand = self.demand_df['job_count'].max()

        # Load skill map
        with open(paths['skill_map_json'], 'r') as f:
            self.skill_map = json.load(f)

        # Load scraped jobs
        try:
            self.jobs_df = pd.read_csv(paths['jobs_csv'])
        except Exception as e:
            print(f"Warning: Could not load jobs CSV: {e}")
            self.jobs_df = pd.DataFrame(columns=['Job Title', 'Company', 'Department'])

        # Load KUCCPS University Mapping
        try:
            kuccps_df = pd.read_csv(paths['kuccps_csv'])
            # Remove duplicates and group
            self.university_map = kuccps_df.groupby('Programme_Name')['Institution_Name'].apply(lambda x: list(set(x))).to_dict()
        except Exception as e:
            print(f"Warning: Could not load KUCCPS CSV: {e}")
            self.university_map = {}

        # Load KUCCPS Academic Requirements
        try:
            with open(paths['requirements_json'], 'r') as f:
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
        
        # Calculate confidence score (Interest + Data Density)
        avg_interest = sum(top_scores) / len(top_scores) if top_scores else 0
        
        # Check data density for the top match
        top_dept_name = [k for k,v in interest_scores.items() if v == top_scores[0]][0] if top_scores else "Unknown"
        demand_key = demand_mapping.get(top_dept_name, top_dept_name)
        has_data =  demand_key in self.demand_df.index and self.demand_df.loc[demand_key, 'job_count'] > 5

        if is_low_signal:
            confidence = "Low"
            conf_reason = "Input was vague/short. We prioritized broad market trends."
        elif avg_interest > 0.4 and has_data:
            confidence = "High"
            conf_reason = "Strong alignment with both your interests AND verified market data."
        elif avg_interest > 0.4:
            confidence = "Medium"
            conf_reason = "High interest match, but limited local job data available to verify."
        else:
            confidence = "Medium"
            conf_reason = "Moderate keyword signal detected."

        # BASELINE COMPARISON (Calculated for Evaluation Tab)
        # Interest-only ranking
        interest_baseline = sorted(interest_scores.items(), key=lambda x: x[1], reverse=True)[:5]
        interest_baseline_names = [d[0] for d in interest_baseline]
        
        # Market-only ranking (pre-computed from self.demand_df)
        market_baseline = self.demand_df.sort_values('job_count', ascending=False).head(5).index.tolist()

        # Calculate scores
        scores = self._calculate_scores(interest_scores, is_low_signal, alpha, beta, demand_mapping)

        for dept, score_data in scores.items():
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
                    "Environmental Studies": ["Ecology", "Environmental Impact Assessment", "Conservation", "GIS"],
                    "Agriculture": ["Agribusiness", "Crop Management", "Soil Science", "Sustainable Farming"],
                    "Education": ["Curriculum Design", "Pedagogy", "Student Mentorship", "EdTech Tools"],
                    "Media & Communications": ["Content Strategy", "Public Relations", "Digital Media", "Storytelling"]
                }
                skills = fallback_skills.get(lookup_dept, ["Analytical Thinking", "Critical Problem Solving", "Effective Communication"])

            # Market context
            # Extract score data for clarity
            interest_score = score_data['interest_score']
            demand_score = score_data['demand_score']
            job_count = score_data['job_count']
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
            
            comprehensive_rationale = self._generate_rationale(dept_status, dept, score_data['interest_score'], score_data['job_count'], primary_skill, matched_keywords, skills)

            # WHY BEST (Dynamic Strategy Context)
            # WHY BEST (Dynamic Strategy Context)
            if alpha > 0.8:
                why_best = f"**Passion-First Priority**: Ranked #1 because it perfectly aligns with your stated interests, ignoring market noise."
            elif beta > 0.6:
                why_best = f"**Market-First Priority**: Prioritized for its massive job security ({job_count} open roles), despite standard interest levels."
            elif is_mixed_interest and interest_score in top_scores:
                why_best = f"**Interdisciplinary Pivot**: Bridging your diverse interests, {dept} serves as a perfect 'Hybrid Career' anchor."
            elif interest_score > 0.6 and demand_score > 0.6:
                 why_best = f"**The Unicorn Match**: Rare high scores in BOTH passion ({interest_score:.0%}) and market demand ({demand_score:.0%})."
            elif interest_score > demand_score + 0.3:
                why_best = f"**Personal Strength**: Your passion for this field significantly outweighs current market trends."
            elif demand_score > interest_score + 0.3:
                why_best = f"**Strategic Opportunity**: A 'Hidden Gem' field where your skills are needed more than you realized."
            else:
                why_best = f"**Balanced Choice**: An ideal trade-off between your happiness and your paycheck."

            # Extract score data for clarity
            interest_score = score_data['interest_score']
            demand_score = score_data['demand_score']
            final_score = score_data['final_score']
            job_count = score_data['job_count']
            interest_contribution = score_data['interest_contribution']
            market_contribution = score_data['market_contribution']

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
            
            comprehensive_rationale = self._generate_rationale(dept_status, dept, interest_score, job_count, primary_skill, matched_keywords, skills)

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

    def _calculate_scores(self, interest_scores, is_low_signal, alpha, beta, demand_mapping):
        """
        Calculates the interest, demand, and final scores for each department.
        """
        scores = {}
        for dept, interest_score in interest_scores.items():
            threshold = 0.02 if is_low_signal else 0.08
            if interest_score < threshold:
                continue

            demand_key = demand_mapping.get(dept, dept)
            job_count = int(self.demand_df.loc[demand_key, 'job_count']) if demand_key in self.demand_df.index else 0
            demand_score = job_count / self.max_demand if self.max_demand > 0 else 0

            effective_alpha = 0.3 if is_low_signal else alpha
            effective_beta = 0.7 if is_low_signal else beta

            final_score = (effective_alpha * interest_score) + (effective_beta * demand_score)

            scores[dept] = {
                'interest_score': interest_score,
                'demand_score': demand_score,
                'final_score': final_score,
                'job_count': job_count,
                'interest_contribution': effective_alpha * interest_score,
                'market_contribution': effective_beta * demand_score
            }
        return scores

    def _generate_summary(self, dept, dept_status, final_score, comprehensive_rationale, why_best_str, top_jobs_str, eligible_courses_str):
        """
        Generates a summary for a recommended department.
        """
        return {
            "department": dept,
            "status": dept_status,
            "score": final_score,
            "rationale": comprehensive_rationale,
            "why_best": why_best_str,
            "top_jobs": top_jobs_str,
            "courses": eligible_courses_str
        }

    def _generate_rationale(self, dept_status, dept, interest_score, job_count, primary_skill, matched_keywords, skills):
        """
        Generates the eligibility-aware rationale for a recommendation.
        """
        if dept_status == "NOT ELIGIBLE":
            academic_layer = (
                f"**1. Academic Reality Check**: Your KCSE results indicate that direct entry into a Degree program for {dept} isn't currently possible. "
                f"However, your passion for this field is a strong signal that you shouldn't give up. This is a redirection, not a dead end."
            )
            market_layer = (
                f"**2. Strategic Pivot to TVET**: The Kenyan market has a high demand for practical skills. With {job_count} jobs available, the quickest way to enter this field is through a TVET Diploma. "
                f"This path is often faster and more hands-on than a traditional degree."
            )
            trajectory_layer = (
                f"**3. The Comeback Plan**: Enroll in a relevant Diploma course. Excel in it. After graduating, you can leverage the 'Diploma-to-Degree' bridge programs offered by many universities to get your degree, often with credit transfers that save you time and money."
            )
        elif dept_status == "ELIGIBLE (DIPLOMA)":
            academic_layer = (
                f"**1. Your Strategic Advantage**: You've qualified for a Diploma in {dept}! This is a powerful position to be in. You'll gain practical, job-ready skills from day one, making you highly attractive to employers."
            )
            market_layer = (
                f"**2. Fast-Track to Your First Job**: Diploma graduates are in high demand. With {job_count} roles currently open, your hands-on training will give you a competitive edge over degree holders who may lack practical experience."
            )
            trajectory_layer = (
                f"**3. The 'Earn While You Learn' Strategy**: Start your career after your diploma. Once you have a few years of experience, you can pursue a degree part-time or through executive programs. You'll have the powerful combination of a degree and solid work experience."
            )
        elif dept_status == "ASPIRATIONAL":
            academic_layer = (
                f"**1. You're Almost There**: You are incredibly close to qualifying for a Degree in {dept}. Your interest match is strong, and you likely only need to improve a single grade or take a bridging course to meet the requirements."
            )
            market_layer = (
                f"**2. A Goal Worth Fighting For**: The high number of vacancies ({job_count}) shows that this is a field with significant opportunity. Your strong interest means you're more likely to succeed if you put in the extra effort to qualify."
            )
            trajectory_layer = (
                f"**3. Your Action Plan**: Identify the specific subject that's holding you back and consider a bridging course. Alternatively, you can enroll in a Diploma program and then bridge to a Degree. Don't let a small gap stop you from pursuing your passion."
            )
        else:  # ELIGIBLE or UNKNOWN
            if matched_keywords:
                m_str = ", ".join(matched_keywords[:3])
                academic_layer = f"**1. Excellent Academic & Interest Alignment**: Your strong interest in **{m_str}** and your academic record make you a perfect candidate for a Degree in {dept}."
            else:
                academic_layer = f"**1. Strong Holistic Fit**: Your profile shows a strong alignment with the analytical and conceptual demands of {dept}, particularly in areas like **{primary_skill}**."

            market_layer = f"**2. High Market Demand**: With **{job_count} active job openings**, {dept} is a field with strong employment prospects. Your skills in {skills[1] if len(skills) > 1 else 'industry tools'} will be particularly valuable."
            trajectory_layer = f"**3. Clear Path to Career Growth**: This degree will provide you with a direct path to leadership roles and specialized opportunities in the field. Your aptitude for {skills[2] if len(skills) > 2 else 'strategic thinking'} will be a key asset."

        return f"{academic_layer}\n\n{market_layer}\n\n{trajectory_layer}"