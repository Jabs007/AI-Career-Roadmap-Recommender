from database import create_connection

def insert_departments(connection):
    cursor = connection.cursor()
    departments = [
        "IT", "Education", "Business", "Engineering", "Health Sciences",
        "Agriculture", "Law", "Arts & Humanities", "Pure Sciences",
        "Environmental Studies", "Hospitality & Tourism",
        "Architecture & Built Environment", "Other"
    ]

    for dept in departments:
        
        try:
            cursor.execute(
                "INSERT IGNORE INTO departments (department_name) VALUES (%s)",
                (dept,)
            )
        except Exception as e:
            print(f"❌ Failed to insert department '{dept}': {e}")
    connection.commit()
    print("✅ Departments inserted.")


def insert_locations(connection):
    cursor = connection.cursor()
    
    # ✅ Expanded list of locations based on keywords in classifier logic
    locations = [
        "Remote",
        "Hybrid",
        "Onsite",
        "Part time",
        "Unclear",
        "Virtual",
        "Telecommute",
        "Home-based",
        "Telework",
        "Mixed model",
        "Both remote and onsite",
        "Split office",
        "Office environment",
        "In-person",
        "Physical location",
        "Flexible hours",
        "Temporary",
        "Flex schedule"
    ]

    for loc in set(locations):  # Remove duplicates just in case
        try:
            cursor.execute(
                "INSERT IGNORE INTO locations (location_name) VALUES (%s)",
                (loc,)
            )
        except Exception as e:
            print(f"❌ Failed to insert location '{loc}': {e}")
    connection.commit()
    print("✅ Locations inserted.")


if __name__ == "__main__":
    conn = create_connection()
    if conn:
        insert_departments(conn)
        insert_locations(conn)
        conn.close()
