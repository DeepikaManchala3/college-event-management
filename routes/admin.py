from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user
from sqlalchemy import func

from models import Event, Registration, User, Venue, db
from routes.decorators import role_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/dashboard")
@role_required("Admin")
def dashboard():
    return render_template(
        "admin/dashboard.html",
        user=current_user,
        total_users=User.query.count(),
        total_events=Event.query.count(),
        pending_count=Event.query.filter_by(status="PENDING").count(),
        total_registrations=Registration.query.count(),
        pending_events=Event.query.filter_by(status="PENDING").order_by(Event.created_at.asc()).all(),
    )


@admin_bp.route("/approvals")
@role_required("Admin")
def approvals():
    return render_template(
        "admin/approvals.html",
        user=current_user,
        pending_events=Event.query.filter_by(status="PENDING").order_by(Event.created_at.asc()).all(),
    )


@admin_bp.route("/events")
@role_required("Admin")
def events():
    return render_template("admin/events.html", user=current_user, events=Event.query.order_by(Event.event_date.asc()).all())


@admin_bp.route("/events/<int:event_id>/approve", methods=["POST"])
@role_required("Admin")
def approve_event(event_id):
    event = Event.query.filter_by(id=event_id, status="PENDING").first_or_404()
    event.status = "PUBLISHED"
    db.session.commit()
    flash(f"{event.title} is now published.", "success")
    return redirect(request.referrer or url_for("admin.approvals"))


@admin_bp.route("/events/<int:event_id>/reject", methods=["POST"])
@role_required("Admin")
def reject_event(event_id):
    event = Event.query.filter_by(id=event_id, status="PENDING").first_or_404()
    event.status = "REJECTED"
    reason = request.form.get("reason", "").strip()
    db.session.commit()
    message = f"{event.title} rejected."
    if reason:
        message += f" Reason: {reason}"
    flash(message, "warning")
    return redirect(request.referrer or url_for("admin.approvals"))


@admin_bp.route("/registrations")
@role_required("Admin")
def registrations():
    registrations = Registration.query.order_by(Registration.registered_at.desc()).all()
    return render_template("admin/registrations.html", user=current_user, registrations=registrations)


@admin_bp.route("/venues", methods=["GET", "POST"])
@role_required("Admin")
def venues():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        location_details = request.form.get("location_details", "").strip()
        try:
            capacity = int(request.form.get("capacity", "0"))
        except ValueError:
            capacity = 0
        if not name or capacity <= 0:
            flash("Venue name and a positive capacity are required.", "danger")
        elif Venue.query.filter(func.lower(Venue.name) == name.lower()).first():
            flash("A venue with that name already exists.", "warning")
        else:
            db.session.add(Venue(name=name, capacity=capacity, location_details=location_details))
            db.session.commit()
            flash("Venue created.", "success")
        return redirect(url_for("admin.venues"))
    return render_template("admin/venues.html", user=current_user, venues=Venue.query.order_by(Venue.name.asc()).all())


@admin_bp.route("/venues/<int:venue_id>/delete", methods=["POST"])
@role_required("Admin")
def delete_venue(venue_id):
    venue = Venue.query.get_or_404(venue_id)
    if Event.query.filter_by(venue_id=venue.id).first():
        flash("A venue used by an event cannot be deleted.", "danger")
    else:
        db.session.delete(venue)
        db.session.commit()
        flash("Venue deleted.", "success")
    return redirect(url_for("admin.venues"))


@admin_bp.route("/reports")
@role_required("Admin")
def reports():
    completed_events = Event.query.filter_by(status="COMPLETED").count()
    published_events = Event.query.filter_by(status="PUBLISHED").count()
    registrations_by_event = (
        db.session.query(Event.title, func.count(Registration.id))
        .outerjoin(Registration, Registration.event_id == Event.id)
        .group_by(Event.id)
        .order_by(func.count(Registration.id).desc())
        .all()
    )
    return render_template(
        "admin/reports.html",
        user=current_user,
        completed_events=completed_events,
        published_events=published_events,
        total_registrations=Registration.query.count(),
        registrations_by_event=registrations_by_event,
    )
