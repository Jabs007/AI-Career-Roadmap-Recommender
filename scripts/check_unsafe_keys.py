import re

path = r"C:\Users\HP\Videos\KUCCUPS_JOBS_ETL\app.py"
with open(path, encoding="utf-8") as f:
    lines = f.readlines()

# Find places where rec['key'] is used directly (not .get())
pattern = re.compile(r"rec\['([a-z_]+)'\]")
safe_pattern = re.compile(r"rec\.get\(")
dangerous = []
for i, line in enumerate(lines, 1):
    if pattern.search(line) and not safe_pattern.search(line):
        # Skip lines that are just dict assignments or comments
        stripped = line.strip()
        if not stripped.startswith("#") and "rec['" in stripped:
            dangerous.append((i, stripped[:120]))

for ln, content in dangerous:
    print(f"Line {ln}: {content}")
