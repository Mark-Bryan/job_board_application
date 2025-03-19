from flask import Flask, render_template, request, session, redirect, url_for
import os
from mySql.dbconn import get_db_conn
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from werkzeug.utils import secure_filename

app = Flask(__name__)

app.secret_key = "job_listings"
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["SQLALCHEMY_DATABASE_URI"] = (
    "mysql+pymysql://Banyeh_Akika:#Capalot1900@localhost/job_listings"
)

db = SQLAlchemy(app)


class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    profile_picture = db.Column(db.String(255), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "profile_picture": self.profile_picture,
        }


class Jobs(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    company = db.Column(db.String(255), nullable=False)
    location = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    posted_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    status = db.Column(db.String(20), default="pending")

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "company": self.company,
            "location": self.location,
            "category": self.category,
            "posted_date": self.posted_date,
            "status": self.status,
        }


class Applications(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey("jobs.id"), nullable=False)
    cover_letter = db.Column(db.Text, nullable=False)
    cv_file_path = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(50), default="Pending")
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "job_id": self.job_id,
            "cover_letter": self.cover_letter,
            "cv_file_path": self.cv_file_path,
            "status": self.status,
            "timestamp": self.timestamp,
        }


@app.route("/")
def home():
    return render_template("landing_page.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        role = request.form.get("role")
        profile_picture = request.files.get("profile_picture")

        if role == "admin":
            existing_admin = db.session.execute(
                text("SELECT id FROM users where role = 'admin'")
            ).fetchone()

            if existing_admin:
                return " Admin already exists, Only one admin is allowed"

        if profile_picture and profile_picture.filename:
            picture_filename = profile_picture.filename
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], picture_filename)
            counter = 1
            base, ext = os.path.splitext(picture_filename)

            while os.path.exists(filepath):
                picture_filename = f"{base}_{counter}{ext}"
                filepath = os.path.join(app.config["UPLOAD_FOLDER"], picture_filename)
                counter += 1
            profile_picture.save(filepath)
        else:
            picture_filename = "default.png"

    try:
        user = Users(
            name=name,
            email=email,
            password=password,
            role=role,
            profile_picture=os.path.join("uploads", picture_filename),
        )

        db.session.add(user)
        db.session.commit()

        return redirect(url_for("home"))

    except Exception as e:
        return f"An error occured: {str(e)}"


@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = Users.query.filter_by(email=email, password=password).first()

        if user:
            session["user_id"] = user.id
            session["user_name"] = user.name
            session["role"] = user.role
            session["profile_picture"] = user.profile_picture

            return redirect(url_for("home"))
        else:
            return "Invalid email or password. Try Again"

    return render_template("landing_page.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


@app.route("/user/create/<name>/<email>/<password>/<role>")
def create_user(name, email, password, role):
    profile_picture = "default.png"
    user = Users(
        name=name,
        email=email,
        password=password,
        role=role,
        profile_picture=profile_picture,
    )
    db.session.add(user)
    db.session.commit()
    return f"User Created with Id: {user.id}"


@app.route("/admin/user/edit/<int:id>", methods=["POST", "GET"])
def edit_user(id):
    user = Users.query.get(id)
    if not user:
        return "User not found"
    if request.method == "POST":
        user.name = request.form["name"]
        user.email = request.form["email"]
        user.role = request.form["role"]
        db.session.commit()

        return redirect(url_for("admin_dashboard"))

    return render_template("edit_user.html", user=user)


@app.route("/user/<int:id>")
def retrieve_user(id):
    user = Users.query.get(id)
    if not user:
        return "User not found"
    return f"User with ID{id} has name {user.name} and email {user.email} has been retrieved"


@app.route("/user/update/<int:id>/<new_name>", methods=["GET"])
def update_user(id, new_name):
    user = Users.query.get(id)
    if not user:
        return f"User with id{id} not found"
    user.name = new_name
    db.session.commit()
    return f"User with id {id} has been updated to name {new_name}"


@app.route("/user/delete/<int:id>")
def delete_user(id):
    user = Users.query.get(id)
    if not user:
        return f"User with id{id} not found"
    db.session.delete(user)
    db.session.commit()
    return f"User with id {id} has been deleted"


@app.route("/admin")
def admin_dashboard():
    if "user_id" not in session or session.get("role") != "admin":
        return "Access Denied. Admins Only"

    users = Users.query.all()
    jobs = Jobs.query.all()
    return render_template("admin_dashboard.html", users=users, jobs=jobs)


@app.route("/admin/job/approve/<int:id>")
def approve_job(id):
    jobs = Jobs.query.get(id)
    if not jobs:
        return "Job Not Found"

    jobs.status = "approved"
    db.session.commit()
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/job/reject/<int:id>")
def reject_job(id):
    jobs = Jobs.query.get(id)
    if not jobs:
        return "Job Not Found"

    jobs.status = "rejected"
    db.session.commit()

    return redirect(url_for("admin_dashboard"))


@app.route("/admin/job/edit/<int:id>", methods=["POST", "GET"])
def edit_job(id):
    jobs = Jobs.query.get(id)
    if not jobs:
        return "Job not Found"

    if request.method == "POST":
        jobs.title = request.form["title"]
        jobs.description = request.form["description"]
        jobs.company = request.form["company"]
        jobs.location = request.form["location"]
        jobs.category = request.form["category"]

        db.session.commit()
        return redirect(url_for("admin_dashboard"))

    return render_template("edit_job.html", jobs=jobs)


@app.route("/admin/job/delete/<int:id>")
def delete_job(id):
    jobs = Jobs.query.get(id)
    if not jobs:
        return "Job Not Found"

    db.session.delete(jobs)
    db.session.commit()
    return redirect(url_for("admin_dashboard"))


@app.route("/apply/<int:job_id>", methods=["GET", "POST"])
def apply_for_job(job_id):

    jobs = {
        1: {"title": "Banker", "company": "ECOBANK", "location": "Douala, Cameroon"},
        2: {
            "title": "Software Developer",
            "company": "ABC Tech",
            "location": "Ontario, Canada",
        },
    }

    job = jobs.get(job_id)
    if not job:
        return "Job Not Found"

    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        cover_letter = request.form.get("cover_letter")
        cv_file = request.files.get("cv_file")

        if not cv_file or not cv_file.filename:
            return "No File Uploaded. Please Upload Your CV! "

        if cv_file and cv_file.filename:
            filename = secure_filename(cv_file.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            counter = 1
            base, ext = os.path.splitext(filename)
            while os.path.exists(filepath):
                filename = f"{base}_{counter}{ext}"
                filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                counter += 1
            cv_file.save(filepath)

            new_application = Applications(
                user_id=session["user_id"],
                job_id=job_id,
                cover_letter=cover_letter,
                cv_file_path=filepath,
            )

            db.session.add(new_application)
            db.session.commit()

            return "Application submitted successfully !"

    return render_template("apply_form.html", job=job)
