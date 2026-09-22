from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user

from models import Activity, Announcement, Event, Registration, User, Venue, db
from routes.decorators import role_required

organizer_bp = Blueprint("organizer", __name__, url_prefix="/organizer")
ACTIVE_STATUSES = ("PENDING", "APPROVED", "PUBLISHED")


def _parse_event_form():
    try:
        event_date = datetime.strptime(request.form["event_date"], "%Y-%m-%d").date()
        start_time = datetime.strptime(request.form["start_time"], "%H:%M").time()
        end_time = datetime.strptime(request.form["end_time"], "%H:%M").time()
        venue_id = int(request.form["venue_id"])
        max_capacity = int(request.form["max_capacity"])
    except (KeyError, TypeError, ValueError):
        raise ValueError("Please provide valid event date, time, venue, and capacity values.")

    if not request.form.get("title", "").strip() or not request.form.get("description", "").strip():
        raise ValueError("Title and description are required.")
    if start_time >= end_time:
        raise ValueError("Event start time must be before the end time.")
    if max_capacity <= 0:
        raise ValueError("Maximum capacity must be greater than zero.")
    return {
        "title": request.form["title"].strip(),
        "description": request.form["description"].strip(),
        "category": request.form.get("category", "Technical"),
        "event_date": event_date,
        "start_time": start_time,
        "end_time": end_time,
        "venue_id": venue_id,
        "max_capacity": max_capacity,
    }


def _find_conflict(values, ignored_event_id=None):
    query = Event.query.filter(
        Event.venue_id == values["venue_id"],
        Event.event_date == values["event_date"],
        Event.status.in_(ACTIVE_STATUSES),
        Event.start_time < values["end_time"],
        Event.end_time > values["start_time"],
    )
    if ignored_event_id is not None:
        query = query.filter(Event.id != ignored_event_id)
    return query.first()


def _event_for_organizer(event_id):
    return Event.query.filter_by(id=event_id, organizer_id=current_user.id).first_or_404()


@organizer_bp.route("/dashboard")
@role_required("Organizer")
def dashboard():
    events = Event.query.filter_by(organizer_id=current_user.id).order_by(Event.created_at.desc()).all()
    event_ids = [event.id for event in events]
    registration_count = Registration.query.filter(Registration.event_id.in_(event_ids)).count() if event_ids else 0
    return render_template(
        "organizer/dashboard.html",
        user=current_user,
        events=events,
        participants_total=registration_count,
        pending_count=sum(event.status == "PENDING" for event in events),
    )


@organizer_bp.route("/my-events")
@organizer_bp.route("/events")
@role_required("Organizer")
def events():
    return render_template(
        "organizer/my_events.html",
        user=current_user,
        events=Event.query.filter_by(organizer_id=current_user.id).order_by(Event.event_date.asc()).all(),
    )


@organizer_bp.route("/create-event", methods=["GET", "POST"])
@role_required("Organizer")
def create_event():
    venues = Venue.query.order_by(Venue.name.asc()).all()
    if request.method == "POST":
        try:
            values = _parse_event_form()
            venue = db.session.get(Venue, values["venue_id"])
            if venue is None:
                raise ValueError("Selected venue does not exist.")
            if values["max_capacity"] > venue.capacity:
                raise ValueError("Maximum capacity cannot exceed the venue capacity.")
            if _find_conflict(values):
                raise ValueError("Venue is already booked during the selected time slot.")
        except ValueError as error:
            flash(str(error), "danger")
            return render_template("organizer/create_event.html", user=current_user, venues=venues)

        event = Event(**values, organizer_id=current_user.id, status="PENDING")
        db.session.add(event)
        db.session.commit()
        flash("Event submitted for admin approval.", "success")
        return redirect(url_for("organizer.events"))

    return render_template("organizer/create_event.html", user=current_user, venues=venues)


@organizer_bp.route("/event/<int:event_id>/edit", methods=["GET", "POST"])
@role_required("Organizer")
def edit_event(event_id):
    event = _event_for_organizer(event_id)
    venues = Venue.query.order_by(Venue.name.asc()).all()
    if request.method == "POST":
        try:
            values = _parse_event_form()
            venue = db.session.get(Venue, values["venue_id"])
            if venue is None or values["max_capacity"] > venue.capacity:
                raise ValueError("Maximum capacity cannot exceed the venue capacity.")
            if _find_conflict(values, event.id):
                raise ValueError("Venue is already booked during the selected time slot.")
        except ValueError as error:
            flash(str(error), "danger")
            return render_template("organizer/create_event.html", user=current_user, venues=venues, event=event)
        for key, value in values.items():
            setattr(event, key, value)
        event.status = "PENDING"
        db.session.commit()
        flash("Event updated and sent for approval.", "success")
        return redirect(url_for("organizer.events"))
    return render_template("organizer/create_event.html", user=current_user, venues=venues, event=event)


