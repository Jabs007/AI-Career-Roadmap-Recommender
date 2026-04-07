"""
BrighterMonday Kenya Scraper
============================
Scrapes job listings from https://www.brightermonday.co.ke using Selenium.
Produces the same column schema as extract_jobs.py (MyJobMag) so both
data sources can be merged cleanly by update_jobs.py.
"""

import time
import json
import re
import os
import pandas as pd # type: ignore
from pathlib import Path
from datetime import datetime
from selenium import webdriver # type: ignore
from selenium.webdriver.chrome.service import Service # type: ignore
from selenium.webdriver.chrome.options import Options # type: ignore
from selenium.webdriver.common.by import By # type: ignore
from selenium.webdriver.support.ui import WebDriverWait # type: ignore
from selenium.webdriver.support import expected_conditions as EC # type: ignore
from webdriver_manager.chrome import ChromeDriverManager # type: ignore

# Reuse shared classification utilities from the existing ETL module
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from etl.extract_jobs import classify_department, normalize_department # type: ignore

# ─────────────────────────────────────────────────────────────────────────────
def _log(msg: str):
    print(f"[BrighterMonday | {datetime.now():%H:%M:%S}] {msg}")

# ─────────────────────────────────────────────────────────────────────────────
def _build_driver(headless: bool = True) -> webdriver.Chrome:
    opts = Options()
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=opts)

# ─────────────────────────────────────────────────────────────────────────────
def _safe_text(driver, css: str, parent=None) -> str:
    """Return stripped text for a CSS selector, or '' on failure."""
    try:
        root = parent if parent else driver
        return root.find_element(By.CSS_SELECTOR, css).text.strip()
    except Exception:
        return ""

def _safe_attr(driver, css: str, attr: str, parent=None) -> str:
    try:
        root = parent if parent else driver
        return root.find_element(By.CSS_SELECTOR, css).get_attribute(attr).strip()
    except Exception:
        return ""

# ─────────────────────────────────────────────────────────────────────────────
def scrape_brightermonday(pages: int = 5,
                          headless: bool = True,
                          delay: float = 1.5,
                          json_path: str = "data/brightermonday_jobs.json",
                          csv_path:  str = "data/brightermonday_jobs.csv") -> list:
    """
    Scrape BrighterMonday Kenya and return a list of job dicts with the same
    schema as extract_jobs.scrape_myjobmag().
    """
    driver = _build_driver(headless)
    wait  = WebDriverWait(driver, 20)
    all_jobs: list[dict] = []

    BASE_URL = "https://www.brightermonday.co.ke/jobs"

    try:
        for page in range(1, pages + 1):
            url = f"{BASE_URL}?page={page}" if page > 1 else BASE_URL
            _log(f"📄 Fetching page {page}: {url}")
            driver.get(url)

            # Wait for job cards to render
            try:
                wait.until(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "article[data-cy='job-card']")
                ))
            except Exception:
                _log(f"⚠️  No job cards found on page {page}, trying fallback…")
                try:
                    wait.until(EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "div.search-result-item, div[class*='JobCard'], a[href*='/jobs/']")
                    ))
                except Exception:
                    _log(f"❌  Skipping page {page}")
                    continue

            cards = driver.find_elements(By.CSS_SELECTOR, "article[data-cy='job-card']")
            if not cards:
                # Broad fallback selector
                cards = driver.find_elements(
                    By.CSS_SELECTOR, "div.search-result-item, div[class*='JobCard']"
                )

            _log(f"   Found {len(cards)} job card(s) on page {page}")

            for card in cards:
                try:
                    # ── Title + URL ──────────────────────────────────────
                    title_elem = card.find_element(By.CSS_SELECTOR, "h3 a, h2 a, a[data-cy='job-title']")
                    job_title = title_elem.text.strip()
                    job_link  = title_elem.get_attribute("href")
                except Exception:
                    continue

                # ── Company ───────────────────────────────────────────
                company = ""
                for sel in ["span[data-cy='company-name']", "div.company-name", "p.company"]:
                    company = _safe_text(driver, sel, parent=card)
                    if company:
                        break

                # ── Location (card-level) ─────────────────────────────
                location = ""
                for sel in ["span[data-cy='job-location']", "li.location", "span.location"]:
                    location = _safe_text(driver, sel, parent=card)
                    if location:
                        break

                # ── Visit detail page for description + category ───────
                description: str = ""
                category: str = ""
                skills_text: str = ""
                experience: str = ""
                description, category, skills_text, experience = "", "", "", ""
                driver.execute_script("window.open('');")
                driver.switch_to.window(driver.window_handles[-1])
                try:
                    driver.get(job_link)
                    wait.until(EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "div[data-cy='job-description'], div.job-description, section.description")
                    ))
                    for sel in ["div[data-cy='job-description']", "div.job-description", "section.description", "div.content"]:
                        description = _safe_text(driver, sel)
                        if description:
                            break

                    # Extract category label shown on detail page
                    for sel in ["span[data-cy='job-category']", "a[href*='/jobs-by-category/']",
                                "li.job-detail-category span"]:
                        category = _safe_text(driver, sel)
                        if category:
                            break

                    # Extract experience text
                    for sel in ["li[data-cy='experience']", "span.experience", "li.experience"]:
                        experience = _safe_text(driver, sel)
                        if experience:
                            break

                    # Try to grab skills / required info from description
                    from typing import Any
                    desc_content: Any = description or ""
                    for line in desc_content.split("\n"): # type: ignore
                        if re.search(r"skill|qualification|require|proficien", line.lower()):
                            skills_text += str(line).strip() + " " # type: ignore
                    
                    st_any: Any = skills_text
                    skills_text = str(st_any.strip())[:500] # type: ignore

                except Exception:
                    pass
                finally:
                    try:
                        driver.close()
                    except Exception:
                        pass
                    driver.switch_to.window(driver.window_handles[0])

                # ── Department classification ──────────────────────────
                classified_dept = classify_department(job_title, description, skills_text)
                dept_norm = normalize_department(
                    category if category else classified_dept,
                    f"{job_title} {description} {skills_text}"
                )

                all_jobs.append({
                    "Job Title":              job_title,
                    "Company":                company,
                    "Description":            str(description)[:2000],   # type: ignore
                    "Minimum Qualification":  "",
                    "Skills Required":        skills_text,
                    "Skillmentequired":       skills_text,
                    "Location":               location,
                    "Work Type":              "Unclear",
                    "Years of Experience":    experience,
                    "Category":               category,
                    "Department":             classified_dept,
                    "DeptNorm":               dept_norm,
                    "Url":                    job_link,
                    "Source":                 "BrighterMonday"
                })
                time.sleep(delay)

    finally:
        driver.quit()

    # ── Persist results ────────────────────────────────────────────────────
    os.makedirs(os.path.dirname(json_path) if os.path.dirname(json_path) else ".", exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(all_jobs, f, indent=2, ensure_ascii=False)
    pd.DataFrame(all_jobs).to_csv(csv_path, index=False, encoding="utf-8")

    _log(f"✅  Saved {len(all_jobs)} BrighterMonday jobs → {csv_path}")
    return all_jobs


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    scrape_brightermonday(pages=10)
