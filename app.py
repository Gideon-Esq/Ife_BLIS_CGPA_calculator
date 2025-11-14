import psycopg2
import psycopg2.extras
from flask import Flask, g, jsonify, render_template, request, session, redirect, url_for, flash
from contextlib import contextmanager
import os
import uuid
import json
from init_db import initialize_database

app = Flask(__name__)

# Set a secret key for session management. In a real app, use a more secure key.
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(24))

# Automatically initialize the database: create tables and populate if needed.
initialize_database()

@contextmanager
def get_db():
    """Provides a PostgreSQL database connection."""
    conn = None
    try:
        conn_string = os.environ.get('POSTGRES_URL')
        if not conn_string:
            raise ValueError("The POSTGRES_URL environment variable is not set.")
        conn = psycopg2.connect(conn_string)
        yield conn
    except (psycopg2.Error, ValueError) as e:
        print(f"Database connection error: {e}")
        # In a web context, you might want to return an error page or response
        # For this script, we'll re-raise to make it clear the connection failed.
        raise
    finally:
        if conn:
            conn.close()

def dict_from_row(row, cursor):
    """Converts a database row into a dictionary."""
    return {col[0]: value for col, value in zip(cursor.description, row)}

@app.route('/')
def index():
    initial_cgpa = 0
    initial_summary = []

    if 'semesters_data' in session and session['semesters_data']:
        grades_for_calc = {s['session_key']: s['courses'] for s in session['semesters_data']}
        results = calculate_gpa_cgpa(grades_for_calc)
        initial_cgpa = results['cumulative_gpa']
        initial_summary = [{"part": s['part'], "semester": s['semester'], "gpa": results['semester_gpas'].get(s['session_key'], 0)} for s in session['semesters_data']]
    else:
        session['semesters_data'] = []

    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                cursor.execute('SELECT DISTINCT part, semester FROM courses ORDER BY part, semester')
                semester_parts = cursor.fetchall()
    except (psycopg2.Error, ValueError):
        return "Error connecting to the database.", 500

    return render_template(
        'index.html',
        semester_parts=semester_parts,
        initial_cgpa=initial_cgpa,
        initial_summary=initial_summary
    )

@app.route('/api/courses/<part>/<semester>')
def get_courses(part, semester):
    if not part.isdigit() or not semester.isalpha():
        return jsonify({"error": "Invalid part or semester format"}), 400

    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                cursor.execute('SELECT course_code, course_title, course_unit FROM courses WHERE part = %s AND semester = %s', (part, semester))
                courses = [dict(row) for row in cursor.fetchall()]

            saved_grades = {}
            session_key = f"{part}-{semester}"
            if 'semesters_data' in session:
                for data in session['semesters_data']:
                    if data.get('session_key') == session_key:
                        for course in data.get('courses', []):
                            saved_grades[course['course_code']] = course['grade']

            for course in courses:
                if course['course_code'] in saved_grades:
                    course['grade'] = saved_grades[course['course_code']]

            carry_overs = session.get('carry_over_courses', [])
            # Bug Fix: Ensure carry-overs only appear in subsequent academic parts.
            relevant_carry_overs = [
                co for co in carry_overs
                if co['semester'] == semester and int(part) > int(co['part'])
            ]
            course_codes = {c['course_code'] for c in courses}
            for co in relevant_carry_overs:
                if co['course_code'] not in course_codes:
                    courses.append({
                        "course_code": co['course_code'], "course_title": co['course_title'],
                        "course_unit": co['course_unit'], "is_carry_over": True,
                        "grade": saved_grades.get(co['course_code'])
                    })
                    course_codes.add(co['course_code'])

            return jsonify(courses)
    except (psycopg2.Error, ValueError):
        return jsonify({"error": "Database query failed"}), 500

