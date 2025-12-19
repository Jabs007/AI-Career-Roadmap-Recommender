import pandas as pd
import json

# Copy department_keywords from interest_vectorizer.py
department_keywords = {
    "Information Technology": [
        "developer", "software", "ict", "data", "ai", "machine learning", "cyber", "programmer",
        "analyst", "information technology", "computer", "network", "support", "systems",
        "cloud", "security", "database", "web", "frontend", "backend", "fullstack"
    ],
    "Business": [
        "business", "operations", "strategy", "manager", "consultant", "entrepreneur",
        "logistics", "supply chain"
    ],
    "Education": [
        "teacher", "lecturer", "education", "instructor", "tutor", "training",
        "curriculum", "school", "dean", "academic", "principal"
    ],
    "Finance & Accounting": [
        "accountant", "finance", "auditor", "economist", "investment", "bookkeeper",
        "financial", "tax", "cpa", "controller", "budget", "accounting"
    ],
    "Healthcare & Medical": [
        "nurse", "doctor", "pharmacist", "medical", "clinical", "health", "surgeon",
        "therapist", "dental", "radiologist", "physician", "lab technician", "veterinary",
        "nutritionist", "psychiatrist"
    ],
    "Engineering": [
        "engineer", "mechanical", "civil", "electrical", "technician", "biomedical",
        "mechatronic", "chemical", "project engineer", "structural",
        "industrial", "automotive", "manufacturing", "telecommunication"
    ],
    "Marketing & Sales": [
        "marketing", "seo", "sales", "brand", "advertising", "digital", "content",
        "promotion", "telemarketing", "social media", "copywriter", "account executive"
    ],
    "Administration & Support": [
        "admin", "clerk", "secretary", "assistant", "receptionist", "office manager",
        "front desk", "executive assistant", "records"
    ],
    "Human Resources": [
        "hr", "human resource", "recruiter", "talent", "personnel", "staffing",
        "employee relations", "talent acquisition", "people operations"
    ],
    "Legal & Compliance": [
        "lawyer", "legal", "attorney", "advocate", "compliance", "legal officer", "paralegal",
        "regulatory", "litigation", "contract", "corporate law"
    ],
    "Arts & Media": [
        "artist", "musician", "painter", "graphic designer", "illustrator", "videographer",
        "photographer", "media", "journalist", "writer", "editor", "communication",
        "film", "animation", "content creator"
    ],
    "Agriculture & Environmental": [
        "agriculture", "horticulture", "environment", "climate", "forestry", "conservation",
        "agronomist", "ecologist", "farm", "natural resources", "soil", "animal", "crop"
    ],
    "Architecture & Construction": [
        "architecture", "architect", "construction", "site supervisor", "planner",
        "urban planning", "interior design", "landscape", "surveying", "quantity surveyor",
        "draughtsman", "builder"
    ],
    "Social Sciences & Community": [
        "social worker", "sociologist", "community", "ngo", "development officer",
        "humanitarian", "psychologist", "counselor", "activist", "gender", "youth worker"
    ],
    "Hospitality & Tourism": [
        "hospitality", "tourism", "hotel", "chef", "cook", "housekeeping", "travel",
        "airline", "waiter", "bartender", "event planner", "front office", "resort"
    ],
    "Security & Protective Services": [
        "security", "guard", "military", "police", "defense", "intelligence", "forensic",
        "safety", "firefighter", "rescue"
    ],
    "Other": []
}

def create_career_skill_map(kuccps_csv="Kuccps/Programmes_with_Departments.csv", output_json="data/career_skill_map.json"):
    """
    Create career-skill-job mapping JSON.

    Args:
        kuccps_csv (str): Path to KUCCPS CSV
        output_json (str): Output JSON path
    """
    # Load KUCCPS data
    df = pd.read_csv(kuccps_csv)

    # Group by Department and get unique programmes
    career_map = {}
    for dept in df['Depertments'].unique():
        programmes = df[df['Depertments'] == dept]['Programme_Name'].unique().tolist()
        skills = department_keywords.get(dept, [])
        career_map[dept] = {
            "skills": skills,
            "programs": programmes
        }

    # Save to JSON
    with open(output_json, 'w') as f:
        json.dump(career_map, f, indent=2)

    print(f"Career skill map saved to {output_json}")
    return career_map

if __name__ == "__main__":
    create_career_skill_map()