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