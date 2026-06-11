# 🌿 TumbuhCerah — Sistem Deteksi Stunting Berbasis Logika Fuzzy Mamdani

> Aplikasi web edukasi dan deteksi dini stunting pada anak usia 0–60 bulan menggunakan metode **Fuzzy Mamdani** dengan standar antropometri **WHO Child Growth Standards**.

---

## 📋 Deskripsi

**TumbuhCerah** adalah aplikasi berbasis Flask yang membantu orang tua, kader posyandu, dan tenaga kesehatan melakukan **skrining awal risiko stunting** secara cepat dan mudah. Sistem menerima input berupa tinggi badan, berat badan, usia, dan jenis kelamin anak, lalu menghitung Z-score berdasarkan tabel WHO dan menjalankan inferensi Fuzzy Mamdani untuk menghasilkan keputusan: **Stunting**, **Risiko Stunting**, atau **Normal**.

Selain deteksi, aplikasi juga menyajikan konten edukasi lengkap tentang stunting — definisi, penyebab, tanda-tanda, dan langkah pencegahan — agar orang tua memahami konteks di balik hasil pemeriksaan.

---

## ✨ Fitur Utama

- **Kalkulator Z-score otomatis** — menggunakan tabel median dan standar deviasi WHO 0–60 bulan untuk laki-laki dan perempuan
- **Inferensi Fuzzy Mamdani** — 6 himpunan fuzzy, 6 rule base, agregasi MAX-MIN, defuzzifikasi weighted average
- **Penjelasan AI** — hasil deteksi diperkaya dengan penjelasan kontekstual dari Claude API (Anthropic) dalam bahasa Indonesia yang ramah orang tua
- **Halaman edukasi** — informasi tentang stunting, penyebab, tanda, dan pencegahan berbasis 1.000 HPK
- **Poster informatif** — poster HTML lengkap berisi seluruh informasi logika fuzzy dan edukasi stunting
- **Responsif** — tampilan optimal di desktop maupun mobile

---

## 🗂️ Struktur Proyek

```
stunting/
├── app.py                  # Backend Flask + logika fuzzy + tabel WHO
└── templates/
    └── index.html          # Frontend: edukasi + form + hasil + AI explanation
```

---

## ⚙️ Instalasi & Menjalankan

### Prasyarat

- Python 3.8+
- pip

### Langkah

```bash
# 1. Clone repositori
git clone https://github.com/username/tumbuhcerah.git
cd tumbuhcerah

# 2. Buat virtual environment (opsional tapi disarankan)
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

# 3. Install dependensi
pip install flask

# 4. Jalankan aplikasi
python app.py
```

Buka browser dan akses: **http://127.0.0.1:5000**

---

## 🧮 Cara Penggunaan

1. Buka halaman utama — baca konten edukasi stunting
2. Gulir ke bagian **"Cek Status Stunting Anak Anda"**
3. Isi form:
   - **Usia anak** (dalam bulan, rentang 0–60)
   - **Jenis kelamin** (Laki-laki / Perempuan)
   - **Tinggi badan** (cm)
   - **Berat badan** (kg)
4. Klik **Periksa Sekarang**
5. Sistem menampilkan:
   - Status: Stunting / Risiko Stunting / Normal
   - Z-score TB/U dan BB/U
   - Skor defuzzifikasi
   - Penjelasan dan saran dari AI

---

## 🔬 Metodologi: Fuzzy Mamdani

### 1. Perhitungan Z-Score WHO

Z-score dihitung menggunakan tabel median dan standar deviasi WHO berdasarkan usia (bulan) dan jenis kelamin:

```
Z-score = (nilai_anak − median_WHO) / SD_WHO
```

Tabel mencakup **TB/U** dan **BB/U** untuk laki-laki dan perempuan, usia **0 hingga 60 bulan**.

---

### 2. Variabel Input & Himpunan Fuzzy

#### TB/U (Tinggi Badan per Usia)

| Himpunan          | Fungsi Keanggotaan                                                               |
| ----------------- | -------------------------------------------------------------------------------- |
| **Sangat Pendek** | `μ = 1` jika z ≤ −3; `μ = (−2 − z)` jika −3 < z < −2; `μ = 0` jika z ≥ −2        |
| **Pendek**        | `μ = (z + 3)` jika −3 < z < −2; `μ = (−1 − z)` jika −2 ≤ z < −1; `μ = 0` lainnya |
| **Normal**        | `μ = 1` jika −2 ≤ z ≤ 2; `μ = 0` lainnya                                         |

#### BB/U (Berat Badan per Usia)

| Himpunan        | Fungsi Keanggotaan                                                               |
| --------------- | -------------------------------------------------------------------------------- |
| **Gizi Buruk**  | `μ = 1` jika z ≤ −3; `μ = (−2 − z)` jika −3 < z < −2; `μ = 0` jika z ≥ −2        |
| **Gizi Kurang** | `μ = (z + 3)` jika −3 < z < −2; `μ = (−1 − z)` jika −2 ≤ z < −1; `μ = 0` lainnya |
| **Gizi Normal** | `μ = 1` jika −2 ≤ z ≤ 1; `μ = 0` lainnya                                         |

---

### 3. Rule Base (6 Aturan)

| #   | IF TB/U       | AND BB/U    | THEN Output         | Operator |
| --- | ------------- | ----------- | ------------------- | -------- |
| R1  | Sangat Pendek | — (apapun)  | **Stunting**        | `μ(sp)`  |
| R2  | Pendek        | Gizi Kurang | **Stunting**        | `min`    |
| R3  | Pendek        | Gizi Buruk  | **Stunting**        | `min`    |
| R4  | Pendek        | Gizi Normal | **Risiko Stunting** | `min`    |
| R5  | Normal        | Gizi Kurang | **Risiko Stunting** | `min`    |
| R6  | Normal        | Gizi Normal | **Normal**          | `min`    |

