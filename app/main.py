from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import app.models
from app.api.auth import router as auth_router
from app.api.documents import document_router, router as documents_router
from app.api.patients import router as patients_router
from app.core.config import CORS_ALLOWED_ORIGINS, validate_auth_config
from app.db.neo4j import close_neo4j, verify_neo4j
from app.db.postgres import create_tables, verify_postgres


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting Patient Progress Tracker...")

    validate_auth_config()
    create_tables()

    yield

    close_neo4j()
    print("Connections closed.")


app = FastAPI(
    title="Patient Progress Tracker",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(patients_router)
app.include_router(documents_router)
app.include_router(document_router)


@app.get("/")
def root():
    return {
        "application": "Patient Progress Tracker",
        "status": "running",
    }


@app.get("/health/postgres")
def postgres_health():
    connected = verify_postgres()

    return {
        "database": "postgresql",
        "connected": connected,
    }


@app.get("/health/neo4j")
def neo4j_health():
    connected = verify_neo4j()

    return {
        "database": "neo4j",
        "connected": connected,
    }


@app.get("/health")
def health():
    postgres = verify_postgres()
    neo4j = verify_neo4j()

    return {
        "status": "healthy",
        "postgres": postgres,
        "neo4j": neo4j,
    }