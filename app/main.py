from contextlib import asynccontextmanager

from fastapi import FastAPI

import app.models

from app.db.neo4j import close_neo4j
from app.db.neo4j import verify_neo4j
from app.db.postgres import verify_postgres
from app.db.postgres import create_tables

from app.api.patients import router as patients_router
from app.api.documents import router as documents_router

from sqlalchemy import select

from app.db.postgres import SessionLocal
from app.models.user import User



@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting Patient Progress Tracker...")

    create_tables()

    with SessionLocal() as db:
        existing_user = db.scalar(
            select(User).where(
                User.email == "demo@patienttracker.local"
            )
        )

        if existing_user is None:
            demo_user = User(
                name="Demo Doctor",
                email="demo@patienttracker.local",
                role="doctor",
            )

            db.add(demo_user)
            db.commit()

    yield

    close_neo4j()
    print("Connections closed.")
    


app = FastAPI(
    title="Patient Progress Tracker",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(patients_router)
app.include_router(documents_router)

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