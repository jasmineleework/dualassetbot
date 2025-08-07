"""
Database configuration and session management
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from core.config import settings
from loguru import logger
import os

# Create database URL
if settings.database_url.startswith("sqlite"):
    # For SQLite, ensure the directory exists
    db_path = settings.database_url.replace("sqlite:///", "")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # SQLite specific settings for better concurrency
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=settings.debug
    )
else:
    # PostgreSQL or other databases
    engine = create_engine(
        settings.database_url,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        echo=settings.debug
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

def get_db() -> Session:
    """
    Get database session
    
    Usage:
        with get_db() as db:
            # Use db session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database - create all tables"""
    try:
        # Import all models to ensure they are registered
        from models import user, investment, market_data, strategy_log
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

def drop_all_tables():
    """Drop all tables - use with caution!"""
    Base.metadata.drop_all(bind=engine)
    logger.warning("All database tables dropped!")