# Rencana Upgrade UX: Trade Execution Feedback

Dokumen ini adalah arsip rencana peningkatan *User Experience* (UX) untuk dasbor QuantBot, yang bertujuan untuk membuat sistem terasa sekelas terminal institusional seperti Hyperliquid atau Binance. Peningkatan ini difokuskan pada memberikan umpan balik seketika (*instant feedback*) bagi pengguna atau bot saat sebuah order perdagangan (Buy/Sell) berhasil dieksekusi.

Berdasarkan analisis dan diskusi, berikut adalah **3 Lapisan Feedback Visual** yang akan diimplementasikan pada pembaruan mendatang:

### 1. Lapisan Notifikasi Toast (Pesan Pop-up Sudut Layar)
Sama seperti di platform modern, saat order terkirim, kotak notifikasi melayang di pojok layar yang ringkas namun padat informasi wajib muncul.

*   **Contoh Teks Target:** `🟢 MARKET BUY: 0.15 BTC @ $64,250.00` atau `🔴 LIMIT SELL: 0.5 ETH @ $3,500.00`
*   **Cara Kerja di Sistem:** Kita akan meningkatkan komponen fungsi `addToast` yang sudah ada di `page.tsx` UI Frontend. Fungsi ini akan memiliki variasi warna dan _styling_ khusus untuk eksekusi perdagangan (Hijau Terang untuk tipe Buy, Merah Terang untuk tipe Sell), beserta ikon pendukung seperti lonceng atau centang sukses.

### 2. Lapisan Penanda di Chart (Chart Order Lines)
Fitur paling krusial di platform trading visual. Saat pesanan masuk, harga masuk (*entry price*) harus langsung digambar sebagai **garis horizontal** (atau level harga) di atas grafik lilin (*candlestick*).

*   **Efek Visual Target:** Muncul garis putus-putus berwarna hijau atau merah di _chart_ secara presisi di level harga *entry*, dengan label teks kecil di ujung kanan (contoh: `Long 0.15`). Target lanjutan termasuk menggambar baris untuk *Take Profit* (TP) dan *Stop Loss* (SL).
*   **Cara Kerja di Sistem:** Menggunakan pustaka klien `Lightweight Charts` (via komponen `Chart.tsx`), kita akan memanfaatkan metode `createPriceLine()`. Saat integrasi Websocket posisi terbuka (*Open Positions*) mensinkronkan data dari Backend, UI akan langsung menghapus level lama dan menggambar ulang _price line_ secara seketika (_real-time_).

### 3. Lapisan Umpan Balik Audio (Opsional/Premium)
Sebuah "klik" mekanis yang halus atau suara denting tipis (*subtle chime*) saat eksekusi tervalidasi.

*   **Efek Psikologis:** Memberikan kepastian absolut ke otak pengguna bahwa sistem telah bereaksi terhadap *input*, bahkan beberapa milidetik sebelum notifikasi visual muncul sepenuhnya.

---

## Ringkasan Langkah Eksekusi (Next Actions)

Fokus eksekusi akan menyuntikkan efek ini ke siklus **Manual Trading** (Tombol Buy/Sell UI) maupun umpan balik **Auto-Trading** dari respons Strategy Engine.

1.  **Modifikasi Fungsi Notifikasi Khusus Trade:** Pembaruan logika UI klik tombol *Buy/Sell* agar langsung memijarkan *Toast Notification* yang sesuai pasca-respons sukses dari API REST atau *Websocket*.
2.  **Modifikasi Komponen `Chart.tsx`:** Menyiapkan _prop_ untuk menerima deretan _Open Positions_ aktif, kemudian iterasi menggunakan _Lightweight Charts PriceLine API_ untuk menderetkan `Entry Price` dan rentang target `TP/SL` langsung di plot grafik _candlestick_ pengguna.
