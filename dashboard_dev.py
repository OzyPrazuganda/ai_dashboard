import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import logging
import datetime
import difflib

# from backend.kula.chatbot_optimized import ChatbotOptimized
from utils_aggregation_dev import aggregation_ratio, aggregate_sum, sidebar_filters, aggregate_table_with_granularity, calculate_checker_accuracy, aggregate_checker_errors, week_of_month, aggregate_csat_dual
from streamlit_chatbox import *
from st_aggrid import AgGrid
from st_aggrid.grid_options_builder import GridOptionsBuilder
from datetime import datetime, timedelta

logging.getLogger('streamlit.runtime.scriptrunner').setLevel(logging.ERROR)

CURRENT_THEME = "light" 
IS_DARK_THEME = False
st.set_page_config(layout="wide")

team = st.sidebar.radio('Team', ['QC'])

if team == 'QC':

    page = st.sidebar.selectbox("Pages", ["Performance"])

        # Page 4
    if page == 'Performance':
        df_sampling = pd.read_csv(
            'dataset_qc/kalib_sampling.csv',
            parse_dates=['Tanggal Sampling']
        )
        
        # Filter
        df_sampling = df_sampling[df_sampling['Agent Sampling'] != 'No Data']
        validator = st.sidebar.radio('Validators', df_sampling['Agent Sampling'].unique())

        # Custom CSS for card style
        st.markdown("""
            <style>
            .card {
                background-color: #ffffff;
                border-radius: 12px;
                padding: 20px;
                box-shadow: 0px 2px 10px rgba(0,0,0,0.1);
                text-align: center;
            }
            
            .card p {
                margin: 0;
                font-size: 14px;
                color: gray;
            }
            </style>
        """, unsafe_allow_html=True)

        # Accuracy Data
        acc_df = calculate_checker_accuracy(df_sampling)
        acc_row = acc_df[acc_df["Checker"] == validator]
        
        total_tagging = acc_row["Total_Tagging"].values[0] if not acc_row.empty else 0
        kesalahan = acc_row["Kesalahan"].values[0] if not acc_row.empty else 0
        acc_value = acc_row["Accuracy"].values[0] if not acc_row.empty else None

        benar = total_tagging - kesalahan if total_tagging > 0 else 0

        # Layout
        cols = st.columns([2, 3, 3, 4])

        # Image column
        with cols[0]:
            images = {
                "Aulia": "pict/aul.png",
                "Reza": "pict/reza.png",
                "Neneng": "pict/neneng.png",
                "Azer": "pict/azer.png"
                # Add other mappings if needed
            }
            if validator in images:
                st.image(images[validator], width=200)

        # Info card
        with cols[1]:
            st.markdown(f"""
                <div class="card", style="text-align: left;">
                    <h3>{validator}</h3>
                    <p>Quality Control Specialist</p>
                    <br>
                </div>
            """, unsafe_allow_html=True)

        # Accuracy card
        with cols[2]:
            if acc_value is not None:
                st.markdown(f"""
                    <div class="card" style="
                        display: flex;
                        flex-direction: column;
                        justify-content: center;
                        align-items: center;
                        text-align: center;
                        padding: 20px;
                    ">
                        <h5>Accuracy</h5>
                        <h3>{acc_value:.2f}%</h3>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                    <div class="card" style="
                        display: flex;
                        flex-direction: column;
                        justify-content: center;
                        align-items: center;
                        text-align: center;
                        padding: 20px;
                    ">
                        <h6>Accuracy</h6>
                        <h3>-</h3>
                        <p>No data</p>
                    </div>
                """, unsafe_allow_html=True)


        # Tag Count card
        with cols[3]:
            if total_tagging > 0:
                pie_data = {
                    "Category": ["Benar", "Salah"],
                    "Count": [benar, kesalahan]
                }
                fig = px.pie(
                    pie_data,
                    values="Count",
                    names="Category",
                    color="Category",
                    color_discrete_map={"Salah": "#5fa8d3", "Benar": "#1b4965"},
                    hole=0.65,
                    title='Tag Count'
                )
                fig.update_traces(
                    textposition='inside',
                    textinfo='value',
                    pull=[0.05]*len([pie_data]),
                    marker=dict(line=dict(color='white', width=2)),
                    insidetextorientation='horizontal'
                )
                fig.update_layout(
                    showlegend=False,
                    title=dict(
                        x=0.5,
                        xanchor='center',
                        yanchor='top'
                    ),
                    margin=dict(t=40, b=20, l=20, r=20),
                    height=240,
                    annotations=[dict(
                        text="{}<br>Tagged".format(total_tagging),
                        font_size=14,
                        showarrow=False,
                        xanchor="center"
                    )],
                )

                # Masukkan ke card container
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.markdown("""
                    <div class="card">
                        <h6>Tagging Result</h6>
                        <p>No data</p>
                    </div>
                """, unsafe_allow_html=True)

        # radar chart
        cols = st.columns([3,5])
        with cols[0]:
            df_checker, count_cols = aggregate_checker_errors(df_sampling)

            row = df_checker[df_checker["Checker"] == validator].iloc[0]

            r = row[count_cols].values.tolist()
            theta = count_cols

            theta_clean = [t.replace("Count ", "") for t in theta]

            fig = go.Figure()

            fig.add_trace(
                go.Scatterpolar(
                    r=r + [r[0]],
                    theta=theta_clean + [theta_clean[0]], 
                    fill='toself',
                    name=validator,
                    line=dict(color='crimson')
                )
            )

            fig.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, max(r)+2])),
                showlegend=False,
                width=300,
                height=300,
                margin=dict(l=30, r=30, t=2, b=30)
            )

            st.plotly_chart(fig, use_container_width=True)
        
        # Barchart mistake per week
        with cols[1]:
            # Pastikan kolom datetime benar
            if not pd.api.types.is_datetime64_any_dtype(df_sampling['Tanggal Sampling']):
                df_sampling['Tanggal Sampling'] = pd.to_datetime(df_sampling['Tanggal Sampling'])

            # Ambil bulan & tahun unik dari data
            available_months = df_sampling['Tanggal Sampling'].dt.to_period('M').unique()
            available_months = sorted(available_months)

            # Konversi ke format label misalnya "Oktober 2025"
            month_labels = [p.strftime("%B %Y") for p in available_months]

            # Sidebar pilih bulan
            selected_month_label = st.sidebar.selectbox("Pilih Bulan", month_labels)
            selected_period = available_months[month_labels.index(selected_month_label)]

            # Filter data sesuai bulan & tahun yang dipilih
            df_current = df_sampling[(df_sampling['Tanggal Sampling'].dt.month == selected_period.month) &
                                     (df_sampling['Tanggal Sampling'].dt.year == selected_period.year)]

            # Tambahkan kolom week
            df_current['week'] = df_current['Tanggal Sampling'].apply(week_of_month)

            # Hitung minggu maksimal yang bisa dipilih
            if (selected_period.month == datetime.now().month) and (selected_period.year == datetime.now().year):
                current_week = week_of_month(datetime.now())
            else:
                current_week = df_current['week'].max()

            week_labels = [f"week {i}" for i in range(1, current_week + 1)]

            # Sidebar filter untuk minggu
            week1_label = st.sidebar.selectbox('First Chart', week_labels)
            week2_label = st.sidebar.selectbox('Second Chart', week_labels)

            week1_num = int(week1_label.split()[-1])
            week2_num = int(week2_label.split()[-1])

            # Filter data sesuai validator & minggu
            df_week1 = df_current[(df_current['Checker'] == validator) & 
                                (df_current['week'] == week1_num)]

            df_week2 = df_current[(df_current['Checker'] == validator) & 
                                (df_current['week'] == week2_num)]

            # Variabel yang dipakai
            variables = ['Count Kejelasan Suara', 'Count Efektif', 'Count Hasil Pemeriksaan Kualitas',
                        'Count Hasil ASR', 'Count Revisi Text', 'Count Kelengkapan Rekaman']

            week1_counts = [df_week1[var].sum() for var in variables]
            week2_counts = [df_week2[var].sum() for var in variables]

            # Bersihkan nama variabel (hapus "Count ")
            clean_labels = [v.replace("Count ", "") for v in variables]

            # Plot horizontal bar chart
            fig = go.Figure()

            fig.add_trace(go.Bar(
                y=clean_labels,
                x=week2_counts,
                name=week2_label,
                marker_color='crimson',
                orientation='h',
                text=week2_counts,
                textposition='outside'
            ))

            fig.add_trace(go.Bar(
                y=clean_labels,
                x=week1_counts,
                name=week1_label,
                marker_color='lightslategrey',
                orientation='h',
                text=week1_counts,
                textposition='outside'
            ))

            fig.update_layout(
                barmode='group',
                xaxis_title='Jumlah Kesalahan',
                yaxis_title='Kategori Kesalahan',
                template='plotly_white',
                height=400,
                margin=dict(l=0, r=0, t=0, b=0),
                xaxis=dict(showgrid=True, gridcolor='lightgrey', gridwidth=0.5),
                yaxis=dict(showgrid=True, gridcolor='lightgrey', gridwidth=0.5)
            )

            st.plotly_chart(fig, use_container_width=True)