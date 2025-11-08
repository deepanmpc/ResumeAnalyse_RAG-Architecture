import os
import pickle
import pandas as pd
import lightgbm as lgb
import shap # Assuming shap is installed

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

def explain_churn(df: pd.DataFrame, model, top_n_features: int = 3):
    features = ['logins', 'support_tickets', 'payment_delay', 'login_frequency', 'support_ticket_spike']
    X = df[features].fillna(0)
    
    # Create a SHAP explainer
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)
    
    # For binary classification, shap_values will be a list of two arrays.
    # We are interested in the SHAP values for the positive class (churn).
    if isinstance(shap_values, list):
        shap_values = shap_values[1] # Get SHAP values for the positive class

    # Create a DataFrame for SHAP values
    shap_df = pd.DataFrame(shap_values, columns=features, index=df.index)

    # For each customer, find the top N features with the highest absolute SHAP values
    explanations = []
    for index, row in shap_df.iterrows():
        # Get absolute SHAP values and sort them
        abs_shap_values = row.abs().sort_values(ascending=False)
        
        # Get the names of the top N features
        top_features = abs_shap_values.head(top_n_features).index.tolist()
        
        # Create explanations string
        feature_explanations = []
        for feature in top_features:
            value = row[feature]
            original_value = X.loc[index, feature]
            if value > 0:
                feature_explanations.append(f"{feature} (value: {original_value}) increases churn risk")
            elif value < 0:
                feature_explanations.append(f"{feature} (value: {original_value}) decreases churn risk")
            else:
                feature_explanations.append(f"{feature} (value: {original_value}) has neutral impact")
        explanations.append(feature_explanations)
    
    return explanations

