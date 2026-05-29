import requests
import re
import json
import random
from flask import Flask, render_template, request, jsonify, session

# --- IMPORT LIBRARY SASTRAWI UNTUK NLP LOKAL ---
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory

app = Flask(__name__, 
            template_folder='../frontend', 
            static_folder='../frontend')

# WAJIB: Secret key agar fitur Flask Session (Memori Jangka Pendek Chat) aktif
app.secret_key = 'tumbuh_cerah_secret_key_untuk_memori_chat'

# Inisialisasi Sastrawi Stemmer
factory = StemmerFactory()
stemmer = factory.create_stemmer()


# ======================================================
# MEMBACA BASIS PENGETAHUAN DARI FILE JSON EXTERNAL
# ======================================================
try:
    with open('kamus_gizi.json', 'r', encoding='utf-8') as file:
        KAMUS_GIZI = json.load(file)
except Exception as e:
    print(f"Gagal memuat file kamus_gizi.json: {str(e)}")
    KAMUS_GIZI = {}


# ======================================================
# FUNGSI PEMBANTU UTAMA
# ======================================================
def dapatkan_jawaban_kamus(key_kamus):
    data_jawaban = KAMUS_GIZI.get(key_kamus)
    if isinstance(data_jawaban, list):
        return random.choice(data_jawaban)
    return data_jawaban

def has_any(kata_list, teks):
    """Cek apakah salah satu kata dalam list ada di teks."""
    return any(kata in teks for kata in kata_list)

def has_all(kata_list, teks):
    """Cek apakah semua kata dalam list ada di teks."""
    return all(kata in teks for kata in kata_list)


# ======================================================
# FUNGSI KEANGGOTAAN FUZZY MAMDANI (Z-SCORE INDEKS WHO)
# ======================================================
def sangat_pendek(z):
    if z <= -3: return 1.0
    elif -3 < z < -2: return -2 - z
    return 0.0

def pendek(z):
    if -3 < z < -2: return z + 3
    elif -2 <= z < -1: return -1 - z
    return 0.0

def normal_tb(z):
    return 1.0 if -2 <= z <= 2 else 0.0

def gizi_buruk(z):
    if z <= -3: return 1.0
    elif -3 < z < -2: return -2 - z
    return 0.0

def gizi_kurang(z):
    if -3 < z < -2: return z + 3
    elif -2 <= z < -1: return -1 - z
    return 0.0

def gizi_normal(z):
    return 1.0 if -2 <= z <= 1 else 0.0


# ======================================================
# LOGIKA PACKING MESIN FUZZY MAMDANI (MEMPERBAIKI NAMEERROR)
# ======================================================
def fuzzy_stunting(tb_u, bb_u):
    tb_sp = sangat_pendek(tb_u)
    tb_p = pendek(tb_u)
    tb_n = normal_tb(tb_u)

    bb_sb = gizi_buruk(bb_u)
    bb_k = gizi_kurang(bb_u)
    bb_n = gizi_normal(bb_u)

    r1 = tb_sp
    r2 = min(tb_p, bb_k)
    r3 = min(tb_p, bb_sb)
    r4 = min(tb_p, bb_n)
    r5 = min(tb_n, bb_k)
    r6 = min(tb_n, bb_n)

    stunting = max(r1, r2, r3)
    risiko = max(r4, r5)
    normal = r6

    pembagi = stunting + risiko + normal
    if pembagi == 0:
        return {"status": "Tidak Terdefinisi", "skor": 0, "stunting": 0, "risiko": 0, "normal": 0}

    skor = (stunting * 1 + risiko * 0.5) / pembagi

    if skor > 0.7: status = "Stunting"
    elif skor > 0.3: status = "Risiko Stunting"
    else: status = "Normal"

    return {
        "status": status,
        "skor": round(skor, 4),
        "stunting": round(stunting, 4),
        "risiko": round(risiko, 4),
        "normal": round(normal, 4)
    }


# ======================================================
# KLASIFIKASI STANDAR KEMENKES RI
# ======================================================
def klasifikasi_bbu(z):
    if z < -3: return "Berat Badan Sangat Kurang"
    elif -3 <= z < -2: return "Berat Badan Kurang"
    elif -2 <= z <= 1: return "Berat Badan Normal"
    else: return "Risiko Berat Badan Lebih"

def klasifikasi_tbu(z):
    if z < -3: return "Sangat Pendek (Severely Stunted)"
    elif -3 <= z < -2: return "Pendek (Stunted)"
    elif -2 <= z <= 3: return "Normal"
    else: return "Tinggi"


