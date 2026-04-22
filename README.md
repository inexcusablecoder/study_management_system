# StudyFlow — Study Management System

A modern, Python-based web application to help students efficiently manage their academic tasks, schedules, study sessions, and performance.

## Features

| Feature | Description |
|---|---|
| 🔐 **Authentication** | Register / Login / Logout with hashed passwords |
| ✅ **Task Tracker** | Add tasks with subject, priority, due date, status |
| 📖 **Subject Manager** | Organise work by subject with colour-coding |
| ⏱️ **Study Sessions** | Log study time with productivity ratings |
| 📊 **Analytics** | Charts: 30-day trend, subject hours, task completion, productivity |
| 🎯 **Goal Setting** | Set academic goals and track progress % |

## Tech Stack

- **Backend**: Python 3.11+, Flask, Flask-Login, Flask-SQLAlchemy
- **Database**: SQLite (`study_system.db`) — compatible with DB Browser for SQLite
- **Frontend**: HTML5, Vanilla CSS (dark theme), JavaScript
- **Charts**: Chart.js

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the app
python app.py

# 3. Open in browser
#    http://127.0.0.1:5000
```

## First Time Setup

1. Open `http://127.0.0.1:5000` — you'll be redirected to the **Login** page
2. Click **"Create one free →"** to register a new account
3. After registering you'll land on the **Dashboard** with a guided onboarding
4. Follow the steps: Add Subjects → Add Tasks → Log Sessions → Set Goals → View Analytics

## Database

The SQLite database file `study_system.db` can be opened in **DB Browser for SQLite** to inspect all tables directly:
- `users` — registered accounts
- `subjects` — subjects per user
- `tasks` — task tracker
- `study_sessions` — logged study time
- `goals` — academic goals
