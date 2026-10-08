# LIFE OS — Personal Command Center

A portfolio-ready full-stack personal productivity dashboard inspired by the references supplied for this project: minimal editorial typography, large whitespace, monochrome surfaces, oversized type, strong card layouts and a high-contrast footer.

## Stack
- Python 3.11+
- Flask
- SQLite
- HTML5
- CSS3
- Vanilla JavaScript
- Werkzeug password hashing

## Features
- Sign up / sign in / logout
- Personal SQLite database
- Dashboard overview
- Task creation + completion
- Expense tracking
- Habit streaks
- Notes
- Upcoming events
- AI-style personal assistant endpoint (rule-based, no paid API required)
- Responsive mobile navigation
- Portfolio-style editorial UI
- REST-style JSON endpoints

## Run in VS Code — Windows

Open the project folder in VS Code.

```cmd
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open:

http://127.0.0.1:5000

## First use
Create an account. A fresh account receives demo data that you can use as a starting point.

## Production notes
SQLite is excellent for local development and portfolio demos. For production hosting, use PostgreSQL or another managed database because many serverless hosts have ephemeral filesystems.

Set a strong secret:

```cmd
set SECRET_KEY=replace-with-a-long-random-secret
```

## Suggested portfolio description

**Life OS — Personal Productivity & Life Management Platform**
Built a full-stack personal command center using Python, Flask, SQLite, REST APIs, responsive HTML/CSS/JavaScript, authentication and an AI-style planning assistant. Implemented task management, expense tracking, habit streaks, notes, events and a responsive editorial dashboard.
