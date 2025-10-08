import pandas as pd
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt

def aggregate_csat(df, date_col, granularity):
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])

    for c in ['Total Responden', 'Total Rating', 'CSAT [Before]', 'CSAT [After]']:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')

    if granularity == 'Daily':
        df['Period'] = df[date_col].dt.date
        grouped = df.groupby('Period').agg({
            'CSAT [Before]': 'mean',
            'CSAT [After]': 'mean'
        }).reset_index().rename(columns={'Period': 'Date'})
        return grouped

    if granularity == 'Weekly':
        df['Period'] = df[date_col].dt.to_period('W').apply(lambda r: r.start_time)
    elif granularity == 'Monthly':
        df['Period'] = df[date_col].dt.to_period('M').dt.to_timestamp()
    else:
        df['Period'] = df[date_col]

    def compute_period(g):
        out = {}
        # Total
        out['Total Rating'] = g['Total Rating'].sum() if 'Total Rating' in g.columns else np.nan
        out['Total Responden'] = g['Total Responden'].sum() if 'Total Responden' in g.columns else np.nan

        # CSAT [Before] (weighted average)
        if 'CSAT [Before]' in g.columns and 'Total Responden' in g.columns and g['Total Responden'].sum() > 0:
            out['CSAT [Before]'] = (g['CSAT [Before]'] * g['Total Responden']).sum() / g['Total Responden'].sum()
        else:
            out['CSAT [Before]'] = g['CSAT [Before]'].mean() if 'CSAT [Before]' in g.columns else np.nan

        # CSAT [After] (weighted average)
        if 'CSAT [After]' in g.columns and 'Total Responden' in g.columns and g['Total Responden'].sum() > 0:
            out['CSAT [After]'] = (g['CSAT [After]'] * g['Total Responden']).sum() / g['Total Responden'].sum()
        else:
            out['CSAT [After]'] = g['CSAT [After]'].mean() if 'CSAT [After]' in g.columns else np.nan

        return pd.Series(out)

    grouped = df.groupby('Period').apply(compute_period).reset_index().rename(columns={'Period': 'Date'})
    
    return grouped[['Date', 'CSAT [Before]', 'CSAT [After]']]

# Function to return the ratio weekly monthly count
def aggregation_ratio(df, date_col, granularity):
    if df is None or df.empty:
        return pd.DataFrame(columns=['Date', 'Robot Success ratio'])

    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])

    # ==== Fungsi bantu week quartile-like ====
    def week_of_month(date):
        days_in_month = pd.Period(date, freq='M').days_in_month
        week_length = days_in_month / 4
        week_num = int((date.day - 1) // week_length) + 1
        return min(week_num, 4)

    if granularity == 'Daily':
        df['Period'] = df[date_col].dt.date
    elif granularity == 'Weekly':
        df['Period'] = df[date_col].apply(lambda d: f"W{week_of_month(d)} {d.strftime('%b %Y')}")
    elif granularity == 'Monthly':
        df['Period'] = df[date_col].dt.to_period('M').dt.to_timestamp()
    else:
        df['Period'] = df[date_col]

    # hitung ratio per period
    grouped = df.groupby('Period').agg({
        'Connected to robot': lambda x: pd.to_numeric(x, errors='coerce').sum(),
        'Number of exit queues': lambda x: pd.to_numeric(x, errors='coerce').sum(),
        'Total handle robot': lambda x: pd.to_numeric(x, errors='coerce').sum()
    }).reset_index()

    grouped['Robot Success ratio'] = (
        (grouped['Total handle robot'] - grouped['Number of exit queues']) /
        grouped['Connected to robot'] * 100
    )

    return grouped[['Period', 'Robot Success ratio']].rename(columns={'Period': 'Date'})


    
def aggregate_sum(df, date_col, granularity, agg_dict):
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])

    if granularity == 'Daily':
        df['Period'] = df[date_col].dt.date
    elif granularity == 'Weekly':
        df['Period'] = df[date_col].dt.to_period('W').apply(lambda r: r.start_time)
    elif granularity == 'Monthly':
        df['Period'] = df[date_col].dt.to_period('M').dt.to_timestamp()
    else:
        df['Period'] = df[date_col]

    result = df.groupby('Period').agg(agg_dict).reset_index()
    return result.rename(columns={'Period': 'Date'})

