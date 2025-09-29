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

    if granularity == 'Daily':
        df['Period'] = df[date_col].dt.date
        result = df.groupby('Period')[['Robot Success ratio']].mean().reset_index()
    else:
        if granularity == 'Weekly':
            df['Period'] = df[date_col].dt.to_period('W').apply(lambda r: r.start_time)
        elif granularity == 'Monthly':
            df['Period'] = df[date_col].dt.to_period('M').dt.to_timestamp()

        grouped = df.groupby('Period').agg({
            'Connected to robot': lambda x: pd.to_numeric(x, errors='coerce').sum(),
            'Number of exit queues': lambda x: pd.to_numeric(x, errors='coerce').sum(),
            'Total handle robot': lambda x: pd.to_numeric(x, errors='coerce').sum()
        }).reset_index()

        grouped['Robot Success ratio'] = (
            (grouped['Total handle robot'] - grouped['Number of exit queues']) /
            grouped['Connected to robot'] * 100
        )

        result = grouped[['Period', 'Robot Success ratio']]

    return result.rename(columns={'Period': 'Date'})

    
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

# ============ Function to show W1 W2 W3 / M1 M2 M3 ============
def aggregate_table_with_granularity(
        df, category_col, value_col=None, date_col=None, granularity=None, start_date=None, end_date=None
):
    df = df.copy()
    
    # make sure there is date range
    if start_date is not None and end_date is not None:
        df = df[(df[date_col] >= start_date) & (df[date_col] <= end_date)]
    
    if df.empty:
        return pd.DataFrame(columns=[category_col, 'Total'])

    # determine period column based on granularity
    if granularity == 'Weekly':
        df['PeriodRaw'] = df[date_col].dt.to_period('W')
        df['Period'] = df['PeriodRaw'].apply(lambda x: f"W{x.start_time.strftime('%U')} {x.start_time.year}")
    elif granularity == 'Monthly':
        df['PeriodRaw'] = df[date_col].dt.to_period('M')
        df['Period'] = df['PeriodRaw'].dt.strftime("%b %Y")  # contoh: Sep 2024
    else:
        df['PeriodRaw'] = df[date_col]
        df['Period'] = df[date_col].dt.strftime('%Y-%m-%d')


    # group by category + period -> pivot
    if value_col is None:
        agg_df = (
            df.groupby([category_col, 'PeriodRaw'])
            .size()
            .reset_index(name='Total Sample')
        )
    else:
        agg_df = (
            df.groupby([category_col, 'PeriodRaw'])[value_col]
            .sum()
            .reset_index(name='Total Sample')
        )
    
    agg_df = agg_df.merge(df[['PeriodRaw','Period']].drop_duplicates(), on='PeriodRaw', how='left')
    pivot = agg_df.pivot(index=category_col, columns='Period', values='Total Sample').fillna(0)

    # Sort column by PeriodRaw
    period_order = df[['PeriodRaw', 'Period']].drop_duplicates().sort_values('PeriodRaw')
    pivot = pivot[period_order['Period'].tolist()]

    # adding total column
    pivot['Total'] = pivot.sum(axis=1)
    pivot = pivot.sort_values('Total', ascending=False)
    
    return pivot.reset_index()

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