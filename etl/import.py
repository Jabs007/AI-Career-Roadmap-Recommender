import os
import re
import time
import logging
import mysql.connector
import pandas as pd
import json
from datetime import datetime
from typing import List, Dict
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from thefuzz import fuzz  # Fuzzy matching for department classification

# ========== CONFIG ==========
COURSES_CSV = os.getenv("COURSES_CSV", r"C:\Users\HP\Documents\KUCCUPS_JOBS_ETL\Kuccps\kuccps_courses.csv")
DB_CONFIG = {
    'host': os.getenv("DB_HOST", 'localhost'),
    'user': os.getenv("DB_USER", 'root'),
    'password': os.getenv("DB_PASSWORD", ''),
    'database': os.getenv("DB_NAME", 'kuccps_jobs')
}
LOG_FILE = os.getenv("LOG_FILE", 'error_log.txt')
DEPT_COLUMN = os.getenv("DEPT_COLUMN", 'departments')
JOBS_JSON = os.getenv("JOBS_JSON", "scraped_jobs.json")
JOBS_CSV = os.getenv("JOBS_CSV", "scraped_jobs.csv")
# ============================

logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')
logging.getLogger().setLevel(logging.INFO)

def get_departments_from_csv(csv_path: str, column: str = DEPT_COLUMN) -> List[str]:
    """Read departments from a CSV file column."""
    try:
        df = pd.read_csv(csv_path)
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found in CSV.")
        depts = df[column].dropna().unique().tolist()
        return [d.strip().lower() for d in depts if isinstance(d, str)]
    except Exception as e:
        logging.error(f"Dept error: {e}")
        return []

def classify_department(job_data: Dict[str, str], departments: List[str], threshold: int = 80) -> str:
    """
    Classify job into department using fuzzy logic on title, description, and qualification.
    Falls back to keyword matching if fuzzy scores are low.
    """
    combined_text = f"{job_data.get('Job_Title', '')} {job_data.get('Description', '')} {job_data.get('Minimum_Qualification', '')}".lower()
    best_match = ("Unclassified", 0)

    for dept in departments:
        score_title = fuzz.partial_ratio(dept.lower(), job_data.get('Job_Title', '').lower())
        score_desc = fuzz.partial_ratio(dept.lower(), job_data.get('Description', '').lower())
        score_qual = fuzz.partial_ratio(dept.lower(), job_data.get('Minimum_Qualification', '').lower())
        score_total = max(score_title, score_desc, score_qual)

        if score_total > best_match[1] and score_total >= threshold:
            best_match = (dept, score_total)

    if best_match[0] == "Unclassified":
        for dept in departments:
            for keyword in dept.lower().split():
                if keyword in combined_text:
                    return dept

    logging.info(f"[CLASSIFY] Best match: {best_match[0]} (Score: {best_match[1]})")
    return best_match[0]

