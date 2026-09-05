"""
Training pipeline for the Fraudulent Job Posting Detection system.

What this script does, in order:
  1. Loads the raw EMSCAD-based "Fake Job Postings" dataset (~17,880 rows).
  2. Cleans it (missing values, duplicates).
  3. Runs EDA and saves the plots the PRD asks for (fraud distribution,
     missing values, industry distribution, salary patterns, word frequency,
     correlation heatmap).
  4. Builds structured + text features (TF-IDF with n-grams, encoded
     categorical fields).
  5. Trains 6 models: Dummy, Logistic Regression, Naive Bayes, Decision
     Tree, Random Forest, XGBoost.
  6. Evaluates every model on the same held-out test set (Accuracy,
     Precision, Recall, F1, ROC-AUC, confusion matrix, PR curve).
  7. Picks the best model by F1 on the fraud (minority) class.
  8. Fits a SHAP explainer on the best model and saves it.
  9. Saves everything the backend needs into backend/models/.

Run it with:  python ml/train.py
Expected runtime: 2-5 minutes on a laptop CPU.
"""

import json
import os
import re
import string
import warnings
from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import shap
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.tree import DecisionTreeClassifier
from xgboost import XGBClassifier

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "fake_job_postings.csv"
MODELS_DIR = ROOT / "backend" / "models"
PLOTS_DIR = ROOT / "docs" / "eda_plots"
METRICS_PATH = MODELS_DIR / "metrics.json"

MODELS_DIR.mkdir(parents=True, exist_ok=True)
PLOTS_DIR.mkdir(parents=True, exist_ok=True)

RANDOM_STATE = 42

STRUCTURED_CATEGORICAL = [
    "employment_type",
    "required_experience",
    "required_education",
    "industry",
    "function",
]
STRUCTURED_BINARY = ["telecommuting", "has_company_logo", "has_questions"]
TEXT_COLUMNS = ["title", "company_profile", "description", "requirements", "benefits"]

try:
    import nltk
    from nltk.corpus import stopwords
    from nltk.stem import WordNetLemmatizer

    for pkg in ["stopwords", "wordnet", "omw-1.4"]:
        try:
            nltk.data.find(f"corpora/{pkg}")
        except LookupError:
            nltk.download(pkg, quiet=True)
    STOPWORDS = set(stopwords.words("english"))
    LEMMATIZER = WordNetLemmatizer()
    HAS_NLTK = True
except Exception:
    STOPWORDS = set()
    LEMMATIZER = None
    HAS_NLTK = False


