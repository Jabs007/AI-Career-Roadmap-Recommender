import pandas as pd

# ---------------------------------------------
# DEPARTMENT CLASSIFICATION FUNCTION
# ---------------------------------------------
def extract_department(programme_name: str) -> str:
    programme = programme_name.lower()

    if any(keyword in programme for keyword in ["engineering", "technology"]):
        return "Engineering"
    elif "education" in programme:
        return "Education"
    elif any(keyword in programme for keyword in ["medicine", "nursing", "pharmacy", "surgery", "clinical"]):
        return "Health Sciences"
    elif any(keyword in programme for keyword in ["business", "commerce", "accounting", "finance", "procurement", "economics"]):
        return "Business"
    elif any(keyword in programme for keyword in ["computer", "ict", "information technology", "software", "data", "ai", "cyber", "informatics"]):
        return "Computing"
    elif any(keyword in programme for keyword in ["agriculture", "agribusiness", "animal", "crop", "food", "horticulture"]):
        return "Agriculture"
    elif any(keyword in programme for keyword in ["law", "criminology", "governance", "security", "international relations", "public policy"]):
        return "Law / Social Sciences"
    elif any(keyword in programme for keyword in ["environment", "forestry", "natural resources", "conservation"]):
        return "Environmental Sciences"
    elif any(keyword in programme for keyword in ["arts", "music", "literature", "theatre", "fine art", "design", "linguistics"]):
        return "Arts & Humanities"
    else:
        return programme_name.strip()  # fallback to full name if no match

# ---------------------------------------------
# MAIN FUNCTION TO LOAD, MAP AND SAVE PROGRAMMES
# ---------------------------------------------
def map_programmes_to_departments(input_csv: str, output_csv: str):
    # Load the cleaned KUCCPS programmes file
    df = pd.read_csv(input_csv)

    # Drop any rows without a programme name
    df = df.dropna(subset=["Programme_Name"])

    # Apply department classification
    df["Department"] = df["Programme_Name"].apply(extract_department)

    # Save the output
    df.to_csv(output_csv, index=False)
    print(f"✅ Saved mapped programmes with departments to: {output_csv}")

# ---------------------------------------------
# ENTRY POINT
# ---------------------------------------------
if __name__ == "__main__":
    input_file = "kuccps/kuccps_courses.csv"
    output_file = "kuccps/Programmes_with_Departments.csv"
    map_programmes_to_departments(input_file, output_file)
