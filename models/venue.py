from . import db


class Venue(db.Model):
    __tablename__ = "venues"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    capacity = db.Column(db.Integer, nullable=False)
    location_details = db.Column(db.String(255), nullable=False, default="")

    def __repr__(self):
        return f"<Venue {self.name}>"
