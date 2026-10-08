from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from pathlib import Path
from datetime import datetime, date, timedelta
import os

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "lifeos.db"

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "life-os-development-secret-change-me")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    db = get_db()
    db.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        priority TEXT NOT NULL DEFAULT 'medium',
        due_date TEXT,
        completed INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        category TEXT NOT NULL DEFAULT 'Other',
        amount REAL NOT NULL,
        spent_on TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS habits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        streak INTEGER NOT NULL DEFAULT 0,
        last_done TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        event_date TEXT NOT NULL,
        event_time TEXT,
        kind TEXT NOT NULL DEFAULT 'personal',
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)
    db.commit()
    db.close()

def seed_demo(user_id):
    db = get_db()
    if db.execute("SELECT COUNT(*) FROM tasks WHERE user_id=?", (user_id,)).fetchone()[0] == 0:
        now = datetime.now().isoformat(timespec="seconds")
        tasks = [
            ("Finish Python practice", "high", date.today().isoformat(), 0),
            ("Apply to 3 developer jobs", "high", date.today().isoformat(), 0),
            ("Update portfolio projects", "medium", date.today().isoformat(), 1),
            ("Read 20 pages", "low", (date.today()+timedelta(days=1)).isoformat(), 0),
        ]
        db.executemany("INSERT INTO tasks(user_id,title,priority,due_date,completed,created_at) VALUES(?,?,?,?,?,?)",
                       [(user_id,*t,now) for t in tasks])
        expenses = [
            ("Lunch", "Food", 180),
            ("Bus / Metro", "Travel", 120),
            ("Internet", "Bills", 799),
            ("Shopping", "Shopping", 1250),
        ]
        db.executemany("INSERT INTO expenses(user_id,title,category,amount,spent_on,created_at) VALUES(?,?,?,?,?,?)",
                       [(user_id,t,c,a,date.today().isoformat(),now) for t,c,a in expenses])
        db.executemany("INSERT INTO habits(user_id,name,streak,last_done) VALUES(?,?,?,?)",
                       [(user_id,"Python practice",7,date.today().isoformat()),
                        (user_id,"Exercise",4,date.today().isoformat()),
                        (user_id,"Read",12,(date.today()-timedelta(days=1)).isoformat())])
        db.executemany("INSERT INTO events(user_id,title,event_date,event_time,kind) VALUES(?,?,?,?,?)",
                       [(user_id,"Portfolio review",date.today().isoformat(),"18:30","work"),
                        (user_id,"Interview preparation",(date.today()+timedelta(days=2)).isoformat(),"10:00","career")])
        db.execute("INSERT INTO notes(user_id,title,content,created_at,updated_at) VALUES(?,?,?,?,?)",
                   (user_id,"Welcome to Life OS","One calm place for your tasks, money, habits, notes and plans.",now,now))
        db.commit()
    db.close()

def current_user():
    return session.get("user_id")

