from datetime import datetime

from . import db


class Event(db.Model):
    __tablename__ = "events"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    event_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    max_capacity = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(30), default="DRAFT", nullable=False)
    organizer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey("venues.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    organizer = db.relationship("User", backref="organized_events")
    venue = db.relationship("Venue", backref="events")

    def __repr__(self):
        return f"<Event {self.title}>"
