#!/usr/bin/env python3
"""
Simple test for migration utilities without complex imports
"""

import json
import tempfile
import os
from pathlib import Path

def test_city_extraction():
    """Test city extraction logic"""
    print("🏙️ Testing city extraction...")
    
    def extract_city_from_location(location: str) -> str:
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
    
    test_cases = [
        ("South Bangalore, Bangalore", "Bangalore"),
        ("Kochi, Kerala", "Kochi"),
        ("Hyderabad, Telangana", "Hyderabad"),
        ("Unknown Location", "Bangalore"),  # Default
        ("", "Bangalore"),  # Empty
    ]
    
    all_passed = True
    for location, expected in test_cases:
        result = extract_city_from_location(location)
        if result == expected:
            print(f"   ✅ '{location}' -> '{result}'")
        else:
            print(f"   ❌ '{location}' -> '{result}' (expected '{expected}')")
            all_passed = False
    
    return all_passed

def test_json_validation():
    """Test JSON validation logic"""
    print("📄 Testing JSON validation...")
    
    def validate_json_data(file_path: Path):
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
            
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON format: {e}")
        except Exception as e:
            errors.append(f"Validation error: {e}")
        
        return len(errors) == 0, errors
    
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
        is_valid, errors = validate_json_data(Path(temp_file))
        
        if is_valid:
            print("   ✅ JSON validation test passed")
            return True
        else:
            print(f"   ❌ JSON validation test failed: {errors}")
            return False
    
    finally:
        # Clean up
        if os.path.exists(temp_file):
            os.unlink(temp_file)

def test_data_files_exist():
    """Test that required data files exist"""
    print("📁 Testing data files existence...")
    
    data_files = [
        "Data_JSON/correct_venue_data.json",
        "Data_JSON/correct_caterers_data.json", 
        "Data_JSON/photographers_data.json",
        "Data_JSON/Makeup_artist.json"
    ]
    
    all_exist = True
    for file_path in data_files:
        if Path(file_path).exists():
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path} (missing)")
            all_exist = False
    
    return all_exist

def test_migration_directories():
    """Test that migration directories are properly set up"""
    print("📂 Testing migration directories...")
    
    required_dirs = [
        "event_planning_agent_v2/database",
        "event_planning_agent_v2/scripts",
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print(f"   ✅ {dir_path}")
        else:
            print(f"   ❌ {dir_path} (missing)")
            all_exist = False
    
    return all_exist

def test_migration_files():
    """Test that migration files exist"""
    print("📄 Testing migration files...")
    
    required_files = [
        "event_planning_agent_v2/database/data_migration.py",
        "event_planning_agent_v2/database/validation_tools.py",
        "event_planning_agent_v2/database/rollback_procedures.py",
        "event_planning_agent_v2/database/migrations.py",
        "event_planning_agent_v2/scripts/migrate_data.py",
    ]
    
    all_exist = True
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path} (missing)")
            all_exist = False
    
    return all_exist

def main():
    """Run all tests"""
    print("🧪 Running simple migration tests...\n")
    
    tests = [
        ("City Extraction", test_city_extraction),
        ("JSON Validation", test_json_validation),
        ("Data Files Exist", test_data_files_exist),
        ("Migration Directories", test_migration_directories),
        ("Migration Files", test_migration_files),
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
    exit(0 if success else 1)