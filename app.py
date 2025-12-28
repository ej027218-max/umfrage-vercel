from flask import Flask, render_template, request, redirect, session
from werkzeug.security import check_password_hash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "7f3a9d8e2b1c4f6a9d0e3b7c1a2d5f8e"
  
# Admin-Zugang
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "Eric"  

# Datenbankverbindung
def get_db():
    return sqlite3.connect("database.db")

# ===========================
# Benutzer Login
# ===========================
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE username = ?",
            (request.form["username"],)
        ).fetchone()
        if user and check_password_hash(user[2], request.form["password"]):
            session["user_id"] = user[0]
            return redirect("/survey")
    return render_template("login.html")

# ===========================
# Umfrage-Seite
# ===========================
@app.route("/survey", methods=["GET", "POST"])
def survey():
    if "user_id" not in session:
        return redirect("/")
    
    db = get_db()
    voted = db.execute(
        "SELECT has_voted FROM users WHERE id = ?",
        (session["user_id"],)
    ).fetchone()[0]

    if voted:
        return "Du hast bereits abgestimmt."

    if request.method == "POST":
        db.execute(
            "INSERT INTO votes (user_id, answer, year) VALUES (?, ?, ?)",
            (session["user_id"], request.form["answer"], datetime.now().year)
        )
        db.execute(
            "UPDATE users SET has_voted = 1 WHERE id = ?",
            (session["user_id"],)
        )
        db.commit()
        return redirect("/done")
    
    return render_template("survey.html")

# ===========================
# Danke-Seite
# ===========================
@app.route("/done")
def done():
    return render_template("done.html")

# ===========================
# Admin Login
# ===========================
@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect("/admin/dashboard")
    return render_template("admin_login.html")

# ===========================
# Admin Dashboard
# ===========================
@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("admin"):
        return redirect("/admin")

    db = get_db()
    votes = db.execute(
        "SELECT users.username, votes.answer, votes.year "
        "FROM votes JOIN users ON votes.user_id = users.id"
    ).fetchall()
    return render_template("admin_dashboard.html", votes=votes)

# ===========================
# Admin Reset
# ===========================
@app.route("/admin/reset")
def admin_reset():
    if not session.get("admin"):
        return redirect("/admin")
    db = get_db()
    db.execute("UPDATE users SET has_voted = 0")
    db.execute("DELETE FROM votes")
    db.commit()
    return "✅ Umfrage zurückgesetzt!"

# ===========================
# Flask starten
# ===========================
if __name__ == "__main__":
    app.run(debug=True)
