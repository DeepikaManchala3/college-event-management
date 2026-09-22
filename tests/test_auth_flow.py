from datetime import date

from werkzeug.security import generate_password_hash

from app import create_app
from models import Event, User, Venue, db


app = create_app(testing=True)


def setup_module():
    with app.app_context():
        db.drop_all()
        db.create_all()
        admin = User(
            full_name="Admin",
            email="admin@college.edu",
            password_hash=generate_password_hash("admin123"),
            role="Admin",
        )
        organizer = User(
            full_name="Organizer",
            email="organizer@test.edu",
            password_hash=generate_password_hash("organizer123"),
            role="Organizer",
        )
        student = User(
            full_name="Student",
            email="student@test.edu",
            password_hash=generate_password_hash("student123"),
            role="Student",
        )
        db.session.add_all([admin, organizer, student, Venue(name="Test Hall", capacity=2, location_details="Test campus")])
        db.session.commit()


def login(client, email, password):
    return client.post("/login", data={"email": email, "password": password}, follow_redirects=False)


def create_event(client, title="Test Event", start="10:00", end="12:00", capacity=2):
    with app.app_context():
        venue = Venue.query.filter_by(name="Test Hall").first()
    return client.post(
        "/organizer/create-event",
        data={
            "title": title,
            "description": "A persisted event.",
            "category": "Technical",
            "event_date": "2026-11-15",
            "start_time": start,
            "end_time": end,
            "venue_id": venue.id,
            "max_capacity": str(capacity),
        },
        follow_redirects=False,
    )


def test_login_page_and_role_redirects():
    client = app.test_client()
    assert client.get("/login").status_code == 200
    response = login(client, "admin@college.edu", "admin123")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/admin/dashboard")


def test_organizer_creation_and_venue_conflict():
    client = app.test_client()
    login(client, "organizer@test.edu", "organizer123")
    assert create_event(client).status_code == 302
    with app.app_context():
        assert Event.query.filter_by(title="Test Event", status="PENDING").count() == 1
    response = create_event(client, title="Conflicting Event", start="11:00", end="13:00")
    assert response.status_code == 200
    assert b"Venue is already booked during the selected time slot" in response.data


def test_admin_approval_and_student_registration_flow():
    admin_client = app.test_client()
    login(admin_client, "admin@college.edu", "admin123")
    with app.app_context():
        event = Event.query.filter_by(title="Test Event").first()
        event_id = event.id
    response = admin_client.post(f"/admin/events/{event_id}/approve", follow_redirects=False)
    assert response.status_code == 302
    with app.app_context():
        assert db.session.get(Event, event_id).status == "PUBLISHED"

    student_client = app.test_client()
    login(student_client, "student@test.edu", "student123")
    response = student_client.post(f"/student/events/{event_id}/register", follow_redirects=False)
    assert response.status_code == 302
    duplicate = student_client.post(f"/student/events/{event_id}/register", follow_redirects=False)
    assert duplicate.status_code == 302
    with app.app_context():
        assert db.session.get(Event, event_id).registrations[0].student.email == "student@test.edu"


def test_organizer_activity_and_announcement_endpoints():
    client = app.test_client()
    login(client, "organizer@test.edu", "organizer123")
    with app.app_context():
        event_id = Event.query.filter_by(title="Test Event").first().id
    response = client.post(
        f"/organizer/event/{event_id}/activities",
        data={"title": "Opening", "start_time": "10:30", "end_time": "11:00"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    response = client.post(
        f"/organizer/event/{event_id}/announcements",
        data={"title": "Room update", "message": "The event is in Test Hall."},
        follow_redirects=False,
    )
    assert response.status_code == 302


def test_admin_can_create_venue():
    client = app.test_client()
    login(client, "admin@college.edu", "admin123")
    response = client.post(
        "/admin/venues",
        data={"name": "New Hall", "capacity": "100", "location_details": "North campus"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    with app.app_context():
        assert Venue.query.filter_by(name="New Hall", capacity=100).first() is not None
