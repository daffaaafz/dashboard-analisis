import io
import pandas as pd
import sqlite3
import streamlit as st

# Konfigurasi halaman Streamlit agar lebar penuh
st.set_page_config(
    page_title="Dashboard Analisis Penjualan Kopi", layout="wide"
)

# Judul Utama Dashboard
st.title("📊 Dashboard Analisis Penjualan Kopi")
st.markdown("---")

# ==========================================
# 1. SIDEBAR: UPLOAD FILE & FILTER
# ==========================================
st.sidebar.header("📂 Unggah Data & Filter")
uploaded_file = st.sidebar.file_uploader(
    "Upload File Excel Penjualan", type=["xlsx", "xls"]
)

# Membuat koneksi SQLite di dalam memori (In-Memory Database)
conn = sqlite3.connect(":memory:")

if uploaded_file is not None:
  # Membaca file Excel yang di-upload user
  df = pd.read_excel(uploaded_file)

  # Membersihkan nama kolom (menghilangkan spasi ekstra jika ada)
  df.columns = df.columns.str.strip()

  # Masukkan dataframe ke dalam tabel SQLite bernama 'tabel_penjualan'
  df.to_sql("tabel_penjualan", conn, if_exists="replace", index=False)

  st.sidebar.success("File berhasil divalidasi, diunggah & dibersihkan!")
else:
  # Data Dummy / Fallback jika belum upload file (agar aplikasi tidak error saat pertama dibuka)
  data_dummy = {
      "ID_Transaksi": ["KOP-001", "KOP-002", "KOP-003", "KOP-004"],
      "Bulan": ["Januari", "Februari", "Maret", "April"],
      "Tanggal": ["2026-01-01", "2026-02-01", "2026-03-01", "2026-04-01"],
      "Nama_Produk": [
          "Kopi Susu Gula Aren",
          "Es Kopi Hitam",
          "Kopi Latte",
          "Kopi Americano",
      ],
      "Kota": ["Jakarta Selatan", "Bandung", "Surabaya", "Jakarta Pusat"],
      "Jumlah_Cup": [15, 20, 10, 25],
      "Total_Harga": [225000, 300000, 150000, 400000],
  }
  df = pd.DataFrame(data_dummy)
  df.to_sql("tabel_penjualan", conn, if_exists="replace", index=False)
  st.sidebar.info(
      "Menggunakan data default. Silakan upload file Excel Anda di atas."
  )

# --- FITUR FILTER KOTA ---
# Mengambil daftar kota unik dari database untuk dropdown filter
query_kota = "SELECT DISTINCT Kota FROM tabel_penjualan"
df_kota = pd.read_sql_query(query_kota, conn)
list_kota = ["Semua Kota"] + df_kota["Kota"].tolist()

selected_kota = st.sidebar.selectbox("Filter Berdasarkan Kota:", list_kota)

# ==========================================
# 2. KUERI SQL UTAMA & GRAFIK
# ==========================================
# Kueri utama untuk tabel dan metrik pendapatan/cup
if selected_kota == "Semua Kota":
  query_main = "SELECT * FROM tabel_penjualan"
  query_chart = """
        SELECT Nama_Produk, SUM(Total_Harga) AS Total_Pendapatan 
        FROM tabel_penjualan 
        GROUP BY Nama_Produk 
        ORDER BY Total_Pendapatan DESC
    """
else:
  query_main = f"SELECT * FROM tabel_penjualan WHERE Kota = '{selected_kota}'"
  query_chart = f"""
        SELECT Nama_Produk, SUM(Total_Harga) AS Total_Pendapatan 
        FROM tabel_penjualan 
        WHERE Kota = '{selected_kota}' 
        GROUP BY Nama_Produk 
        ORDER BY Total_Pendapatan DESC
    """

# Eksekusi kueri utama & chart
df_filtered = pd.read_sql_query(query_main, conn)
df_chart = pd.read_sql_query(query_chart, conn)

# ==========================================
# 3. KUERI SQL TAMBAHAN (PRODUK, BULAN, & AOV)
# ==========================================
# A. Produk Terlaris
if selected_kota == "Semua Kota":
  query_top_product = """
        SELECT Nama_Produk, SUM(Jumlah_Cup) AS Total_Terjual 
        FROM tabel_penjualan 
        GROUP BY Nama_Produk 
        ORDER BY Total_Terjual DESC 
        LIMIT 1
    """
