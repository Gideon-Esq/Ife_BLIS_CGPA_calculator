import sqlite3
from flask import Flask, jsonify
import os

app = Flask(__name__)

# Note: Vercel provides a writable /tmp directory.
DB_PATH = '/tmp/database.db'

def init_db_logic():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create courses table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            part TEXT NOT NULL,
            semester TEXT NOT NULL,
            course_code TEXT NOT NULL UNIQUE,
            course_title TEXT NOT NULL,
            course_unit INTEGER NOT NULL
        )
    ''')

    # Create gpa_records table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gpa_records (
            record_id TEXT PRIMARY KEY,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            semester_data TEXT,
            final_gpa REAL,
            final_cgpa REAL,
            total_units_taken INTEGER,
            total_credit_points INTEGER
        )
    ''')

    # Populate courses table
    courses = [
        # Part 1 - Harmattan Semester
        ('1', 'Harmattan', 'EDU101', 'Introduction to Teaching Profession', 2),
        ('1', 'Harmattan', 'ETL101', 'Introduction to Information Work', 2),
        ('1', 'Harmattan', 'ETL103', 'Introduction to Information Science', 2),
        ('1', 'Harmattan', 'PHL101', 'Introduction to Philosophy I', 3),
        ('1', 'Harmattan', 'SSC101', 'Man and His Social Environment', 3),
        ('1', 'Harmattan', 'YOR101', 'Introduction to the Yoruba People and the Yoruba Language', 3),

        # Part 1 - Rain Semester
        ('1', 'Rain', 'EDU102', 'Principles and Practice of Education', 2),
        ('1', 'Rain', 'ETL102', 'Introduction to ICT in Library and Information Services', 2),
        ('1', 'Rain', 'ETL104', 'Information Resources and Services', 2),
        ('1', 'Rain', 'ETL106', 'Information Literacy', 2),
        ('1', 'Rain', 'ETL108', 'Libraries and Societies', 2),
        ('1', 'Rain', 'ETL110', 'Introduction to Information Management', 2),
        ('1', 'Rain', 'PHL104', 'Introduction to Philosophy II', 3),
        ('1', 'Rain', 'SSC102', 'Elements of Economic Theory and Principles', 3),
        ('1', 'Rain', 'YOR114', 'Introduction to Yoruba Culture', 3),

        # Part 2 - Harmattan Semester
        ('2', 'Harmattan', 'ALL201', 'Literacy Education for Adults', 2),
        ('2', 'Harmattan', 'CSC221', 'Computer Appreciation', 2),
        ('2', 'Harmattan', 'EFC201', 'Historical Foundations of Education', 2),
        ('2', 'Harmattan', 'ETL201', 'Principles and Theories of Library and Information Management', 2),
        ('2', 'Harmattan', 'ETL203', 'Organization of Knowledge I (Classification)', 2),
        ('2', 'Harmattan', 'ETL205', 'Multimedia Application in Libraries and Information Centers', 2),
        ('2', 'Harmattan', 'ETL207', 'Introduction to Reference and Information Services', 2),
        ('2', 'Harmattan', 'ETL209', 'Information Retrieval 1 (Cataloguing)', 2),

        # Part 2 - Rain Semester
        ('2', 'Rain', 'ASE202', 'Curriculum and Instruction', 2),
        ('2', 'Rain', 'ETL202', 'Introduction to Educational Technology and Communications', 2),
        ('2', 'Rain', 'ETL204', 'Preservation and Security of Library and Information Resources', 2),
        ('2', 'Rain', 'ETL206', 'Library and Information Services to People with Special Needs', 2),
        ('2', 'Rain', 'ETL208', 'Learning and Communication Skills', 2),
        ('2', 'Rain', 'ETL212', 'Literature and Library Services for Young People', 2),
        ('2', 'Rain', 'ETL214', 'Management of Serials and Government Publications', 2),
        ('2', 'Rain', 'ETL216', 'Introduction to Information Systems', 2),

        # Part 3 - Harmattan Semester
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


        # Part 3 - Rain Semester
        ('3', 'Rain', 'ETL300', 'SIWES (Students’ Industrial Work Experiences)', 6),
        ('3', 'Rain', 'ETL304', 'Indigenous Knowledge', 2),
        ('3', 'Rain', 'ETL306', 'Database Design and Management', 2),
        ('3', 'Rain', 'ETL314', 'Project Management and Evaluation', 2),
        ('3', 'Rain', 'ETL316', 'Research Methodology in Library, Archives and Information Science', 2),
        ('3', 'Rain', 'ETL330', 'Resources Sharing and Networking', 2),
        ('3', 'Rain', 'ETL332', 'Information Resources in Subject Area', 2)
    ]

    cursor.executemany('''
        INSERT OR IGNORE INTO courses (part, semester, course_code, course_title, course_unit)
        VALUES (?, ?, ?, ?, ?)
    ''', courses)

    conn.commit()
    conn.close()

# The Vercel entrypoint is this 'app' object.
# The route is defined in vercel.json. Any request to /init-db will be routed here.
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def handle_init_db(path):
    try:
        init_db_logic()
        return jsonify(message="Database initialized successfully.")
    except Exception as e:
        print(f"Error during database initialization: {e}")
        return jsonify(error=str(e)), 500
