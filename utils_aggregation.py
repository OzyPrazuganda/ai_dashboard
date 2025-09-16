import pandas as pd
import numpy as np
import streamlit as st

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
def aggregate_table_with_granularity(df, category_col, value_col, date_col, granularity, start_date=None, end_date=None):
    df = df.copy()
    
    # make sure there is date range
    if start_date is not None and end_date is not None:
        df = df[(df[date_col] >= start_date) & (df[date_col] <= end_date)]
    
    if df.empty:
        return pd.DataFrame(columns=[category_col, 'Total'])

    # determine period column based on granularity
    if granularity == 'Weekly':
        df['PeriodRaw'] = df[date_col].dt.to_period('W')
    elif granularity == 'Monthly':
        df['PeriodRaw'] = df[date_col].dt.to_period('M')
    else:
        df['PeriodRaw'] = df[date_col].dt.strftime('%Y-%m-%d')

    # Mapping W1/W2... or M1/M2...
    unique_periods = sorted(df['PeriodRaw'].unique())
    mapping = {
        p: f"W{i+1}" if granularity == "Weekly" else f"M{i+1}"
        for i, p in enumerate(unique_periods)
    }

    # Assign period label
    df["Period"] = df["PeriodRaw"].map(mapping)

    # group by category + period -> pivot
    pivot = (
        df.groupby([category_col, 'Period'])[value_col]
        .sum()
        .reset_index()
        .pivot(index=category_col, columns='Period', values=value_col)
        .fillna(0)
    )

    # adding total column
    pivot['Total'] = pivot.sum(axis=1)
    pivot = pivot.sort_values('Total', ascending=False)
    
    return pivot.reset_index()