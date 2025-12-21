import json
import os

path = os.path.join("Kuccps", "kuccps_requirements.json")

try:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Keywords for programs that typically require B- or higher (Cluster-heavy)
    # We keep these strict, but relax general degrees.
    strict_keywords = [
        "MEDICINE", "SURGERY", "PHARMACY", "DENTAL", "ENGINEERING", 
        "LAW", "ARCHITECT", "VETERINARY", "NURSING", "QUANTITY SURVEYING", "GEOSPATIAL"
    ]

    count = 0
    for course, req in data.items():
        course_upper = course.upper()
        
        is_strict = any(kw in course_upper for kw in strict_keywords)
        
        if not is_strict:
            # Relax B- to C+ (Statutory University Entry)
            if req.get("min_mean_grade") == "B-":
                 req["min_mean_grade"] = "C+"
                 count += 1

    print(f"SUCCESS: Relaxed {count} courses to Mean Grade C+.")

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

except Exception as e:
    print(f"ERROR: {e}")
