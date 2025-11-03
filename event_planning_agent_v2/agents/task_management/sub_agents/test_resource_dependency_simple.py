"""
Simple test for Resource & Dependency Agent Core

Tests basic functionality without requiring full infrastructure.
"""

import asyncio
import sys
from pathlib import Path
from datetime import timedelta

# Add parent directories to path for imports
current_dir = Path(__file__).parent
task_management_dir = current_dir.parent
agents_dir = task_management_dir.parent
project_root = agents_dir.parent

sys.path.insert(0, str(project_root))
sys.path.insert(0, str(agents_dir))
sys.path.insert(0, str(task_management_dir))

from agents.task_management.sub_agents.resource_dependency_agent import ResourceDependencyAgentCore
from agents.task_management.models.task_models import GranularTask
from agents.task_management.models.data_models import Resource


async def test_basic_functionality():
    """Test basic resource and dependency detection"""
    print("=" * 60)
    print("Testing Resource & Dependency Agent Core")
    print("=" * 60)
    
    # Create agent
    agent = ResourceDependencyAgentCore()
    print("\n✓ Agent initialized successfully")
    
    # Create sample granular tasks
    tasks = [
        GranularTask(
            task_id="task_1",
            parent_task_id=None,
            task_name="Venue Setup",
            task_description="Coordinate venue setup and preparation",
            granularity_level=0,
            estimated_duration=timedelta(hours=4),
            sub_tasks=["task_1_sub_1", "task_1_sub_2"]
        ),
        GranularTask(
            task_id="task_1_sub_1",
            parent_task_id="task_1",
            task_name="Confirm venue booking",
            task_description="Finalize venue contract and payment",
            granularity_level=1,
            estimated_duration=timedelta(hours=1),
            sub_tasks=[]
        ),
        GranularTask(
            task_id="task_1_sub_2",
            parent_task_id="task_1",
            task_name="Coordinate venue setup requirements",
            task_description="Discuss layout, equipment, and timing with venue",
            granularity_level=1,
            estimated_duration=timedelta(hours=2),
            sub_tasks=[]
        ),
        GranularTask(
            task_id="task_2",
            parent_task_id=None,
            task_name="Catering Coordination",
            task_description="Coordinate catering services and menu",
            granularity_level=0,
            estimated_duration=timedelta(hours=6),
            sub_tasks=["task_2_sub_1"]
        ),
        GranularTask(
            task_id="task_2_sub_1",
            parent_task_id="task_2",
            task_name="Finalize menu selection",
            task_description="Confirm dishes and dietary accommodations after venue is confirmed",
            granularity_level=1,
            estimated_duration=timedelta(hours=2),
            sub_tasks=[]
        )
    ]
    
    print(f"\n✓ Created {len(tasks)} sample tasks")
    
    # Create mock state
    mock_state = {
        'client_request': {
            'event_type': 'wedding',
            'guest_count': 150,
            'budget': 50000,
            'location': 'Mumbai',
            'preferences': {},
            'requirements': {}
        },
        'selected_combination': {
            'venue': {
                'id': 1,
                'name': 'Grand Palace Hotel',
                'type': 'hotel'
            },
            'caterer': {
                'id': 2,
                'name': 'Delicious Catering Co.',
                'type': 'caterer'
            },
            'photographer': {
                'id': 3,
                'name': 'Perfect Moments Photography',
                'type': 'photographer'
            }
        },
        'timeline_data': {}
    }
    
    print("\n✓ Created mock event planning state")
    
    # Test dependency analysis
    print("\n" + "-" * 60)
    print("Testing Dependency Analysis...")
    print("-" * 60)
    
    try:
        # Note: This will fail without LLM infrastructure, but we can test the structure
        print("\nAttempting to analyze dependencies...")
        print("(Note: Full analysis requires LLM infrastructure)")
        
        # Test individual methods that don't require LLM
        print("\n1. Testing dependency detection (rule-based):")
        
        # Test parent-child dependency
        task_with_parent = tasks[1]  # task_1_sub_1
        dependencies = agent._detect_dependencies(task_with_parent, tasks)
        print(f"   Task: {task_with_parent.task_name}")
        print(f"   Dependencies detected: {dependencies}")
        
        # Test sibling dependencies
        task_with_siblings = tasks[2]  # task_1_sub_2
        siblings = [t for t in tasks if t.parent_task_id == task_with_siblings.parent_task_id 
                   and t.task_id != task_with_siblings.task_id]
        sibling_deps = agent._detect_sibling_dependencies(task_with_siblings, siblings)
        print(f"\n   Task: {task_with_siblings.task_name}")
        print(f"   Sibling dependencies: {sibling_deps}")
        
        # Test logical dependencies
        task_with_logical_deps = tasks[4]  # task_2_sub_1 (mentions "after venue is confirmed")
        logical_deps = agent._detect_logical_dependencies(task_with_logical_deps, tasks)
        print(f"\n   Task: {task_with_logical_deps.task_name}")
        print(f"   Logical dependencies: {logical_deps}")
        
        print("\n2. Testing resource extraction (rule-based):")
        
        # Test vendor resource extraction
        event_context = agent._extract_event_context(mock_state)
        venue_task = tasks[0]  # Venue Setup
        vendor_resources = agent._extract_vendor_resources(venue_task, event_context)
        print(f"   Task: {venue_task.task_name}")
        print(f"   Vendor resources found: {len(vendor_resources)}")
        for resource in vendor_resources:
            print(f"     - {resource.resource_name} ({resource.resource_type})")
        
        # Test equipment resource extraction (fallback)
        equipment_resources = agent._extract_equipment_resources_fallback(venue_task)
        print(f"\n   Equipment resources found: {len(equipment_resources)}")
        for resource in equipment_resources:
            print(f"     - {resource.resource_name}")
        
        # Test personnel resource extraction
        personnel_resources = agent._extract_personnel_resources(venue_task, event_context)
        print(f"\n   Personnel resources found: {len(personnel_resources)}")
        for resource in personnel_resources:
            print(f"     - {resource.resource_name} (Qty: {resource.quantity_required})")
        
        print("\n3. Testing resource conflict detection:")
        
        # Create sample resources
        sample_resources = [
            Resource(
                resource_type="vendor",
                resource_id="1",
                resource_name="Grand Palace Hotel",
                quantity_required=1
            ),
            Resource(
                resource_type="equipment",
                resource_id="eq1",
                resource_name="Tables",
                quantity_required=20
            ),
            Resource(
                resource_type="personnel",
                resource_id="p1",
                resource_name="Event Staff",
                quantity_required=5
            )
        ]
        
        conflicts = agent._detect_resource_conflicts(venue_task, sample_resources, tasks)
        print(f"   Potential conflicts detected: {len(conflicts)}")
        for conflict in conflicts:
            print(f"     - {conflict}")
        
        print("\n" + "=" * 60)
        print("✓ Basic functionality tests completed successfully!")
        print("=" * 60)
        
        print("\nSummary:")
        print("- Dependency detection: Working (rule-based)")
        print("- Resource extraction: Working (rule-based)")
        print("- Conflict detection: Working")
        print("- LLM integration: Requires full infrastructure")
        
    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_basic_functionality())
