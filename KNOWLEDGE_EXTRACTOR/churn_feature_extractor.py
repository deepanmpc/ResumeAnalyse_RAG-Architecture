import pandas as pd

def extract_churn_features(df: pd.DataFrame) -> pd.DataFrame:
    # Normalize columns
    df = df.rename(columns={
        'CustomerID': 'customer_id',
        'Usage Frequency': 'logins',
        'Support Calls': 'support_tickets',
        'Payment Delay': 'payment_delay',
        'Churn': 'churn',
    })
    if 'customer_id' not in df.columns:
        df['customer_id'] = df.index.astype(str)
    if 'logins' not in df.columns:
        df['logins'] = 0
    if 'support_tickets' not in df.columns:
        df['support_tickets'] = 0
    if 'payment_delay' not in df.columns:
        df['payment_delay'] = 0
    if 'churn' not in df.columns:
        df['churn'] = 0
    # Add engineered features
    df['login_frequency'] = df['logins'].rolling(window=7, min_periods=1).mean()
    df['support_ticket_spike'] = (df['support_tickets'] > df['support_tickets'].shift(1)).astype(int)
    return df
