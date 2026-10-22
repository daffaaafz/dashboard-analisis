import sqlite3
import pandas as pd
import streamlit as st

# 1. Konfigurasi Halaman Web
st.set_page_config(page_title="Dashboard Penjualan Kopi", layout="wide")

st.title("Dashboard Analisis ")
st.write(
    ""
)

# ---------------------------------------------------------
# SIDEBAR: Fitur Unggah File & Filter
# ---------------------------------------------------------
st.sidebar.header("📁 Unggah Data & Filter")

# Fitur 1: File Uploader
uploaded_file = st.sidebar.file_uploader(
    "Unggah File Excel Penjualan", type=["xlsx", "xls"]
)


# Fungsi untuk Membersihkan Data (ETL) dengan Validasi Kolom
py_validation_passed = True


def clean_data(df_raw):
  global py_validation_passed

  # Daftar kolom wajib yang harus ada di file Excel klien
  kolom_wajib = [
      "ID_Transaksi",
      "Bulan",
      "Tanggal",
      "Nama_Produk",
      "Kota",
      "Jumlah_Cup",
      "Total_Harga",
  ]

  # Periksa apakah semua kolom wajib ada
  missing_columns = [col for col in kolom_wajib if col not in df_raw.columns]

  if missing_columns:
    st.sidebar.error(
        f"⚠️ Gagal! Kolom berikut tidak ditemukan di file Anda: {missing_columns}"
    )
    py_validation_passed = False
    return None

  df_clean = df_raw.copy()

  # Pembersihan Tanggal
  df_clean["Tanggal"] = pd.to_datetime(
      df_clean["Tanggal"], errors="coerce"
  ).dt.strftime("%d %B %Y")

  # Pembersihan Teks Nama Produk & Kota
  df_clean["Nama_Produk"] = df_clean["Nama_Produk"].str.title().str.strip()
  df_clean["Kota"] = df_clean["Kota"].str.title().str.strip()

  # Pengisian data hilang & konversi tipe data angka
  df_clean["Jumlah_Cup"] = df_clean["Jumlah_Cup"].fillna(0).astype(int)
  df_clean["Total_Harga"] = df_clean["Total_Harga"].fillna(0).astype(float)

  return df_clean


# Menentukan Sumber Data (Apakah dari Upload atau File Lokal Default)
df = None

if uploaded_file is not None:
  df_raw = pd.read_excel(uploaded_file)
  df_cleaned_temp = clean_data(df_raw)

  if py_validation_passed and df_cleaned_temp is not None:
    df = df_cleaned_temp
    st.sidebar.success("✅ File berhasil divalidasi, diunggah & dibersihkan!")
  else:
    df = None
else:
  try:
    df = pd.read_excel("Laporan_Penjualan_Kopi_Bersih.xlsx")
  except FileNotFoundError:
    st.error(
        "⚠️ File default tidak ditemukan! Silakan unggah file Excel di sidebar"
        " sebelah kiri."
    )

# ---------------------------------------------------------
# PROSES UTAMA (Jika Data Valid & Tersedia)
# ---------------------------------------------------------
if df is not None:
  # 2. Simpan & Hubungkan ke SQL Database (SQLite)
  conn = sqlite3.connect("database_kopi.db")
  df.to_sql("tabel_penjualan", conn, if_exists="replace", index=False)

  # Fitur 2: Filter Sidebar Interaktif (Berdasarkan Kota)
  kota_list = ["Semua Kota"] + list(df["Kota"].dropna().unique())
  selected_kota = st.sidebar.selectbox("Filter Berdasarkan Kota:", kota_list)

  # Filter Query SQL berdasarkan Pilihan User
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

  df_filtered = pd.read_sql_query(query_main, conn)
  df_chart = pd.read_sql_query(query_chart, conn)

  # 3. Ringkasan Metrik (Menyesuaikan dengan Filter)
  total_pendapatan = df_filtered["Total_Harga"].sum()
  total_cup = df_filtered["Jumlah_Cup"].sum()

  col1, col2 = st.columns(2)
  with col1:
    st.metric(
        label=f"Total Pendapatan ({selected_kota})",
        value=f"Rp {total_pendapatan:,.0f}",
    )
  with col2:
    st.metric(
        label=f"Total Cup Terjual ({selected_kota})", value=f"{total_cup} Cup"
    )

  st.markdown("---")

  # 4. Tabel Data Interaktif
  st.subheader(f"📋 Data Transaksi ({selected_kota})")
  st.dataframe(df_filtered, use_container_width=True)

  # 5. Grafik Penjualan Dinamis
  st.subheader(f"📊 Grafik Penjualan per Produk ({selected_kota})")
  if not df_chart.empty:
    st.bar_chart(data=df_chart, x="Nama_Produk", y="Total_Pendapatan")
  else:
    st.info("Tidak ada data untuk kombinasi filter ini.")

  # Tutup Koneksi Database
  conn.close()