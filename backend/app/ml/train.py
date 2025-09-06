# Train a simple text+meta model for transaction categorization
# Uses sample training_data.csv in this folder.
import os
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.metrics import f1_score, classification_report
import joblib

from datetime import datetime

DATA_PATH = os.path.join(os.path.dirname(__file__), "training_data.csv")
MODEL_PATH = os.path.join(os.path.dirname(__file__), "model.joblib")

def main():
    df = pd.read_csv(DATA_PATH)
    df.fillna({"merchant": "", "description": "", "category": "Uncategorized"}, inplace=True)

    # Build text field
    df["text"] = (df["merchant"].astype(str) + " " + df["description"].astype(str)).str.strip()

    # Simple categorical target
    labels = df["category"].astype(str).values
    le = LabelEncoder()
    y = le.fit_transform(labels)

    # TF-IDF text
    vectorizer = TfidfVectorizer(min_df=1, max_features=5000, ngram_range=(1,2))

    # Fit vectorizer on text
    X_text = vectorizer.fit_transform(df["text"].values)

    # Numeric meta features
    def parse_date(dt):
        try:
            return pd.to_datetime(dt)
        except Exception:
            return pd.NaT

    dts = df["date"].apply(parse_date)
    weekday = dts.dt.weekday.fillna(0).astype(int).values.reshape(-1,1)
    month = dts.dt.month.fillna(0).astype(int).values.reshape(-1,1)
    amount = df["amount"].astype(float).values.reshape(-1,1)

    from scipy.sparse import hstack
    X = hstack([X_text, amount, weekday, month])

    n = y.shape[0]
    n_classes = len(set(y))
    # minimum test size so we have >= 1 per class (when possible)
    min_test = max(n_classes, int(max(1, 0.2 * n)))
    test_size = min_test / n if min_test < n else 0.2  # fallback

    try:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )
    except ValueError:
        # If stratified split still fails (very small data), do non-stratified split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=None
        )

    # simple, robust classifier
    clf = LogisticRegression(max_iter=200, n_jobs=1)
    clf.fit(X_train, y_train)
    y_pred = clf.predict(X_test)
    f1 = f1_score(y_test, y_pred, average="macro")
    print("F1-macro:", round(float(f1), 4))
    print(classification_report(y_test, y_pred, target_names=le.classes_))

    bundle = {
        "model": clf,
        "vectorizer": vectorizer,
        "label_encoder": le,
        "trained_at": pd.Timestamp.utcnow().isoformat(),
        "metrics": {"f1_macro": float(f1)}
    }
    joblib.dump(bundle, MODEL_PATH)
    print("Saved model to", MODEL_PATH)

if __name__ == "__main__":
    main()
