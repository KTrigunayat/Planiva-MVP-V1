#!/usr/bin/env python3
"""
Test script to verify navigation structure and page routing
"""
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_navigation_structure():
    """Test that navigation structure is properly defined"""
    print("🧪 Testing Navigation Structure...")
    print("=" * 60)
    
    try:
        from app import EventPlanningApp
        
        # Create app instance
        app = EventPlanningApp()
        
        # Test main pages
        print("\n📌 Main Pages:")
        for page_key, page_info in app.main_pages.items():
            print(f"  ✓ {page_info['title']}")
            print(f"    - Key: {page_key}")
            print(f"    - Description: {page_info['description']}")
            print(f"    - Requires Plan: {page_info.get('requires_plan', False)}")
        
        # Test task pages
        print("\n📋 Task Management Pages:")
        for page_key, page_info in app.task_pages.items():
            print(f"  ✓ {page_info['title']}")
            print(f"    - Key: {page_key}")
            print(f"    - Description: {page_info['description']}")
            print(f"    - Requires Plan: {page_info.get('requires_plan', False)}")
            print(f"    - Requires Tasks: {page_info.get('requires_tasks', False)}")
        
        # Test CRM pages
        print("\n💬 CRM Communication Pages:")
        for page_key, page_info in app.crm_pages.items():
            print(f"  ✓ {page_info['title']}")
            print(f"    - Key: {page_key}")
            print(f"    - Description: {page_info['description']}")
            print(f"    - Requires Plan: {page_info.get('requires_plan', False)}")
            print(f"    - Requires CRM: {page_info.get('requires_crm', False)}")
        
        # Test all pages combined
        print(f"\n📊 Total Pages: {len(app.pages)}")
        print(f"   - Main: {len(app.main_pages)}")
        print(f"   - Tasks: {len(app.task_pages)}")
        print(f"   - CRM: {len(app.crm_pages)}")
        
        # Verify all pages have render methods
        print("\n🔍 Verifying Render Methods:")
        missing_methods = []
        for page_key in app.pages.keys():
            method_name = f"render_{page_key}_page"
            if page_key == 'home':
                method_name = "render_home_page"
            
            if not hasattr(app, method_name):
                missing_methods.append((page_key, method_name))
                print(f"  ✗ Missing: {method_name} for page '{page_key}'")
            else:
                print(f"  ✓ Found: {method_name}")
        
        if missing_methods:
            print(f"\n❌ Missing {len(missing_methods)} render methods!")
            return False
        
        print("\n✅ All navigation structure tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_page_imports():
    """Test that all page modules can be imported"""
    print("\n🧪 Testing Page Module Imports...")
    print("=" * 60)
    
    pages_to_test = [
        ('pages.create_plan', 'render_create_plan_page'),
        ('pages.plan_status', 'render_plan_status_page'),
        ('pages.plan_results', 'render_plan_results_page'),
        ('pages.plan_blueprint', 'render_plan_blueprint_page'),
        ('pages.task_list', 'render_task_list_page'),
        ('pages.timeline_view', 'render_timeline_view_page'),
        ('pages.conflicts', 'render_conflicts_page'),
        ('pages.vendors', 'render_vendors_page'),
        ('pages.crm_preferences', 'render_crm_preferences_page'),
        ('pages.communication_history', 'render_communication_history_page'),
        ('pages.crm_analytics', 'render_crm_analytics_page'),
    ]
    
    failed_imports = []
    
    for module_name, function_name in pages_to_test:
        try:
            module = __import__(module_name, fromlist=[function_name])
            if hasattr(module, function_name):
                print(f"  ✓ {module_name}.{function_name}")
            else:
                print(f"  ✗ {module_name} missing {function_name}")
                failed_imports.append((module_name, function_name))
        except Exception as e:
            print(f"  ✗ {module_name}: {str(e)}")
            failed_imports.append((module_name, str(e)))
    
    if failed_imports:
        print(f"\n❌ {len(failed_imports)} import failures!")
        return False
    
    print("\n✅ All page imports successful!")
    return True

def main():
    """Main test function"""
    print("🎯 Event Planning Agent v2 - Navigation Test")
    print("=" * 60)
    
    # Test navigation structure
    structure_ok = test_navigation_structure()
    
    # Test page imports
    imports_ok = test_page_imports()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary:")
    print(f"  Navigation Structure: {'✅ PASS' if structure_ok else '❌ FAIL'}")
    print(f"  Page Imports: {'✅ PASS' if imports_ok else '❌ FAIL'}")
    
    if structure_ok and imports_ok:
        print("\n🎉 All tests PASSED!")
        print("\n💡 Navigation Features:")
        print("  • Grouped navigation (Main, Tasks, Communications)")
        print("  • Conditional navigation based on plan/task/CRM availability")
        print("  • Quick links on home page")
        print("  • Feature status indicators")
        print("  • Session state management")
        return True
    else:
        print("\n❌ Some tests FAILED!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
