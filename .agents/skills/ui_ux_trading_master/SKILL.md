---
name: ui_ux_trading_master
description: A master blueprint containing the 5 core UI/UX formulas and the ideal layout structure for modern Crypto Trading Dashboards.
---

# UI/UX Trading Master Skill

Use this skill whenever you are tasked with designing or building a Frontend interface for a Trading Dashboard, Crypto Exchange, or any Data-Heavy Analytics platform. Ensure that the generated code strictly follows the 5 UX Formulas and the Layout Architecture outlined below.

```markdown
# Panduan Utama: Formula UX Modern untuk Dashboard Trading (2025-2026)

Panduan ini berisi prinsip-prinsip desain tingkat produksi yang wajib diterapkan saat membangun antarmuka (*interface*) untuk platform *trading*, pertukaran *crypto*, atau dasbor finansial berkinerja tinggi.

## 5 Formula UX Wajib

### 1. Information Hierarchy & Data Density Control
Trader harus bisa melihat data penting dalam 1 detik. Jangan menyembunyikan informasi vital.
- **Primary Data**: Chart Trading (ukuran terbesar di tengah).
- **Secondary Data**: Order Book & Daftar Posisi Terbuka.
- **Action Panel**: Tombol Buy/Sell & Konfigurasi Bot.
- **History Panel**: Trade History & System Logs.

### 2. Component-Based Dashboard System
Seluruh UI harus mengimplementasikan komponen yang modular dan dapat digunakan berulang (*reusable*), bukan halaman statis raksasa.
- *Wajib ada komponen:* Diagram (*Chart component*), *Order book component*, *Bot status component*, *Metrics widget*.
- Ini menjamin antarmuka yang konsisten dan skalabilitas tinggi.

### 3. Low Cognitive Load Interface
Kurangi kelelahan mata pengguna (*Eye Strain*) akibat menatap layar selama berjam-jam.
- **Tema:** Wajib menggunakan mode gelap (*Dark Mode* / latar belakang hitam/abu-abu sangat gelap).
- **Warna:** Sangat minimalis. Hanya gunakan warna mencolok pada teks data (*Hijau untuk naik, Merah untuk turun*).
- Kurangi *noise*, bayangan yang berlebihan, atau elemen dekoratif yang tidak berguna.

### 4. Real-Time Interaction UX
Tampilan harus terasa secepat kilat (⚡). Kecepatan adalah segalanya di dunia *trading*.
- Pembaruan harga (*price update*) harus *real-time* via WebSocket.
- Umpan balik seketika (*Instant feedback*) untuk setiap klik tombol menggunakan *notification toast* (tanpa memunculkan popup yang memblokir layar).
- Gunakan status "loading skeleton" saat menarik data awal *(low latency UI)*.

### 5. Modular Trading Workspace
Setiap *trader* memiliki gaya yang berbeda. Sistem UI yang baik tidak mengunci *widget* secara permanen.
- Jika memungkinkan, sediakan kemampuan *Drag and Drop* panel, merestrukturisasi ukuran tabel, dan menyembunyikan panel yang tidak relevan bagi pengguna.

---

## Arsitektur Layout Universal (CSS Grid Blueprint)

Saat menggunakan Tailwind CSS atau sistem Grid lainnya, bangun kerangka susunan halaman persis seperti di bawah ini:

```text
--------------------------------------------------------------
Top Bar (Navigasi Utama)
[ Logo/Market Selector ] | [ Strategy Config ] | [ Wallet Balance / Bot Status ]
--------------------------------------------------------------
Left Panel                | Center Panel           | Right Panel
                          |                        |
[ Order Book Bids ]       | [ TradingView Chart /  | [ Action Panel: Buy/Sell ]
                          |   Lightweight Charts ] | [ Bot Config Form ]
[ Order Book Asks ]       |                        | [ Margin Info ]
                          |                        |
--------------------------------------------------------------
Bottom Panel (Tabel Melebar)
[ Open Positions ] | [ Trade History ] | [ Pending Orders ] | [ Bot Execution Logs ]
--------------------------------------------------------------
```

> [!IMPORTANT]
> Ketika membangun dengan *Next.js/React*, jadikan setiap blok dalam skema di atas sebagai file komponen terpisah (misalnya `components/layout/RightPanel.tsx`, `components/trading/OrderBook.tsx`) untuk meredam pemuatan ulang layar *(re-rendering)* yang tidak perlu.
```
