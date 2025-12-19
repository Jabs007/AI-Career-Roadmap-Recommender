import pandas as pd
import mysql.connector
from mysql.connector import Error

def load_jobs(cursor, connection):
    print("📂 Loading job data...")

    try:
        df = pd.read_csv("data/myjobmag_jobs.csv")
    except FileNotFoundError:
        print("❌ Error: 'data/myjobmag_jobs.csv' not found.")
        return

    # Replace NaN with None for SQL compatibility
    df = df.where(pd.notnull(df), None)

    inserted, skipped = 0, 0

    for _, row in df.iterrows():
        try:
            cursor.execute("""
                INSERT INTO jobs (
                    job_title, company, description,
                    minimum_qualification, skills_required,
                    location, work_type, years_of_experience, department
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                row["Job Title"],
                row["Company"],
                row["Description"],
                row["Minimum Qualification"],
                row["Skills Required"],
                row["Location"],
                row["Work Type"],
                row["Years of Experience"],
                row["Department"]
            ))
            inserted += 1
        except Error as e:
            print(f"❌ Job insert failed: {e}")
            skipped += 1

    connection.commit()
    print(f"✅ Inserted: {inserted} jobs")
    print(f"⚠️ Skipped: {skipped} jobs")

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
            load_jobs(cursor, connection)

    except Error as e:
        print(f"❌ Error: {e}")

    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()
            print("🔌 MySQL connection closed.")

if __name__ == "__main__":
    main()
