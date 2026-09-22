from datetime import datetime

from . import db


class Activity(db.Model):
    __tablename__ = "activities"

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)

    event = db.relationship("Event", backref="activities")

    def __repr__(self):
        return f"<Activity {self.title}>"
