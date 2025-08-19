import os
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import logging
import pyperclip
import datetime
import difflib
from st_aggrid import AgGrid
from st_aggrid.grid_options_builder import GridOptionsBuilder
from collections import defaultdict
from datetime import datetime, timedelta
logging.getLogger('streamlit.runtime.scriptrunner').setLevel(logging.ERROR)

CURRENT_THEME = "light" 
IS_DARK_THEME = False
st.set_page_config(layout="wide")

team = st.sidebar.radio('Team', ['QC', 'KULA'])

if team == 'QC':
    st.sidebar.header("Adjust Data")

    page = st.sidebar.selectbox("Pages", ["Overview","Sampling","Audio Sample"])


    #Page 1
    if page == "Overview":
        def styled_metric(label, value, delta, delta_color="normal"):
            delta_symbol = "↑" if delta_color == "normal" else ("↓" if delta_color == "inverse" else "")
            delta_color_code = {
                "normal": "#28a745",     # hijau
                "inverse": "#dc3545",    # merah
                "off": "#999999"         # abu netral
            }.get(delta_color, "#000000")

            html = f"""
            <div style="
                border: 1px solid #ddd;
                border-radius: 10px;
                padding: 14px 16px;
                box-shadow: 0px 2px 6px rgba(0, 0, 0, 0.1);
                background-color: #fff;
                display: flex;
                flex-direction: column;
                gap: 6px;
            ">
                <div style="font-size: 14px; font-weight: semi-bold; color: #444; text-align: left;">
                    {label}
                </div>
                <div style="display: flex; flex-direction: column; align-items: flex-end;">
                    <div style="font-size: 24px; font-weight: bold; color: #111;">{value}</div>
                    <div style="font-size: 14px; font-weight: bold; color: {delta_color_code};">{delta_symbol} {delta:,}</div>
                </div>
            </div>
            """
            st.markdown(html, unsafe_allow_html=True)

        # Dashboard
        df = pd.read_csv('dataset_qc/new_4_clean.csv', parse_dates=['Tanggal Pengerjaan', 'Waktu Inbound'])

        # Filter "Tidak bisa di Play"
        df_filtered = df[df['Efektif'] != 'Tidak bisa di Play']

        # Sidebar Filters
        asi_afi_filter = st.sidebar.selectbox("ASI/AFI", ['All'] + df['ASI/AFI'].unique().tolist())
        checker_filter = st.sidebar.selectbox("Checker", ['All'] + df['Checker'].unique().tolist())
        date_range = st.sidebar.date_input("Tanggal Pengerjaan", [df['Tanggal Pengerjaan'].min(), df['Tanggal Pengerjaan'].max()])

        # Apply Filters
        mask = (
            (df['Tanggal Pengerjaan'].dt.date >= date_range[0]) &
            (df['Tanggal Pengerjaan'].dt.date <= date_range[1])
        )
        if asi_afi_filter != 'All':
            mask &= (df['ASI/AFI'] == asi_afi_filter)
        if checker_filter != 'All':
            mask &= (df['Checker'] == checker_filter)

        df_filtered = df_filtered[mask]

        # Score Cards
        with st.container():
            st.title("AI - Quality Control Dashboard")
            
            latest_date = df["Tanggal Pengerjaan"].max()
            latest_date_str = latest_date.strftime("%d/%m/%Y")

            st.markdown(f"##### Hotline - updated till {latest_date_str}")


            cols = st.columns(5)

            # Total Tagged berdasarkan pertambahan dari hari sebelumnya
            last_selected_date = date_range[1]
            day_before_last = last_selected_date - pd.Timedelta(days=1)

            # Hitung total data sampai hari sebelum tanggal terakhir
            total_before = df[
                (df['Tanggal Pengerjaan'].dt.date >= date_range[0]) &
                (df['Tanggal Pengerjaan'].dt.date <= day_before_last)
            ]
            count_before = len(total_before)

            # Hitung total data sampai tanggal terakhir
            total_until_last = df[
                (df['Tanggal Pengerjaan'].dt.date >= date_range[0]) &
                (df['Tanggal Pengerjaan'].dt.date <= last_selected_date)
            ]
            count_until_last = len(total_until_last)

            delta_tagged = count_until_last - count_before
            if delta_tagged > 0:
                delta_color_tagged = "normal"
            elif delta_tagged < 0:
                delta_color_tagged = "inverse"
            else:
                delta_color_tagged = "off"
            with cols[0]:
                st.markdown('<div class="metric-box">', unsafe_allow_html=True)
                styled_metric("Total Tagged", f"{count_until_last:,}", delta_tagged, delta_color_tagged)
                st.markdown('</div>', unsafe_allow_html=True)

            # Efektif Score Cards
            efektif_list = ['On Target/HC', 'On Target/Not HC', 'Miss Target/ Not HC', 'Miss Target/HC']
            last_selected_date = date_range[1]
            day_before_last = last_selected_date - pd.Timedelta(days=1)

            for i, label in enumerate(efektif_list):
                # Total hingga tanggal terakhir
                count_until_last = df[
                    (df['Tanggal Pengerjaan'].dt.date >= date_range[0]) &
                    (df['Tanggal Pengerjaan'].dt.date <= last_selected_date) &
                    (df['Efektif'] == label)
                ].shape[0]

                # Total hingga hari sebelumnya
                count_before = df[
                    (df['Tanggal Pengerjaan'].dt.date >= date_range[0]) &
                    (df['Tanggal Pengerjaan'].dt.date <= day_before_last) &
                    (df['Efektif'] == label)
                ].shape[0]

                delta = count_until_last - count_before
                if delta > 0:
                    delta_color = "normal"
                elif delta < 0:
                    delta_color = "inverse"
                else:
                    delta_color = "off"
                with cols[i + 1]:
                    st.markdown('<div class="metric-box">', unsafe_allow_html=True)
                    styled_metric(label, f"{count_until_last:,}", delta, delta_color)
                    st.markdown('</div>', unsafe_allow_html=True)

        st.markdown(
            "<h5 style='text-align: center;'>Current AI Accuracy: 91.04%</h5>",
            unsafe_allow_html=True
            )

        # Line Chart Graphic
        with st.container():
            # cols = st.columns([0.6,2.3])

            # #KPI
            # with cols[0]:
            #     st.markdown("")
            #     st.markdown("")
            #     st.markdown("##### 🎯 KPI Harian")
            #     st.markdown("""
            #     <div style="border: 1px solid #ddd; border-radius: 10px; padding: 14px 16px;
            #                 box-shadow: 0px 2px 6px rgba(0, 0, 0, 0.1); background-color: #fff; display: flex; flex-direction: column; gap: 6px;">
            #         <div><strong>HC:</strong> 200</div>
            #         <div><strong>Live Chat:</strong> 100</div>
            #         <div><strong>AI Summary:</strong> 30</div>
            #     </div>
            #     """, unsafe_allow_html=True)

            df_weekly = df_filtered.copy()
            df_weekly['Week'] = df_weekly['Tanggal Pengerjaan'].dt.to_period('W').apply(lambda r: r.start_time)

            # Grafik 1: Hanya kategori "Miss Target/ Not HC"
            df_miss_target_not_hc = df_weekly[df_weekly['Efektif'] == 'Miss Target/ Not HC']
            df_miss_group = df_miss_target_not_hc.groupby(['Week', 'Efektif']).size().reset_index(name='Count')

            # Urutkan Week dan ambil 2 minggu terakhir
            df_miss_group = df_miss_group.sort_values('Week')
            unique_weeks = df_miss_group['Week'].drop_duplicates().sort_values()
            last_2_weeks = unique_weeks.iloc[-1:].tolist()

            # Plot
            fig_miss = px.line(
                df_miss_group,
                x='Week',
                y='Count',
                color='Efektif',
                title='Weekly Trend: Miss Target/Not HC',
                text='Count'
            )
            fig_miss.update_traces(
                mode='lines+markers+text',
                textposition='top center',
                textfont=dict(size=12, color='black')
            )
            fig_miss.update_layout(
                yaxis=dict(title=None),
                legend=dict(
                    orientation="v",
                    yanchor="top",
                    y=1.1,
                    xanchor="right",
                    x=1
                )
            )
            st.plotly_chart(fig_miss, use_container_width=True)

            # Grafik 2: 3 kategori lainnya
            other_labels = ['Miss Target/HC', 'On Target/Not HC', 'On Target/HC']
            df_others = df_weekly[df_weekly['Efektif'].isin(other_labels)]
            df_others_group = df_others.groupby(['Week', 'Efektif']).size().reset_index(name='Count')
            fig_others = px.line(
                df_others_group,
                x='Week',
                y='Count',
                color='Efektif',
                title='Weekly Trends: Other Categories',
                text='Count'
            )
            fig_others.update_traces(
                mode='lines+markers+text',
                textposition = 'top center',
                textfont=dict(size=12, color='black')
            )
            fig_others.update_layout(
                yaxis=dict(title=None),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.1,
                    xanchor="left",
                    x=0.5
                )
            )
            st.plotly_chart(fig_others, use_container_width=True)
            
        with st.container():
            cols = st.columns(2)

            # Checker Doughnut Graph
            asr_result = df_filtered['Hasil ASR'].value_counts().reset_index()
            asr_result.columns = ['Kategori', 'Jumlah']
            total_asr = "{:,}".format(asr_result['Jumlah'].sum())

            # Doughnut Chart dengan label di luar dan garis penunjuk
            fig_asr = px.pie(
                asr_result,
                values='Jumlah',
                names='Kategori',
                hole=0.5,
                title='Hasil ASR',
                color='Kategori',
                color_discrete_map={
                    'Terdapat kesalahan': 'red',
                    'No Data': 'gray',
                    'Entri Akurat': 'light blue'
                }
            )

            fig_asr.update_traces(
                textposition='inside',  # Label di luar chart
                textinfo='label+percent',
                pull=[0.05]*len(asr_result),
                marker=dict(line=dict(color='white', width=2))
            )

            fig_asr.update_layout(
                showlegend=False,  # Set True jika ingin daftar legend di samping
                annotations=[dict(
                    text=f"Total<br>{total_asr}",
                    x=0.5,
                    y=0.5,
                    font_size=16,
                    showarrow=False
                )]
            )

            cols[0].plotly_chart(fig_asr, use_container_width=True)

            # ASI/AFI Bar Graph di kolom kedua
            asi_afi_count = df_filtered['ASI/AFI'].value_counts().reset_index()
            asi_afi_count.columns = ['ASI/AFI', 'Count']
            
            asi_afi_count['Percent'] = asi_afi_count['Count'] / asi_afi_count['Count'].sum() * 100
            asi_afi_count['Label'] = asi_afi_count.apply(lambda row: f"{row['Count']:,} Tag<br>({row['Percent']:.1f}%)", axis=1)

            fig_asi_afi = px.bar(
                asi_afi_count,
                x='ASI/AFI',
                y='Count',
                color='ASI/AFI',
                title='ASI vs AFI',
                text='Label',
                color_discrete_map={'ASI': '#1f77b4', 'AFI': 'RED'}
            )

            fig_asi_afi.update_traces(
                textposition='inside'
            )
            fig_asi_afi.update_layout(showlegend=False)

            cols[1].plotly_chart(fig_asi_afi, use_container_width=True)
        
        with st.container():
            cols = st.columns([1, 1])

            checker_count = df_filtered['Checker'].value_counts().reset_index()
            checker_count.columns = ['Checker', 'Count']
            total_checker = "{:,}".format(checker_count['Count'].sum())
            fig_checker = px.pie(
                checker_count,
                values='Count',
                names='Checker',
                hole=0.5,
                title='Checker Distribution'
            )
            fig_checker.update_traces(
                textposition='inside',
                textinfo='label+percent+value'
            )
            fig_checker.update_layout(
                showlegend=False,
                annotations=[dict(
                    text=f"Total<br>{total_checker}",
                    x=0.5,
                    y=0.5,
                    font_size=16,
                    
                    showarrow=False
                )]
            )
            cols[0].plotly_chart(fig_checker, use_container_width=True)


    #Page 2
    elif page == "Sampling":
        # ==== Scorecard Style ====
        def styled_metric(label, value, delta, delta_color="normal"):
            delta_symbol = "↑" if delta_color == "normal" else ("↑" if delta_color == "inverse" else "") #↓
            delta_color_code = {
                "normal": "#28a745",     # Merah
                "inverse": "#dc3545",    # hijau
                "off": "#999999"         # abu netral
            }.get(delta_color, "#000000")

            delta_text = f"{delta_symbol} {abs(delta):,} data" if delta_color != "off" else "-"

            html = f"""
            <div style="
                border: 1px solid #ddd;
                border-radius: 10px;
                padding: 14px 16px;
                box-shadow: 0px 2px 6px rgba(0, 0, 0, 0.1);
                background-color: #fff;
                display: flex;
                flex-direction: column;
                gap: 6px;
            ">
                <div style="font-size: 14px; font-weight: semi-bold; color: #444; text-align: left;">
                    {label}
                </div>
                <div style="display: flex; flex-direction: column; align-items: flex-end;">
                    <div style="font-size: 24px; font-weight: bold; color: #111;">{value}</div>
                    <div style="font-size: 14px; font-weight: bold; color: {delta_color_code};">{delta_text}</div>
                </div>
            </div>
            """
            st.markdown(html, unsafe_allow_html=True)

        df_sampling = pd.read_csv('dataset_qc/kalib_sampling.csv', parse_dates=['Tanggal Sampling'])

        # ==== Layout ====
        st.title("Sampling Data")

        latest_date = df_sampling["Tanggal Sampling"].max()
        latest_date_str = latest_date.strftime("%d/%m/%Y")

        st.markdown(f"##### Updated Till {latest_date_str}")

        # ==== Filter Tanggal ====
        min_date = df_sampling['Tanggal Sampling'].min().date()
        max_date = df_sampling['Tanggal Sampling'].max().date()

        start_date, end_date = st.sidebar.date_input(
            "Pilih Rentang Tanggal",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )

        # Konversi ke datetime
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)

        # Filter DataFrame berdasarkan tanggal
        df_sampling = df_sampling[
            (df_sampling['Tanggal Sampling'] >= start_date) &
            (df_sampling['Tanggal Sampling'] <= end_date)
        ]

        # ==== Filter RED LABEL ====
        df_merah = df_sampling[
            df_sampling['Red Label'].str.upper().isin(["MERAH", "TEXT"])
        ]

        # ==== Hitung Persentase ====
        total_data = len(df_sampling)
        total_merah = len(df_merah)
        persen_merah = (total_merah / total_data) * 100
        persen_non_merah = 100 - persen_merah

        # ==== Scorecards ====
        with st.container():

            # Hitung total
            total_data = len(df_sampling)
            total_merah = len(df_merah)
            total_tidak_merah = total_data - total_merah

            # Ambil tanggal terakhir dan hari sebelumnya
            last_selected_date = end_date.date()
            day_before_last = (end_date - pd.Timedelta(days=1)).date()

            # Filter data Sampling untuk hari terakhir
            df_this_day = df_sampling[df_sampling['Tanggal Sampling'].dt.date == last_selected_date]
            df_last_day = df_sampling[df_sampling['Tanggal Sampling'].dt.date == day_before_last]

            # === Jumlah Hari Ini ===
            total_this_day = df_this_day.shape[0]
            merah_this_day = df_this_day[
                df_this_day['Red Label'].str.upper().str.contains('MERAH') +
                df_this_day['Red Label'].str.upper().str.contains('TEXT')
                ].shape[0]

            non_merah_this_day = df_this_day[df_this_day['Red Label'].str.upper() != 'MERAH'].shape[0]

            # === Delta ===
            delta_total = total_this_day
            delta_merah = merah_this_day
            delta_non_merah = non_merah_this_day

            # === Warna Panah ===
            delta_color_total = "normal"
            delta_color_non_merah = "normal"
            delta_color_merah = "inverse"

            # Tampilkan scorecard
            cols = st.columns(3)
            with cols[0]:
                styled_metric("TOTAL SAMPLING", f"{total_data:,} data", delta_total, delta_color_total)
            with cols[1]:
                styled_metric("MERAH & TEXT", f"{total_merah:,} data", delta_merah, delta_color_merah)
            with cols[2]:
                styled_metric("TIDAK MERAH", f"{total_tidak_merah:,} data", delta_non_merah, delta_color_non_merah)

        # ==== Weekly Trend Line Chart ===
        df_sampling['Week'] = df_sampling['Tanggal Sampling'].dt.to_period('W').apply(lambda r: r.start_time)

        # Pisahkan berdasarkan Red Label
        df_merah = df_sampling[df_sampling['Red Label'].str.upper() == "MERAH"]
        df_text = df_sampling[df_sampling['Red Label'].str.upper() == "TEXT"]

        # Hitung jumlah per minggu
        df_merah_weekly = df_merah.groupby('Week').size().reset_index(name='Jumlah')
        df_text_weekly = df_text.groupby('Week').size().reset_index(name='Jumlah')

        # Pastikan kolom 'Week' jadi datetime agar bisa digabung
        df_merah_weekly['Week'] = pd.to_datetime(df_merah_weekly['Week'])
        df_text_weekly['Week'] = pd.to_datetime(df_text_weekly['Week'])

        # ==== Buat Figure manual ====
        fig_line = go.Figure()

        # Tambahkan garis MERAH
        fig_line.add_trace(go.Scatter(
            x=df_merah_weekly['Week'],
            y=df_merah_weekly['Jumlah'],
            mode='lines+markers+text',
            name='MERAH',
            line=dict(color='#dc3545', width=2, dash='solid'),
            text=df_merah_weekly['Jumlah'],
            textposition='top center'
        ))

        # Tambahkan garis TEXT (dashed)
        fig_line.add_trace(go.Scatter(
            x=df_text_weekly['Week'],
            y=df_text_weekly['Jumlah'],
            mode='lines+markers+text',
            name='TEXT',
            line=dict(color='#f4a261', width=2, dash='dash'),
            text=df_text_weekly['Jumlah'],
            textposition='top center'
        ))

        # Layout
        fig_line.update_layout(
            title='Weekly Trend',
            xaxis_title='Minggu',
            yaxis_title='Jumlah',
            plot_bgcolor='#fff',
            hovermode='x unified',
            legend=dict(orientation="h", y=1.2, x=1, xanchor="right")
        )

        st.plotly_chart(fig_line, use_container_width=True)


        # ==== Doughnut Chart ====
        with st.container():
            cols = st.columns([2, 3])

            total_merah = df_sampling['Red Label'].str.upper().isin(['MERAH', 'TEXT']).sum()
            total_tidak_merah = total_data - total_merah

            pie_df = pd.DataFrame({
                'Label': ['Red Data', 'Not Red'],
                'Jumlah': [total_merah, total_tidak_merah]
            })

            fig_pie = px.pie(
                pie_df,
                names='Label',
                values='Jumlah',
                hole=0.5,
                title='Persentase',
                color='Label',
                color_discrete_map={
                    'Red Data': 'red',
                    'Not Red': "light blue"
                }
            )
            fig_pie.update_traces(
                textposition='inside',
                textinfo='label+percent+value',
                textfont = dict(color='white')
            )
            fig_pie.update_layout(
                showlegend=False,
                annotations=[dict(
                    text=f"Total<br>{total_data:,}",
                    x=0.5, y=0.5,
                    font_size=16,
                    showarrow=False
                )]
            )
            cols[0].plotly_chart(fig_pie, use_container_width=True)

        # ==== Weekly Bar Chart: Jumlah Merah ====
        df_merah_weekly = df_merah.groupby('Week').size().reset_index(name='MERAH')
        df_text_weekly = df_text.groupby('Week').size().reset_index(name='TEXT')

        # Gabungkan data
        df_bar = pd.merge(df_merah_weekly, df_text_weekly, on='Week', how='outer').fillna(0)
        df_bar = df_bar.sort_values(by='Week')

        # Ubah ke long format untuk stacked bar
        df_melted_bar = df_bar.melt(id_vars='Week', value_vars=['MERAH', 'TEXT'], var_name='Label', value_name='Jumlah')

        # Stacked Bar Chart
        fig_bar = px.bar(
            df_melted_bar,
            x='Week',
            y='Jumlah',
            color='Label',
            title='Jumlah Sampling per Minggu',
            text='Jumlah',
            color_discrete_map={
                'MERAH': '#dc3545',
                'TEXT': '#f4a261'
            }
        )
        fig_bar.update_layout(
            barmode='stack',
            xaxis_title=None,
            yaxis_title=None,
            plot_bgcolor="#fff",
            hovermode="x unified",
            legend=dict(orientation="h", y=1.15, x=0, xanchor="left")
        )
        fig_bar.update_traces(
            textposition='inside'
        )
        cols[1].plotly_chart(fig_bar, use_container_width=True)


    # Page 3
    elif page == "Audio Sample":
        st.title("Audio Sample")

        def highlight_diff_words(original, revised):
            """
            Mengembalikan string HTML yang menandai kata-kata berbeda dalam `revised` dibandingkan `original` dengan warna merah.
            """
            original_words = original.split()
            revised_words = revised.split()
            s = difflib.SequenceMatcher(None, original_words, revised_words)
            result = []

            for tag, i1, i2, j1, j2 in s.get_opcodes():
                if tag == "equal":
                    result.extend(revised_words[j1:j2])
                elif tag in ("replace", "insert"):
                    for word in revised_words[j1:j2]:
                        result.append(f"<span style='color: red'>{word}</span>")
                elif tag == "delete":
                    continue  # tidak perlu menampilkan kata yang dihapus

            return " ".join(result)

        # Load data
        df = pd.read_csv("dataset_qc/weekly_calibration_data.csv")
        df.columns = df.columns.str.strip()
        df = df.fillna("")
        df["Tanggal Meeting"] = pd.to_datetime(df["Tanggal Meeting"], errors="coerce").dt.date

        meeting_data = {}

        for _, row in df.iterrows():
            tanggal_meeting = row["Tanggal Meeting"]
            checker = row["Checker"]
            agent = row["Agent Sampling"]

            # Ambil nama file audio
            audio_filename = str(row.get("File Audio", "")).strip()
            audio_file = f"audio/{audio_filename}" if audio_filename else None

            # Siapkan teks kalibrasi
            sections = []

            mapping = [
                ("Hasil ASR", "Text Awal Hasil ASR", "ASR"),
                ("Hasil Pemeriksaan Kualitas", "Text Awal Hasil Pemeriksaan Kualitas", "Hasil Pemeriksaan Kualitas" ),
                ("Efektif", "Text Awal Efektif", "Efektif"),
                ("Kejelasan Suara", "Text Awal Kejelasan Suara", "Kejelasan Suara"),
                ("Suara Lain", "Text Awal Suara Lain", "Suara Lain"),
                ("Kelengkapan Rekaman", "Text Awal Kelengkapan Rekaman", "Kelengkapan Rekaman"),
                ("Revisi Teks", "Text Awal Revisi Text", "Revisi Teks")
            ]

            for final_col, awal_col, label in mapping:
                text_awal = str(row[awal_col]).strip()
                hasil = str(row[final_col]).strip()

                if text_awal:
                    if label == "Revisi Teks" and hasil:
                        hasil_diff = highlight_diff_words(text_awal, hasil)
                        hasil_markdown = f"**{label}:** {text_awal}  \n**Diubah:** <span>{hasil_diff}</span>  \n"
                        sections.append(hasil_markdown)
                    else:
                        sections.append(f"**{label}:** {text_awal}  \n**Diubah:** {hasil}  \n")


            if not sections and not audio_filename:
                continue

            entry = {
                "checker": checker,
                "agent": agent,
                "text": f"**Checker:** {checker}" + ("\n\n" + "\n".join(sections) if sections else ""),
                "file": audio_file
            }

            if tanggal_meeting not in meeting_data:
                meeting_data[tanggal_meeting] = []

            meeting_data[tanggal_meeting].append(entry)


        # === Sidebar: Pilih tanggal ===
        selected_date = st.sidebar.date_input(
            "Tanggal Meeting",
            value=max(meeting_data.keys()),  #default
            min_value=min(meeting_data.keys()),
            max_value=max(meeting_data.keys())
        )

        if selected_date not in meeting_data:
            st.warning(f"Tidak ada data untuk tanggal {selected_date.strftime('%d %B %Y')}.")
            st.stop()

        # Date filter
        manual_order = ["Neneng","Aulia", "Azer", "Reza"]
        agent_list = [agent for agent in manual_order if agent in {entry["agent"] for entry in meeting_data[selected_date]}]
        selected_agent = st.sidebar.radio("Agent Sampling", agent_list)

        st.markdown(f"### {selected_agent}")

        filtered_entries = [
            item for item in meeting_data[selected_date]
            if item["agent"] == selected_agent
        ]

        for i in range(0, len(filtered_entries), 3):
            row_entries = filtered_entries[i:i+3]
            cols = st.columns(3)

            for col, item in zip(cols, row_entries):
                with col:
                    with st.expander(f"Audio {i + filtered_entries.index(item) + 1}"):
                        st.markdown(item["text"], unsafe_allow_html=True)
                        if item["file"]:
                            try:
                                st.audio(item["file"])
                            except Exception as e:
                                st.error(f"Audio Restricted")


