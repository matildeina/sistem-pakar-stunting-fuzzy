from extensions import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum('User', 'Admin'), default='User', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relasi token otomatis
    consultations = db.relationship('ConsultationHistory', backref='user', lazy=True, cascade="all, delete-orphan")