# College Event Management System

This project is a Flask-based college event management system with separate dashboards for students, organizers, and admins.

## Features

- User login and registration
- Role-based dashboards
- Event creation with venue conflict prevention
- Student event discovery and registration
- Organizer participant and activity management
- Admin approval workflow
- Venue management and conflict validation
- Activity timelines and announcements
- Basic reports

## Run locally

```bash
cd college-event-management
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open http://localhost:5000

The local development database is SQLite. The deployed Render configuration uses PostgreSQL so data survives deploys and restarts.

## Deploy to Render

1. Push this project to a GitHub repository.
2. In Render, choose **New -> Blueprint** and select the repository.
3. Render reads [render.yaml](render.yaml), creates the web service and PostgreSQL database, installs the dependencies, and runs `gunicorn app:app`.
4. Open the generated Render URL and sign in with the seeded admin account.

## Initial admin account

- Email: `admin@college.edu`
- Password: `admin123`

Create Student and Organizer accounts through the public registration page. Change the admin password before sharing the deployment.

## Default project flow

Login -> role-based dashboard -> event creation -> admin approval -> event registration -> schedule -> announcements -> reports
