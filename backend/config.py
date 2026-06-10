import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'tumbuh_cerah_super_secret_key_2026_uniyubgtina')
    # Menggunakan SQLite agar langsung jalan tanpa perlu install MySQL server di lokal
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///tumbuh_cerah.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Pengerasan Session Cookie (OWASP Top 10 Mitigation)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = False  # Set ke True jika nanti sudah menggunakan HTTPS/SSL di AWS
    SESSION_COOKIE_SAMESITE = 'Lax'