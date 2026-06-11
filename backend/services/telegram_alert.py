import os
import requests
from datetime import datetime

TOKEN_BOT = os.environ.get('TELEGRAM_BOT_TOKEN', '')
ID_CHAT_GRUP = os.environ.get('TELEGRAM_CHAT_ID', '')

def kirim_insiden_ke_telegram(pesan_alert):
    if not TOKEN_BOT or not ID_CHAT_GRUP:
        print("Telegram token/chat ID belum dikonfigurasi")
        return
    url = f"https://api.telegram.org/bot{TOKEN_BOT}/sendMessage"
    payload = {
        "chat_id": ID_CHAT_GRUP,
        "text": f"⚠️ *[INCIDENT ALERT - TUMBUHCERAH]* ⚠️\n{pesan_alert}",
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=3)
    except Exception as e:
        print(f"Gagal push notifikasi SOC Telegram: {str(e)}")

def alert_brute_force(ip, username):
    pesan = (
        f"🚨 *Brute Force Detected*\n"
        f"IP: `{ip}`\n"
        f"Username: `{username}`\n"
        f"Waktu: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
        f"Server: AWS EC2 ap-southeast-2"
    )
    kirim_insiden_ke_telegram(pesan)

def alert_login_gagal(ip, username):
    pesan = (
        f"❌ *Login Gagal*\n"
        f"IP: `{ip}`\n"
        f"Username: `{username}`\n"
        f"Waktu: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
    )
    kirim_insiden_ke_telegram(pesan)

def alert_login_berhasil(username):
    pesan = (
        f"✅ *Login Berhasil*\n"
        f"Username: `{username}`\n"
        f"Waktu: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
    )
    kirim_insiden_ke_telegram(pesan)

def alert_register_baru(username):
    pesan = (
        f"🆕 *User Baru Terdaftar*\n"
        f"Username: `{username}`\n"
        f"Waktu: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
    )
    kirim_insiden_ke_telegram(pesan)