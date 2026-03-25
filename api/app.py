from flask import Flask, render_template, request, redirect, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from datetime import date
import os

# ✅ Correct Flask app initialization (for api folder)
app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), '../templates'),
    static_folder=os.path.join(os.path.dirname(__file__), '../static')
)

app.secret_key = "secret123"


# ---------------- DATABASE ----------------
def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()

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
            title TEXT,
            description TEXT,
            status TEXT DEFAULT 'Pending',
            due_date TEXT,
            user_id INTEGER
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
        conn = get_db()

        try:
            conn.execute(
                "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                (
                    request.form['name'],
                    request.form['email'],
                    generate_password_hash(request.form['password'])
                )
            )
            conn.commit()
            flash("Registered successfully!")
            return redirect('/login')

        except sqlite3.IntegrityError:
            flash("Email already exists!")

        finally:
            conn.close()

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

    search = request.args.get("search")
    filter_status = request.args.get("filter")
    sort = request.args.get("sort")

    query = "SELECT * FROM tasks WHERE user_id=?"
    params = [user_id]

    if search:
        query += " AND title LIKE ?"
        params.append(f"%{search}%")

    if filter_status == "completed":
        query += " AND status='Completed'"
    elif filter_status == "pending":
        query += " AND status='Pending'"

    if sort == "latest":
        query += " ORDER BY id DESC"
    elif sort == "oldest":
        query += " ORDER BY id ASC"
    elif sort == "due":
        query += " ORDER BY due_date ASC"

    tasks = conn.execute(query, tuple(params)).fetchall()
    conn.close()

    total = len(tasks)
    completed = len([t for t in tasks if t['status'] == 'Completed'])
    pending = len([t for t in tasks if t['status'] == 'Pending'])

    percent = int((completed / total) * 100) if total > 0 else 0

    # Notifications
    today = str(date.today())
    due_today = [
        t for t in tasks
        if t['due_date'] == today and t['status'] == "Pending"
    ]

    return render_template(
        'dashboard.html',
        tasks=tasks,
        total=total,
        completed=completed,
        pending=pending,
        percent=percent,
        due_today=due_today,
        user_name=session.get('user_name')
    )

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

    conn.execute(
        "INSERT INTO tasks (title, description, status, due_date, user_id) VALUES (?, ?, ?, ?, ?)",
        (
            request.form['title'],
            request.form['desc'],
            'Pending',
            request.form['due_date'],
            session['user_id']
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

# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out!")
    return redirect('/login')

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)
    app = app