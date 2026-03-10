---
name: ui_ux_ecommerce_master
description: A master blueprint containing the 5 core UI/UX formulas and the ideal layout structure for modern 2025 E-Commerce and D2C Applications.
---

# UI/UX E-Commerce Master Skill

Use this skill whenever you are tasked with designing or building a Frontend interface for an E-Commerce store, Marketplace, or Direct-to-Consumer (D2C) brand. Ensure that the generated code strictly follows the 5 UX Formulas and the Layout Architecture outlined below.

```markdown
# Panduan Utama: Formula UX Modern untuk E-Commerce (2025-2026)

Panduan ini berisi prinsip-prinsip desain tingkat produksi yang berfokus pada **Konversi (Conversion Rate)** dan **Pengalaman Belanja Tanpa Hambatan (Frictionless UX)**.

## 5 Formula UX Wajib E-Commerce

### 1. Mobile-First & "Thumb Zone" Optimization
Mayoritas pembeli berbelanja lewat HP (Mobile). Desain harus diprioritaskan untuk layar berukuran 375px - 430px.
- **Thumb Zone:** Tempatkan elemen *Call-to-Action* (CTA) paling penting (seperti tombol "Add to Cart") di bagian bawah layar (*Sticky Bottom*) agar mudah dijangkau jempol (Satu Tangan).
- Menu navigasi *Slide-out* (Hamburger menu) harus mulus, jangan gunakan *dropdown hover* yang sulit disentuh di HP.

### 2. Frictionless Checkout (Minim Hambatan)
Langkah pembayaran yang panjang akan membunuh konversi.
- Wajib sediakan opsi **Guest Checkout** (Pembayaran Tanpa Daftar Akun).
- Jika ada *login*, sediakan opsi *One-Click Login* (Google/Apple).
- Tampilkan visual pengaman belanja (Ikon Gembok SSL, Logo Visa/Mastercard, Jaminan Uang Kembali) tepat di bawah tombol *Checkout*.

### 3. Advanced Filtering & Predictive Search
Pembeli yang menggunakan fitur pencarian memiliki probabilitas beli 3x lipat lebih tinggi.
- Gunakan fitur **Predictive Search** (Auto-complete) saat pengguna mulai mengetik.
- Sediakan filter produk minimalis di sisi kiri (Desktop) atau *Slide-out* layar penuh (Mobile). Pisahkan filter berdasarkan Harga, Kategori, dan Rating.

### 4. Visual Trust & Social Proof Hierarchy
Kepercayaan (*Trust*) adalah segalanya bagi e-commerce baru.
- Penilaian (*Star Ratings*) harus menempel tepat di bawah nama produk (baik di Grid maupun di Detail Produk).
- Bagian Ulasan (Reviews) wajib menampilkan foto dari pembeli lain (*User Generated Content*), bukan sekadar teks.

### 5. Micro-Interactions (Umpan Balik Instan)
Setiap interaksi harus memberi tahu sistem sedang merespons, tanpa memindahkan halaman.
- Saat klik "Add to Cart", gunakan interaksi **Slide-out Cart** (Keranjang geser dari kanan) bukannya berpindah halaman.
- Gunakan *Skeleton Loading* untuk memuat galeri gambar produk.
- Tambahkan animasi getar halus saat ada validasi data *checkout* yang salah.

---

## Arsitektur Layout Universal E-Commerce

Saat membangun antarmuka web, terapkan 3 struktur tata letak emas ini:

### A. Homepage (Beranda)
```text
[ Navbar Teratas: Logo | Search Bar Lebar | Ikon Akun | Ikon Keranjang ]
[ --- Hero Banner: Foto Lifestyle Resolusi Tinggi + Tombol Beli Utama --- ]
[ Carousel: Promo Bank / Jaminan Pengiriman ]
[ Grid 4 Kolom: Best-Sellers (Gambar, Nama, Harga, Bintang) ]
[ Grid Kategori Lengkap (Bulat/Kotak dengan Ikon) ]
[ Footer: Link Kebijakan | Metode Pembayaran | Kolom Newsletter ]
```

### B. Product Listing Page / PLP (Halaman Etalase)
```text
[ Navbar ]
[ Breadcrumbs: Home > Kategori > Pakaian Pria ]
--------------------------------------------------------------
Left Sidebar (25%)       | Main Content (75%)
[ Filter: Kategori ]     | [ Header Kategori + Jumlah Barangnya ]
[ Filter: Harga ]        | [ Grid Produk (3-4 Kolom Desktop)    ]
[ Filter: Rating ]       | [ Tiap Kartu: Gambar + Nama + Harga  ]
[ Tombol Clear Filter ]  | [ + Tombol Beli Cepat (Quick Add)    ]
--------------------------------------------------------------
```

### C. Product Details Page / PDP (Halaman Produk Spesifik)
```text
[ Navbar ]
--------------------------------------------------------------
Image Gallery (50%)      | Purchase Action (50%)
[ Foto Utama Besar ]     | [ Merek Produk ]
[ Foto Kecil di Bawah ]  | [ Nama Produk Ekstra Besar ]
                         | [ Bintang Ulasan (Misal: 4.8 / 5) ]
                         | [ Harga Besar + Diskon Dicoret ]
                         | [ Pemilih Varian: Ukuran / Warna ]
                         | [ TOMBOL "ADD TO CART" (Lebar 100%) ]
                         | [ Akordion: Deskripsi / Pengiriman / FAQ ]
--------------------------------------------------------------
```

> [!IMPORTANT]
> Ketika membangun dengan *Next.js/React*, pastikan `Cart` dibuat dengan pola **Global State** (seperti Zustand atau React Context) agar status angka di ikon keranjang header ter-update seketika (*real-time*) di setiap halaman.
```
