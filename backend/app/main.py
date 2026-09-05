from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import history, models_info, predict


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create DB tables on startup
    Base.metadata.create_all(bind=engine)
    # Warm up the model registry so the first prediction isn't slow
    from app.ml.inference import get_registry

    get_registry()
    yield


app = FastAPI(
    title="Fraudulent Job Posting Detection API",
    description="Explainable ML/NLP system for detecting fraudulent online job advertisements.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(predict.router)
app.include_router(models_info.router)
app.include_router(history.router)


@app.get("/")
def root():
    return {"status": "ok", "message": "Fraudulent Job Posting Detection API. See /docs for the API reference."}


@app.get("/api/health")
def health():
    return {"status": "healthy"}
