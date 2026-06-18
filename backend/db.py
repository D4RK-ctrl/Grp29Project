import os
from sqlalchemy import create_engine, Column, String, JSON, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./trips.db"
    ANTHROPIC_API_KEY: str = ""
    FOURSQUARE_API_KEY: str = ""
    YELP_API_KEY: str = ""
    TAVILY_API_KEY: str = ""
    OPENWEATHER_API_KEY: str = ""

    class Config:
        env_file = ".env"


settings = Settings()

# Handle Render's postgres:// URL format
db_url = settings.DATABASE_URL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

connect_args = {"check_same_thread": False} if "sqlite" in db_url else {}
engine = create_engine(db_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class TripModel(Base):
    __tablename__ = "trips"
    id = Column(String, primary_key=True)
    brief = Column(Text)
    status = Column(String, default="planning")  # planning | complete | failed
    itinerary = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ChangeModel(Base):
    __tablename__ = "changes"
    id = Column(String, primary_key=True)
    trip_id = Column(String)
    change_request = Column(Text)
    revised_itinerary = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


def create_tables():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
