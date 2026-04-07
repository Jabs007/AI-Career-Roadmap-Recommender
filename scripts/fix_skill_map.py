import json

with open('data/career_skill_map.json', 'r') as f:
    data = json.load(f)

# Programs to move
pm_programs = [
    "BACHELOR OF PROJECT PLANNING AND MANAGEMENT",
    "BACHELOR OF PROJECT MANAGEMENT",
    "BACHELOR OF PROJECT DEVELOPMENT AND MANAGEMENT"
]

aviation_programs = [
    "BACHELOR OF AVIATION MANAGEMENT",
    "BACHELOR IN SUPPLY CHAIN AND LOGISTICS MANAGEMENT",
    "BACHELOR OF LOGISTICS AND SUPPLY CHAIN MANAGEMENT"
]

# Add new categories
data["Project Management"] = {
    "skills": ["Project Planning", "Agile/Scrum", "Risk Management", "Stakeholder Communication", "Budgeting", "Delivery"],
    "programs": []
}

data["Aviation & Logistics"] = {
    "skills": ["Supply Chain Management", "Operations Planning", "Fleet Management", "Aviation Regulations", "Logistics Tech"],
    "programs": []
}

# Move programs from 'Other' or anywhere else
for prog in pm_programs:
    for cat in list(data.keys()):
        if prog in data[cat]["programs"] and cat != "Project Management":  # type: ignore
            data[cat]["programs"].remove(prog)  # type: ignore
    data["Project Management"]["programs"].append(prog)  # type: ignore

for prog in aviation_programs:
    for cat in list(data.keys()):
        if prog in data[cat]["programs"] and cat != "Aviation & Logistics":  # type: ignore
            data[cat]["programs"].remove(prog)  # type: ignore
    data["Aviation & Logistics"]["programs"].append(prog)  # type: ignore

# Also ensure "Other" still has its skills array even if empty (it does by default)

with open('data/career_skill_map.json', 'w') as f:
    json.dump(data, f, indent=2)

print("Updated career_skill_map.json successfully.")