# ======================================================
# GENERATOR REKOMENDASI KLINIS DASAR KEMENKES
# ======================================================
def buat_rekomendasi(status_fuzzy, status_gizi, z_tb, z_bb, usia, jenis_kelamin):
    rekomendasi = {"tindakan_segera": [], "pola_makan": [], "pemantauan": [], "kapan_ke_dokter": []}

    if status_fuzzy == "Stunting":
        rekomendasi["tindakan_segera"] = [
            "Segera bawa anak ke dokter anak atau puskesmas untuk evaluasi menyeluruh.",
            "Minta rujukan ke ahli gizi anak untuk perencanaan diet terapi.",
            "Periksa kemungkinan penyakit penyerta (infeksi kronis, anemia, dll).",
            "Ikuti program Pemberian Makanan Tambahan (PMT) di posyandu setempat."
        ]
        rekomendasi["pola_makan"] = [
            "Tingkatkan asupan protein hewani: telur, daging, ikan, ayam setiap hari.",
            "Berikan makanan kaya zat besi: hati ayam/sapi, bayam, kacang-kacangan.",
            "Pastikan anak mendapat asupan kalsium: susu, keju, tahu, tempe."
        ]
        rekomendasi["pemantauan"] = [
            "Timbang dan ukur tinggi badan setiap bulan di posyandu.",
            "Catat perkembangan dalam buku KIA secara rutin."
        ]
        rekomendasi["kapan_ke_dokter"] = [
            "SEGERA ke dokter — kondisi ini memerlukan penanganan medis.",
            "Jangan tunda meski anak terlihat aktif dan ceria."
        ]
    elif status_fuzzy == "Risiko Stunting":
        rekomendasi["tindakan_segera"] = [
            "Konsultasi ke bidan atau petugas gizi di puskesmas dalam 1-2 minggu ke depan.",
            "Lakukan pemeriksaan darah sederhana untuk cek anemia."
        ]
        rekomendasi["pola_makan"] = [
            "Tingkatkan kualitas MPASI dengan lebih banyak protein hewani.",
            "Berikan makanan bergizi tinggi 3x makan utama + 2x snack bergizi."
        ]
        rekomendasi["pemantauan"] = [
            "Timbang berat badan setiap bulan di posyandu.",
            "Ukur tinggi badan setiap 3 bulan."
        ]
        rekomendasi["kapan_ke_dokter"] = [
            "Ke dokter jika berat badan tidak naik dalam 2 bulan berturut-turut."
        ]
    else:
        rekomendasi["tindakan_segera"] = [
            "Pertahankan pola asuh dan gizi yang sudah baik.",
            "Tetap rutin ke posyandu setiap bulan untuk pemantauan."
        ]
        rekomendasi["pola_makan"] = [
            "Lanjutkan pola makan bergizi seimbang: karbohidrat, protein, lemak, sayur, buah."
        ]
        rekomendasi["pemantauan"] = [
            "Timbang dan ukur tinggi badan setiap bulan di posyandu."
        ]
        rekomendasi["kapan_ke_dokter"] = [
            "Ke dokter saat jadwal imunisasi rutin atau jika berat badan tiba-tiba turun."
        ]

    catatan_tambahan = []
    if usia < 6:
        catatan_tambahan.append(f"Untuk usia {usia} bulan: ASI eksklusif adalah prioritas utama. Jangan beri MPASI sebelum usia 6 bulan.")
    elif usia < 24:
        catatan_tambahan.append(f"Untuk usia {usia} bulan: Lanjutkan ASI sambil beri MPASI bergizi, tepat waktu, dan aman.")

    return rekomendasi, catatan_tambahan


# ======================================================
# STANDAR DATA TABEL ANTROPOMETRI WHO (0-60 BULAN)
# ======================================================
WHO_TB_L = {
    0: [49.9, 1.89], 1: [54.7, 1.95], 2: [58.4, 2.0], 3: [61.4, 2.05],
    4: [63.9, 2.1], 5: [65.9, 2.12], 6: [67.6, 2.18], 7: [69.2, 2.21],
    8: [70.6, 2.25], 9: [72.0, 2.27], 10: [73.3, 2.31], 11: [74.5, 2.33],
    12: [75.7, 2.37], 13: [76.9, 2.39], 14: [78.0, 2.43], 15: [79.1, 2.46],
    16: [80.2, 2.5], 17: [81.2, 2.54], 18: [82.3, 2.57], 19: [83.2, 2.6],
    20: [84.2, 2.64], 21: [85.1, 2.67], 22: [86.0, 2.71], 23: [86.9, 2.74],
    24: [87.8, 2.78], 25: [88.0, 2.81], 26: [88.8, 2.85], 27: [89.6, 2.88],
    28: [90.4, 2.92], 29: [91.2, 2.95], 30: [91.9, 2.99], 31: [92.7, 3.02],
    32: [93.4, 3.06], 33: [94.1, 3.1], 34: [94.8, 3.13], 35: [95.4, 3.17],
    36: [96.1, 3.21], 37: [96.7, 3.24], 38: [97.4, 3.28], 39: [98.0, 3.32],
    40: [98.6, 3.36], 41: [99.2, 3.4], 42: [99.9, 3.44], 43: [100.4, 3.48],
    44: [101.0, 3.52], 45: [101.6, 3.56], 46: [102.2, 3.6], 47: [102.8, 3.64],
    48: [103.3, 3.68], 49: [103.9, 3.72], 50: [104.4, 3.76], 51: [105.0, 3.8],
    52: [105.6, 3.85], 53: [106.1, 3.89], 54: [106.7, 3.93], 55: [107.2, 3.97],
    56: [107.8, 4.02], 57: [108.3, 4.06], 58: [108.9, 4.11], 59: [109.4, 4.15],
    60: [110.0, 4.2]
}

