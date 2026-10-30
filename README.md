#  Sales Analytics & Business Insights Dashboard

> Dashboard analitik penjualan kopi interaktif berbasis web yang dibangun menggunakan **Python, Streamlit, dan Plotly**, dirancang dengan arsitektur *vendor-agnostic* untuk memproses data multi-klien secara dinamis.

---

## 🌟 Tentang Proyek
Proyek ini dikembangkan sebagai bagian dari portofolio *Data Science / Data Analyst* untuk menunjukkan pemahaman mendalam terhadap:
- **Logika Bisnis & Data Storytelling:** Menerjemahkan data transaksi mentah menjadi temuan analitis dan rekomendasi strategis otomatis.
- **SQL & Manajemen Data:** Memanfaatkan SQLite *in-memory database* untuk menangani kueri cepat pada data multi-file.
- **Data Engineering & Modularitas:** Sistem *multi-file upload* yang dapat menerima berbagai format file Excel penjualan dari berbagai cabang tanpa terikat satu nama file spesifik.

---

## 🛠️ Tech Stack
- **Bahasa Pemrograman:** Python 3.x
- **Framework Web:** Streamlit
- **Visualisasi Data:** Plotly (Express, Density Heatmap, Bar/Line/Pie Charts)
- **Pengolahan & Analisis Data:** Pandas, NumPy
- **Database:** SQLite (In-Memory)
- **Manajemen Berkas:** OpenPyXL

---

## 🚀 Fitur Utama Dashboard
1. **Multi-File Upload & Dynamic Concat:** Menggabungkan beberapa file laporan penjualan dari berbagai cabang/vendor secara instan.
2. **Global & Local Filtering:** Filter interaktif berdasarkan kota yang otomatis memperbarui seluruh metrik dan visualisasi di layar.
3. **Executive KPI Cards:** Ringkasan metrik utama (Total Pendapatan, Total Cup, Produk Terlaris, Bulan Terbaik, dan Rata-rata Nilai Order / AOV).
4. **Tab Analisis Bisnis Mendalam (*Business Insights & Recommendations*):**
   - **Tren Omzet Harian:** Normalisasi omzet bulanan berdasarkan jumlah hari riil (`Rp/Hari`) untuk perbandingan yang adil.
   - **Analisis Pareto (80/20):** Identifikasi produk unggulan penopang utama pendapatan.
   - **Analisis Geografis:** Perbandingan performa pertumbuhan omzet antar kota.
   - **Heatmap Waktu Sibuk:** Deteksi jam dan hari operasional terpadat untuk efisiensi penjadwalan staf.
   - **Uji Statistik Diskon & Pembayaran:** Analisis dampak diskon terhadap volume cup per transaksi (dilengkapi uji signifikansi statistik dan peringatan sampel kecil) serta dominasi metode pembayaran digital (QRIS & E-Wallet).
5. **Ekspor Data Terfilter:** Fitur unduh laporan data yang telah disaring ke dalam format `.xlsx`.

---

## 💻 LINK

1. **Clone repository ini:**
   ```bash
   git clone [https://github.com/daffaaafz/dashboard-analisis.git]