# 🔄 Auto-Update Job Data System

## Overview

This system ensures your AI Career Recommender always uses **fresh, live job market data** without manual intervention.

## How It Works

### 📊 Data Flow

```
┌─────────────────┐
│  Job Scraper    │  Scrapes MyJobMag daily
│ extract_jobs.py │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────┐
│  data/myjobmag_jobs.csv     │  Raw job listings
│  data/myjobmag_jobs.json    │
└────────┬────────────────────┘
         │
         ▼
┌──────────────────────────────┐
│  compute_demand_metrics.py   │  Calculates market demand
└────────┬─────────────────────┘
         │
         ▼
┌──────────────────────────────┐
│  data/job_demand_metrics.csv │  Department demand scores
└────────┬─────────────────────┘
         │
         ▼
┌──────────────────────────────┐
│  CareerRecommender System    │  Uses fresh data for recommendations
│  (config.ini points here)    │
└──────────────────────────────┘
```

## Quick Start

### Option 1: Manual Update (Recommended for Testing)

Run the auto-update script whenever you want fresh data:

```bash
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Run the update script
python update_jobs.py
```

This will:
1. ✅ Scrape latest jobs from MyJobMag
2. ✅ Save to `data/myjobmag_jobs.csv` and `.json`
3. ✅ Auto-calculate demand metrics
4. ✅ Verify all files are updated

### Option 2: Scheduled Daily Updates (Windows)

Set up a Windows Task Scheduler to run daily at 2 AM:

1. Open **Task Scheduler**
2. Click **Create Basic Task**
3. Name: "Update Career Recommender Jobs"
4. Trigger: **Daily** at 2:00 AM
5. Action: **Start a program**
   - Program: `C:\Users\HP\Videos\KUCCUPS_JOBS_ETL\.venv\Scripts\python.exe`
   - Arguments: `update_jobs.py`
   - Start in: `C:\Users\HP\Videos\KUCCUPS_JOBS_ETL`

### Option 3: GitHub Actions (Automated Cloud)

The project includes a GitHub Actions workflow that can run the scraper automatically:

```yaml
# .github/workflows/scrape-jobs.yml (create this file)
name: Daily Job Scraper

on:
  schedule:
    - cron: '0 2 * * *'  # Runs at 2 AM UTC daily
  workflow_dispatch:  # Manual trigger

jobs:
  scrape:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run scraper
        run: python update_jobs.py
      - name: Commit updated data
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          git add data/
          git commit -m "Auto-update job data" || echo "No changes"
          git push
```

## File Structure

### Configuration (`config.ini`)

```ini
[paths]
demand_csv = data/job_demand_metrics.csv
skill_map_json = data/career_skill_map.json
jobs_csv = data/myjobmag_jobs.csv  ← Points to auto-updated file
kuccps_csv = Kuccps/kuccps_courses.csv
requirements_json = Kuccps/kuccps_requirements.json
```

### Data Files

| File | Purpose | Updated By |
|------|---------|------------|
| `data/myjobmag_jobs.csv` | Raw scraped jobs | Scraper |
| `data/myjobmag_jobs.json` | JSON format jobs | Scraper |
| `data/job_demand_metrics.csv` | Market demand scores | Auto-computed |
| `data/career_skill_map.json` | Skills mapping | Manual (rarely) |

## Verification

After running `update_jobs.py`, verify the updates:

```bash
# Check file timestamps
ls -l data/myjobmag_jobs.csv
ls -l data/job_demand_metrics.csv

# View job count
python -c "import pandas as pd; df = pd.read_csv('data/myjobmag_jobs.csv'); print(f'Total jobs: {len(df)}')"

# View demand metrics
python -c "import pandas as pd; df = pd.read_csv('data/job_demand_metrics.csv'); print(df.head())"
```

## Troubleshooting

### Issue: Scraper fails with ChromeDriver error

**Solution**: The scraper uses `webdriver-manager` which auto-downloads ChromeDriver. Ensure Chrome browser is installed.

```bash
pip install --upgrade webdriver-manager
```

### Issue: "No departments found"

**Solution**: Verify `Kuccps/kuccps_courses.csv` exists and has a `departments` column.

### Issue: Recommender still shows old data

**Solution**: Restart the Streamlit app to reload the data:

```bash
# Stop current server (Ctrl+C)
# Restart
streamlit run app.py
```

Or use the "Sync Market Data" button in the sidebar (clears cache).

## Best Practices

1. **Run scraper during off-peak hours** (2-4 AM) to avoid rate limiting
2. **Monitor scraper logs** at `etl/scraper_log.txt`
3. **Backup data weekly** before running scraper
4. **Test with small page count** first: `scrape_myjobmag(pages=2)`

## Advanced: Custom Scraping

Edit `etl/extract_jobs.py` to customize:

```python
# Scrape more pages
scrape_myjobmag(pages=20)  # Default is 10

# Change output location (not recommended)
scrape_myjobmag(
    json_path="custom/path/jobs.json",
    csv_path="custom/path/jobs.csv"
)
```

## Monitoring

Track scraper performance:

```bash
# View recent scraper logs
tail -n 50 etl/scraper_log.txt

# Count jobs by department
python -c "import pandas as pd; df = pd.read_csv('data/myjobmag_jobs.csv'); print(df['Department'].value_counts())"
```

## Questions?

- Check `etl/scraper_log.txt` for detailed logs
- Review `error_log.txt` for system errors
- See `CONTRIBUTING.md` for development guidelines
