# etl/create_tables.py

from database import create_connection

def create_tables():
    connection = create_connection()
    if connection:
        cursor = connection.cursor()

        # Jobs Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                job_title VARCHAR(255),
                company VARCHAR(255),
                description TEXT,
                min_qualification VARCHAR(255),
                skills_required TEXT,
                location VARCHAR(255),
                experience VARCHAR(255),
                date_posted VARCHAR(100),
                job_link TEXT,
                department VARCHAR(100)
            );
        """)

        # Programmes Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS programmes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                programme_code VARCHAR(50),
                institution_name VARCHAR(255),
                department VARCHAR(255),
                programme_name VARCHAR(255),
                cutoff_2023 VARCHAR(10),
                cutoff_2022 VARCHAR(10),
                subject_1 VARCHAR(255),
                subject_2 VARCHAR(255),
                subject_3 VARCHAR(255),
                subject_4 VARCHAR(255)
            );
        """)

        connection.commit()
        print("✅ Tables created successfully")
        connection.close()

if __name__ == "__main__":
    create_tables()