WHO_TB_P = {
    0: [49.1, 1.86], 1: [53.7, 1.95], 2: [57.1, 2.0], 3: [59.8, 2.05],
    4: [62.1, 2.1], 5: [64.0, 2.13], 6: [65.7, 2.18], 7: [67.3, 2.22],
    8: [68.7, 2.27], 9: [70.1, 2.31], 10: [71.5, 2.36], 11: [72.8, 2.4],
    12: [74.0, 2.44], 13: [75.2, 2.49], 14: [76.4, 2.53], 15: [77.5, 2.58],
    16: [78.6, 2.63], 17: [79.7, 2.68], 18: [80.7, 2.72], 19: [81.7, 2.77],
    20: [82.7, 2.82], 21: [83.7, 2.87], 22: [84.6, 2.92], 23: [85.5, 2.97],
    24: [86.4, 3.02], 25: [86.6, 3.07], 26: [87.4, 3.12], 27: [88.3, 3.17],
    28: [89.1, 3.22], 29: [89.9, 3.27], 30: [90.7, 3.32], 31: [91.4, 3.37],
    32: [92.2, 3.43], 33: [92.9, 3.48], 34: [93.6, 3.53], 35: [94.4, 3.59],
    36: [95.1, 3.65], 37: [95.7, 3.7], 38: [96.4, 3.76], 39: [97.1, 3.82],
    40: [97.7, 3.88], 41: [98.4, 3.94], 42: [99.0, 4.0], 43: [99.7, 4.06],
    44: [100.3, 4.12], 45: [100.9, 4.18], 46: [101.5, 4.25], 47: [102.1, 4.31],
    48: [102.7, 4.37], 49: [103.3, 4.44], 50: [103.9, 4.5], 51: [104.5, 4.57],
    52: [105.0, 4.64], 53: [105.6, 4.71], 54: [106.2, 4.77], 55: [106.7, 4.84],
    56: [107.3, 4.91], 57: [107.8, 4.98], 58: [108.4, 5.05], 59: [108.9, 5.12],
    60: [109.4, 5.19]
}

WHO_BB_L = {
    0: [3.3, 0.45], 1: [4.5, 0.55], 2: [5.6, 0.63], 3: [6.4, 0.7],
    4: [7.0, 0.75], 5: [7.5, 0.79], 6: [7.9, 0.83], 7: [8.3, 0.87],
    8: [8.6, 0.9], 9: [8.9, 0.93], 10: [9.2, 0.96], 11: [9.4, 0.99],
    12: [9.6, 1.02], 13: [9.9, 1.05], 14: [10.1, 1.08], 15: [10.3, 1.11],
    16: [10.5, 1.13], 17: [10.7, 1.16], 18: [10.9, 1.19], 19: [11.1, 1.22],
    20: [11.3, 1.25], 21: [11.5, 1.28], 22: [11.8, 1.31], 23: [12.0, 1.34],
    24: [12.2, 1.37], 25: [12.4, 1.39], 26: [12.5, 1.41], 27: [12.7, 1.43],
    28: [12.9, 1.45], 29: [13.1, 1.47], 30: [13.3, 1.49], 31: [13.5, 1.51],
    32: [13.7, 1.53], 33: [13.8, 1.55], 34: [14.0, 1.57], 35: [14.2, 1.59],
    36: [14.3, 1.61], 37: [14.5, 1.63], 38: [14.7, 1.65], 39: [14.8, 1.67],
    40: [15.0, 1.69], 41: [15.2, 1.71], 42: [15.3, 1.73], 43: [15.5, 1.76],
    44: [15.7, 1.78], 45: [15.8, 1.8], 46: [16.0, 1.82], 47: [16.2, 1.84],
    48: [16.3, 1.86], 49: [16.5, 1.88], 50: [16.7, 1.9], 51: [16.8, 1.92],
    52: [17.0, 1.94], 53: [17.2, 1.96], 54: [17.3, 1.98], 55: [17.5, 2.0],
    56: [17.7, 2.02], 57: [17.8, 2.04], 58: [18.0, 2.06], 59: [18.2, 2.08],
    60: [18.3, 2.1]
}

WHO_BB_P = {
    0: [3.2, 0.43], 1: [4.2, 0.52], 2: [5.1, 0.6], 3: [5.8, 0.67],
    4: [6.4, 0.73], 5: [6.9, 0.78], 6: [7.3, 0.82], 7: [7.6, 0.86],
    8: [7.9, 0.9], 9: [8.2, 0.94], 10: [8.5, 0.97], 11: [8.7, 1.01],
    12: [8.9, 1.05], 13: [9.2, 1.08], 14: [9.4, 1.12], 15: [9.6, 1.15],
    16: [9.8, 1.19], 17: [10.0, 1.22], 18: [10.2, 1.26], 19: [10.4, 1.29],
    20: [10.6, 1.33], 21: [10.9, 1.36], 22: [11.1, 1.4], 23: [11.3, 1.43],
    24: [11.5, 1.47], 25: [11.7, 1.51], 26: [11.9, 1.54], 27: [12.1, 1.58],
    28: [12.3, 1.62], 29: [12.5, 1.65], 30: [12.7, 1.69], 31: [12.9, 1.73],
    32: [13.1, 1.77], 33: [13.3, 1.81], 34: [13.5, 1.85], 35: [13.7, 1.89],
    36: [13.9, 1.93], 37: [14.0, 1.97], 38: [14.2, 2.01], 39: [14.4, 2.05],
    40: [14.6, 2.09], 41: [14.8, 2.13], 42: [15.0, 2.17], 43: [15.2, 2.21],
    44: [15.3, 2.25], 45: [15.5, 2.29], 46: [15.7, 2.34], 47: [15.9, 2.38],
    48: [16.1, 2.42], 49: [16.3, 2.46], 50: [16.4, 2.51], 51: [16.6, 2.55],
    52: [17.0, 2.59], 53: [17.0, 2.64], 54: [17.2, 2.68], 55: [17.3, 2.73],
    56: [17.5, 2.77], 57: [17.7, 2.82], 58: [17.9, 2.86], 59: [18.0, 2.91],
    60: [18.2, 2.95]
}


# ======================
# ROUTING FLASK UTAMA
# ======================
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/chat", methods=["GET"])
def chat():
    session.clear()
    return render_template("chat.html")


