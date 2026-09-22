from functools import wraps

from flask import flash, redirect, url_for
from flask_login import current_user


def role_required(role):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for("auth.login"))
            if current_user.role != role:
                flash("You do not have permission to access that page.", "danger")
                return redirect(url_for("auth.login"))
            return view(*args, **kwargs)

        return wrapped

    return decorator
