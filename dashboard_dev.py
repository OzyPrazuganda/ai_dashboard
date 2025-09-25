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
        df_sampling = pd.read_csv('dataset_qc/kalib_sampling.csv', parse_dates=['Tanggal Sampling'])
        
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
                margin: 10px;
                text-align: center;
            }
            .card img {
                border-radius: 8px;
                max-width: 100%;
            }
            </style>
        """, unsafe_allow_html=True)

        cols = st.columns([2, 4, 4, 4])

        with cols[0]:
            if validator == 'Aulia':
                st.image('pict/gawr_gura.png', width=200)

        with cols[1]:
            st.markdown(f"""
                <div class="card", style="text-align: left;">
                    <h3>{validator}</h3>
                    <p>Quality Control Specialist</p>
                </div>
            """, unsafe_allow_html=True)

        # Accuracy
        with cols[2]:
            acc_df = calculate_checker_accuracy(df_sampling)
            
            # filter sesuai validator yang dipilih di sidebar
            acc_row = acc_df[acc_df["Checker"] == validator]
            
            if not acc_row.empty:
                acc_value = acc_row["Accuracy"].values[0]
                total_tagging = acc_row["Total_Tagging"].values[0]
                kesalahan = acc_row["Kesalahan"].values[0]
                
                st.markdown(f"""
                    <div class="card" style="padding:10px; border-radius:10px; box-shadow:0 2px 5px rgba(0,0,0,0.1)">
                        <h6>Accuracy</h6>
                        <h3>{acc_value:.2f}%</h3>
                        <p style="margin:0; font-size:12px; color:gray">
                            {total_tagging} Tagging<br>
                            {kesalahan} Salah
                        </p>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                    <div class="card" style="padding:10px; border-radius:10px; box-shadow:0 2px 5px rgba(0,0,0,0.1)">
                        <h6>Accuracy</h6>
                        <h3>-</h3>
                        <p style="margin:0; font-size:12px; color:gray">No data</p>
                    </div>
                """, unsafe_allow_html=True)

        with cols[3]:
            st.markdown("""
                <div class="card">
                    <h6>Tagged</h6>
                </div>
            """, unsafe_allow_html=True)