@app.route("/cek", methods=["POST"])
def cek_stunting():
    data = request.get_json()
    try:
        usia = int(data.get("usia", 0))
        jk = data.get("jk", "L")
        tb_cm = float(data.get("tb_cm", 0))
        bb_kg = float(data.get("bb_kg", 0))

        if usia < 0 or usia > 60: 
            return jsonify({"error": "Usia harus 0-60 bulan"}), 400
        if tb_cm <= 0 or bb_kg <= 0: 
            return jsonify({"error": "Tinggi dan berat badan harus > 0"}), 400

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
            z_tb, z_bb, 
            usia, jk
        )

        # ── RACIKAN TEKS ANALISIS AI KUSTOM UNTUK HALAMAN CHECKER ──
        jk_teks = "Laki-laki" if jk == "L" else "Perempuan"
        if hasil_fuzzy["status"] == "Stunting":
            kondisi_teks = "terindikasi mengalami <strong>Stunting (Sangat Pendek/Pendek)</strong>"
            solusi_teks = "Fokus utama saat ini adalah menggempur asupan <strong>Protein Hewani</strong> (seperti telur minimal 1-2 butir sehari, hati ayam, atau ikan lokal) di setiap porsi makannya."
        elif hasil_fuzzy["status"] == "Risiko Stunting":
            kondisi_teks = "berada pada kategori <strong>Risiko Stunting</strong>"
            solusi_teks = "Jangan lengah ya Bun, segera perbaiki kualitas MPASI/makanannya dengan meningkatkan porsi protein hewani and zat besi agar tingginya segera mengejar grafik normal."
        else:
            kondisi_teks = "dalam kondisi <strong>Normal dan Sehat</strong>"
            solusi_teks = "Pertahankan pola asuh dan gizi seimbang yang sudah baik ini. Tetap rutin ke Posyandu setiap bulan untuk memantau tumbuh kembang si kecil."

        analisis_ai_teks = (
            f"Halo Ayah/Bunda! Berdasarkan analisis sistem pakar gizi TumbuhCerah, anak {jk_teks} usia {usia} bulan "
            f"dengan tinggi {tb_cm} cm {kondisi_teks} dengan skor fuzzy sebesar {round(hasil_fuzzy['skor'], 2)}.<br><br>"
            f"💡 <strong>Catatan Konselor Virtual:</strong> {solusi_teks}<br><br>"
            f"Jika butuh tips lebih detail mengenai menu MPASI atau penanganan khusus, Anda bisa langsung ngobrol "
            f"dengan saya di halaman <strong>Fitur Chatbot Konsultasi AI</strong> ya! 🌿"
        )

        return jsonify({
            "z_tb": round(z_tb, 2),
            "z_bb": round(z_bb, 2),
            "median_tb": med_tb,
            "median_bb": med_bb,
            "status_gizi": status_gizi,
            "fuzzy": hasil_fuzzy,
            "rekomendasi": rekomendasi,
            "catatan_tambahan": catatan,
            "analisis_ai": analisis_ai_teks  # --- KIRIMKAN VARIABEL BARU INI KE FRONTEND ---
        })
        
    except Exception as e:
        print(f"Error pada kalkulator backend: {str(e)}")
        return jsonify({"error": f"Data tidak valid: {str(e)}"}), 400

