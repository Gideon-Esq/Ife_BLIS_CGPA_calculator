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

## Deployment Guide (Render)

This guide will walk you through deploying the application to **Render**, a cloud hosting service with a generous free tier that supports SQLite with a persistent disk.

### 1. Fork the Repository

-   First, **fork this repository** to your own GitHub account.

### 2. Create a New Web Service on Render

1.  Go to your [Render Dashboard](https://dashboard.render.com/) and click **"New + > Web Service"**.
2.  **Connect your GitHub account** and select the forked repository.
3.  Fill in the service details:
    *   **Name:** Give your application a unique name (e.g., `ife-blis-gpa-calculator`).
    *   **Region:** Choose a region close to you.
    *   **Branch:** Select your main branch (e.g., `main` or `master`).
    *   **Root Directory:** Leave this blank.
    *   **Runtime:** Select **Python 3**.
    *   **Build Command:** `pip install -r requirements.txt && python init_db.py`
    *   **Start Command:** `gunicorn app:app`

### 3. Add a Persistent Disk (Crucial for SQLite)

1.  Before creating the service, click on the **"Advanced Settings"** button.
2.  Scroll down and click **"+ Add Disk"**.
3.  Fill in the disk details:
    *   **Name:** `database`
    *   **Mount Path:** `/app/database`
    *   **Size (GB):** `1` (the smallest size is sufficient)
4.  Click **"Save"**.

### 4. Create the Web Service

-   Scroll down and click the **"Create Web Service"** button.
-   Render will now build and deploy your application. The first build may take a few minutes as it installs dependencies and initializes the database.

### 5. Access Your Deployed Application

-   Once the deployment is complete, Render will provide you with a public URL (e.g., `https-your-app-name.onrender.com`). You can access your GPA calculator at this URL.

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
