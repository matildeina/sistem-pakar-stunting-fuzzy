import re

def sanitize_xss(text):
    if not isinstance(text, str):
        return text
    # Hapus tag <script> dan modifikasinya
    clean = re.sub(r'<script.*?>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
    # Ganti karakter khusus HTML menjadi HTML entities aman
    clean = clean.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&#x27;')
    return clean