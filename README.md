# SaaS Churn Predictor + Explainer Agent

This project is a Streamlit application that predicts customer churn for a SaaS company and explains the predictions.

## How to Run

1.  **Install Dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

2.  **Set OpenAI API Key:**

    The application uses OpenAI's GPT-3 for contextual explanations. You need to set your OpenAI API key as an environment variable:

    ```bash
    export OPENAI_API_KEY="YOUR_API_KEY"
    ```

3.  **Run the Streamlit App:**

    ```bash
    streamlit run main.py
    ```

4.  **Upload Data:**

    -   Open your browser and go to the Streamlit URL (usually `http://localhost:8501`).
    -   Use the sidebar to upload a CSV file with customer activity data. A sample file `data/customer_activity.csv` is provided.

## How it Works

The application consists of three coordinated agents:

1.  **Feature Extractor Agent:** Reads and processes customer activity logs to compute behavioral metrics (e.g., usage frequency, engagement drop, support ticket spike).

2.  **Churn Predictor Agent:** Uses a lightweight LightGBM model to predict churn risk based on the extracted features.

3.  **Explainer Agent:** Applies RAG (Retrieval-Augmented Generation) to retrieve customer interaction history and uses explainability methods (SHAP) to clarify the key drivers influencing the churn score.