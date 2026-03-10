---
name: ui_menu_architecture_master
description: A blueprint for standard website navigation, covering public marketing pages and private dashboard routes. Use this to quickly architect an application's menu structure.
---

# UI Menu Architecture Master Skill

Use this blueprint whenever you need to architect the navigation menu and routing structure for a new web application, SaaS, or E-commerce platform. It provides the standard required routes for both public and private areas of an application.

```markdown
# Panduan Utama: Arsitektur Menu Universal & Struktur Routing Website Modern

Gunakan daftar struktur navigasi (menu) di bawah ini sebagai **Blueprint Final** kapan pun Anda (atau AI) diminta untuk membangun *web app*, SaaS, atau *E-commerce* baru dari nol. Struktur ini memastikan alur perjalanan pengguna (*user journey*) yang mulus, lengkap, dan profesional tanpa perlu menebak-nebak lagi.

Struktur dibangun menggunakan paradigma **Public/Marketing vs Private/Dashboard**.

---

## 🌐 A. PUBLIC PAGES (Marketing & Landing)
*Berfungsi sebagai etalase produk. Menu diletakkan pada `Navbar` atas. Rute bersifat publik (tanpa otentikasi).*

1. **Home** (`/`)
   - *Tujuan:* 5 detik pertama (Hero Section), Value Proposition utama.
   - *Intensi:* Menjelaskan apa yang dilakukan aplikasi Anda.
2. **Features / Solusi** (`/features` atau `/solutions`)
   - *Tujuan:* Menjelaskan fungsionalitas produk secara mendalam, studi kasus.
   - *Intensi:* Menjawab "Bagaimana ini memecahkan masalah saya?".
3. **Pricing** (`/pricing`)
   - *Tujuan:* Tabel perbandingan tier harga, FAQ pembayaran.
   - *Intensi:* Menjawab keraguan tentang biaya langganan.
4. **Resources / Blog** (`/blog` atau `/docs`)
   - *Tujuan:* Edukasi pasar, dokumentasi API, SEO organik.
   - *Intensi:* Nilai tambah gratis bagi yang belum siap membeli.
5. **About Us / Contact** (`/about` atau `/contact`)
   - *Tujuan:* Visi misi perusahaan, form hubungi kami, kredibilitas.
   - *Intensi:* Menumbuhkan rasa percaya.

### Rute Khusus Auth (Action Buttons):
Diletakkan di ujung kanan `Navbar` publik.
- **Login / Sign In** (`/login` atau `/auth/login`) -> "Saya punya akun."
- **Sign Up / Register** (`/register` atau `/auth/register`) -> "Saya mau coba."

---

## 🔒 B. PRIVATE DASHBOARD (Aplikasi Inti / Workspace)
*Berjalan di dalam layout terpisah (contoh `app/(dashboard)/layout.tsx`). Hanya bisa diakses setelah login. Menu biasanya diletakkan pada `Sidebar` kiri.*

1. **Overview / Dashboard Utama** (`/app` atau `/dashboard`)
   - *Tujuan:* Mata elang. Menampilkan metrik kunci (Pendapatan hari ini, sisa kuota, jumlah klik).
   - *Intensi:* Pemeriksaan vitalitas akun secara cepat.
2. **Core Module 1** (`/app/projects`, `/app/orders`, atau `/app/campaigns`)
   - *Tujuan:* Fitur utama aplikasi. Daftar proyek, pesanan e-commerce, atau kampanye.
   - *Intensi:* Area eksekusi kerja sehari-hari pengguna.
3. **Core Module 2 [Opsional]** (`/app/customers`, `/app/inventory`)
   - *Tujuan:* Fitur pendukung fitur utama (CRUD Data).
4. **Analytics / Reports** (`/app/reports` atau `/app/analytics`)
   - *Tujuan:* Tabel dan grafik mendetail dengan *date picker/filter*.
   - *Intensi:* Analisa performa masa lalu pengguna.
5. **Billing / Langganan** (`/app/billing`)
   - *Tujuan:* Upgrade/Downgrade paket (*plan*), atur kartu kredit (via Stripe Portal), riwayat *invoice*.
   - *Intensi:* Mendapat uang dengan memfasilitasi pengguna yang ingin membayar.
6. **Integrations / API** (`/app/integrations`)
   - *Tujuan:* Menyambungkan sistem dengan Slack, Telegram, Webhook, API Keys.
   - *Intensi:* Meningkatkan *stickiness* produk pada alur kerja perusahaan pengguna.
7. **Settings / Pengaturan** (`/app/settings`)
   - *Tujuan (Sub-menu):*
      - `Profile`: Ganti Avatar, Nama.
      - `Account`: Ganti Email, Reset Password, Hapus Akun.
      - `Preferences`: *Light/Dark mode*, Zona Waktu, Bahasa.
      - `Notifications`: Matikan/hidupkan pengingat email agar tidak terkesan spam.
8. **Help & Support** (`/app/support`)
   - *Tujuan:* Buka *ticket*, link ke dokumentasi, atau percakapan obrolan (Intercom/Crisp).

---

## 🛟 C. HALAMAN SISTEM (Sangat Penting Namun Sering Terlupa)
Pastikan hal ini terprogram di *router*!

1. **404 Not Found** (`/404`): Desain ramah yang mengembalikan user ke Home.
2. **Terms of Service** (`/terms`): Syarat & Ketentuan legalitas.
3. **Privacy Policy** (`/privacy`): Kebijakan privasi data (wajib untuk izin Google/FB Ads).
4. **Onboarding / Setup** (`/onboarding`): Halaman paksaan (*force-redirect*) satu kali untuk user yang baru mendaftar agar segera melengkapi data sebelum masuk ke Dashboard.

---

### Cara Praktis Implementasi oleh AI
Jika diminta membuat aplikasi apa pun:
- Langsung bangun arsitektur rute berbasis direktori (*directory-based routing* seperti Next.js App Router) berdasarkan pembagian di atas.
- Folder `(marketing)` untuk daftar "A", dan folder `(dashboard)` untuk daftar "B".
- Proteksi semua rute `(dashboard)` menggunakan *Middleware* otentikasi.
```
