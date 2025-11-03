# Data Migration Utilities

This directory contains comprehensive data migration utilities for Event Planning Agent v2. These tools handle the migration from the original Event_planning_agent to the modernized event_planning_agent_v2 with enhanced schema and capabilities.

## Overview

The migration system provides:
- **Safe data migration** with backup and rollback capabilities
- **Comprehensive validation** to ensure data integrity
- **Schema migrations** for database structure updates
- **Rollback procedures** for safe deployment

## Components

### 1. Schema Migrations (`migrations.py`)
Handles database schema changes and version management.

```bash
# Run all pending migrations
python -m database.migrations

# Check current schema version
python -m database.migrations --version

# Show migration history
python -m database.migrations --history
```

### 2. Data Migration (`data_migration.py`)
Migrates vendor data from JSON files to the enhanced database schema.

```bash
# Run complete data migration
python -m database.data_migration

# Validate data only
python -m database.data_migration --validate-only
```

**Features:**
- Migrates venues, caterers, photographers, and makeup artists
- Preserves all existing data while enhancing schema
- Validates data integrity before and after migration
- Creates automatic backups

### 3. Validation Tools (`validation_tools.py`)
Comprehensive validation suite for migrated data.

```bash
# Run full validation
python -m database.validation_tools

# Generate statistics only
python -m database.validation_tools --stats-only

# Save results to file
python -m database.validation_tools --output validation_results.json
```

**Validation Checks:**
- Table structure validation
- Data integrity constraints
- JSON field format validation
- Business logic validation
- Performance index validation

### 4. Rollback Procedures (`rollback_procedures.py`)
Safe rollback capabilities for migration operations.

```bash
# Create rollback point
python -m database.rollback_procedures --create "Before major update"

# List available rollback points
python -m database.rollback_procedures --list

# Rollback to specific point (requires confirmation)
python -m database.rollback_procedures --rollback POINT_ID --confirm

# Validate rollback point
python -m database.rollback_procedures --validate POINT_ID
```

## Migration Process

### Complete Migration
Use the orchestration script for a full migration:

```bash
# Run complete migration with safety backup
python scripts/migrate_data.py

# Skip safety backup (faster, but less safe)
python scripts/migrate_data.py --skip-backup

# Run only specific parts
python scripts/migrate_data.py --schema-only
python scripts/migrate_data.py --data-only
python scripts/migrate_data.py --validate-only
```

### Step-by-Step Migration

1. **Pre-migration Setup**
   ```bash
   # Ensure database is running
   # Verify data files exist in Data_JSON/
   # Create backup of current database (optional)
   ```

2. **Run Schema Migrations**
   ```bash
   python -m database.migrations
   ```

3. **Create Safety Rollback Point**
   ```bash
   python -m database.rollback_procedures --create "Pre-data-migration"
   ```

4. **Run Data Migration**
   ```bash
   python -m database.data_migration
   ```

5. **Validate Results**
   ```bash
   python -m database.validation_tools
   ```

## Data Mapping

### Venues
- **Source**: `Data_JSON/correct_venue_data.json`
- **Target**: `venues` table
- **Enhancements**:
  - Added `vendor_id` UUID primary key
  - Enhanced location parsing (city extraction)
  - Structured attributes in JSONB format
  - Added performance indexes

### Caterers
- **Source**: `Data_JSON/correct_caterers_data.json`
- **Target**: `caterers` table
- **Enhancements**:
  - Added `vendor_id` UUID primary key
  - Preserved pricing structure
  - Enhanced attributes with cuisine information
  - Added capacity constraints

### Photographers
- **Source**: `Data_JSON/photographers_data.json`
- **Target**: `photographers` table
- **Enhancements**:
  - Added `vendor_id` UUID primary key
  - Video availability detection
  - Service categorization
  - Enhanced metadata

### Makeup Artists
- **Source**: `Data_JSON/Makeup_artist.json`
- **Target**: `makeup_artists` table
- **Enhancements**:
  - Added `vendor_id` UUID primary key
  - On-site service detection
  - Specialty categorization
  - Enhanced service metadata

## Safety Features

### Automatic Backups
- All migration operations create automatic backups
- Backups stored in `migration_backups/` directory
- Full table data exported as JSON
- Schema structure preserved

### Rollback Points
- Create named rollback points before major operations
- Full database state capture
- Validated rollback integrity
- Safe restoration procedures

### Validation
- Pre-migration data validation
- Post-migration integrity checks
- Business logic validation
- Performance optimization verification

## Configuration

### Environment Variables
```bash
# Database connection
DATABASE_URL=postgresql://user:pass@localhost:5432/eventdb

# Optional: Old database for direct migration
OLD_DATABASE_URL=postgresql://user:pass@localhost:5432/old_eventdb

# Migration settings
MIGRATION_BACKUP_DIR=migration_backups
MIGRATION_LOG_LEVEL=INFO
```

### Database Requirements
- PostgreSQL 12+ with UUID extension
- JSONB support for enhanced attributes
- Sufficient disk space for backups
- Connection pooling recommended

## Troubleshooting

### Common Issues

1. **Connection Errors**
   ```bash
   # Check database connectivity
   psql $DATABASE_URL -c "SELECT 1"
   
   # Verify credentials and host
   ```

2. **Missing Data Files**
   ```bash
   # Verify data files exist
   ls -la Data_JSON/
   
   # Check file permissions
   ```

3. **Migration Failures**
   ```bash
   # Check migration logs
   tail -f migration.log
   
   # Validate rollback points
   python -m database.rollback_procedures --list
   ```

4. **Validation Errors**
   ```bash
   # Run detailed validation
   python -m database.validation_tools --output validation_report.json
   
   # Check specific table issues
   ```

### Recovery Procedures

1. **Rollback Failed Migration**
   ```bash
   # List available rollback points
   python -m database.rollback_procedures --list
   
   # Rollback to safe point
   python -m database.rollback_procedures --rollback POINT_ID --confirm
   ```

2. **Data Corruption**
   ```bash
   # Validate data integrity
   python -m database.validation_tools
   
   # Restore from backup if needed
   ```

3. **Performance Issues**
   ```bash
   # Check index creation
   python -m database.validation_tools
   
   # Rebuild indexes if needed
   ```

## Testing

### Unit Tests
```bash
# Run simple migration tests
python test_migration_simple.py

# Test individual components
python -m database.data_migration --validate-only
```

### Integration Tests
```bash
# Full migration test (use test database)
DATABASE_URL=postgresql://test:test@localhost:5432/testdb python scripts/migrate_data.py
```

## Monitoring

### Migration Logs
- All operations logged to `migration.log`
- Structured JSON logs for parsing
- Error details and stack traces
- Performance metrics

### Migration Reports
- Detailed migration reports in JSON format
- Success/failure status
- Timing information
- Rollback point references

### Health Checks
```bash
# Database health
python -c "from database.validation_tools import DataValidator; print(DataValidator().generate_data_statistics())"

# Migration status
python -m database.migrations --history
```

## Best Practices

1. **Always create rollback points** before major operations
2. **Validate data** before and after migration
3. **Monitor disk space** for backup storage
4. **Test migrations** on non-production data first
5. **Keep migration logs** for troubleshooting
6. **Clean up old backups** periodically
7. **Document custom changes** for future reference

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review migration logs for error details
3. Validate rollback points are available
4. Test on a copy of the data first
5. Create detailed issue reports with logs