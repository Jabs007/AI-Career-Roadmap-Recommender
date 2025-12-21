#!/usr/bin/env python
"""
Quick Update Script - One-liner to refresh all job data
Run this anytime you want fresh job market data!
"""

if __name__ == "__main__":
    import subprocess
    import sys
    
    print("🚀 Quick Update: Refreshing job data...")
    result = subprocess.run([sys.executable, "update_jobs.py"], cwd=".")
    sys.exit(result.returncode)
