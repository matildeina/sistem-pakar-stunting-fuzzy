# 🌿 TumbuhCerah — Sistem Deteksi Stunting Berbasis Fuzzy Mamdani

> Aplikasi web deteksi dini stunting pada anak usia 0–60 bulan menggunakan **Fuzzy Mamdani**, standar antropometri **WHO**, dan arsitektur **Cloud Native** (AWS + Azure).

---

## 📋 Deskripsi

**TumbuhCerah** adalah aplikasi berbasis Flask yang membantu orang tua, kader posyandu, dan tenaga kesehatan melakukan **skrining awal risiko stunting** secara cepat dan mudah. Sistem menerima input berupa tinggi badan, berat badan, usia, jenis kelamin, dan foto anak, lalu menghitung Z-score berdasarkan tabel WHO dan menjalankan inferensi Fuzzy Mamdani untuk menghasilkan keputusan: **Stunting**, **Risiko Stunting**, atau **Normal**.

Foto anak disimpan secara aman di **Azure Blob Storage** sebagai bagian dari arsitektur multi-cloud.

---

## ✨ Fitur Utama

- **Kalkulator Z-score otomatis** — tabel median dan SD WHO 0–60 bulan untuk laki-laki dan perempuan
- **Inferensi Fuzzy Mamdani** — 6 himpunan fuzzy, 6 rule base, agregasi MAX-MIN, defuzzifikasi weighted average
- **Upload foto anak** — tersimpan di Azure Blob Storage (multi-cloud)
- **Chatbot NLP** — menggunakan Sastrawi stemmer untuk memproses pertanyaan bahasa Indonesia
- **Autentikasi aman** — register, login, logout dengan session management
- **Dashboard riwayat** — histori konsultasi per user
- **Security hardening** — CSRF, bcrypt, rate limiting, XSS filter, SQL injection protection

---

## 🏗️ Arsitektur Cloud

---

## ⚙️ Instalasi Lokal

### Prasyarat
- Python 3.11+
- Docker & Docker Compose
- Git

### Langkah

```bash
# 1. Clone repositori
git clone https://github.com/matildeina/sistem-pakar-stunting-fuzzy.git
cd sistem-pakar-stunting-fuzzy

# 2. Buat file .env
cp .env.example .env
# Edit .env sesuai konfigurasi lokal

# 3. Jalankan dengan Docker
cd docker
docker compose up -d --build

# 4. Akses aplikasi
# Buka browser: http://localhost
```

### Tanpa Docker

```bash
cd backend
pip install -r requirements.txt
python app.py
# Akses: http://127.0.0.1:5000
```

---

## 🚀 Deployment ke AWS EC2

```bash
# 1. SSH ke EC2
ssh -i tumbuhcerah-key.pem ubuntu@IP_EC2

# 2. Install Docker
sudo apt update
sudo apt install -y docker.io docker-compose-v2 git
sudo usermod -aG docker ubuntu
newgrp docker

# 3. Clone repo
git clone https://github.com/matildeina/sistem-pakar-stunting-fuzzy.git
cd sistem-pakar-stunting-fuzzy

# 4. Buat .env
nano .env

# 5. Jalankan
cd docker
docker compose up -d --build
```

---

## 🔄 CI/CD Pipeline

Pipeline otomatis via **GitHub Actions** (`.github/workflows/deploy.yml`):

---

## 🔐 Implementasi Keamanan

| No | Fitur | Implementasi |
|----|-------|-------------|
| 1 | Password Hashing | Flask-Bcrypt |
| 2 | Session Management | Flask Session + HttpOnly Cookie |
| 3 | Validasi Input | Server-side validation |
| 4 | SQL Injection Protection | SQLAlchemy ORM |
| 5 | XSS Protection | Custom xss_filter.py |
| 6 | CSRF Protection | Flask-WTF CSRFProtect |
| 7 | Rate Limiting | Flask-Limiter (10/menit login) |
| 8 | Brute Force Prevention | FailedLogin tracking + IP block |
| 9 | Role-Based Access Control | Belum diimplementasikan (planned enhancement)|
| 10 | Secure File Upload | Validasi ekstensi + Azure Blob |
| 11 | Security Logging | Custom logger → security.log |
| 12 | Reverse Proxy | Nginx dengan security headers |

