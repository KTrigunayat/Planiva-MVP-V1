"""
CRM Database Migration Runner

This script runs the CRM schema migration and validates the setup.
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional

import asyncpg
from asyncpg import Connection

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import get_settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def run_migration(conn: Connection, migration_file: Path) -> bool:
    """
    Run a single migration file.
    
    Args:
        conn: Database connection
        migration_file: Path to SQL migration file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info(f"Running migration: {migration_file.name}")
        
        # Read migration SQL
        sql = migration_file.read_text(encoding='utf-8')
        
        # Execute migration
        await conn.execute(sql)
        
        logger.info(f"✓ Migration completed: {migration_file.name}")
        return True
        
    except Exception as e:
        logger.error(f"✗ Migration failed: {migration_file.name}")
        logger.error(f"Error: {e}")
        return False


async def verify_tables(conn: Connection) -> bool:
    """
    Verify that all CRM tables were created successfully.
    
    Args:
        conn: Database connection
        
    Returns:
        True if all tables exist, False otherwise
    """
    required_tables = [
        'crm_communications',
        'crm_client_preferences',
        'crm_communication_templates',
        'crm_delivery_logs'
    ]
    
    logger.info("Verifying CRM tables...")
    
    for table_name in required_tables:
        exists = await conn.fetchval(
            """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = $1
            )
            """,
            table_name
        )
        
        if exists:
            logger.info(f"✓ Table exists: {table_name}")
        else:
            logger.error(f"✗ Table missing: {table_name}")
            return False
    
    return True


async def verify_indexes(conn: Connection) -> bool:
    """
    Verify that all CRM indexes were created successfully.
    
    Args:
        conn: Database connection
        
    Returns:
        True if key indexes exist, False otherwise
    """
    key_indexes = [
        'idx_crm_communications_plan_id',
        'idx_crm_communications_client_id',
        'idx_crm_communications_status',
        'idx_crm_client_preferences_timezone',
        'idx_crm_templates_lookup',
        'idx_crm_delivery_logs_communication_id'
    ]
    
    logger.info("Verifying CRM indexes...")
    
    for index_name in key_indexes:
        exists = await conn.fetchval(
            """
            SELECT EXISTS (
                SELECT FROM pg_indexes 
                WHERE schemaname = 'public' 
                AND indexname = $1
            )
            """,
            index_name
        )
        
        if exists:
            logger.info(f"✓ Index exists: {index_name}")
        else:
            logger.warning(f"⚠ Index missing: {index_name}")
    
    return True


async def verify_view(conn: Connection) -> bool:
    """
    Verify that the analytics view was created successfully.
    
    Args:
        conn: Database connection
        
    Returns:
        True if view exists, False otherwise
    """
    logger.info("Verifying CRM analytics view...")
    
    exists = await conn.fetchval(
        """
        SELECT EXISTS (
            SELECT FROM information_schema.views 
            WHERE table_schema = 'public' 
            AND table_name = 'crm_communication_analytics'
        )
        """
    )
    
    if exists:
        logger.info("✓ View exists: crm_communication_analytics")
        return True
    else:
        logger.error("✗ View missing: crm_communication_analytics")
        return False


async def get_table_stats(conn: Connection) -> dict:
    """
    Get statistics about CRM tables.
    
    Args:
        conn: Database connection
        
    Returns:
        Dictionary with table statistics
    """
    stats = {}
    
    tables = [
        'crm_communications',
        'crm_client_preferences',
        'crm_communication_templates',
        'crm_delivery_logs'
    ]
    
    for table in tables:
        count = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
        stats[table] = count
    
    return stats


async def main():
    """Main migration runner."""
    logger.info("=" * 70)
    logger.info("CRM Database Migration Runner")
    logger.info("=" * 70)
    
    # Load settings
    try:
        settings = get_settings()
        db_url = settings.get_database_url()
        logger.info(f"Database URL: {db_url.split('@')[1] if '@' in db_url else 'configured'}")
    except Exception as e:
        logger.error(f"Failed to load settings: {e}")
        return 1
    
    # Connect to database
    try:
        conn = await asyncpg.connect(db_url)
        logger.info("✓ Database connection established")
    except Exception as e:
        logger.error(f"✗ Failed to connect to database: {e}")
        return 1
    
    try:
        # Run migration
        migration_file = Path(__file__).parent / "migrations" / "003_crm_complete_schema.sql"
        
        if not migration_file.exists():
            logger.error(f"Migration file not found: {migration_file}")
            return 1
        
        success = await run_migration(conn, migration_file)
        
        if not success:
            logger.error("Migration failed!")
            return 1
        
        # Verify setup
        logger.info("")
        logger.info("=" * 70)
        logger.info("Verifying Migration")
        logger.info("=" * 70)
        
        tables_ok = await verify_tables(conn)
        indexes_ok = await verify_indexes(conn)
        view_ok = await verify_view(conn)
        
        if not (tables_ok and view_ok):
            logger.error("Verification failed!")
            return 1
        
        # Get statistics
        logger.info("")
        logger.info("=" * 70)
        logger.info("Table Statistics")
        logger.info("=" * 70)
        
        stats = await get_table_stats(conn)
        for table, count in stats.items():
            logger.info(f"{table}: {count} rows")
        
        logger.info("")
        logger.info("=" * 70)
        logger.info("✓ CRM Migration Completed Successfully!")
        logger.info("=" * 70)
        
        return 0
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1
        
    finally:
        await conn.close()
        logger.info("Database connection closed")


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
