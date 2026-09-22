import os

from flask import Flask
from flask_login import LoginManager

from config import Config, TestConfig
from models import User, db
from routes import admin_bp, auth_bp, organizer_bp, student_bp


def create_app(testing=False):
    app = Flask(__name__)
    app.config.from_object(TestConfig if testing else Config)

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(organizer_bp)
    app.register_blueprint(admin_bp)

    with app.app_context():
        if not testing:
            from sqlalchemy import inspect

            inspector = inspect(db.engine)
            event_columns = {column["name"] for column in inspector.get_columns("events")} if "events" in inspector.get_table_names() else set()
            if event_columns and "title" not in event_columns:
                db.drop_all()
        db.create_all()
        from seed import ensure_seed_data

        ensure_seed_data()

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
