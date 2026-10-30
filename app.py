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
        where_clause = "WHERE 1=0"
    else:
        formatted_cities = "', '".join(selected_kota)
        where_clause = f"WHERE Kota IN ('{formatted_cities}')"

    # ---------------------------------------------------------
    # TAB UTAMA: Membagi Dashboard & Analisis Bisnis
    # ---------------------------------------------------------
    tab1, tab2 = st.tabs(["📊 Dashboard Utama", "📈 Analisis Bisnis & Rekomendasi"])

    with tab1:
        # --- KARTU METRIK UTAMA ---
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

        aov_query = f"SELECT AVG(Total_Harga) FROM penjualan {where_clause}"
        res_aov = conn.execute(aov_query).fetchone()
        aov = res_aov[0] if res_aov[0] else 0

        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Pendapatan Total", f"Rp {total_revenue:,.0f}".replace(",", "."))
        col2.metric("Total Cup Terjual", f"{total_cup:,}".replace(",", "."))
        col3.metric("Produk Terlaris 🏆", best_product)
        col4.metric("Bulan Terbaik 📈", best_month)
        col5.metric("Rata-rata Order (AOV)", f"Rp {aov:,.0f}".replace(",", "."))

        st.markdown("---")

        # --- VISUALISASI UTAMA ---
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
                st.info("Kolom 'Metode_Bayar' tidak ditemukan.")

        st.subheader("📋 Detail Data Transaksi")
        table_query = f"SELECT * FROM penjualan {where_clause} LIMIT 100"
        df_table = pd.read_sql_query(table_query, conn)
        st.dataframe(df_table, use_container_width=True)

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

    with tab2:
        st.header("📈 Analisis Mendalam & Rekomendasi Strategis")
        st.markdown("Tab ini merangkum 5 pilar evaluasi kinerja bisnis berdasarkan data transaksi.")
        st.markdown("---")

        # Ambil data terfilter untuk tab 2
        df_filtered = pd.read_sql_query(f"SELECT * FROM penjualan {where_clause}", conn)

        if df_filtered.empty:
            st.warning("Tidak ada data untuk kota yang dipilih.")
        else:
            # 1. Tren Omzet Bulanan
            st.subheader("1. Tren Omzet Bulanan")
            df_filtered['Tanggal_DT'] = pd.to_datetime(df_filtered['Tanggal'])
            df_filtered['Bulan_Tahun'] = df_filtered['Tanggal_DT'].dt.to_period('M').astype(str)
            df_monthly = df_filtered.groupby('Bulan_Tahun')['Total_Harga'].sum().reset_index()
            
            fig_trend = px.line(df_monthly, x='Bulan_Tahun', y='Total_Harga', markers=True,
                                labels={'Bulan_Tahun': 'Bulan', 'Total_Harga': 'Total Omzet (Rp)'})
            st.plotly_chart(fig_trend, use_container_width=True)
            
            st.markdown("**🔍 Temuan:** Omzet bulanan menunjukkan fluktuasi stabil dengan titik puncak dan koreksi di beberapa periode tertentu.")
            st.markdown("**💡 Rekomendasi:** Tingkatkan promosi atau adakan event khusus pada bulan-bulan yang mengalami penurunan untuk menjaga kestabilan cash flow.")
            st.markdown("---")

            # 2. Kontribusi Produk (Pareto)
            st.subheader("2. Kontribusi Produk terhadap Omzet")
            df_prod_contrib = df_filtered.groupby('Nama_Produk')['Total_Harga'].sum().reset_index()
            df_prod_contrib = df_prod_contrib.sort_values(by='Total_Harga', ascending=False)
            df_prod_contrib['Persentase'] = (df_prod_contrib['Total_Harga'] / df_prod_contrib['Total_Harga'].sum()) * 100

            fig_prod_contrib = px.bar(df_prod_contrib, x='Nama_Produk', y='Total_Harga', 
                                      text=df_prod_contrib['Persentase'].round(1).astype(str) + '%',
                                      labels={'Nama_Produk': 'Produk', 'Total_Harga': 'Omzet (Rp)'})
            st.plotly_chart(fig_prod_contrib, use_container_width=True)

            st.markdown("**🔍 Temuan:** Sebagian besar omzet didominasi oleh segelintir produk unggulan (seperti Kopi Susu Gula Aren dan Kopi Latte) yang menyumbang mayoritas pendapatan.")
            st.markdown("**💡 Rekomendasi:** Pastikan inventaris bahan baku untuk produk-produk kontributor utama ini selalu aman agar terhindar dari kehabisan stok.")
            st.markdown("---")

            # 3. Performa Kota
            st.subheader("3. Performa Pertumbuhan Kota")
            df_city_trend = df_filtered.groupby(['Bulan_Tahun', 'Kota'])['Total_Harga'].sum().reset_index()
            fig_city = px.line(df_city_trend, x='Bulan_Tahun', y='Total_Harga', color='Kota', markers=True,
                               labels={'Bulan_Tahun': 'Bulan', 'Total_Harga': 'Omzet (Rp)', 'Kota': 'Kota'})
            st.plotly_chart(fig_city, use_container_width=True)

            st.markdown("**🔍 Temuan:** Terdapat ketimpangan performa di mana kota tertentu mengalami pertumbuhan positif yang konsisten, sementara kota lain cenderung mendatar atau melemah.")
            st.markdown("**💡 Rekomendasi:** Alokasikan strategi pemasaran lokal yang lebih agresif ke kota yang menunjukkan tren melemah guna mendongkrak kembali angka penjualan.")
            st.markdown("---")

            # 4. Jam dan Hari Tersibuk (Heatmap)
            st.subheader("4. Analisis Jam dan Hari Tersibuk")
            day_order = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
            df_heat = df_filtered.groupby(['Hari', 'Jam'])['ID_Transaksi'].count().reset_index(name='Jumlah_Transaksi')
            
            fig_heat = px.density_heatmap(df_heat, x='Jam', y='Hari', z='Jumlah_Transaksi', 
                                          category_orders={"Hari": day_order},
                                          color_continuous_scale="Viridis",
                                          labels={'Jam': 'Jam Operasional', 'Hari': 'Hari', 'Jumlah_Transaksi': 'Jml Transaksi'})
            st.plotly_chart(fig_heat, use_container_width=True)

            st.markdown("**🔍 Temuan:** Kepadatan transaksi sangat terkonsentrasi pada jam-jam tertentu (pagi dan sore hari) serta akhir pekan.")
            st.markdown("**💡 Rekomendasi:** Atur jadwal shift staf agar lebih padat di jam sibuk tersebut dan tawarkan promo 'Happy Hour' untuk menarik pelanggan di jam-jam sepi.")
            st.markdown("---")

            # 5. Efek Diskon dan Metode Bayar
            st.subheader("5. Analisis Efek Diskon dan Metode Pembayaran")
            col_a, col_b = st.columns(2)

            with col_a:
                st.markdown("**Rata-rata Nilai Transaksi: Dengan vs Tanpa Diskon**")
                df_filtered['Status_Diskon'] = df_filtered['Diskon_Persen'].apply(lambda x: 'Dengan Diskon' if x > 0 else 'Tanpa Diskon')
                df_disc = df_filtered.groupby('Status_Diskon')['Total_Harga'].mean().reset_index()
                fig_disc = px.bar(df_disc, x='Status_Diskon', y='Total_Harga', text_auto='.2f',
                                  labels={'Status_Diskon': 'Kategori', 'Total_Harga': 'Rata-rata Transaksi (Rp)'})
                st.plotly_chart(fig_disc, use_container_width=True)

            with col_b:
                st.markdown("**Dominasi Metode Pembayaran**")
                df_pay_meth = df_filtered.groupby('Metode_Bayar')['Total_Harga'].sum().reset_index()
                fig_pay_meth = px.pie(df_pay_meth, names='Metode_Bayar', values='Total_Harga', hole=0.3)
                st.plotly_chart(fig_pay_meth, use_container_width=True)

            st.markdown("**🔍 Temuan:** Transaksi didominasi oleh metode pembayaran digital (terutama QRIS) dan pemberian diskon terbukti menarik volume transaksi yang lebih besar.")
            st.markdown("**💡 Rekomendasi:** Jaga kestabilan infrastruktur pembayaran digital dan evaluasi margin keuntungan secara berkala agar program diskon tetap memberikan profit yang sehat.")

else:
    st.info("👋 Silakan unggah file Excel `data_penjualan_kopi.xlsx` pada sidebar untuk melihat dashboard.")