---

### 4. Agregasi (Metode MAX)

```python
stunting = max(r1, r2, r3)
risiko   = max(r4, r5)
normal   = r6
```

---

### 5. Defuzzifikasi (Weighted Average)

Setiap output diberi bobot numerik:

| Output          | Bobot |
| --------------- | ----- |
| Stunting        | 1.0   |
| Risiko Stunting | 0.5   |
| Normal          | 0.0   |

```python
total   = (stunting × 1.0) + (risiko × 0.5) + (normal × 0.0)
pembagi = stunting + risiko + normal
skor    = total / pembagi
```

---

### 6. Keputusan Akhir

| Skor             | Keputusan             |
| ---------------- | --------------------- |
| skor > 0.7       | ⚠️ **Stunting**       |
| 0.3 < skor ≤ 0.7 | △ **Risiko Stunting** |
| skor ≤ 0.3       | ✓ **Normal**          |

---

## 🌐 Alur Sistem

```
Input (TB cm, BB kg, Usia bulan, Jenis Kelamin)
        ↓
Lookup Tabel WHO → Hitung Z-score TB/U dan BB/U
        ↓
Fuzzifikasi → 6 Himpunan Fuzzy (TB/U × BB/U)
        ↓
Inferensi Mamdani → 6 Rule Base (MIN per rule)
        ↓
Agregasi → MAX per kategori output
        ↓
Defuzzifikasi → Weighted Average → Skor 0.0–1.0
        ↓
Keputusan: Stunting / Risiko Stunting / Normal
        ↓
Penjelasan AI (Claude API) dalam Bahasa Indonesia
```

---

## 📊 Referensi Tabel WHO (Penggalan)

Tabel lengkap 0–60 bulan tersedia di `app.py`. Berikut contoh beberapa usia kunci:

### Laki-laki

| Usia     | Median TB (cm) | SD TB | Median BB (kg) | SD BB |
| -------- | -------------- | ----- | -------------- | ----- |
| 0 bulan  | 49.9           | 1.89  | 3.35           | 0.43  |
| 6 bulan  | 67.6           | 2.28  | 7.93           | 0.74  |
| 12 bulan | 75.7           | 2.44  | 9.62           | 0.85  |
| 24 bulan | 87.8           | 2.67  | 11.68          | 1.00  |
| 36 bulan | 97.1           | 2.87  | 13.24          | 1.13  |
| 60 bulan | 112.4          | 3.26  | 15.96          | 1.39  |

### Perempuan

| Usia     | Median TB (cm) | SD TB | Median BB (kg) | SD BB |
| -------- | -------------- | ----- | -------------- | ----- |
| 0 bulan  | 49.1           | 1.86  | 3.23           | 0.40  |
| 6 bulan  | 65.7           | 2.26  | 7.25           | 0.69  |
| 12 bulan | 74.0           | 2.46  | 8.95           | 0.81  |
| 24 bulan | 86.4           | 2.73  | 11.24          | 1.00  |
| 36 bulan | 96.2           | 2.97  | 13.12          | 1.18  |
| 60 bulan | 112.9          | 3.43  | 16.99          | 1.56  |

---

## 🛠️ Teknologi

| Komponen             | Teknologi                                         |
| -------------------- | ------------------------------------------------- |
| Backend              | Python 3, Flask                                   |
| Logika Fuzzy         | Implementasi manual (tanpa library eksternal)     |
| Standar Antropometri | WHO Child Growth Standards 2006                   |
| Frontend             | HTML5, CSS3, JavaScript (Vanilla)                 |
| Tipografi            | Fraunces (Google Fonts), DM Sans                  |
| AI Explanation       | Anthropic Claude API (`claude-sonnet-4-20250514`) |

---

## 📦 Dependensi

```txt
flask
```

> Tidak ada dependensi fuzzy library eksternal. Seluruh logika Mamdani diimplementasikan secara native di `app.py`.

---

## ⚠️ Disclaimer

Aplikasi ini bersifat **informatif dan edukatif** sebagai alat skrining awal. Hasil yang ditampilkan **bukan diagnosis medis resmi**. Konsultasikan selalu dengan dokter anak, ahli gizi, atau tenaga kesehatan terlatih untuk penanganan lebih lanjut.

---

## 📚 Referensi

- WHO. (2006). _WHO Child Growth Standards: Length/height-for-age, weight-for-age, weight-for-length, weight-for-height and body mass index-for-age_. World Health Organization.
- Kemenkes RI. (2023). _Survei Status Gizi Indonesia (SSGI) 2023_. Kementerian Kesehatan Republik Indonesia.
- Kemenkes RI. (2020). _Peraturan Menteri Kesehatan No. 2 Tahun 2020 tentang Standar Antropometri Anak_.
- Mamdani, E. H., & Assilian, S. (1975). An experiment in linguistic synthesis with a fuzzy logic controller. _International Journal of Man-Machine Studies_, 7(1), 1–13.

---

## 👨‍💻 Kontribusi

Pull request dan issue sangat terbuka. Untuk perubahan besar, buka issue terlebih dahulu untuk mendiskusikan apa yang ingin diubah.

---

<p align="center">
  Dibuat dengan ❤️ untuk generasi Indonesia yang sehat dan cerdas<br>
  <strong>TumbuhCerah</strong> · Edukasi & Deteksi Stunting
</p>
"# CI/CD test" 
