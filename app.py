import io
import calendar
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

# Fungsi Format Angka Lokal Indonesia
def fmt(x, d=1):
    return f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")

# 2. Sidebar: Upload File Banyak Klien & Filter
st.sidebar.header("📁 Unggah Data & Filter")

uploaded_files = st.sidebar.file_uploader(
    "Unggah File Excel Penjualan (.xlsx)", 
    type=["xlsx"], 
    accept_multiple_files=True
)

if uploaded_files:
    # Read & combine Excel files
    df_list = []
    for file in uploaded_files:
        temp_df = pd.read_excel(file)
        temp_df.columns = temp_df.columns.str.strip()
        df_list.append(temp_df)
    
    df = pd.concat(df_list, ignore_index=True)

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
        st.header("📈 Insight Bisnis & Rekomendasi Strategis")
        
        # Ambil data terfilter
        df_filtered = pd.read_sql_query(f"SELECT * FROM penjualan {where_clause}", conn)

        if df_filtered.empty:
            st.warning("Tidak ada data untuk kota yang dipilih.")
        else:
            # Preprocessing Waktu
            df_filtered['Tanggal_DT'] = pd.to_datetime(df_filtered['Tanggal'])
            df_filtered['Tahun'] = df_filtered['Tanggal_DT'].dt.year
            df_filtered['Bulan_Num'] = df_filtered['Tanggal_DT'].dt.month
            df_filtered['Bulan_Tahun'] = df_filtered['Tanggal_DT'].dt.to_period('M').astype(str)
            df_filtered['Jumlah_Hari'] = df_filtered.apply(lambda r: calendar.monthrange(int(r['Tahun']), int(r['Bulan_Num']))[1], axis=1)

            # --- METRIK PERSIAPAN DYNAMIC REKOMENDASI UTAMA ---
            df_p = df_filtered.groupby('Nama_Produk')['Total_Harga'].sum().reset_index().sort_values(by='Total_Harga', ascending=False)
            df_p['Cum_Pct'] = (df_p['Total_Harga'].cumsum() / df_p['Total_Harga'].sum()) * 100
            top_80_prods = df_p[df_p['Cum_Pct'] <= 85]['Nama_Produk'].tolist()
            if not top_80_prods:
                top_80_prods = df_p.head(1)['Nama_Produk'].tolist()
            top_prods_str = ", ".join(top_80_prods)

            df_c = df_filtered.groupby('Kota')['Total_Harga'].sum().reset_index().sort_values(by='Total_Harga', ascending=False)
            top_city = df_c.iloc[0]['Kota'] if len(df_c) > 0 else "-"
            low_city = df_c.iloc[-1]['Kota'] if len(df_c) > 1 else top_city

            df_h = df_filtered.groupby(['Hari', 'Jam'])['ID_Transaksi'].count().reset_index(name='Jml').sort_values(by='Jml', ascending=False)
            peak_day = df_h.iloc[0]['Hari'] if not df_h.empty else "-"
            peak_jam = df_h.iloc[0]['Jam'] if not df_h.empty else "-"

            # --- RINGKASAN EXECUTIVE (3 POIN REKOMENDASI UTAMA) ---
            st.info(f"""
            📌 **Ringkasan Eksekutif & Fokus Strategis:**
            1. **Fokus Inventaris Utama:** Jaga kontinuitas stok bahan baku untuk produk penyumbang omzet terbesar (**{top_prods_str}**).
            2. **Alokasi Pemasaran Wilayah:** Optimalkan ekspansi pasar di **{top_city}** dan evaluasi ulang penetrasi strategi di **{low_city}**.
            3. **Efisiensi Operasional:** Tingkatkan jumlah *barista/staf* pada jam sibuk (Hari **{peak_day}**, Pukul **{peak_jam}**) untuk mencegah antrean panjang.
            """)
            st.markdown("---")

            # 1. Tren Omzet Bulanan (Dinormalisasi per Hari)
            st.subheader("1. Tren Omzet Rata-rata per Hari (Bulanan)")
            df_monthly = df_filtered.groupby(['Bulan_Tahun', 'Jumlah_Hari'])['Total_Harga'].sum().reset_index()
            df_monthly['Omzet_Per_Hari'] = df_monthly['Total_Harga'] / df_monthly['Jumlah_Hari']

            max_m = df_monthly.sort_values(by='Omzet_Per_Hari', ascending=False).iloc[0]
            min_m = df_monthly.sort_values(by='Omzet_Per_Hari', ascending=True).iloc[0]

            fig_trend = px.line(
                df_monthly, 
                x='Bulan_Tahun', 
                y='Omzet_Per_Hari', 
                markers=True,
                labels={'Bulan_Tahun': 'Bulan', 'Omzet_Per_Hari': 'Rata-rata Omzet / Hari (Rp)'}
            )
            st.plotly_chart(fig_trend, use_container_width=True)

            st.markdown(f"**🔍 Temuan:** Performa harian tertinggi diraih pada **{max_m['Bulan_Tahun']}** dengan rata-rata **Rp {max_m['Omzet_Per_Hari']:,.0f}/hari**, sedangkan terendah pada **{min_m['Bulan_Tahun']}** di tingkat **Rp {min_m['Omzet_Per_Hari']:,.0f}/hari**.".replace(",", "."))
            st.markdown(f"**💡 Rekomendasi:** Alokasikan anggaran promosi dan program *loyalty* tambahan pada periode mendekati **{min_m['Bulan_Tahun']}** guna mendongkrak omzet harian saat periode sepi.")
            st.markdown("---")

            # 2. Kontribusi Produk (Pareto 80/20)
            st.subheader("2. Kontribusi Produk terhadap Omzet (Analisis Pareto)")
            df_prod_contrib = df_p.copy()
            df_prod_contrib['Persentase'] = (df_prod_contrib['Total_Harga'] / df_prod_contrib['Total_Harga'].sum()) * 100

            fig_prod_contrib = px.bar(
                df_prod_contrib, 
                x='Nama_Produk', 
                y='Total_Harga', 
                text=df_prod_contrib['Persentase'].round(1).astype(str) + '%',
                labels={'Nama_Produk': 'Produk', 'Total_Harga': 'Total Omzet (Rp)'}
            )
            st.plotly_chart(fig_prod_contrib, use_container_width=True)

            tot_80_pct = df_prod_contrib[df_prod_contrib['Nama_Produk'].isin(top_80_prods)]['Persentase'].sum()
            st.markdown(f"**🔍 Temuan:** Produk **{top_prods_str}** secara kumulatif menyumbang **{tot_80_pct:.1f}%** dari total pendapatan.")
            st.markdown(f"**💡 Rekomendasi:** Fokuskan strategi ketersediaan stok (*never out-of-stock*) pada **{top_prods_str}** dan pertimbangkan skema *bundling* produk kurang laris dengan produk unggulan ini.")
            st.markdown("---")

            # 3. Performa Kota
            st.subheader("3. Performa Pertumbuhan Kota")
            df_city_trend = df_filtered.groupby(['Bulan_Tahun', 'Kota'])['Total_Harga'].sum().reset_index()
            fig_city = px.line(
                df_city_trend, 
                x='Bulan_Tahun', 
                y='Total_Harga', 
                color='Kota', 
                markers=True,
                labels={'Bulan_Tahun': 'Bulan', 'Total_Harga': 'Total Omzet (Rp)', 'Kota': 'Kota'}
            )
            st.plotly_chart(fig_city, use_container_width=True)

            if len(selected_kota) == 1:
                st.markdown(f"**🔍 Temuan:** Kota **{top_city}** menghasilkan total omzet sebesar **Rp {df_c.iloc[0]['Total_Harga']:,.0f}** selama periode analisis.".replace(",", "."))
                st.markdown(f"**💡 Rekomendasi:** Pertahankan performa pasar di **{top_city}** dengan memperkuat efisiensi operasional outlet.")
            else:
                st.markdown(f"**🔍 Temuan:** Kota **{top_city}** memimpin kontribusi omzet terbesar (Rp {df_c.iloc[0]['Total_Harga']:,.0f}), sementara **{low_city}** mencatatkan kinerja terendah (Rp {df_c.iloc[-1]['Total_Harga']:,.0f}).".replace(",", "."))
                st.markdown(f"**💡 Rekomendasi:** Evaluasi efektivitas kampanye lokal di **{low_city}** atau alokasikan ulang sebagian anggaran pemasaran ke kota **{top_city}** yang terbukti bertumbuh lebih cepat.")
            st.markdown("---")

            # 4. Jam dan Hari Tersibuk (Heatmap)
            st.subheader("4. Analisis Waktu Operasional Tersibuk")
            day_order = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
            df_heat = df_filtered.groupby(['Hari', 'Jam'])['ID_Transaksi'].count().reset_index(name='Jumlah_Transaksi')
            
            fig_heat = px.density_heatmap(
                df_heat, 
                x='Jam', 
                y='Hari', 
                z='Jumlah_Transaksi', 
                category_orders={"Hari": day_order},
                color_continuous_scale="Viridis",
                labels={'Jam': 'Jam Operasional', 'Hari': 'Hari', 'Jumlah_Transaksi': 'Jml Transaksi'}
            )
            st.plotly_chart(fig_heat, use_container_width=True)

            peak_count = df_h.iloc[0]['Jml'] if not df_h.empty else 0
            
            # Tambahan Jam Tersibuk secara Keseluruhan
            puncak = df_filtered["Jam"].value_counts()
            if not puncak.empty:
                st.markdown(f"🔍 Jam tersibuk secara keseluruhan: **{puncak.idxmax()}** ({fmt(puncak.max() / len(df_filtered) * 100)}% transaksi)")

            st.markdown(f"**🔍 Temuan Waktu Puncak:** Transaksi tertinggi spesifik terjadi pada hari **{peak_day}** pukul **{peak_jam}** dengan total **{peak_count} transaksi**.")
            st.markdown(f"**💡 Rekomendasi:** Jadwalkan kuota staf maksimum di hari **{peak_day}** sekitar pukul **{peak_jam}**, serta luncurkan promo *Happy Hour* pada jam-jam sepi untuk meratakan arus pengunjung.")
            st.markdown("---")

            # 5. Efek Diskon dan Metode Pembayaran (Menggunakan Uji Statistik & Format Kustom)
            st.subheader("5. Analisis Efek Diskon dan Metode Pembayaran")
            col_a, col_b = st.columns(2)

            df = df_filtered.copy() # Alias untuk mencocokkan snippet

            with col_a:
                st.markdown("**Analisis Efek Diskon**")
                
                # Uji signifikansi statistik diskon
                a = df.loc[df["Diskon_Persen"] > 0, "Jumlah_Cup"]
                b = df.loc[df["Diskon_Persen"] == 0, "Jumlah_Cup"]
                if len(a) > 1 and len(b) > 1:
                    se = (a.var() / len(a) + b.var() / len(b)) ** 0.5
                    bermakna = abs(a.mean() - b.mean()) > 1.96 * se if se > 0 else False
                    kesimpulan = ("selisih ini bermakna secara statistik" if bermakna else "selisih ini tidak bermakna secara statistik, jadi diskon belum terbukti menambah isi keranjang")
                else:
                    kesimpulan = "data sampel kurang untuk uji statistik"

                g = df.assign(diskon=df["Diskon_Persen"] > 0).groupby("diskon").agg(
                    n=("Total_Harga", "size"), cup=("Jumlah_Cup", "mean"), aov=("Total_Harga", "mean"))
                if len(g) == 2:
                    d_cup = (g.loc[True, "cup"] / g.loc[False, "cup"] - 1) * 100
                    d_aov = (g.loc[True, "aov"] / g.loc[False, "aov"] - 1) * 100
                    catatan = " Sampel kecil, hati-hati menyimpulkan." if g.loc[True, "n"] < 30 else ""
                    st.markdown(
                        f"🔍 **Temuan:** Transaksi berdiskon berisi {g.loc[True, 'cup']:.2f} cup vs "
                        f"{g.loc[False, 'cup']:.2f} tanpa diskon ({d_cup:+.1f}%), tetapi nilainya "
                        f"{abs(d_aov):.1f}% lebih rendah ({g.loc[True, 'n']} transaksi berdiskon). {kesimpulan}.{catatan}")
                
                # Grafik bar diskon pendukung
                df_disc = df.assign(Status_Diskon=df["Diskon_Persen"].apply(lambda x: 'Dengan Diskon' if x > 0 else 'Tanpa Diskon'))
                df_disc_agg = df_disc.groupby('Status_Diskon')['Total_Harga'].mean().reset_index()
                fig_disc = px.bar(
                    df_disc_agg, 
                    x='Status_Diskon', 
                    y='Total_Harga', 
                    text_auto='.0f',
                    labels={'Status_Diskon': 'Kategori', 'Total_Harga': 'Rata-rata Nilai Transaksi (Rp)'}
                )
                st.plotly_chart(fig_disc, use_container_width=True)

            with col_b:
                st.markdown("**Dominasi Metode Pembayaran**")
                
                # Metode bayar: konsisten pakai jumlah transaksi
                share = df["Metode_Bayar"].value_counts(normalize=True) * 100
                digital = share.reindex(["QRIS", "E-Wallet"]).sum()
                st.markdown(f"🔍 **{share.idxmax()}** adalah metode terbesar ({fmt(share.max())}% transaksi); "
                            f"QRIS + E-Wallet mencapai {fmt(digital)}%.")

                # Pie: hitung jumlah transaksi (tanpa values=...) dan kunci warna
                fig = px.pie(df, names="Metode_Bayar", hole=0.4, color="Metode_Bayar",
                             color_discrete_map={"QRIS": "#636EFA", "E-Wallet": "#00CC96",
                                                "Tunai": "#EF553B", "Debit": "#AB63FA"})
                st.plotly_chart(fig, use_container_width=True)

            st.markdown("**💡 Rekomendasi:** Evaluasi kembali besar penetapan diskon agar tidak menurunkan ukuran nilai keranjang secara drastis, serta jaga stabilitas operasional sistem pembayaran digital utama (QRIS & E-Wallet).")

else:
    st.info("👋 Silakan unggah file pada sidebar untuk melihat dashboard.")