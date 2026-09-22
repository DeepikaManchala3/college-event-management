from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user

from models import Announcement, Event, Registration, db
from routes.decorators import role_required

student_bp = Blueprint("student", __name__, url_prefix="/student")


def _published_events():
    query = Event.query.filter_by(status="PUBLISHED")
    category = request.args.get("category", "").strip()
    if category:
        query = query.filter_by(category=category)
    return query.order_by(Event.event_date.asc(), Event.start_time.asc())


@student_bp.route("/dashboard")
@role_required("Student")
def dashboard():
    registrations = Registration.query.filter_by(student_id=current_user.id).all()
    registered_event_ids = [registration.event_id for registration in registrations]
    upcoming_events = Event.query.filter_by(status="PUBLISHED").order_by(Event.event_date.asc()).limit(5).all()
    announcements = (
        Announcement.query.filter(Announcement.event_id.in_(registered_event_ids))
        .order_by(Announcement.created_at.desc())
        .limit(10)
        .all()
        if registered_event_ids
        else []
    )
    return render_template(
        "student/dashboard.html",
        user=current_user,
        upcoming_events=upcoming_events,
        registrations=registrations,
        announcements=announcements,
    )


@student_bp.route("/events")
@role_required("Student")
def events():
    return render_template(
        "student/events.html",
        user=current_user,
        events=_published_events().all(),
        selected_category=request.args.get("category", ""),
    )


@student_bp.route("/events/<int:event_id>")
@role_required("Student")
def event_details(event_id):
    event = Event.query.filter_by(id=event_id, status="PUBLISHED").first_or_404()
    registration = Registration.query.filter_by(student_id=current_user.id, event_id=event.id).first()
    return render_template("student/event_details.html", user=current_user, event=event, registration=registration)


@student_bp.route("/events/<int:event_id>/register", methods=["POST"])
@role_required("Student")
def register_for_event(event_id):
    event = Event.query.filter_by(id=event_id, status="PUBLISHED").first_or_404()
    if Registration.query.filter_by(student_id=current_user.id, event_id=event.id).first():
        flash("You are already registered for this event.", "warning")
        return redirect(url_for("student.event_details", event_id=event.id))

    if Registration.query.filter_by(event_id=event.id).count() >= event.max_capacity:
        flash("This event has reached its capacity.", "danger")
        return redirect(url_for("student.event_details", event_id=event.id))

    db.session.add(Registration(student_id=current_user.id, event_id=event.id))
    db.session.commit()
    flash("Registration successful.", "success")
    return redirect(url_for("student.registrations"))


@student_bp.route("/registrations")
@role_required("Student")
def registrations():
    registrations = (
        Registration.query.filter_by(student_id=current_user.id)
        .join(Event)
        .order_by(Event.event_date.asc())
        .all()
    )
    return render_template("student/registrations.html", user=current_user, registrations=registrations)


@student_bp.route("/announcements")
@role_required("Student")
def announcements():
    event_ids = db.session.query(Registration.event_id).filter_by(student_id=current_user.id).subquery()
    items = Announcement.query.filter(Announcement.event_id.in_(event_ids)).order_by(Announcement.created_at.desc()).all()
    return render_template("student/announcements.html", user=current_user, announcements=items)
