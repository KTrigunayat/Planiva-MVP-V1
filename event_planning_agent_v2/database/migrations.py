"""
Data migration utilities for Event Planning Agent v2
Migrates existing vendor data to enhanced schema with validation and rollback capabilities.
"""

import json
import logging
import uuid
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from contextlib import contextmanager
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import settings (will be created if not exists)
try:
    from config.settings import get_settings
except ImportError:
    # Fallback settings for standalone execution
    class Settings:
        database_url = os.getenv("DATABASE_URL", "postgresql://eventuser:eventpass@localhost:5432/eventdb")
        database_echo = False
    
    def get_settings():
        return Settings()


class DatabaseMigration:
    """Database migration manager"""
    
    def __init__(self, database_url: Optional[str] = None):
        self.settings = get_settings()
        self.database_url = database_url or self.settings.database_url
        self.engine = create_engine(self.database_url, echo=self.settings.database_echo)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
    @contextmanager
    def get_session(self):
        """Get database session with proper cleanup"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def get_current_schema_version(self) -> str:
        """Get current database schema version"""
        try:
            with self.get_session() as session:
                # Check if migration_history table exists
                inspector = inspect(self.engine)
                if 'migration_history' not in inspector.get_table_names():
                    return "0.0.0"  # No migrations applied
                
                result = session.execute(text("""
                    SELECT version FROM migration_history 
                    ORDER BY applied_at DESC LIMIT 1
                """)).fetchone()
                
                return result[0] if result else "0.0.0"
                
        except Exception as e:
            logger.warning(f"Could not determine schema version: {e}")
            return "unknown"
    
    def create_migration_history_table(self) -> None:
        """Create migration history tracking table"""
        try:
            with self.get_session() as session:
                session.execute(text("""
                    CREATE TABLE IF NOT EXISTS migration_history (
                        id SERIAL PRIMARY KEY,
                        version VARCHAR(20) NOT NULL,
                        description TEXT,
                        applied_at TIMESTAMPTZ DEFAULT NOW(),
                        success BOOLEAN DEFAULT TRUE,
                        error_message TEXT
                    );
                """))
                logger.info("Created migration_history table")
        except Exception as e:
            logger.error(f"Failed to create migration_history table: {e}")
            raise
    
    def record_migration(self, version: str, description: str, success: bool = True, error: str = None) -> None:
        """Record migration in history table"""
        try:
            with self.get_session() as session:
                session.execute(text("""
                    INSERT INTO migration_history (version, description, success, error_message)
                    VALUES (:version, :description, :success, :error)
                """), {
                    'version': version,
                    'description': description,
                    'success': success,
                    'error': error
                })
        except Exception as e:
            logger.error(f"Failed to record migration: {e}")
    
    def migrate_to_v1_0_0(self) -> bool:
        """
        Migration to v1.0.0: Add LangGraph state management tables
        - Enhance event_plans table with workflow state columns
        - Add agent_performance table
        - Add workflow_metrics table
        - Add system_health table
        """
        version = "1.0.0"
        description = "Add LangGraph state management and monitoring tables"
        
        try:
            logger.info(f"🔄 Applying migration {version}: {description}")
            
            with self.get_session() as session:
                # Check if event_plans table exists (from old schema)
                inspector = inspect(self.engine)
                existing_tables = inspector.get_table_names()
                
                if 'event_plans' in existing_tables:
                    # Enhance existing event_plans table
                    logger.info("   Enhancing existing event_plans table...")
                    
                    # Add new columns to event_plans
                    new_columns = [
                        "ADD COLUMN IF NOT EXISTS workflow_state JSONB",
                        "ADD COLUMN IF NOT EXISTS beam_history JSONB", 
                        "ADD COLUMN IF NOT EXISTS agent_logs JSONB",
                        "ADD COLUMN IF NOT EXISTS selected_combination JSONB",
                        "ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW()"
                    ]
                    
                    for column_sql in new_columns:
                        session.execute(text(f"ALTER TABLE event_plans {column_sql};"))
                    
                    # Add update trigger for updated_at
                    session.execute(text("""
                        CREATE OR REPLACE FUNCTION update_updated_at_column()
                        RETURNS TRIGGER AS $$
                        BEGIN
                            NEW.updated_at = NOW();
                            RETURN NEW;
                        END;
                        $$ language 'plpgsql';
                    """))
                    
                    session.execute(text("""
                        DROP TRIGGER IF EXISTS update_event_plans_updated_at ON event_plans;
                        CREATE TRIGGER update_event_plans_updated_at
                            BEFORE UPDATE ON event_plans
                            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
                    """))
                    
                else:
                    # Create new event_plans table
                    logger.info("   Creating new event_plans table...")
                    session.execute(text("""
                        CREATE TABLE event_plans (
                            plan_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                            client_id VARCHAR(255),
                            status VARCHAR(50) NOT NULL DEFAULT 'initialized',
                            plan_data JSONB,
                            workflow_state JSONB,
                            beam_history JSONB,
                            agent_logs JSONB,
                            final_blueprint TEXT,
                            selected_combination JSONB,
                            created_at TIMESTAMPTZ DEFAULT NOW(),
                            updated_at TIMESTAMPTZ DEFAULT NOW()
                        );
                    """))
                
                # Create agent_performance table
                logger.info("   Creating agent_performance table...")
                session.execute(text("""
                    CREATE TABLE IF NOT EXISTS agent_performance (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        plan_id UUID REFERENCES event_plans(plan_id),
                        agent_name VARCHAR(100) NOT NULL,
                        task_name VARCHAR(100) NOT NULL,
                        execution_time_ms INTEGER,
                        success BOOLEAN NOT NULL,
                        error_message TEXT,
                        input_data JSONB,
                        output_data JSONB,
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    );
                """))
                
                # Create workflow_metrics table
                logger.info("   Creating workflow_metrics table...")
                session.execute(text("""
                    CREATE TABLE IF NOT EXISTS workflow_metrics (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        plan_id UUID REFERENCES event_plans(plan_id),
                        total_iterations INTEGER,
                        total_execution_time_ms INTEGER,
                        combinations_evaluated INTEGER,
                        final_score FLOAT,
                        beam_width_used INTEGER DEFAULT 3,
                        convergence_iteration INTEGER,
                        error_count INTEGER DEFAULT 0,
                        retry_count INTEGER DEFAULT 0,
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    );
                """))
                
                # Create system_health table
                logger.info("   Creating system_health table...")
                session.execute(text("""
                    CREATE TABLE IF NOT EXISTS system_health (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        component_name VARCHAR(100) NOT NULL,
                        status VARCHAR(20) NOT NULL,
                        response_time_ms INTEGER,
                        error_message TEXT,
                        metadata JSONB,
                        checked_at TIMESTAMPTZ DEFAULT NOW()
                    );
                """))
                
                # Create performance indexes
                logger.info("   Creating performance indexes...")
                indexes = [
                    "CREATE INDEX IF NOT EXISTS idx_event_plans_client ON event_plans(client_id);",
                    "CREATE INDEX IF NOT EXISTS idx_event_plans_status ON event_plans(status);",
                    "CREATE INDEX IF NOT EXISTS idx_event_plans_created ON event_plans(created_at);",
                    "CREATE INDEX IF NOT EXISTS idx_event_plans_workflow_state_gin ON event_plans USING GIN (workflow_state);",
                    "CREATE INDEX IF NOT EXISTS idx_event_plans_beam_history_gin ON event_plans USING GIN (beam_history);",
                    
                    "CREATE INDEX IF NOT EXISTS idx_agent_perf_plan ON agent_performance(plan_id);",
                    "CREATE INDEX IF NOT EXISTS idx_agent_perf_agent ON agent_performance(agent_name);",
                    "CREATE INDEX IF NOT EXISTS idx_agent_perf_success ON agent_performance(success);",
                    "CREATE INDEX IF NOT EXISTS idx_agent_perf_time ON agent_performance(execution_time_ms);",
                    "CREATE INDEX IF NOT EXISTS idx_agent_perf_created ON agent_performance(created_at);",
                    
                    "CREATE INDEX IF NOT EXISTS idx_workflow_metrics_plan ON workflow_metrics(plan_id);",
                    "CREATE INDEX IF NOT EXISTS idx_workflow_metrics_score ON workflow_metrics(final_score);",
                    "CREATE INDEX IF NOT EXISTS idx_workflow_metrics_time ON workflow_metrics(total_execution_time_ms);",
                    "CREATE INDEX IF NOT EXISTS idx_workflow_metrics_created ON workflow_metrics(created_at);",
                    
                    "CREATE INDEX IF NOT EXISTS idx_system_health_component ON system_health(component_name);",
                    "CREATE INDEX IF NOT EXISTS idx_system_health_status ON system_health(status);",
                    "CREATE INDEX IF NOT EXISTS idx_system_health_checked ON system_health(checked_at);"
                ]
                
                for index_sql in indexes:
                    session.execute(text(index_sql))
            
            # Record successful migration
            self.record_migration(version, description, success=True)
            logger.info(f"✅ Migration {version} completed successfully")
            return True
            
        except Exception as e:
            error_msg = f"Migration {version} failed: {e}"
            logger.error(f"❌ {error_msg}")
            self.record_migration(version, description, success=False, error=str(e))
            return False
    
    def migrate_vendor_tables_v1_1_0(self) -> bool:
        """
        Migration to v1.1.0: Enhance vendor tables with better indexing
        - Add performance indexes to vendor tables
        - Add GIN indexes for JSONB attributes
        """
        version = "1.1.0"
        description = "Enhance vendor tables with performance indexes"
        
        try:
            logger.info(f"🔄 Applying migration {version}: {description}")
            
            with self.get_session() as session:
                # Add indexes for vendor tables
                vendor_indexes = [
                    # Venues
                    "CREATE INDEX IF NOT EXISTS idx_venues_city ON venues(location_city);",
                    "CREATE INDEX IF NOT EXISTS idx_venues_capacity ON venues(ideal_capacity);",
                    "CREATE INDEX IF NOT EXISTS idx_venues_cost ON venues(rental_cost);",
                    "CREATE INDEX IF NOT EXISTS idx_venues_attributes_gin ON venues USING GIN (attributes);",
                    
                    # Caterers
                    "CREATE INDEX IF NOT EXISTS idx_caterers_city ON caterers(location_city);",
                    "CREATE INDEX IF NOT EXISTS idx_caterers_veg_price ON caterers(min_veg_price);",
                    "CREATE INDEX IF NOT EXISTS idx_caterers_capacity ON caterers(max_guest_capacity);",
                    "CREATE INDEX IF NOT EXISTS idx_caterers_attributes_gin ON caterers USING GIN (attributes);",
                    
                    # Photographers
                    "CREATE INDEX IF NOT EXISTS idx_photographers_city ON photographers(location_city);",
                    "CREATE INDEX IF NOT EXISTS idx_photographers_price ON photographers(photo_package_price);",
                    "CREATE INDEX IF NOT EXISTS idx_photographers_attributes_gin ON photographers USING GIN (attributes);",
                    
                    # Makeup Artists
                    "CREATE INDEX IF NOT EXISTS idx_makeup_artists_city ON makeup_artists(location_city);",
                    "CREATE INDEX IF NOT EXISTS idx_makeup_artists_price ON makeup_artists(bridal_makeup_price);",
                    "CREATE INDEX IF NOT EXISTS idx_makeup_artists_attributes_gin ON makeup_artists USING GIN (attributes);"
                ]
                
                logger.info("   Creating vendor table indexes...")
                for index_sql in vendor_indexes:
                    session.execute(text(index_sql))
            
            # Record successful migration
            self.record_migration(version, description, success=True)
            logger.info(f"✅ Migration {version} completed successfully")
            return True
            
        except Exception as e:
            error_msg = f"Migration {version} failed: {e}"
            logger.error(f"❌ {error_msg}")
            self.record_migration(version, description, success=False, error=str(e))
            return False
    
    def migrate_task_management_tables_v1_2_0(self) -> bool:
        """
        Migration to v1.2.0: Add Task Management Agent tables
        - Create task_management_runs table for run metadata
        - Create extended_tasks table for enhanced task data
        - Create task_conflicts table for conflict tracking
        - Add performance indexes and constraints
        """
        version = "1.2.0"
        description = "Add Task Management Agent tables"
        
        try:
            logger.info(f"🔄 Applying migration {version}: {description}")
            
            # Read SQL migration file
            migration_file = Path(__file__).parent / "migrations" / "add_task_management_tables.sql"
            
            if not migration_file.exists():
                raise FileNotFoundError(f"Migration file not found: {migration_file}")
            
            with open(migration_file, 'r', encoding='utf-8') as f:
                migration_sql = f.read()
            
            logger.info("   Executing Task Management tables migration...")
            
            with self.get_session() as session:
                # Execute the entire SQL migration script
                session.execute(text(migration_sql))
            
            # Record successful migration
            self.record_migration(version, description, success=True)
            logger.info(f"✅ Migration {version} completed successfully")
            return True
            
        except FileNotFoundError as e:
            error_msg = f"Migration {version} failed: {e}"
            logger.error(f"❌ {error_msg}")
            logger.error("   Please ensure the migration SQL file exists at: database/migrations/add_task_management_tables.sql")
            self.record_migration(version, description, success=False, error=str(e))
            return False
            
        except Exception as e:
            error_msg = f"Migration {version} failed: {e}"
            logger.error(f"❌ {error_msg}")
            self.record_migration(version, description, success=False, error=str(e))
            return False
    
    def migrate_crm_tables_v1_3_0(self) -> bool:
        """
        Migration to v1.3.0: Add CRM Communication Engine tables
        - Create crm_communications table for tracking all communications
        - Create crm_client_preferences table for client preferences
        - Create crm_communication_templates table for message templates
        - Create crm_delivery_logs table for delivery tracking
        - Add performance indexes and default templates
        """
        version = "1.3.0"
        description = "Add CRM Communication Engine tables"
        
        try:
            logger.info(f"🔄 Applying migration {version}: {description}")
            
            # Read SQL migration file
            migration_file = Path(__file__).parent / "migrations" / "add_crm_tables.sql"
            
            if not migration_file.exists():
                raise FileNotFoundError(f"Migration file not found: {migration_file}")
            
            with open(migration_file, 'r', encoding='utf-8') as f:
                migration_sql = f.read()
            
            logger.info("   Executing CRM tables migration...")
            
            with self.get_session() as session:
                # Execute the entire SQL migration script
                session.execute(text(migration_sql))
            
            # Record successful migration
            self.record_migration(version, description, success=True)
            logger.info(f"✅ Migration {version} completed successfully")
            return True
            
        except FileNotFoundError as e:
            error_msg = f"Migration {version} failed: {e}"
            logger.error(f"❌ {error_msg}")
            logger.error("   Please ensure the migration SQL file exists at: database/migrations/add_crm_tables.sql")
            self.record_migration(version, description, success=False, error=str(e))
            return False
            
        except Exception as e:
            error_msg = f"Migration {version} failed: {e}"
            logger.error(f"❌ {error_msg}")
            self.record_migration(version, description, success=False, error=str(e))
            return False
    
    def run_all_migrations(self) -> bool:
        """Run all pending migrations"""
        logger.info("🚀 Starting database migrations...")
        
        # Create migration history table if it doesn't exist
        self.create_migration_history_table()
        
        # Get current version
        current_version = self.get_current_schema_version()
        logger.info(f"Current schema version: {current_version}")
        
        # Define migration sequence
        migrations = [
            ("1.0.0", self.migrate_to_v1_0_0),
            ("1.1.0", self.migrate_vendor_tables_v1_1_0),
            ("1.2.0", self.migrate_task_management_tables_v1_2_0),
            ("1.3.0", self.migrate_crm_tables_v1_3_0),
        ]
        
        success = True
        for version, migration_func in migrations:
            if self._should_run_migration(current_version, version):
                if not migration_func():
                    success = False
                    break
            else:
                logger.info(f"⏭️ Skipping migration {version} (already applied)")
        
        if success:
            logger.info("✅ All migrations completed successfully!")
        else:
            logger.error("❌ Migration process failed")
        
        return success
    
    def _should_run_migration(self, current_version: str, target_version: str) -> bool:
        """Check if migration should be run based on version comparison"""
        if current_version == "unknown":
            return True
        
        try:
            # Simple version comparison (assumes semantic versioning)
            current_parts = [int(x) for x in current_version.split('.')]
            target_parts = [int(x) for x in target_version.split('.')]
            
            # Pad with zeros if needed
            max_len = max(len(current_parts), len(target_parts))
            current_parts.extend([0] * (max_len - len(current_parts)))
            target_parts.extend([0] * (max_len - len(target_parts)))
            
            return target_parts > current_parts
            
        except Exception:
            # If version comparison fails, run the migration
            return True
    
    def rollback_migration(self, target_version: str) -> bool:
        """Rollback to a specific version (limited rollback support)"""
        logger.warning("⚠️ Migration rollback is not fully implemented")
        logger.warning("   Manual intervention may be required for complete rollback")
        
        # For now, just record the rollback attempt
        self.record_migration(
            f"rollback_to_{target_version}",
            f"Attempted rollback to version {target_version}",
            success=False,
            error="Rollback not fully implemented"
        )
        
        return False
    
    def get_migration_history(self) -> List[Dict[str, Any]]:
        """Get migration history"""
        try:
            with self.get_session() as session:
                result = session.execute(text("""
                    SELECT version, description, applied_at, success, error_message
                    FROM migration_history
                    ORDER BY applied_at DESC
                """)).fetchall()
                
                return [
                    {
                        'version': row[0],
                        'description': row[1],
                        'applied_at': row[2],
                        'success': row[3],
                        'error_message': row[4]
                    }
                    for row in result
                ]
        except Exception as e:
            logger.error(f"Failed to get migration history: {e}")
            return []


def run_migrations(database_url: Optional[str] = None) -> bool:
    """
    Run all pending database migrations
    
    Args:
        database_url: Database connection URL
    
    Returns:
        True if all migrations succeeded, False otherwise
    """
    migration = DatabaseMigration(database_url)
    return migration.run_all_migrations()


if __name__ == "__main__":
    import sys
    import argparse
    import json
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    parser = argparse.ArgumentParser(description='Database migrations for Event Planning Agent')
    parser.add_argument('--history', action='store_true', help='Show migration history')
    parser.add_argument('--version', action='store_true', help='Show current schema version')
    parser.add_argument('--rollback', help='Rollback to specific version (limited support)')
    
    args = parser.parse_args()
    
    migration = DatabaseMigration()
    
    if args.history:
        history = migration.get_migration_history()
        print(json.dumps(history, indent=2, default=str))
    elif args.version:
        version = migration.get_current_schema_version()
        print(f"Current schema version: {version}")
    elif args.rollback:
        success = migration.rollback_migration(args.rollback)
        sys.exit(0 if success else 1)
    else:
        success = migration.run_all_migrations()
        sys.exit(0 if success else 1)