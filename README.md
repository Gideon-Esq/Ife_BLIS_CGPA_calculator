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

## Deployment Guide (Railway)

This guide will walk you through deploying the application to **Railway**, a modern cloud hosting platform with a free tier that supports persistent storage for our SQLite database.

### 1. Fork the Repository

-   First, **fork this repository** to your own GitHub account.

### 2. Create a New Project on Railway

1.  Go to your [Railway Dashboard](https://railway.app/dashboard) and click **"New Project"**.
2.  Select **"Deploy from GitHub repo"**.
3.  **Connect your GitHub account** and select the forked repository. Railway will automatically detect the project and start the initial deployment.

### 3. Add a Persistent Volume (Crucial for SQLite)

The initial deployment might fail or run into errors because the database needs a permanent place to live. We will now add a persistent volume.

1.  Once the project is created in Railway, click on the **service** that was just created (it will have the name of your repository).
2.  Go to the **"Volumes"** tab.
3.  Click **"+ New Volume"**.
4.  Fill in the volume details:
    *   **Mount Path:** `/app`
    *   **Size (MB):** `512` (the smallest size is plenty for the database)
5.  Click **"Create"**. This will automatically trigger a new deployment.

### 4. Configure the Start Command and Database Initialization

Railway uses the `Procfile` to start the app, but we need to ensure the database is initialized during the build.

1.  In your service, go to the **"Settings"** tab.
2.  Scroll down to the **"Deploy"** section.
3.  In the **"Build Command"** field, enter the following:
    ```
    pip install -r requirements.txt && python init_db.py
    ```
4.  The **"Start Command"** should be automatically detected from the `Procfile` (`gunicorn app:app`). If not, you can enter it here.
5.  Railway saves automatically, and these new settings will be applied on the next deploy.

### 5. Access Your Deployed Application

1.  After the deployment finishes successfully, go to the **"Settings"** tab for your service.
2.  In the **"Domains"** section, you will find a public URL ending in `.up.railway.app`.
3.  Click this URL to access your live GPA calculator.

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
