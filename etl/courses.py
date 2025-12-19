# etl/courses.py

import pandas as pd
import mysql.connector
from mysql.connector import Error

def get_department_mapping(cursor):
    cursor.execute("SELECT id, department_name FROM departments")
    return {name.strip().lower(): id for id, name in cursor.fetchall()}

def insert_missing_department(cursor, connection, dept_name):
    try:
        cursor.execute("INSERT INTO departments (department_name) VALUES (%s)", (dept_name,))
        connection.commit()
        print(f"➕ Added missing department: {dept_name}")
        return cursor.lastrowid
    except Error as e:
        print(f"❌ Failed to add department '{dept_name}': {e}")
        return None

def load_programmes(cursor, connection):
    print("📂 Loading programme data...")

    try:
        df = pd.read_csv("kuccps/kuccps_courses.csv")
    except FileNotFoundError:
        print("❌ Error: CSV file not found at 'kuccps/kuccps_courses.csv'")
        return

    df = df.where(pd.notnull(df), None)
    dept_map = get_department_mapping(cursor)

    inserted, skipped = 0, 0

    for _, row in df.iterrows():
        raw_dept = str(row.get("departments", "")).strip()
        dept_key = raw_dept.lower()

        # Check if department is known, if not — insert
        department_id = dept_map.get(dept_key)
        if not department_id:
            department_id = insert_missing_department(cursor, connection, raw_dept)
            if department_id:
                dept_map[dept_key] = department_id  # Update map
            else:
                skipped += 1
                continue

        try:
            cursor.execute("""
                INSERT INTO programmes (
                    Program_Code, Institution_Name, department_id,
                    Programme_Name, Cutoff_2023, Cutoff_2022,
                    Subject_1, Subject_2, Subject_3, Subject_4
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                row.get("Program_Code"),
                row.get("Institution_Name"),
                department_id,
                row.get("Programme_Name"),
                row.get("Cutoff_2023"),
                row.get("Cutoff_2022"),
                row.get("Subject_1"),
                row.get("Subject_2"),
                row.get("Subject_3"),
                row.get("Subject_4")
            ))
            inserted += 1
        except Error as e:
            print(f"❌ Programme insert failed: {e}")
            skipped += 1

    connection.commit()
    print(f"✅ Inserted: {inserted} programmes")
    print(f"⚠️ Skipped: {skipped} programmes")

def main():
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',
            database='kuccps_jobs'
        )

        if connection.is_connected():
            print("✅ Connected to MySQL database")
            cursor = connection.cursor()
            load_programmes(cursor, connection)

    except Error as e:
        print(f"❌ Error: {e}")

    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()
            print("🔌 MySQL connection closed.")

if __name__ == "__main__":
    main()
