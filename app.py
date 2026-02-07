from flask import Flask, render_template, request, redirect, url_for, send_from_directory, session, flash
import os
import sqlite3
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "secret123"

UPLOAD_FOLDER = "uploads"
DB_NAME = "database.db"
ALLOWED_EXTENSIONS = {"pdf"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# ------------------ Database ------------------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT
        )
    """)
    conn.commit()
    conn.close()


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ------------------ Routes ------------------
@app.route("/")
def home():
    return render_template("upload.html")


@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("pdf")

    if not file or file.filename == "":
        flash("No file selected")
        return redirect("/")

    if not allowed_file(file.filename):
        flash("Only PDF allowed!")
        return redirect("/")

    filename = secure_filename(file.filename)
    path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(path)

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("INSERT INTO files(filename) VALUES(?)", (filename,))
    conn.commit()
    conn.close()

    flash("Upload successful!")
    return redirect("/")


# ------------------ Admin Login ------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "admin123":
            session["admin"] = True
            return redirect("/admin")
        else:
            flash("Wrong credentials")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ------------------ Admin Dashboard ------------------
@app.route("/admin")
def admin():
    if not session.get("admin"):
        return redirect("/login")

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT * FROM files")
    files = cur.fetchall()
    conn.close()

    return render_template("admin.html", files=files)


@app.route("/download/<filename>")
def download(filename):
    if not session.get("admin"):
        return redirect("/login")

    return send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=True)


@app.route("/delete/<int:file_id>")
def delete(file_id):
    if not session.get("admin"):
        return redirect("/login")

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("SELECT filename FROM files WHERE id=?", (file_id,))
    row = cur.fetchone()

    if row:
        filename = row[0]
        path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        if os.path.exists(path):
            os.remove(path)

        cur.execute("DELETE FROM files WHERE id=?", (file_id,))

    conn.commit()
    conn.close()

    return redirect("/admin")


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
