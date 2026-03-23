import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
from flask import Flask, render_template, request, redirect, session
import sqlite3
import matplotlib.pyplot as plt
import io
import base64
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import io
from flask import send_file

app = Flask(__name__)
app.secret_key = "secret123"

# Database connection
def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

# ---------------- LOGIN PAGE ----------------
@app.route("/login_page")
def login_page():
    return render_template("login.html")

# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm = request.form.get("confirm")

        if password != confirm:
            return render_template("register.html", error="Passwords do not match")

        conn = get_db()
        conn.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, password)
        )
        conn.commit()
        conn.close()

        return redirect("/login_page")

    return render_template("register.html")

# ---------------- LOGIN ----------------
@app.route("/login", methods=["POST"])
def login():
    # ✅ Correct field names (must match HTML)
    username = request.form.get("username")
    password = request.form.get("password")

    print("Entered:", username, password)

    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE username=? AND password=?",
        (username, password)
    ).fetchone()
    conn.close()

    print("Database result:", user)

    if user:
        session["user"] = username
        return redirect("/")
    else:
        return render_template("login.html", error="Invalid Login")

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login_page")

# ---------------- DASHBOARD ----------------
@app.route("/")
def dashboard():
    if "user" not in session:
        return redirect("/login_page")

    conn = get_db()
    tasks = conn.execute("SELECT * FROM tasks").fetchall()
    conn.close()

    return render_template("dashboard.html", tasks=tasks)

# ---------------- ADD TASK ----------------
@app.route("/add", methods=["POST"])
def add_task():
    title = request.form.get("title")
    desc = request.form.get("desc")

    conn = get_db()
    conn.execute(
        "INSERT INTO tasks (title, description, status) VALUES (?, ?, ?)",
        (title, desc, "Pending")
    )
    conn.commit()
    conn.close()

    return redirect("/")

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_task(id):
    conn = get_db()

    if request.method == "POST":
        title = request.form.get("title")
        desc = request.form.get("desc")

        conn.execute(
            "UPDATE tasks SET title=?, description=? WHERE id=?",
            (title, desc, id)
        )
        conn.commit()
        conn.close()

        return redirect("/")

    task = conn.execute("SELECT * FROM tasks WHERE id=?", (id,)).fetchone()
    conn.close()

    return render_template("edit.html", task=task)    

# ---------------- COMPLETE ----------------
@app.route("/complete/<int:id>")
def complete_task(id):
    conn = get_db()

    task = conn.execute("SELECT status FROM tasks WHERE id=?", (id,)).fetchone()

    if task["status"] == "Pending":
        new_status = "Completed"
    else:
        new_status = "Pending"

    conn.execute(
        "UPDATE tasks SET status=? WHERE id=?",
        (new_status, id)
    )
    conn.commit()
    conn.close()

    return redirect("/")

@app.route("/graph")
def graph():
    conn = get_db()
    tasks = conn.execute("SELECT status FROM tasks").fetchall()
    conn.close()

    completed = sum(1 for t in tasks if t["status"] == "Completed")
    pending = sum(1 for t in tasks if t["status"] == "Pending")

    labels = ["Completed", "Pending"]
    values = [completed, pending]

    plt.figure()
    plt.pie(values, labels=labels, autopct='%1.1f%%')

    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)

    graph_url = base64.b64encode(img.getvalue()).decode()

    return render_template("graph.html", graph_url=graph_url)

@app.route("/download_pdf")
def download_pdf():
    from reportlab.platypus import SimpleDocTemplate, Paragraph

    doc = SimpleDocTemplate("report.pdf")
    elements = []

    for task in tasks:
        elements.append(Paragraph(f"{task['title']} - {task['status']}", None))

    doc.build(elements)
    return send_file("report.pdf", as_attachment=True)  


# ---------------- DELETE ----------------
@app.route("/delete/<int:id>")
def delete_task(id):
    conn = get_db()
    conn.execute("DELETE FROM tasks WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)