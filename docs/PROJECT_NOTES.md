# Project Notes — how this implementation maps to the PRD and Review 2

Direct assessment of what's actually delivered vs. what the documents
describe, so there are no surprises in a review or demo.

## Fully matches the PRD

- Dataset: real EMSCAD-derived Fake Job Postings CSV, ~17,880 rows, not a
  subsample or synthetic stand-in.
- All 6 models trained and compared (Dummy, Logistic Regression, Naive
  Bayes, Decision Tree, Random Forest, XGBoost) on the same test split.
- All 7 evaluation metrics computed: Accuracy, Precision, Recall, F1,
  ROC-AUC, Confusion Matrix, Precision-Recall Curve.
- NLP pipeline exactly as specified: lowercasing, HTML tag removal,
  tokenization, stop-word removal, lemmatization, TF-IDF, n-grams.
- SHAP explainability on the best-performing model, surfaced per
  individual prediction (not just an aggregate chart).
- React + FastAPI full-stack deployment.
- Prediction history with confidence scores, persisted.
- Dashboard sections: dataset statistics, prediction page, model
  comparison, feature importance (via SHAP factors), ROC curve, confusion
  matrix.
- Structured feature handling (employment type, company logo, salary
  presence, etc.) combined with unstructured text.

## Simplified or worth knowing about before you present this

- **Database default is SQLite, not Postgres.** Postgres is fully wired up
  in `docker-compose.yml` and works if you run it that way — but the
  zero-setup manual path (`uvicorn app.main:app`) uses SQLite unless you
  set `DATABASE_URL`. If a reviewer asks "is this PostgreSQL," the honest
  answer is "yes, via Docker; SQLite is the local dev default."
- **SHAP is computed live per-request for tree models**, not by reusing
  a single frozen background distribution across the whole app session.
  This is the practically correct way to do single-row explanations, but
  if you're asked "how does the explainer relate to the one saved during
  training," the answer is: the training run fits and saves an explainer
  object as evidence of methodology, but the API refits a lightweight
  TreeExplainer per prediction for accuracy and speed. For Logistic
  Regression the explanation is coefficient × feature value (a standard
  linear-model attribution, not SHAP in the strict sense). For Naive Bayes
  and the Dummy baseline, there isn't a principled per-feature attribution
  method built in — the "factors" shown are a rough magnitude proxy, and
  the UI/README says so. Don't present those two as SHAP explanations if
  asked directly.
- **The 6 EDA plots described in the PRD (Section 10) are generated as
  static PNGs** by `ml/train.py` into `docs/eda_plots/`, not re-rendered
  live in the React dashboard as interactive charts — the dashboard's
  "Dataset & EDA" page renders the same underlying numbers as
  lightweight bar charts. If a grader specifically wants to see the PNGs,
  they're in `docs/eda_plots/` after you run the training script (or open
  the ones already generated).
- **Docker builds are not layer-optimized for size** (backend image
  includes build-essential for compiling scientific packages; this is
  normal but makes the image a few hundred MB larger than a minimal
  runtime image). Fine for a course project, worth noting if size ever
  matters.
- **No automated test suite (pytest) is included** — verification is done
  via `scripts/smoke_test.sh`, which is an end-to-end script, not unit
  tests with mocking. If your rubric specifically credits unit tests,
  that's a gap, not something already covered under a different name.
- **Class imbalance handling**: XGBoost uses `scale_pos_weight`, and
  Logistic Regression / Decision Tree / Random Forest use
  `class_weight="balanced"`. This is a standard, defensible approach, but
  it is not SMOTE/ADASYN oversampling, which some of the papers in your
  literature survey used. If your research gap section claims you solve
  the "imbalance + deployment" gap other papers didn't close, be precise
  about which imbalance technique you're actually using — `class_weight`
  is not the same technique as SMOTE, and a reviewer familiar with the
  literature may ask the difference.
- **Conference paper (PRD Section 5, "prepare a conference paper") is not
  part of this deliverable** — this is code and documentation, not the
  paper itself. You'll still need to write that up separately, though the
  metrics, plots, and methodology described here give you the results
  section's raw material.

## Where the numbers actually landed (real run, not illustrative)

From the training run used to produce the shipped artifacts:

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC |
|---|---|---|---|---|---|
| Dummy | 0.952 | 0.000 | 0.000 | 0.000 | 0.500 |
| Logistic Regression | 0.966 | 0.602 | 0.908 | 0.724 | 0.985 |
| Naive Bayes | 0.964 | — | — | 0.557 | 0.927 |
| Decision Tree | 0.937 | — | — | 0.561 | 0.896 |
| Random Forest | 0.980 | — | — | 0.733 | 0.992 |
| **XGBoost (selected)** | **0.984** | — | — | **0.832** | 0.990 |

Full numbers, including precision/recall for every model, are in
`backend/models/metrics.json` and visible live on the Model Comparison
page. XGBoost was selected automatically by the training script because
it has the highest F1 score on the fraud (minority) class — that's the
right metric to optimize here, since accuracy alone is misleading on a
95/5 imbalanced dataset (the Dummy baseline's 95.2% accuracy from always
guessing "genuine" makes that obvious).
