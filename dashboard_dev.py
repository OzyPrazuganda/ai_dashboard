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
from utils_aggregation import aggregate_csat, aggregation_ratio, aggregate_sum, sidebar_filters, aggregate_table_with_granularity, calculate_checker_accuracy, aggregate_checker_errors
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

    page = st.sidebar.selectbox("Pages", ['Dashboard'])

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
            text=[f"<span style='color:black'>{x:.2f}%" for x in filtered_df['Robot Success ratio']],
            fill='tonexty',
            fillcolor='rgba(0, 123, 255, 0.2)'
        )

        y_min = filtered_df['Robot Success ratio'].min()
        y_max = filtered_df['Robot Success ratio'].max()
        x_min = filtered_df['Date'].min()
        x_max = filtered_df['Date'].max()

        y_margin = (y_max - y_min) * 0.25

        fig.update_layout(
            xaxis_title='',
            xaxis=dict(range=[x_min - pd.Timedelta(days=1), x_max + pd.Timedelta(days=1)]),
            yaxis_title='',
            yaxis=dict(
                range=[y_min - y_margin, y_max + y_margin],
                ticksuffix='%'
            ),
            template='plotly_white'
        )
 
        st.plotly_chart(fig, use_container_width=True)


        # Chart 2: CSAT Robot

        df_csat = pd.read_csv('dataset_kula/csat_takeout.csv')
        df_csat['Date'] = pd.to_datetime(df_csat['Date'])

        filtered_df = df_csat[(df_csat['Date'] >= pd.to_datetime(start)) & (df_csat['Date'] <= pd.to_datetime(end))]
        filtered_df = aggregate_csat(filtered_df, 'Date', granularity)

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=filtered_df['Date'],
            y=filtered_df['CSAT [Before]'],
            mode='lines+markers+text',
            name='Before take out',
            text=[f"<span style='color:black'>{x:.2f}" for x in filtered_df['CSAT [Before]']],
            textposition='top center',
            fill='tonexty',
            fillcolor='rgba(0, 123, 255, 0.2)'
        ))

        fig.add_trace(go.Scatter(
            x=filtered_df['Date'],
            y=filtered_df['CSAT [After]'],
            mode='lines+markers+text',
            name='After take out',
            line=dict(color='red'),
            text=[f"<span style='color:black'>{x:.2f}" for x in filtered_df['CSAT [After]']],
            textposition='top center',
            fill='tonexty',
            fillcolor='rgba(255,0,0,0.2)'
        ))
        
        x_min = filtered_df['Date'].min()
        x_max = filtered_df['Date'].max()

        fig.update_layout(
            title='CSAT Robot 机器人用户满意度',
            xaxis=dict(range=[(x_min - pd.Timedelta(days=1)),x_max + pd.Timedelta(days=1)]),
            yaxis_title='',
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
        company_filter, date_mode, selected_date = sidebar_filters()

        if date_mode == 'Range':
            selected_range = (start, end)
        else:
            selected_range = None

        # Filter tanggal
        if date_mode == 'Single' and selected_date:
            df_bad_survey = df_bad_survey[df_bad_survey['Conversation Start Time'].dt.date == selected_date]
        elif date_mode == 'Range' and selected_range and len(selected_range) == 2:
            start_date, end_date = pd.to_datetime(selected_range[0]), pd.to_datetime(selected_range[1])
            df_bad_survey = df_bad_survey[df_bad_survey['Conversation Start Time'].between(start_date, end_date)]

        # Terapkan filter company
        if company_filter:
            df_bad_survey = df_bad_survey[df_bad_survey['Business Type'].isin(company_filter)]

        # === Table 1: Sub Category with Granularity ===
        if granularity in ['Weekly', 'Monthly'] and date_mode == 'Range':
            subcat_summary = aggregate_table_with_granularity(
                df_bad_survey,
                category_col='Sub Category',
                date_col='Conversation Start Time',
                granularity=granularity,
                start_date=start_date,
                end_date=end_date
            )
        else:
            subcat_summary = (
                df_bad_survey.groupby('Sub Category')
                .size()
                .reset_index(name='Total Sample')
                .sort_values('Total Sample', ascending=False)
            )

        # === Table 2: QC result with Granularity ===
        if granularity in ['Weekly', 'Monthly'] and date_mode == 'Range':
            cat_summary = aggregate_table_with_granularity(
                df_bad_survey,
                category_col='QC Result',
                date_col='Conversation Start Time',
                granularity=granularity,
                start_date=start_date,
                end_date=end_date
            )
        else:
            cat_summary = (
                df_bad_survey.groupby('QC Result')
                .size()
                .reset_index(name='Total Sample')
                .sort_values('Total Sample', ascending=False)
            )

        # if there is percent label
        if 'Total Sample' in subcat_summary.columns:
            subcat_summary['Percentage'] = (
                subcat_summary['Total Sample'] / subcat_summary['Total Sample'].sum() * 100
            ).round(2).astype(str) + '%'
        
        if 'Total Sample' in cat_summary.columns:
            cat_summary['Percentage'] = (
                cat_summary['Total Sample'] / cat_summary['Total Sample'].sum() * 100
            ).round(2).astype(str) + '%'

        # Tampilkan di dashboard AGGrid
        with st.container():
            st.markdown("##### Bad Survey")
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

            # Filter company
            if company_filter:
                df_like_dislike = df_like_dislike[
                    df_like_dislike['Manual Check [business]'].isin(company_filter)
                ]

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
                text=[f"<span style='color:black'>{x}" for x in df_daily['Like']],
                textposition='top center',
                fill='tonexty',
                fillcolor='rgba(0, 123, 255, 0.2)'
            ))

            # Dislike
            fig.add_trace(go.Scatter(
                x=df_daily['Date'],
                y=df_daily['Dislike'],
                mode='lines+markers+text',
                name='Dislike',
                line=dict(color='red'),
                text=[f"<span style='color:black'>{x}" for x in df_daily['Dislike']],
                textposition='top center',
                fill='tonexty',
                fillcolor='rgba(255,0,0,0.2)'
            ))

            x_min = df_like_dislike['Date'].min()
            x_max = df_like_dislike['Date'].max()

            fig.update_layout(
                xaxis=dict(range=[x_min - pd.Timedelta(days=0.5), x_max + pd.Timedelta(days=0.5)]),
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
        if date_mode == 'Single' and selected_date:
            df_like_dislike = df_like_dislike[df_like_dislike['Date'].dt.date == selected_date]
        elif date_mode == 'Range' and selected_range and len(selected_range) == 2:
            df_like_dislike = df_like_dislike[df_like_dislike['Date'].between(start_date, end_date)]

        if company_filter:  # multiselect
            df_like_dislike = df_like_dislike[df_like_dislike['Manual Check [business]'].isin(company_filter)]

        # ===== Table 1: Berdasarkan Team/Category =====
        if granularity in ['Weekly', 'Monthly'] and date_mode == 'Range':
            team_summary = aggregate_table_with_granularity(
                df_like_dislike,
                category_col = 'Team/Category',
                value_col = 'unsolved_num',
                date_col = 'Date',
                granularity = granularity,
                start_date = start_date,
                end_date = end_date
            )
        else:
            team_summary = (
                df_like_dislike.groupby('Team/Category')
                .agg(
                    **{
                        'Total Dislike': ('unsolved_num', 'sum')
                    }
                )
                .reset_index()
                .sort_values('Total Dislike', ascending=False)
            )

        # ===== Table 2: Berdasarkan Background detail =====
        if granularity in ['Weekly', 'Monthly'] and date_mode == 'Range':
            bg_summary = aggregate_table_with_granularity(
                df_like_dislike,
                category_col='Background detail',
                value_col='unsolved_num',
                date_col='Date',
                granularity=granularity,
                start_date=start_date,
                end_date=end_date
            )
        else:
            bg_summary = (
                df_like_dislike.groupby('Background detail')
                .agg(
                    **{
                        'Total Dislike': ('unsolved_num', 'sum')
                    }
                )
                .reset_index()
                .sort_values('Total Dislike', ascending=False)
            )

        # ===== Tampilkan di dashboard =====
        st.markdown("##### Dislike Summary")
        with st.container():
            cols = st.columns([0.45, 0.5])

            with cols[0]:
                gd1 = GridOptionsBuilder.from_dataframe(team_summary)
                gd1.configure_pagination()
                gd1.configure_default_column(sortable=True, resizable=True)
                grid_options1 = gd1.build()
                AgGrid(team_summary, gridOptions=grid_options1, height=400)

            with cols[1]:
                gd2 = GridOptionsBuilder.from_dataframe(bg_summary)
                gd2.configure_pagination()
                gd2.configure_default_column(sortable=True, resizable=True)
                grid_options2 = gd2.build()
                AgGrid(bg_summary, gridOptions=grid_options2, height=400)

        
        # Table QC KULA
        df_qc_kula = pd.read_csv('dataset_kula/qc_kula.csv')
        df_qc_kula['Score_date'] = pd.to_datetime(df_qc_kula['Score_date'], errors='coerce')

        if date_mode == 'Single' and selected_date:
            df_qc_kula = df_qc_kula[df_qc_kula['Score_date'].dt.date == selected_date]
        elif date_mode == 'Range' and selected_range and len(selected_range) == 2:
            start_date, end_date = pd.to_datetime(selected_range[0]), pd.to_datetime(selected_range[1])
            df_qc_kula = df_qc_kula[df_qc_kula['Score_date'].between(start_date, end_date)]
        
        # Filter the company
        if company_filter:
            df_qc_kula = df_qc_kula[df_qc_kula['Business Type'].isin(company_filter)]

        
        # === Table 1: Main Category & Sub Category ===
        main_sub_summary = (
            df_qc_kula.groupby(['Main Category', 'Checking Result (Sub Category)'])
            .size()
            .reset_index(name='Total Sample')
            .sort_values('Total Sample', ascending=False)
        )

        # === Table 2: Team Category ===
        if granularity in ['Weekly', 'Monthly'] and date_mode == 'Range':
            team_cat_qc = aggregate_table_with_granularity(
                df_qc_kula,
                category_col='Team/Category',
                date_col='Score_date',
                granularity=granularity,
                start_date=start_date,
                end_date=end_date
            )
        else:
            team_cat_qc = (
                df_qc_kula.groupby('Team/Category')
                .size()
                .reset_index(name='Total Sample')
                .sort_values('Total Sample', ascending=False)
            )

        # === Table 3: Background Detail ===
        if granularity in ['Weekly','Monthly'] and date_mode == 'Range':
            bg_summary = aggregate_table_with_granularity(
                df_qc_kula,
                category_col='Background detail- ID',
                date_col='Score_date',
                granularity=granularity,
                start_date=start_date,
                end_date=end_date
            )
        else:
            bg_summary = (
                df_qc_kula.groupby('Background detail- ID')
                .size()
                .reset_index(name='Total Sample')
                .sort_values('Total Sample', ascending=False)
            )

        # Show the data
        st.markdown('##### QC Dislike')
        with st.container():
            cols = st.columns([0.35, 0.3, 0.35])

            with cols[0]:
                gd_main = GridOptionsBuilder.from_dataframe(main_sub_summary)
                gd_main.configure_pagination()
                gd_main.configure_default_column(sortable=True, resizable=True)
                gd_main.configure_column('Total Sample', filter=False)
                grid_options_main = gd_main.build()
                AgGrid(main_sub_summary, gridOptions=grid_options_main, height=400)

            with cols[1]:
                gd_bg = GridOptionsBuilder.from_dataframe(team_cat_qc)
                gd_bg.configure_pagination()
                gd_bg.configure_default_column(sortable=True, resizable=True)
                gd_bg.configure_column('Total Sample', filter=False)
                grid_options_bg = gd_bg.build()
                AgGrid(team_cat_qc, gridOptions=grid_options_bg, height=400)

            with cols[2]:
                gd_bg = GridOptionsBuilder.from_dataframe(bg_summary)
                gd_bg.configure_pagination()
                gd_bg.configure_default_column(sortable=True, resizable=True)
                gd_bg.configure_column('Total Sample', filter=False)
                grid_options_bg = gd_bg.build()
                AgGrid(bg_summary, gridOptions=grid_options_bg, height=400)