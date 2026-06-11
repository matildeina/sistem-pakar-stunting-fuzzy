from flask import (
    Blueprint,
    request,
    jsonify,
    session,
    render_template,
    redirect,
    url_for
)

from services.fuzzy_service import (
    fuzzy_stunting,
    klasifikasi_bbu,
    klasifikasi_tbu,
    buat_rekomendasi,
    dapatkan_jawaban_kamus,
    has_any
)

from security.xss_filter import sanitize_xss
from middleware.auth_middleware import login_required

from models.consultation import ConsultationHistory

from extensions import db, limiter, csrf

import re

# ==================================================
# WHO REFERENCE (sementara)
# ==================================================

WHO_TB_L = {i: [80.0, 2.5] for i in range(61)}
WHO_TB_P = {i: [79.0, 2.5] for i in range(61)}

WHO_BB_L = {i: [10.0, 1.2] for i in range(61)}
WHO_BB_P = {i: [9.5, 1.2] for i in range(61)}

WHO_TB_L.update({
    0: [49.9, 1.89],
    1: [54.7, 1.95],
    2: [58.4, 2.0],
    24: [87.8, 2.78],
    60: [109.4, 5.19]
})

WHO_TB_P.update({
    0: [49.1, 1.86],
    1: [53.7, 1.95],
    2: [57.1, 2.0],
    24: [86.4, 3.02],
    60: [109.4, 5.19]
})

WHO_BB_L.update({
    0: [3.3, 0.45],
    1: [4.5, 0.55],
    2: [5.6, 0.63],
    24: [12.2, 1.37],
    60: [18.3, 2.1]
})

WHO_BB_P.update({
    0: [3.2, 0.43],
    1: [4.2, 0.52],
    2: [5.1, 0.6],
    24: [11.5, 1.47],
    60: [18.2, 2.95]
})

# ==================================================
# STEMMER
# ==================================================

try:
    from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
    stemmer = StemmerFactory().create_stemmer()
except Exception:
    stemmer = None

# ==================================================
# BLUEPRINT
# ==================================================

api_bp = Blueprint("api", __name__)

# ==================================================
# HOME
# ==================================================

@api_bp.route("/")
def home():

    if "user_id" in session:
        return redirect(url_for("api.index"))

    return redirect(url_for("auth.login"))

# ==================================================
# LANDING PAGE
# ==================================================

@api_bp.route("/index")
@login_required
def index():
    return render_template("index.html")

# ==================================================
# CHAT PAGE
# ==================================================

@api_bp.route("/chat")
@login_required
def chat():

    session.pop("last_tb", None)
    session.pop("last_bb", None)
    session.pop("last_usia", None)

    return render_template("chat.html")

# ==================================================
# DASHBOARD
# ==================================================

@api_bp.route("/dashboard")
@login_required
def dashboard():

    history = ConsultationHistory.query.filter_by(
        user_id=session["user_id"]
    ).order_by(
        ConsultationHistory.created_at.desc()
    ).all()

    return render_template(
        "dashboard.html",
        history=history
    )

# ==================================================
# CEK STUNTING
# ==================================================

