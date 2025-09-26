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
import json

# from backend.kula.chatbot_optimized import ChatbotOptimized
from utils_aggregation import aggregate_csat, aggregation_ratio, aggregate_sum, sidebar_filters, aggregate_table_with_granularity, calculate_checker_accuracy
from streamlit_chatbox import *
from st_aggrid import AgGrid
from st_aggrid.grid_options_builder import GridOptionsBuilder
from collections import defaultdict
from datetime import datetime, timedelta
logging.getLogger('streamlit.runtime.scriptrunner').setLevel(logging.ERROR)

CURRENT_THEME = "light" 
IS_DARK_THEME = False
st.set_page_config(layout="wide")

team = st.sidebar.radio('Team', ['QC'])

if team == 'QC':
    page = st.sidebar.selectbox("Pages", ['Performance'])

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
                "Aulia": "pict/gawr_gura.png",
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
                    <div class="card">
                        <h5>Accuracy</h5>
                        <h3>{acc_value:.2f}%</h3>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                    <div class="card">
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
                    color_discrete_map={"Benar": "light blue", "Salah": "red"},
                    hole=0.45,
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
                    annotations=[dict(
                        text="ini apa ya",
                        font_size=14,
                        showarrow=False,
                        xanchor="center"
                    )],
                    margin=dict(t=20, b=20, l=20, r=20),
                    height=200,
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

        # account
        cols = st.columns([2, 4])
        