# ---------------------------------------------------------------------------
# 1-3. Load, clean, EDA
# ---------------------------------------------------------------------------
def load_and_clean(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df = df.drop_duplicates()

    # Fill missing text with empty string, missing categoricals with "Unknown"
    for col in TEXT_COLUMNS:
        df[col] = df[col].fillna("")
    for col in STRUCTURED_CATEGORICAL:
        df[col] = df[col].fillna("Unknown")
    for col in STRUCTURED_BINARY:
        df[col] = df[col].fillna(0).astype(int)

    df["fraudulent"] = df["fraudulent"].astype(int)

    # Combined text field used for TF-IDF
    df["full_text"] = (
        df["title"] + " " + df["company_profile"] + " " + df["description"] + " "
        + df["requirements"] + " " + df["benefits"]
    )
    return df


def clean_text(text: str) -> str:
    text = str(text).lower()
    text = re.sub(r"<.*?>", " ", text)  # strip HTML tags
    text = re.sub(r"http\S+|www\.\S+", " ", text)  # strip URLs
    text = text.translate(str.maketrans("", "", string.punctuation))
    text = re.sub(r"\d+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    tokens = text.split()
    if HAS_NLTK:
        tokens = [LEMMATIZER.lemmatize(t) for t in tokens if t not in STOPWORDS and len(t) > 2]
    else:
        tokens = [t for t in tokens if len(t) > 2]
    return " ".join(tokens)


def run_eda(df: pd.DataFrame) -> dict:
    summary = {}

    # Fraud class distribution
    counts = df["fraudulent"].value_counts()
    summary["fraud_distribution"] = {"genuine": int(counts.get(0, 0)), "fraudulent": int(counts.get(1, 0))}
    plt.figure(figsize=(5, 4))
    sns.countplot(x="fraudulent", data=df, palette=["#4C72B0", "#C44E52"])
    plt.xticks([0, 1], ["Genuine", "Fraudulent"])
    plt.title("Fraud Class Distribution")
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "fraud_distribution.png", dpi=120)
    plt.close()

    # Missing values (on the original raw columns, before fill)
    raw = pd.read_csv(DATA_PATH)
    missing = raw.isnull().mean().sort_values(ascending=False) * 100
    summary["missing_values_pct"] = missing.round(2).to_dict()
    plt.figure(figsize=(7, 6))
    missing[missing > 0].plot(kind="barh", color="#DD8452")
    plt.xlabel("% missing")
    plt.title("Missing Values by Column")
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "missing_values.png", dpi=120)
    plt.close()

    # Industry distribution (top 10)
    top_industries = df["industry"].value_counts().head(10)
    summary["top_industries"] = top_industries.to_dict()
    plt.figure(figsize=(7, 5))
    top_industries.plot(kind="bar", color="#55A868")
    plt.title("Top 10 Industries by Job Posting Volume")
    plt.ylabel("Count")
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "industry_distribution.png", dpi=120)
    plt.close()

    # Salary presence vs fraud
    df["has_salary"] = df["salary_range"].notna().astype(int)
    salary_fraud = df.groupby("has_salary")["fraudulent"].mean() * 100
    summary["fraud_rate_by_salary_presence_pct"] = salary_fraud.round(2).to_dict()
    plt.figure(figsize=(5, 4))
    salary_fraud.plot(kind="bar", color="#8172B2")
    plt.xticks([0, 1], ["No salary listed", "Salary listed"], rotation=0)
    plt.ylabel("Fraud rate (%)")
    plt.title("Fraud Rate by Salary Field Presence")
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "salary_vs_fraud.png", dpi=120)
    plt.close()

    # Word frequency in fraudulent postings
    fraud_text = " ".join(df.loc[df["fraudulent"] == 1, "full_text"].apply(clean_text))
    words = pd.Series(fraud_text.split()).value_counts().head(20)
    summary["top_fraud_words"] = words.to_dict()
    plt.figure(figsize=(7, 6))
    words.sort_values().plot(kind="barh", color="#C44E52")
    plt.title("Top 20 Words in Fraudulent Job Postings")
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "word_frequency_fraud.png", dpi=120)
    plt.close()

    # Correlation heatmap of numeric/binary features
    numeric_cols = STRUCTURED_BINARY + ["fraudulent"]
    corr = df[numeric_cols].corr()
    plt.figure(figsize=(6, 5))
    sns.heatmap(corr, annot=True, cmap="coolwarm", fmt=".2f")
    plt.title("Correlation Heatmap (Structured Binary Features)")
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "correlation_heatmap.png", dpi=120)
    plt.close()

    return summary


# ---------------------------------------------------------------------------
# 4-7. Feature engineering, training, evaluation
# ---------------------------------------------------------------------------
def build_preprocessor() -> ColumnTransformer:
    text_pipe = Pipeline([
        ("tfidf", TfidfVectorizer(max_features=5000, ngram_range=(1, 2), min_df=3)),
    ])
    cat_pipe = Pipeline([
        ("ohe", OneHotEncoder(handle_unknown="ignore")),
    ])
    preprocessor = ColumnTransformer(
        transformers=[
            ("text", text_pipe, "clean_text"),
            ("cat", cat_pipe, STRUCTURED_CATEGORICAL),
        ],
        remainder="passthrough",  # passes through the binary columns
    )
    return preprocessor


def get_models() -> dict:
    return {
        "dummy": DummyClassifier(strategy="most_frequent"),
        "logistic_regression": LogisticRegression(max_iter=1000, class_weight="balanced", random_state=RANDOM_STATE),
        "naive_bayes": MultinomialNB(),
        "decision_tree": DecisionTreeClassifier(max_depth=20, class_weight="balanced", random_state=RANDOM_STATE),
        "random_forest": RandomForestClassifier(
            n_estimators=200, max_depth=None, class_weight="balanced", random_state=RANDOM_STATE, n_jobs=-1
        ),
        "xgboost": XGBClassifier(
            n_estimators=300,
            max_depth=6,
            learning_rate=0.1,
            eval_metric="logloss",
            random_state=RANDOM_STATE,
            scale_pos_weight=17,  # roughly genuine/fraud ratio, helps the minority class
        ),
    }