@api_bp.route("/cek", methods=["POST"])
@csrf.exempt
@limiter.limit("10 per minute")  # ← tambah ini
@login_required
def cek_stunting():

    # Ambil data — bisa JSON atau form-data (karena ada file upload)
    if request.content_type and 'multipart/form-data' in request.content_type:
        data = request.form
    else:
        data = request.get_json() or {}

    try:
        usia = int(data.get("usia", 0))
        jk = str(data.get("jk", "L"))
        tb_cm = float(data.get("tb_cm", 0))
        bb_kg = float(data.get("bb_kg", 0))

        if usia < 0 or usia > 60:
            return jsonify({"error": "Usia harus 0-60 bulan"}), 400

        if tb_cm <= 0 or bb_kg <= 0:
            return jsonify({"error": "TB dan BB harus lebih dari 0"}), 400

        tbl_tb = WHO_TB_L if jk == "L" else WHO_TB_P
        tbl_bb = WHO_BB_L if jk == "L" else WHO_BB_P

        med_tb, sd_tb = tbl_tb[usia]
        med_bb, sd_bb = tbl_bb[usia]

        z_tb = (tb_cm - med_tb) / sd_tb
        z_bb = (bb_kg - med_bb) / sd_bb

        status_gizi = {
            "tbu": klasifikasi_tbu(z_tb),
            "bbu": klasifikasi_bbu(z_bb)
        }

        hasil_fuzzy = fuzzy_stunting(z_tb, z_bb)

        rekomendasi, catatan = buat_rekomendasi(
            hasil_fuzzy["status"],
            status_gizi,
            z_tb, z_bb, usia, jk
        )

        analisis_ai = (
            f"Anak usia {usia} bulan "
            f"dengan tinggi {tb_cm} cm "
            f"dan berat {bb_kg} kg "
            f"memiliki status {hasil_fuzzy['status']}."
        )

        # ── Upload foto ke Azure jika ada ──
        foto_url = None
        if 'foto' in request.files:
            foto = request.files['foto']
            if foto and foto.filename:
                try:
                    from services.azure_service import upload_foto_anak
                    foto_url = upload_foto_anak(foto)
                except Exception as e:
                    print(f"Warning upload foto: {e}")

        # Simpan ke database
        history = ConsultationHistory(
            user_id=session["user_id"],
            usia_bulan=usia,
            jenis_kelamin=jk,
            tinggi_badan=tb_cm,
            berat_badan=bb_kg,
            status_fuzzy=hasil_fuzzy["status"],
            skor_fuzzy=hasil_fuzzy["skor"],
            foto_url=foto_url
        )

        db.session.add(history)
        db.session.commit()

        return jsonify({
            "z_tb": round(z_tb, 2),
            "z_bb": round(z_bb, 2),
            "status_gizi": status_gizi,
            "fuzzy": hasil_fuzzy,
            "rekomendasi": rekomendasi,
            "catatan_tambahan": catatan,
            "analisis_ai": analisis_ai,
            "foto_url": foto_url
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ==================================================
# CHATBOT
# ==================================================

@api_bp.route("/api/chat", methods=["POST"])
@csrf.exempt
@limiter.limit("30 per minute")
@login_required
def api_chat():

    data = request.get_json() or {}

    pesan_raw = data.get("pesan", "")
    pesan_user = sanitize_xss(pesan_raw)

    if not pesan_user:
        return jsonify({
            "error": "Pesan kosong"
        }), 400

    try:

        pesan_clean = pesan_user.lower().strip()

        if stemmer:
            pesan_stemmed = stemmer.stem(pesan_clean)
        else:
            pesan_stemmed = pesan_clean

        jawaban_ai = None

        match_usia = re.search(r'(\d+)\s*(bulan|bln)', pesan_clean)
        match_tb = re.search(r'(tinggi|tb)\s*(\d+)', pesan_clean)
        match_bb = re.search(r'(berat|bb)\s*(\d+)', pesan_clean)

        if match_tb:
            session["last_tb"] = float(match_tb.group(2))
        if match_bb:
            session["last_bb"] = float(match_bb.group(2))
        if match_usia:
            session["last_usia"] = int(match_usia.group(1))

        if has_any(["halo", "hai"], pesan_clean):
            jawaban_ai = (
                "Halo Ayah/Bunda 🌿 "
                "Ada yang bisa saya bantu terkait stunting?"
            )
        elif has_any(["ciri", "tanda", "gejala"], pesan_clean):
            jawaban_ai = dapatkan_jawaban_kamus("ciri stunting")
        elif has_any(["cegah", "pencegahan"], pesan_clean):
            jawaban_ai = dapatkan_jawaban_kamus("cegah stunting")

        if not jawaban_ai:
            jawaban_ai = (
                "Maaf, saya belum memahami pertanyaan tersebut. "
                "Coba tanyakan mengenai stunting, MPASI, atau gizi anak."
            )

        return jsonify({
            "jawaban": jawaban_ai,
            "text_asli": pesan_user,
            "text_stemming": pesan_stemmed
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500