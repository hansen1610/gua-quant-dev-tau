---
name: project_map_updater
description: Memperbarui dokumen pemetaan/arsitektur proyek yang sudah ada tanpa harus memetakannya dari nol.
---

# Project Map Updater (Pembaruan Peta Proyek)

Skill ini digunakan untuk meng-update dokumen peta arsitektur proyek (misalnya `docs/project_architecture_map.md`) setelah terjadi *refactoring*, penambahan fitur, atau penghapusan kode, sehingga dokumen tetap relevan (*Living Document*).

## Instruksi Eksekusi untuk AI:
1.  **Pahami Konteks Perubahan:** Tanyakan atau analisa apa saja yang baru saja diubah oleh user (misalnya: "pemindahan folder komponen", "penggabungan service backend", "penambahan rute API baru").
2.  **Baca Dokumen Peta Lama:** Gunakan `view_file` untuk membaca file peta arsitektur yang sudah ada (biasanya di folder `docs/`).
3.  **Inspeksi Area Terdampak:** Cek kode sumber/folder yang baru dimodifikasi menggunakan `list_dir` atau `view_file` untuk memastikan struktur terbarunya.
4.  **Targeted Edit (Patching):** Gunakan `replace_file_content` atau `multi_replace_file_content` pada dokumen peta arsitektur lama untuk:
    *   Menghapus referensi file/folder yang sudah hilang/dipindah.
    *   Menambahkan deskripsi folder/file baru.
    *   Menyesuaikan narasi alur kerja/arsitektur yang berubah.
5.  **Output:** Berikan ringkasan ringkas kepada user mengenai bagian mana saja dari dokumen yang telah diperbarui. Jangan merombak seluruh dokumen jika tidak diperlukan.
