from flask import Flask, render_template, request, redirect, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from datetime import date
import os
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import io
from flask import send_file
from flask import jsonify
import os
DB_PATH = os.path.join(os.path.dirname(__file__), 'database.db')


app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), '../templates'),
    static_folder=os.path.join(os.path.dirname(__file__), '../static')
)

app.secret_key = "secret123"


# ---------------- DATABASE ----------------
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            password TEXT
        )
    ''')

    conn.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT,
            description TEXT,
            due_date TEXT,
            status TEXT,
            priority TEXT
        )
    ''')

    conn.commit()
    conn.close()

init_db()

# ---------------- HOME ----------------
@app.route('/')
def home():
    return redirect('/login')

# ---------------- REGISTER ----------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')

        conn = get_db()

        # 🔍 Check if email exists
        existing_user = conn.execute(
            "SELECT * FROM users WHERE email=?",
            (email,)
        ).fetchone()

        if existing_user:
            flash("⚠️ Email already registered!")
            conn.close()
            return redirect('/register')

        # ✅ Insert new user
        conn.execute(
            "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
            (name, email, generate_password_hash(password))
        )
        conn.commit()
        conn.close()

        flash("✅ Registered successfully!")
        return redirect('/login')

    return render_template('register.html')

# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        conn = get_db()

        user = conn.execute(
            "SELECT * FROM users WHERE email=?",
            (request.form['email'],)
        ).fetchone()

        conn.close()

        if user and check_password_hash(user['password'], request.form['password']):
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            flash("Login successful!")
            return redirect('/dashboard')

        flash("Invalid credentials")

    return render_template('login.html')

# ---------------- DASHBOARD ----------------
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')

    conn = get_db()
    user_id = session['user_id']

    tasks = conn.execute(
        "SELECT * FROM tasks WHERE user_id=?",
        (user_id,)
    ).fetchall()

    conn.close()

    total = len(tasks)
    completed = len([t for t in tasks if t['status'] == 'Completed'])
    pending = len([t for t in tasks if t['status'] == 'Pending'])

    percent = int((completed / total) * 100) if total > 0 else 0

    today = str(date.today())

    due_today = [
        t for t in tasks
        if t['due_date'] == today and t['status'] == "Pending"
    ]

    overdue_tasks = [
        t for t in tasks
        if t['due_date'] < today and t['status'] == "Pending"
    ]

    return render_template(
        'dashboard.html',
        tasks=tasks,
        total=total,
        completed=completed,
        pending=pending,
        percent=percent,
        due_today=due_today,
        overdue_tasks=overdue_tasks,
        user_name=session.get('user_name'),
        today=today
    )

@app.route('/suggest', methods=['GET', 'POST'])
def suggest():
    suggestions = []

    if request.method == 'POST':
        topic = request.form['topic']

        # Simple AI-like logic
        if "exam" in topic.lower():
            suggestions = [
                "📘 Revise important concepts",
                "📝 Practice previous question papers",
                "⏰ Create a study schedule",
                "📊 Analyze weak topics"
            ]
        elif "project" in topic.lower():
            suggestions = [
                "💻 Complete coding module",
                "📄 Prepare documentation",
                "🎯 Test all features",
                "📊 Create presentation slides"
            ]
        else:
            suggestions = [
                "📚 Study consistently",
                "🧠 Practice coding",
                "🎯 Set daily goals",
                "📝 Track your progress"
            ]

    return render_template('suggest.html', suggestions=suggestions)    

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect('/login')

    conn = get_db()

    user = conn.execute(
        "SELECT name, email FROM users WHERE id=?",
        (session['user_id'],)
    ).fetchone()

    tasks = conn.execute(
        "SELECT * FROM tasks WHERE user_id=?",
        (session['user_id'],)
    ).fetchall()

    conn.close()

    total = len(tasks)
    completed = len([t for t in tasks if t['status'] == 'Completed'])
    pending = len([t for t in tasks if t['status'] == 'Pending'])

    return render_template(
        'profile.html',
        user=user,
        total=total,
        completed=completed,
        pending=pending
    )    

@app.route('/update-priority/<int:id>', methods=['POST'])
def update_priority(id):
    data = request.get_json()
    priority = data.get('priority')

    conn = get_db()

    conn.execute(
        "UPDATE tasks SET priority=? WHERE id=?",
        (priority, id)
    )

    conn.commit()
    conn.close()

    return jsonify({"status": "success"})

