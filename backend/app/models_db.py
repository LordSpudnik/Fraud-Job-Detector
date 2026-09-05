"""SQLAlchemy ORM table for storing prediction history."""

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text

from app.database import Base


class PredictionRecord(Base):
    __tablename__ = "prediction_history"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    title = Column(String, nullable=True)
    company_profile = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    requirements = Column(Text, nullable=True)
    benefits = Column(Text, nullable=True)
    employment_type = Column(String, nullable=True)
    required_experience = Column(String, nullable=True)
    required_education = Column(String, nullable=True)
    industry = Column(String, nullable=True)
    function = Column(String, nullable=True)
    telecommuting = Column(Integer, default=0)
    has_company_logo = Column(Integer, default=0)
    has_questions = Column(Integer, default=0)

    model_used = Column(String, nullable=False)
    prediction = Column(String, nullable=False)  # "Genuine" or "Fraudulent"
    confidence = Column(Float, nullable=False)
    top_factors = Column(Text, nullable=True)  # JSON-encoded SHAP top factors
