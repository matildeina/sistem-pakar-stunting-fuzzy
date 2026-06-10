from flask import Blueprint, render_template, session
from middleware.role_middleware import require_role
from models.activity_log import ActivityLog, FailedLogin

admin_bp = Blueprint('admin', __name__)

@admin_bp.route("/admin/dashboard", methods=["GET"])
@require_role('Admin')  # Menjamin proteksi Broken Function Level Access Control
def admin_dashboard():
    logs = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(100).all()
    failed_attempts = FailedLogin.query.order_by(FailedLogin.created_at.desc()).limit(50).all()
    return render_template("admin_dashboard.html", logs=logs, failed_attempts=failed_attempts)