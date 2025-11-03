"""
Database setup and initialization for Event Planning Agent v2
"""

import logging
import asyncio
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from .connection import get_sync_session, get_async_session
from .models import Base
from ..config.settings import get_settings

logger = logging.getLogger(__name__)


async def initialize_database():
    """Initialize database schema and perform setup tasks"""
    try:
        settings = get_settings()
        
        logger.info("Initializing database...")
        
        # Create engine for schema creation
        engine = create_engine(settings.database_url)
        
        # Create all tables
        Base.metadata.create_all(engine)
        logger.info("Database tables created successfully")
        
        # Test database connectivity
        with get_sync_session() as session:
            result = session.execute(text("SELECT 1"))
            if result.scalar() == 1:
                logger.info("Database connectivity test passed")
            else:
                raise Exception("Database connectivity test failed")
        
        logger.info("Database initialization completed successfully")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


def setup_observability():
    """Setup observability components"""
    try:
        logger.info("Setting up observability...")
        
        # Initialize logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        logger.info("Observability setup completed")
        
    except Exception as e:
        logger.error(f"Observability setup failed: {e}")
        raise