@app.route("/")
def index():
    if not current_user():
        return redirect(url_for("login"))
    return render_template("index.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        data = request.form
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email=?", (data.get("email","").strip().lower(),)).fetchone()
        db.close()
        if user and check_password_hash(user["password_hash"], data.get("password","")):
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            seed_demo(user["id"])
            return redirect(url_for("index"))
        return render_template("auth.html", mode="login", error="Invalid email or password.")
    return render_template("auth.html", mode="login", error=None)

@app.route("/signup", methods=["GET","POST"])
def signup():
    if request.method == "POST":
        name = request.form.get("name","").strip()
        email = request.form.get("email","").strip().lower()
        password = request.form.get("password","")
        if len(name) < 2 or "@" not in email or len(password) < 6:
            return render_template("auth.html", mode="signup", error="Use a valid name, email and 6+ character password.")
        db = get_db()
        try:
            cur = db.execute("INSERT INTO users(name,email,password_hash,created_at) VALUES(?,?,?,?)",
                             (name,email,generate_password_hash(password),datetime.now().isoformat(timespec="seconds")))
            db.commit()
            user_id = cur.lastrowid
        except sqlite3.IntegrityError:
            db.close()
            return render_template("auth.html", mode="signup", error="An account with that email already exists.")
        db.close()
        session["user_id"] = user_id
        session["user_name"] = name
        seed_demo(user_id)
        return redirect(url_for("index"))
    return render_template("auth.html", mode="signup", error=None)

@app.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.get("/api/dashboard")
def dashboard():
    uid = current_user()
    if not uid:
        return jsonify({"error":"unauthorized"}),401
    db = get_db()
    tasks = [dict(r) for r in db.execute("SELECT * FROM tasks WHERE user_id=? ORDER BY completed, due_date, id DESC", (uid,))]
    expenses = [dict(r) for r in db.execute("SELECT * FROM expenses WHERE user_id=? ORDER BY spent_on DESC, id DESC LIMIT 12", (uid,))]
    notes = [dict(r) for r in db.execute("SELECT * FROM notes WHERE user_id=? ORDER BY updated_at DESC LIMIT 8", (uid,))]
    habits = [dict(r) for r in db.execute("SELECT * FROM habits WHERE user_id=? ORDER BY id DESC", (uid,))]
    events = [dict(r) for r in db.execute("SELECT * FROM events WHERE user_id=? ORDER BY event_date,event_time LIMIT 8", (uid,))]
    total = db.execute("SELECT COALESCE(SUM(amount),0) FROM expenses WHERE user_id=? AND substr(spent_on,1,7)=?", (uid,date.today().strftime("%Y-%m"))).fetchone()[0]
    completed = db.execute("SELECT COUNT(*) FROM tasks WHERE user_id=? AND completed=1", (uid,)).fetchone()[0]
    pending = db.execute("SELECT COUNT(*) FROM tasks WHERE user_id=? AND completed=0", (uid,)).fetchone()[0]
    db.close()
    return jsonify({
        "user":{"name":session.get("user_name","")},
        "tasks":tasks,"expenses":expenses,"notes":notes,"habits":habits,"events":events,
        "stats":{"spent":round(total,2),"completed":completed,"pending":pending}
    })

@app.post("/api/tasks")
def add_task():
    uid=current_user()
    if not uid:return jsonify({"error":"unauthorized"}),401
    d=request.json or {}
    title=(d.get("title") or "").strip()
    if not title:return jsonify({"error":"Task title required"}),400
    db=get_db()
    cur=db.execute("INSERT INTO tasks(user_id,title,priority,due_date,created_at) VALUES(?,?,?,?,?)",
                   (uid,title,d.get("priority","medium"),d.get("due_date") or None,datetime.now().isoformat(timespec="seconds")))
    db.commit()
    row=dict(db.execute("SELECT * FROM tasks WHERE id=?",(cur.lastrowid,)).fetchone())
    db.close()
    return jsonify(row),201

@app.patch("/api/tasks/<int:task_id>")
def update_task(task_id):
    uid=current_user()
    if not uid:return jsonify({"error":"unauthorized"}),401
    d=request.json or {}
    db=get_db()
    db.execute("UPDATE tasks SET completed=? WHERE id=? AND user_id=?",(1 if d.get("completed") else 0,task_id,uid))
    db.commit(); db.close()
    return jsonify({"ok":True})

@app.delete("/api/tasks/<int:task_id>")
def delete_task(task_id):
    uid=current_user()
    if not uid:return jsonify({"error":"unauthorized"}),401
    db=get_db(); db.execute("DELETE FROM tasks WHERE id=? AND user_id=?",(task_id,uid)); db.commit(); db.close()
    return jsonify({"ok":True})

@app.post("/api/expenses")
def add_expense():
    uid=current_user()
    if not uid:return jsonify({"error":"unauthorized"}),401
    d=request.json or {}
    try: amount=float(d.get("amount",0))
    except: amount=0
    if not d.get("title") or amount<=0:return jsonify({"error":"Valid expense required"}),400
    db=get_db()
    cur=db.execute("INSERT INTO expenses(user_id,title,category,amount,spent_on,created_at) VALUES(?,?,?,?,?,?)",
                   (uid,d["title"],d.get("category","Other"),amount,d.get("spent_on") or date.today().isoformat(),datetime.now().isoformat(timespec="seconds")))
    db.commit(); row=dict(db.execute("SELECT * FROM expenses WHERE id=?",(cur.lastrowid,)).fetchone()); db.close()
    return jsonify(row),201

@app.delete("/api/expenses/<int:item_id>")
def delete_expense(item_id):
    uid=current_user()
    if not uid:return jsonify({"error":"unauthorized"}),401
    db=get_db(); db.execute("DELETE FROM expenses WHERE id=? AND user_id=?",(item_id,uid)); db.commit(); db.close()
    return jsonify({"ok":True})

@app.post("/api/notes")
def add_note():
    uid=current_user()
    if not uid:return jsonify({"error":"unauthorized"}),401
    d=request.json or {}; title=(d.get("title") or "").strip(); content=(d.get("content") or "").strip()
    if not title:return jsonify({"error":"Note title required"}),400
    now=datetime.now().isoformat(timespec="seconds")
    db=get_db(); cur=db.execute("INSERT INTO notes(user_id,title,content,created_at,updated_at) VALUES(?,?,?,?,?)",(uid,title,content,now,now)); db.commit()
    row=dict(db.execute("SELECT * FROM notes WHERE id=?",(cur.lastrowid,)).fetchone()); db.close()
    return jsonify(row),201

@app.post("/api/habits/<int:habit_id>/done")
def habit_done(habit_id):
    uid=current_user()
    if not uid:return jsonify({"error":"unauthorized"}),401
    db=get_db()
    row=db.execute("SELECT * FROM habits WHERE id=? AND user_id=?",(habit_id,uid)).fetchone()
    if not row:return jsonify({"error":"Not found"}),404
    today=date.today().isoformat()
    if row["last_done"] != today:
        streak=row["streak"]+1
        db.execute("UPDATE habits SET streak=?,last_done=? WHERE id=? AND user_id=?",(streak,today,habit_id,uid)); db.commit()
    db.close()
    return jsonify({"ok":True})

@app.post("/api/ai")
def ai():
    uid=current_user()
    if not uid:return jsonify({"error":"unauthorized"}),401
    prompt=(request.json or {}).get("prompt","").lower()
    db=get_db()
    pending=db.execute("SELECT COUNT(*) FROM tasks WHERE user_id=? AND completed=0",(uid,)).fetchone()[0]
    spent=db.execute("SELECT COALESCE(SUM(amount),0) FROM expenses WHERE user_id=? AND substr(spent_on,1,7)=?",(uid,date.today().strftime("%Y-%m"))).fetchone()[0]
    high=db.execute("SELECT title FROM tasks WHERE user_id=? AND completed=0 AND priority='high' ORDER BY id DESC LIMIT 3",(uid,)).fetchall()
    db.close()
    if any(k in prompt for k in ["money","expense","spend","budget"]):
        answer=f"You've logged ₹{spent:,.0f} this month. Review your largest categories and set a weekly spending limit before adding more purchases."
    elif any(k in prompt for k in ["task","today","focus","plan"]):
        names=", ".join(r["title"] for r in high) or "your next small task"
        answer=f"You have {pending} pending tasks. Start with: {names}. Finish one high-impact item before switching context."
    elif any(k in prompt for k in ["career","job","interview"]):
        answer="For a job-focused day, spend 45 minutes on DSA/Python, 45 minutes on one portfolio feature, and 30 minutes applying to targeted roles. Keep a short log of what you shipped."
    else:
        answer="Life OS sees your tasks, spending and habits. Ask me about today's priorities, your money, career planning, or how to organize the week."
    return jsonify({"answer":answer})

@app.route("/health")
def health():
    return jsonify({"status":"ok","app":"Life OS"})

init_db()

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
