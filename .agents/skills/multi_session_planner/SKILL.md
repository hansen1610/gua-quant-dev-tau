---
name: multi_session_planner
description: Memecah implementation plan besar menjadi beberapa sesi prompt siap pakai untuk dieksekusi oleh AI di sesi percakapan terpisah agar hemat konteks memori.
---

# Multi-Session Planner (Pemandu Sesi Eksekusi)

Skill ini berguna ketika ukuran perubahan sistem sangat besar atau kompleks (misalnya: major refactoring, migrasi architecture, atau menulis banyak microservices baru sekaligus). Karena AI (LLM) memiliki batasan context window (batas "ingatan"), memecahnya menjadi beberapa sesi chat terpisah adalah strategi terbaik.

## Kapan Skill ini Ter-Trigger (Dipanggil):
*   User berkata: "Tolong pecah implementasinya jadi beberapa sesi"
*   User berkata: "Buat panduan pengerjaan per sesi untuk AI"
*   User berkata: "Konteksnya terlalu besar, jadikan 3 sesi terpisah"

## Instruksi Eksekusi untuk AI:
1.  **Analisis Implementation Plan / Task:** Pahami apa gol akhir dari proyek yang sedang direncanakan (misalnya: merujuk pada file `implementation_plan.md` atau `task.md` yang baru dibuat).
2.  **Rancang Pembagian Moduler:** Bagi seluruh pekerjaan menjadi beberapa sesi (ideal 3 hingga 5 sesi max), dengan prinsip:
    *   **Isolasi Kode:** File yang dikerjakan di satu sesi sebisa mungkin tidak overlap (bertumpuk) dengan file di sesi lain untuk mencegah konflik.
    *   **Urutan Logis:** Sesi 1 selalu yang paling mendasar (misal pembuatan folder, boilerplate, copy file dependencies), Sesi tengah adalah logika inti, Sesi pelengkap untuk wiring/konfigurasi infrastruktur pendukung.
3.  **Tulis Prompt Copy-Paste per Sesi:** Untuk HAPUS beban user berpikir ulang, buat blok teks "Prompt untuk Copy-Paste" bagi setiap sesi. Prompt ini *harus*:
    *   Menjelaskan State/Konteks saat ini (apa yang sudah dikerjakan di sesi sebelumnya).
    *   Memberikan instruksi sangat spesifik tanpa ambigu apa file yang harus diedit dan buat di sesi tersebut.
    *   Memberi *constraint* (batasan) tegas: "JANGAN sentuh file X dan Y di sesi ini."
4.  **Aturan Baku Sesi Terakhir (WAJIB):** Sesi paling akhir HARUS selalu berupa "Sesi Review & Integrasi". Di instruksi Sesi Terakhir ini, AI dilarang keras menulis fitur baru. Tugas AI di sesi akhir hanyalah:
    *   Meng-audit import cross-file.
    *   Meng-audit konfigurasi gateway (API, Nginx, Docker) apakah ada port/nama routing yang *mismatch*.
    *   Menguji konsistensi dan menghapus file/folder sampah lama.
5.  **Output:** Dokumentasikan hasil pengerjaan skill ini dalam sebuah file (misal: `docs/panduan_sesi_refactoring.md`) dan berikan ringkasan struktur sesinya saja kepada User.
