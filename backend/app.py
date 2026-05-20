from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# ======================
# STANDAR WHO (Median & SD) UNTUK Z-SCORE
# Format: {usia_bulan: [median_tb, sd_tb, median_bb, sd_bb]}
# Sumber: Permenkes No. 2 Tahun 2020 (Standar Antropometri Anak)
# ======================

# TB/U Laki-laki (cm): median, SD
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

# TB/U Perempuan (cm): median, SD
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

# BB/U Laki-laki (kg): median, SD
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

# BB/U Perempuan (kg): median, SD
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
    52: [16.8, 2.59], 53: [17.0, 2.64], 54: [17.2, 2.68], 55: [17.3, 2.73],
    56: [17.5, 2.77], 57: [17.7, 2.82], 58: [17.9, 2.86], 59: [18.0, 2.91],
    60: [18.2, 2.95]
}

# ======================
# FUNGSI MEMBERSHIP (Z-SCORE)
# ======================

def sangat_pendek(z):
    if z <= -3:
        return 1.0
    elif -3 < z < -2:
        return -2 - z
    return 0.0

def pendek(z):
    if -3 < z < -2:
        return z + 3
    elif -2 <= z < -1:
        return -1 - z
    return 0.0

def normal_tb(z):
    return 1.0 if -2 <= z <= 2 else 0.0

def gizi_buruk(z):
    if z <= -3:
        return 1.0
    elif -3 < z < -2:
        return -2 - z
    return 0.0

def gizi_kurang(z):
    if -3 < z < -2:
        return z + 3
    elif -2 <= z < -1:
        return -1 - z
    return 0.0

def gizi_normal(z):
    return 1.0 if -2 <= z <= 1 else 0.0

# ======================
# KLASIFIKASI STATUS GIZI (Permenkes No. 2/2020)
# ======================

def klasifikasi_bbu(z):
    """Klasifikasi BB/U"""
    if z < -3:
        return "Berat Badan Sangat Kurang"
    elif -3 <= z < -2:
        return "Berat Badan Kurang"
    elif -2 <= z <= 1:
        return "Berat Badan Normal"
    else:
        return "Risiko Berat Badan Lebih"

def klasifikasi_tbu(z):
    """Klasifikasi TB/U"""
    if z < -3:
        return "Sangat Pendek (Severely Stunted)"
    elif -3 <= z < -2:
        return "Pendek (Stunted)"
    elif -2 <= z <= 3:
        return "Normal"
    else:
        return "Tinggi"

# ======================
# FUZZY MAMDANI
# ======================

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
        return {
            "status": "Tidak Terdefinisi",
            "skor": 0,
            "stunting": 0,
            "risiko": 0,
            "normal": 0
        }

    skor = (stunting * 1 + risiko * 0.5) / pembagi

    if skor > 0.7:
        status = "Stunting"
    elif skor > 0.3:
        status = "Risiko Stunting"
    else:
        status = "Normal"

    return {
        "status": status,
        "skor": round(skor, 4),
        "stunting": round(stunting, 4),
        "risiko": round(risiko, 4),
        "normal": round(normal, 4)
    }

# ======================
# REKOMENDASI BERDASARKAN STATUS
# ======================

