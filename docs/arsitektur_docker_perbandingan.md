# 🏗️ Perbandingan 3 Versi Arsitektur Docker (QuantBot)

Dokumen ini menjelaskan 3 opsi arsitektur Docker Compose untuk proyek QuantBot Anda, lengkap dengan analogi sederhana agar mudah dipahami, serta kelebihan dan kekurangannya (*trade-offs*).

---

## 🏎️ Versi 1: Arsitektur "Mobil Balap Lean" (Fokus Eksekusi Utama)

Analogi: **Mobil F1 (Formula 1)**. 
Mobil balap F1 dirancang hanya untuk satu tujuan: **melaju secepat mungkin di lintasan**. Semua beban ekstra (seperti AC, radio tape, kursi penumpang) dibuang agar mobil menjadi sangat ringan dan lincah.

Dalam arsitektur ini, kita membuang semua komponen analitik, AI, dan sistem pencatatan log (Grafana, Loki, ML Engine) yang berat. Kita hanya mempertahankan "mesin inti" agar bot bisa trading.

**Isi Kontainer:**
*   Nginx (Pintu Gerbang)
*   Frontend (Dashboard)
*   Backend API (Logika Utama)
*   Strategy Engine (Otak Trading)
*   Hummingbot (Tangan Eksekutor)
*   Postgres & Redis (Ingatan/Database)

**Trade-offs (Untung-Rugi):**
*   ✅ **Sangat Ringan & Cepat:** Hemat RAM dan CPU. Cocok dijalankan di laptop *development* atau server murah (VPS kecil).
*   ✅ **Lebih Aman Secara *Default*:** Karena komponen sedikit, potensi celah keamanan juga berkurang.
*   ❌ **Minim Fitur Tambahan:** Anda kehilangan "dashboard mewah" untuk melihat grafik performa server yang cantik (Grafana) dan fitur prediksi AI cerdas (ML Engine).
*   ❌ **Debugging Manual:** Jika ada error, Anda harus mengeceknya secara manual lewat Terminal layar hitam (`docker logs`).

---

## 🚌 Versi 2: Arsitektur "Bus Sedang / Monolith-Lite" (Penggabungan Otak)

Analogi: **Bus Sedang (Minibus)**.
Alih-alih menyewa 3 mobil kecil yang berbeda (dengan 3 supir berbeda) untuk membawa rombongan, Anda menyewa 1 bus sedang dengan 1 supir. Lebih hemat bensin dan koordinasi lebih mudah, meski manuvernya tidak selincah mobil kecil.

Dalam arsitektur ini, kita menggabungkan beberapa "otak/servis" Python (`backend-api`, `strategy-engine`, dan `monitoring`) menjadi satu aplikasi besar ("Core Engine").

**Isi Kontainer:**
*   Nginx
*   Frontend
*   **Core Engine (Gabungan Backend + Strategy + Monitoring)**
*   Hummingbot
*   ML Engine (Opsional)
*   Postgres & Redis

**Trade-offs (Untung-Rugi):**
*   ✅ **Hemat *Overhead* Server:** Menjalankan 1 kontainer Python jauh lebih hemat memori ketimbang menjalankan 3 kontainer terpisah. Fitur-fitur utama tetap ada.
*   ❌ **Butuh Bongkar Mesin (Refactoring Code):** Anda harus menulis ulang/menyatukan kode program Anda agar ketiga servis tersebut bisa berjalan bersama di satu tempat. Ini butuh usaha ekstra untuk *developer*.
*   ❌ **Risiko "Satu Sakit, Semua Tumbang":** Jika fitur *monitoring* mengalami *error* atau kehabisan memori, fitur eksekusi trading (`strategy`) di dalamnya akan ikut mati karena mereka berada di bus (kontainer) yang sama.

---

## 🏙️ Versi 3: Arsitektur "Gedung Perusahaan Mewah" (Production Secured)

Analogi: **Gedung Perusahaan Multinasional (Enterprise)**.
Sebuah gedung dengan banyak departemen (Keuangan, HRD, IT, Keamanan). Setiap departemen punya ruangan sendiri. Jika ruangan HRD terbakar, divisi IT tetap bisa bekerja. Namun, agar aman, tidak ada pintu luar dari ruangan departemen langsung ke jalan. Semua harus masuk lewat **Satu Pintu Lobi Utama (Nginx)** yang dijaga satpam.

Di versi ini, kita mempertahankan semua 13 servis (Microservices penuh) agar sistem sangat canggih dan modular, **TETAPI** kita mengamankannya. Tidak ada *service* yang membuka pintunya (port) sembarangan ke internet luar (seperti port 5432 untuk Postgres, atau port 8005 dsb).

**Isi Kontainer:**
*   **FULL 13 Kontainer** (Nginx, Frontend, Backend, Strategy, Hummingbot, ML, Quant Research, Postgres, Redis, Monitoring, Grafana, Loki, Promtail).

**Trade-offs (Untung-Rugi):**
*   ✅ **Sistem Kelas Kakap (*Enterprise-Grade*):** Paling canggih, tangguh, dan sangat teroganisir. Tiap fitur punya ruang isolasi sendiri.
*   ✅ **Keamanan Maksimal:** Walaupun servisnya banyak, hanya Nginx (Port 80/443) yang menghadap ke internet. Segala akses (termasuk ke Grafana) diatur lewat *subdomain/path* di Nginx.
*   ❌ **Sangat Boros *Resource* (RAM/CPU):** Seperti merawat gedung besar, butuh biaya listrik/server yang mahal. Hanya cocok untuk server *Production* kuat (Misal: CPU 4 Core, RAM 8GB atau 16GB++). Tidak cocok dinyalakan terus-menerus di laptop biasa.

---

### 💡 Kesimpulan Rekomendasi
*   **Masa Pembuatan Awal / Dana Terbatas:** Pilih **Versi 1 🏎️**.
*   **Ingin Optimalisasi Ekstrem & Rela Ngoding Ulang:** Pilih **Versi 2 🚌**.
*   **Sistem Sudah Siap Rilis Profesional & Punya Server Kuat:** Pilih **Versi 3 🏙️**.
