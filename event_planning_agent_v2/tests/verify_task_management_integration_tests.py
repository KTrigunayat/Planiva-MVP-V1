"""
Verification script for Task Management Agent integration tests

This script verifies that:
1. Integration test file exists and is properly structured
2. All test classes and methods are defined
3. Test fixtures are properly configured
4. Documentation is complete
"""

import os
import sys
from pathlib import Path

def verify_test_file():
    """Verify the integration test file exists and has correct structure"""
    test_file = Path(__file__).parent / "test_task_management_agent.py"
    
    if not test_file.exists():
        print("❌ Test file does not exist")
        return False
    
    print("✅ Test file exists")
    
    # Read the file content
    with open(test_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for required test classes
    required_classes = [
        "TestTaskManagementAgentIntegration",
        "TestTaskManagementAgentPerformance",
        "TestTaskManagementAgentEdgeCases"
    ]
    
    for class_name in required_classes:
        if f"class {class_name}" in content:
            print(f"✅ Test class '{class_name}' found")
        else:
            print(f"❌ Test class '{class_name}' not found")
            return False
    
    # Check for required test methods
    required_tests = [
        "test_full_workflow_integration",
        "test_error_scenario_missing_sub_agent_data",
        "test_error_scenario_tool_failure",
        "test_error_scenario_database_unavailable",
        "test_state_management_and_persistence",
        "test_workflow_integration_with_timeline_agent",
        "test_workflow_integration_with_blueprint_agent",
        "test_performance_with_many_tasks",
        "test_empty_selected_combination",
        "test_missing_timeline_data"
    ]
    
    for test_name in required_tests:
        if f"def {test_name}" in content:
            print(f"✅ Test method '{test_name}' found")
        else:
            print(f"❌ Test method '{test_name}' not found")
            return False
    
    # Check for fixtures
    required_fixtures = [
        "sample_event_state",
        "mock_sub_agent_outputs",
        "large_event_state"
    ]
    
    for fixture_name in required_fixtures:
        if f"def {fixture_name}" in content:
            print(f"✅ Fixture '{fixture_name}' found")
        else:
            print(f"❌ Fixture '{fixture_name}' not found")
            return False
    
    return True


def verify_readme():
    """Verify the README documentation exists and is complete"""
    readme_file = Path(__file__).parent.parent / "agents" / "task_management" / "README.md"
    
    if not readme_file.exists():
        print("❌ README.md does not exist")
        return False
    
    print("✅ README.md exists")
    
    # Read the file content
    with open(readme_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for required sections
    required_sections = [
        "# Task Management Agent",
        "## Overview",
        "## Architecture",
        "## Components",
        "## Data Models",
        "## Usage",
        "## Configuration",
        "## Tool Execution Order",
        "## Testing",
        "## Database Schema",
        "## Error Handling",
        "## Performance Considerations",
        "## Troubleshooting"
    ]
    
    for section in required_sections:
        if section in content:
            print(f"✅ Section '{section}' found")
        else:
            print(f"❌ Section '{section}' not found")
            return False
    
    # Check for code examples
    if "```python" in content:
        print("✅ Code examples found")
    else:
        print("❌ No code examples found")
        return False
    
    # Check for diagrams
    if "```mermaid" in content or "```" in content:
        print("✅ Diagrams/code blocks found")
    else:
        print("⚠️  No diagrams found (optional)")
    
    return True


def verify_directory_structure():
    """Verify the task management directory structure"""
    base_dir = Path(__file__).parent.parent / "agents" / "task_management"
    
    required_dirs = [
        "core",
        "sub_agents",
        "tools",
        "models"
    ]
    
    for dir_name in required_dirs:
        dir_path = base_dir / dir_name
        if dir_path.exists() and dir_path.is_dir():
            print(f"✅ Directory '{dir_name}' exists")
        else:
            print(f"❌ Directory '{dir_name}' not found")
            return False
    
    return True


def main():
    """Main verification function"""
    print("=" * 70)
    print("Task Management Agent Integration Tests Verification")
    print("=" * 70)
    print()
    
    print("1. Verifying directory structure...")
    print("-" * 70)
    structure_ok = verify_directory_structure()
    print()
    
    print("2. Verifying integration test file...")
    print("-" * 70)
    test_ok = verify_test_file()
    print()
    
    print("3. Verifying README documentation...")
    print("-" * 70)
    readme_ok = verify_readme()
    print()
    
    print("=" * 70)
    print("Verification Summary")
    print("=" * 70)
    print(f"Directory Structure: {'✅ PASS' if structure_ok else '❌ FAIL'}")
    print(f"Integration Tests: {'✅ PASS' if test_ok else '❌ FAIL'}")
    print(f"README Documentation: {'✅ PASS' if readme_ok else '❌ FAIL'}")
    print()
    
    if structure_ok and test_ok and readme_ok:
        print("🎉 All verifications passed!")
        print()
        print("Next steps:")
        print("1. Run integration tests: pytest tests/test_task_management_agent.py -v")
        print("2. Review README.md for usage instructions")
        print("3. Check test coverage: pytest tests/test_task_management_agent.py --cov")
        return 0
    else:
        print("❌ Some verifications failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