def evaluate(model, X_test, y_test) -> dict:
    y_pred = model.predict(X_test)
    try:
        y_proba = model.predict_proba(X_test)[:, 1]
    except Exception:
        y_proba = y_pred.astype(float)

    cm = confusion_matrix(y_test, y_pred).tolist()
    fpr, tpr, _ = roc_curve(y_test, y_proba)
    prec, rec, _ = precision_recall_curve(y_test, y_proba)

    return {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision": float(precision_score(y_test, y_pred, zero_division=0)),
        "recall": float(recall_score(y_test, y_pred, zero_division=0)),
        "f1": float(f1_score(y_test, y_pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_test, y_proba)),
        "confusion_matrix": cm,
        "roc_curve": {"fpr": fpr.tolist()[::5], "tpr": tpr.tolist()[::5]},
        "pr_curve": {"precision": prec.tolist()[::5], "recall": rec.tolist()[::5]},
    }


def main():
    print("Loading and cleaning data...")
    df = load_and_clean(DATA_PATH)
    print(f"  {len(df)} rows after cleaning/dedup.")

    print("Running EDA and saving plots to docs/eda_plots/ ...")
    eda_summary = run_eda(df)

    print("Preprocessing text (this takes ~30-60s)...")
    df["clean_text"] = df["full_text"].apply(clean_text)

    feature_cols = ["clean_text"] + STRUCTURED_CATEGORICAL + STRUCTURED_BINARY
    X = df[feature_cols]
    y = df["fraudulent"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y
    )
    print(f"  Train: {len(X_train)}  Test: {len(X_test)}")

    preprocessor = build_preprocessor()
    print("Fitting feature preprocessor...")
    X_train_t = preprocessor.fit_transform(X_train)
    X_test_t = preprocessor.transform(X_test)

    models = get_models()
    results = {}
    fitted_models = {}

    for name, model in models.items():
        print(f"Training {name} ...")
        model.fit(X_train_t, y_train)
        metrics = evaluate(model, X_test_t, y_test)
        results[name] = metrics
        fitted_models[name] = model
        print(f"  {name}: accuracy={metrics['accuracy']:.4f} f1={metrics['f1']:.4f} roc_auc={metrics['roc_auc']:.4f}")

    best_name = max(results, key=lambda n: results[n]["f1"])
    print(f"\nBest model by F1 score: {best_name}")

    # Save everything the backend needs
    joblib.dump(preprocessor, MODELS_DIR / "preprocessor.joblib")
    for name, model in fitted_models.items():
        joblib.dump(model, MODELS_DIR / f"model_{name}.joblib")

    with open(MODELS_DIR / "best_model.json", "w") as f:
        json.dump({"best_model": best_name}, f, indent=2)

    with open(METRICS_PATH, "w") as f:
        json.dump(results, f, indent=2)

    with open(MODELS_DIR / "eda_summary.json", "w") as f:
        json.dump(eda_summary, f, indent=2, default=str)

    # ---- SHAP explainer on the best model ----
    print("Fitting SHAP explainer on the best model (this may take a minute)...")
    best_model = fitted_models[best_name]
    feature_names = preprocessor.get_feature_names_out()

    # Use a small background sample for speed
    background_idx = np.random.RandomState(RANDOM_STATE).choice(
        X_train_t.shape[0], size=min(100, X_train_t.shape[0]), replace=False
    )
    background = X_train_t[background_idx]
    if hasattr(background, "toarray"):
        background = background.toarray()

    if best_name in ("random_forest", "decision_tree", "xgboost"):
        explainer = shap.TreeExplainer(best_model)
    else:
        # Model-agnostic fallback (slower, so we cap background size)
        predict_fn = best_model.predict_proba
        explainer = shap.KernelExplainer(predict_fn, background[:50])

    joblib.dump(explainer, MODELS_DIR / "shap_explainer.joblib")
    with open(MODELS_DIR / "feature_names.json", "w") as f:
        json.dump(list(feature_names), f)

    print("\nDone. Artifacts saved to backend/models/:")
    for p in sorted(MODELS_DIR.glob("*")):
        print(f"  {p.name}")


if __name__ == "__main__":
    main()
