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

    if Venue.query.count() == 0:
        db.session.add_all(
            [
                Venue(name="Main Auditorium", capacity=500, location_details="Central campus"),
                Venue(name="Seminar Hall", capacity=120, location_details="Academic block, first floor"),
                Venue(name="Open Air Stage", capacity=800, location_details="Student activity lawn"),
            ]
        )
    db.session.commit()
