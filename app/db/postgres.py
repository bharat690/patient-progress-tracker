from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import DATABASE_URL


if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not configured")


engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def verify_postgres():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        return result.scalar() == 1
    
def create_tables():
    Base.metadata.create_all(bind=engine)