def buat_rekomendasi(status_fuzzy, status_gizi, z_tb, z_bb, usia, jenis_kelamin):
    """Menghasilkan rekomendasi lengkap berdasarkan semua indikator"""

    rekomendasi = {
        "tindakan_segera": [],
        "pola_makan": [],
        "pemantauan": [],
        "kapan_ke_dokter": []
    }

    # --- Berdasarkan status fuzzy stunting ---
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
            "Pastikan anak mendapat asupan kalsium: susu, keju, tahu, tempe.",
            "Hindari makanan manis berlebih yang menurunkan nafsu makan.",
            "Sajikan makanan dalam porsi kecil tapi sering (5-6x/hari).",
            "Tambahkan sumber lemak sehat: minyak kelapa, alpukat, kacang-kacangan."
        ]
        rekomendasi["pemantauan"] = [
            "Timbang dan ukur tinggi badan setiap bulan di posyandu.",
            "Catat perkembangan dalam buku KIA secara rutin.",
            "Pantau perkembangan motorik dan kognitif anak."
        ]
        rekomendasi["kapan_ke_dokter"] = [
            "SEGERA ke dokter — kondisi ini memerlukan penanganan medis.",
            "Jangan tunda meski anak terlihat aktif dan ceria.",
            "Bawa buku KIA saat konsultasi untuk evaluasi tren pertumbuhan."
        ]

    elif status_fuzzy == "Risiko Stunting":
        rekomendasi["tindakan_segera"] = [
            "Konsultasi ke bidan atau petugas gizi di puskesmas dalam 1-2 minggu ke depan.",
            "Lakukan pemeriksaan darah sederhana untuk cek anemia.",
            "Ikuti kelas parenting gizi di posyandu atau puskesmas."
        ]
        rekomendasi["pola_makan"] = [
            "Tingkatkan kualitas MPASI dengan lebih banyak protein hewani.",
            "Berikan makanan bergizi tinggi 3x makan utama + 2x snack bergizi.",
            "Variasikan jenis makanan agar anak tidak bosan.",
            "Tambahkan sumber omega-3: ikan salmon, ikan kembung, teri.",
            "Pastikan anak mendapat ASI atau susu formula yang cukup (jika < 2 tahun)."
        ]
        rekomendasi["pemantauan"] = [
            "Timbang berat badan setiap bulan di posyandu.",
            "Ukur tinggi badan setiap 3 bulan.",
            "Perhatikan tren pertumbuhan — apakah naik sesuai grafik."
        ]
        rekomendasi["kapan_ke_dokter"] = [
            "Ke dokter jika berat badan tidak naik dalam 2 bulan berturut-turut.",
            "Ke dokter jika anak sering sakit (> 2x/bulan), rewel, atau nafsu makan sangat menurun.",
            "Segera ke UGD jika anak tidak mau makan sama sekali lebih dari 2 hari."
        ]

    else:  # Normal
        rekomendasi["tindakan_segera"] = [
            "Pertahankan pola asuh dan gizi yang sudah baik.",
            "Tetap rutin ke posyandu setiap bulan untuk pemantauan."
        ]
        rekomendasi["pola_makan"] = [
            "Lanjutkan pola makan bergizi seimbang: karbohidrat, protein, lemak, sayur, buah.",
            "Variasikan menu agar anak terbiasa dengan beragam makanan bergizi.",
            "Batasi makanan olahan, junk food, dan minuman manis.",
            "Pastikan anak mendapat cukup cairan (air putih)."
        ]
        rekomendasi["pemantauan"] = [
            "Timbang dan ukur tinggi badan setiap bulan di posyandu.",
            "Pantau perkembangan milestone sesuai usia.",
            "Catat vaksinasi dan tumbuh kembang di buku KIA."
        ]
        rekomendasi["kapan_ke_dokter"] = [
            "Ke dokter saat jadwal imunisasi rutin.",
            "Ke dokter jika berat badan tiba-tiba turun atau tidak naik 2 bulan berturut-turut.",
            "Ke dokter jika ada kekhawatiran tentang tumbuh kembang anak."
        ]

    # --- Tambahan berdasarkan status gizi individual ---
    catatan_tambahan = []

    if "Sangat Kurang" in status_gizi.get("bbu", "") or "Sangat Pendek" in status_gizi.get("tbu", ""):
        catatan_tambahan.append(
            "⚠ Kondisi ini termasuk kategori BERAT menurut standar WHO. Penanganan medis segera sangat diperlukan."
        )

    if "Risiko Berat Badan Lebih" in status_gizi.get("bbu", ""):
        catatan_tambahan.append(
            "Meski BB lebih, pastikan TB/U tetap dalam batas normal. Konsultasikan ke dokter untuk evaluasi."
        )

    if usia < 6:
        catatan_tambahan.append(
            f"Untuk usia {usia} bulan: ASI eksklusif adalah prioritas utama. Jangan beri MPASI sebelum usia 6 bulan."
        )
    elif usia < 24:
        catatan_tambahan.append(
            f"Untuk usia {usia} bulan: Lanjutkan ASI sambil beri MPASI bergizi, tepat waktu, dan aman."
        )

    return rekomendasi, catatan_tambahan

# ======================
# ROUTING FLASK
# ======================

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/cek", methods=["POST"])
def cek_stunting():
    data = request.get_json()

    try:
        usia = int(data.get("usia", 0))
        jk = data.get("jk", "L")
        tb_cm = float(data.get("tb_cm", 0))
        bb_kg = float(data.get("bb_kg", 0))

        # Validasi
        if usia < 0 or usia > 60:
            return jsonify({"error": "Usia harus 0-60 bulan"}), 400
        if tb_cm <= 0 or bb_kg <= 0:
            return jsonify({"error": "Tinggi dan berat badan harus > 0"}), 400

        # Ambil data WHO
        tbl_tb = WHO_TB_L if jk == "L" else WHO_TB_P
        tbl_bb = WHO_BB_L if jk == "L" else WHO_BB_P

        med_tb, sd_tb = tbl_tb[usia]
        med_bb, sd_bb = tbl_bb[usia]

        z_tb = (tb_cm - med_tb) / sd_tb
        z_bb = (bb_kg - med_bb) / sd_bb

        # Klasifikasi per indeks (Permenkes No. 2/2020)
        status_gizi = {
            "tbu": klasifikasi_tbu(z_tb),
            "bbu": klasifikasi_bbu(z_bb)
        }

        # Fuzzy Mamdani
        hasil_fuzzy = fuzzy_stunting(z_tb, z_bb)

        # Rekomendasi
        rekomendasi, catatan = buat_rekomendasi(
            hasil_fuzzy["status"],
            status_gizi,
            z_tb, z_bb,
            usia, jk
        )

        return jsonify({
            "z_tb": round(z_tb, 2),
            "z_bb": round(z_bb, 2),
            "median_tb": med_tb,
            "median_bb": med_bb,
            "status_gizi": status_gizi,
            "fuzzy": hasil_fuzzy,
            "rekomendasi": rekomendasi,
            "catatan_tambahan": catatan
        })

    except (KeyError, ValueError, TypeError) as e:
        return jsonify({"error": f"Data tidak valid: {str(e)}"}), 400


# ======================
# RUN
# ======================

if __name__ == "__main__":
    app.run(debug=True)
