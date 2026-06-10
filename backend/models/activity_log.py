from extensions import db
from datetime import datetime

class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    action = db.Column(db.String(255), nullable=False)
    ip_address = db.Column(db.String(45), nullable=False)
    user_agent = db.Column(db.String(255), nullable=False)
    severity = db.Column(db.Enum('INFO', 'WARNING', 'CRITICAL'), default='INFO', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class FailedLogin(db.Model):
    __tablename__ = 'failed_logins'
    
    id = db.Column(db.Integer, primary_key=True)
    username_attempted = db.Column(db.String(50), nullable=False)
    ip_address = db.Column(db.String(45), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)