from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Creates a local SQLite database file named 'recipe_ocr.db'
SQLALCHEMY_DATABASE_URL = "sqlite:///./recipe_ocr.db"

# connect_args={"check_same_thread": False} is needed only for SQLite in FastAPI
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """Dependency to get a database session for FastAPI."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()