@organizer_bp.route("/event/<int:event_id>/participants")
@role_required("Organizer")
def event_participants(event_id):
    event = _event_for_organizer(event_id)
    registrations = Registration.query.filter_by(event_id=event.id).order_by(Registration.registered_at.asc()).all()
    return render_template("organizer/participants.html", user=current_user, event=event, participants=registrations)


@organizer_bp.route("/participants")
@role_required("Organizer")
def participants():
    event = Event.query.filter_by(organizer_id=current_user.id).order_by(Event.event_date.asc()).first()
    if event is None:
        return render_template("organizer/participants.html", user=current_user, event=None, participants=[])
    return redirect(url_for("organizer.event_participants", event_id=event.id))


@organizer_bp.route("/event/<int:event_id>/activities", methods=["GET", "POST"])
@role_required("Organizer")
def event_activities(event_id):
    event = _event_for_organizer(event_id)
    if event.status not in {"APPROVED", "PUBLISHED"}:
        flash("Activities can be managed after admin approval.", "warning")
        return redirect(url_for("organizer.events"))
    if request.method == "POST":
        try:
            title = request.form["title"].strip()
            start_time = datetime.strptime(request.form["start_time"], "%H:%M").time()
            end_time = datetime.strptime(request.form["end_time"], "%H:%M").time()
            if not title or start_time >= end_time or start_time < event.start_time or end_time > event.end_time:
                raise ValueError
        except (KeyError, ValueError):
            flash("Activity must have valid times within the event time window.", "danger")
        else:
            db.session.add(Activity(event_id=event.id, title=title, start_time=start_time, end_time=end_time))
            db.session.commit()
            flash("Activity added.", "success")
        return redirect(url_for("organizer.event_activities", event_id=event.id))
    activities = Activity.query.filter_by(event_id=event.id).order_by(Activity.start_time.asc()).all()
    return render_template("organizer/activities.html", user=current_user, event=event, activities=activities)


@organizer_bp.route("/activities")
@role_required("Organizer")
def activities():
    event = Event.query.filter_by(organizer_id=current_user.id).order_by(Event.event_date.asc()).first()
    if event is None:
        flash("Create an event before managing activities.", "warning")
        return redirect(url_for("organizer.create_event"))
    return redirect(url_for("organizer.event_activities", event_id=event.id))


@organizer_bp.route("/event/<int:event_id>/activities/<int:activity_id>/delete", methods=["POST"])
@role_required("Organizer")
def delete_activity(event_id, activity_id):
    event = _event_for_organizer(event_id)
    activity = Activity.query.filter_by(id=activity_id, event_id=event.id).first_or_404()
    db.session.delete(activity)
    db.session.commit()
    flash("Activity deleted.", "success")
    return redirect(url_for("organizer.event_activities", event_id=event.id))


@organizer_bp.route("/event/<int:event_id>/announcements", methods=["GET", "POST"])
@role_required("Organizer")
def event_announcements(event_id):
    event = _event_for_organizer(event_id)
    if event.status not in {"APPROVED", "PUBLISHED"}:
        flash("Announcements can be published after admin approval.", "warning")
        return redirect(url_for("organizer.events"))
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        message = request.form.get("message", "").strip()
        if not title or not message:
            flash("Announcement title and message are required.", "danger")
        else:
            db.session.add(Announcement(event_id=event.id, title=title, message=message))
            db.session.commit()
            flash("Announcement published.", "success")
        return redirect(url_for("organizer.event_announcements", event_id=event.id))
    announcements = Announcement.query.filter_by(event_id=event.id).order_by(Announcement.created_at.desc()).all()
    return render_template("organizer/announcements.html", user=current_user, event=event, announcements=announcements)


@organizer_bp.route("/announcements")
@role_required("Organizer")
def announcements():
    event = Event.query.filter_by(organizer_id=current_user.id).order_by(Event.event_date.asc()).first()
    if event is None:
        return render_template("organizer/announcements.html", user=current_user, event=None, announcements=[])
    return redirect(url_for("organizer.event_announcements", event_id=event.id))
