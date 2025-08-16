"""
Database configuration for the application.
"""

# app/config/database.py
from app.config.settings import settings
from app.config.logger import logger
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import os
from typing import Generator

# Create Base class for models
Base = declarative_base()

# Database URL from Environment settings
DATABASE_URL = settings.DATABASE_URL

# Create SQLAlchemy engine
if DATABASE_URL.startswith("sqlite"):
    
    # Logging the use of SQLite
    logger.info("Using SQLite database with URL: %s", DATABASE_URL)
    
    # SQLite specific configuration
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},  # Needed for SQLite
        poolclass=StaticPool,  # Use static pool for SQLite
        echo=True  # Set to False in production
    )
else:
    
    # Logging the use of PostgreSQL or MySQL
    logger.info("Using PostgreSQL/MySQL database with URL: %s", DATABASE_URL)
    
    # PostgreSQL/MySQL configuration
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,  # Verify connections before use
        pool_recycle=300,    # Recycle connections every 5 minutes
        echo=True  # Set to False in production
    )

# Create SessionLocal class
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Dependency to get database session
def get_db() -> Generator:
    """
    Database session dependency for FastAPI.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()