elif team == 'KULA':
    st.title("Dashboard KULA")
    # st.markdown('#####')

    # Chart 1: Ratio Success Rate
    df_ratio = pd.read_csv('dataset_kula/success_ratio.csv')
    df_ratio['Date'] = pd.to_datetime(df_ratio['Date'])

    # Default range: 2 minggu terakhir
    end_date = df_ratio['Date'].max()
    start_date = end_date - timedelta(days=13)  # total 14 hari termasuk hari ini

    # Tampilkan date range filter
    selected_range = st.sidebar.date_input(
        "Select Date",
        value=(start_date, end_date),
        min_value=df_ratio['Date'].min(),
        max_value=df_ratio['Date'].max()
    )

    # Filter data berdasarkan tanggal
    if isinstance(selected_range, tuple) and len(selected_range) == 2:
        start, end = selected_range
        filtered_df = df_ratio[(df_ratio['Date'] >= pd.to_datetime(start)) & (df_ratio['Date'] <= pd.to_datetime(end))]
    else:
        filtered_df = df_ratio.copy()

    # point on line
    fig = px.line(
        filtered_df.sort_values('Date'),
        x='Date',
        y='Robot Success ratio',
        title='Ratio Success Rate 机器人有效拦截率',
        markers=True,
        text='Robot Success ratio'
    )

    fig.update_traces(
        textposition="top center",
        texttemplate='%{text:.2f}%'
    )

    fig.update_layout(
        xaxis_title='',
        yaxis_title='Success Ratio (%)',
        yaxis_ticksuffix='%',
        yaxis=dict(range=[60,70]),
        template='plotly_white'
    )

    st.plotly_chart(fig, use_container_width=True)


    # Chart 2: CSAT Robot

    df_csat = pd.read_csv('dataset_kula/csat.csv')
    
    df_csat['Date'] = pd.to_datetime(df_csat['Date'])

    if isinstance(selected_range, tuple) and len(selected_range) == 2:
        start, end = selected_range
        filtered_df = df_csat[(df_csat['Date'] >= pd.to_datetime(start)) & (df_csat['Date'] <= pd.to_datetime(end))]
    else:
        filtered_df = df_csat.copy()

    fig = px.line(
        filtered_df.sort_values('Date'),
        x='Date',
        y='CSAT',
        title='CSAT Robot 机器人用户满意度',
        markers=True,
        text='CSAT'
    )

    fig.update_traces(
        textposition='top center',
        texttemplate='%{text:.2f}'
    )

    fig.update_layout(
        xaxis_title='',
        yaxis_title='CSAT',
        yaxis_ticksuffix='',
        yaxis=dict(range=[1,5]),
        template='plotly_white'
    )

    st.plotly_chart(fig, use_container_width=True)

    # Load data bad survey
    
    df_bad_survey = pd.read_csv('dataset_kula/bad_survey.csv')

    # Pastikan kolom tanggal dalam format datetime
    df_bad_survey['Conversation Start Time'] = pd.to_datetime(df_bad_survey['Conversation Start Time'], errors='coerce')

    # Sidebar filter untuk Company
    company_filter = st.sidebar.multiselect(
        "Select Company",
        options=["ASI", "AFI", "No Differentiated", "AFI/ASI"],
        default=["ASI"]
    )

    def get_nearest_tuesday_thursday(today=None):
        if today is None:
            today = datetime.today().date()

        weekday = today.weekday()

        # cari selasa minggu ini & depan
        tuesday_this_week = today - timedelta(days=(weekday - 1)) if weekday >= 1 else today + timedelta(days=(1 - weekday))
        tuesday_next_week = tuesday_this_week + timedelta(days = 7)

        # cari kamis minggu ini & depan
        thursday_this_week = today - timedelta(days=(weekday - 3)) if weekday >= 3 else today + timedelta(days=(3 - weekday))
        thursday_next_week = thursday_this_week + timedelta(days = 7)

        # aturan khusus
        if weekday == 1:
            return thursday_this_week - timedelta(days=7)
        elif weekday == 3:
            return tuesday_next_week

        # hitung jarak ke selasa & kamis terdekat
        distance_to_tuesday = min(abs((tuesday_this_week - today).days), abs((tuesday_next_week - today).days))
        distance_to_thursday = min(abs((thursday_this_week - today).days), abs((tuesday_next_week - today).days))

        if distance_to_tuesday <= distance_to_thursday:
            if abs((tuesday_this_week - today).days) <= abs((tuesday_next_week - today).days):
                return tuesday_this_week
            else:
                return tuesday_next_week
        else:
            if abs((thursday_this_week - today).days) <= abs((thursday_next_week - today).days):
                return tuesday_this_week
            else:
                return thursday_next_week
    
    default_date = get_nearest_tuesday_thursday()

    # Sidebar filter: Tanggal (hanya 1 tanggal)
    min_date = df_bad_survey['Conversation Start Time'].min().date()
    max_date = df_bad_survey['Conversation Start Time'].max().date()

    selected_date = st.sidebar.date_input(
        "Select Bad Survey & Dislike Date",
        value=default_date,
        min_value=min_date,
        max_value=max_date
    )

    # Filter berdasarkan 1 tanggal (tanpa jam)
    selected_date = pd.to_datetime(selected_date)
    df_bad_survey = df_bad_survey[
        df_bad_survey['Conversation Start Time'].dt.date == selected_date.date()
    ]

    # Terapkan filter
    if company_filter:
        df_bad_survey = df_bad_survey[df_bad_survey['Business Type'].isin(company_filter)]

    # Hitung Sub Category Summary
    subcat_summary = df_bad_survey['Sub Category'].value_counts().reset_index()
    subcat_summary.columns = ['Sub Category', 'Total Sample']
    subcat_summary['Percentage'] = (subcat_summary['Total Sample'] / subcat_summary['Total Sample'].sum() * 100).round(2).astype(str) + '%'

    # Hitung QC Result
    cat_summary = df_bad_survey['QC Result'].value_counts().reset_index()
    cat_summary.columns = ['Category', 'Total Sample']
    cat_summary['Percentage'] = (cat_summary['Total Sample'] / cat_summary['Total Sample'].sum() * 100).round(2).astype(str) + '%'

    # Tampilkan di dashboard AGGrid
    st.markdown("##### Bad Survey")
    with st.container():
        cols = st.columns([0.5, 0.45])

        with cols[0]:
            gd1 = GridOptionsBuilder.from_dataframe(subcat_summary)
            gd1.configure_pagination()
            gd1.configure_default_column(sortable=True, resizable=True)
            gd1.configure_column("Total Sample", filter=False)
            grid_options1 = gd1.build()
            AgGrid(subcat_summary, gridOptions=grid_options1, height=300)

        with cols[1]:
            gd2 = GridOptionsBuilder.from_dataframe(cat_summary)
            gd2.configure_pagination()
            gd2.configure_default_column(sortable=True, resizable=True)
            gd2.configure_column("Total Sample", filter=False)
            grid_options2 = gd2.build()
            AgGrid(cat_summary, gridOptions=grid_options2, height=300)

    # Like and Dislike
    st.markdown('##### Like and Dislike')
    with st.container():
        cols = st.columns([1,4])
        
        #The Linechart
        df_like_dislike = pd.read_csv('dataset_kula/kula_like_dislike.csv')
        df_like_dislike['Date'] = pd.to_datetime(df_like_dislike['Date'])

        #filter data berdasarkan tanggal
        if isinstance(selected_range, tuple) and len(selected_range) == 2:
            start, end = selected_range
            df_like_dislike = df_like_dislike[
                (df_like_dislike['Date'] >= pd.to_datetime(start)) &
                (df_like_dislike['Date'] <= pd.to_datetime(end))
            ]

        # Agregasi total Like & Dislike per hari
        df_daily = df_like_dislike.groupby('Date').agg(
            Like=('solved_num', 'sum'),
            Dislike=('unsolved_num', 'sum')
        ).reset_index()
        
        #The BarGraph Chart
        latest_date = df_daily['Date'].max()
        latest_data = df_daily[df_daily['Date'] == latest_date].melt(
            id_vars='Date',
            value_vars=['Like', 'Dislike'],
            var_name='Category',
            value_name='Total'
        )

        # Bar chart
        bar_fig = px.bar(
            latest_data,
            x='Category',
            y='Total',
            color='Category',
            color_discrete_map={'Like': 'light blue','Dislike': 'red'},
            text='Total'
        )

        bar_fig.update_traces(textposition='inside')
        bar_fig.update_layout(
            yaxis_title='Jumlah',
            xaxis_title=None,
            showlegend=False,
            template='plotly_white'
        )

        # Tampilkan di kolom kiri
        cols[0].plotly_chart(bar_fig, use_container_width=True)


        # Plot line chart
        fig = go.Figure()

        # Like
        fig.add_trace(go.Scatter(
            x=df_daily['Date'],
            y=df_daily['Like'],
            mode='lines+markers+text',
            name='Like',
            text=df_daily['Like'],
            textposition='top center'
        ))

        # Dislike
        fig.add_trace(go.Scatter(
            x=df_daily['Date'],
            y=df_daily['Dislike'],
            mode='lines+markers+text',
            name='Dislike',
            line=dict(color='red'),
            text=df_daily['Dislike'],
            textposition='top center'
        ))

        fig.update_layout(
            yaxis=dict(title=None),
            legend=dict(
                orientation="v",
                yanchor="top",
                y=1.1,
                xanchor="right",
                x=1
            )
        )

        cols[1].plotly_chart(fig, use_container_width=True)

    # Tabel data category like and dislike
    df_like_dislike['unsolved_num'] = pd.to_numeric(df_like_dislike['unsolved_num'], errors='coerce').fillna(0)

    # Filter data berdasarkan date range & company jika perlu
    df_like_dislike = df_like_dislike[
        df_like_dislike['Date'].dt.date == selected_date.date()
    ]

    if company_filter:  # multiselect
        df_like_dislike = df_like_dislike[df_like_dislike['Manual Check [business]'].isin(company_filter)]

    # ===== Table 1: Berdasarkan Team/Category =====
    team_summary = (
        df_like_dislike.groupby('Team/Category')
        .agg(
            **{
                'Total Like': ('solved_num', 'sum'),
                'Total Dislike': ('unsolved_num', 'sum')
            }
        )
        .reset_index()
    )

    team_summary['Total Feedback'] = team_summary['Total Like'] + team_summary['Total Dislike']
    team_summary = team_summary.sort_values('Total Feedback', ascending=False)

    # ===== Table 2: Berdasarkan Background detail =====
    bg_summary = (
        df_like_dislike.groupby('Background detail')
        .agg(
            **{
                'Total Like': ('solved_num', 'sum'),
                'Total Dislike': ('unsolved_num', 'sum')
            }
        )
        .reset_index()
    )

    bg_summary['Total Feedback'] = bg_summary['Total Like'] + bg_summary['Total Dislike']
    bg_summary = bg_summary.sort_values('Total Feedback', ascending=False)

    # ===== Tampilkan di dashboard =====
    st.markdown("##### Like & Dislike Summary")
    with st.container():
        cols = st.columns([0.45, 0.5])

        with cols[0]:
            gd1 = GridOptionsBuilder.from_dataframe(team_summary)
            gd1.configure_pagination()
            gd1.configure_default_column(sortable=True, resizable=True)
            gd1.configure_column("Total Feedback", filter=False)
            grid_options1 = gd1.build()
            AgGrid(team_summary, gridOptions=grid_options1, height=400)

        with cols[1]:
            gd2 = GridOptionsBuilder.from_dataframe(bg_summary)
            gd2.configure_pagination()
            gd2.configure_default_column(sortable=True, resizable=True)
            gd2.configure_column("Total Feedback", filter=False)
            grid_options2 = gd2.build()
            AgGrid(bg_summary, gridOptions=grid_options2, height=400)