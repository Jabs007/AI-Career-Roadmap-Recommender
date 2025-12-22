import pandas as pd
import json
import re

# Load the KUCCPS courses CSV
df = pd.read_csv('Kuccps/kuccps_courses.csv')

# Function to parse subject requirement
def parse_subject(sub_str):
    if pd.isna(sub_str) or sub_str == '':
        return None
    # Example: "MAT A(121):C" -> "Mathematics": "C"
    match = re.match(r'(\w+)\s*\w*\(\d+\):(.*)', sub_str)
    if match:
        subj_code = match.group(1)
        grade = match.group(2).strip()
        # Map codes to subjects
        subj_map = {
            'MAT': 'Mathematics',
            'ENG': 'English',
            'KIS': 'Kiswahili',
            'BIO': 'Biology',
            'CHE': 'Chemistry',
            'PHY': 'Physics',
            'HIS': 'History',
            'GEO': 'Geography',
            'COM': 'Computer_Studies',
            'BUS': 'Business_Studies',
            'AGR': 'Agriculture',
            'FRE': 'French',
            'GER': 'German',
            'ARA': 'Arabic',
            'MUS': 'Music',
            'ART': 'Art_and_Design',
            'CRE': 'Christian_Religious_Education',
            'IRE': 'Islamic_Religious_Education',
            'HRE': 'Hindu_Religious_Education',
            'HOM': 'Home_Science',
            'BST': 'Building_Construction',
            'PHE': 'Physical_Education',
            'AVI': 'Aviation',
            'ELE': 'Electricity',
            'PWR': 'Power_Mechanics',
            'MET': 'Metalwork',
            'WOD': 'Woodwork',
            'DRW': 'Drawing_and_Design',
            'AVT': 'Automotive',
            'ELT': 'Electrical_Electronics',
            'CMP': 'Computer_Studies',
            'INF': 'Information_Communication_Technology'
        }
        subj = subj_map.get(subj_code, subj_code)
        return subj, grade
    return None

# Group by Programme_Name
requirements = {}
for _, row in df.iterrows():
    prog = row['Programme_Name']
    if pd.isna(prog):
        continue
    cutoff_str = row['Cutoff_2023']
    if pd.isna(cutoff_str):
        cutoff_str = row['Cutoff_2022']
    if pd.isna(cutoff_str):
        continue
    try:
        cutoff = float(cutoff_str)
    except ValueError:
        continue
    # Assume cutoff is the min_mean_grade, but actually it's the cluster points
    # For simplicity, map to grade
    # But cutoffs are mean points, so for degree, usually C+ =7, but varies
    # For now, set min_mean_grade based on cutoff
    if cutoff >= 10:
        min_grade = 'B-'
    elif cutoff >= 7:
        min_grade = 'C+'
    elif cutoff >= 5:
        min_grade = 'C-'
    else:
        min_grade = 'D+'

    required_subjects = {}
    for i in range(1,5):
        subj_str = row.get(f'Subject_{i}')
        parsed = parse_subject(subj_str)
        if parsed:
            subj, grade = parsed
            required_subjects[subj] = grade

    if prog not in requirements:
        requirements[prog] = {
            "min_mean_grade": min_grade,
            "required_subjects": required_subjects,
            "level": "Degree"  # Assume degree
        }
    else:
        # Merge subjects if different
        for subj, grade in required_subjects.items():
            if subj not in requirements[prog]["required_subjects"]:
                requirements[prog]["required_subjects"][subj] = grade

# Save to json
with open('Kuccps/kuccps_requirements.json', 'w') as f:
    json.dump(requirements, f, indent=2)

print("Built requirements.json from CSV.")