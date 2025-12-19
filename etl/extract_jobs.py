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

# ... (Previous code sections remain unchanged) ...

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
