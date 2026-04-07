# Career Recommender Engine - v2.1
import pandas as pd # type: ignore
import json
import configparser
import os, re
from typing import List, Dict, Optional, Any, cast # type: ignore
from .interest_classifier import InterestClassifier # type: ignore

class CareerRecommender:
    GRADE_POINTS = {
        "A": 12, "A-": 11, "B+": 10, "B": 9, "B-": 8, "C+": 7, "C": 6, "C-": 5, "D+": 4, "D": 3, "D-": 2, "E": 1, "N/A": 0
    }

    def __init__(self, config_file="config.ini"):
        config = configparser.ConfigParser()
        config.read(config_file)
        
        # Default fallback paths
        default_paths = {
            'demand_csv': 'data/job_demand_metrics.csv',
            'skill_map_json': 'data/career_skill_map.json',
            'jobs_csv': 'data/myjobmag_jobs.csv',
            'kuccps_csv': 'Kuccps/kuccps_courses.csv',
            'requirements_json': 'Kuccps/kuccps_requirements.json'
        }
        
        try:
            if 'paths' in config:
                paths = {**default_paths, **dict(config['paths'])}
            else:
                paths = default_paths
        except Exception as e:
            print(f"Warning: Using default paths due to config error: {e}")
            paths = default_paths

        self.classifier = InterestClassifier()
        self.data_health = {}

        # Load demand metrics
        try:
            self.demand_df = pd.read_csv(paths.get('demand_csv', ''))
            if 'Department' in self.demand_df.columns:
                self.demand_df.set_index('Department', inplace=True)
            self.max_demand = self.demand_df['job_count'].max() if 'job_count' in self.demand_df.columns and not self.demand_df.empty else 0
            self.data_health['demand_ok'] = True
        except Exception as e:
            print(f"Warning: Could not load demand metrics: {e}")
            self.demand_df = pd.DataFrame(columns=['Department', 'job_count']).set_index('Department')
            self.max_demand = 0
            self.data_health['demand_ok'] = False

        # Load skill map
        try:
            with open(paths.get('skill_map_json', ''), 'r') as f:
                self.skill_map = json.load(f)
            self.data_health['skillmap_ok'] = True
        except Exception as e:
            print(f"Warning: Could not load skill map: {e}")
            self.skill_map = {}
            self.data_health['skillmap_ok'] = False

        # Load scraped jobs
        try:
            self.jobs_df = pd.read_csv(paths.get('jobs_csv', ''))
            # Normalize job categories to internal department taxonomy
            job_category_mapping = {
                # IT
                'IT': 'Information Technology', 'I.T.': 'Information Technology', 'Information Tech': 'Information Technology',
                # Business family
                'Sales & Marketing': 'Marketing & Sales', 'Sales/Marketing': 'Marketing & Sales', 'Marketing': 'Marketing & Sales', 'Sales': 'Marketing & Sales',
                'Accounting/Finance': 'Finance & Accounting', 'Finance': 'Finance & Accounting', 'Accounting': 'Finance & Accounting',
                'Admin & Support': 'Administration & Support', 'Administration': 'Administration & Support',
                'Business Development': 'Business', 'Operations': 'Business', 'Customer Service': 'Business',
                'Real Estate': 'Real Estate & Property', 'Property': 'Real Estate & Property',
                # Education
                'Education/Teaching': 'Education', 'Teaching': 'Education', 'Education': 'Education', 'Teacher': 'Education', 'Lecturer': 'Education',
                # Data / Analytics
                'Data/Analytics': 'Data Science & Analytics', 'Data Science': 'Data Science & Analytics', 'Analytics': 'Data Science & Analytics',
                # Project Management
                'Project/Program Management': 'Project Management', 'Programme Management': 'Project Management',
                # Agriculture & Environment
                'Agriculture': 'Agriculture & Environmental', 'Environment': 'Agriculture & Environmental', 'Environmental': 'Agriculture & Environmental', 'Horticulture': 'Agriculture & Environmental', 'Livestock': 'Agriculture & Environmental',
                # Law
                'Legal': 'Law', 'Legal & Compliance': 'Law', 'Law': 'Law',
                # Healthcare
                'Healthcare': 'Healthcare & Medical', 'Medical': 'Healthcare & Medical', 'Nursing': 'Healthcare & Medical', 'Pharmacy': 'Healthcare & Medical', 'Dentistry': 'Healthcare & Medical', 'Veterinary': 'Healthcare & Medical',
                # HR
                'Human Resource': 'Human Resources', 'Human Resources': 'Human Resources', 'HR': 'Human Resources',
                # Renewable Energy & Environment
                'Renewable Energy': 'Renewable Energy & Environment', 'Environment & Conservation': 'Renewable Energy & Environment'
            }
            # Merge external admin-defined mappings if present
            try:
                project_root = os.path.dirname(os.path.dirname(__file__))
                cat_map_path = os.path.join(project_root, 'data', 'category_mappings.json')
                if os.path.exists(cat_map_path):
                    with open(cat_map_path, 'r', encoding='utf-8') as f:
                        ext_map = json.load(f)
                        if isinstance(ext_map, dict):
                            job_category_mapping.update(ext_map)
            except Exception as e:
                print(f"Warning: Could not load external category mappings: {e}")

            if 'Department' in self.jobs_df.columns:
                self.jobs_df['DeptNorm'] = self.jobs_df['Department'].map(job_category_mapping).fillna(self.jobs_df['Department'])
            else:
                # Fallback if source uses Category instead of Department
                if 'Category' in self.jobs_df.columns:
                    self.jobs_df['Department'] = self.jobs_df['Category']
                    self.jobs_df['DeptNorm'] = self.jobs_df['Category'].map(job_category_mapping).fillna(self.jobs_df['Category'])
                else:
                    # Ensure columns exist to avoid downstream errors
                    self.jobs_df['Department'] = ''
                    self.jobs_df['DeptNorm'] = ''

            # Heuristic inference from job title/category if DeptNorm is missing/empty
            if 'DeptNorm' in self.jobs_df.columns:
                def _infer_dept(row):
                    dn = str(row.get('DeptNorm', '') or '').strip()
                    if dn:
                        return dn
                    source = ' '.join([
                        str(row.get('Department', '')),
                        str(row.get('Category', '')),
                        str(row.get('Job Title', ''))
                    ]).lower()
                    patterns = [
                        (r'nurs|pharm|dent|clinic|medical|health|vet', 'Healthcare & Medical'),
                        (r'human resource|\bhr\b|recruit|talent', 'Human Resources'),
                        (r'teacher|lectur|education|tsc|school', 'Education'),
                        (r'sales|marketing|brand|seo|sem|growth', 'Marketing & Sales'),
                        (r'agri|farm|horti|soil|crop|livestock', 'Agriculture & Environmental'),
                        (r'environ|ecolog|conserv|renewable|solar|wind|energy', 'Renewable Energy & Environment'),
                        (r'data|analytics?|machine learning|\bml\b|\bai\b|business intelligence|\bbi\b', 'Data Science & Analytics'),
                        (r'project manager|program manager|\bpmo\b|project', 'Project Management'),
                        (r'law|legal|advocate|attorney|compliance', 'Law'),
                        (r'account|finance|auditor|\bcpa\b|bookkeep|treasury', 'Finance & Accounting'),
                        (r'software|developer|engineer|\bit\b|systems|network|cyber|cloud|devops', 'Information Technology'),
                    ]
                    for pat, dep in patterns:
                        try:
                            if re.search(pat, source):
                                return dep
                        except Exception:
                            continue
                    return dn
                try:
                    self.jobs_df['DeptNorm'] = self.jobs_df.apply(_infer_dept, axis=1)
                except Exception:
                    pass
            self.data_health['jobs_ok'] = True
        except Exception as e:
            print(f"Warning: Could not load jobs CSV: {e}")
            self.jobs_df = pd.DataFrame(columns=['Job Title', 'Company', 'Department', 'DeptNorm'])
            self.data_health['jobs_ok'] = False

        # Load KUCCPS University Mapping
        try:
            kuccps_df = pd.read_csv(paths.get('kuccps_csv', ''))
            # Remove duplicates and group
            self.university_map = kuccps_df.groupby('Programme_Name')['Institution_Name'].apply(lambda x: list(set(x))).to_dict()
            
            # Extract Cutoff points (try 2024, fallback to 2023 or 2022)
            self.cutoff_map = {}
            for col in ['Cutoff_2022', 'Cutoff_2023', 'Cutoff_2024']:
                if col in kuccps_df.columns:
                    temp_df = pd.DataFrame({
                        'Programme_Name': kuccps_df['Programme_Name'],
                        'Cutoff': pd.to_numeric(kuccps_df[col], errors='coerce')
                    }).dropna()
                    
                    if not temp_df.empty:
                        def _get_cutoff(x):
                            c_min = x.min()
                            c_max = x.max()
                            if pd.isna(c_min): return "N/A"
                            if abs(c_min - c_max) < 0.1: return f"{c_min:.2f}"
                            return f"{c_min:.1f} - {c_max:.1f}"
                        current_year_map = temp_df.groupby('Programme_Name')['Cutoff'].apply(_get_cutoff).to_dict()
                        self.cutoff_map.update(current_year_map)
            
            self.data_health['kuccps_map_ok'] = True
        except Exception as e:
            print(f"Warning: Could not load KUCCPS CSV: {e}")
            self.university_map = {}
            self.cutoff_map = {}
            self.data_health['kuccps_map_ok'] = False

        # Load KUCCPS Academic Requirements
        try:
            with open(paths.get('requirements_json', ''), 'r') as f:
                self.kuccps_requirements = json.load(f)
            self.data_health['kuccps_requirements_ok'] = True
        except Exception as e:
            print(f"Warning: Could not load KUCCPS requirements: {e}")
            self.kuccps_requirements = {}
            self.data_health['kuccps_requirements_ok'] = False

    def check_eligibility(self, program_name: str, student_results: Optional[dict]):
        """
        Validate student eligibility for a specific program with detailed feedback.
        """
        # Find requirement (Exact or fuzzy match)
        req = None
        best_match_key = None
        
        # Clean program name for matching
        clean_prog = program_name.replace('\n', ' ').strip().lower()
        
        for key in self.kuccps_requirements:
            clean_key = key.replace('\n', ' ').strip().lower()
            if clean_key == clean_prog:
                req = self.kuccps_requirements[key]
                best_match_key = key
                break
        
        if not req:
            # Fallback to partially fuzzy
            for key in self.kuccps_requirements: # type: ignore
                clean_key = str(key).replace('\n', ' ').strip().lower()
                if clean_key in clean_prog or clean_prog in clean_key:
                    req = self.kuccps_requirements[key] # type: ignore
                    best_match_key = key
                    break
        
        if not req or student_results is None:
            return "UNKNOWN", "No detailed requirement data available for this program.", []

        # Anchor type for linter
        res_cast = cast(dict, student_results)
        req_cast = cast(dict, req)
        status = "ELIGIBLE"
        details = [] # List of dicts: {subject, required, actual, status}

        # 1. Mean Grade Check
        student_mean = res_cast.get("mean_grade", "E")
        req_mean = req_cast.get('min_mean_grade', 'C+')
        
        mean_status = "MEETS"
        diff = self.GRADE_POINTS.get(student_mean, 0) - self.GRADE_POINTS.get(req_mean, 0)
        if diff < 0:
            mean_status = "MISSING"
            if diff == -1:
                status = "ASPIRATIONAL"
            else:
                status = "NOT ELIGIBLE"
        
        details.append({
            "criterion": "Mean Grade",
            "required": req_mean,
            "actual": student_mean,
            "status": mean_status
        })

        # 2. Subject Check
        req_cast = cast(Any, req)
        for sub, min_g in req_cast.get('required_subjects', {}).items():
            s_grade = "E"
            actual_sub_name = sub
            
            # Handle Logical OR subjects (e.g., English_or_Kiswahili)
            if "_or_" in sub:
                options = sub.split("_or_")
                max_pts = -1
                best_opt = options[0]
                for opt in options:
                    current_g = res_cast.get("subjects", {}).get(opt, "N/A")
                    if current_g == "N/A": current_g = "E"
                    current_pts = self.GRADE_POINTS.get(current_g, 0)
                    if current_pts > max_pts:
                        max_pts = current_pts
                        s_grade = current_g
                        best_opt = opt
                actual_sub_name = sub.replace("_or_", " or ")
            
            # Handle Generic "Teaching Subjects"
            elif "Teaching_Subject" in sub:
                all_subject_pts = sorted([self.GRADE_POINTS.get(g, 0) for g in res_cast.get("subjects", {}).values()], reverse=True)
                idx = 0 if "1" in sub else 1
                if len(all_subject_pts) > idx:
                    pts = all_subject_pts[idx]
                    s_grade = [g for g, p in self.GRADE_POINTS.items() if p == pts][0]
                actual_sub_name = "Teaching Subject"
            else:
                s_grade = res_cast.get("subjects", {}).get(sub, "N/A")
                if s_grade == "N/A": s_grade = "E"

            sub_status = "MEETS"
            if self.GRADE_POINTS.get(s_grade, 0) < self.GRADE_POINTS.get(min_g, 0):
                sub_status = "MISSING"
                # Aspirational if only missing by 1 grade point in subjects
                if status == "ELIGIBLE" and self.GRADE_POINTS.get(s_grade, 0) == self.GRADE_POINTS.get(min_g, 0) - 1:
                    status = "ASPIRATIONAL"
                elif status != "ASPIRATIONAL" or self.GRADE_POINTS.get(s_grade, 0) < self.GRADE_POINTS.get(min_g, 0) - 1:
                    status = "NOT ELIGIBLE"

            details.append({
                "criterion": actual_sub_name,
                "required": min_g,
                "actual": s_grade,
                "status": sub_status
            })

        # Summary reason
        missing = [d['criterion'] for d in details if d['status'] == "MISSING"]
        if not missing and status in ["ELIGIBLE", "ELIGIBLE (SPECIAL)", "ELIGIBLE (DIPLOMA)"]:
            reason = f"Meets all criteria for {req_cast.get('level', 'Degree')}"
        elif status == "ASPIRATIONAL":
            reason = f"Aspirational: Slightly below {req_cast.get('level', 'Degree')} requirements for: {', '.join(missing)}"
        else:
            reason = f"Does not meet requirements for: {', '.join(missing)}"
        
        if req_cast.get('note'):
            # Access conservatively if linter is confused
            try:
                note = req_cast['note']
                reason += f" (Note: {note})"
            except:
                pass

        return status, reason, details

    def get_top_jobs(self, department: str, top_n: int = 3):
        """
        Get sample jobs for a department.
        """
        # Normalize target department similarly to jobs normalization
        lookup_dept = department
        if department == 'IT':
            lookup_dept = 'Information Technology'
        
        # Filter jobs using normalized column if available
        try:
            if 'DeptNorm' in self.jobs_df.columns:
                filtered_jobs = self.jobs_df[self.jobs_df['DeptNorm'] == lookup_dept]
                if filtered_jobs.empty and department == 'Information Technology':
                    filtered_jobs = self.jobs_df[self.jobs_df['DeptNorm'] == 'IT']
            else:
                filtered_jobs = self.jobs_df[self.jobs_df['Department'] == lookup_dept]
                if filtered_jobs.empty and department == 'Information Technology':
                    filtered_jobs = self.jobs_df[self.jobs_df['Department'] == 'IT']
            
            # Select relevant columns including description (safely)
            base_cols = ['Job Title', 'Company']
            optional_cols = []
            if 'Description' in self.jobs_df.columns:
                optional_cols.append('Description')
            if 'Skillmentequired' in self.jobs_df.columns:
                optional_cols.append('Skillmentequired')
            cols = [c for c in base_cols + optional_cols if c in filtered_jobs.columns]
            
            return filtered_jobs[cols].head(top_n).to_dict('records') if cols else []
        except Exception:
            return []

    def recommend(self, student_text: str, top_n: int = 5, alpha: float = 0.75, beta: float = 0.25, kcse_results: Optional[dict] = None, target_level: str = "All"):
        """
        Recommend careers based on student's target academic level (Degree/Diploma/Certificate).
        Enhanced with level filtering and bridge suggestions.
        """
        from .interest_vectorizer import department_keywords # type: ignore
        from .nlp_preprocessing import preprocess_text # type: ignore
        
        # Get interest scores — pass live job data for 3rd-layer semantic matching
        interest_scores = self.classifier.classify(
            student_text,
            jobs_df=self.jobs_df if not self.jobs_df.empty else None
        )
        
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
            "Project Management": "Project Management",
            "Renewable Energy & Environment": "Environmental Studies",
            "Real Estate & Property": "Business",
            "Aviation & Logistics": "Aviation & Logistics"
        }
        
        # Reverse mapping for demand metrics if names differ
        demand_mapping = {
            # Law
            "Law": "Legal & Compliance",
            # Business and related
            "Marketing & Sales": "Sales & Marketing",
            "Finance & Accounting": "Accounting/Finance",
            "Administration & Support": "Admin & Support",
            "Real Estate & Property": "Real Estate",
            # IT is often already aligned; keep as-is
            # Education
            "Education": "Education/Teaching",
            # Data / Analytics
            "Data Science & Analytics": "Data/Analytics",
            # Project Management
            "Project Management": "Project/Program Management",
            # Agriculture & Environmental
            "Agriculture & Environmental": "Agriculture",
            # Healthcare & Medical
            "Healthcare & Medical": "Healthcare & Medical",
            # Human Resources
            "Human Resources": "Human Resources",
            # Renewable Energy & Environment
            "Renewable Energy & Environment": "Renewable Energy & Environment",
            # Social Sciences & Community
            "Social Sciences & Community": "Social Sciences & Community"
        }

        # Calculate variance to detect Mixed/Uncertain interests
        scores_list = list(interest_scores.values())
        top_scores = sorted(scores_list, reverse=True)[:3] # type: ignore
        
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
        interest_baseline = sorted(interest_scores.items(), key=lambda x: x[1], reverse=True)[:5] # type: ignore
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
            all_programs = self.skill_map.get(lookup_dept, {}).get('programs', [])
            
            # Filter standard programs by target level
            if target_level == "Degree":
                programs = [p for p in all_programs if "BACHELOR" in p.upper() or "DEGREE" in p.upper()]
            elif target_level == "Diploma":
                programs = [p for p in all_programs if "DIPLOMA" in p.upper()]
            elif target_level == "Certificate":
                programs = [p for p in all_programs if "CERTIFICATE" in p.upper()]
            else:
                programs = all_programs
            
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

            # PHASE 4: ELIGIBILITY PROCESSING (Enhanced for Clarity)
            dept_status = "UNKNOWN"
            eligibility_map = {}
            if kcse_results:
                has_pure_degree_eligible = False
                has_hybrid_degree_eligible = False
                has_aspirational = False
                diploma_options = []
                
                # Keywords that indicate hybrid/alternative programs
                hybrid_indicators = ["with it", "and it", "business and", "records management", 
                                    "information technology)", "arts, with", "education(arts)"]

                for prog in programs:
                    status, reason, details = self.check_eligibility(prog, kcse_results)
                    eligibility_map[prog] = {"status": status, "reason": reason, "details": details}
                    
                    if status == "ELIGIBLE":
                        # Check if this is a hybrid/alternative program
                        prog_lower = prog.lower()
                        is_hybrid = any(indicator in prog_lower for indicator in hybrid_indicators)
                        
                        if is_hybrid:
                            has_hybrid_degree_eligible = True
                        else:
                            has_pure_degree_eligible = True
                    
                    if status == "ASPIRATIONAL": 
                        has_aspirational = True
                
                # Check for diploma/certificate pathways if requested or if degree eligibility failed
                needs_fallback = (not has_pure_degree_eligible and not has_hybrid_degree_eligible)
                is_level_target = target_level in ["Diploma", "Certificate", "All"]
                
                if needs_fallback or is_level_target:
                    dept_str: Any = dept
                    # Exclude common stop words and short conjunctions that cause false positives (e.g., '&', 'and')
                    stop_words = {'and', 'or', 'in', 'of', 'the', '&', 'with'}
                    dept_kw = [kw for kw in str(dept_str).lower().split() if len(kw) > 2 and kw not in stop_words]
                    dept_kw.append(str(dept_str).lower())
                    
                    target_qual = "Diploma" if target_level == "Diploma" else ("Certificate" if target_level == "Certificate" else None)
                    
                    for req_name, req_data in self.kuccps_requirements.items():
                        req_level = req_data.get('level', '')
                        
                        # Use target_level if specified, else look for bridges
                        if target_qual and req_level != target_qual:
                            continue
                        elif not target_qual and req_level not in ["Diploma", "Certificate"]:
                            continue
                            
                        req_clean = req_name.lower()
                        # Match if any dept keyword is in the diploma name
                        if any(kw in req_clean for kw in dept_kw) and len(diploma_options) < 5:
                            d_status, d_reason, d_details = self.check_eligibility(str(req_name), kcse_results)
                            if d_status == "ELIGIBLE":
                                # Prepend to make sure it's seen
                                eligibility_map[str(req_name)] = {"status": d_status, "reason": f"Qualification Found: {d_reason}", "details": d_details}
                                if str(req_name) not in diploma_options:
                                    diploma_options.append(str(req_name))

                # Determine final department status - Honor target_level strictly
                if target_level == "Degree":
                    if has_pure_degree_eligible: dept_status = "ELIGIBLE"
                    elif has_hybrid_degree_eligible: dept_status = "ELIGIBLE (HYBRID)"
                    elif has_aspirational: dept_status = "ASPIRATIONAL"
                    else: dept_status = "NOT ELIGIBLE"
                elif target_level == "Diploma":
                    if diploma_options: dept_status = "ELIGIBLE (DIPLOMA)"
                    else: dept_status = "NOT ELIGIBLE"
                elif target_level == "Certificate":
                    certificate_eligible = any(eligibility_map.get(p, {}).get('status') == "ELIGIBLE" and "CERTIFICATE" in str(p).upper() for p in programs)
                    if certificate_eligible: dept_status = "ELIGIBLE"
                    else: dept_status = "NOT ELIGIBLE"
                else: 
                    # Original 'All' / Fallback logic
                    if has_pure_degree_eligible: dept_status = "ELIGIBLE"
                    elif has_hybrid_degree_eligible: dept_status = "ELIGIBLE (HYBRID)"
                    elif diploma_options: dept_status = "ELIGIBLE (DIPLOMA)"
                    elif has_aspirational: dept_status = "ASPIRATIONAL"
                    else: dept_status = "NOT ELIGIBLE"
                
                # REORDERING: If a specific target level is chosen, keep those programs at the top
                # even if 'other' programs (like bridges) are more eligible.
                target_items = {}
                other_items = {}
                
                for p, v in eligibility_map.items():
                    p_up = str(p).upper()
                    if target_level == "Degree" and ("BACHELOR" in p_up or "DEGREE" in p_up):
                        target_items[p] = v
                    elif target_level == "Diploma" and "DIPLOMA" in p_up:
                        target_items[p] = v
                    elif target_level == "Certificate" and "CERTIFICATE" in p_up:
                        target_items[p] = v
                    elif target_level == "All" and v['status'] == "ELIGIBLE":
                        target_items[p] = v
                    else:
                        other_items[p] = v

                # Build final re-ordered map
                reordered_map = {}
                # For target level, sort by status (MET first)
                for status in ["ELIGIBLE", "ELIGIBLE (HYBRID)", "ASPIRATIONAL", "NOT ELIGIBLE"]:
                    for p, v in target_items.items():
                        if v['status'] == status: reordered_map[p] = v
                # Add remaining target items
                for p, v in target_items.items():
                    if p not in reordered_map: reordered_map[p] = v
                # Add other items (Bridges / Alternatives)
                for status in ["ELIGIBLE", "ASPIRATIONAL", "NOT ELIGIBLE"]:
                    for p, v in other_items.items():
                        if v['status'] == status: reordered_map[p] = v
                # Add anything else
                for p, v in other_items.items():
                    if p not in reordered_map: reordered_map[p] = v
                
                eligibility_map = reordered_map
                
                # Update programs list order to match
                programs = list(eligibility_map.keys())

                # If NOT ELIGIBLE or ASPIRATIONAL for target, add a "bridge_courses" info
                if dept_status in ["NOT ELIGIBLE", "ASPIRATIONAL"] and diploma_options:
                     eligibility_map["__BRIDGE__"] = {"status": "INFO", "reason": "You missed the degree threshold. See the Diploma courses below as a strategic bridge.", "details": []}

            # PHASE 5: ELIGIBILITY-AWARE RATIONALE
            interest_score = score_data['interest_score']
            demand_score = score_data['demand_score']
            final_score = score_data['final_score']
            job_count = score_data['job_count']
            interest_contribution = score_data['interest_contribution']
            market_contribution = score_data['market_contribution']

            primary_skill = skills[0] if skills else "specialized techniques"
            matched_keywords = [kw for kw in department_keywords.get(dept, []) if kw in user_tokens]
            
            comprehensive_rationale = self._generate_rationale(dept_status, dept, interest_score, job_count, primary_skill, matched_keywords, skills)

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

            # Adjust confidence per-department using actual job_count
            loc_confidence, loc_conf_reason = confidence, conf_reason
            if job_count > 20:
                loc_confidence = "High"; loc_conf_reason = "High local job evidence supports this recommendation."
            elif job_count == 0 and interest_score >= 0.4:
                loc_confidence = "Medium"; loc_conf_reason = "High interest match, but limited local job data available to verify."

            recommendations.append({
                'dept': dept,
                'final_score': final_score,
                'interest_score': interest_score,
                'demand_score': demand_score,
                'interest_contribution': interest_contribution,
                'market_contribution': market_contribution,
                'confidence': loc_confidence,
                'conf_reason': loc_conf_reason,
                'skills': skills,
                'programs': programs,
                'university_mapping': {p: self.university_map.get(p, ["Consult KUCCPS Portal for Institutions"])[:5] for p in programs},
                'cutoff_mapping': {p: self.cutoff_map.get(p, "N/A") for p in programs},
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
            sorted_depts = sorted(interest_scores.items(), key=lambda x: x[1], reverse=True)[:3] # type: ignore
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
                        status, reason, details = self.check_eligibility(p, kcse_results)
                        prog_eligibility[p] = {"status": status, "reason": reason, "details": details}
                        if status == "ELIGIBLE": has_deg = True
                        if status == "ASPIRATIONAL": has_asp = True
                    
                    if not has_deg:
                        for req_name, req_data in self.kuccps_requirements.items():
                            if req_data.get('level') == "Diploma" and any(kw in req_name.lower() for kw in dept.lower().split()):
                                d_status, d_reason, d_details = self.check_eligibility(req_name, kcse_results)
                                if d_status == "ELIGIBLE":
                                    prog_eligibility[req_name] = {"status": "ELIGIBLE", "reason": f"Qualify for Diploma Pathway: {d_reason}", "details": d_details}
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
        
        # Override: Ensure the user's primary passion is anchored as the very first recommendation 
        if recommendations:
            highest_passion_rec = max(recommendations, key=lambda x: float(x['interest_score'])) # type: ignore
            if float(highest_passion_rec['interest_score']) > 0.4:  # type: ignore
                recommendations.remove(highest_passion_rec)
                recommendations.insert(0, highest_passion_rec)

        top_recommendations = recommendations[:top_n] # type: ignore
        
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

            if job_count > 0:
                market_layer = f"**2. High Market Demand**: With **{job_count} active job openings**, {dept} is a field with strong employment prospects. Your skills in {skills[1] if len(skills) > 1 else 'industry tools'} will be particularly valuable."
            else:
                market_layer = f"**2. Emerging/Niche Field**: While there are currently no immediate massive listings captured, {dept} can offer specialized opportunities. Your skills in {skills[1] if len(skills) > 1 else 'industry tools'} will be key to carving out your niche."
            
            trajectory_layer = f"**3. Clear Path to Career Growth**: This degree will provide you with a direct path to leadership roles and specialized opportunities in the field. Your aptitude for {skills[2] if len(skills) > 2 else 'strategic thinking'} will be a key asset."

        return f"{academic_layer}\n\n{market_layer}\n\n{trajectory_layer}"