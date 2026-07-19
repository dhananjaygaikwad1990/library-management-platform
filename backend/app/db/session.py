import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

DATABASE_URL = os.getenv("TEST_DATABASE_URL") or os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:12345@localhost:5432/postgres",
)

engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()