def scrape_jobs(departments: List[str]) -> List[Dict[str, str]]:
    """Scrape jobs from myjobmag.co.ke and classify them."""
    jobs = []
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920,1080")

    with webdriver.Chrome(service=Service(), options=options) as driver:
        wait = WebDriverWait(driver, 15)
        driver.get("https://www.myjobmag.co.ke/jobs")
        try:
            pag = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "setPaginate")))
            pages = pag.find_elements(By.TAG_NAME, "a")
            max_page = int(pages[-1].text) if pages else 1
        except Exception:
            max_page = 1

        for page in range(1, max_page + 1):
            url = f"https://www.myjobmag.co.ke/jobs/page/{page}" if page > 1 else "https://www.myjobmag.co.ke/jobs"
            driver.get(url)
            try:
                wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li.job-list-li")))
            except TimeoutException:
                continue

            cards = driver.find_elements(By.CSS_SELECTOR, "li.job-list-li")
            print(f"🔍 Found {len(cards)} job cards on page {page}")

            for card in cards:
                try:
                    title_elem = card.find_element(By.CSS_SELECTOR, "h2 > a")
                    title = title_elem.text.strip()
                    link = title_elem.get_attribute("href")
                    if not link.startswith("http"):
                        link = "https://www.myjobmag.co.ke" + link

                    logo_elem = card.find_element(By.CSS_SELECTOR, "li.job-logo img")
                    company = logo_elem.get_attribute("alt").strip()

                    # Open job detail in a new tab
                    driver.execute_script("window.open('');")
                    driver.switch_to.window(driver.window_handles[-1])
                    driver.get(link)
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.job-details")))

                    desc = driver.find_element(By.CSS_SELECTOR, "div.job-details").text.strip()

                    def extract(label: str) -> str:
                        match = re.search(fr"{label}:(.*)", desc, re.IGNORECASE)
                        return match.group(1).split("\n")[0].strip() if match else ""

                    qualification = extract("Qualification")
                    experience = extract("Experience")
                    skills = extract("Skills")
                    location = extract("Location")

                    job_data = {
                        'Job_Title': title,
                        'Description': desc,
                        'Minimum_Qualification': qualification
                    }

                    dept = classify_department(job_data, departments)

                    jobs.append({
                        'Job_Title': title,
                        'Company': company,
                        'Description': desc,
                        'Minimum_Qualification': qualification,
                        'Skills_Required': skills,
                        'Location': location,
                        'Work_Type': '',  # Placeholder
                        'Years_of_Experience': experience,
                        'Department': dept
                    })

                except Exception as e:
                    logging.error(f"Job extraction error: {e}")

                finally:
                    if len(driver.window_handles) > 1:
                        driver.close()
                        driver.switch_to.window(driver.window_handles[0])

    return jobs

def save_jobs_to_json(jobs: List[Dict[str, str]], json_path: str = JOBS_JSON) -> None:
    """Save jobs to a JSON file."""
    try:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(jobs, f, ensure_ascii=False, indent=2)
        print(f"✅ Jobs saved to {json_path}")
    except Exception as e:
        logging.error(f"JSON save error: {e}")
        print("❌ Error saving jobs to JSON.")

def save_jobs_to_csv(jobs: List[Dict[str, str]], csv_path: str = JOBS_CSV) -> None:
    """Save jobs to a CSV file."""
    try:
        df = pd.DataFrame(jobs)
        df.to_csv(csv_path, index=False, encoding="utf-8")
        print(f"✅ Jobs saved to {csv_path}")
    except Exception as e:
        logging.error(f"CSV save error: {e}")
        print("❌ Error saving jobs to CSV.")

def load_jobs_to_mysql(jobs: List[Dict[str, str]]) -> None:
    """Insert scraped jobs into MySQL database."""
    try:
        with mysql.connector.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                cur.execute("TRUNCATE TABLE jobs")
                for j in jobs:
                    cur.execute("""
                        INSERT INTO jobs (Job_Title, Company, Description, Minimum_Qualification,
                                          Skills_Required, Location, Work_Type,
                                          Years_of_Experience, Department)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """, tuple(j.values()))
                conn.commit()
        print(f"✅ {len(jobs)} jobs inserted.")
    except Exception as e:
        logging.error(f"DB error: {e}")
        print("❌ DB error - check error_log.")

def main():
    print("🚀 Starting ETL Process...")
    deps = get_departments_from_csv(COURSES_CSV, DEPT_COLUMN)
    if not deps:
        print("⚠️ No departments found. Check your CSV and column name.")
        return
    data = scrape_jobs(deps)
    if data:
        save_jobs_to_json(data)
        save_jobs_to_csv(data)
        load_jobs_to_mysql(data)
    else:
        print("⚠️ No jobs scraped.")
        print("❌ No jobs found to insert.")
    print("✅ ETL Process completed.")

if __name__ == "__main__":
    main()
import mysql.connector