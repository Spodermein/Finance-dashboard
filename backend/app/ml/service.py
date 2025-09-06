import os
import joblib
from typing import Tuple
from datetime import date
import numpy as np

MODEL_PATH = os.path.join(os.path.dirname(__file__), "model.joblib")

_model = None
_vectorizer = None
_label_encoder = None
_threshold = 0.75
_metrics = {}
_meta = {}


def load_model():
    global _model, _vectorizer, _label_encoder
    if os.path.exists(MODEL_PATH):
        bundle = joblib.load(MODEL_PATH)
        _model = bundle["model"]
        _vectorizer = bundle["vectorizer"]
        _label_encoder = bundle["label_encoder"]
        metrics = bundle.get("metrics", {})
        _meta = {"trained_at": bundle.get("trained_at")}
        return True
    return False

def get_status():
    return {"loaded": is_ready(), "threshold": _threshold, "metrics": _metrics, "meta": _meta}

def set_threshold(t: float):
    global _threshold
    _threshold = max(0.0, min(1.0, float(t)))

def is_ready() -> bool:
    return _model is not None and _vectorizer is not None and _label_encoder is not None

def _featurize(merchant: str, description: str, amount: float, dt: date | None):
    text = (merchant or "") + " " + (description or "")
    X_text = _vectorizer.transform([text])
    # simple numeric features: amount bucket, weekday, month
    if dt is None:
        weekday = 0
        month = 0
    else:
        weekday = dt.weekday()
        month = dt.month
    extra = np.array([[amount, weekday, month]], dtype=float)
    # concatenate sparse + dense
    from scipy.sparse import hstack
    return hstack([X_text, extra])

def predict(merchant: str = "", description: str = "", amount: float = 0.0, dt: date | None = None) -> Tuple[str, float]:
    if not is_ready():
        return "Uncategorized", 0.0
    X = _featurize(merchant, description, amount, dt)
    proba = getattr(_model, "predict_proba", None)
    if proba is None:
        y = _model.predict(X)
        label = _label_encoder.inverse_transform(y)[0]
        return label, 0.0
    probs = _model.predict_proba(X)[0]
    idx = int(np.argmax(probs))
    label = _label_encoder.inverse_transform([idx])[0]
    conf = float(probs[idx])
    return (label if conf >= _threshold else "Uncategorized"), conf
