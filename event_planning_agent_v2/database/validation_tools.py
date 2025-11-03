"""
Data validation tools for Event Planning Agent v2
Comprehensive validation utilities for ensuring data integrity after migration
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from contextlib import contextmanager
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataValidator:
    """Comprehensive data validation for migrated database"""
    
    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or os.getenv("DATABASE_URL", 
            "postgresql://eventuser:eventpass@localhost:5432/eventdb")
        self.engine = create_engine(self.database_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Validation results
        self.validation_results = {
            'passed': [],
            'failed': [],
            'warnings': []
        }
    
    @contextmanager
    def get_session(self):
        """Get database session with proper cleanup"""
        session = self.SessionLocal()
        try:
            yield session
        finally:
            session.close()
    
    def validate_table_structure(self) -> bool:
        """Validate that all required tables and columns exist"""
        logger.info("🔍 Validating table structure...")
        
        required_tables = {
            'venues': [
                'vendor_id', 'name', 'area_name', 'area_type', 'location_city', 
                'location_full', 'ideal_capacity', 'max_seating_capacity', 
                'rental_cost', 'min_veg_price', 'policies', 'room_count', 
                'room_cost', 'decor_options', 'attributes'
            ],
            'caterers': [
                'vendor_id', 'name', 'location_city', 'location_full', 'veg_only',
                'min_veg_price', 'min_non_veg_price', 'max_guest_capacity', 'attributes'
            ],
            'photographers': [
                'vendor_id', 'name', 'location_city', 'location_full', 
                'photo_package_price', 'video_available', 'attributes'
            ],
            'makeup_artists': [
                'vendor_id', 'name', 'location_city', 'location_full', 
                'bridal_makeup_price', 'on_site_service', 'attributes'
            ],
            'event_plans': [
                'plan_id', 'client_id', 'status', 'plan_data', 'workflow_state',
                'beam_history', 'agent_logs', 'final_blueprint', 'created_at', 'updated_at'
            ],
            'agent_performance': [
                'id', 'plan_id', 'agent_name', 'task_name', 'execution_time_ms',
                'success', 'error_message', 'created_at'
            ],
            'workflow_metrics': [
                'id', 'plan_id', 'total_iterations', 'total_execution_time_ms',
                'combinations_evaluated', 'final_score', 'created_at'
            ]
        }
        
        try:
            inspector = inspect(self.engine)
            existing_tables = inspector.get_table_names()
            
            all_valid = True
            
            for table_name, required_columns in required_tables.items():
                if table_name not in existing_tables:
                    self.validation_results['failed'].append(f"Missing table: {table_name}")
                    all_valid = False
                    continue
                
                # Check columns
                existing_columns = [col['name'] for col in inspector.get_columns(table_name)]
                missing_columns = set(required_columns) - set(existing_columns)
                
                if missing_columns:
                    self.validation_results['failed'].append(
                        f"Table {table_name} missing columns: {list(missing_columns)}"
                    )
                    all_valid = False
                else:
                    self.validation_results['passed'].append(f"Table {table_name} structure valid")
            
            return all_valid
            
        except Exception as e:
            self.validation_results['failed'].append(f"Structure validation error: {e}")
            return False    
   
 def validate_data_integrity(self) -> bool:
        """Validate data integrity constraints"""
        logger.info("🔍 Validating data integrity...")
        
        try:
            with self.get_session() as session:
                all_valid = True
                
                # Check for required fields
                integrity_checks = [
                    ("venues", "name IS NOT NULL AND name != ''", "Venues with missing names"),
                    ("venues", "rental_cost >= 0", "Venues with negative rental costs"),
                    ("venues", "ideal_capacity > 0", "Venues with invalid capacity"),
                    
                    ("caterers", "name IS NOT NULL AND name != ''", "Caterers with missing names"),
                    ("caterers", "min_veg_price >= 0", "Caterers with negative veg prices"),
                    ("caterers", "max_guest_capacity > 0", "Caterers with invalid capacity"),
                    
                    ("photographers", "name IS NOT NULL AND name != ''", "Photographers with missing names"),
                    ("photographers", "photo_package_price >= 0", "Photographers with negative prices"),
                    
                    ("makeup_artists", "name IS NOT NULL AND name != ''", "Makeup artists with missing names"),
                    ("makeup_artists", "bridal_makeup_price >= 0", "Makeup artists with negative prices"),
                ]
                
                for table, condition, description in integrity_checks:
                    try:
                        result = session.execute(text(f"""
                            SELECT COUNT(*) FROM {table} WHERE NOT ({condition})
                        """)).fetchone()
                        
                        invalid_count = result[0] if result else 0
                        
                        if invalid_count > 0:
                            self.validation_results['failed'].append(f"{description}: {invalid_count} records")
                            all_valid = False
                        else:
                            self.validation_results['passed'].append(f"{description}: All valid")
                    
                    except Exception as e:
                        self.validation_results['failed'].append(f"Integrity check failed for {table}: {e}")
                        all_valid = False
                
                return all_valid
                
        except Exception as e:
            self.validation_results['failed'].append(f"Data integrity validation error: {e}")
            return False
    
    def validate_json_fields(self) -> bool:
        """Validate JSON field formats"""
        logger.info("🔍 Validating JSON fields...")
        
        try:
            with self.get_session() as session:
                all_valid = True
                
                json_field_checks = [
                    ("venues", "policies", "Venue policies JSON"),
                    ("venues", "decor_options", "Venue decor options JSON"),
                    ("venues", "attributes", "Venue attributes JSON"),
                    ("caterers", "attributes", "Caterer attributes JSON"),
                    ("photographers", "attributes", "Photographer attributes JSON"),
                    ("makeup_artists", "attributes", "Makeup artist attributes JSON"),
                    ("event_plans", "plan_data", "Event plan data JSON"),
                    ("event_plans", "workflow_state", "Event workflow state JSON"),
                    ("event_plans", "beam_history", "Event beam history JSON"),
                    ("event_plans", "agent_logs", "Event agent logs JSON"),
                ]
                
                for table, column, description in json_field_checks:
                    try:
                        # Check if table exists
                        inspector = inspect(self.engine)
                        if table not in inspector.get_table_names():
                            continue
                        
                        # Test JSON validity
                        result = session.execute(text(f"""
                            SELECT COUNT(*) FROM {table} 
                            WHERE {column} IS NOT NULL 
                            AND NOT ({column}::text ~ '^\\{{.*\\}}$' OR {column}::text ~ '^\\[.*\\]$')
                        """)).fetchone()
                        
                        invalid_count = result[0] if result else 0
                        
                        if invalid_count > 0:
                            self.validation_results['failed'].append(f"{description}: {invalid_count} invalid JSON records")
                            all_valid = False
                        else:
                            self.validation_results['passed'].append(f"{description}: All valid JSON")
                    
                    except Exception as e:
                        self.validation_results['warnings'].append(f"JSON validation skipped for {table}.{column}: {e}")
                
                return all_valid
                
        except Exception as e:
            self.validation_results['failed'].append(f"JSON validation error: {e}")
            return False
    
    def validate_business_logic(self) -> bool:
        """Validate business logic constraints"""
        logger.info("🔍 Validating business logic...")
        
        try:
            with self.get_session() as session:
                all_valid = True
                
                # Business logic checks
                business_checks = [
                    # Venue business logic
                    ("venues", "max_seating_capacity >= ideal_capacity", "Venues where max < ideal capacity"),
                    ("venues", "location_city IS NOT NULL", "Venues without city information"),
                    
                    # Caterer business logic
                    ("caterers", "CASE WHEN veg_only = false THEN min_non_veg_price > 0 ELSE true END", 
                     "Non-veg caterers without non-veg pricing"),
                    
                    # Photographer business logic
                    ("photographers", "location_city IS NOT NULL", "Photographers without city information"),
                    
                    # Makeup artist business logic
                    ("makeup_artists", "location_city IS NOT NULL", "Makeup artists without city information"),
                ]
                
                for table, condition, description in business_checks:
                    try:
                        # Check if table exists
                        inspector = inspect(self.engine)
                        if table not in inspector.get_table_names():
                            continue
                        
                        result = session.execute(text(f"""
                            SELECT COUNT(*) FROM {table} WHERE NOT ({condition})
                        """)).fetchone()
                        
                        invalid_count = result[0] if result else 0
                        
                        if invalid_count > 0:
                            self.validation_results['failed'].append(f"{description}: {invalid_count} records")
                            all_valid = False
                        else:
                            self.validation_results['passed'].append(f"{description}: All valid")
                    
                    except Exception as e:
                        self.validation_results['warnings'].append(f"Business logic check failed for {table}: {e}")
                
                return all_valid
                
        except Exception as e:
            self.validation_results['failed'].append(f"Business logic validation error: {e}")
            return False  
  
    def validate_performance_indexes(self) -> bool:
        """Validate that performance indexes exist"""
        logger.info("🔍 Validating performance indexes...")
        
        try:
            with self.get_session() as session:
                all_valid = True
                
                # Expected indexes
                expected_indexes = [
                    ("venues", "idx_venues_city"),
                    ("venues", "idx_venues_capacity"),
                    ("venues", "idx_venues_cost"),
                    ("caterers", "idx_caterers_city"),
                    ("caterers", "idx_caterers_veg_price"),
                    ("photographers", "idx_photographers_city"),
                    ("photographers", "idx_photographers_price"),
                    ("makeup_artists", "idx_makeup_artists_city"),
                    ("event_plans", "idx_event_plans_status"),
                    ("event_plans", "idx_event_plans_client_id"),
                    ("agent_performance", "idx_agent_performance_plan_id"),
                    ("workflow_metrics", "idx_workflow_metrics_plan_id"),
                ]
                
                # Get existing indexes
                existing_indexes = session.execute(text("""
                    SELECT schemaname, tablename, indexname 
                    FROM pg_indexes 
                    WHERE schemaname = 'public'
                """)).fetchall()
                
                existing_index_names = {idx[2] for idx in existing_indexes}
                
                for table, index_name in expected_indexes:
                    if index_name not in existing_index_names:
                        self.validation_results['warnings'].append(f"Missing performance index: {index_name} on {table}")
                    else:
                        self.validation_results['passed'].append(f"Index exists: {index_name}")
                
                return all_valid
                
        except Exception as e:
            self.validation_results['failed'].append(f"Index validation error: {e}")
            return False
    
    def generate_data_statistics(self) -> Dict[str, Any]:
        """Generate comprehensive data statistics"""
        logger.info("📊 Generating data statistics...")
        
        statistics = {}
        
        try:
            with self.get_session() as session:
                # Table record counts
                tables = ['venues', 'caterers', 'photographers', 'makeup_artists', 'event_plans']
                
                for table in tables:
                    try:
                        # Check if table exists
                        inspector = inspect(self.engine)
                        if table not in inspector.get_table_names():
                            statistics[table] = {'count': 0, 'status': 'table_not_exists'}
                            continue
                        
                        # Get record count
                        result = session.execute(text(f"SELECT COUNT(*) FROM {table}")).fetchone()
                        count = result[0] if result else 0
                        
                        table_stats = {'count': count}
                        
                        # Additional statistics based on table type
                        if table == 'venues':
                            # Venue-specific stats
                            city_dist = session.execute(text("""
                                SELECT location_city, COUNT(*) 
                                FROM venues 
                                GROUP BY location_city 
                                ORDER BY COUNT(*) DESC
                            """)).fetchall()
                            
                            capacity_stats = session.execute(text("""
                                SELECT 
                                    MIN(ideal_capacity) as min_capacity,
                                    MAX(ideal_capacity) as max_capacity,
                                    AVG(ideal_capacity) as avg_capacity
                                FROM venues 
                                WHERE ideal_capacity IS NOT NULL
                            """)).fetchone()
                            
                            table_stats.update({
                                'city_distribution': dict(city_dist),
                                'capacity_stats': dict(capacity_stats._mapping) if capacity_stats else {}
                            })
                        
                        elif table == 'caterers':
                            # Caterer-specific stats
                            veg_stats = session.execute(text("""
                                SELECT veg_only, COUNT(*) 
                                FROM caterers 
                                GROUP BY veg_only
                            """)).fetchall()
                            
                            price_stats = session.execute(text("""
                                SELECT 
                                    MIN(min_veg_price) as min_veg_price,
                                    MAX(min_veg_price) as max_veg_price,
                                    AVG(min_veg_price) as avg_veg_price
                                FROM caterers 
                                WHERE min_veg_price IS NOT NULL AND min_veg_price > 0
                            """)).fetchone()
                            
                            table_stats.update({
                                'veg_distribution': dict(veg_stats),
                                'price_stats': dict(price_stats._mapping) if price_stats else {}
                            })
                        
                        statistics[table] = table_stats
                    
                    except Exception as e:
                        statistics[table] = {'error': str(e)}
                
                # Overall database statistics
                try:
                    db_size = session.execute(text("""
                        SELECT pg_size_pretty(pg_database_size(current_database()))
                    """)).fetchone()
                    
                    statistics['database'] = {
                        'size': db_size[0] if db_size else 'unknown',
                        'validation_timestamp': datetime.now().isoformat()
                    }
                except Exception as e:
                    statistics['database'] = {'error': str(e)}
                
        except Exception as e:
            statistics['error'] = str(e)
        
        return statistics
    
    def run_comprehensive_validation(self) -> Tuple[bool, Dict[str, Any]]:
        """Run all validation checks and return comprehensive results"""
        logger.info("🚀 Running comprehensive validation...")
        
        validation_start = datetime.now()
        
        # Run all validation checks
        validation_checks = [
            ("Table Structure", self.validate_table_structure),
            ("Data Integrity", self.validate_data_integrity),
            ("JSON Fields", self.validate_json_fields),
            ("Business Logic", self.validate_business_logic),
            ("Performance Indexes", self.validate_performance_indexes),
        ]
        
        overall_success = True
        
        for check_name, check_function in validation_checks:
            logger.info(f"Running {check_name} validation...")
            try:
                success = check_function()
                if not success:
                    overall_success = False
                    logger.warning(f"❌ {check_name} validation failed")
                else:
                    logger.info(f"✅ {check_name} validation passed")
            except Exception as e:
                logger.error(f"❌ {check_name} validation error: {e}")
                self.validation_results['failed'].append(f"{check_name} validation error: {e}")
                overall_success = False
        
        # Generate statistics
        statistics = self.generate_data_statistics()
        
        validation_end = datetime.now()
        duration = (validation_end - validation_start).total_seconds()
        
        # Compile final results
        final_results = {
            'overall_success': overall_success,
            'validation_duration_seconds': duration,
            'timestamp': validation_end.isoformat(),
            'results': self.validation_results,
            'statistics': statistics,
            'summary': {
                'passed_checks': len(self.validation_results['passed']),
                'failed_checks': len(self.validation_results['failed']),
                'warnings': len(self.validation_results['warnings'])
            }
        }
        
        if overall_success:
            logger.info(f"✅ Comprehensive validation completed successfully in {duration:.2f} seconds")
        else:
            logger.error(f"❌ Comprehensive validation failed in {duration:.2f} seconds")
        
        return overall_success, final_results


def validate_migrated_data(database_url: Optional[str] = None) -> Tuple[bool, Dict[str, Any]]:
    """
    Run comprehensive validation on migrated data
    
    Args:
        database_url: Database connection URL
    
    Returns:
        Tuple of (success, validation_results)
    """
    validator = DataValidator(database_url)
    return validator.run_comprehensive_validation()


if __name__ == "__main__":
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description='Data validation for Event Planning Agent')
    parser.add_argument('--db-url', help='Database URL')
    parser.add_argument('--output', help='Output file for validation results')
    parser.add_argument('--stats-only', action='store_true', help='Only generate statistics')
    
    args = parser.parse_args()
    
    if args.stats_only:
        validator = DataValidator(args.db_url)
        stats = validator.generate_data_statistics()
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(stats, f, indent=2, default=str)
        else:
            print(json.dumps(stats, indent=2, default=str))
    else:
        success, results = validate_migrated_data(args.db_url)
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2, default=str)
        else:
            print(json.dumps(results, indent=2, default=str))
        
        exit(0 if success else 1)