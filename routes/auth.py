from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash

from models import User, db


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/")
def index():
    return redirect(url_for("auth.login"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            if user.role == "Admin":
                return redirect(url_for("admin.dashboard"))
            if user.role == "Organizer":
                return redirect(url_for("organizer.dashboard"))
            return redirect(url_for("student.dashboard"))

        flash("Invalid email or password.", "danger")

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        role = request.form.get("role", "Student")

        if not name or not email or not password:
            flash("All fields are required.", "danger")
            return render_template("auth/register.html")
        if role not in {"Student", "Organizer"}:
            flash("Only Student and Organizer accounts can be registered here.", "danger")
            return render_template("auth/register.html")

        if User.query.filter_by(email=email).first():
            flash("User already exists.", "warning")
            return render_template("auth/register.html")

        user = User(
            full_name=name,
            email=email,
            password_hash=generate_password_hash(password),
            role=role,
        )
        db.session.add(user)
        db.session.commit()
        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")
