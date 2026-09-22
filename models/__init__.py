from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()

from .user import User
from .event import Event
from .registration import Registration
from .activity import Activity
from .announcement import Announcement
from .venue import Venue
