#!/usr/bin/env python3
"""
Simple test script to verify form functionality
"""
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_form_imports():
    """Test that all form components can be imported"""
    try:
        from components.forms import EventPlanningForm
        from pages.create_plan import CreatePlanPage
        from utils.validators import EventPlanValidator
        from utils.helpers import save_form_data_to_session, format_form_summary
        print("✅ All form imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_form_validation():
    """Test form validation functionality"""
    try:
        from utils.validators import EventPlanValidator
        
        # Test basic info validation
        from datetime import date, timedelta
        future_date = (date.today() + timedelta(days=30)).isoformat()
        
        valid_data = {
            'client_name': 'John Doe',
            'event_type': 'Wedding',
            'event_date': future_date,
            'location': 'New York'
        }
        
        errors = EventPlanValidator.validate_basic_info(valid_data)
        if not errors:
            print("✅ Basic info validation working")
        else:
            print(f"❌ Basic info validation failed: {errors}")
            return False
        
        # Test guest info validation
        guest_data = {
            'total_guests': 100
        }
        
        errors = EventPlanValidator.validate_guest_info(guest_data)
        if not errors:
            print("✅ Guest info validation working")
        else:
            print(f"❌ Guest info validation failed: {errors}")
            return False
        
        # Test budget validation
        budget_data = {
            'total_budget': 15000
        }
        
        errors = EventPlanValidator.validate_budget_info(budget_data)
        if not errors:
            print("✅ Budget validation working")
        else:
            print(f"❌ Budget validation failed: {errors}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Validation test error: {e}")
        return False

def test_form_helpers():
    """Test form helper functions"""
    try:
        from utils.helpers import format_form_summary, export_form_to_json, get_form_completion_percentage
        
        test_data = {
            'client_name': 'Test Client',
            'event_type': 'Wedding',
            'total_guests': 100,
            'total_budget': 15000
        }
        
        # Test summary formatting
        summary = format_form_summary(test_data)
        if summary and 'Test Client' in summary:
            print("✅ Form summary formatting working")
        else:
            print("❌ Form summary formatting failed")
            return False
        
        # Test JSON export
        json_export = export_form_to_json(test_data)
        if json_export and 'Test Client' in json_export:
            print("✅ JSON export working")
        else:
            print("❌ JSON export failed")
            return False
        
        # Test completion percentage
        completion = get_form_completion_percentage(test_data)
        if 0 <= completion <= 100:
            print(f"✅ Form completion calculation working: {completion}%")
        else:
            print("❌ Form completion calculation failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Helper test error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Event Planning Form Implementation")
    print("=" * 50)
    
    tests = [
        ("Form Imports", test_form_imports),
        ("Form Validation", test_form_validation),
        ("Form Helpers", test_form_helpers)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Testing {test_name}...")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} failed")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Form implementation is working correctly.")
        return True
    else:
        print("⚠️ Some tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)