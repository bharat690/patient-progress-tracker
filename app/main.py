from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db.neo4j import close_neo4j
from app.db.neo4j import verify_neo4j
from app.db.postgres import verify_postgres


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting Patient Progress Tracker...")

    yield

    close_neo4j()
    print("Connections closed.")


app = FastAPI(
    title="Patient Progress Tracker",
    version="0.1.0",
    lifespan=lifespan,
)


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