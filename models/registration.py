from datetime import datetime

from . import db


class Registration(db.Model):
    __tablename__ = "registrations"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False)
    registered_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (db.UniqueConstraint("student_id", "event_id", name="uq_student_event"),)

    event = db.relationship("Event", backref="registrations")
    student = db.relationship("User")

    def __repr__(self):
        return f"<Registration {self.student_id}:{self.event_id}>"
