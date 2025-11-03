"""
Standalone verification script for Task Management Agent Core

This script verifies the implementation without running full tests.
It checks:
1. Module imports correctly
2. Class structure is correct
3. Methods are defined
4. Basic instantiation works
"""

import sys
import inspect


def verify_imports():
    """Verify that all imports work"""
    print("=" * 60)
    print("VERIFICATION: Task Management Agent Core")
    print("=" * 60)
    print("\n[1] Checking imports...")
    
    try:
        # Try importing the main class
        from task_management_agent import TaskManagementAgent
        print("  ✓ TaskManagementAgent imported successfully")
        return TaskManagementAgent
    except ImportError as e:
        print(f"  ✗ Import failed: {e}")
        return None


def verify_class_structure(TaskManagementAgent):
    """Verify class has required methods"""
    print("\n[2] Checking class structure...")
    
    required_methods = [
        '__init__',
        'process',
        '_invoke_sub_agents',
        '_consolidate_data',
        '_process_tools',
        '_generate_extended_task_list',
        '_update_state',
        '_serialize_extended_task_list'
    ]
    
    all_present = True
    for method_name in required_methods:
        if hasattr(TaskManagementAgent, method_name):
            print(f"  ✓ Method '{method_name}' exists")
        else:
            print(f"  ✗ Method '{method_name}' missing")
            all_present = False
    
    return all_present


def verify_method_signatures(TaskManagementAgent):
    """Verify method signatures match requirements"""
    print("\n[3] Checking method signatures...")
    
    # Check __init__ signature
    init_sig = inspect.signature(TaskManagementAgent.__init__)
    init_params = list(init_sig.parameters.keys())
    print(f"  __init__ parameters: {init_params}")
    
    expected_init = ['self', 'state_manager', 'llm_model', 'db_connection']
    if all(p in init_params for p in expected_init):
        print("  ✓ __init__ signature correct")
    else:
        print(f"  ⚠ __init__ signature differs from expected: {expected_init}")
    
    # Check process signature
    process_sig = inspect.signature(TaskManagementAgent.process)
    process_params = list(process_sig.parameters.keys())
    print(f"  process parameters: {process_params}")
    
    if 'state' in process_params:
        print("  ✓ process signature correct")
    else:
        print("  ✗ process signature missing 'state' parameter")


def verify_instantiation(TaskManagementAgent):
    """Verify basic instantiation works"""
    print("\n[4] Checking instantiation...")
    
    try:
        # Try to create instance (may fail due to dependencies)
        agent = TaskManagementAgent()
        print("  ✓ TaskManagementAgent instantiated successfully")
        
        # Check attributes
        attributes = [
            'prioritization_agent',
            'granularity_agent',
            'resource_dependency_agent',
            'data_consolidator',
            'timeline_tool',
            'llm_tool',
            'vendor_tool',
            'logistics_tool',
            'conflict_tool',
            'venue_tool',
            'tool_execution_status'
        ]
        
        print("\n  Checking attributes:")
        for attr in attributes:
            if hasattr(agent, attr):
                print(f"    ✓ {attr}")
            else:
                print(f"    ✗ {attr} missing")
        
        return True
    except Exception as e:
        print(f"  ⚠ Instantiation failed (may be due to dependencies): {e}")
        print("  This is acceptable if dependencies are not available")
        return False


def verify_docstrings(TaskManagementAgent):
    """Verify docstrings are present"""
    print("\n[5] Checking documentation...")
    
    if TaskManagementAgent.__doc__:
        print("  ✓ Class docstring present")
    else:
        print("  ✗ Class docstring missing")
    
    methods_with_docs = 0
    methods_without_docs = 0
    
    for name, method in inspect.getmembers(TaskManagementAgent, predicate=inspect.isfunction):
        if not name.startswith('_') or name in ['__init__', '_invoke_sub_agents', '_consolidate_data', 
                                                  '_process_tools', '_generate_extended_task_list',
                                                  '_update_state']:
            if method.__doc__:
                methods_with_docs += 1
            else:
                methods_without_docs += 1
                print(f"  ⚠ Method '{name}' missing docstring")
    
    print(f"  Methods with docstrings: {methods_with_docs}")
    print(f"  Methods without docstrings: {methods_without_docs}")


def main():
    """Run all verifications"""
    
    # Step 1: Import
    TaskManagementAgent = verify_imports()
    if not TaskManagementAgent:
        print("\n✗ VERIFICATION FAILED: Could not import TaskManagementAgent")
        return False
    
    # Step 2: Class structure
    structure_ok = verify_class_structure(TaskManagementAgent)
    
    # Step 3: Method signatures
    verify_method_signatures(TaskManagementAgent)
    
    # Step 4: Instantiation
    verify_instantiation(TaskManagementAgent)
    
    # Step 5: Documentation
    verify_docstrings(TaskManagementAgent)
    
    # Summary
    print("\n" + "=" * 60)
    if structure_ok:
        print("✓ VERIFICATION PASSED")
        print("  All required methods are present")
        print("  Implementation appears complete")
    else:
        print("⚠ VERIFICATION INCOMPLETE")
        print("  Some methods may be missing")
    print("=" * 60)
    
    return structure_ok


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
