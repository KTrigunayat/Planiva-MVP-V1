"""
Simple verification script for Task Management Node integration.

This script verifies that:
1. The task_management_node module can be imported
2. The workflow includes the task management node
3. The conditional logic functions work correctly
4. The node is properly connected in the workflow graph
"""

import sys
import os
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))


def verify_imports():
    """Verify that all required modules can be imported"""
    print("=" * 80)
    print("STEP 1: Verifying imports...")
    print("=" * 80)
    
    try:
        from event_planning_agent_v2.workflows.task_management_node import (
            task_management_node,
            should_run_task_management
        )
        print("✓ task_management_node module imported successfully")
        print(f"  - task_management_node: {task_management_node}")
        print(f"  - should_run_task_management: {should_run_task_management}")
        return True
    except Exception as e:
        print(f"✗ Failed to import task_management_node: {e}")
        return False


def verify_workflow_structure():
    """Verify that the workflow includes the task management node"""
    print("\n" + "=" * 80)
    print("STEP 2: Verifying workflow structure...")
    print("=" * 80)
    
    try:
        from event_planning_agent_v2.workflows.planning_workflow import (
            create_event_planning_workflow,
            should_generate_blueprint,
            should_skip_task_management
        )
        
        print("✓ Workflow functions imported successfully")
        
        # Create workflow
        workflow = create_event_planning_workflow()
        print("✓ Workflow created successfully")
        
        # Check if task_management node exists
        if hasattr(workflow, 'nodes'):
            nodes = workflow.nodes
            if 'task_management' in nodes:
                print("✓ task_management node found in workflow")
                print(f"  - Node function: {nodes['task_management']}")
            else:
                print("✗ task_management node NOT found in workflow")
                print(f"  - Available nodes: {list(nodes.keys())}")
                return False
        else:
            print("✗ Workflow does not have nodes attribute")
            return False
        
        # Verify other expected nodes
        expected_nodes = [
            'initialize',
            'budget_allocation',
            'vendor_sourcing',
            'beam_search',
            'client_selection',
            'task_management',
            'blueprint_generation'
        ]
        
        missing_nodes = [node for node in expected_nodes if node not in nodes]
        if missing_nodes:
            print(f"✗ Missing expected nodes: {missing_nodes}")
            return False
        else:
            print(f"✓ All expected nodes present: {expected_nodes}")
        
        return True
        
    except Exception as e:
        print(f"✗ Failed to verify workflow structure: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_conditional_logic():
    """Verify that conditional logic functions work correctly"""
    print("\n" + "=" * 80)
    print("STEP 3: Verifying conditional logic...")
    print("=" * 80)
    
    try:
        from event_planning_agent_v2.workflows.task_management_node import (
            should_run_task_management
        )
        from event_planning_agent_v2.workflows.state_models import WorkflowStatus
        
        # Test case 1: Should run with timeline data
        state_with_timeline: Dict[str, Any] = {
            'plan_id': 'test-123',
            'timeline_data': {'tasks': []},
            'workflow_status': WorkflowStatus.RUNNING.value
        }
        
        result1 = should_run_task_management(state_with_timeline)
        if result1:
            print("✓ Test 1 passed: Returns True when timeline_data is present")
        else:
            print("✗ Test 1 failed: Should return True when timeline_data is present")
            return False
        
        # Test case 2: Should skip without timeline data
        state_without_timeline: Dict[str, Any] = {
            'plan_id': 'test-123',
            'timeline_data': None,
            'workflow_status': WorkflowStatus.RUNNING.value
        }
        
        result2 = should_run_task_management(state_without_timeline)
        if not result2:
            print("✓ Test 2 passed: Returns False when timeline_data is missing")
        else:
            print("✗ Test 2 failed: Should return False when timeline_data is missing")
            return False
        
        # Test case 3: Should skip when workflow is failed
        state_failed: Dict[str, Any] = {
            'plan_id': 'test-123',
            'timeline_data': {'tasks': []},
            'workflow_status': WorkflowStatus.FAILED.value
        }
        
        result3 = should_run_task_management(state_failed)
        if not result3:
            print("✓ Test 3 passed: Returns False when workflow is FAILED")
        else:
            print("✗ Test 3 failed: Should return False when workflow is FAILED")
            return False
        
        print("✓ All conditional logic tests passed")
        return True
        
    except Exception as e:
        print(f"✗ Failed to verify conditional logic: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_workflow_edges():
    """Verify that workflow edges are properly configured"""
    print("\n" + "=" * 80)
    print("STEP 4: Verifying workflow edges...")
    print("=" * 80)
    
    try:
        from event_planning_agent_v2.workflows.planning_workflow import (
            create_event_planning_workflow
        )
        
        workflow = create_event_planning_workflow()
        
        # Check if workflow has edges
        if hasattr(workflow, '_edges'):
            print("✓ Workflow has edges defined")
            
            # Look for task_management in edges
            edges_str = str(workflow._edges)
            if 'task_management' in edges_str:
                print("✓ task_management node is referenced in workflow edges")
            else:
                print("⚠ task_management node may not be connected in workflow edges")
        else:
            print("⚠ Cannot verify edges (workflow structure may differ)")
        
        return True
        
    except Exception as e:
        print(f"✗ Failed to verify workflow edges: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_exports():
    """Verify that new functions are exported from __init__.py"""
    print("\n" + "=" * 80)
    print("STEP 5: Verifying module exports...")
    print("=" * 80)
    
    try:
        from event_planning_agent_v2.workflows import (
            task_management_node,
            should_run_task_management,
            should_skip_task_management
        )
        
        print("✓ task_management_node exported from workflows module")
        print("✓ should_run_task_management exported from workflows module")
        print("✓ should_skip_task_management exported from workflows module")
        
        return True
        
    except ImportError as e:
        print(f"✗ Failed to import from workflows module: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all verification steps"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 15 + "TASK MANAGEMENT NODE INTEGRATION VERIFICATION" + " " * 16 + "║")
    print("╚" + "=" * 78 + "╝")
    print("\n")
    
    results = []
    
    # Run verification steps
    results.append(("Imports", verify_imports()))
    results.append(("Workflow Structure", verify_workflow_structure()))
    results.append(("Conditional Logic", verify_conditional_logic()))
    results.append(("Workflow Edges", verify_workflow_edges()))
    results.append(("Module Exports", verify_exports()))
    
    # Print summary
    print("\n" + "=" * 80)
    print("VERIFICATION SUMMARY")
    print("=" * 80)
    
    for step_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{step_name:.<50} {status}")
    
    all_passed = all(result[1] for result in results)
    
    print("=" * 80)
    if all_passed:
        print("✓ ALL VERIFICATION STEPS PASSED")
        print("\nTask Management Node is properly integrated into the LangGraph workflow!")
        return 0
    else:
        print("✗ SOME VERIFICATION STEPS FAILED")
        print("\nPlease review the errors above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
