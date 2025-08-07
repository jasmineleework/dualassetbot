#!/usr/bin/env python3
"""
Initialize database - create all tables
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from core.database import init_db, engine
from core.config import settings
from loguru import logger

def main():
    """Initialize database"""
    logger.info(f"Initializing database: {settings.database_url}")
    
    try:
        # Create all tables
        init_db()
        
        # Verify tables were created
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        logger.info(f"Created {len(tables)} tables:")
        for table in tables:
            logger.info(f"  - {table}")
        
        logger.success("Database initialized successfully!")
        return 0
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())