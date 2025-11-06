# Ife BLIS GPA Calculator

A simple, user-friendly web application for Obafemi Awolowo University (OAU) BLIS students to calculate their semester GPA and cumulative CGPA. The application is designed to be lightweight and fully functional in a Termux environment on Android.

## Features

-   **Real-time GPA/CGPA Calculation:** See your GPA and CGPA update as you add semesters.
-   **Multi-Semester Support:** Add multiple semesters to a single calculation session.
-   **Session Management:** Your calculation is preserved in a session until you save or reset.
-   **Persistent Records:** Save your completed calculations and view them later.
-   **Admin Panel:** A simple panel to view all saved calculation records, each with a unique ID.

## Technology Stack

-   **Backend:** Python 3 (Flask)
-   **Database:** SQLite3
-   **Frontend:** Vanilla HTML, CSS, and JavaScript

---

## Termux Setup and Usage Guide

This guide will walk you through setting up and running the application on your Android device using Termux.

### 1. Prerequisites

-   Install the [Termux](https://f-droid.org/en/packages/com.termux/) app on your Android device from F-Droid.

### 2. Installation

Open Termux and run the following commands one by one:

```bash
# Update package lists
pkg update && pkg upgrade

# Install Python
pkg install python

# Install pip (if not already installed)
pkg install python-pip

# Install Git to clone the repository
pkg install git
```

### 3. Clone the Repository

Clone this repository into your Termux home directory:

```bash
git clone <repository_url>  # Replace <repository_url> with the actual URL
cd Ife-BLIS-GPA-Calculator  # Navigate into the project directory
```

### 4. Install Dependencies

Install the only required Python package, Flask:

```bash
pip install Flask
```

### 5. Initialize the Database

Before running the application for the first time, you need to create and populate the database with the required course data:

```bash
python init_db.py
```

This will create a `database.db` file in the project directory.

### 6. Run the Application

Now you can start the Flask web server:

```bash
python app.py
```

You will see output indicating that the server is running, usually on `http://127.0.0.1:5000/`.

### 7. Access the Application

-   Open a web browser on your Android device (e.g., Chrome, Firefox).
-   Navigate to `http://127.0.0.1:5000` or `http://localhost:5000`.
-   You should now see the GPA Calculator interface.

---

## How to Use the Calculator

1.  **Select a Semester:** Use the dropdowns to select a "Part" and "Semester". The courses for that semester will be loaded automatically.
2.  **Enter Grades:** For each course, select a grade from the dropdown (A, B, C, D, E, or F).
3.  **Add to Calculation:** Click the **"Add Semester to Calculation"** button. The Semester GPA and your overall Cumulative GPA will be displayed. The semester will also appear in the "Calculation Session Summary".
4.  **Add More Semesters:** Repeat steps 1-3 for any other semesters you wish to include. The CGPA will update with each addition.
5.  **Finalize and Save:** Once you have added all desired semesters, click **"Finalize & Save Calculation"**. Your result will be saved to the database with a unique ID, which will be displayed briefly.
6.  **Reset:** To start a new calculation from scratch at any time, click **"Start New Calculation (Reset)"**.

## Admin Panel

The admin panel is accessible via a private, non-disclosed URL for security purposes.

---

## Project Structure

```
.
├── app.py              # Main Flask application file (backend logic, routes)
├── init_db.py          # Script to initialize the SQLite database
├── database.db         # The SQLite database file (created by init_db.py)
├── static/
│   ├── script.js       # Frontend JavaScript for interactivity
│   └── style.css       # CSS for styling
├── templates/
│   ├── index.html      # Main calculator page template
│   └── admin.html      # Admin panel template
│   └── admin_login.html # Admin login page template
└── README.md           # This file
```
