#!/usr/bin/env python
"""
Quick Update Script - One-liner to refresh all job data
Run this anytime you want fresh job market data!
"""

if __name__ == "__main__":
    import subprocess
    import sys
    import os

    # Force UTF-8 to avoid Windows cp1252 issues
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    print("Quick Update: Refreshing job data...")
    # Limit pages via env var (read inside update_jobs.py or extractor if supported)
    result = subprocess.run([sys.executable, "update_jobs.py"], cwd=".", env=env)
    sys.exit(result.returncode)