# ======================================================
# FUNGSI INTENT MATCHING MODULAR
# ======================================================
def match_intent(pesan_clean, pesan_stemmed):
    """
    Mencocokkan pesan user ke intent kamus.
    Mengembalikan key kamus atau None jika tidak cocok.
    """
    # ── SAPAAN & BASA-BASI ──────────────────────────────────────────────────
    if has_any(["terima kasih", "makasih", "thanks", "thx"], pesan_clean):
        if has_any(["dokter", "dok", "bapak", "ibu"], pesan_clean):
            return "terima kasih dokter"
        return "terima kasih"
    if has_any(["oke", "ok ", "sip", "siap"], pesan_clean):
        return "oke"
    if has_any(["baik", "alhamdulillah", "mantap", "bagus sekali"], pesan_clean):
        return "baik"
    if has_any(["halo", "hai", "hi ", "assalamualaikum", "selamat"], pesan_clean):
        if "pagi" in pesan_clean:    return "pagi"
        if "siang" in pesan_clean:   return "siang"
        if "sore" in pesan_clean:    return "sore"
        if "malam" in pesan_clean:   return "malam"
        return "halo"

    # ── TENTANG APLIKASI ────────────────────────────────────────────────────
    if has_any(["tumbuhcerah", "tumbuh cerah", "aplikasi ini", "tentang app", "cara kerja", "cara pakai", "cara guna", "fitur"], pesan_clean):
        if has_any(["cara", "fitur", "pakai", "guna", "kerja"], pesan_clean):
            return "cara kerja aplikasi"
        return "tentang tumbuhcerah"
    if has_any(["siapa kamu", "siapa anda", "apa kamu", "kamu siapa", "kamu apa", "anda siapa"], pesan_clean):
        return "tentang tumbuhcerah"

    # ── TOPIK STUNTING SPESIFIK Terlebih Dahulu (Urutan Cerdas Anti-Bentrokan) ──
    if has_any(["ciri", "tanda", "gejala", "risiko stunting", "indikator"], pesan_stemmed):
        return "ciri stunting"
    if has_any(["gtm", "gerakan tutup mulut", "mogok makan", "anak tidak mau makan", "susah makan", "lesu"], pesan_clean):
        return "anak gtm"
    if has_any(["penyebab", "sebab", "faktor", "kenapa", "mengapa", "pemicu", "akibat dari"], pesan_stemmed):
        if "stunting" in pesan_stemmed or "pendek" in pesan_stemmed:
            return "sebab stunting"
    if has_any(["cegah", "prevent", "hindari", "antisipasi", "kurangi risiko"], pesan_stemmed):
        return "cegah stunting"
    if has_any(["sembuh", "pulih", "sembuhkan", "obati stunting", "bisa normal", "bisa sembuh"], pesan_stemmed):
        return "sembuh stunting"
    if has_any(["mitos", "hoaks", "salah kaprah", "fakta stunting"], pesan_stemmed):
        if has_any(["pendek", "tinggi", "stunting", "gen", "keturunan", "genetik"], pesan_stemmed):
            return "mitos pendek"
    if has_any(["data stunting", "angka stunting", "prevalensi", "statistik stunting", "indonesia stunting"], pesan_clean):
        return "stunting data indonesia"
    if has_any(["intervensi", "program stunting", "penanganan stunting", "kebijakan stunting"], pesan_clean):
        return "intervensi stunting"
    if has_any(["wasting", "kurus akut", "gizi akut"], pesan_clean):
        return "apa itu wasting"
    if has_any(["gizi buruk", "sam ", "severe acute", "sangat kurus"], pesan_clean):
        return "gizi buruk"
    if has_any(["stunting lahir", "lahir stunting", "baru lahir stunting", "iugr", "intrauterine"], pesan_clean):
        return "stunting lahir"

    # ── DEFINISI UMUM (Diletakkan di Bawah Topik Spesifik) ──────────────────────
    if has_any(["apa itu stunting", "apa stunting", "pengertian stunting", "definisi stunting", "arti stunting", "maksud stunting"], pesan_clean):
        return "apa stunting"

    # ── 1000 HPK ────────────────────────────────────────────────────────────
    if has_any(["1000 hari", "1000hpk", "hpk", "seribu hari", "hari pertama kehidupan"], pesan_clean):
        return "1000 hpk"

    # ── ASI ─────────────────────────────────────────────────────────────────
    if has_any(["asi eksklusif", "asi exclusive", "6 bulan asi", "asi saja"], pesan_clean):
        return "asi eksklusif"
    if has_any(["manfaat asi", "kegunaan asi", "fungsi asi", "kenapa asi", "mengapa asi penting"], pesan_clean):
        return "manfaat asi"
    if has_any(["kolostrum", "susu pertama", "asi pertama", "cairan kuning"], pesan_clean):
        return "kolostrum"
    if has_any(["mitos asi", "hoaks asi", "salah kaprah asi"], pesan_clean):
        return "mitos asi"
    if has_any(["asi tidak keluar", "asi sedikit", "asi kering", "produksi asi", "asi lancar", "lancarkan asi", "pelancar asi"], pesan_clean):
        return "asi tidak keluar"
    if has_any(["menyapih", "sapih", "berhenti menyusui", "stop asi", "lepas asi"], pesan_clean):
        return "menyapih anak"
    if has_any(["air minum bayi", "boleh minum air", "kapan minum air", "bayi minum air putih"], pesan_clean):
        return "air minum bayi"

    # ── MPASI ───────────────────────────────────────────────────────────────
    if has_any(["mulai mpasi", "kapan mpasi", "umur mpasi", "usia mpasi", "awal mpasi"], pesan_clean):
        return "mulai mpasi"
    if has_any(["mpasi terlalu dini", "mpasi sebelum 6", "mpasi 4 bulan", "mpasi 5 bulan", "mpasi cepat"], pesan_clean):
        return "mpasi terlalu dini"
    if has_any(["mpasi terlambat", "mpasi telat", "mpasi lewat 6", "mpasi setelah 6"], pesan_clean):
        return "mpasi terlambat"
    if has_any(["tekstur mpasi", "tekstur makanan bayi", "haluskan mpasi", "konsistensi mpasi", "puree", "finger food"], pesan_clean):
        return "tekstur mpasi"
    if has_any(["porsi mpasi", "jumlah mpasi", "berapa banyak mpasi", "takaran mpasi"], pesan_clean):
        return "porsi mpasi"
    if has_any(["jadwal makan bayi", "waktu makan bayi", "jam makan bayi", "frekuensi makan"], pesan_clean):
        return "jadwal makan bayi"
    if has_any(["mitos mpasi", "hoaks mpasi", "boleh mpasi", "pantangan mpasi"], pesan_clean):
        return "mitos mpasi"
    if_any = has_any(["cara masak mpasi", "olah mpasi", "cara buat mpasi", "masak mpasi", "pengolahan mpasi"], pesan_clean)
    if if_any: return "cara masak mpasi"
    if has_any(["minyak mpasi", "minyak dalam mpasi", "tambah minyak", "vco mpasi", "minyak kelapa"], pesan_clean):
        return "minyak dalam mpasi"
    if has_any(["garam mpasi", "garam bayi", "garam anak", "kapan boleh garam"], pesan_clean):
        return "garam mpasi"
    if has_any(["gula mpasi", "gula bayi", "gula anak", "kapan boleh gula", "manis bayi"], pesan_clean):
        return "gula mpasi"
    if has_any(["tepung mpasi", "jenis tepung", "karbohidrat mpasi", "beras merah mpasi", "oat bayi"], pesan_clean):
        return "tepung mpasi"
    if has_any(["resep 6 bulan", "menu 6 bulan", "mpasi 6 bulan", "contoh mpasi 6"], pesan_clean):
        return "resep mpasi 6 bulan"
    if has_any(["resep 9 bulan", "menu 9 bulan", "mpasi 9 bulan", "contoh mpasi 9", "mpasi 10 bulan", "mpasi 11 bulan"], pesan_clean):
        return "resep mpasi 9 bulan"
    if has_any(["menu 12 bulan", "menu 1 tahun", "mpasi 12 bulan", "makanan 1 tahun", "menu 18 bulan", "menu 2 tahun"], pesan_clean):
        return "menu sehat 12 bulan"
    if has_any(["menu 6 bulan"], pesan_clean):
        return "menu sehat 6 bulan"
    if has_any(["menu 9 bulan", "menu 10 bulan", "menu 11 bulan"], pesan_clean):
        return "menu sehat 9 bulan"

    # ── MASALAH MAKAN UTAMA ──────────────────────────────────────────────────
    if has_any(["picky eater", "pilih makan", "pilih-pilih", "pemilih makanan", "tidak mau sayur"], pesan_clean):
        return "picky eater"
    if has_any(["camilan", "snack sehat", "makanan selingan", "cemilan anak"], pesan_clean):
        return "camilan sehat"

    # ── PROTEIN & MAKANAN SPESIFIK ──────────────────────────────────────────
    if has_any(["protein hewani", "protein hewan", "pentingnya protein", "fungsi protein"], pesan_clean):
        return "protein hewani"
    if has_any(["makanan cegah", "makanan stunting", "makanan anti stunting", "makanan terbaik anak"], pesan_clean):
        return "makan cegah"
    if has_any(["telur anak", "berapa telur", "manfaat telur", "telur untuk bayi"], pesan_clean):
        return "telur untuk anak"
    if has_any(["ikan anak", "manfaat ikan", "ikan untuk bayi", "ikan untuk balita", "ikan mpasi"], pesan_clean):
        return "ikan untuk anak"
    if has_any(["hati ayam", "hati sapi", "lever"], pesan_clean):
        return "hati ayam"
    if has_any(["sayuran anak", "sayur bayi", "sayur mpasi", "manfaat sayur", "jenis sayur anak"], pesan_clean):
        return "sayuran anak"
    if has_any(["buah anak", "buah bayi", "buah mpasi", "manfaat buah", "jenis buah anak"], pesan_clean):
        return "buah untuk anak"
    if has_any(["makanan berserat", "serat anak", "serat makanan", "fiber anak"], pesan_clean):
        return "makanan berserat"
    if has_any(["makanan ultra proses", "junk food", "makanan instan", "makanan kemasan", "snack kemasan"], pesan_clean):
        return "makanan ultra proses"
    if has_any(["minyak ikan", "suplemen omega", "fish oil"], pesan_clean):
        return "minyak ikan"

    # ── ZAT GIZI MIKRO ──────────────────────────────────────────────────────
    if has_any(["zat besi", "fe ", "ferum", "hemoglobin", "anemia besi"], pesan_clean):
        return "zat besi"
    if has_any(["kalsium", "ca ", "tulang anak", "kuat tulang", "keropos"], pesan_clean):
        return "kalsium anak"
    if has_any(["vitamin d", "vit d", "rickets", "rakitis", "sinar matahari pagi"], pesan_clean):
        return "vitamin d anak"
    if has_any(["zinc", "seng ", "mineral pertumbuhan"], pesan_clean):
        return "zinc seng"
    if has_any(["yodium", "iodium", "iodine", "garam beryodium", "gondok"], pesan_clean):
        return "yodium anak"
    if has_any(["omega 3", "omega-3", "dha", "epa ", "lemak otak", "asam lemak"], pesan_clean):
        return "omega 3 anak"
    if has_any(["vitamin anak", "vitamin a", "suplemen", "sirup nafsu makan", "penambah nafsu"], pesan_clean):
        return "vitamin anak"
    if has_any(["tablet tambah darah", "ttd", "suplemen ibu hamil", "tablet besi ibu"], pesan_clean):
        return "tablet tambah darah"

    # ── KONDISI & PENYAKIT ──────────────────────────────────────────────────
    if has_any(["anemia", "pucat", "lemas anak", "kekurangan darah", "hb rendah"], pesan_clean):
        return "anemia anak"
    if has_any(["kurang gizi", "malnutrisi", "gizi buruk anak", "kekurangan gizi"], pesan_clean):
        return "kurang gizi"
    if has_any(["gemuk anak", "obesitas anak", "overweight anak", "kelebihan berat"], pesan_clean):
        return "gemuk anak"
    if has_any(["diare", "mencret", "buang air besar cair", "bab cair"], pesan_clean):
        return "diare anak"
    if has_any(["ispa", "batuk pilek", "flu anak", "infeksi saluran napas", "radang tenggorokan"], pesan_clean):
        return "ispa anak"
    if has_any(["cacing", "cacingan", "obat cacing", "parasit", "cacing perut"], pesan_clean):
        return "cacing anak"
    if has_any(["bblr", "berat lahir rendah", "prematur", "bayi kecil lahir"], pesan_clean):
        return "bblr berat"
    if has_any(["alergi makanan", "alergi anak", "reaksi alergi", "gatal setelah makan"], pesan_clean):
        if has_any(["susu", "laktosa", "susu sapi"], pesan_clean):
            return "alergi susu sapi"
        return "alergi makanan"
    if has_any(["intoleransi laktosa", "tidak tahan susu", "perut kembung susu", "minum susu diare"], pesan_clean):
        return "intoleransi laktosa"
    if has_any(["sembelit", "konstipasi", "bab keras", "susah bab", "tidak bab"], pesan_clean):
        return "sembelit anak"
    if has_any(["celiac", "gluten", "gandum alergi"], pesan_clean):
        return "penyakit celiac"
    if has_any(["gumoh", "regurgitasi", "sering muntah bayi", "bayi muntah terus"], pesan_clean):
        return "gumoh bayi"
    if has_any(["bayi rewel", "bayi nangis terus", "bayi menangis", "kolik", "rewel malam"], pesan_clean):
        return "bayi rewel"

    # ── OTAK & PERKEMBANGAN ─────────────────────────────────────────────────
    if has_any(["otak", "cerdas", "iq", "kecerdasan", "kognitif", "memori anak"], pesan_stemmed):
        return "otak cerdas"
    if has_any(["perkembangan anak", "tumbuh kembang", "milestone", "tahap perkembangan", "motorik"], pesan_clean):
        return "perkembangan anak"
    if has_any(["stimulasi anak", "rangsang anak", "stimulus bayi", "bermain anak", "stimulasi otak"], pesan_clean):
        return "stimulasi anak"
    if has_any(["tidur anak", "jam tidur", "kebutuhan tidur", "hormon pertumbuhan tidur", "sleep"], pesan_clean):
        return "jam tidur anak"
    if has_any(["aktivitas fisik", "olahraga anak", "gerak anak", "bermain aktif", "tummy time"], pesan_clean):
        return "aktivitas fisik anak"

    # ── IBU HAMIL & GIZI IBU ─────────────────────────────────────────────────
    if has_any(["gizi ibu hamil", "makan ibu hamil", "nutrisi ibu hamil", "hamil gizi"], pesan_clean):
        return "gizi ibu hamil"
    if has_any(["stres ibu", "depresi ibu", "baby blues", "depresi pasca", "mental ibu", "kesehatan ibu"], pesan_clean):
        return "stres ibu"
    if has_any(["pola asuh", "pengasuhan", "cara asuh", "parenting gizi"], pesan_clean):
        return "pola asuh gizi"

    # ── POSYANDU & PROGRAM ───────────────────────────────────────────────────
    if has_any(["posyandu", "puskesmas gizi", "kunjungan posyandu"], pesan_clean):
        if has_any(["manfaat", "pentingnya", "kegunaan", "kenapa posyandu"], pesan_clean):
            return "posyandu manfaat"
        return "posyandu"
    if has_any(["pmt", "pemberian makanan tambahan", "makanan tambahan anak", "biskuit pmt"], pesan_clean):
        return "pmt"
    if has_any(["imunisasi", "vaksin", "vaksinasi", "suntik anak"], pesan_clean):
        return "imunisasi anak"
    if has_any(["buku kia", "kms", "kartu menuju sehat", "buku pink"], pesan_clean):
        return "buku kia"
    if has_any(["bantuan pemerintah", "pkh", "bpnt", "subsidi gizi", "program gizi"], pesan_clean):
        return "bantuan pemerintah"
    if has_any(["dokter gizi", "kapan ke dokter", "konsultasi dokter", "spesialis gizi", "sp.gk", "sp.a"], pesan_clean):
        return "dokter gizi"

    # ── PEMANTAUAN PERTUMBUHAN GRAFIK ─────────────────────────────────────────
    if has_any(["timbang anak", "timbang berat", "pantau pertumbuhan", "monitoring tumbuh"], pesan_clean):
        return "timbang anak"
    if has_any(["baca zscore", "z score", "zscore", "z-score", "cara baca grafik", "sd grafik", "baca kms"], pesan_clean):
        return "baca zscore"
    if has_any(["berat badan ideal", "bb ideal anak", "bb normal anak", "berat normal"], pesan_clean):
        return "berat badan ideal"
    if has_any(["tinggi badan ideal", "tinggi ideal anak", "tb ideal", "potensi tinggi", "tinggi dewasa", "mid parental"], pesan_clean):
        return "tinggi badan ideal"
    if has_any(["pertumbuhan normal", "kenaikan bb", "kenaikan berat normal", "naik berat normal", "berapa naik bb"], pesan_clean):
        return "pertumbuhan normal"
    if has_any(["growth faltering", "bb tidak naik", "berat stagnan", "bb stagnan", "bb turun", "berat tidak naik"], pesan_clean):
        return "growth faltering"

    # ── SUSU & LIABILITAS LAINNYA ────────────────────────────────────────────
    if has_any(["susu formula", "sufor", "susu sapi formula", "formula bayi"], pesan_clean):
        return "susu formula"
    if has_any(["kolesterol anak", "lemak anak", "kuning telur kolesterol", "takut lemak"], pesan_clean):
        return "kolesterol anak"
    if has_any(["sanitasi", "air bersih", "cuci tangan", "phbs", "lingkungan sehat", "jamban", "babs"], pesan_clean):
        return "sanitasi stunting"

    return None


