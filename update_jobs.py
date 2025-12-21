"""
Enhanced Update Script with Automatic Backups
Keeps historical data while updating to latest
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
        "data/job_demand_metrics.csv"
    ]
    
    print("\n💾 Backing up existing data...")
    backed_up = 0
    
    for file_path in files_to_backup:
        full_path = project_root / file_path
        if full_path.exists():
            filename = full_path.stem  # e.g., "myjobmag_jobs"
            extension = full_path.suffix  # e.g., ".csv"
            backup_name = f"{filename}_{timestamp}{extension}"
            backup_path = backup_dir / backup_name
            
            shutil.copy2(full_path, backup_path)
            size_kb = backup_path.stat().st_size / 1024
            print(f"  ✅ Backed up: {backup_name} ({size_kb:.1f} KB)")
            backed_up += 1
    
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
    
    # Get all backup files sorted by modification time
    backup_files = sorted(backup_dir.glob("*"), key=lambda x: x.stat().st_mtime, reverse=True)
    
    # Group by base name (csv, json, metrics)
    from collections import defaultdict
    grouped = defaultdict(list)
    
    for f in backup_files:
        # Extract base name (before timestamp)
        base = f.name.split('_')[0] + '_' + f.name.split('_')[1]  # e.g., "myjobmag_jobs"
        grouped[base].append(f)
    
    # Keep only last N of each type
    deleted = 0
    for base, files in grouped.items():
        for old_file in files[keep_last_n:]:
            old_file.unlink()
            deleted += 1
    
    if deleted > 0:
        print(f"  🗑️ Cleaned up {deleted} old backup(s) (keeping last {keep_last_n})")

def main():
    print("=" * 60)
    print("🔄 AUTO-UPDATE JOB DATA PIPELINE (With Backups)")
    print("=" * 60)
    
    # Step 0: Backup existing data
    backup_existing_data()
    
    # Step 1: Run the scraper
    print("\n📡 Step 1: Scraping fresh job data from MyJobMag...")
    try:
        from etl.extract_jobs import scrape_myjobmag as scraper_main
        scraper_main()
        print("✅ Scraping completed!")
    except Exception as e:
        print(f"❌ Scraping failed: {e}")
        return False
    
    # Step 2: Update demand metrics
    print("\n📊 Step 2: Computing demand metrics...")
    try:
        from models.compute_demand_metrics import compute_demand_metrics
        compute_demand_metrics(
            jobs_csv_path="data/myjobmag_jobs.csv",
            output_path="data/job_demand_metrics.csv"
        )
        print("✅ Demand metrics updated!")
    except Exception as e:
        print(f"⚠️ Warning: Could not update demand metrics: {e}")
    
    # Step 3: Verify files exist
    print("\n🔍 Step 3: Verifying data files...")
    required_files = [
        "data/myjobmag_jobs.csv",
        "data/myjobmag_jobs.json",
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
    
    # Step 4: Cleanup old backups
    print("\n🧹 Step 4: Managing backups...")
    cleanup_old_backups(keep_last_n=10)
    
    if all_exist:
        print("\n" + "=" * 60)
        print("✅ SUCCESS! All data files updated successfully!")
        print("=" * 60)
        print("\n💡 Your recommender system will now use the latest job data.")
        print("   Restart the Streamlit app to see fresh recommendations.")
        print("\n📁 Historical backups saved in: data/backups/")
        return True
    else:
        print("\n⚠️ Some files are missing. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)