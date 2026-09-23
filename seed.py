from werkzeug.security import generate_password_hash

from models import User, Venue, db


def ensure_seed_data():
    if not User.query.filter_by(email="admin@college.edu").first():
        db.session.add(
            User(
                full_name="College Administrator",
                email="admin@college.edu",
                password_hash=generate_password_hash("admin123"),
                role="Admin",
            )
        )

    demo_accounts = [
        ("Harsh Organizer", "harsh@gmail.com", "Organizer"),
        ("Deepika Manchala", "deepikamanchala3@gmail.com", "Student"),
    ]
    for full_name, email, role in demo_accounts:
        if not User.query.filter_by(email=email).first():
            db.session.add(
                User(
                    full_name=full_name,
                    email=email,
                    password_hash=generate_password_hash("demo123"),
                    role=role,
                )
            )

    if Venue.query.count() == 0:
        db.session.add_all(
            [
                Venue(name="Main Auditorium", capacity=500, location_details="Central campus"),
                Venue(name="Seminar Hall", capacity=120, location_details="Academic block, first floor"),
                Venue(name="Open Air Stage", capacity=800, location_details="Student activity lawn"),
            ]
        )
    db.session.commit()
