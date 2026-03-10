# 🗺️ Pemetaan Direktori & Analisis Eksekusi "Monolith-Lite" (Versi 2)

Dokumen ini memuat pemetaan lengkap struktur direktori saat ini beserta penjelasan fungsi setiap file kunci, dilanjutkan dengan detail langkah teknis (*engineering plan*) untuk mengeksekusi arsitektur Versi 2 ("Monolith-Lite").

---

## 1. Pemetaan Struktur Direktori Saat Ini (Target Peleburan)

Berikut adalah struktur dari 3 servis yang akan dilebur menjadi satu servis baru bernama **`core-engine`**:

### A. `services/backend-api/` (Pintu Utama via API)
Berisi *routing* REST API dan *Websocket* yang melayani request dari Frontend (UI) menggunakan framework **FastAPI**.
*   `Dockerfile` & `requirements.txt`: Instruksi *build* Docker dan dependensi Python (FastAPI, Redis, dll).
*   `app/main.py`: Titik masuk utama FastAPI. Mengatur koneksi *database* (Postgres) dan Redis melalui fungsi `lifespan`. Me-*routing* akses API melalui fitur `app.include_router()`.
*   `app/routes/` (Berisi pemisahan logika API):
    *   `auth.py`: Autentikasi dan login.
    *   `research.py`: Penarikan data *historical* untuk halaman riset.
    *   `risk.py`: Setting batas *drawdown*, stop loss, dll.
    *   `strategy.py`: Manajemen mengaktifkan/mematikan strategi.
    *   `trading.py`: Eksekusi perintah *trade* manual, riwayat order.
    *   `websocket.py`: Sinkronisasi data *real-time* ke React/Next.js UI.

### B. `services/strategy-engine/` (Otak Pengambil Keputusan)
Ini adalah *worker* berjalan di latar belakang (bukan web server) berbasis **Python Asyncio**.
*   `main.py`: Berisi kelas `StrategyCoordinator`. Servis ini "mendengarkan" (*subscribe*) data harga *real-time* dari Redis (dikirim oleh Hummingbot), mengevaluasinya ke algoritma strategi, lalu mempublikasikan (*publish*) sinyal trading kembali ke Redis.
*   `risk_engine.py`: Modul verifikasi sebelum sinyal dikirim ke *exchange* (memastikan batas risiko tidak terlampaui).
*   `strategies/` (Folder berisi algoritma trading siap pakai):
    *   `base_strategy.py`: Kelas dasar *template* (OOP Parent).
    *   `ema_trend.py`, `fibonacci_pullback.py`, `multi_timeframe.py`: Berbagai varian logika trading.
    *   `portfolio_allocation.py`, `regime_detection.py`, `volatility_sizing.py`: Modul *sizing* modal dan probabilitas arah pasar.

### C. `services/monitoring/` (Sistem Pemantauan)
Aplikasi **FastAPI** kedua yang menumpang untuk keperluan pencatatan log *"health check"*.
*   `main.py`: Berisi API (`/api/monitoring/...`) dan `_health_monitor_loop()` (loop interval 30 detik yang mencatat *latency* dan *uptime* ping dari service lain ke Postgres).
*   `streamer.py`: Alat simulasi data market masuk ke sistem (jika koneksi bursa asli mati).
*   `stress_test.py` & `stress_results.log`: Skrip *benchmark* dan hasil uji performa.

---

## 2. Analisis Eksekusi Servis Baru (`core-engine`)

Untuk masuk ke **Versi 2**, kita tidak akan menjalankan 3 *container* secara terpisah. Kita akan membuat servis baru (`services/core-engine/`) yang memadukan ketiga fungsi tersebut menggunakan **FastAPI Lifespan**.

### Apa Saja yang Dikerjakan (Langkah-Langkah *Refactoring*):

1. **Pembuatan Struktur Direktori Baru (`core-engine`)**
   Kita akan menggabungkan semuanya dalam satu struktur modern:
   ```text
   services/core-engine/
   ├── app/
   │   ├── api/          (Eks backend-api/app/routes + monitoring API)
   │   ├── engine/       (Eks strategy-engine coordinator & loop)
   │   ├── strategies/   (Eks strategy-engine/strategies logika)
   │   ├── utils/        (Utility, database pool, redis client)
   │   └── main.py       (Titik lebur utama FastAPI)
   ├── Dockerfile
   └── requirements.txt  (Gabungan library dari ketiga servis)
   ```

2. **Penggabungan File `main.py` (Tantangan Terbesar)**
   Saat ini ada tiga `main.py`. Kita akan menyatukannya ke dalam satu `app/main.py`.
   *   Mekanisme eksekusi: **FastAPI Background Tasks & Lifespan**.
   *   Saat `core-engine` (FastAPI) *startup*, aplikasi akan membuka koneksi *Database* dan Redis (eks dari `backend-api`).
   *   *Setelah* koneksi terbuka, aplikasi akan memanggil `asyncio.create_task(StrategyCoordinator().start())` (eks dari `strategy-engine`).
   *   Lalu aplikasi akan memanggil `asyncio.create_task(_health_monitor_loop())` (eks dari `monitoring`).
   *   Dengan ini, Web Server (API), Loop Trading (Strategy), dan Loop Pemantauan berjalan mulus bersamaan *dalam satu memori RAM (1 container)* secara asinkron (Bebas *blocking*).

3. **Perombakan Routing dan Endpoints (API)**
   *   Seluruh *routes* dari `backend-api` dimuat ulang ke FastAPI instance baru.
   *   *Routes* dari `monitoring` (`/api/monitoring/health_history` dsb) ditambahkan sebagai satu *controller* baru di dalam *core-engine*.

4. **Penghapusan Service Lama di Docker Compose**
   *   Di file `docker-compose.yml`, blok `backend-api`, `strategy-engine`, dan `monitoring` **dihapus**.
   *   Diganti dengan satu blok baru bertitel `core-engine` dengan *port* yang aman, yang memetakan file *build* ke `./services/core-engine`.
   *   Karena lokasinya berada dalam kontainer yang sama, pemanggilan "API internal" kini tergantikan oleh pemanggilan fungsi kelas Python langsung, sehingga sangat memangkas jeda *network latency*.

### Kesimpulan
Secara fundamental, transisi ke "Monolith-Lite" sangat dimungkinkan dan bahkan **sangat menguntungkan untuk performa RAM dan rasio eksekusi** karena menumpuk (stack) *event-loop Asyncio*. Pekerjaan utamanya murni *copy-paste* struktural (*refactoring*) ke dalam wadah `core-engine` baru, dan mengamankan jalur *background_task* agar saat `strategy-engine` terjadi *error* secara logis, ia tidak menumbangkan respons API (menggunakan *try-except wrapper*).