# ============ Multiselect filter date for bad surey and like dislike table ============
def sidebar_filters():
    company_filter = st.sidebar.multiselect(
        'Select Company',
        options=['ASI','AFI','No Differentiated','AFI/ASI'],
        default=['ASI']
    )
    
    date_mode = st.sidebar.radio('Date Mode', ['Range','Single'], index=0)

    selected_date = None

    if date_mode == 'Single':
        selected_date = st.sidebar.date_input(
            'Selected Date',
            value=pd.to_datetime('today').date(),
            key='global_date'
        )

    return company_filter, date_mode, selected_date

# ============ Function to show Weeks and Months ============
def aggregate_table_with_granularity(
        df, category_col, value_col=None, date_col=None, granularity=None, start_date=None, end_date=None
):
    df = df.copy()
    
    # pastikan ada filter tanggal
    if start_date is not None and end_date is not None:
        df = df[(df[date_col] >= start_date) & (df[date_col] <= end_date)]
    
    if df.empty:
        return pd.DataFrame(columns=[category_col, 'Total'])

    # ==== Fungsi bantu untuk week quartile-like ====
    def week_of_month(date):
        days_in_month = pd.Period(date, freq='M').days_in_month
        week_length = days_in_month / 4
        week_num = int((date.day - 1) // week_length) + 1
        return min(week_num, 4)

    if granularity == 'Weekly':
        df['Year'] = df[date_col].dt.year
        df['Month'] = df[date_col].dt.strftime('%b %Y')
        df['WeekInMonth'] = df[date_col].apply(week_of_month)
        df['PeriodRaw'] = df[date_col].dt.to_period('W')
        df['Period'] = 'W' + df['WeekInMonth'].astype(str) + ' ' + df['Month']

    elif granularity == 'Monthly':
        df['PeriodRaw'] = df[date_col].dt.to_period('M')
        df['Period'] = df['PeriodRaw'].dt.strftime("%b %Y")

    else:
        df['PeriodRaw'] = df[date_col]
        df['Period'] = df[date_col].dt.strftime('%Y-%m-%d')

    # ==== Aggregasi ====
    if value_col is None:
        agg_df = (
            df.groupby([category_col, 'PeriodRaw','Period'])
            .size()
            .reset_index(name='Total Sample')
        )
    else:
        agg_df = (
            df.groupby([category_col, 'PeriodRaw','Period'])[value_col]
            .sum()
            .reset_index(name='Total Sample')
        )
    
    pivot = agg_df.pivot_table(index=category_col, columns='Period', values='Total Sample', aggfunc='sum', fill_value=0)

    # urutkan kolom sesuai PeriodRaw
    period_order = (
        agg_df[['PeriodRaw','Period']]
        .drop_duplicates()
        .sort_values('PeriodRaw')
    )
    pivot = pivot[period_order['Period'].tolist()]

    # adding total column
    pivot['Total'] = pivot.sum(axis=1)
    pivot = pivot.sort_values('Total', ascending=False)
    
    pivot = pivot.reset_index()

    pivot.columns = pd.Index(pivot.columns).map(str)
    pivot = pivot.loc[:, ~pivot.columns.duplicated()]

    return pivot



def calculate_checker_accuracy(df):
    # cari semua kolom yang dimulai dengan 'Count'
    count_cols = [col for col in df.columns if col.startswith("Count")]
    
    # bikin kolom baru = total kesalahan di 1 baris
    df["Total_Kesalahan"] = df[count_cols].sum(axis=1)
    
    # groupby per checker
    result = (
        df.groupby("Checker")
        .agg(
            Total_Tagging=("Checker", "count"),
            Kesalahan=("Total_Kesalahan", "sum")
        )
        .reset_index()
    )
    
    # hitung akurasi
    result["Accuracy"] = (result["Total_Tagging"] - result["Kesalahan"]) / result["Total_Tagging"] * 100
    
    return result

def aggregate_checker_errors(df):
    count_cols = [
        'Count Hasil ASR',
        'Count Hasil Pemeriksaan Kualitas',
        'Count Efektif',
        'Count Kejelasan Suara',
        'Count Kelengkapan Rekaman',
        'Count Revisi Text'
    ]
    df_checker = df.groupby('Checker')[count_cols].sum().reset_index()
    return df_checker, count_cols