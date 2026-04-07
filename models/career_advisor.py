import pandas as pd # type: ignore
import json
import os
import re
from typing import List, Dict, Optional, Any
from datetime import datetime

class CareerAdvisor:
    """
    A unified career advisor logic for the AI Career Roadmap Recommender.
    Extracted from main_app.py for better maintainability.
    """
    
    def __init__(self, recommender=None):
        self.recommender = recommender
        self.salaries = {
            "Information Technology": "KES 60,000 - 150,000 (Entry), KES 180,000 - 350,000 (Mid)",
            "Healthcare & Medical": "KES 50,000 - 120,000 (Entry), KES 150,000 - 300,000 (Mid)",
            "Business": "KES 40,000 - 100,000 (Entry), KES 120,000 - 250,000 (Mid)",
            "Engineering": "KES 60,000 - 150,000 (Entry), KES 180,000 - 350,000 (Mid)",
            "Finance & Accounting": "KES 50,000 - 120,000 (Entry), KES 150,000 - 300,000 (Mid)",
            "Marketing & Sales": "KES 40,000 - 90,000 (Entry), KES 100,000 - 220,000 (Mid)",
            "Data Science & Analytics": "KES 80,000 - 180,000 (Entry), KES 220,000 - 450,000 (Mid)",
            "Education": "KES 35,000 - 80,000 (Entry), KES 90,000 - 180,000 (Mid)"
        }
        
    def get_response(self, query: str, recommendations: Optional[List[Dict]] = None) -> str:
        """
        Process a user query and return a helpful response.
        If recommendations are provided, it tailors advice to the top match.
        """
        query_lower = query.lower().strip()
        
        # Default response if no specific intent is found
        default_response = (
            "That's a sophisticated question! As your AI Career Advisor, I can help you with:\n\n"
            "1. **Economic Clarity**: Ask about *salaries, marketability, or job availability*.\n"
            "2. **Learning Path**: Ask about *skills, certificates, or difficulty*.\n"
            "3. **Academic Guidance**: Ask about *university courses or KUCCPS programs*.\n"
            "4. **Future-Proofing**: Ask about *AI impact or long-term growth*."
        )

        if not recommendations:
            return "Please run the recommendation engine first so I can give you personalized advice! But in general, " + default_response

        top_rec = recommendations[0]
        dept = top_rec.get('dept', 'this field')
        s_list = top_rec.get('skills', [])
        f_skill = s_list[0] if len(s_list) > 0 else "Fundamentals"
        i_skill = s_list[3] if len(s_list) > 3 else "Advanced Industry Tools"

        # 1. WHY THIS CAREER?
        if any(w in query_lower for w in ["why", "reason", "because", "fit", "suggest"]):
             match_pct = str(int(top_rec.get('final_score', 0) * 100)) + "%"
             return (f"Excellent question. I recommended **{dept}** as your #1 match based on a 360-degree analysis:\n\n"
                    f"- **Passion Alignment**: Your interests show a **{match_pct} semantic match** with the core curriculum. This suggests you'll find the work intrinsically motivating.\n"
                    f"- **Market Demand**: With **{top_rec.get('job_count', 'many')} live vacancies** in Kenya, this field has strong hiring momentum.\n"
                    f"- **Skill Synergy**: Your profile indicates a potential aptitude for **{f_skill}**, a critical skill for success.")
            
        # 2. MARKETABILITY & JOBS
        elif any(w in query_lower for w in ["market", "demand", "job", "vacancy", "available"]):
            return (f"Let's talk about market dynamics for **{dept}**:\n\n"
                    f"- **Sector Growth**: This area is seeing significant investment in Kenya, driving hiring momentum.\n"
                    f"- **Talent Scarcity**: Many roles remain open for specialized talent. Your skills are highly marketable.\n"
                    f"- **The Verdict**: With **{top_rec.get('job_count', 0)} active roles**, focuses your search on major hubs like Nairobi or Mombasa.")

        # 3. SALARY & MONEY
        elif any(w in query_lower for w in ["salary", "money", "pay", "earn", "income", "compensation", "much"]):
            sal_range = self.salaries.get(dept, "KES 40,000 - 100,000 (indicative)")
            return (f"The financial outlook for **{dept}** is strong in the current Kenyan market:\n\n"
                    f"- **Standard Range**: Typically, you can expect **{sal_range}** per month depending on the specific company.\n"
                    f"- **Strategic Advice**: To maximize your earning potential, focus on mastering the 'Salary Booster' skills like **{i_skill}** mentioned in your roadmap.")

        # 4. SKILLS & CERTIFICATES
        elif any(w in query_lower for w in ["skill", "learn", "study", "certificate", "master"]):
            return (f"To become a top-tier candidate in **{dept}**, focus on a 'T-shaped' skill set:\n\n"
                    f"- **Foundational Pillar**: You must be proficient in **{f_skill}**. This is the non-negotiable entry ticket.\n"
                    f"- **Competitive Edge**: To truly stand out, master **{i_skill}**. This is frequently requested for senior roles.")

        # 5. KUCCPS & PROGRAMS
        elif any(w in query_lower for w in ["university", "course", "program", "kuccps", "degree", "diploma", "where", "college", "institute"]):
            progs = top_rec.get('programs', [])[:3]
            uni_map = top_rec.get('university_mapping', {})
            prog_uni_detail = ""
            if not progs:
                prog_uni_detail = "- No specific degree programs were matched. Consider foundational Diplomas or TVET options."
            else:
                for p in progs:
                    unis = uni_map.get(p, ["Consult KUCCPS Portal"])
                    uni_list = ", ".join(unis[:2])
                    prog_uni_detail += f"- **{p}**: Notable institutions include **{uni_list}**.\n"
            return f"For **{dept}**, here are the primary academic pathways in Kenya:\n\n{prog_uni_detail}\n*Pro-Tip: Always cross-check with the official [KUCCPS Portal](https://students.kuccps.net/).*"

        # 6. AI IMPACT & FUTURE-PROOFING
        elif any(w in query_lower for w in ["ai", "future", "automation", "replace", "robot"]):
            s_strat = s_list[2] if len(s_list)>2 else 'Strategic Thinking'
            return (f"Regarding AI's impact on **{dept}**:\n\n"
                    f"- **Role Evolution**: AI handles repetitive tasks, freeing you for complex strategy and human-centric problem-solving.\n"
                    f"- **Your Defense**: By mastering **{s_strat}**, you become an 'AI-augmented' professional, which increases your market value.")

        # 7. DIFFICULTY & EFFORT
        elif any(w in query_lower for w in ["hard", "difficult", "easy", "challenge", "tough"]):
            return (f"The difficulty for **{dept}** is manageable with the right strategy:\n\n"
                    f"- **The Hurdle**: Mastering **{f_skill}** requires consistent effort.\n"
                    f"- **Verdict**: Based on your grades, you have the foundational aptitude. We classify this path as 'Challenging, but Rewarding'.")

        # 8. NETWORKING & INTERNSHIPS
        elif any(w in query_lower for w in ["network", "internship", "attachment", "body", "society"]):
            networking_hub = {
                "Finance & Accounting": "ICPAK", "Engineering": "IEK & EBK",
                "Information Technology": "CSK & iHub", "Healthcare & Medical": "KMA", 
                "Law": "LSK", "Agriculture & Agribusiness": "ASK",
                "Education": "TSC", "Media & Communications": "MCK"
            }.get(dept, "a relevant professional body")
            return (f"To build your network in **{dept}**:\n\n"
                    f"- **Professional Body**: Connect with the **{networking_hub}** group.\n"
                    f"- **Internship Strategy**: When applying, highlight your expertise in **{f_skill}** to show you are ready to contribute.")

        # 9. ALTERNATIVES
        elif any(w in query_lower for w in ["another", "else", "alternative", "other", "instead"]):
            if len(recommendations) > 1:
                alt = recommendations[1]
                alt_match = str(int(alt.get('final_score', 0) * 100)) + "%"
                return (f"Your #2 recommendation is **{alt['dept']}** with an **{alt_match} match**.\n\n"
                        f"This is a strong alternative if you want to explore a different career vector.")
            return "Your current profile has a uniquely strong alignment with your top recommendation. Other fields were not as strong a match."

        # 10. BRIDGING & UPGRADING
        elif any(w in query_lower for w in ["bridge", "upgrade", "diploma", "tvet", "foundation"]):
            status = top_rec.get('dept_status', 'ELIGIBLE')
            if "DIPLOMA" in status:
                return "Your eligibility for a Diploma is the perfect launchpad! You can graduate and then use lateral entry to jump into a Degree program later."
            elif status == "ASPIRATIONAL":
                return "For an 'Aspirational' path, a bridging course or a related TVET Diploma is the best strategy. It builds the academic foundation for your target Degree."
            return "While you qualify for a Degree, specialized Diplomas *after* graduation can help you become a niche expert."

        # 11. POLITE CLOSING
        elif any(w in query_lower for w in ["thank", "bye", "hello", "hi", "help", "who"]):
            return "I'm your AI Career Advisor! I can help you understand your roadmap, salaries, and the Kenyan job market. How can I guide you today?"
            
        return "I'm not quite sure about that specific detail. Try asking about salaries, skills, or job demand in Kenya!"
