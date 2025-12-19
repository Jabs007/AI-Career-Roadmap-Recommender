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
from thefuzz import fuzz

# -------------------------------
# 🔍 Department Classification
# -------------------------------
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

def classify_department(title: str) -> str:
    title = title.lower()
    best_match = ("Other", 0)
    for department, keywords in department_keywords.items():
        for kw in keywords:
            score = fuzz.partial_ratio(kw, title)
            if score > best_match[1]:
                best_match = (department, score)
    return best_match[0] if best_match[1] > 75 else "Other"

# -------------------------------
# 🏠 Location Classification (Improved)
# -------------------------------
def classify_location(text: str) -> str:
    if not text:
        return "Unclear"

    text = text.lower()

    if "remote" in text or "remotely" in text or "work from home" in text:
        return "Remote"

    if "hybrid" in text or "mixed model" in text or "both remote and onsite" in text:
        return "Hybrid"

    if any(word in text for word in ["onsite", "on-site", "office", "in-person", "physical location"]):
        return "Onsite"

    if any(word in text for word in ["part time", "part-time", "flexible hours"]):
        return "Part time"

    keywords = {
        "Remote": ["virtual", "telecommute", "home-based", "telework"],
        "Hybrid": ["hybrid model", "split office", "part remote"],
        "Onsite": ["office environment", "at the office", "work at site"],
        "Part time": ["part time", "flex schedule", "temporary"]
    }

    for category, terms in keywords.items():
        for term in terms:
            score = fuzz.partial_ratio(term, text)
            if score >= 80:
                return category

    return "Unclear"

# -------------------------------
# 📜 Logging
# -------------------------------
def log(msg: str):
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    print(f"{timestamp} {msg}")
    with open("scraper_log.txt", "a", encoding="utf-8") as f:
        f.write(f"{timestamp} {msg}\n")

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

    chromedriver_path = str(Path(__file__).resolve().parent.parent / "chromedriver.exe")
    if not os.path.exists(chromedriver_path):
        raise FileNotFoundError(f"chromedriver.exe not found at: {chromedriver_path}")
    service = Service(chromedriver_path)

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

                    job_data = {
                        "Job Title": job_title,
                        "Company": company_name,
                        "Description": description,
                        "Minimum Qualification": extract_field("Qualification"),
                        "Skills Required": extract_field("Skills"),
                        "Location": location,
                        "Work Type": classify_location(location),
                        "Years of Experience": extract_field("Experience"),
                        "Department": classify_department(job_title)
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
                        "Department": classify_department(job_title)
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
