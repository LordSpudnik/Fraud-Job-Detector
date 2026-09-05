"""
Loads the trained artifacts produced by ml/train.py and exposes:

  - predict(job_dict, model_name) -> (label, confidence, top_factors)
  - list_models() -> available model names
  - get_metrics() -> full metrics.json content
  - get_best_model_name() -> str
  - get_eda_summary() -> dict

Everything is loaded once at import time (module-level singletons), since
FastAPI runs as a single long-lived process and re-loading joblib files on
every request would be slow.
"""

import json
import re
import string
from pathlib import Path

import joblib
import numpy as np

MODELS_DIR = Path(__file__).resolve().parent.parent.parent / "models"

STRUCTURED_CATEGORICAL = [
    "employment_type",
    "required_experience",
    "required_education",
    "industry",
    "function",
]
STRUCTURED_BINARY = ["telecommuting", "has_company_logo", "has_questions"]

try:
    import nltk
    from nltk.corpus import stopwords
    from nltk.stem import WordNetLemmatizer

    STOPWORDS = set(stopwords.words("english"))
    LEMMATIZER = WordNetLemmatizer()
    HAS_NLTK = True
except Exception:
    STOPWORDS = set()
    LEMMATIZER = None
    HAS_NLTK = False


def clean_text(text: str) -> str:
    text = str(text).lower()
    text = re.sub(r"<.*?>", " ", text)
    text = re.sub(r"http\S+|www\.\S+", " ", text)
    text = text.translate(str.maketrans("", "", string.punctuation))
    text = re.sub(r"\d+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    tokens = text.split()
    if HAS_NLTK:
        tokens = [LEMMATIZER.lemmatize(t) for t in tokens if t not in STOPWORDS and len(t) > 2]
    else:
        tokens = [t for t in tokens if len(t) > 2]
    return " ".join(tokens)


class ModelRegistry:
    def __init__(self):
        self.preprocessor = joblib.load(MODELS_DIR / "preprocessor.joblib")
        self.feature_names = json.load(open(MODELS_DIR / "feature_names.json"))
        self.best_model_name = json.load(open(MODELS_DIR / "best_model.json"))["best_model"]
        self.metrics = json.load(open(MODELS_DIR / "metrics.json"))
        self.eda_summary = json.load(open(MODELS_DIR / "eda_summary.json"))

        self.models = {}
        for f in MODELS_DIR.glob("model_*.joblib"):
            name = f.stem.replace("model_", "")
            self.models[name] = joblib.load(f)

        try:
            self.shap_explainer = joblib.load(MODELS_DIR / "shap_explainer.joblib")
        except Exception:
            self.shap_explainer = None

    def list_models(self):
        return sorted(self.models.keys())

    def get_best_model_name(self):
        return self.best_model_name

    def get_metrics(self):
        return self.metrics

    def get_eda_summary(self):
        return self.eda_summary

    def _row_to_dataframe(self, job: dict):
        import pandas as pd

        full_text = " ".join(
            [
                job.get("title", "") or "",
                job.get("company_profile", "") or "",
                job.get("description", "") or "",
                job.get("requirements", "") or "",
                job.get("benefits", "") or "",
            ]
        )
        row = {
            "clean_text": clean_text(full_text),
        }
        for col in STRUCTURED_CATEGORICAL:
            row[col] = job.get(col) or "Unknown"
        for col in STRUCTURED_BINARY:
            row[col] = int(job.get(col) or 0)

        return pd.DataFrame([row])

    def predict(self, job: dict, model_name: str = None):
        model_name = model_name or self.best_model_name
        if model_name not in self.models:
            raise ValueError(f"Unknown model '{model_name}'. Available: {self.list_models()}")

        model = self.models[model_name]
        df_row = self._row_to_dataframe(job)
        X = self.preprocessor.transform(df_row)

        pred = int(model.predict(X)[0])
        try:
            proba = float(model.predict_proba(X)[0][pred])
        except Exception:
            proba = 1.0

        label = "Fraudulent" if pred == 1 else "Genuine"

        top_factors = self._explain(model_name, model, X)

        return label, proba, top_factors

    def _explain(self, model_name: str, model, X, top_n: int = 8):
        """Return the top contributing features for this single prediction.

        Uses SHAP for the best model (tree-based models get a fast
        TreeExplainer computed on the fly; this is cheap for a single row).
        Falls back to model coefficients / feature importances for other
        models so every model in the comparison dashboard can still show
        *some* explanation, even without a pre-fit SHAP explainer.
        """
        X_dense = X.toarray() if hasattr(X, "toarray") else X

        try:
            if model_name in ("random_forest", "decision_tree", "xgboost"):
                import shap

                explainer = shap.TreeExplainer(model)
                shap_values = explainer.shap_values(X_dense)
                if isinstance(shap_values, list):
                    values = shap_values[1][0]  # class 1 (fraudulent)
                else:
                    values = shap_values[0]
                    if values.ndim > 1:
                        values = values[:, 1]
            elif model_name == "logistic_regression":
                values = model.coef_[0] * X_dense[0]
            else:
                # naive_bayes, dummy: fall back to raw feature magnitude as a
                # rough proxy since these don't have SHAP-friendly structure.
                values = X_dense[0]
        except Exception:
            values = np.zeros(X_dense.shape[1])

        values = np.asarray(values).flatten()
        idx = np.argsort(-np.abs(values))[:top_n]
        factors = [
            {"feature": prettify_feature_name(self.feature_names[i]), "impact": float(values[i])}
            for i in idx
            if abs(values[i]) > 0
        ]
        return factors


def prettify_feature_name(raw: str) -> str:
    """Turn sklearn ColumnTransformer feature names into readable labels.

    e.g. 'text__tfidf__urgent' -> 'word: urgent'
         'cat__ohe__industry_Oil & Energy' -> 'industry = Oil & Energy'
         'remainder__has_company_logo' -> 'has_company_logo'
    """
    if raw.startswith("text__"):
        return f"word: {raw[len('text__'):]}"
    if raw.startswith("cat__"):
        rest = raw[len("cat__"):]
        for col in STRUCTURED_CATEGORICAL:
            if rest.startswith(col + "_"):
                return f"{col} = {rest[len(col) + 1:]}"
        return rest
    if raw.startswith("remainder__"):
        return raw[len("remainder__"):]
    return raw


_registry = None


def get_registry() -> ModelRegistry:
    global _registry
    if _registry is None:
        _registry = ModelRegistry()
    return _registry
