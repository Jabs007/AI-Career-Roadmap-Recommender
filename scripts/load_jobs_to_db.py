import os
import sys
import pandas as pd # type: ignore
import psycopg2 # type: ignore
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "kuccps_jobs"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432")
}

def load_jobs_to_db(csv_path="data/myjobmag_jobs.csv"):
    if not os.path.exists(csv_path):
        print(f"File {csv_path} not found.")
        return

    print("Loading jobs from CSV...")
    df = pd.read_csv(csv_path)

    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        print("Connected! Emptying existing jobs table...")
        cur.execute("TRUNCATE TABLE jobs RESTART IDENTITY CASCADE;")
        
        print("Inserting fresh data into PostgreSQL...")
        insert_query = """
            INSERT INTO jobs (Job_Title, Company, Description, Minimum_Qualification, 
                              Skills_Required, Location, Work_Type, Years_of_Experience, Department)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        count = 0
        for index, row in df.iterrows():
            dept = row.get('DeptNorm', row.get('Department', 'Unknown'))
            if pd.isna(dept): dept = 'Unknown'

            data = (
                str(row.get('Job Title', '')) if not pd.isna(row.get('Job Title')) else '',
                str(row.get('Company', '')) if not pd.isna(row.get('Company')) else '',
                str(row.get('Description', '')) if not pd.isna(row.get('Description')) else '',
                str(row.get('Minimum Qualification', '')) if not pd.isna(row.get('Minimum Qualification')) else '',
                str(row.get('Skills Required', '')) if not pd.isna(row.get('Skills Required')) else '',
                str(row.get('Location', '')) if not pd.isna(row.get('Location')) else '',
                str(row.get('Work Type', '')) if not pd.isna(row.get('Work Type')) else '',
                str(row.get('Years of Experience', '')) if not pd.isna(row.get('Years of Experience')) else '',
                str(dept) if not pd.isna(dept) else ''
            )
            
            cur.execute(insert_query, data)
            count += 1
            
        conn.commit()
        print(f"✅ Successfully written {count} jobs into the PostgreSQL database.")
        cur.close()
    except psycopg2.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    load_jobs_to_db()