def calculate_gpa_cgpa(grades_data):
    grade_points = {'A': 5, 'B': 4, 'C': 3, 'D': 2, 'E': 1, 'F': 0}
    total_credit_points_cumulative, total_units_cumulative, total_courses_cumulative = 0, 0, 0
    semester_results = {}

    for semester, courses in grades_data.items():
        semester_tcp, semester_tnu = 0, 0
        total_courses_cumulative += len(courses)
        for course in courses:
            unit, grade = course['course_unit'], course.get('grade')
            if grade in grade_points:
                semester_tcp += grade_points[grade] * unit
                semester_tnu += unit

        semester_results[semester] = round(semester_tcp / semester_tnu if semester_tnu > 0 else 0, 2)
        total_credit_points_cumulative += semester_tcp
        total_units_cumulative += semester_tnu

    cumulative_gpa = total_credit_points_cumulative / total_units_cumulative if total_units_cumulative > 0 else 0
    return {
        "semester_gpas": semester_results, "cumulative_gpa": round(cumulative_gpa, 2),
        "total_units_taken": total_units_cumulative, "total_credit_points": total_credit_points_cumulative,
        "total_courses": total_courses_cumulative
    }

@app.route('/api/add_semester', methods=['POST'])
def add_semester():
    data = request.json
    part, semester_name, grades = data.get('part'), data.get('semester'), data.get('grades', [])

    if not all([part, semester_name, isinstance(grades, list)]) or not grades:
        return jsonify({"error": "Invalid or missing data."}), 400

    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                new_semester_courses = []
                if 'carry_over_courses' not in session: session['carry_over_courses'] = []

                for grade_info in grades:
                    cursor.execute('SELECT * FROM courses WHERE course_code = %s', (grade_info['course_code'],))
                    course_db = cursor.fetchone()
                    if course_db:
                        new_semester_courses.append({**grade_info, 'course_unit': course_db['course_unit']})
                        if grade_info.get('grade') == 'F' and not any(c['course_code'] == grade_info['course_code'] for c in session['carry_over_courses']):
                            session['carry_over_courses'].append(dict(course_db))
                    else:
                        return jsonify({"error": f"Course code not found: {grade_info['course_code']}"}), 400

        session_key = f"{part}-{semester_name}"
        session['semesters_data'] = [s for s in session.get('semesters_data', []) if s.get('session_key') != session_key]
        session['semesters_data'].append({"session_key": session_key, "part": part, "semester": semester_name, "courses": new_semester_courses})

        passed_co = [g['course_code'] for g in grades if g.get('grade') != 'F' and any(c['course_code'] == g['course_code'] for c in session.get('carry_over_courses', []))]
        if passed_co: session['carry_over_courses'] = [c for c in session['carry_over_courses'] if c['course_code'] not in passed_co]
        session.modified = True

        results = calculate_gpa_cgpa({s['session_key']: s['courses'] for s in session['semesters_data']})
        display_data = [{"part": s['part'], "semester": s['semester'], "gpa": results['semester_gpas'].get(s['session_key'], 0)} for s in session['semesters_data']]

        return jsonify({
            "semester_gpa": results['semester_gpas'].get(session_key, 0),
            "cumulative_gpa": results['cumulative_gpa'], "session_summary": display_data
        })
    except (psycopg2.Error, ValueError) as e:
        return jsonify({"error": f"An error occurred: {e}"}), 500

@app.route('/api/reset_session', methods=['POST'])
def reset_session():
    session.clear()
    return jsonify({"message": "Session reset successfully"})

