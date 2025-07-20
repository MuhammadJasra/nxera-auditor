"""
Train LightGBM on the Kaggle Credit‑Card‑Fraud dataset
and save fraud_cc_model.pkl ready for Nxera Auditor.
"""

import pandas as pd, numpy as np, joblib, os, lightgbm as lgb
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import roc_auc_score, classification_report
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import IsolationForest

print("[INFO] Starting training script...")
try:
    # 1. Load the CSV you downloaded
    print("[INFO] Loading dataset...")
    CSV_PATH = r"D:\Muhammad Jasra\cold_email_agent\archive\creditcard.csv"
    df = pd.read_csv(CSV_PATH)
    print(f"[INFO] Loaded dataset with shape: {getattr(df, 'shape', 'N/A')}")

    # 2. Feature engineering: universal features + behavioral/frequency features
    def add_universal_features(df):
        df = df.copy()
        # Date features
        if 'Time' in df.columns:
            df['day_of_week'] = ((df['Time'] // (60*60*24)) % 7).astype(int)
            df['month'] = ((df['Time'] // (60*60*24*30)) % 12 + 1).astype(int)
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            df['day_of_week'] = df['date'].dt.dayofweek
            df['is_weekend'] = df['day_of_week'] >= 5
            df['month'] = df['date'].dt.month
        else:
            df['is_weekend'] = df['day_of_week'] >= 5
        # Amount features
        df['abs_amount'] = df['Amount'].abs() if 'Amount' in df.columns else 0
        df['is_expense'] = (df['Amount'] < 0) if 'Amount' in df.columns else False
        df['is_rounded'] = (df['Amount'] % 1000 == 0) if 'Amount' in df.columns else False
        # Description features
        if 'description' in df.columns:
            df['desc_length'] = df['description'].astype(str).str.len()
            keywords = ['cash','bonus','refund','rent','salary','invoice','transfer','payment','fee','tax','interest','loan','travel','gift','reimbursement','utilities','office','subscription','maintenance','insurance','commission','consulting','legal','supplies','equipment','marketing','advertising','client','vendor','employee','director','shareholder','partner','contractor','consultant','manager','executive','board','audit','compliance','fraud','risk','suspicious','duplicate','error','adjustment','write-off','bad debt','loss','profit','revenue','expense','asset','liability','equity','capital','investment','dividend','distribution','withdrawal','deposit']
            for kw in keywords:
                df[f'kw_{kw}'] = df['description'].astype(str).str.contains(kw, case=False, na=False).astype(int)
        else:
            df['desc_length'] = 0
        # --- Behavioral/Frequency Features ---
        # Transaction count per description per month
        if 'description' in df.columns and 'month' in df.columns:
            df['desc_month_count'] = df.groupby(['description','month'])['amount' if 'amount' in df.columns else 'Amount'].transform('count')
        else:
            df['desc_month_count'] = 0
        # Average amount per description
        if 'description' in df.columns:
            df['desc_avg_amount'] = df.groupby('description')['amount' if 'amount' in df.columns else 'Amount'].transform('mean')
        else:
            df['desc_avg_amount'] = 0
        # Time since last transaction with same description
        if 'description' in df.columns and 'date' in df.columns:
            df = df.sort_values('date')
            df['time_since_last_desc'] = df.groupby('description')['date'].diff().dt.total_seconds().fillna(0)
        else:
            df['time_since_last_desc'] = 0
        # Rolling sum of amounts over last 7 days
        if 'date' in df.columns and ('amount' in df.columns or 'Amount' in df.columns):
            amt_col = 'amount' if 'amount' in df.columns else 'Amount'
            df = df.sort_values('date')
            df['rolling_sum_7d'] = df.set_index('date')[amt_col].rolling('7D').sum().reset_index(drop=True)
        else:
            df['rolling_sum_7d'] = 0
        return df

    df = add_universal_features(df)

    # 3. Features / label
    X = df.drop(columns=[c for c in ['Class'] if c in df.columns])
    y = df['Class'] if 'Class' in df.columns else None
    print("[INFO] Split features and label.")

    # 4. Train‑test split 80/20 stratified
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"[INFO] Train shape: {getattr(X_train, 'shape', 'N/A')}, Test shape: {getattr(X_test, 'shape', 'N/A')}")

    # 5. Select numeric columns for scaling
    num_cols = [c for c in X.columns if X[c].dtype in [np.float64, np.int64, float, int]]
    pre = ColumnTransformer(
        transformers=[("scaler", StandardScaler(), num_cols)],
        remainder="passthrough"
    )

    # 6. LightGBM classifier (works well on imbalanced)
    # --- Model tuning: grid of hyperparameters ---
    lgbm = lgb.LGBMClassifier(class_weight={0:1, 1:25}, random_state=42)
    param_grid = {
        'n_estimators': [200, 400],
        'learning_rate': [0.01, 0.05, 0.1],
        'max_depth': [5, 10, -1],
        'subsample': [0.8],
        'colsample_bytree': [0.8],
    }
    pipe = Pipeline([("prep", pre), ("clf", lgbm)])
    print("[INFO] Starting GridSearchCV for LightGBM...")
    grid = GridSearchCV(pipe, param_grid={f"clf__{k}": v for k, v in param_grid.items()},
                       scoring='roc_auc', cv=3, n_jobs=-1, verbose=2)
    grid.fit(X_train, y_train)
    print(f"[INFO] Best params: {grid.best_params_}")
    best_pipe = grid.best_estimator_
    print("[INFO] Model training complete.")

    # 7. Evaluate
    proba = best_pipe.predict_proba(X_test)[:, 1]
    pred = (proba >= 0.50).astype(int)
    print("ROC‑AUC:", roc_auc_score(y_test, proba))
    print(classification_report(y_test, pred, digits=4))

    # 8. Save model
    joblib.dump(best_pipe, "fraud_cc_model.pkl")
    print("✔︎ Saved best model to fraud_cc_model.pkl")

    # --- Ensembling: Isolation Forest anomaly model ---
    print("[INFO] Training Isolation Forest for anomaly detection...")
    # Always convert X_train to DataFrame for .loc usage
    X_train_df = pd.DataFrame(X_train, columns=X.columns)
    iso = IsolationForest(contamination='auto', random_state=42)
    iso.fit(X_train_df.loc[:, num_cols].to_numpy())
    joblib.dump(iso, "iso_forest_model.pkl")
    print("✔︎ Saved Isolation Forest model to iso_forest_model.pkl")

except Exception as e:
    print("[ERROR] Exception occurred:", e)
