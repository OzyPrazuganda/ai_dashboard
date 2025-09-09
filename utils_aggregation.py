import pandas as pd
import numpy as np

'''
Previous code

# The Function
def aggregate_by_granularity(df, date_col, granularity, agg_dict=None):
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

    # Apply aggregation
    if agg_dict:
        df = df.groupby('Period').agg(agg_dict).reset_index()
    else:
        df = df.groupby('Period').mean().reset_index()
    
    return df.rename(columns={'Period': 'Date'})

'''

# Function to return the CSAT weekly monthly count
def aggregate_csat(df, date_col, granularity):
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])

    for c in ['Total Responden', 'Total Rating', 'CSAT[Before]', 'CSAT[After]']:
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

    def computer_period(g):
        out = {}
        #total
        tot_rating = g['Total Rating'].sum() if 'Total Rating' in g.columns else np.nan
        tot_resp = g['Total Responden'].sum() if 'Total Responden' in g.columns else np.nan
        out['Total Rating'] = tot_rating
        out['Total Responden'] = tot_resp

        # CSAT [Before]
        if 'CSAT [Before]' in g.columns:
            if 'Total Responden' in g.columns and g['Total Responden'].sum() > 0:
                denom = g['Total Responden'].sum()
                numer = (g['CSAT [Before]']) * g['Total Responden'].sum()
                out['CSAT [Before]'] = numer / denom
            else:
                out['CSAT [Before]'] = g['CSAT [Before]'].mean()
        else:
            out['CSAT [Before]'] = np.nan

        # CSAT [After]
        if 'CSAT [After]' in g.columns:
            if 'Total Responden' in g.columns and g['Total Responden'].sum() > 0:
                denom = g['Total Responden'].sum()
                numer = (g['CSAT [After]']) * g['Total Responden'].sum()
                out['CSAT [After]'] = numer / denom
            else:
                out['CSAT [After]'] = g['CSAT [After]'].mean()
        else:
            out['CSAT [After]'] = np.nan
        
        return pd.Series(out)

    grouped = df.groupby('Period').apply(computer_period).reset_index().rename(columns={'Period': 'Date'})
    
    # result that will showed on the dashboard
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