else:
  query_top_product = f"""
        SELECT Nama_Produk, SUM(Jumlah_Cup) AS Total_Terjual 
        FROM tabel_penjualan 
        WHERE Kota = '{selected_kota}'
        GROUP BY Nama_Produk 
        ORDER BY Total_Terjual DESC 
        LIMIT 1
    """
df_top_product = pd.read_sql_query(query_top_product, conn)

# B. Bulan Paling Produktif
if selected_kota == "Semua Kota":
  query_top_month = """
        SELECT Bulan, SUM(Total_Harga) AS Pendapatan_Bulan 
        FROM tabel_penjualan 
        GROUP BY Bulan 
        ORDER BY Pendapatan_Bulan DESC 
        LIMIT 1
    """
else:
  query_top_month = f"""
        SELECT Bulan, SUM(Total_Harga) AS Pendapatan_Bulan 
        FROM tabel_penjualan 
        WHERE Kota = '{selected_kota}'
        GROUP BY Bulan 
        ORDER BY Pendapatan_Bulan DESC 
        LIMIT 1
    """
df_top_month = pd.read_sql_query(query_top_month, conn)

# ==========================================
# 4. RINGKASAN METRIK (4 KOLOM)
# ==========================================
total_pendapatan = df_filtered["Total_Harga"].sum()
total_cup = df_filtered["Jumlah_Cup"].sum()

# Hitung Rata-rata Nilai Transaksi (AOV)
if not df_filtered.empty:
  rata_rata_transaksi = df_filtered["Total_Harga"].mean()
else:
  rata_rata_transaksi = 0

col1, col2, col3, col4 = st.columns(4)

with col1:
  st.metric(
      label=f"Total Pendapatan ({selected_kota})",
      value=f"Rp {total_pendapatan:,.0f}",
  )

with col2:
  st.metric(
      label=f"Total Cup Terjual ({selected_kota})", value=f"{total_cup} Cup"
  )

with col3:
  if not df_top_product.empty:
    top_name = df_top_product.iloc[0]["Nama_Produk"]
    top_qty = df_top_product.iloc[0]["Total_Terjual"]
    st.metric(
        label=f"🏆 Terlaris", value=top_name, delta=f"{top_qty} Cup Terjual"
    )

with col4:
  if not df_top_month.empty:
    top_bulan = df_top_month.iloc[0]["Bulan"]
    top_bulan_omzet = df_top_month.iloc[0]["Pendapatan_Bulan"]
    st.metric(
        label=f"📈 Bulan Terbaik",
        value=top_bulan,
        delta=f"Rp {top_bulan_omzet:,.0f}",
    )

# Tambahan Info AOV di bawahnya atau ringkasan kecil
st.caption(
    f"💳 Rata-rata Nilai Transaksi (AOV) untuk {selected_kota}: **Rp"
    f" {rata_rata_transaksi:,.0f}** per transaksi"
)

st.markdown("---")

# ==========================================
# 5. TABEL DATA TRANSAKSI & FITUR EXCEL EXPORT
# ==========================================
st.subheader(f"📋 Data Transaksi ({selected_kota})")
st.dataframe(df_filtered, use_container_width=True)

# Tombol Export Data ke Excel menggunakan io.BytesIO
output = io.BytesIO()
with pd.ExcelWriter(output, engine="openpyxl") as writer:
  df_filtered.to_excel(writer, index=False, sheet_name="Laporan Penjualan")
excel_data = output.getvalue()

st.download_button(
    label=f"📥 Export Data {selected_kota} ke Excel",
    data=excel_data,
    file_name=f"laporan_penjualan_{selected_kota.lower().replace(' ', '_')}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)

st.markdown("---")

# ==========================================
# 6. VISUALISASI GRAFIK BATANG
# ==========================================
st.subheader(f"📊 Grafik Penjualan per Produk ({selected_kota})")

if not df_chart.empty:
  # Mengatur 'Nama_Produk' sebagai index agar bar chart Streamlit membaca label dengan benar
  df_chart_indexed = df_chart.set_index("Nama_Produk")
  st.bar_chart(df_chart_indexed["Total_Pendapatan"])
else:
  st.warning("Tidak ada data grafik untuk kota yang dipilih.")

# Tutup koneksi database di akhir skrip
conn.close()