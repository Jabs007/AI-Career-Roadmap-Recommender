from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

options = Options()
options.add_argument("--headless")
driver = webdriver.Chrome(service=Service(), options=options)

driver.get("https://www.myjobmag.co.ke/jobs")
time.sleep(2)

# TEST: try printing job card count
cards = driver.find_elements(By.CSS_SELECTOR, ".job-listing")
print(f"Found {len(cards)} job cards.")

for card in cards[:3]:  # Try just a few
    try:
        title_elem = card.find_element(By.CSS_SELECTOR, ".job-title a")
        print("Title:", title_elem.text)
        print("Link:", title_elem.get_attribute("href"))
    except Exception as e:
        print("❌ Could not extract job title:", e)

driver.quit()