@app.route('/forgot', methods=['GET', 'POST'])
def forgot():
    if request.method == 'POST':
        email = request.form['email']
        new_password = request.form['password']

        conn = get_db()

        user = conn.execute(
            "SELECT * FROM users WHERE email=?",
            (email,)
        ).fetchone()

        if user:
            conn.execute(
                "UPDATE users SET password=? WHERE email=?",
                (generate_password_hash(new_password), email)
            )
            conn.commit()
            conn.close()

            flash("Password updated successfully!")
            return redirect('/login')
        else:
            flash("Email not found!")

    return render_template('forgot.html')


# ---------------- TOGGLE STATUS ----------------
@app.route('/toggle/<int:id>')
def toggle(id):
    conn = get_db()

    task = conn.execute(
        "SELECT status FROM tasks WHERE id=?",
        (id,)
    ).fetchone()

    new_status = "Completed" if task['status'] == "Pending" else "Pending"

    conn.execute(
        "UPDATE tasks SET status=? WHERE id=?",
        (new_status, id)
    )

    conn.commit()
    conn.close()

    return redirect('/dashboard')

# ---------------- ADD TASK ----------------
@app.route('/add', methods=['POST'])
def add_task():
    conn = get_db()

    priority = request.form.get('priority', 'Medium')

    conn.execute(
        "INSERT INTO tasks (title, description, status, due_date, user_id, priority) VALUES (?, ?, ?, ?, ?, ?)",
        (
            request.form['title'],
            request.form['desc'],
            'Pending',
            request.form['due_date'],
            session['user_id'],
            priority
        )
    )

    conn.commit()
    conn.close()

    flash("Task added!")
    return redirect('/dashboard')

# ---------------- EDIT ----------------
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    conn = get_db()

    if request.method == 'POST':
        conn.execute(
            "UPDATE tasks SET title=?, description=?, due_date=? WHERE id=?",
            (
                request.form['title'],
                request.form['desc'],
                request.form['due_date'],
                id
            )
        )
        conn.commit()
        conn.close()
        return redirect('/dashboard')

    task = conn.execute(
        "SELECT * FROM tasks WHERE id=?",
        (id,)
    ).fetchone()

    conn.close()

    return render_template('edit.html', task=task)

# ---------------- DELETE ----------------
@app.route('/delete/<int:id>', methods=['POST'])
def delete_task(id):
    conn = get_db()

    conn.execute("DELETE FROM tasks WHERE id=?", (id,))
    
    conn.commit()
    conn.close()

    return redirect('/dashboard')

# ---------------- CALENDAR ----------------
@app.route('/calendar')
def calendar():
    if 'user_id' not in session:
        return redirect('/login')

    conn = get_db()

    tasks = conn.execute(
        "SELECT * FROM tasks WHERE user_id=?",
        (session['user_id'],)
    ).fetchall()

    conn.close()

    return render_template('calendar.html', tasks=tasks)


@app.route('/download-report')
def download_report():
    if 'user_id' not in session:
        return redirect('/login')

    conn = get_db()

    tasks = conn.execute(
        "SELECT * FROM tasks WHERE user_id=?",
        (session['user_id'],)
    ).fetchall()

    conn.close()

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()

    elements = []

    # Title
    elements.append(Paragraph("Student Task Report", styles['Title']))
    elements.append(Spacer(1, 10))

    # User
    elements.append(Paragraph(f"User: {session.get('user_name')}", styles['Normal']))
    elements.append(Spacer(1, 10))

    # Summary
    total = len(tasks)
    completed = len([t for t in tasks if t['status'] == 'Completed'])
    pending = len([t for t in tasks if t['status'] == 'Pending'])

    elements.append(Paragraph(f"Total Tasks: {total}", styles['Normal']))
    elements.append(Paragraph(f"Completed: {completed}", styles['Normal']))
    elements.append(Paragraph(f"Pending: {pending}", styles['Normal']))
    elements.append(Spacer(1, 20))

    # Task list
    for t in tasks:
        elements.append(Paragraph(
            f"{t['title']} - {t['status']} (Due: {t['due_date']})",
            styles['Normal']
        ))
        elements.append(Spacer(1, 5))

    doc.build(elements)

    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name="report.pdf", mimetype='application/pdf')


# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)
    