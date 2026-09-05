# Sentry: Explainable Fraud Detection for Job Postings

Sentry is a full-stack machine learning system that detects fraudulent job postings using a combination of natural language processing and structured data analysis. It classifies listings as Genuine or Fraudulent, explains every prediction with SHAP, and lets you compare the performance of six different models side by side.

## Overview

Online job boards are an easy target for scammers. Sentry was built to catch fraudulent listings automatically by analyzing both the text of a posting (title, description, requirements, benefits) and its structured metadata (industry, employment type, whether a salary is listed, and so on).

Instead of just returning a yes or no answer, Sentry shows you the specific words and fields that drove each prediction, so the output is something a human can actually trust and verify.

## Features

- Predicts whether a job posting is genuine or fraudulent, with a confidence score
- Explains each prediction using SHAP, showing the top contributing factors
- Trains and compares six models: Dummy Classifier, Logistic Regression, Naive Bayes, Decision Tree, Random Forest, and XGBoost
- Full evaluation suite: accuracy, precision, recall, F1 score, ROC AUC, confusion matrix, and precision recall curves
- Interactive dashboard built with React, including a model comparison view and dataset statistics
- Persistent prediction history stored in a database
- Fully containerized with Docker Compose (PostgreSQL, FastAPI backend, React frontend)

## Tech Stack

**Frontend:** React, Vite, Recharts

**Backend:** FastAPI, SQLAlchemy

**Machine Learning:** scikit-learn, XGBoost, SHAP

**NLP:** NLTK, TF-IDF, n-grams

**Database:** PostgreSQL (SQLite supported for local development)

**Deployment:** Docker, Docker Compose

## Dataset

This project uses the EMSCAD-derived Fake Job Postings dataset, containing approximately 17,880 real job listings labeled as genuine or fraudulent. The dataset includes both free text fields (title, description, requirements, benefits, company profile) and structured fields (employment type, required experience, required education, industry, function, and more).

## Model Performance

All six models were trained and evaluated on the same held out test split. XGBoost was selected as the production model based on F1 score, since the dataset is heavily imbalanced (roughly 95 percent genuine, 5 percent fraudulent).

| Model | Accuracy | F1 Score | ROC AUC |
|---|---|---|---|
| Dummy Classifier | 0.952 | 0.000 | 0.500 |
| Logistic Regression | 0.966 | 0.724 | 0.985 |
| Naive Bayes | 0.964 | 0.557 | 0.927 |
| Decision Tree | 0.937 | 0.561 | 0.896 |
| Random Forest | 0.980 | 0.733 | 0.992 |
| XGBoost (selected) | 0.984 | 0.832 | 0.990 |

## Project Structure

```
project/
├── data/                   Raw dataset (CSV)
├── ml/
│   └── train.py            Training pipeline: cleaning, EDA, feature engineering, model training
├── backend/
│   ├── app/                FastAPI application
│   └── models/             Trained model artifacts and metrics
├── frontend/
│   └── src/                React application
├── docs/
│   └── eda_plots/          Generated exploratory data analysis plots
├── scripts/
│   └── smoke_test.sh       End to end API test script
└── docker-compose.yml
```

## Getting Started

### Option 1: Run with Docker (recommended)

1. Make sure Docker Desktop is installed and running.
2. From the project root, run:
   ```
   docker compose up --build
   ```
3. Once the build finishes, open the app at `http://localhost:3010`.
4. The API and its interactive documentation are available at `http://localhost:8010/docs`.

### Option 2: Run manually

**Backend**

```
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m nltk.downloader stopwords wordnet omw-1.4
uvicorn app.main:app --reload --port 8000
```

**Frontend**

```
cd frontend
npm install
npm run dev
```

Then open `http://localhost:5173`. The frontend dev server automatically forwards API requests to the backend on port 8000.

## Retraining the Models

Trained models and evaluation results are already included in the repository. To retrain from scratch, for example after changing the feature engineering or adding new data, run:

```
python ml/train.py
```

This regenerates the EDA plots, retrains all six models, re-evaluates them, and refits the SHAP explainer on the best performing model.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/predict` | Submit a job posting and get a prediction |
| GET | `/api/models` | List available trained models |
| GET | `/api/models/compare` | Get evaluation metrics for all models |
| GET | `/api/eda` | Get dataset exploratory analysis summary |
| GET | `/api/history` | Get prediction history |
| DELETE | `/api/history` | Clear prediction history |

## Testing

Run the included smoke test script to verify every endpoint works end to end:

```
./scripts/smoke_test.sh
```

For a Docker deployment, point it at the mapped port instead:

```
./scripts/smoke_test.sh http://localhost:8010
```
