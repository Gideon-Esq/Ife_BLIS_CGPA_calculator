import sqlite3
from flask import Flask, g, jsonify, render_template, request, session
from contextlib import contextmanager
import os
import uuid
import json

app = Flask(__name__)
# Set a secret key for session management. In a real app, use a more secure key.
app.config['SECRET_KEY'] = os.urandom(24)
DATABASE = 'database.db'

@contextmanager
def get_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    try:
        yield db
    finally:
        db.close()

@app.route('/')
def index():
    if 'semesters_data' not in session:
        session['semesters_data'] = []

    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT DISTINCT part, semester FROM courses ORDER BY part, semester')
            semester_parts = cursor.fetchall()
    except sqlite3.Error as e:
        # Log the error and render a simple error page or message
        print(f"Database error: {e}")
        return "Error connecting to the database.", 500

    return render_template('index.html', semester_parts=semester_parts, session_data=session['semesters_data'])

@app.route('/api/courses/<part>/<semester>')
def get_courses(part, semester):
    if not part.isdigit() or not semester.isalpha():
        return jsonify({"error": "Invalid part or semester format"}), 400

    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT course_code, course_title, course_unit FROM courses WHERE part = ? AND semester = ?', (part, semester))
            courses = cursor.fetchall()
            return jsonify([dict(row) for row in courses])
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return jsonify({"error": "Database query failed"}), 500

def calculate_gpa_cgpa(grades_data):
    grade_points = {'A': 5, 'B': 4, 'C': 3, 'D': 2, 'E': 1, 'F': 0}

    total_credit_points_cumulative = 0
    total_units_cumulative = 0

    semester_results = {}

    for semester, courses in grades_data.items():
        semester_tcp = 0
        semester_tnu = 0

        for course in courses:
            unit = course['course_unit']
            grade = course.get('grade')

            if grade in grade_points:
                points = grade_points[grade]
                semester_tcp += points * unit
                semester_tnu += unit

        semester_gpa = semester_tcp / semester_tnu if semester_tnu > 0 else 0
        semester_results[semester] = round(semester_gpa, 2)

        total_credit_points_cumulative += semester_tcp
        total_units_cumulative += semester_tnu

    cumulative_gpa = total_credit_points_cumulative / total_units_cumulative if total_units_cumulative > 0 else 0

    return {
        "semester_gpas": semester_results,
        "cumulative_gpa": round(cumulative_gpa, 2),
        "total_units_taken": total_units_cumulative,
        "total_credit_points": total_credit_points_cumulative
    }

@app.route('/api/add_semester', methods=['POST'])
def add_semester():
    data = request.json
    part = data.get('part')
    semester_name = data.get('semester')
    grades = data.get('grades', [])

    if not all([part, semester_name, isinstance(grades, list)]) or not grades:
        return jsonify({"error": "Invalid or missing data. Ensure part, semester, and a list of grades are provided."}), 400

    valid_grades = {'A', 'B', 'C', 'D', 'E', 'F'}
    for g in grades:
        if not isinstance(g, dict) or 'course_code' not in g or 'grade' not in g or g['grade'] not in valid_grades:
            return jsonify({"error": f"Invalid grade entry: {g}"}), 400

    try:
        with get_db() as conn:
            cursor = conn.cursor()
            new_semester_courses = []
            for grade_info in grades:
                cursor.execute('SELECT course_unit FROM courses WHERE course_code = ?', (grade_info['course_code'],))
                course_db = cursor.fetchone()
                if course_db:
                    new_semester_courses.append({**grade_info, 'course_unit': course_db['course_unit']})
                else:
                    return jsonify({"error": f"Course code not found: {grade_info['course_code']}"}), 400

        session_key = f"{part}-{semester_name}"
        session['semesters_data'] = [s for s in session.get('semesters_data', []) if s.get('session_key') != session_key]
        session['semesters_data'].append({"session_key": session_key, "part": part, "semester": semester_name, "courses": new_semester_courses})
        session.modified = True

        grades_for_calc = {s['session_key']: s['courses'] for s in session['semesters_data']}
        results = calculate_gpa_cgpa(grades_for_calc)

        display_data = [{"part": s['part'], "semester": s['semester'], "gpa": results['semester_gpas'].get(s['session_key'], 0)} for s in session['semesters_data']]

        return jsonify({
            "semester_gpa": results['semester_gpas'].get(session_key, 0),
            "cumulative_gpa": results['cumulative_gpa'],
            "session_summary": display_data
        })

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return jsonify({"error": "An error occurred while processing your request."}), 500

@app.route('/api/reset_session', methods=['POST'])
def reset_session():
    session.clear()
    return jsonify({"message": "Session reset successfully"})

@app.route('/api/save_calculation', methods=['POST'])
def save_calculation():
    semesters_data = session.get('semesters_data')
    if not semesters_data:
        return jsonify({"error": "No calculation data in session to save."}), 400

    grades_for_calc = {s['session_key']: s['courses'] for s in semesters_data}
    results = calculate_gpa_cgpa(grades_for_calc)

    try:
        with get_db() as conn:
            cursor = conn.cursor()
            record_id = str(uuid.uuid4())
            cursor.execute('''
                INSERT INTO gpa_records (record_id, semester_data, final_gpa, final_cgpa, total_units_taken, total_credit_points)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (record_id, json.dumps(semesters_data), results['cumulative_gpa'], results['cumulative_gpa'], results['total_units_taken'], results['total_credit_points']))
            conn.commit()

        session.clear()
        return jsonify({"message": "Calculation saved successfully", "record_id": record_id})

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return jsonify({"error": "Failed to save calculation to the database."}), 500

@app.route('/admin')
def admin_panel():
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM gpa_records ORDER BY timestamp DESC')
            records = cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return "Error connecting to the database.", 500

    return render_template('admin.html', records=records)

if __name__ == '__main__':
    app.run(debug=True)
