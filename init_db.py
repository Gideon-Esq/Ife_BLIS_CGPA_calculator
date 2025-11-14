import psycopg2
import os

def get_db_connection():
    """Establishes a connection to the PostgreSQL database using the Vercel environment variable."""
    conn_string = os.environ.get('POSTGRES_URL')
    if not conn_string:
        raise ValueError("The POSTGRES_URL environment variable is not set. Please connect a Vercel Postgres database.")
    return psycopg2.connect(conn_string)

def initialize_database():
    """
    Initializes the PostgreSQL database.
    - Creates tables if they do not exist.
    - Populates the courses table if it is empty.
    """
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Create courses table with PostgreSQL syntax
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS courses (
                    id SERIAL PRIMARY KEY,
                    part TEXT NOT NULL,
                    semester TEXT NOT NULL,
                    course_code TEXT NOT NULL UNIQUE,
                    course_title TEXT NOT NULL,
                    course_unit INTEGER NOT NULL
                )
            ''')

            # Create gpa_records table with PostgreSQL syntax
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS gpa_records (
                    record_id TEXT PRIMARY KEY,
                    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    semester_data JSONB,
                    final_gpa REAL,
                    final_cgpa REAL,
                    total_units_taken INTEGER,
                    total_credit_points INTEGER
                )
            ''')
            conn.commit()

            # Check if the courses table is empty before populating
            cursor.execute("SELECT COUNT(1) FROM courses")
            if cursor.fetchone()[0] == 0:
                print("Courses table is empty. Populating with initial data...")

                courses = [
                    ('1', 'Harmattan', 'EDU101', 'Introduction to Teaching Profession', 2),
                    ('1', 'Harmattan', 'ETL101', 'Introduction to Information Work', 2),
                    ('1', 'Harmattan', 'ETL103', 'Introduction to Information Science', 2),
                    ('1', 'Harmattan', 'PHL101', 'Introduction to Philosophy I', 3),
                    ('1', 'Harmattan', 'SSC101', 'Man and His Social Environment', 3),
                    ('1', 'Harmattan', 'YOR101', 'Introduction to the Yoruba People and the Yoruba Language', 3),
                    ('1', 'Rain', 'EDU102', 'Principles and Practice of Education', 2),
                    ('1', 'Rain', 'ETL102', 'Introduction to ICT in Library and Information Services', 2),
                    ('1', 'Rain', 'ETL104', 'Information Resources and Services', 2),
                    ('1', 'Rain', 'ETL106', 'Information Literacy', 2),
                    ('1', 'Rain', 'ETL108', 'Libraries and Societies', 2),
                    ('1', 'Rain', 'ETL110', 'Introduction to Information Management', 2),
                    ('1', 'Rain', 'PHL104', 'Introduction to Philosophy II', 3),
                    ('1', 'Rain', 'SSC102', 'Elements of Economic Theory and Principles', 3),
                    ('1', 'Rain', 'YOR114', 'Introduction to Yoruba Culture', 3),
                    ('2', 'Harmattan', 'ALL201', 'Literacy Education for Adults', 2),
                    ('2', 'Harmattan', 'CSC221', 'Computer Appreciation', 2),
                    ('2', 'Harmattan', 'EFC201', 'Historical Foundations of Education', 2),
                    ('2', 'Harmattan', 'ETL201', 'Principles and Theories of Library and Information Management', 2),
                    ('2', 'Harmattan', 'ETL203', 'Organization of Knowledge I (Classification)', 2),
                    ('2', 'Harmattan', 'ETL205', 'Multimedia Application in Libraries and Information Centers', 2),
                    ('2', 'Harmattan', 'ETL207', 'Introduction to Reference and Information Services', 2),
                    ('2', 'Harmattan', 'ETL209', 'Information Retrieval 1 (Cataloguing)', 2),
                    ('2', 'Rain', 'ASE202', 'Curriculum and Instruction', 2),
                    ('2', 'Rain', 'ETL202', 'Introduction to Educational Technology and Communications', 2),
                    ('2', 'Rain', 'ETL204', 'Preservation and Security of Library and Information Resources', 2),
                    ('2', 'Rain', 'ETL206', 'Library and Information Services to People with Special Needs', 2),
                    ('2', 'Rain', 'ETL208', 'Learning and Communication Skills', 2),
                    ('2', 'Rain', 'ETL212', 'Literature and Library Services for Young People', 2),
                    ('2', 'Rain', 'ETL214', 'Management of Serials and Government Publications', 2),
                    ('2', 'Rain', 'ETL216', 'Introduction to Information Systems', 2),
                    ('3', 'Harmattan', 'EFC303', 'Tests and Measurement', 2),
                    ('3', 'Harmattan', 'ETL301', 'Organization and Management of Learning Resources', 2),
                    ('3', 'Harmattan', 'ETL303', 'Organization of Knowledge II (Classification)', 2),
                    ('3', 'Harmattan', 'ETL305', 'Information Retrieval II (Cataloguing)', 2),
                    ('3', 'Harmattan', 'ETL307', 'Internet and Information Searching II', 2),
                    ('3', 'Harmattan', 'ETL309', 'System Analysis and Design', 2),
                    ('3', 'Harmattan', 'ETL311', 'Entrepreneurship in Library and Information Service', 2),
                    ('3', 'Harmattan', 'ETL313', 'Indexing and Abstracting', 2),
                    ('3', 'Harmattan', 'ETL315', 'Archives and Records Management', 2),
                    ('3', 'Harmattan', 'STE301', 'Curriculum Development ', 2),
                    ('3', 'Rain', 'ETL300', 'SIWES (Students’ Industrial Work Experiences)', 6),
                    ('3', 'Rain', 'ETL304', 'Indigenous Knowledge', 2),
                    ('3', 'Rain', 'ETL306', 'Database Design and Management', 2),
                    ('3', 'Rain', 'ETL314', 'Project Management and Evaluation', 2),
                    ('3', 'Rain', 'ETL316', 'Research Methodology in Library, Archives and Information Science', 2),
                    ('3', 'Rain', 'ETL330', 'Resources Sharing and Networking', 2),
                    ('3', 'Rain', 'ETL332', 'Information Resources in Subject Area', 2)
                ]

                insert_query = '''
                    INSERT INTO courses (part, semester, course_code, course_title, course_unit)
                    VALUES (%s, %s, %s, %s, %s)
                '''
                cursor.executemany(insert_query, courses)
                conn.commit()
                print("Database populated with course data.")
            else:
                print("Database already contains course data.")

    except (psycopg2.Error, ValueError) as e:
        print(f"Database initialization error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    print("Running database initialization script.")
    print("Ensure the POSTGRES_URL environment variable is set for this to work.")
    initialize_database()
