#!/usr/bin/env python3
"""
Test script for migration utilities
Verifies that all migration components work correctly
"""

import os
import sys
import json
import tempfile
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

def test_data_validation():
    """Test data validation utilities"""
    print("🔍 Testing data validation...")
    
    # Create test JSON data
    test_data = [
        {"name": "Test Venue", "location": "Bangalore", "capacity": 100},
        {"name": "Another Venue", "location": "Mumbai", "capacity": 200}
    ]
    
    # Write to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(test_data, f)
        temp_file = f.name
    
    try:
        from database.data_migration import DataMigrationManager
        
        # Test validation
        migration_manager = DataMigrationManager()
        is_valid, errors = migration_manager.validate_json_data(Path(temp_file))
        
        if is_valid:
            print("   ✅ Data validation test passed")
            return True
        else:
            print(f"   ❌ Data validation test failed: {errors}")
            return False
    
    except Exception as e:
        print(f"   ❌ Data validation test error: {e}")
        return False
    
    finally:
        # Clean up
        if os.path.exists(temp_file):
            os.unlink(temp_file)

def test_city_extraction():
    """Test city extraction logic"""
    print("🏙️ Testing city extraction...")
    
    try:
        from database.data_migration import DataMigrationManager
        
        migration_manager = DataMigrationManager()
        
        test_cases = [
            ("South Bangalore, Bangalore", "Bangalore"),
            ("Kochi, Kerala", "Kochi"),
            ("Hyderabad, Telangana", "Hyderabad"),
            ("Unknown Location", "Bangalore"),  # Default
            ("", "Bangalore"),  # Empty
        ]
        
        all_passed = True
        for location, expected in test_cases:
            result = migration_manager._extract_city_from_location(location)
            if result == expected:
                print(f"   ✅ '{location}' -> '{result}'")
            else:
                print(f"   ❌ '{location}' -> '{result}' (expected '{expected}')")
                all_passed = False
        
        return all_passed
    
    except Exception as e:
        print(f"   ❌ City extraction test error: {e}")
        return False

def test_validation_tools():
    """Test validation tools"""
    print("🔧 Testing validation tools...")
    
    try:
        from database.validation_tools import DataValidator
        
        # This will test basic initialization
        validator = DataValidator()
        
        # Test statistics generation (will work even with empty DB)
        stats = validator.generate_data_statistics()
        
        if isinstance(stats, dict):
            print("   ✅ Validation tools test passed")
            return True
        else:
            print("   ❌ Validation tools test failed")
            return False
    
    except Exception as e:
        print(f"   ❌ Validation tools test error: {e}")
        return False

def test_rollback_procedures():
    """Test rollback procedures"""
    print("🔄 Testing rollback procedures...")
    
    try:
        from database.rollback_procedures import RollbackManager
        
        # Test initialization and basic methods
        rollback_manager = RollbackManager()
        
        # Test listing rollback points (should work even if none exist)
        points = rollback_manager.list_rollback_points()
        
        if isinstance(points, list):
            print(f"   ✅ Rollback procedures test passed ({len(points)} rollback points found)")
            return True
        else:
            print("   ❌ Rollback procedures test failed")
            return False
    
    except Exception as e:
        print(f"   ❌ Rollback procedures test error: {e}")
        return False

def test_migration_orchestrator():
    """Test migration orchestrator"""
    print("🎭 Testing migration orchestrator...")
    
    try:
        from scripts.migrate_data import MigrationOrchestrator
        
        # Test initialization
        orchestrator = MigrationOrchestrator()
        
        if orchestrator.migration_id:
            print(f"   ✅ Migration orchestrator test passed (ID: {orchestrator.migration_id})")
            return True
        else:
            print("   ❌ Migration orchestrator test failed")
            return False
    
    except Exception as e:
        print(f"   ❌ Migration orchestrator test error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Running migration utilities tests...\n")
    
    tests = [
        ("Data Validation", test_data_validation),
        ("City Extraction", test_city_extraction),
        ("Validation Tools", test_validation_tools),
        ("Rollback Procedures", test_rollback_procedures),
        ("Migration Orchestrator", test_migration_orchestrator),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"   ❌ Test failed with exception: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All tests passed!")
        return True
    else:
        print("❌ Some tests failed!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)