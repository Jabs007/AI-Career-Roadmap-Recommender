import os
import json
import time
import pandas as pd
from pathlib import Path
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from thefuzz import fuzz

# -------------------------------
# 🪵 UTILITY- Log Function
# -------------------------------
def log(message):
    """Simple logger to print messages with a timestamp."""
    print(f"[{datetime.now():%H:%M:%S}] {message}")

# -------------------------------
# 🗺️ CLASSIFICATION LOGIC
# -------------------------------
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

def classify_department(job_title, description="", skills=""):
    text = f"{job_title} {description} {skills}".lower()
    for dept, keywords in department_keywords.items():
        for kw in keywords:
            if kw.lower() in text:
                return dept
    return "Other"

def classify_location(location_text):
    # TODO: Implement robust location classification (Remote, On-site, Hybrid)
    return "Unclear"

# -------------------------------
# 🕷 Scraper Function
# -------------------------------
def scrape_myjobmag(pages=5, headless=True, delay=1.5,
                    json_path="data/myjobmag_jobs.json",
                    csv_path="data/myjobmag_jobs.csv"):

    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920,1080")

    # Use WebDriver Manager to automatically handle driver installation
    service = Service(ChromeDriverManager().install())
    
    driver = webdriver.Chrome(service=service, options=options)
    wait = WebDriverWait(driver, 20)
    all_jobs = []

    try:
        for page in range(1, pages + 1):
            url = f"https://www.myjobmag.co.ke/jobs/page/{page}" if page > 1 else "https://www.myjobmag.co.ke/jobs"
            log(f"Fetching page {page}: {url}")
            driver.get(url)

            try:
                wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ul.job-list > li.job-list-li")))
            except:
                log(f"No jobs found on page {page}")
                continue

            job_cards = driver.find_elements(By.CSS_SELECTOR, "ul.job-list > li.job-list-li")

            for card in job_cards:
                try:
                    job_title_elem = card.find_element(By.CSS_SELECTOR, "h2 > a")
                    job_title = job_title_elem.text.strip()
                    job_link = job_title_elem.get_attribute("href")

                    company_elem = card.find_element(By.CSS_SELECTOR, "li.job-logo img")
                    company_name = company_elem.get_attribute("alt").strip()
                except Exception:
                    continue

                driver.execute_script("window.open('');")
                driver.switch_to.window(driver.window_handles[-1])

                try:
                    driver.get(job_link)
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.job-details")))
                    description = driver.find_element(By.CSS_SELECTOR, "div.job-details").text.strip()

                    def extract_field(keyword):
                        for line in description.split("\n"):
                            if keyword.lower() in line.lower():
                                return line.split(":", 1)[-1].strip()
                        return ""

                    location = extract_field("Location")

                    skills = extract_field("Skills")
                    job_data = {
                        "Job Title": job_title,
                        "Company": company_name,
                        "Description": description,
                        "Minimum Qualification": extract_field("Qualification"),
                        "Skills Required": skills,
                        "Location": location,
                        "Work Type": classify_location(location),
                        "Years of Experience": extract_field("Experience"),
                        "Department": classify_department(job_title, description, skills)
                    }

                except Exception as e:
                    log(f"Failed to extract job from: {job_link}")
                    job_data = {
                        "Job Title": job_title,
                        "Company": company_name,
                        "Description": "",
                        "Minimum Qualification": "",
                        "Skills Required": "",
                        "Location": "",
                        "Work Type": "Unclear",
                        "Years of Experience": "",
                        "Department": classify_department(job_title, "", "")
                    }

                try:
                    driver.close()
                except Exception:
                    pass
                driver.switch_to.window(driver.window_handles[0])
                all_jobs.append(job_data)
                time.sleep(delay)

    finally:
        driver.quit()

    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(all_jobs, f, indent=2, ensure_ascii=False)

    pd.DataFrame(all_jobs).to_csv(csv_path, index=False, encoding="utf-8")
    log(f"Scraped and saved {len(all_jobs)} jobs.")
    return all_jobs

# -------------------------------
# ▶️ Entry Point
# -------------------------------
if __name__ == "__main__":
    scrape_myjobmag(pages=10)