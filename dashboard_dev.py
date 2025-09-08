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
from utils_aggregation import aggregation_csat, aggregation_ratio, aggregate_sum
from streamlit_chatbox import *
from st_aggrid import AgGrid
from st_aggrid.grid_options_builder import GridOptionsBuilder
from collections import defaultdict
from datetime import datetime, timedelta
logging.getLogger('streamlit.runtime.scriptrunner').setLevel(logging.ERROR)

CURRENT_THEME = "light" 
IS_DARK_THEME = False
st.set_page_config(layout="wide")

team = st.sidebar.radio('Team', ['KULA'])

if team == 'KULA':
    # st.markdown('#####')

    page = st.sidebar.selectbox("Pages", ['Dashboard', 'Chatbot'])

    if page == 'Dashboard':
        
        with st.container():
            cols = st.columns([3.5,0.5])
        
            with cols[0]:
                st.title("KULA Dashboard")
            with cols[1]:
                granularity = st.selectbox(
                    '',
                    options=['Daily', 'Weekly', 'Monthly'],
                    index=0
                )

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
        
        filtered_df = aggregation_ratio(filtered_df, 'Date', granularity)

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

        df_csat = pd.read_csv('dataset_kula/csat_takeout.csv')
        df_csat['Date'] = pd.to_datetime(df_csat['Date'])

        filtered_df = df_csat[(df_csat['Date'] >= pd.to_datetime(start)) & (df_csat['Date'] <= pd.to_datetime(end))]
        filtered_df = aggregation_csat(filtered_df, 'Date', granularity)

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=filtered_df['Date'],
            y=filtered_df['CSAT [Before]'],
            mode='lines+markers+text',
            name='Before take out',
            text=filtered_df['CSAT [Before]'],
            textposition='top center'
        ))

        fig.add_trace(go.Scatter(
            x=filtered_df['Date'],
            y=filtered_df['CSAT [After]'],
            mode='lines+markers+text',
            name='After take out',
            line=dict(color='red'),
            text=filtered_df['CSAT [After]'],
            textposition='top center'
        ))

        fig.update_layout(
            title='CSAT Robot 机器人用户满意度',
            yaxis_title='CSAT',
            yaxis=dict(range=[1,5]),
            legend=dict(
                orientation='v',
                yanchor='top',
                y=1.1,
                xanchor='right',
                x=1,
                title=None
            )
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

        # Sidebar filter: Tanggal (hanya 1 tanggal)
        min_date = df_bad_survey['Conversation Start Time'].min().date()
        max_date = df_bad_survey['Conversation Start Time'].max().date()

        selected_date = st.sidebar.date_input(
            "Select Bad Survey & Dislike Date",
            value=max_date,
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

            df_like_dislike = df_like_dislike[(df_like_dislike['Date'] >= pd.to_datetime(start)) & (df_like_dislike['Date'] <= pd.to_datetime(end))]
            df_daily = aggregate_sum(df_like_dislike, 'Date', granularity,{
                "solved_num": "sum",
                "unsolved_num": "sum"
            })
            df_daily.rename(columns={'solved_num': 'Like', 'unsolved_num': 'Dislike'}, inplace=True)

            latest_date = df_daily['Date'].max()
            latest_data = df_daily[df_daily['Date'] == latest_date].melt(
                id_vars = 'Date',
                value_vars = ['Like', 'Dislike'],
                var_name = 'Category',
                value_name = 'Total'
            )
            
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
                yaxis=dict(title=None, range=[100,800]),
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