@app.route('/api/save_calculation', methods=['POST'])
def save_calculation():
    if not session.get('semesters_data'):
        return jsonify({"error": "No calculation data to save."}), 400

    results = calculate_gpa_cgpa({s['session_key']: s['courses'] for s in session['semesters_data']})
    try:
        with get_db() as conn:
            with conn.cursor() as cursor:
                record_id = str(uuid.uuid4())
                cursor.execute(
                    'INSERT INTO gpa_records (record_id, semester_data, final_gpa, final_cgpa, total_units_taken, total_credit_points) VALUES (%s, %s, %s, %s, %s, %s)',
                    (record_id, json.dumps(session['semesters_data']), results['cumulative_gpa'], results['cumulative_gpa'], results['total_units_taken'], results['total_credit_points'])
                )
                conn.commit()

        session['last_calculation_results'] = {
            "cumulative_gpa": results['cumulative_gpa'],
            "semester_gpas": [{"part": s['part'], "semester": s['semester'], "gpa": results['semester_gpas'].get(s['session_key'], 0)} for s in session['semesters_data']],
            "total_units_taken": results['total_units_taken'],
            "total_credit_points": results['total_credit_points'],
            "total_courses": results['total_courses']
        }
        session.pop('semesters_data', None)
        session.pop('carry_over_courses', None)
        session.modified = True

        return jsonify({"success": True, "redirect_url": url_for('results_page')})
    except (psycopg2.Error, ValueError) as e:
        return jsonify({"error": f"Failed to save calculation: {e}"}), 500

@app.route('/blis-records-management')
def admin_panel():
    if not session.get('admin_authenticated'): return redirect(url_for('admin_login'))
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                cursor.execute('SELECT *, to_char(timestamp, \'YYYY-MM-DD HH24:MI:SS\') as formatted_timestamp FROM gpa_records ORDER BY timestamp DESC')
                records = cursor.fetchall()
    except (psycopg2.Error, ValueError):
        return "Error connecting to the database.", 500
    return render_template('admin.html', records=records)

@app.route('/api/blis-records-management/records', methods=['GET'])
def get_admin_records():
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                cursor.execute('SELECT *, to_char(timestamp, \'YYYY-MM-DD HH24:MI:SS\') as formatted_timestamp FROM gpa_records ORDER BY timestamp DESC')
                records = [dict(row) for row in cursor.fetchall()]
                return jsonify(records)
    except (psycopg2.Error, ValueError) as e:
        return jsonify({"error": f"Failed to fetch records: {e}"}), 500

@app.route('/load_calculation/<record_id>')
def load_calculation(record_id):
    try:
        with get_db() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                cursor.execute('SELECT semester_data FROM gpa_records WHERE record_id = %s', (record_id,))
                record = cursor.fetchone()

                if record and record['semester_data']:
                    session.clear()
                    session['semesters_data'] = record['semester_data']
                    session['carry_over_courses'] = []
                    for s_data in session['semesters_data']:
                        for course in s_data.get('courses', []):
                            if course.get('grade') == 'F':
                                cursor.execute('SELECT * FROM courses WHERE course_code = %s', (course['course_code'],))
                                course_db = cursor.fetchone()
                                if course_db and not any(c['course_code'] == course_db['course_code'] for c in session['carry_over_courses']):
                                    session['carry_over_courses'].append(dict(course_db))
                    session.modified = True
                    flash(f"Calculation {record_id[:8]}... loaded successfully.", "success")
                else:
                    flash("Calculation not found.", "error")
    except (psycopg2.Error, ValueError) as e:
        flash(f"Failed to load calculation: {e}", "error")
    return redirect(url_for('index'))

@app.route('/results')
def results_page():
    if 'last_calculation_results' not in session:
        flash("No results to display. Please calculate your GPA first.", "info")
        return redirect(url_for('index'))

    results = session.pop('last_calculation_results', None)

    if not results:
        flash("Could not retrieve results. Please try again.", "error")
        return redirect(url_for('index'))

    return render_template('results.html', results=results)

@app.route('/blis-records-management/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if request.form.get('pin', '').strip() == '162019':
            session['admin_authenticated'] = True
            return redirect(url_for('admin_panel'))
        else:
            flash("Invalid PIN.", "error")
    return render_template('admin_login.html')

@app.route('/blis-records-management/logout')
def admin_logout():
    session.pop('admin_authenticated', None)
    flash("You have been logged out.", "success")
    return redirect(url_for('admin_login'))

if __name__ == '__main__':
    # For local development, ensure POSTGRES_URL is set in your environment
    app.run(debug=True)
