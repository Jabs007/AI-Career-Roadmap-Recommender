from .nlp_preprocessing import preprocess_text, get_bert_embedding
import torch
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

# Department keywords from extract_jobs.py (copied for independence)
department_keywords = {
    "Information Technology": [
        "developer", "software", "ict", "data", "ai", "machine learning", "cyber", "programmer",
        "analyst", "information technology", "computer", "network", "support", "systems",
        "cloud", "security", "database", "web", "frontend", "backend", "fullstack",
        "coding", "programming", "software engineering", "it", "hardware", "tech",
        "apps", "mobile", "internet", "coding", "algorithm", "devops", "code", "coder", "website",
        "python", "javascript", "java", "c#", "rust", "go", "php", "ruby", "sql", "flutter", "react",
        "node", "typescript", "swift", "kotlin", "android", "ios", "aws", "azure", "docker", "kubernetes"
    ],
    "Business": [
        "business", "operations", "strategy", "manager", "consultant", "entrepreneur",
        "logistics", "supply chain", "management", "administration", "leadership", "commerce", "startup"
    ],
    "Education": [
        "teacher", "lecturer", "education", "instructor", "tutor", "training",
        "curriculum", "school", "dean", "academic", "principal", "teaching", "pedagogy", "training"
    ],
    "Finance & Accounting": [
        "accountant", "finance", "auditor", "economist", "investment", "bookkeeper",
        "financial", "tax", "cpa", "controller", "budget", "accounting", "banking", "audit", "money"
    ],
    "Healthcare & Medical": [
        "nurse", "doctor", "pharmacist", "medical", "clinical", "health", "surgeon",
        "therapist", "dental", "radiologist", "physician", "lab technician", "veterinary",
        "nutritionist", "psychiatrist", "medicine", "dentistry", "pharmacy", "patient",
        "care", "healthcare", "therapy", "hospital", "surgery", "anatomy", "biology",
        "diseases", "pathology", "pharmaceuticals", "public health", "physiology",
        "nursing", "midwifery", "diagnostics", "treatment", "human health", "biologist", "science"
    ],
    "Engineering": [
        "engineer", "mechanical", "civil", "electrical", "technician", "biomedical",
        "mechatronic", "chemical", "project engineer", "structural",
        "industrial", "automotive", "manufacturing", "telecommunication", "machinery",
        "construction", "design", "robotics", "automation", "robot", "robots", "build", "building",
        "electronics", "maintenance", "architecture", "system design", "engines"
    ],
    "Marketing & Sales": [
        "marketing", "seo", "sales", "brand", "advertising", "digital", "content",
        "promotion", "telemarketing", "social media", "copywriter", "account executive",
        "market research", "public relations", "pr", "selling"
    ],
    "Administration & Support": [
        "admin", "clerk", "secretary", "assistant", "receptionist", "office manager",
        "front desk", "executive assistant", "records", "filing"
    ],
    "Human Resources": [
        "human resources", "hr", "recruiter", "talent management", "personnel", "staffing",
        "employee relations", "talent acquisition", "labor laws", "payroll", "onboarding", "hiring"
    ],
    "Law": [
        "lawyer", "legal", "attorney", "advocate", "compliance", "legal officer", "paralegal",
        "regulatory", "litigation", "contract", "corporate law", "law", "justice", "judiciary",
        "courts", "arbitration"
    ],
    "Arts & Media": [
        "artist", "musician", "painter", "graphic designer", "illustrator", "videographer",
        "photographer", "media", "journalist", "writer", "editor", "communication",
        "film", "animation", "content creator", "design", "creative", "theatre", "drawing"
    ],
    "Agriculture & Environmental": [
        "agriculture", "horticulture", "environment", "climate", "forestry", "conservation",
        "agronomist", "ecologist", "farm", "natural resources", "soil", "animal", "crop",
        "farming", "livestock", "irrigation", "agribusiness", "vet"
    ],
    "Architecture & Construction": [
        "architecture", "architect", "construction", "site supervisor", "planner",
        "urban planning", "interior design", "landscape", "surveying", "quantity surveyor",
        "draughtsman", "builder", "real estate development", "building"
    ],
    "Social Sciences & Community": [
        "social worker", "sociologist", "community", "ngo", "development officer",
        "humanitarian", "psychologist", "counselor", "activist", "gender", "youth worker",
        "counseling", "anthropology"
    ],
    "Hospitality & Tourism": [
        "hospitality", "tourism", "hotel", "chef", "cook", "housekeeping", "travel",
        "airline", "waiter", "bartender", "event planner", "front office", "resort", "catering"
    ],
    "Security & Protective Services": [
        "security", "guard", "military", "police", "defense", "intelligence", "forensic",
        "safety", "firefighter", "rescue", "policing", "crimonology"
    ],
    "Data Science & Analytics": [
        "data analyst", "data scientist", "big data", "statistics", "mathematics",
        "tableau", "power bi", "sql", "excel", "visualization", "predictive modeling",
        "machine learning", "data mining", "math", "analysis"
    ],
    "Project Management": [
        "project manager", "pmp", "agile", "scrum", "planning", "delivery", "stakeholder",
        "budgeting", "coordination", "implementation"
    ],
    "Renewable Energy & Environment": [
        "solar", "wind", "renewable", "energy", "sustainability", "environmental",
        "climate change", "green energy", "conservation"
    ],
    "Real Estate & Property": [
        "real estate", "property", "valuation", "realtor", "broker", "estate agent",
        "leasing", "tenancy", "land", "property management"
    ],
    "Aviation & Logistics": [
        "pilot", "aviation", "flight", "logistics", "warehouse", "transport",
        "airline", "cargo", "fleet", "clearing", "forwarding"
    ],
    "Other": []
}



class InterestVectorizer:
    def __init__(self):
        # Prepare corpus: each department's keywords as a document
        self.corpus = []
        self.departments = []
        for dept, keywords in department_keywords.items():
            if dept != "Other":
                # Preprocess keywords to ensure consistent matching
                processed_keywords = [preprocess_text(kw) for kw in keywords]
                self.corpus.append(' '.join(processed_keywords))
                self.departments.append(dept)

        # Initialize TF-IDF
        self.tfidf = TfidfVectorizer()
        self.tfidf_matrix = self.tfidf.fit_transform(self.corpus)

        # Pre-compute BERT embeddings for department keywords
        self.department_embeddings = {}
        for dept, text in zip(self.departments, self.corpus):
            self.department_embeddings[dept] = get_bert_embedding(text)

    def vectorize_bert(self, text: str):
        """Vectorize text using BERT embedding."""
        return get_bert_embedding(text)

    def vectorize_tfidf(self, text: str):
        """Vectorize text using TF-IDF."""
        processed_text = preprocess_text(text)
        return self.tfidf.transform([processed_text])

    def get_department_bert_vectors(self):
        """Get BERT embeddings for all departments."""
        return self.department_embeddings

    def get_department_tfidf_vectors(self):
        """Get TF-IDF matrix for all departments."""
        return self.tfidf_matrix
