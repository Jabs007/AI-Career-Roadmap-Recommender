# 📁 File Handling & Backup Strategy

## 🎯 Quick Answer

**Q: Does scraping create new files or overwrite existing ones?**

**A: It OVERWRITES the same files, BUT now with automatic backups!** ✅

---

## 📊 How It Works Now

### **Every Time You Run `update_jobs.py`:**

```
STEP 0: Backup (NEW!)
├─ Copies: data/myjobmag_jobs.csv → data/backups/myjobmag_jobs_20241220_214500.csv
├─ Copies: data/myjobmag_jobs.json → data/backups/myjobmag_jobs_20241220_214500.json
└─ Copies: data/job_demand_metrics.csv → data/backups/job_demand_metrics_20241220_214500.csv

STEP 1: Scrape Fresh Data
├─ Scrapes MyJobMag
└─ OVERWRITES: data/myjobmag_jobs.csv (with new jobs)
└─ OVERWRITES: data/myjobmag_jobs.json (with new jobs)

STEP 2: Update Metrics
└─ OVERWRITES: data/job_demand_metrics.csv (with new metrics)

STEP 3: Cleanup
└─ Keeps last 10 backups, deletes older ones
```

---

## 🎁 What You Get

### **Active Files (Always Latest)**
```
data/
├── myjobmag_jobs.csv         ← Latest scraped jobs (OVERWRITES)
├── myjobmag_jobs.json        ← Latest scraped jobs (OVERWRITES)
└── job_demand_metrics.csv    ← Latest metrics (OVERWRITES)
```
**Your recommender uses these** ✅

### **Backup Files (Historical Archive)**
```
data/backups/
├── myjobmag_jobs_20241220_140000.csv      ← Morning scrape
├── myjobmag_jobs_20241220_140000.json
├── job_demand_metrics_20241220_140000.csv
├── myjobmag_jobs_20241220_210000.csv      ← Evening scrape
├── myjobmag_jobs_20241220_210000.json
├── job_demand_metrics_20241220_210000.csv
└── ... (keeps last 10 of each)
```
**For your records/analysis** 📊

---

## ✅ Benefits of This Approach

### **1. Always Fresh Data**
- ✅ Recommender uses latest jobs
- ✅ No stale listings
- ✅ No duplicates

### **2. Historical Tracking**
- ✅ Can compare job trends over time
- ✅ Can restore if scraping fails
- ✅ Can analyze market changes

### **3. Automatic Management**
- ✅ Backups happen automatically
- ✅ Old backups auto-deleted (keeps last 10)
- ✅ No manual file management needed

---

## 📈 Example Timeline

```
Day 1 (Dec 20):
├─ 2:00 AM scrape → 500 jobs
│  ├─ Active: data/myjobmag_jobs.csv (500 jobs)
│  └─ Backup: data/backups/myjobmag_jobs_20241220_020000.csv
│
└─ 2:00 PM scrape → 520 jobs (20 new!)
   ├─ Active: data/myjobmag_jobs.csv (520 jobs) ← OVERWROTE 500
   └─ Backup: data/backups/myjobmag_jobs_20241220_140000.csv

Day 2 (Dec 21):
└─ 2:00 AM scrape → 510 jobs
   ├─ Active: data/myjobmag_jobs.csv (510 jobs) ← OVERWROTE 520
   └─ Backup: data/backups/myjobmag_jobs_20241221_020000.csv
```

**Result:**
- Active file always has latest (510 jobs)
- Backups show history (500 → 520 → 510)

---

## 🔍 Comparing Backups

### **See What Changed Between Scrapes:**

```bash
# Count jobs in current file
python -c "import pandas as pd; print(len(pd.read_csv('data/myjobmag_jobs.csv')))"

# Count jobs in yesterday's backup
python -c "import pandas as pd; print(len(pd.read_csv('data/backups/myjobmag_jobs_20241219_020000.csv')))"

# Compare departments
python -c "
import pandas as pd
current = pd.read_csv('data/myjobmag_jobs.csv')
old = pd.read_csv('data/backups/myjobmag_jobs_20241219_020000.csv')
print('Current:', current['Department'].value_counts())
print('Old:', old['Department'].value_counts())
"
```

---

## 🛡️ Backup Management

### **Automatic Cleanup**
- Keeps last **10 backups** of each file type
- Automatically deletes older backups
- Saves disk space

### **Manual Backup Management**

**View all backups:**
```bash
ls data/backups/
```

**Delete all backups (if needed):**
```bash
rm data/backups/*
```

**Keep specific backup:**
```bash
# Copy important backup to safe location
cp data/backups/myjobmag_jobs_20241220_020000.csv important_backups/
```

---

## 🔄 Restore from Backup

If a scrape fails or you want to restore old data:

```bash
# Restore from specific backup
cp data/backups/myjobmag_jobs_20241220_020000.csv data/myjobmag_jobs.csv
cp data/backups/myjobmag_jobs_20241220_020000.json data/myjobmag_jobs.json
cp data/backups/job_demand_metrics_20241220_020000.csv data/job_demand_metrics.csv

# Restart Streamlit
streamlit run app.py
```

---

## 📊 File Naming Convention

```
Format: {filename}_{YYYYMMDD}_{HHMMSS}.{ext}

Examples:
myjobmag_jobs_20241220_140530.csv
                │        │
                │        └─ Time: 2:05:30 PM
                └─ Date: Dec 20, 2024

job_demand_metrics_20241221_020000.csv
                    │        │
                    │        └─ Time: 2:00:00 AM
                    └─ Date: Dec 21, 2024
```

---

## 💡 Best Practices

### **1. Regular Scraping**
- ✅ Daily scrapes at 2 AM (automated)
- ✅ Backups accumulate automatically
- ✅ Can track market trends

### **2. Monitor Backups**
```bash
# Check backup folder size
du -sh data/backups/

# Count backups
ls data/backups/ | wc -l
```

### **3. Archive Important Backups**
```bash
# Monthly archive (before cleanup deletes them)
mkdir archives/2024-12/
cp data/backups/myjobmag_jobs_20241231_*.csv archives/2024-12/
```

---

## 🎯 Summary

| Aspect | Behavior |
|--------|----------|
| **Active Files** | Always OVERWRITTEN with latest data |
| **Backups** | Automatically created before each scrape |
| **Backup Retention** | Last 10 backups kept |
| **Recommender** | Uses active files (always fresh) |
| **Historical Analysis** | Use backup files |
| **Disk Space** | Auto-managed (old backups deleted) |

---

## ❓ FAQ

**Q: Will I lose old data?**  
A: No! Backups are created automatically before each scrape.

**Q: How many backups are kept?**  
A: Last 10 of each file type (configurable in `update_jobs.py`).

**Q: Can I change the retention period?**  
A: Yes! Edit `update_jobs.py` line: `cleanup_old_backups(keep_last_n=10)` to any number.

**Q: What if I want to keep ALL backups?**  
A: Set `keep_last_n=999999` or comment out the cleanup function.

**Q: Do backups slow down the update?**  
A: No, copying files takes < 1 second.

---

## 🎉 Bottom Line

✅ **Active files** = Always latest (recommender uses these)  
✅ **Backups** = Historical archive (for your analysis)  
✅ **Automatic** = No manual work needed  
✅ **Safe** = Can always restore if needed  

**You get the best of both worlds: fresh data + historical tracking!** 🚀
