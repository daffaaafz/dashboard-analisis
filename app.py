import io
import sqlite3
import pandas as pd
import plotly.express as px
import streamlit as st

# 1. Konfigurasi Halaman Web
st.set_page_config(
    page_title="Dashboard Analisis Penjualan Kopi",
    layout="wide",
    page_icon="☕",
)

st.title("☕ Dashboard Analisis Penjualan Kopi")
st.markdown("---")

# 2. Sidebar: Upload File & Filter
st.sidebar.header("📁 Unggah Data & Filter")

uploaded_file = st.sidebar.file_uploader(
    "Unggah File Excel Penjualan (.xlsx)", type=["xlsx"]
)

if uploaded_file is not None:
    # Read Excel
    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip()  # Hapus spasi tak terlihat pada kolom

    # Simpan Data ke SQLite In-Memory Database
    conn = sqlite3.connect(":memory:")
    df.to_sql("penjualan", conn, index=False, if_exists="replace")

    # Filter Kota di Sidebar
    list_kota_query = "SELECT DISTINCT Kota FROM penjualan WHERE Kota IS NOT NULL ORDER BY Kota"
    list_kota = [row[0] for row in conn.execute(list_kota_query).fetchall()]
    selected_kota = st.sidebar.multiselect(
        "Pilih Kota:", options=list_kota, default=list_kota
    )

    # Penyusunan klausa WHERE untuk SQL
    if not selected_kota:
        where_clause = "WHERE 1=0"  # Jika tidak ada kota dipilih, tampilkan kosong
    else:
        formatted_cities = "', '".join(selected_kota)
        where_clause = f"WHERE Kota IN ('{formatted_cities}')"

    # ---------------------------------------------------------
    # 3. KARTU METRIK UTAMA (SQL Queries)
    # ---------------------------------------------------------
    m1_query = f"SELECT SUM(Total_Harga), SUM(Jumlah_Cup) FROM penjualan {where_clause}"
    res_m1 = conn.execute(m1_query).fetchone()
    total_revenue = res_m1[0] if res_m1[0] else 0
    total_cup = res_m1[1] if res_m1[1] else 0

    m2_query = f"""
        SELECT Nama_Produk, SUM(Jumlah_Cup) as total
        FROM penjualan {where_clause}
        GROUP BY Nama_Produk ORDER BY total DESC LIMIT 1
    """
    res_m2 = conn.execute(m2_query).fetchone()
    best_product = res_m2[0] if res_m2 else "-"

    m3_query = f"""
        SELECT Bulan, SUM(Total_Harga) as total
        FROM penjualan {where_clause}
        GROUP BY Bulan ORDER BY total DESC LIMIT 1
    """
    res_m3 = conn.execute(m3_query).fetchone()
    best_month = res_m3[0] if res_m3 else "-"

    # AOV (Average Order Value)
    aov_query = f"SELECT AVG(Total_Harga) FROM penjualan {where_clause}"
    res_aov = conn.execute(aov_query).fetchone()
    aov = res_aov[0] if res_aov[0] else 0

    # Layout 5 Kartu Metrik
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Pendapatan Total", f"Rp {total_revenue:,.0f}".replace(",", "."))
    col2.metric("Total Cup Terjual", f"{total_cup:,}".replace(",", "."))
    col3.metric("Produk Terlaris 🏆", best_product)
    col4.metric("Bulan Terbaik 📈", best_month)
    col5.metric("Rata-rata Order (AOV)", f"Rp {aov:,.0f}".replace(",", "."))

    st.markdown("---")

    # ---------------------------------------------------------
    # 4. VISUALISASI INTERAKTIF (PLOTLY CHART)
    # ---------------------------------------------------------
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.subheader("📊 Pendapatan per Produk")
        prod_query = f"""
            SELECT Nama_Produk, SUM(Total_Harga) as Total_Pendapatan
            FROM penjualan {where_clause}
            GROUP BY Nama_Produk ORDER BY Total_Pendapatan DESC
        """
        df_prod = pd.read_sql_query(prod_query, conn)
        fig_prod = px.bar(
            df_prod,
            x="Nama_Produk",
            y="Total_Pendapatan",
            text_auto=".2s",
            color="Nama_Produk",
            labels={"Total_Pendapatan": "Pendapatan (Rp)", "Nama_Produk": "Produk"},
        )
        fig_prod.update_layout(showlegend=False)
        st.plotly_chart(fig_prod, use_container_width=True)

    with chart_col2:
        st.subheader("💳 Proporsi Metode Pembayaran")
        # Menyesuaikan fitur baru dari file excel generator
        pay_query = f"""
            SELECT Metode_Bayar, COUNT(*) as Total_Transaksi
            FROM penjualan {where_clause}
            GROUP BY Metode_Bayar
        """
        df_pay = pd.read_sql_query(pay_query, conn)
        if not df_pay.empty and "Metode_Bayar" in df_pay.columns:
            fig_pay = px.pie(
                df_pay,
                names="Metode_Bayar",
                values="Total_Transaksi",
                hole=0.4,
            )
            st.plotly_chart(fig_pay, use_container_width=True)
        else:
            st.info("Kolom 'Metode_Bayar' tidak ditemukan di file ini.")

    # ---------------------------------------------------------
    # 5. TABEL DETAIL & EKSPOR EXCEL
    # ---------------------------------------------------------
    st.subheader("📋 Detail Data Transaksi")
    table_query = f"SELECT * FROM penjualan {where_clause} LIMIT 100"
    df_table = pd.read_sql_query(table_query, conn)
    st.dataframe(df_table, use_container_width=True)

    # Ekspor ke Excel
    export_query = f"SELECT * FROM penjualan {where_clause}"
    df_export = pd.read_sql_query(export_query, conn)

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df_export.to_excel(writer, index=False, sheet_name="Filtered_Data")

    st.download_button(
        label="📥 Unduh Data Hasil Filter (.xlsx)",
        data=buffer.getvalue(),
        file_name="Laporan_Penjualan_Filtered.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

else:
    st.info("👋 Silakan unggah file Excel `data_penjualan_kopi.xlsx` pada sidebar untuk melihat dashboard.")