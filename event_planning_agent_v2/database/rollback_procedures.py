"""
Rollback procedures for Event Planning Agent v2 migrations
Provides safe rollback capabilities for database migrations and data changes
"""

import json
import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from contextlib import contextmanager
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RollbackManager:
    """Manages rollback procedures for database migrations"""
    
    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or os.getenv("DATABASE_URL", 
            "postgresql://eventuser:eventpass@localhost:5432/eventdb")
        self.engine = create_engine(self.database_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Backup and rollback directories
        self.backup_dir = Path("migration_backups")
        self.rollback_dir = Path("rollback_scripts")
        self.backup_dir.mkdir(exist_ok=True)
        self.rollback_dir.mkdir(exist_ok=True)
        
        # Rollback tracking
        self.rollback_id = str(datetime.now().strftime("%Y%m%d_%H%M%S"))
        self.rollback_log = []
    
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
    
    def create_rollback_point(self, description: str) -> str:
        """Create a rollback point with full database backup"""
        logger.info(f"📸 Creating rollback point: {description}")
        
        rollback_point_id = f"rollback_{self.rollback_id}_{len(self.rollback_log)}"
        rollback_dir = self.backup_dir / rollback_point_id
        rollback_dir.mkdir(exist_ok=True)
        
        try:
            with self.get_session() as session:
                # Get all tables
                inspector = inspect(self.engine)
                tables = inspector.get_table_names()
                
                backup_manifest = {
                    'rollback_point_id': rollback_point_id,
                    'description': description,
                    'created_at': datetime.now().isoformat(),
                    'tables': {},
                    'schema_version': self._get_schema_version(session)
                }
                
                # Backup each table
                for table in tables:
                    try:
                        table_file = rollback_dir / f"{table}.json"
                        
                        # Export table data
                        result = session.execute(text(f"SELECT * FROM {table}")).fetchall()
                        
                        # Convert to JSON serializable format
                        table_data = []
                        for row in result:
                            row_dict = dict(row._mapping) if hasattr(row, '_mapping') else dict(row)
                            # Convert special types to strings
                            for key, value in row_dict.items():
                                if hasattr(value, 'isoformat'):  # datetime objects
                                    row_dict[key] = value.isoformat()
                                elif str(type(value)) == "<class 'uuid.UUID'>":  # UUID objects
                                    row_dict[key] = str(value)
                            table_data.append(row_dict)
                        
                        # Save table data
                        with open(table_file, 'w', encoding='utf-8') as f:
                            json.dump(table_data, f, indent=2, default=str)
                        
                        backup_manifest['tables'][table] = {
                            'file': str(table_file),
                            'record_count': len(table_data),
                            'backup_size_bytes': table_file.stat().st_size
                        }
                        
                        logger.info(f"   ✅ Backed up {table}: {len(table_data)} records")
                    
                    except Exception as e:
                        logger.error(f"   ❌ Failed to backup table {table}: {e}")
                        backup_manifest['tables'][table] = {'error': str(e)}
                
                # Save backup manifest
                manifest_file = rollback_dir / "manifest.json"
                with open(manifest_file, 'w', encoding='utf-8') as f:
                    json.dump(backup_manifest, f, indent=2, default=str)
                
                # Create schema backup
                self._backup_schema(session, rollback_dir)
                
                self.rollback_log.append({
                    'action': 'create_rollback_point',
                    'rollback_point_id': rollback_point_id,
                    'description': description,
                    'timestamp': datetime.now().isoformat()
                })
                
                logger.info(f"✅ Rollback point created: {rollback_point_id}")
                return rollback_point_id
                
        except Exception as e:
            logger.error(f"❌ Failed to create rollback point: {e}")
            # Clean up partial backup
            if rollback_dir.exists():
                shutil.rmtree(rollback_dir)
            raise
    
    def _backup_schema(self, session, backup_dir: Path):
        """Backup database schema"""
        try:
            # Export schema using pg_dump equivalent query
            schema_queries = [
                # Tables
                """
                SELECT 'CREATE TABLE ' || schemaname||'.'||tablename||' (' || 
                       array_to_string(array_agg(column_name||' '||data_type), ', ') || ');'
                FROM information_schema.columns 
                WHERE table_schema = 'public'
                GROUP BY schemaname, tablename
                """,
                
                # Indexes
                """
                SELECT indexdef || ';'
                FROM pg_indexes 
                WHERE schemaname = 'public'
                """,
                
                # Constraints
                """
                SELECT 'ALTER TABLE ' || table_name || ' ADD CONSTRAINT ' || constraint_name || 
                       ' ' || constraint_type || ';'
                FROM information_schema.table_constraints
                WHERE table_schema = 'public'
                """
            ]
            
            schema_backup = {
                'tables': [],
                'indexes': [],
                'constraints': []
            }
            
            for i, query in enumerate(schema_queries):
                try:
                    result = session.execute(text(query)).fetchall()
                    key = ['tables', 'indexes', 'constraints'][i]
                    schema_backup[key] = [row[0] for row in result]
                except Exception as e:
                    logger.warning(f"Could not backup schema component {i}: {e}")
            
            # Save schema backup
            schema_file = backup_dir / "schema.json"
            with open(schema_file, 'w', encoding='utf-8') as f:
                json.dump(schema_backup, f, indent=2)
            
            logger.info("   ✅ Schema backed up")
            
        except Exception as e:
            logger.warning(f"Schema backup failed: {e}")
    
    def _get_schema_version(self, session) -> str:
        """Get current schema version"""
        try:
            result = session.execute(text("""
                SELECT version FROM migration_history 
                ORDER BY applied_at DESC LIMIT 1
            """)).fetchone()
            return result[0] if result else "unknown"
        except Exception:
            return "unknown"    
  
  def list_rollback_points(self) -> List[Dict[str, Any]]:
        """List available rollback points"""
        rollback_points = []
        
        try:
            for rollback_dir in self.backup_dir.iterdir():
                if rollback_dir.is_dir() and rollback_dir.name.startswith('rollback_'):
                    manifest_file = rollback_dir / "manifest.json"
                    
                    if manifest_file.exists():
                        try:
                            with open(manifest_file, 'r', encoding='utf-8') as f:
                                manifest = json.load(f)
                            
                            rollback_points.append({
                                'rollback_point_id': manifest['rollback_point_id'],
                                'description': manifest['description'],
                                'created_at': manifest['created_at'],
                                'schema_version': manifest.get('schema_version', 'unknown'),
                                'table_count': len(manifest['tables']),
                                'backup_path': str(rollback_dir)
                            })
                        except Exception as e:
                            logger.warning(f"Could not read rollback point {rollback_dir.name}: {e}")
            
            # Sort by creation time (newest first)
            rollback_points.sort(key=lambda x: x['created_at'], reverse=True)
            
        except Exception as e:
            logger.error(f"Failed to list rollback points: {e}")
        
        return rollback_points
    
    def rollback_to_point(self, rollback_point_id: str, confirm: bool = False) -> bool:
        """Rollback database to a specific rollback point"""
        if not confirm:
            logger.warning("⚠️ Rollback operation requires confirmation. Set confirm=True to proceed.")
            return False
        
        logger.info(f"🔄 Rolling back to point: {rollback_point_id}")
        
        rollback_dir = self.backup_dir / rollback_point_id
        manifest_file = rollback_dir / "manifest.json"
        
        if not rollback_dir.exists() or not manifest_file.exists():
            logger.error(f"❌ Rollback point not found: {rollback_point_id}")
            return False
        
        try:
            # Load rollback manifest
            with open(manifest_file, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            
            logger.info(f"   📋 Rollback description: {manifest['description']}")
            logger.info(f"   📅 Created at: {manifest['created_at']}")
            
            # Create a rollback point before proceeding (safety measure)
            safety_point = self.create_rollback_point(f"Safety backup before rollback to {rollback_point_id}")
            
            with self.get_session() as session:
                # Disable foreign key checks temporarily
                session.execute(text("SET session_replication_role = replica;"))
                
                rollback_success = True
                restored_tables = []
                
                # Restore each table
                for table_name, table_info in manifest['tables'].items():
                    if 'error' in table_info:
                        logger.warning(f"   ⏭️ Skipping {table_name} (backup error)")
                        continue
                    
                    try:
                        table_file = Path(table_info['file'])
                        
                        if not table_file.exists():
                            logger.error(f"   ❌ Backup file not found for {table_name}: {table_file}")
                            rollback_success = False
                            continue
                        
                        # Load table data
                        with open(table_file, 'r', encoding='utf-8') as f:
                            table_data = json.load(f)
                        
                        # Clear current table data
                        session.execute(text(f"DELETE FROM {table_name}"))
                        
                        # Restore data
                        if table_data:
                            # Get column names from first record
                            columns = list(table_data[0].keys())
                            placeholders = ', '.join([f':{col}' for col in columns])
                            
                            insert_sql = f"""
                                INSERT INTO {table_name} ({', '.join(columns)})
                                VALUES ({placeholders})
                            """
                            
                            for record in table_data:
                                session.execute(text(insert_sql), record)
                        
                        restored_tables.append(table_name)
                        logger.info(f"   ✅ Restored {table_name}: {len(table_data)} records")
                    
                    except Exception as e:
                        logger.error(f"   ❌ Failed to restore {table_name}: {e}")
                        rollback_success = False
                
                # Re-enable foreign key checks
                session.execute(text("SET session_replication_role = DEFAULT;"))
                
                if rollback_success:
                    # Update migration history
                    session.execute(text("""
                        INSERT INTO migration_history (version, description, success)
                        VALUES (:version, :description, :success)
                    """), {
                        'version': f"rollback_{rollback_point_id}",
                        'description': f"Rollback to {rollback_point_id}: {manifest['description']}",
                        'success': True
                    })
                    
                    self.rollback_log.append({
                        'action': 'rollback_completed',
                        'rollback_point_id': rollback_point_id,
                        'restored_tables': restored_tables,
                        'safety_backup': safety_point,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    logger.info(f"✅ Rollback completed successfully")
                    logger.info(f"   📦 Safety backup created: {safety_point}")
                    return True
                else:
                    logger.error(f"❌ Rollback failed - some tables could not be restored")
                    return False
                
        except Exception as e:
            logger.error(f"❌ Rollback failed: {e}")
            return False
    
    def rollback_last_migration(self, confirm: bool = False) -> bool:
        """Rollback the last migration"""
        if not confirm:
            logger.warning("⚠️ Rollback operation requires confirmation. Set confirm=True to proceed.")
            return False
        
        logger.info("🔄 Rolling back last migration...")
        
        try:
            with self.get_session() as session:
                # Get last migration
                result = session.execute(text("""
                    SELECT version, description FROM migration_history 
                    WHERE success = true AND version NOT LIKE 'rollback_%'
                    ORDER BY applied_at DESC LIMIT 1
                """)).fetchone()
                
                if not result:
                    logger.warning("No migrations found to rollback")
                    return False
                
                last_version, last_description = result
                logger.info(f"   📋 Last migration: {last_version} - {last_description}")
                
                # Find appropriate rollback point
                rollback_points = self.list_rollback_points()
                
                # Look for rollback point created before this migration
                suitable_point = None
                for point in rollback_points:
                    if point['schema_version'] != last_version:
                        suitable_point = point
                        break
                
                if not suitable_point:
                    logger.error("❌ No suitable rollback point found")
                    return False
                
                logger.info(f"   🎯 Using rollback point: {suitable_point['rollback_point_id']}")
                return self.rollback_to_point(suitable_point['rollback_point_id'], confirm=True)
                
        except Exception as e:
            logger.error(f"❌ Failed to rollback last migration: {e}")
            return False
    
    def cleanup_old_rollback_points(self, keep_count: int = 5) -> bool:
        """Clean up old rollback points, keeping only the most recent ones"""
        logger.info(f"🧹 Cleaning up old rollback points (keeping {keep_count})...")
        
        try:
            rollback_points = self.list_rollback_points()
            
            if len(rollback_points) <= keep_count:
                logger.info(f"   ✅ Only {len(rollback_points)} rollback points exist, no cleanup needed")
                return True
            
            # Remove oldest rollback points
            points_to_remove = rollback_points[keep_count:]
            
            for point in points_to_remove:
                try:
                    rollback_dir = Path(point['backup_path'])
                    if rollback_dir.exists():
                        shutil.rmtree(rollback_dir)
                        logger.info(f"   🗑️ Removed rollback point: {point['rollback_point_id']}")
                except Exception as e:
                    logger.warning(f"   ⚠️ Failed to remove {point['rollback_point_id']}: {e}")
            
            logger.info(f"✅ Cleanup completed, {len(points_to_remove)} rollback points removed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Cleanup failed: {e}")
            return False
    
    def validate_rollback_point(self, rollback_point_id: str) -> Tuple[bool, List[str]]:
        """Validate a rollback point for integrity"""
        logger.info(f"🔍 Validating rollback point: {rollback_point_id}")
        
        rollback_dir = self.backup_dir / rollback_point_id
        manifest_file = rollback_dir / "manifest.json"
        
        validation_errors = []
        
        if not rollback_dir.exists():
            validation_errors.append(f"Rollback directory not found: {rollback_dir}")
            return False, validation_errors
        
        if not manifest_file.exists():
            validation_errors.append(f"Manifest file not found: {manifest_file}")
            return False, validation_errors
        
        try:
            # Load and validate manifest
            with open(manifest_file, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            
            required_fields = ['rollback_point_id', 'description', 'created_at', 'tables']
            for field in required_fields:
                if field not in manifest:
                    validation_errors.append(f"Missing manifest field: {field}")
            
            # Validate table backups
            for table_name, table_info in manifest['tables'].items():
                if 'error' in table_info:
                    validation_errors.append(f"Table {table_name} has backup error: {table_info['error']}")
                    continue
                
                if 'file' not in table_info:
                    validation_errors.append(f"Table {table_name} missing file path")
                    continue
                
                table_file = Path(table_info['file'])
                if not table_file.exists():
                    validation_errors.append(f"Table backup file not found: {table_file}")
                    continue
                
                # Validate JSON format
                try:
                    with open(table_file, 'r', encoding='utf-8') as f:
                        table_data = json.load(f)
                    
                    if not isinstance(table_data, list):
                        validation_errors.append(f"Table {table_name} backup is not a list")
                    
                    # Check record count matches manifest
                    if len(table_data) != table_info.get('record_count', 0):
                        validation_errors.append(f"Table {table_name} record count mismatch")
                
                except json.JSONDecodeError as e:
                    validation_errors.append(f"Table {table_name} backup has invalid JSON: {e}")
                except Exception as e:
                    validation_errors.append(f"Table {table_name} validation error: {e}")
            
            is_valid = len(validation_errors) == 0
            
            if is_valid:
                logger.info(f"✅ Rollback point validation passed")
            else:
                logger.error(f"❌ Rollback point validation failed: {len(validation_errors)} errors")
            
            return is_valid, validation_errors
            
        except Exception as e:
            validation_errors.append(f"Manifest validation error: {e}")
            return False, validation_errors
    
    def get_rollback_log(self) -> List[Dict[str, Any]]:
        """Get rollback operation log"""
        return self.rollback_log.copy()


def create_rollback_point(description: str, database_url: Optional[str] = None) -> str:
    """
    Create a rollback point for the database
    
    Args:
        description: Description of the rollback point
        database_url: Database connection URL
    
    Returns:
        Rollback point ID
    """
    rollback_manager = RollbackManager(database_url)
    return rollback_manager.create_rollback_point(description)


def rollback_to_point(rollback_point_id: str, database_url: Optional[str] = None, confirm: bool = False) -> bool:
    """
    Rollback database to a specific point
    
    Args:
        rollback_point_id: ID of the rollback point
        database_url: Database connection URL
        confirm: Confirmation flag (required for safety)
    
    Returns:
        True if rollback succeeded, False otherwise
    """
    rollback_manager = RollbackManager(database_url)
    return rollback_manager.rollback_to_point(rollback_point_id, confirm)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Rollback procedures for Event Planning Agent')
    parser.add_argument('--db-url', help='Database URL')
    parser.add_argument('--create', help='Create rollback point with description')
    parser.add_argument('--list', action='store_true', help='List available rollback points')
    parser.add_argument('--rollback', help='Rollback to specific point ID')
    parser.add_argument('--rollback-last', action='store_true', help='Rollback last migration')
    parser.add_argument('--validate', help='Validate specific rollback point')
    parser.add_argument('--cleanup', type=int, help='Cleanup old rollback points (keep N most recent)')
    parser.add_argument('--confirm', action='store_true', help='Confirm destructive operations')
    
    args = parser.parse_args()
    
    rollback_manager = RollbackManager(args.db_url)
    
    if args.create:
        point_id = rollback_manager.create_rollback_point(args.create)
        print(f"Created rollback point: {point_id}")
    
    elif args.list:
        points = rollback_manager.list_rollback_points()
        print(json.dumps(points, indent=2, default=str))
    
    elif args.rollback:
        success = rollback_manager.rollback_to_point(args.rollback, args.confirm)
        exit(0 if success else 1)
    
    elif args.rollback_last:
        success = rollback_manager.rollback_last_migration(args.confirm)
        exit(0 if success else 1)
    
    elif args.validate:
        is_valid, errors = rollback_manager.validate_rollback_point(args.validate)
        if not is_valid:
            print("Validation errors:")
            for error in errors:
                print(f"  - {error}")
        exit(0 if is_valid else 1)
    
    elif args.cleanup:
        success = rollback_manager.cleanup_old_rollback_points(args.cleanup)
        exit(0 if success else 1)
    
    else:
        parser.print_help()