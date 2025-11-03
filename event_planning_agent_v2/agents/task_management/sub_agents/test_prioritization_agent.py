"""
Simple test for Prioritization Agent Core

Tests basic functionality without requiring full system setup.
"""

import asyncio
from datetime import datetime, timedelta
from prioritization_agent import PrioritizationAgentCore


async def test_prioritization_agent():
    """Test basic prioritization functionality"""
    
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
                'name': 'Grand Palace',
                'type': 'venue'
            },
            'caterer': {
                'id': 'caterer_001',
                'name': 'Royal Caterers',
                'type': 'caterer'
            },
            'photographer': {
                'id': 'photo_001',
                'name': 'Perfect Moments',
                'type': 'photographer'
            }
        },
        'timeline_data': None,
        'workflow_status': 'running'
    }
    
    print("Testing Prioritization Agent Core...")
    print(f"Event Date: {event_date}")
    print(f"Days until event: ~10 days")
    print()
    
    # Initialize agent
    agent = PrioritizationAgentCore()
    
    try:
        # Test prioritization
        print("Running prioritization...")
        prioritized_tasks = await agent.prioritize_tasks(test_state)
        
        print(f"\nSuccessfully prioritized {len(prioritized_tasks)} tasks:")
        print("-" * 80)
        
        for task in prioritized_tasks:
            print(f"\nTask ID: {task.task_id}")
            print(f"Task Name: {task.task_name}")
            print(f"Priority Level: {task.priority_level}")
            print(f"Priority Score: {task.priority_score:.2f}")
            print(f"Rationale: {task.priority_rationale}")
        
        print("\n" + "=" * 80)
        print("✓ Test completed successfully!")
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_prioritization_agent())
