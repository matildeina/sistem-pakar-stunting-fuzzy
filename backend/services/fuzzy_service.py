import json
import random
import os

# Membaca basis pengetahuan JSON secara aman
KAMUS_GIZI = {}
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
json_path = os.path.join(base_dir, 'data', 'kamus_gizi.json')

try:
    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='utf-8') as file:
            KAMUS_GIZI = json.load(file)
except Exception as e:
    print(f"Gagal memuat file kamus_gizi.json: {str(e)}")

def dapatkan_jawaban_kamus(key_kamus):
    data_jawaban = KAMUS_GIZI.get(key_kamus)
    if isinstance(data_jawaban, list):
        return random.choice(data_jawaban)
    return data_jawaban

def has_any(kata_list, teks):
    return any(kata in teks for kata in kata_list)

def has_all(kata_list, teks):
    return all(kata in teks for kata in kata_list)

# Fungsi Keanggotaan Fuzzy
def sangat_pendek(z):
    return 1.0 if z <= -3 else (-2 - z if -3 < z < -2 else 0.0)

def pendek(z):
    return z + 3 if -3 < z < -2 else (-1 - z if -2 <= z < -1 else 0.0)

def normal_tb(z):
    return 1.0 if -2 <= z <= 2 else 0.0

def gizi_buruk(z):
    return 1.0 if z <= -3 else (-2 - z if -3 < z < -2 else 0.0)

def gizi_kurang(z):
    return z + 3 if -3 < z < -2 else (-1 - z if -2 <= z < -1 else 0.0)

def gizi_normal(z):
    return 1.0 if -2 <= z <= 1 else 0.0

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