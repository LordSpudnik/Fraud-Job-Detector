#!/usr/bin/env bash
# End-to-end smoke test for the backend API.
# Usage: ./scripts/smoke_test.sh [base_url]
# Default base_url is http://localhost:8000

set -e
BASE="${1:-http://localhost:8000}"

echo "1. Health check"
curl -sf "$BASE/api/health" | python3 -m json.tool
echo

echo "2. List models"
curl -sf "$BASE/api/models" | python3 -m json.tool
echo

echo "3. Predict on a suspicious posting"
curl -sf -X POST "$BASE/api/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Work From Home Data Entry - Immediate Start! $5000/week",
    "company_profile": "",
    "description": "No experience needed. Send your bank details and SSN to start immediately. Urgent, limited spots, wire transfer required for training kit.",
    "requirements": "Must have a bank account",
    "benefits": "Guaranteed income",
    "employment_type": "Full-time",
    "required_experience": "Not Applicable",
    "required_education": "Unspecified",
    "industry": "Unknown",
    "function": "Unknown",
    "telecommuting": 1,
    "has_company_logo": 0,
    "has_questions": 0
  }' | python3 -m json.tool
echo

echo "4. Predict on a genuine-looking posting"
curl -sf -X POST "$BASE/api/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Senior Backend Engineer",
    "company_profile": "We are an established fintech company with 10 years in business.",
    "description": "We are looking for an experienced backend engineer to join our engineering team.",
    "requirements": "5+ years experience with Python, strong CS fundamentals.",
    "benefits": "Health insurance, 401k matching, remote-friendly.",
    "employment_type": "Full-time",
    "required_experience": "Mid-Senior level",
    "required_education": "Bachelor'"'"'s Degree",
    "industry": "Computer Software",
    "function": "Engineering",
    "telecommuting": 0,
    "has_company_logo": 1,
    "has_questions": 1
  }' | python3 -m json.tool
echo

echo "5. Model comparison"
curl -sf "$BASE/api/models/compare" | python3 -m json.tool | head -20
echo

echo "6. Dataset EDA summary"
curl -sf "$BASE/api/eda" | python3 -m json.tool | head -20
echo

echo "7. Prediction history"
curl -sf "$BASE/api/history" | python3 -m json.tool
echo

echo "All checks passed."
