import pandas as pd # type: ignore
from typing import List, Dict, Any, cast, Optional, Tuple # type: ignore
import json
import re

# Load the KUCCPS courses CSV
df = pd.read_csv('Kuccps/kuccps_courses.csv')

# Function to parse subject requirement
def parse_subject(sub_str):
    if pd.isna(sub_str) or sub_str == '' or sub_str == 'nan':
        return None
    
    # Map codes to human readable subjects
    subj_map = {
        'MAT': 'Mathematics',
        'MAT A': 'Mathematics',
        'MAT B': 'Mathematics',
        'ENG': 'English',
        'KIS': 'Kiswahili',
        'BIO': 'Biology',
        'CHE': 'Chemistry',
        'PHY': 'Physics',
        'HIS': 'History',
        'GEO': 'Geography',
        'COM': 'Computer Studies',
        'BUS': 'Business Studies',
        'AGR': 'Agriculture',
        'FRE': 'French',
        'GER': 'German',
        'ARA': 'Arabic',
        'MUS': 'Music',
        'ART': 'Art and Design',
        'CRE': 'CRE',
        'IRE': 'IRE',
        'HRE': 'HRE',
        'HOM': 'Home Science',
        'BST': 'Building Construction',
        'PHE': 'Physical Education',
        'AVI': 'Aviation',
        'ELE': 'Electricity',
        'PWR': 'Power Mechanics',
        'MET': 'Metalwork',
        'WOD': 'Woodwork',
        'DRW': 'Drawing and Design',
        'AVT': 'Automotive',
        'ELT': 'Electrical Electronics',
        'CMP': 'Computer Studies',
        'INF': 'ICT'
    }

    # Extract the grade (usually after colon or dash)
    parts = re.split(r'[:\-]', str(sub_str))
    if len(parts) < 2:
        return None
    
    subjects_part = parts[0].strip()
    grade = parts[1].strip()

    # Handle "ENG(101)/KIS(102)" or "MAT A(121)"
    tokens = re.split(r'[/]', subjects_part)
    clean_tokens: List[str] = []
    for t in tokens:
        # Extract letters and spaces (to catch MAT A) but ignore numbers/parentheses
        match = re.match(r'([A-Z\s]+)', t.strip())
        if match:
            code = match.group(1).strip()
            # If it's a known code, use the map
            human_name = subj_map.get(code, code)
            clean_tokens.append(human_name)
    
    if not clean_tokens:
        return None
    
    if len(clean_tokens) > 1:
        # Return as an OR condition
        return "_or_".join(clean_tokens), grade
    else:
        return clean_tokens[0], grade

# Group by Programme_Name
requirements: Dict[str, Any] = {}
reqs_any: Any = requirements
for _, row in df.iterrows():
    prog = row['Programme_Name']
    if pd.isna(prog):
        continue
    
    # Detect Level
    level = "Degree"
    min_grade = "C+" # Default for Degree
    
    prog_upper = prog.upper()
    if "DIPLOMA" in prog_upper:
        level = "Diploma"
        min_grade = "C-"
    elif "CERTIFICATE" in prog_upper:
        level = "Certificate"
        min_grade = "D"
    elif "BACHELOR" in prog_upper:
        level = "Degree"
        min_grade = "C+"
    
    required_subjects = {}
    # Use Subject columns (1 to 4)
    for i in range(1, 5):
        col_name = f'Subject_{i}'
        if col_name in row:
            subj_str = row[col_name]
            parsed = parse_subject(subj_str)
            if parsed:
                subj, grade = parsed
                required_subjects[subj] = grade

    # For programs that appear multiple times (different institutions),
    # we take the most restrictive requirements or the first one found.
    if prog not in reqs_any:
        reqs_any[prog] = {
            "min_mean_grade": min_grade,
            "required_subjects": required_subjects,
            "level": level
        }
    else:
        # Update subjects if new ones found
        for subj, grade in required_subjects.items():
            if subj not in reqs_any[prog]["required_subjects"]: # type: ignore
                reqs_any[prog]["required_subjects"][subj] = grade # type: ignore

# Save to json
with open('Kuccps/kuccps_requirements.json', 'w') as f:
    json.dump(requirements, f, indent=2)

print(f"Built requirements.json for {len(requirements)} unique programs.")
