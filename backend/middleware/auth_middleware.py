from functools import wraps
from flask import session, redirect, url_for, request
from utils.logger import log_security_event

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):

        if 'user_id' not in session:

            log_security_event(
                f"Akses tanpa login ke: {request.path}",
                "WARNING"
            )

            return redirect(url_for("auth.login"))

        return f(*args, **kwargs)

    return decorated_function