# ======================================================
# API CHAT ENGINE UTAMA — STATEFUL SYSTEM
# ======================================================
@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json()
    pesan_user = data.get("pesan", "")
    
    if not pesan_user:
        return jsonify({"error": "Pesan tidak boleh kosong"}), 400

    try:
        pesan_clean = pesan_user.lower().strip()
        pesan_stemmed = stemmer.stem(pesan_clean)
        jawaban_ai = None

        # ── 1. Deteksi komponen data dari pesan menggunakan Regex ──────────────────
        match_usia = (re.search(r'(\d+)\s*(?:bulan|bln)', pesan_clean) or
                      re.search(r'(?:umur|usia)\s*(\d+)', pesan_clean))
        match_tb   = (re.search(r'(?:tinggi|tb|panjang)\s*(\d+(?:\.\d+)?)', pesan_clean) or
                      re.search(r'(\d+(?:\.\d+)?)\s*(?:cm)', pesan_clean))
        match_bb   = (re.search(r'(?:berat|bb)\s*(\d+(?:\.\d+)?)', pesan_clean) or
                      re.search(r'(\d+(?:\.\d+)?)\s*(?:kg)', pesan_clean))

        # Tangkap angka murni sebagai usia (susulan chat)
        if not match_usia and re.fullmatch(r'\d{1,2}', pesan_clean):
            angka_murni = int(pesan_clean)
            if 0 <= angka_murni <= 60:
                pesan_clean = f"{angka_murni} bulan"
                match_usia = re.search(r'(\d+)\s*bulan', pesan_clean)

        # ── 2. Simpan ke Memori Sesi (Session) ──────────────────────────────────
        if match_tb:   session['last_tb']   = float(match_tb.group(1))
        if match_bb:   session['last_bb']   = float(match_bb.group(1))
        if match_usia: session['last_usia'] = int(match_usia.group(1))
        if has_any(["perempuan", "putri", "cewek", "wanita"], pesan_clean):
            session['last_jk'] = "P"
        elif has_any(["laki", "putra", "cowok", "pria"], pesan_clean):
            session['last_jk'] = "L"

        # ── 3. Hitung Z-Score jika data akumulasi lengkap ─────────────────────────
        if 'last_tb' in session and 'last_usia' in session:
            usia  = session['last_usia']
            tb_cm = session['last_tb']
            bb_teks = f"{session['last_bb']} kg" if 'last_bb' in session else "belum diinput"
            jk    = session.get('last_jk', 'L')
            jk_teks = "Perempuan" if jk == "P" else "Laki-laki"

            tbl_tb = WHO_TB_L if jk == "L" else WHO_TB_P
            if usia in tbl_tb:
                med_tb, sd_tb = tbl_tb[usia]
                z_tb = (tb_cm - med_tb) / sd_tb
                status_tbu = klasifikasi_tbu(z_tb)

                if z_tb < -3:
                    kondisi = "<strong>Sangat Pendek (Severely Stunted)</strong>. Kondisi ini memerlukan intervensi gizi medis segera. Segera bawa ke dokter anak atau Puskesmas terdekat."
                    saran = "Prioritaskan protein hewani <strong>setiap hari</strong> (telur, ikan, hati ayam, daging) dan segera konsultasikan ke dokter anak untuk penanganan lebih lanjut."
                elif -3 <= z_tb < -2:
                    kondisi = "<strong>Pendek (Stunted)</strong>. Anak terindikasi stunting. Intervensi gizi segera diperlukan."
                    saran = "Perbanyak lauk protein hewani setiap kali makan, rutin pantau di Posyandu, dan konsultasikan ke ahli gizi."
                elif z_tb > 3:
                    kondisi = "<strong>Sangat Tinggi</strong>. Ini umumnya baik, namun perlu dipastikan tidak ada kondisi medis tertentu."
                    saran = "Tetap pantau pertumbuhan secara rutin dan konsultasikan ke dokter anak jika ada kekhawatiran."
                else:
                    kondisi = "<strong>Normal dan Sehat</strong>! Tinggi badan anak sudah sesuai grafik standar WHO untuk usianya. 🎉"
                    saran = "Pertahankan pola makan bergizi seimbang dan pantau terus setiap bulan di Posyandu."

                jawaban_ai = (
                    f"Terima kasih datanya Bun/Yah! Berikut hasil analisis saya:<br><br>"
                    f"📋 <strong>Data Anak:</strong> {jk_teks} | Usia {usia} bulan | TB {tb_cm} cm | BB {bb_teks}<br>"
                    f"📊 <strong>Z-Score TB/U:</strong> {round(z_tb, 2)} SD<br>"
                    f"🏷️ <strong>Status Pertumbuhan:</strong> {status_tbu}<br><br>"
                    f"📌 <strong>Kondisi saat ini:</strong> {kondisi}<br><br>"
                    f"💡 <strong>Saran:</strong> {saran}"
                )
                session.clear()

        # Kasus jika baru menginput TB saja tapi belum menginput Usia
        elif match_tb and not match_usia and 'last_usia' not in session:
            jawaban_ai = (
                f"Saya mendeteksi tinggi badan <strong>{session.get('last_tb', '?')} cm</strong>. 📏<br><br>"
                "Untuk menghitung Z-score dan mengetahui apakah tinggi badan tersebut normal, "
                "saya perlu tahu <strong>usia anak dalam bulan</strong>. "
                "Ketik langsung angka usianya, contoh: *18 bulan* atau cukup ketik *18*."
            )

        # ── 4. Jalankan Intent Matching Modular ──────────────────────────────────
        if not jawaban_ai:
            kunci_cocok = match_intent(pesan_clean, pesan_stemmed)
            if kunci_cocok:
                jawaban_ai = dapatkan_jawaban_kamus(kunci_cocok)

        # ── 5. Fallback Loop Kamus Tradisional ──────────────────────────────────
        if not jawaban_ai:
            for kunci, jawaban in KAMUS_GIZI.items():
                komponen_kunci = kunci.split()
                if len(komponen_kunci) >= 2 and has_all(komponen_kunci, pesan_stemmed):
                    jawaban_ai = dapatkan_jawaban_kamus(kunci)
                    break

        # ── 6. Fallback Teks Alternatif Akhir ────────────────────────────────────
        if not jawaban_ai:
            jawaban_ai = dapatkan_jawaban_kamus("tidak tahu") or (
                "Maaf, saya belum memahami pertanyaan tersebut. 😔<br><br>"
                "Anda bisa menanyakan hal-hal seperti:<br>"
                "• <em>Apa itu stunting?</em><br>"
                "• <em>Makanan apa yang mencegah stunting?</em><br>"
                "• <em>Anak saya umur 18 bulan tinggi 70 cm, apakah normal?</em><br>"
                "• <em>Bagaimana cara memulai MPASI?</em><br>"
                "• <em>Apa manfaat ASI eksklusif?</em>"
            )
            
        return jsonify({
            "jawaban": jawaban_ai,
            "text_asli": pesan_user,
            "text_stemming": pesan_stemmed
        })
        
    except Exception as e:
        print(f"=== ERROR: {str(e)} ===")
        return jsonify({"error": f"Server Error: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True)