import pandas as pd

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
def aggregation_csat(df, date_col, granularity):
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])

    if granularity == 'Daily':
        df['Period'] = df['date_col'].dt.date
        result = df.groupby('Period')[['CSAT [Before]', 'CSAT [After]']].mean().reset_index()
    else:
        if granularity == 'Weekly':
            df['Period'] = df[date_col].dt.to_period('W').apply(lambda r: r.start_time)
        elif granularity == 'Monthly':
            df['Period'] = df[date_col].dt.to_period('M').dt.to_timestamp()
        
        grouped = df.groupby('Period').agg({
            'rating_before': 'sum',
            'respondent_before': 'sum',
            'rating_after': 'sum',
            'respondent_after': 'sum'
        }).reset_index()

        grouped['CSAT [Before]'] = grouped['rating_before']/grouped['respondent_before']
        grouped['CSAT [After]'] = grouped['rating_after']/grouped['respondent_after']

        result = grouped[['Period', 'CSAT [Before]', 'CSAT [After]']]
    return result.rename(columns={'Period': 'Date'})


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