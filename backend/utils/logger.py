import os
import logging
from flask import request, session
from extensions import db
from models.activity_log import ActivityLog

# Setup log file local menggunakan sub-modul os.path yang benar
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

logging.basicConfig(
    filename=os.path.join(log_dir, 'security.log'),
    level=logging.WARNING,
    format='%(asctime)s [%(levelname)s] IP: %(message)s'
)

def log_security_event(action, severity="INFO", user_id=None):
    ip_addr = request.remote_addr or '127.0.0.1'
    user_agent = request.headers.get('User-Agent', 'Unknown')
    active_uid = user_id or session.get('user_id')
    
    # Catat ke file lokal untuk Wazuh Agent
    logging.warning(f"{ip_addr} - UID: {active_uid} - Action: {action} - Severity: {severity} - UA: {user_agent}")
    
    # Catat ke database
    try:
        log_entry = ActivityLog(
            user_id=active_uid,
            action=action,
            ip_address=ip_addr,
            user_agent=user_agent,
            severity=severity
        )
        db.session.add(log_entry)
        db.session.commit()
    except Exception as e:
        print(f"Gagal mencatat log ke database: {str(e)}")
        db.session.rollback()