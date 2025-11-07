import os
import pickle
import pandas as pd
import lightgbm as lgb

def load_churn_model(model_path: str = "models/churn_model.pkl"):
    if os.path.exists(model_path):
        with open(model_path, 'rb') as f:
            return pickle.load(f)
    return None

def predict_churn(df: pd.DataFrame, model) -> pd.DataFrame:
    features = ['logins', 'support_tickets', 'payment_delay', 'login_frequency', 'support_ticket_spike']
    X = df[features].fillna(0)
    df['churn_probability'] = model.predict_proba(X)[:, 1]
    return df
