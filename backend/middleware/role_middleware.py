from functools import wraps
from flask import session, abort, request
from utils.logger import log_security_event

def require_role(required_role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                abort(401)
            if session.get('role') != required_role:
                log_security_event(
                    f"Eskalasi privilese ilegal oleh user ID {session.get('user_id')} ke rute: {request.path}", 
                    "CRITICAL"
                )
                abort(403)  # Forbidden
            return f(*args, **kwargs)
        return decorated_function
    return decorator