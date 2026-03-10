---
name: project_mapper
description: Menganalisa sebuah proyek dari nol dan membuat dokumen arsitektur dan pemetaan direktori yang komprehensif.
---

# Project Mapper (Pembuat Peta Proyek dari Nol)

Skill ini digunakan untuk memetakan keseluruhan direktori dan file dalam sebuah proyek, kemudian menyusun sebuah dokumen arsitektur (biasanya di `docs/project_architecture_map.md`).

## Instruksi Eksekusi untuk AI:
1.  **Observasi Awal:** Gunakan tool `run_command` (misalnya `tree /F /A > tree.txt` atau eksekusi `dir /s /b`) dan `list_dir` untuk memahami struktur utama (High-Level) dari proyek.
2.  **Identifikasi File Kunci:** Cari dan gunakan tool `view_file` pada file-file sentral yang mendefinisikan proyek (cth: `package.json`, `docker-compose.yml`, `main.py`, `app.js`, `index.html`, `requirements.txt`).
3.  **Analisis Peran Direktori:** Untuk setiap folder utama (seperti `src/`, `services/`, `components/`, `app/`), baca minimal 1-2 file inti di dalamnya untuk menyimpulkan tujuan direktori tersebut.
4.  **Generasi Dokumen Output:** Buat file markdown (direkomendasikan di `docs/project_architecture_map.md`) menggunakan `write_to_file` yang memuat struktur berikut:
    *   **Deskripsi Proyek (High-Level):** Apa tujuan aplikasi ini dan stack teknologinya.
    *   **Struktur Direktori (Tree):** Berikan visualisasi tree sederhana.
    *   **Pemetaan Direktori & File Inti:** Jelaskan *untuk apa* file/folder tersebut dibuat (bukan hanya terjemahan nama, tapi fungsionalitasnya).
    *   **Alur Komunikasi/Data:** (Opsional) Jelaskan bagaimana komponen A berbicara dengan komponen B.
5.  **Batasan:** Jangan mencoba membaca *semua* file jika proyek terlalu besar. Fokus pada abstraksi tingkat tinggi dan fungsi-fungsi inti.
