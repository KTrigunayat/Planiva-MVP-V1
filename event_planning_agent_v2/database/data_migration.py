"""
Data migration utilities for migrating existing vendor data to enhanced schema
Handles migration from Event_planning_agent to event_planning_agent_v2
"""

import json
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from contextlib import contextmanager
import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataMigrationManager:
    """Manages data migration from old to new schema with validation and rollback"""
    
    def __init__(self, old_db_url: Optional[str] = None, new_db_url: Optional[str] = None):
        # Database connections
        self.old_db_url = old_db_url or os.getenv("OLD_DATABASE_URL")
        self.new_db_url = new_db_url or os.getenv("DATABASE_URL", 
            "postgresql://eventuser:eventpass@localhost:5432/eventdb")
        
        # Setup new database connection
        self.new_engine = create_engine(self.new_db_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.new_engine)
        
        # Data paths
        self.data_dir = Path("Data_JSON")
        self.backup_dir = Path("migration_backups")
        self.backup_dir.mkdir(exist_ok=True)
        
        # Migration tracking
        self.migration_id = str(uuid.uuid4())
        self.migration_log = []
    
    @contextmanager
    def get_new_session(self):
        """Get new database session with proper cleanup"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close() 
   
    def get_old_db_connection(self):
        """Get connection to old database if available"""
        if not self.old_db_url:
            return None
        try:
            return psycopg2.connect(self.old_db_url, cursor_factory=RealDictCursor)
        except Exception as e:
            logger.warning(f"Could not connect to old database: {e}")
            return None
    
    def create_backup(self, table_name: str) -> str:
        """Create backup of existing table data"""
        backup_file = self.backup_dir / f"{table_name}_{self.migration_id}.json"
        
        try:
            with self.get_new_session() as session:
                # Check if table exists
                inspector = inspect(self.new_engine)
                if table_name not in inspector.get_table_names():
                    logger.info(f"Table {table_name} does not exist, skipping backup")
                    return str(backup_file)
                
                # Export existing data
                result = session.execute(text(f"SELECT * FROM {table_name}")).fetchall()
                
                # Convert to JSON serializable format
                backup_data = []
                for row in result:
                    row_dict = dict(row._mapping) if hasattr(row, '_mapping') else dict(row)
                    # Convert UUID and datetime objects to strings
                    for key, value in row_dict.items():
                        if isinstance(value, uuid.UUID):
                            row_dict[key] = str(value)
                        elif isinstance(value, datetime):
                            row_dict[key] = value.isoformat()
                    backup_data.append(row_dict)
                
                # Save backup
                with open(backup_file, 'w', encoding='utf-8') as f:
                    json.dump(backup_data, f, indent=2, default=str)
                
                logger.info(f"✅ Backed up {len(backup_data)} records from {table_name} to {backup_file}")
                self.migration_log.append(f"Backup created: {backup_file}")
                
        except Exception as e:
            logger.error(f"❌ Failed to backup {table_name}: {e}")
            raise
        
        return str(backup_file)
    
    def validate_json_data(self, file_path: Path) -> Tuple[bool, List[str]]:
        """Validate JSON data file structure"""
        errors = []
        
        if not file_path.exists():
            errors.append(f"File does not exist: {file_path}")
            return False, errors
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                errors.append("Data must be a list of objects")
                return False, errors
            
            if len(data) == 0:
                errors.append("Data file is empty")
                return False, errors
            
            # Validate first few records for structure
            for i, record in enumerate(data[:5]):
                if not isinstance(record, dict):
                    errors.append(f"Record {i} is not a dictionary")
                
                if 'name' not in record:
                    errors.append(f"Record {i} missing required 'name' field")
            
            logger.info(f"✅ Validated {len(data)} records in {file_path}")
            
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON format: {e}")
        except Exception as e:
            errors.append(f"Validation error: {e}")
        
        return len(errors) == 0, errors    
    d
ef migrate_venues_data(self) -> bool:
        """Migrate venues data from JSON to enhanced schema"""
        logger.info("🏢 Migrating venues data...")
        
        # Validate source data
        venues_file = self.data_dir / "correct_venue_data.json"
        is_valid, errors = self.validate_json_data(venues_file)
        if not is_valid:
            logger.error(f"❌ Venues data validation failed: {errors}")
            return False
        
        # Create backup
        backup_file = self.create_backup("venues")
        
        try:
            with open(venues_file, 'r', encoding='utf-8') as f:
                venues_data = json.load(f)
            
            with self.get_new_session() as session:
                # Clear existing data
                session.execute(text("DELETE FROM venues"))
                
                migrated_count = 0
                for venue in venues_data:
                    try:
                        # Extract city from location
                        location_full = venue.get('location', '')
                        location_city = self._extract_city_from_location(location_full)
                        
                        # Calculate min veg price estimate
                        rental_cost = venue.get('rental_cost', 0)
                        min_veg_price = max(rental_cost // 100, 500) if rental_cost > 0 else 500
                        
                        # Prepare attributes
                        attributes = {
                            'about': f"Premium venue in {location_city} with {venue.get('area_type', 'mixed')} space",
                            'area_type': venue.get('area_type', 'mixed'),
                            'policies': venue.get('policies', {}),
                            'decor_options': venue.get('decor_cost', [])
                        }
                        
                        # Insert venue record
                        session.execute(text("""
                            INSERT INTO venues (
                                vendor_id, name, area_name, area_type, location_city, location_full,
                                ideal_capacity, max_seating_capacity, rental_cost, min_veg_price,
                                policies, room_count, room_cost, decor_options, attributes
                            ) VALUES (
                                gen_random_uuid(), :name, :area_name, :area_type, :location_city, :location_full,
                                :ideal_capacity, :max_seating_capacity, :rental_cost, :min_veg_price,
                                :policies, :room_count, :room_cost, :decor_options, :attributes
                            )
                        """), {
                            'name': venue['name'],
                            'area_name': venue.get('area_name'),
                            'area_type': venue.get('area_type', 'mixed'),
                            'location_city': location_city,
                            'location_full': location_full,
                            'ideal_capacity': venue.get('ideal_capacity'),
                            'max_seating_capacity': venue.get('max_capacity', venue.get('ideal_capacity')),
                            'rental_cost': rental_cost,
                            'min_veg_price': min_veg_price,
                            'policies': json.dumps(venue.get('policies', {})),
                            'room_count': venue.get('room_count'),
                            'room_cost': venue.get('room_cost'),
                            'decor_options': json.dumps(venue.get('decor_cost', [])),
                            'attributes': json.dumps(attributes)
                        })
                        
                        migrated_count += 1
                        
                    except Exception as e:
                        logger.error(f"❌ Failed to migrate venue '{venue.get('name', 'unknown')}': {e}")
                        continue
                
                logger.info(f"✅ Migrated {migrated_count}/{len(venues_data)} venues")
                self.migration_log.append(f"Venues migrated: {migrated_count}/{len(venues_data)}")
                
        except Exception as e:
            logger.error(f"❌ Venues migration failed: {e}")
            return False
        
        return True    

    def migrate_caterers_data(self) -> bool:
        """Migrate caterers data from JSON to enhanced schema"""
        logger.info("🍽️ Migrating caterers data...")
        
        # Validate source data
        caterers_file = self.data_dir / "correct_caterers_data.json"
        is_valid, errors = self.validate_json_data(caterers_file)
        if not is_valid:
            logger.error(f"❌ Caterers data validation failed: {errors}")
            return False
        
        # Create backup
        backup_file = self.create_backup("caterers")
        
        try:
            with open(caterers_file, 'r', encoding='utf-8') as f:
                caterers_data = json.load(f)
            
            with self.get_new_session() as session:
                # Clear existing data
                session.execute(text("DELETE FROM caterers"))
                
                migrated_count = 0
                for caterer in caterers_data:
                    try:
                        # Extract city from location
                        location_full = caterer.get('location', '')
                        location_city = self._extract_city_from_location(location_full)
                        
                        # Prepare attributes
                        attributes = {
                            'about': caterer.get('about', f"Professional catering service in {location_city}"),
                            'cuisines': caterer.get('cuisines', []),
                            'specialties': caterer.get('specialties', [])
                        }
                        
                        # Insert caterer record
                        session.execute(text("""
                            INSERT INTO caterers (
                                vendor_id, name, location_city, location_full, veg_only,
                                min_veg_price, min_non_veg_price, max_guest_capacity, attributes
                            ) VALUES (
                                gen_random_uuid(), :name, :location_city, :location_full, :veg_only,
                                :min_veg_price, :min_non_veg_price, :max_guest_capacity, :attributes
                            )
                        """), {
                            'name': caterer['name'],
                            'location_city': location_city,
                            'location_full': location_full,
                            'veg_only': caterer.get('veg_only', False),
                            'min_veg_price': caterer.get('per_plate_price_veg', 0),
                            'min_non_veg_price': caterer.get('per_plate_price_non_veg', 0),
                            'max_guest_capacity': caterer.get('max_guest_capacity', 10000),
                            'attributes': json.dumps(attributes)
                        })
                        
                        migrated_count += 1
                        
                    except Exception as e:
                        logger.error(f"❌ Failed to migrate caterer '{caterer.get('name', 'unknown')}': {e}")
                        continue
                
                logger.info(f"✅ Migrated {migrated_count}/{len(caterers_data)} caterers")
                self.migration_log.append(f"Caterers migrated: {migrated_count}/{len(caterers_data)}")
                
        except Exception as e:
            logger.error(f"❌ Caterers migration failed: {e}")
            return False
        
        return True
    
    def migrate_photographers_data(self) -> bool:
        """Migrate photographers data from JSON to enhanced schema"""
        logger.info("📸 Migrating photographers data...")
        
        # Validate source data
        photographers_file = self.data_dir / "photographers_data.json"
        is_valid, errors = self.validate_json_data(photographers_file)
        if not is_valid:
            logger.error(f"❌ Photographers data validation failed: {errors}")
            return False
        
        # Create backup
        backup_file = self.create_backup("photographers")
        
        try:
            with open(photographers_file, 'r', encoding='utf-8') as f:
                photographers_data = json.load(f)
            
            with self.get_new_session() as session:
                # Clear existing data
                session.execute(text("DELETE FROM photographers"))
                
                migrated_count = 0
                for photographer in photographers_data:
                    try:
                        # Extract city from location
                        location_full = photographer.get('location', '')
                        location_city = self._extract_city_from_location(location_full)
                        
                        # Check for video services
                        services = photographer.get('services', [])
                        video_available = any('video' in service.lower() or 'cinematography' in service.lower() 
                                            for service in services)
                        
                        # Prepare attributes
                        attributes = {
                            'about': f"Professional photographer in {location_city}",
                            'services': services,
                            'styles': photographer.get('styles', ['candid', 'traditional']),
                            'equipment': photographer.get('equipment', [])
                        }
                        
                        # Insert photographer record
                        session.execute(text("""
                            INSERT INTO photographers (
                                vendor_id, name, location_city, location_full, photo_package_price,
                                video_available, attributes
                            ) VALUES (
                                gen_random_uuid(), :name, :location_city, :location_full, :photo_package_price,
                                :video_available, :attributes
                            )
                        """), {
                            'name': photographer['name'],
                            'location_city': location_city,
                            'location_full': location_full,
                            'photo_package_price': photographer.get('price', 0),
                            'video_available': video_available,
                            'attributes': json.dumps(attributes)
                        })
                        
                        migrated_count += 1
                        
                    except Exception as e:
                        logger.error(f"❌ Failed to migrate photographer '{photographer.get('name', 'unknown')}': {e}")
                        continue
                
                logger.info(f"✅ Migrated {migrated_count}/{len(photographers_data)} photographers")
                self.migration_log.append(f"Photographers migrated: {migrated_count}/{len(photographers_data)}")
                
        except Exception as e:
            logger.error(f"❌ Photographers migration failed: {e}")
            return False
        
        return True    

    def migrate_makeup_artists_data(self) -> bool:
        """Migrate makeup artists data from JSON to enhanced schema"""
        logger.info("💄 Migrating makeup artists data...")
        
        # Validate source data
        makeup_file = self.data_dir / "Makeup_artist.json"
        is_valid, errors = self.validate_json_data(makeup_file)
        if not is_valid:
            logger.error(f"❌ Makeup artists data validation failed: {errors}")
            return False
        
        # Create backup
        backup_file = self.create_backup("makeup_artists")
        
        try:
            with open(makeup_file, 'r', encoding='utf-8') as f:
                makeup_data = json.load(f)
            
            with self.get_new_session() as session:
                # Clear existing data
                session.execute(text("DELETE FROM makeup_artists"))
                
                migrated_count = 0
                for artist in makeup_data:
                    try:
                        # Extract city from location
                        location_full = artist.get('location', '')
                        location_city = self._extract_city_from_location(location_full)
                        
                        # Check for on-site services
                        services = artist.get('services', [])
                        on_site = any('travels' in service.lower() or 'on-site' in service.lower() 
                                     for service in services)
                        
                        # Prepare attributes
                        attributes = {
                            'about': f"Professional makeup artist in {location_city}",
                            'services': services,
                            'specialties': artist.get('specialties', ['bridal', 'party']),
                            'products_used': artist.get('products', [])
                        }
                        
                        # Insert makeup artist record
                        session.execute(text("""
                            INSERT INTO makeup_artists (
                                vendor_id, name, location_city, location_full, bridal_makeup_price,
                                on_site_service, attributes
                            ) VALUES (
                                gen_random_uuid(), :name, :location_city, :location_full, :bridal_makeup_price,
                                :on_site_service, :attributes
                            )
                        """), {
                            'name': artist['name'],
                            'location_city': location_city,
                            'location_full': location_full,
                            'bridal_makeup_price': artist.get('price', 0),
                            'on_site_service': on_site,
                            'attributes': json.dumps(attributes)
                        })
                        
                        migrated_count += 1
                        
                    except Exception as e:
                        logger.error(f"❌ Failed to migrate makeup artist '{artist.get('name', 'unknown')}': {e}")
                        continue
                
                logger.info(f"✅ Migrated {migrated_count}/{len(makeup_data)} makeup artists")
                self.migration_log.append(f"Makeup artists migrated: {migrated_count}/{len(makeup_data)}")
                
        except Exception as e:
            logger.error(f"❌ Makeup artists migration failed: {e}")
            return False
        
        return True
    
    def _extract_city_from_location(self, location: str) -> str:
        """Extract city name from location string"""
        if not location:
            return "Bangalore"
        
        location_lower = location.lower()
        
        # Common patterns for cities
        if "bangalore" in location_lower or "bengaluru" in location_lower:
            return "Bangalore"
        elif "kochi" in location_lower:
            return "Kochi"
        elif "hyderabad" in location_lower:
            return "Hyderabad"
        elif "mumbai" in location_lower:
            return "Mumbai"
        elif "delhi" in location_lower:
            return "Delhi"
        elif "chennai" in location_lower:
            return "Chennai"
        elif "pune" in location_lower:
            return "Pune"
        else:
            # Default to Bangalore if unclear
            return "Bangalore"    
    d
ef validate_migration_integrity(self) -> Tuple[bool, List[str]]:
        """Validate data integrity after migration"""
        logger.info("🔍 Validating migration integrity...")
        
        validation_errors = []
        
        try:
            with self.get_new_session() as session:
                # Check record counts
                tables = ['venues', 'caterers', 'photographers', 'makeup_artists']
                
                for table in tables:
                    try:
                        result = session.execute(text(f"SELECT COUNT(*) FROM {table}")).fetchone()
                        count = result[0] if result else 0
                        
                        if count == 0:
                            validation_errors.append(f"Table {table} is empty after migration")
                        else:
                            logger.info(f"✅ {table}: {count} records")
                        
                        # Check for required fields
                        null_names = session.execute(text(f"SELECT COUNT(*) FROM {table} WHERE name IS NULL OR name = ''")).fetchone()
                        if null_names and null_names[0] > 0:
                            validation_errors.append(f"Table {table} has {null_names[0]} records with missing names")
                        
                        # Check for valid JSON in attributes column
                        if table in ['venues', 'caterers', 'photographers', 'makeup_artists']:
                            invalid_json = session.execute(text(f"""
                                SELECT COUNT(*) FROM {table} 
                                WHERE attributes IS NOT NULL AND NOT (attributes::text ~ '^\\{{.*\\}}$')
                            """)).fetchone()
                            if invalid_json and invalid_json[0] > 0:
                                validation_errors.append(f"Table {table} has {invalid_json[0]} records with invalid JSON attributes")
                    
                    except Exception as e:
                        validation_errors.append(f"Failed to validate table {table}: {e}")
                
                # Check referential integrity for event_plans if it has data
                try:
                    event_plans_count = session.execute(text("SELECT COUNT(*) FROM event_plans")).fetchone()
                    if event_plans_count and event_plans_count[0] > 0:
                        logger.info(f"✅ event_plans: {event_plans_count[0]} records")
                except Exception:
                    # event_plans table might not exist yet
                    pass
                
        except Exception as e:
            validation_errors.append(f"Database connection error during validation: {e}")
        
        is_valid = len(validation_errors) == 0
        
        if is_valid:
            logger.info("✅ Migration integrity validation passed")
        else:
            logger.error(f"❌ Migration integrity validation failed: {validation_errors}")
        
        return is_valid, validation_errors
    
    def rollback_migration(self, backup_files: List[str]) -> bool:
        """Rollback migration using backup files"""
        logger.info("🔄 Rolling back migration...")
        
        try:
            with self.get_new_session() as session:
                for backup_file in backup_files:
                    if not os.path.exists(backup_file):
                        logger.warning(f"Backup file not found: {backup_file}")
                        continue
                    
                    # Extract table name from backup file
                    filename = os.path.basename(backup_file)
                    table_name = filename.split('_')[0]
                    
                    try:
                        with open(backup_file, 'r', encoding='utf-8') as f:
                            backup_data = json.load(f)
                        
                        # Clear current data
                        session.execute(text(f"DELETE FROM {table_name}"))
                        
                        # Restore backup data
                        for record in backup_data:
                            columns = list(record.keys())
                            values = list(record.values())
                            placeholders = ', '.join([f':{col}' for col in columns])
                            
                            session.execute(text(f"""
                                INSERT INTO {table_name} ({', '.join(columns)})
                                VALUES ({placeholders})
                            """), record)
                        
                        logger.info(f"✅ Restored {len(backup_data)} records to {table_name}")
                    
                    except Exception as e:
                        logger.error(f"❌ Failed to restore {table_name}: {e}")
                        return False
            
            logger.info("✅ Migration rollback completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Rollback failed: {e}")
            return False
    
    def run_full_migration(self) -> bool:
        """Run complete data migration with validation and backup"""
        logger.info("🚀 Starting full data migration...")
        
        migration_start = datetime.now()
        backup_files = []
        
        try:
            # Step 1: Migrate all vendor data
            migration_steps = [
                ("venues", self.migrate_venues_data),
                ("caterers", self.migrate_caterers_data),
                ("photographers", self.migrate_photographers_data),
                ("makeup_artists", self.migrate_makeup_artists_data)
            ]
            
            for table_name, migration_func in migration_steps:
                logger.info(f"📋 Migrating {table_name}...")
                if not migration_func():
                    logger.error(f"❌ Migration failed for {table_name}")
                    return False
            
            # Step 2: Validate migration integrity
            is_valid, errors = self.validate_migration_integrity()
            if not is_valid:
                logger.error(f"❌ Migration validation failed: {errors}")
                return False
            
            # Step 3: Log migration completion
            migration_end = datetime.now()
            duration = (migration_end - migration_start).total_seconds()
            
            self.migration_log.append(f"Migration completed in {duration:.2f} seconds")
            
            # Save migration log
            log_file = self.backup_dir / f"migration_log_{self.migration_id}.json"
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'migration_id': self.migration_id,
                    'start_time': migration_start.isoformat(),
                    'end_time': migration_end.isoformat(),
                    'duration_seconds': duration,
                    'log': self.migration_log
                }, f, indent=2)
            
            logger.info(f"✅ Full migration completed successfully in {duration:.2f} seconds")
            logger.info(f"📄 Migration log saved to: {log_file}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Full migration failed: {e}")
            return False


def run_data_migration(old_db_url: Optional[str] = None, new_db_url: Optional[str] = None) -> bool:
    """
    Run complete data migration from old to new schema
    
    Args:
        old_db_url: Connection URL for old database (optional)
        new_db_url: Connection URL for new database
    
    Returns:
        True if migration succeeded, False otherwise
    """
    migration_manager = DataMigrationManager(old_db_url, new_db_url)
    return migration_manager.run_full_migration()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Data migration for Event Planning Agent')
    parser.add_argument('--old-db', help='Old database URL')
    parser.add_argument('--new-db', help='New database URL')
    parser.add_argument('--validate-only', action='store_true', help='Only validate existing data')
    
    args = parser.parse_args()
    
    if args.validate_only:
        migration_manager = DataMigrationManager(args.old_db, args.new_db)
        is_valid, errors = migration_manager.validate_migration_integrity()
        exit(0 if is_valid else 1)
    else:
        success = run_data_migration(args.old_db, args.new_db)
        exit(0 if success else 1)