---

## 🧮 Metodologi Fuzzy Mamdani

### Variabel Input

**TB/U (Tinggi Badan per Usia)**

| Himpunan | Fungsi Keanggotaan |
|----------|--------------------|
| Sangat Pendek | μ = 1 jika z ≤ −3 |
| Pendek | μ = (z+3) jika −3 < z < −2 |
| Normal | μ = 1 jika −2 ≤ z ≤ 2 |

**BB/U (Berat Badan per Usia)**

| Himpunan | Fungsi Keanggotaan |
|----------|--------------------|
| Gizi Buruk | μ = 1 jika z ≤ −3 |
| Gizi Kurang | μ = (z+3) jika −3 < z < −2 |
| Gizi Normal | μ = 1 jika −2 ≤ z ≤ 1 |

### Rule Base

| # | IF TB/U | AND BB/U | THEN |
|---|---------|----------|------|
| R1 | Sangat Pendek | — | Stunting |
| R2 | Pendek | Gizi Kurang | Stunting |
| R3 | Pendek | Gizi Buruk | Stunting |
| R4 | Pendek | Gizi Normal | Risiko Stunting |
| R5 | Normal | Gizi Kurang | Risiko Stunting |
| R6 | Normal | Gizi Normal | Normal |

### Keputusan Akhir

| Skor | Status |
|------|--------|
| > 0.7 | ⚠️ Stunting |
| 0.3 – 0.7 | △ Risiko Stunting |
| ≤ 0.3 | ✓ Normal |

---

## 🛠️ Teknologi

| Komponen | Teknologi |
|----------|-----------|
| Backend | Python 3.11, Flask, Gunicorn |
| Database | SQLite (dev), MySQL (prod schema) |
| AI Engine | Fuzzy Mamdani + NLP Sastrawi |
| Frontend | HTML5, CSS3, JavaScript |
| Container | Docker, Docker Compose |
| Reverse Proxy | Nginx |
| Cloud Compute | AWS EC2 (ap-southeast-2) |
| Object Storage | Azure Blob Storage |
| CI/CD | GitHub Actions |
| Security | Flask-WTF, Flask-Bcrypt, Flask-Limiter |

---

## 🌐 Live Demo

**URL:** http://32.236.142.31

---

## 📦 Environment Variables

Buat file `.env` di root project:

```env
SECRET_KEY=your_secret_key
DATABASE_URL=sqlite:///tumbuh_cerah.db
DOCKER_USERNAME=your_dockerhub_username
AZURE_CONNECTION_STRING=your_azure_connection_string
AZURE_CONTAINER_NAME=foto-anak
```

---

## ⚠️ Disclaimer

Aplikasi ini bersifat **informatif dan edukatif** sebagai alat skrining awal. Hasil yang ditampilkan **bukan diagnosis medis resmi**. Konsultasikan selalu dengan dokter anak atau tenaga kesehatan terlatih.

---

## 📚 Referensi

- WHO. (2006). *WHO Child Growth Standards*. World Health Organization.
- Kemenkes RI. (2023). *Survei Status Gizi Indonesia (SSGI) 2023*.
- Kemenkes RI. (2020). *Peraturan Menteri Kesehatan No. 2 Tahun 2020*.
- Mamdani, E. H., & Assilian, S. (1975). An experiment in linguistic synthesis with a fuzzy logic controller.

---

<p align="center">
  Dibuat dengan ❤️ untuk generasi Indonesia yang sehat dan cerdas<br>
  <strong>TumbuhCerah</strong> · Deteksi Stunting Berbasis Cloud & AI
</p>