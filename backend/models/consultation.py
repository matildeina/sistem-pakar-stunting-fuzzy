from extensions import db
from datetime import datetime

class ConsultationHistory(db.Model):
    __tablename__ = 'consultation_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    usia_bulan = db.Column(db.Integer, nullable=False)
    jenis_kelamin = db.Column(db.Enum('L', 'P'), nullable=False)
    tinggi_badan = db.Column(db.Float, nullable=False)
    berat_badan = db.Column(db.Float, nullable=False)
    status_fuzzy = db.Column(db.String(50), nullable=False)
    skor_fuzzy = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)