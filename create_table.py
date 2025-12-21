
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "kuccps_jobs"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432")
}

def create_table():
    """Creates the jobs table in the PostgreSQL database."""
    conn = None
    try:
        print("Connecting to the PostgreSQL database...")
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        print("Creating the 'jobs' table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id SERIAL PRIMARY KEY,
                Job_Title TEXT,
                Company TEXT,
                Description TEXT,
                Minimum_Qualification TEXT,
                Skills_Required TEXT,
                Location TEXT,
                Work_Type TEXT,
                Years_of_Experience TEXT,
                Department TEXT
            )
        """)
        
        conn.commit()
        print("Table 'jobs' created successfully.")
        
        cur.close()
    except psycopg2.Error as e:
        print(f"Error creating table: {e}")
    finally:
        if conn is not None:
            conn.close()
            print("Database connection closed.")

if __name__ == "__main__":
    create_table()