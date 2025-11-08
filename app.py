import sqlite3
from flask import Flask, g, jsonify, render_template, request, session, redirect, url_for, flash
from contextlib import contextmanager
import os
import uuid
import json

app = Flask(__name__)
import os

# Set a secret key for session management. In a real app, use a more secure key.
app.config['SECRET_KEY'] = os.urandom(24)

# Use an absolute path for the database to ensure it's in the persistent disk area
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), 'database'))
DATABASE_PATH = os.path.join(DATA_DIR, 'database.db')

# Ensure the directory for the database exists
os.makedirs(DATA_DIR, exist_ok=True)

@contextmanager
def get_db():
    db = sqlite3.connect(DATABASE_PATH)
    db.row_factory = sqlite3.Row
    try:
        yield db
    finally:
        db.close()

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
            cursor = conn.cursor()
            cursor.execute('SELECT DISTINCT part, semester FROM courses ORDER BY part, semester')
            semester_parts = cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
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
            cursor = conn.cursor()
            # Get the standard courses
            cursor.execute('SELECT course_code, course_title, course_unit FROM courses WHERE part = ? AND semester = ?', (part, semester))
            courses = [dict(row) for row in cursor.fetchall()]

            # Check for saved grades in the session
            saved_grades = {}
            session_key = f"{part}-{semester}"
            if 'semesters_data' in session:
                for data in session['semesters_data']:
                    if data.get('session_key') == session_key:
                        for course in data.get('courses', []):
                            saved_grades[course['course_code']] = course['grade']

            # Add saved grades to the course data
            for course in courses:
                if course['course_code'] in saved_grades:
                    course['grade'] = saved_grades[course['course_code']]

            # Handle carry-over courses
            carry_overs = session.get('carry_over_courses', [])
            relevant_carry_overs = [co for co in carry_overs if co['semester'] == semester]

            course_codes = {c['course_code'] for c in courses}
            for co in relevant_carry_overs:
                if co['course_code'] not in course_codes:
                    course_data = {
                        "course_code": co['course_code'],
                        "course_title": co['course_title'],
                        "course_unit": co['course_unit'],
                        "is_carry_over": True,
                        "grade": saved_grades.get(co['course_code']) # Also check grade for carry-over
                    }
                    courses.append(course_data)
                    course_codes.add(co['course_code'])

            return jsonify(courses)
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

            if 'carry_over_courses' not in session:
                session['carry_over_courses'] = []

            for grade_info in grades:
                cursor.execute('SELECT * FROM courses WHERE course_code = ?', (grade_info['course_code'],))
                course_db = cursor.fetchone()
                if course_db:
                    new_semester_courses.append({**grade_info, 'course_unit': course_db['course_unit']})

                    if grade_info.get('grade') == 'F':
                        is_already_carry_over = any(c['course_code'] == grade_info['course_code'] for c in session['carry_over_courses'])
                        if not is_already_carry_over:
                            session['carry_over_courses'].append(dict(course_db))
                else:
                    return jsonify({"error": f"Course code not found: {grade_info['course_code']}"}), 400

        session_key = f"{part}-{semester_name}"
        session['semesters_data'] = [s for s in session.get('semesters_data', []) if s.get('session_key') != session_key]
        session['semesters_data'].append({"session_key": session_key, "part": part, "semester": semester_name, "courses": new_semester_courses})

        # Also remove a course from carry-over if the user passes it
        passed_carry_overs = [g['course_code'] for g in grades if g.get('grade') != 'F' and any(c['course_code'] == g['course_code'] for c in session.get('carry_over_courses', []))]
        if passed_carry_overs:
            session['carry_over_courses'] = [c for c in session['carry_over_courses'] if c['course_code'] not in passed_carry_overs]

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

        # Format the results for the results page
        display_data = {
            "cumulative_gpa": results['cumulative_gpa'],
            "semester_gpas": [{"part": s['part'], "semester": s['semester'], "gpa": results['semester_gpas'].get(s['session_key'], 0)} for s in semesters_data]
        }
        session['last_calculation_results'] = display_data

        # Clear the calculation data but keep the results for the next page
        session.pop('semesters_data', None)
        session.pop('carry_over_courses', None)
        session.modified = True

        return jsonify({"success": True, "redirect_url": url_for('results_page')})

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return jsonify({"error": "Failed to save calculation to the database."}), 500

@app.route('/blis-records-management')
def admin_panel():
    if not session.get('admin_authenticated'):
        return redirect(url_for('admin_login'))

    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM gpa_records ORDER BY timestamp DESC')
            records = cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return "Error connecting to the database.", 500

    return render_template('admin.html', records=records)

@app.route('/api/blis-records-management/records', methods=['GET'])
def get_admin_records():
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM gpa_records ORDER BY timestamp DESC')
            records = cursor.fetchall()
            # The `semester_data` may need special handling if it's stored as a JSON string
            return jsonify([dict(row) for row in records])
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return jsonify({"error": "Failed to fetch records from the database."}), 500

@app.route('/load_calculation/<record_id>')
def load_calculation(record_id):
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT semester_data FROM gpa_records WHERE record_id = ?', (record_id,))
            record = cursor.fetchone()

            if record and record['semester_data']:
                session.clear()
                session['semesters_data'] = json.loads(record['semester_data'])
                # Regenerate carry-overs from the loaded data
                session['carry_over_courses'] = []
                for semester_data in session['semesters_data']:
                    for course in semester_data.get('courses', []):
                        if course.get('grade') == 'F':
                            # Fetch full course details to store in carry_over
                            cursor.execute('SELECT * FROM courses WHERE course_code = ?', (course['course_code'],))
                            course_db = cursor.fetchone()
                            if course_db and not any(c['course_code'] == course_db['course_code'] for c in session['carry_over_courses']):
                                session['carry_over_courses'].append(dict(course_db))

                session.modified = True
                flash(f"Calculation {record_id[:8]}... loaded successfully.", "success")
            else:
                flash("Calculation not found.", "error")
    except (sqlite3.Error, json.JSONDecodeError) as e:
        print(f"Error loading calculation: {e}")
        flash("Failed to load calculation due to an error.", "error")

    return redirect(url_for('index'))

@app.route('/results')
def results_page():
    if 'last_calculation_results' not in session:
        flash("No results to display. Please calculate your GPA first.", "error")
        return redirect(url_for('index'))

    results = session.get('last_calculation_results')
    # Clear the results from the session so they aren't shown again on refresh
    session.pop('last_calculation_results', None)

    return render_template('results.html', results=results)

@app.route('/blis-records-management/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        pin = request.form.get('pin', '').strip()
        # In a real app, use a more secure way to store and check the PIN
        if pin == '162019':
            session['admin_authenticated'] = True
            return redirect(url_for('admin_panel'))
        else:
            flash("Invalid PIN.", "error")
            return redirect(url_for('admin_login'))
    return render_template('admin_login.html')

@app.route('/blis-records-management/logout')
def admin_logout():
    session.pop('admin_authenticated', None)
    flash("You have been logged out.", "success")
    return redirect(url_for('admin_login'))

if __name__ == '__main__':
    app.run(debug=True)
