FROM python:3.11-slim

WORKDIR /app

# System deps needed for some scientific packages (xgboost, shap, matplotlib)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# NLTK data needed at inference time for text cleaning
RUN python -m nltk.downloader stopwords wordnet omw-1.4

COPY app ./app
COPY models ./models

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
