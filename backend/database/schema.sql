-- ======================================================
-- SCRIPT SKEMA DATABASE MUTASI PRODUCTION (MYSQL 8)
-- MATAKULIAH: KEAMANAN JARINGAN
-- ======================================================

CREATE DATABASE IF NOT EXISTS tumbuh_cerah_db;
USE tumbuh_cerah_db;

-- 1. Tabel Utama Pengguna (Users)
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('User', 'Admin') DEFAULT 'User',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. Tabel Riwayat Konsultasi Antropometri (Integritas Referensi)
CREATE TABLE IF NOT EXISTS consultation_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    usia_bulan INT NOT NULL,
    jenis_kelamin ENUM('L', 'P') NOT NULL,
    tinggi_badan DECIMAL(5,2) NOT NULL,
    berat_badan DECIMAL(5,2) NOT NULL,
    status_fuzzy VARCHAR(50) NOT NULL,
    skor_fuzzy DECIMAL(5,4) NOT NULL,
    foto_url VARCHAR(500) NULL COMMENT 'URL foto anak di Azure Blob Storage',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. Tabel Audit Log Aktivitas & Deteksi Serangan
CREATE TABLE IF NOT EXISTS activity_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    action VARCHAR(255) NOT NULL,
    ip_address VARCHAR(45) NOT NULL,
    user_agent VARCHAR(255) NOT NULL,
    severity ENUM('INFO', 'WARNING', 'CRITICAL') DEFAULT 'INFO',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. Tabel Monitoring Kegagalan Otentikasi (Anti-Brute Force)
CREATE TABLE IF NOT EXISTS failed_logins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username_attempted VARCHAR(50) NOT NULL,
    ip_address VARCHAR(45) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;