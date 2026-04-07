"""
Enhanced Update Script with Automatic Backups
Scrapes BOTH MyJobMag and BrighterMonday Kenya, merges and deduplicates them,
then recomputes demand metrics from the unified dataset.
"""
import os
import sys
import shutil
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def backup_existing_data():
    """Backup existing data files before updating"""
    backup_dir = project_root / "data" / "backups"
    backup_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    files_to_backup = [
        "data/myjobmag_jobs.csv",
        "data/myjobmag_jobs.json",
        "data/brightermonday_jobs.csv",
        "data/all_jobs_merged.csv",
        "data/job_demand_metrics.csv"
    ]
    
    print("\n💾 Backing up existing data...")
    backed_up = 0
    
    for file_path in files_to_backup:
        full_path = project_root / file_path
        if full_path.exists():
            filename = full_path.stem
            extension = full_path.suffix
            backup_name = f"{filename}_{timestamp}{extension}"
            backup_path = backup_dir / backup_name
            
            shutil.copy2(full_path, backup_path)
            size_kb = backup_path.stat().st_size / 1024
            print(f"  ✅ Backed up: {backup_name} ({size_kb:.1f} KB)")
            backed_up += 1 # type: ignore
    
    if backed_up > 0:
        print(f"  📁 Backups saved to: {backup_dir}")
    else:
        print("  ℹ️ No existing files to backup")
    
    return backed_up

def cleanup_old_backups(keep_last_n=10):
    """Keep only the last N backups to save disk space"""
    backup_dir = project_root / "data" / "backups"
    if not backup_dir.exists():
        return
    
    backup_files = sorted(backup_dir.glob("*"), key=lambda x: x.stat().st_mtime, reverse=True)
    
    from collections import defaultdict
    grouped = defaultdict(list)
    
    for f in backup_files:
        base = '_'.join(f.name.split('_')[:2]) # type: ignore
        grouped[base].append(f)
    
    deleted = 0
    for base, files in grouped.items():
        for old_file in files[keep_last_n:]: # type: ignore
            old_file.unlink()
            deleted += 1 # type: ignore
    
    if deleted > 0:
        print(f"  🗑️ Cleaned up {deleted} old backup(s) (keeping last {keep_last_n})")

def merge_and_deduplicate(dfs: list, output_csv: str) -> int:
    """
    Merge multiple DataFrames, deduplicate by (Job Title, Company),
    and save to the unified CSV used by the recommender.
    Returns the total number of unique jobs.
    """
    import pandas as pd # type: ignore

    combined = pd.concat(dfs, ignore_index=True)
    before = len(combined)
    
    # Normalise key columns for dedup
    combined["_title_lower"] = combined["Job Title"].str.lower().str.strip()
    combined["_company_lower"] = combined["Company"].str.lower().str.strip()
    combined.drop_duplicates(subset=["_title_lower", "_company_lower"], inplace=True)
    combined.drop(columns=["_title_lower", "_company_lower"], inplace=True)
    
    # Reset index
    combined.reset_index(drop=True, inplace=True)
    combined.to_csv(output_csv, index=False, encoding="utf-8")
    
    after = len(combined)
    print(f"  📊 Merged: {before} raw → {after} unique jobs saved to {output_csv}")
    return after

def main():
    print("=" * 65)
    print("🔄 MULTI-SOURCE JOB DATA PIPELINE  (MyJobMag + BrighterMonday)")
    print("=" * 65)
    
    # ── Step 0: Backup ────────────────────────────────────────────────
    backup_existing_data()
    
    import pandas as pd # type: ignore
    scraped_dfs = []

    # ── Step 1: Scrape MyJobMag ───────────────────────────────────────
    print("\n📡 Step 1: Scraping MyJobMag Kenya...")
    try:
        from etl.extract_jobs import scrape_myjobmag # type: ignore
        scrape_myjobmag(pages=5)
        myjobmag_csv = project_root / "data" / "myjobmag_jobs.csv"
        if myjobmag_csv.exists():
            df_mj = pd.read_csv(myjobmag_csv)
            df_mj["Source"] = "MyJobMag"
            scraped_dfs.append(df_mj)
            print(f"  ✅ MyJobMag: {len(df_mj)} jobs scraped.")
        else:
            print("  ⚠️  MyJobMag CSV not found after scrape.")
    except Exception as e:
        print(f"  ❌ MyJobMag scraping failed: {e}")

    # ── Step 2: Scrape BrighterMonday ────────────────────────────────
    print("\n📡 Step 2: Scraping BrighterMonday Kenya...")
    try:
        from etl.scrape_brightermonday import scrape_brightermonday # type: ignore
        scrape_brightermonday(pages=5)
        bm_csv = project_root / "data" / "brightermonday_jobs.csv"
        if bm_csv.exists():
            df_bm = pd.read_csv(bm_csv)
            scraped_dfs.append(df_bm)
            print(f"  ✅ BrighterMonday: {len(df_bm)} jobs scraped.")
        else:
            print("  ⚠️  BrighterMonday CSV not found after scrape.")
    except Exception as e:
        print(f"  ❌ BrighterMonday scraping failed: {e}")

    # ── Step 3: Merge & Deduplicate ───────────────────────────────────
    merged_csv = str(project_root / "data" / "myjobmag_jobs.csv")  # keep original path for recommender
    if scraped_dfs:
        print("\n🔗 Step 3: Merging and deduplicating all sources...")
        total = merge_and_deduplicate(scraped_dfs, merged_csv)
        # Also save a separate all_jobs file for admin inspection
        all_csv = str(project_root / "data" / "all_jobs_merged.csv")
        import shutil as _shutil
        _shutil.copy2(merged_csv, all_csv)
    else:
        print("\n⚠️ No data scraped from any source. Aborting merge.")
        return False

    # ── Step 4: Recompute demand metrics off the merged dataset ───────
    print("\n📊 Step 4: Recomputing demand metrics from merged data...")
    try:
        from models.compute_demand_metrics import compute_demand_metrics # type: ignore
        compute_demand_metrics(
            jobs_csv_path=merged_csv,
            output_path=str(project_root / "data" / "job_demand_metrics.csv")
        )
        print("  ✅ Demand metrics updated!")
    except Exception as e:
        print(f"  ⚠️ Could not update demand metrics: {e}")

    # ── Step 5: Verify ───────────────────────────────────────────────
    print("\n🔍 Step 5: Verifying data files...")
    required_files = [
        "data/myjobmag_jobs.csv",
        "data/job_demand_metrics.csv"
    ]
    all_exist = True
    for file_path in required_files:
        full_path = project_root / file_path
        if full_path.exists():
            size_kb = full_path.stat().st_size / 1024
            print(f"  ✅ {file_path} ({size_kb:.1f} KB)")
        else:
            print(f"  ❌ {file_path} - NOT FOUND")
            all_exist = False

    # ── Step 6: Cleanup old backups ───────────────────────────────────
    print("\n🧹 Step 6: Managing backups...")
    cleanup_old_backups(keep_last_n=10)

    if all_exist:
        print("\n" + "=" * 65)
        print(f"✅ SUCCESS! Combined job dataset ready ({total:,} unique jobs).")
        print("=" * 65)
        print("\n💡 Restart the Streamlit app to use the latest data.")
        print("📁 Historical backups saved in: data/backups/")
        return True
    else:
        print("\n⚠️ Some files are missing. Check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
