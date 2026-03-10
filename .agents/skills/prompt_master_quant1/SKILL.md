---
name: prompt master quant1
description: Blueprint prompt to rebuild the QuantBot institutional trading platform quickly.
---

# Prompt Master: QuantBot Institutional Trading Platform

Use the following prompt format to initialize and rebuild the entire QuantBot ecosystem based on the architecture established by the user.

```markdown
# 1. Project Context & Architecture Overview
Saya ingin membangun sebuah infrastruktur "Institutional Quant Trading Platform" berskala besar yang menggunakan arsitektur microservices berbasis Docker Compose. Sistem ini ditujukan untuk eksekusi algoritma berfrekuensi tinggi (HFT) dan Market Making.
Arsitektur menggunakan jembatan jaringan (bridge network) internal dengan subnet `172.28.0.0/16`.

Stack Teknologi Utama:
- **Orchestration**: Docker & Docker Compose
- **Execution Engine**: Hummingbot (Custom Image)
- **Backend Orchestrator**: FastAPI (Python 3.11+) + Uvicorn
- **Frontend Dashboard**: Next.js 14 (App Router) + TailwindCSS
- **Database Utama**: PostgreSQL 15
- **Message Broker & Cache**: Redis 7 Alpine
- **Strategy & ML**: Microservices Python terpisah (TensorFlow/PyTorch/Pandas)
- **Observability Stack**: Grafana, Loki (Log Aggregation), Promtail (Log Collector)
- **Reverse Proxy**: Nginx (Port 80/443)

# 2. Complete 10-Container Topology (docker-compose.yml Requirement)
Bangun file `docker-compose.yml` yang berisi 10 services berikut beserta dependensinya (`depends_on` dengan `condition: service_healthy` untuk database/redis):
1. `nginx`: Nginx reverse proxy.
2. `frontend`: Next.js node server on port 3000 (internal).
3. `backend-api`: FastAPI on port 8000. Harus memiliki container `volume: logs:/app/logs`.
4. `hummingbot`: Custom Hummingbot image. Mounting volume `hummingbot-data:/app/data`.
5. `strategy-engine`: Engine Python untuk kalkulasi matriks (Port 8001).
6. `ml-engine`: Engine Machine learning (Port 8003). Mounting volume `ml-models:/app/models`.
7. `quant-research`: Jupyter Lab environment untuk backtesting (Port 8002).
8. `postgres`: Setup DB dengan `PGDATA` volume lokal dan healthcheck `pg_isready`.
9. `redis`: Confirgured with `--maxmemory 256mb --maxmemory-policy allkeys-lru --appendonly yes` dan `redis-cli ping` healthcheck.
10. `Observability Stack` (`grafana`, `loki`, `promtail`, `monitoring-service`): Mounting `/var/run/docker.sock` ke Promtail untuk menarik log secara real-time dari semua container QuantBot.

# 3. Development & CI/CD Pipeline (GitHub Integration)
Sistem ini harus dirancang agar siap masuk ke GitHub.
1. **GitHub Actions (CI)**: Buatkan workflow `.github/workflows/ci.yml` yang melakukan:
   - Linting & Formating checking untuk Frontend (ESLint/Prettier) dan Backend (Ruff/Black).
   - Menjalankan Unit Tests (Pytest untuk backend API dan strategy engine).
   - Build dry-run Docker image untuk memastikan tidak ada build yang gagal.
2. **Environment Management (`.env`)**:
   - Berikan saya template `.env.example` yang mencakup sekuritas dasar: kredensial Postgres, kredensial Redis, JWT Secret Key, API Keys Eksternal (Binance/Bybit Testnet), dan konfigurasi port.
3. **Database Migrations**:
   - Implementasikan struktur Alembic di dalam direktori `services/backend-api` untuk manajemen skema database. Buatkan setup struktur tabel awal untuk: `users`, `strategies`, `trade_ history`, dan `risk_parameters`.

# 4. Frontend Specs (Next.js Dashboard)
- **Desain UI/UX**: Gunakan gaya "Terminal Trading" atau "Hyperliquid Style". Warna dominan hitam pekat/hitam kebiruan dengan aksen hijau teal terang (Neon Teal) untuk profit/status online, dan merah rose (Crimson) untuk loss/offline. Font menggunakan monospace untuk angka (Inter/Roboto Mono).
- **Fitur Wajib**:
  - Halaman terbagi atas: Trade (Terminal Utama), Strategies, Risk, Research, History.
  - Grafik Lilin (Candlestick) terintegrasi menggunakan paket `lightweight-charts` by TradingView.
  - Tabel Order Book langsung (live) di sebelah kiri grafik.
  - Komponen Websocket client (`/ws/dashboard`) yang menangkap pesan JSON tipe `equity_update`, `positions_update`, dan `health_update`.
  - Tombol "GLOBAL KILL SWITCH" dengan mekanisme konfirmasi (Prompt bahaya besar).

# 5. Backend Specs (FastAPI Gateway)
- File entry point (`services/backend-api/app/main.py`) harus menginisialisasi `asyncpg` pool connection dan `redis.asyncio` pool connection di dalam blocks `@asynccontextmanager async def lifespan(app: FastAPI):`.
- Pisahkan router berdasarkan fungsinya: `auth.py`, `trading.py`, `strategy.py`, `risk.py`, dan `websocket.py`.
- Buatkan background task/dependency injection untuk melakukan "Ping" interval 15 detik ke Websocket agar koneksi frontend tidak timeout.

# 6. Actionable Blueprint Instructions untuk AI
Sebagai AI Assistant, lakukan tugas berikut SECARA BERURUTAN ketika menerima prompt ini:
1. Buatkan struktur shell script / perintah terminal (bash/powershell) untuk men-generate struktur foldernya.
2. Tuliskan isi `docker-compose.yml` secara lengkap (tanpa pemotongan).
3. Tuliskan `requirements.txt` untuk backend dan `package.json` untuk frontend.
4. Tulis file `services/backend-api/app/main.py`.
5. Tulis file `services/frontend/src/app/page.tsx` (desain lengkap dengan Tailwind dan Websocket state).
6. Tulis file CI/CD GitHub Actions `.github/workflows/main.yml`.
Jangan bertanya lagi, langsung buatkan kode untuk masing-masing poin di atas dengan standar kode production-ready (bersih, dengan komentar, penanganan error, dan log strukturnya).
```
