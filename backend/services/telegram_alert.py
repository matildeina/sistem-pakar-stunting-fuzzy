import requests

TOKEN_BOT = "77654321:AAH_ExampleTokenSecret2026"
ID_CHAT_GRUP = "-100123456789"

def kirim_insiden_ke_telegram(pesan_alert):
    url = f"https://api.telegram.org/bot{TOKEN_BOT}/sendMessage"
    payload = {
        "chat_id": ID_CHAT_GRUP,
        "text": f"⚠️ [INCIDENT ALERT - TUMBUHCERAH] ⚠️\n{pesan_alert}",
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=3)
    except Exception as e:
        print(f"Gagal push notifikasi SOC Telegram: {str(e)}")