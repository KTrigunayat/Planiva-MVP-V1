#!/usr/bin/env python3
"""
Comprehensive data migration script for Event Planning Agent v2
Orchestrates the complete migration process with safety measures
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional
from sqlalchemy import text

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from database.data_migration import DataMigrationManager
from database.validation_tools import DataValidator
from database.rollback_procedures import RollbackManager
from database.migrations import DatabaseMigration

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('migration.log')
    ]
)
logger = logging.getLogger(__name__)


class MigrationOrchestrator:
    """Orchestrates the complete migration process"""
    
    def __init__(self, database_url: Optional[str] = None, old_db_url: Optional[str] = None):
        self.database_url = database_url or os.getenv("DATABASE_URL")
        self.old_db_url = old_db_url or os.getenv("OLD_DATABASE_URL")
        
        # Initialize managers
        self.db_migration = DatabaseMigration(self.database_url)
        self.data_migration = DataMigrationManager(self.old_db_url, self.database_url)
        self.validator = DataValidator(self.database_url)
        self.rollback_manager = RollbackManager(self.database_url)
        
        # Migration tracking
        self.migration_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.migration_log = []
        self.rollback_point = None
    
    def pre_migration_checks(self) -> bool:
        """Perform pre-migration validation checks"""
        logger.info("🔍 Performing pre-migration checks...")
        
        try:
            # Check database connectivity
            with self.data_migration.get_new_session() as session:
                session.execute(text("SELECT 1"))
            logger.info("   ✅ Database connectivity verified")
            
            # Check data files exist
            data_files = [
                "Data_JSON/correct_venue_data.json",
                "Data_JSON/correct_caterers_data.json", 
                "Data_JSON/photographers_data.json",
                "Data_JSON/Makeup_artist.json"
            ]
            
            missing_files = []
            for file_path in data_files:
                if not Path(file_path).exists():
                    missing_files.append(file_path)
            
            if missing_files:
                logger.error(f"❌ Missing data files: {missing_files}")
                return False
            
            logger.info("   ✅ All data files found")
            
            # Validate data file formats
            for file_path in data_files:
                is_valid, errors = self.data_migration.validate_json_data(Path(file_path))
                if not is_valid:
                    logger.error(f"❌ Invalid data file {file_path}: {errors}")
                    return False
            
            logger.info("   ✅ Data file validation passed")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Pre-migration checks failed: {e}")
            return False
    
    def run_schema_migrations(self) -> bool:
        """Run database schema migrations"""
        logger.info("🔄 Running schema migrations...")
        
        try:
            success = self.db_migration.run_all_migrations()
            if success:
                logger.info("   ✅ Schema migrations completed")
                self.migration_log.append("Schema migrations: SUCCESS")
            else:
                logger.error("   ❌ Schema migrations failed")
                self.migration_log.append("Schema migrations: FAILED")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Schema migration error: {e}")
            self.migration_log.append(f"Schema migrations: ERROR - {e}")
            return False
    
    def run_data_migration(self) -> bool:
        """Run data migration"""
        logger.info("🔄 Running data migration...")
        
        try:
            success = self.data_migration.run_full_migration()
            if success:
                logger.info("   ✅ Data migration completed")
                self.migration_log.append("Data migration: SUCCESS")
            else:
                logger.error("   ❌ Data migration failed")
                self.migration_log.append("Data migration: FAILED")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Data migration error: {e}")
            self.migration_log.append(f"Data migration: ERROR - {e}")
            return False
    
    def validate_migration(self) -> bool:
        """Validate migration results"""
        logger.info("🔍 Validating migration results...")
        
        try:
            is_valid, results = self.validator.run_comprehensive_validation()
            
            if is_valid:
                logger.info("   ✅ Migration validation passed")
                self.migration_log.append("Migration validation: SUCCESS")
            else:
                logger.error("   ❌ Migration validation failed")
                self.migration_log.append("Migration validation: FAILED")
                
                # Log validation details
                for error in results['results']['failed']:
                    logger.error(f"      - {error}")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"❌ Migration validation error: {e}")
            self.migration_log.append(f"Migration validation: ERROR - {e}")
            return False
    
    def create_safety_backup(self) -> bool:
        """Create safety backup before migration"""
        logger.info("📸 Creating safety backup...")
        
        try:
            self.rollback_point = self.rollback_manager.create_rollback_point(
                f"Pre-migration backup {self.migration_id}"
            )
            logger.info(f"   ✅ Safety backup created: {self.rollback_point}")
            self.migration_log.append(f"Safety backup: {self.rollback_point}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Safety backup failed: {e}")
            self.migration_log.append(f"Safety backup: FAILED - {e}")
            return False
    
    def run_complete_migration(self, skip_backup: bool = False) -> bool:
        """Run the complete migration process"""
        logger.info("🚀 Starting complete migration process...")
        migration_start = datetime.now()
        
        try:
            # Step 1: Pre-migration checks
            if not self.pre_migration_checks():
                logger.error("❌ Pre-migration checks failed")
                return False
            
            # Step 2: Create safety backup (unless skipped)
            if not skip_backup:
                if not self.create_safety_backup():
                    logger.error("❌ Safety backup failed")
                    return False
            
            # Step 3: Run schema migrations
            if not self.run_schema_migrations():
                logger.error("❌ Schema migrations failed")
                return False
            
            # Step 4: Run data migration
            if not self.run_data_migration():
                logger.error("❌ Data migration failed")
                return False
            
            # Step 5: Validate migration
            if not self.validate_migration():
                logger.error("❌ Migration validation failed")
                return False
            
            # Step 6: Log completion
            migration_end = datetime.now()
            duration = (migration_end - migration_start).total_seconds()
            
            self.migration_log.append(f"Migration completed in {duration:.2f} seconds")
            
            # Save migration report
            self._save_migration_report(migration_start, migration_end, True)
            
            logger.info(f"✅ Complete migration process finished successfully in {duration:.2f} seconds")
            
            if self.rollback_point:
                logger.info(f"📦 Rollback point available: {self.rollback_point}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Migration process failed: {e}")
            self._save_migration_report(migration_start, datetime.now(), False, str(e))
            return False
    
    def _save_migration_report(self, start_time: datetime, end_time: datetime, 
                              success: bool, error: str = None):
        """Save detailed migration report"""
        report = {
            'migration_id': self.migration_id,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration_seconds': (end_time - start_time).total_seconds(),
            'success': success,
            'error': error,
            'rollback_point': self.rollback_point,
            'log': self.migration_log,
            'database_url': self.database_url.replace(
                self.database_url.split('@')[0].split('://')[-1], 
                '***'
            ) if self.database_url else None  # Mask credentials
        }
        
        report_file = Path(f"migration_report_{self.migration_id}.json")
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"📄 Migration report saved: {report_file}")


def main():
    """Main migration script entry point"""
    parser = argparse.ArgumentParser(description='Event Planning Agent v2 Data Migration')
    
    parser.add_argument('--db-url', help='New database URL')
    parser.add_argument('--old-db-url', help='Old database URL (optional)')
    parser.add_argument('--skip-backup', action='store_true', help='Skip safety backup creation')
    parser.add_argument('--validate-only', action='store_true', help='Only run validation')
    parser.add_argument('--schema-only', action='store_true', help='Only run schema migrations')
    parser.add_argument('--data-only', action='store_true', help='Only run data migration')
    
    args = parser.parse_args()
    
    # Initialize orchestrator
    orchestrator = MigrationOrchestrator(args.db_url, args.old_db_url)
    
    try:
        if args.validate_only:
            logger.info("🔍 Running validation only...")
            success = orchestrator.validate_migration()
        
        elif args.schema_only:
            logger.info("🔄 Running schema migrations only...")
            success = orchestrator.run_schema_migrations()
        
        elif args.data_only:
            logger.info("🔄 Running data migration only...")
            success = orchestrator.run_data_migration()
        
        else:
            logger.info("🚀 Running complete migration...")
            success = orchestrator.run_complete_migration(args.skip_backup)
        
        if success:
            logger.info("✅ Migration completed successfully!")
            sys.exit(0)
        else:
            logger.error("❌ Migration failed!")
            sys.exit(1)
    
    except KeyboardInterrupt:
        logger.warning("⚠️ Migration interrupted by user")
        sys.exit(130)
    
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()