"""
Test for Resource & Dependency Agent Core

Tests dependency detection and resource identification functionality.
"""

import asyncio
from datetime import datetime, timedelta
from agents.task_management.sub_agents.resource_dependency_agent import ResourceDependencyAgentCore
from agents.task_management.sub_agents.prioritization_agent import PrioritizationAgentCore
from agents.task_management.sub_agents.granularity_agent import GranularityAgentCore


async def test_resource_dependency_agent():
    """Test resource and dependency analysis functionality"""
    
    # Create test state
    event_date = (datetime.now() + timedelta(days=10)).isoformat()
    
    test_state = {
        'plan_id': 'test_plan_001',
        'client_request': {
            'client_id': 'test_client',
            'event_type': 'wedding',
            'guest_count': 150,
            'budget': 50000.0,
            'date': event_date,
            'location': 'Mumbai',
            'preferences': {'photography': 'high_priority'},
            'requirements': {'venue': 'outdoor'}
        },
        'selected_combination': {
            'venue': {
                'id': 'venue_001',
                'name': 'Grand Palace Hotel',
                'type': 'venue'
            },
            'caterer': {
                'id': 'caterer_001',
                'name': 'Royal Caterers',
                'type': 'caterer'
            },
            'photographer': {
                'id': 'photo_001',
                'name': 'Perfect Moments Photography',
                'type': 'photographer'
            },
            'makeup_artist': {
                'id': 'makeup_001',
                'name': 'Glamour Beauty Studio',
                'type': 'makeup_artist'
            }
        },
        'timeline_data': {},
        'workflow_status': 'running'
    }
    
    print("=" * 80)
    print("Testing Resource & Dependency Agent Core")
    print("=" * 80)
    print(f"Event Type: {test_state['client_request']['event_type']}")
    print(f"Guest Count: {test_state['client_request']['guest_count']}")
    print(f"Days until event: ~10 days")
    print()
    
    try:
        # Step 1: Get prioritized tasks
        print("Step 1: Getting prioritized tasks...")
        print("-" * 80)
        prioritization_agent = PrioritizationAgentCore()
        prioritized_tasks = await prioritization_agent.prioritize_tasks(test_state)
        print(f"✓ Generated {len(prioritized_tasks)} prioritized tasks")
        
        # Step 2: Get granular tasks
        print("\nStep 2: Decomposing tasks into granular sub-tasks...")
        print("-" * 80)
        granularity_agent = GranularityAgentCore()
        granular_tasks = await granularity_agent.decompose_tasks(prioritized_tasks, test_state)
        print(f"✓ Generated {len(granular_tasks)} granular tasks")
        
        # Step 3: Analyze dependencies and resources
        print("\nStep 3: Analyzing dependencies and resources...")
        print("-" * 80)
        resource_dependency_agent = ResourceDependencyAgentCore()
        tasks_with_dependencies = await resource_dependency_agent.analyze_dependencies(
            granular_tasks, 
            test_state
        )
        
        print(f"✓ Analyzed {len(tasks_with_dependencies)} tasks")
        
        # Display results
        print("\n" + "=" * 80)
        print("ANALYSIS RESULTS")
        print("=" * 80)
        
        for task in tasks_with_dependencies:
            print(f"\nTask ID: {task.task_id}")
            print(f"Task Name: {task.task_name}")
            
            # Dependencies
            if task.dependencies:
                print(f"Dependencies ({len(task.dependencies)}):")
                for dep_id in task.dependencies:
                    # Find the dependency task name
                    dep_task = next((t for t in tasks_with_dependencies if t.task_id == dep_id), None)
                    dep_name = dep_task.task_name if dep_task else "Unknown"
                    print(f"  - {dep_id}: {dep_name}")
            else:
                print("Dependencies: None (can start immediately)")
            
            # Resources
            if task.resources_required:
                print(f"Resources Required ({len(task.resources_required)}):")
                for resource in task.resources_required:
                    print(f"  - {resource.resource_name} ({resource.resource_type})")
                    if resource.quantity_required > 0:
                        print(f"    Quantity: {resource.quantity_required}")
                    if resource.availability_constraint:
                        print(f"    Constraint: {resource.availability_constraint}")
            else:
                print("Resources Required: None identified")
            
            # Conflicts
            if task.resource_conflicts:
                print(f"Potential Conflicts ({len(task.resource_conflicts)}):")
                for conflict in task.resource_conflicts:
                    print(f"  ⚠ {conflict}")
            
            print("-" * 80)
        
        # Summary statistics
        print("\n" + "=" * 80)
        print("SUMMARY STATISTICS")
        print("=" * 80)
        
        total_tasks = len(tasks_with_dependencies)
        tasks_with_deps = sum(1 for t in tasks_with_dependencies if t.dependencies)
        tasks_with_resources = sum(1 for t in tasks_with_dependencies if t.resources_required)
        tasks_with_conflicts = sum(1 for t in tasks_with_dependencies if t.resource_conflicts)
        
        total_dependencies = sum(len(t.dependencies) for t in tasks_with_dependencies)
        total_resources = sum(len(t.resources_required) for t in tasks_with_dependencies)
        
        print(f"Total Tasks Analyzed: {total_tasks}")
        print(f"Tasks with Dependencies: {tasks_with_deps} ({tasks_with_deps/total_tasks*100:.1f}%)")
        print(f"Tasks with Resources: {tasks_with_resources} ({tasks_with_resources/total_tasks*100:.1f}%)")
        print(f"Tasks with Conflicts: {tasks_with_conflicts} ({tasks_with_conflicts/total_tasks*100:.1f}%)")
        print(f"Total Dependencies Identified: {total_dependencies}")
        print(f"Total Resources Identified: {total_resources}")
        
        # Resource breakdown
        resource_types = {}
        for task in tasks_with_dependencies:
            for resource in task.resources_required:
                resource_type = resource.resource_type
                resource_types[resource_type] = resource_types.get(resource_type, 0) + 1
        
        if resource_types:
            print("\nResource Breakdown by Type:")
            for resource_type, count in sorted(resource_types.items()):
                print(f"  - {resource_type}: {count}")
        
        print("\n" + "=" * 80)
        print("✓ Test completed successfully!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_resource_dependency_agent())
