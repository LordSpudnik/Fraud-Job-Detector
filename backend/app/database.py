"""
Database setup.

By default this uses a local SQLite file (backend/predictions.db) so the
project runs with zero external setup. Set the DATABASE_URL environment
variable to point at PostgreSQL instead (this is what docker-compose does),
matching the PRD's requirement of a PostgreSQL-backed prediction history.

Example Postgres URL:
    postgresql://fraud_user:fraud_pass@db:5432/fraud_detection
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./predictions.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
