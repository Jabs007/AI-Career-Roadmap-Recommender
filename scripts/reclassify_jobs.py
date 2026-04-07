import pandas as pd # type: ignore
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from etl.extract_jobs import classify_department, normalize_department # type: ignore
from models.compute_demand_metrics import compute_demand_metrics

# Load the existing scraped data
df = pd.read_csv('data/myjobmag_jobs.csv')

def reclassify(row):
    title = str(row.get('Job Title', ''))
    desc = str(row.get('Description', ''))
    skills = str(row.get('Skills Required', ''))
    raw_cat = str(row.get('Category', ''))
    
    classified_dept = classify_department(title, desc, skills)
    # Prefer explicit category if provided, but raw_category is often empty or bad in scrapers
    # So we use the new logic
    dept_norm = normalize_department(raw_cat or classified_dept, f"{title} {desc} {skills}")
    
    return pd.Series({'Department': classified_dept, 'DeptNorm': dept_norm})

# Apply the new robust classification
df[['Department', 'DeptNorm']] = df.apply(reclassify, axis=1)

# Save back to CSV
df.to_csv('data/myjobmag_jobs.csv', index=False)

print("Reclassification complete. New distribution:")
print(df['DeptNorm'].value_counts())

# Now update the metric scores
compute_demand_metrics("data/myjobmag_jobs.csv", "data/job_demand_metrics.csv")
print("\nMetrics updated successfully!")
