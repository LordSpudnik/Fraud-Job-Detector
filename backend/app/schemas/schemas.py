from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class JobPostingInput(BaseModel):
    title: str = Field(..., example="Marketing Intern")
    company_profile: str = Field("", example="We are a fast-growing startup...")
    description: str = Field(..., example="Looking for a motivated marketing intern...")
    requirements: str = Field("", example="Currently enrolled in a bachelor's degree...")
    benefits: str = Field("", example="Flexible hours, mentorship...")
    employment_type: str = Field("Full-time", example="Full-time")
    required_experience: str = Field("Not Applicable", example="Entry level")
    required_education: str = Field("Unspecified", example="Bachelor's Degree")
    industry: str = Field("Unknown", example="Marketing and Advertising")
    function: str = Field("Unknown", example="Marketing")
    telecommuting: int = Field(0, ge=0, le=1)
    has_company_logo: int = Field(0, ge=0, le=1)
    has_questions: int = Field(0, ge=0, le=1)
    model_name: Optional[str] = Field(
        None, description="Which trained model to use. Defaults to the best model found during training."
    )


class ShapFactor(BaseModel):
    feature: str
    impact: float


class PredictionResponse(BaseModel):
    prediction: str
    confidence: float
    model_used: str
    top_factors: List[ShapFactor]
    record_id: int


class ModelMetrics(BaseModel):
    accuracy: float
    precision: float
    recall: float
    f1: float
    roc_auc: float
    confusion_matrix: List[List[int]]
    roc_curve: dict
    pr_curve: dict


class ModelComparisonResponse(BaseModel):
    best_model: str
    models: dict  # model_name -> ModelMetrics-like dict


class HistoryItem(BaseModel):
    id: int
    created_at: datetime
    title: Optional[str]
    model_used: str
    prediction: str
    confidence: float

    class Config:
        from_attributes = True


class EdaSummaryResponse(BaseModel):
    fraud_distribution: dict
    missing_values_pct: dict
    top_industries: dict
    fraud_rate_by_salary_presence_pct: dict
    top_fraud_words: dict
