"""
Test script for API/LLM Tool

Tests the APILLMTool implementation with sample consolidated task data.
Verifies:
- Task enhancement with LLM
- Retry logic with exponential backoff
- Fallback mechanism when LLM unavailable
- Parsing of structured and unstructured responses
- Manual review flagging
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import timedelta
from typing import List

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from agents.task_management.tools.api_llm_tool import APILLMTool
from agents.task_management.models.consolidated_models import ConsolidatedTaskData, ConsolidatedTask
from agents.task_management.models.data_models import Resource, EnhancedTask

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_sample_consolidated_data() -> ConsolidatedTaskData:
    """Create sample consolidated task data for testing"""
    
    # Sample resources
    venue_resource = Resource(
        resource_type="venue",
        resource_id="venue_001",
        resource_name="Grand Ballroom",
        quantity_required=1,
        availability_constraint="Must be available 2 hours before event"
    )
    
    caterer_resource = Resource(
        resource_type="vendor",
        resource_id="caterer_001",
        resource_name="Gourmet Catering Co.",
        quantity_required=1
    )
    
    photographer_resource = Resource(
        resource_type="vendor",
        resource_id="photographer_001",
        resource_name="Perfect Moments Photography",
        quantity_required=1
    )
    
    # Sample tasks
    tasks = [
        ConsolidatedTask(
            task_id="task_001",
            task_name="Venue Setup and Decoration",
            priority_level="Critical",
            priority_score=0.92,
            priority_rationale="Must be completed before any other activities",
            parent_task_id=None,
            task_description="Set up venue with decorations, seating arrangements, and stage",
            granularity_level=0,
            estimated_duration=timedelta(hours=4),
            sub_tasks=["task_001_1", "task_001_2"],
            dependencies=[],
            resources_required=[venue_resource],
            resource_conflicts=[]
        ),
        ConsolidatedTask(
            task_id="task_002",
            task_name="Catering Coordination",
            priority_level="High",
            priority_score=0.85,
            priority_rationale="Food service is critical for guest satisfaction",
            parent_task_id=None,
            task_description="Coordinate with caterer for menu setup, service timing, and dietary requirements",
            granularity_level=0,
            estimated_duration=timedelta(hours=6),
            sub_tasks=["task_002_1", "task_002_2", "task_002_3"],
            dependencies=["task_001"],
            resources_required=[caterer_resource, venue_resource],
            resource_conflicts=[]
        ),
        ConsolidatedTask(
            task_id="task_003",
            task_name="Photography Coverage",
            priority_level="High",
            priority_score=0.78,
            priority_rationale="Capturing memories is important for the event",
            parent_task_id=None,
            task_description="Coordinate photographer for event coverage",
            granularity_level=0,
            estimated_duration=timedelta(hours=8),
            sub_tasks=[],
            dependencies=["task_001"],
            resources_required=[photographer_resource],
            resource_conflicts=[]
        ),
        ConsolidatedTask(
            task_id="task_004",
            task_name="Guest Registration Setup",
            priority_level="Medium",
            priority_score=0.55,
            priority_rationale="Important for smooth guest flow",
            parent_task_id=None,
            task_description="Set up registration desk",
            granularity_level=0,
            estimated_duration=timedelta(hours=1),
            sub_tasks=[],
            dependencies=["task_001"],
            resources_required=[],
            resource_conflicts=[]
        ),
    ]
    
    # Event context
    event_context = {
        'event_type': 'Wedding',
        'event_date': '2025-11-15',
        'guest_count': 150,
        'budget': 50000.0,
        'location': 'Mumbai, India',
        'days_until_event': 30,
        'preferences': {
            'theme': 'Traditional Indian',
            'cuisine': 'North Indian'
        }
    }
    
    return ConsolidatedTaskData(
        tasks=tasks,
        event_context=event_context,
        processing_metadata={
            'sub_agents_completed': ['prioritization', 'granularity', 'resource_dependency'],
            'timestamp': '2025-10-18T10:00:00'
        }
    )


async def test_basic_enhancement():
    """Test basic task enhancement functionality"""
    logger.info("=" * 60)
    logger.info("TEST 1: Basic Task Enhancement")
    logger.info("=" * 60)
    
    # Create tool
    tool = APILLMTool()
    
    # Create sample data
    consolidated_data = create_sample_consolidated_data()
    
    try:
        # Enhance tasks
        enhanced_tasks = await tool.enhance_tasks(consolidated_data)
        
        logger.info(f"\nSuccessfully enhanced {len(enhanced_tasks)} tasks")
        
        # Display results
        for enhanced_task in enhanced_tasks:
            logger.info(f"\n--- Task: {enhanced_task.task_id} ---")
            logger.info(f"Enhanced Description: {enhanced_task.enhanced_description[:100]}...")
            logger.info(f"Suggestions: {len(enhanced_task.suggestions)}")
            for i, suggestion in enumerate(enhanced_task.suggestions, 1):
                logger.info(f"  {i}. {suggestion}")
            logger.info(f"Potential Issues: {len(enhanced_task.potential_issues)}")
            for i, issue in enumerate(enhanced_task.potential_issues, 1):
                logger.info(f"  {i}. {issue}")
            logger.info(f"Best Practices: {len(enhanced_task.best_practices)}")
            for i, practice in enumerate(enhanced_task.best_practices, 1):
                logger.info(f"  {i}. {practice}")
            logger.info(f"Requires Manual Review: {enhanced_task.requires_manual_review}")
        
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        return False


async def test_fallback_mechanism():
    """Test fallback mechanism when LLM is unavailable"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 2: Fallback Mechanism")
    logger.info("=" * 60)
    
    # Create tool with invalid model to trigger fallback
    tool = APILLMTool(llm_model="invalid_model_name")
    
    # Create minimal sample data
    task = ConsolidatedTask(
        task_id="fallback_task",
        task_name="Test Fallback Task",
        priority_level="High",
        priority_score=0.75,
        priority_rationale="Testing fallback",
        parent_task_id=None,
        task_description="This task should use fallback enhancement",
        granularity_level=0,
        estimated_duration=timedelta(hours=2),
        sub_tasks=[],
        dependencies=["task_001"],
        resources_required=[],
        resource_conflicts=["resource_conflict_1"]
    )
    
    consolidated_data = ConsolidatedTaskData(
        tasks=[task],
        event_context={'event_type': 'Test Event'},
        processing_metadata={}
    )
    
    try:
        # This should use fallback mechanism
        enhanced_tasks = await tool.enhance_tasks(consolidated_data)
        
        logger.info(f"\nFallback enhancement completed for {len(enhanced_tasks)} tasks")
        
        enhanced_task = enhanced_tasks[0]
        logger.info(f"\n--- Fallback Task: {enhanced_task.task_id} ---")
        logger.info(f"Enhanced Description: {enhanced_task.enhanced_description}")
        logger.info(f"Suggestions: {enhanced_task.suggestions}")
        logger.info(f"Potential Issues: {enhanced_task.potential_issues}")
        logger.info(f"Best Practices: {enhanced_task.best_practices}")
        logger.info(f"Requires Manual Review: {enhanced_task.requires_manual_review}")
        
        # Verify fallback was used
        if enhanced_task.requires_manual_review:
            logger.info("\n✓ Fallback mechanism correctly flagged task for manual review")
            return True
        else:
            logger.warning("\n✗ Fallback task should be flagged for manual review")
            return False
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        return False


async def test_manual_review_flagging():
    """Test automatic flagging of tasks requiring manual review"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 3: Manual Review Flagging")
    logger.info("=" * 60)
    
    tool = APILLMTool()
    
    # Create tasks with various issues that should trigger manual review
    tasks = [
        ConsolidatedTask(
            task_id="incomplete_task",
            task_name="Incomplete Task",
            priority_level="Critical",
            priority_score=0.90,
            priority_rationale="Critical but incomplete",
            parent_task_id=None,
            task_description="TBD",  # Should trigger manual review
            granularity_level=0,
            estimated_duration=timedelta(hours=1),
            sub_tasks=[],
            dependencies=[],
            resources_required=[],  # Critical task without resources
            resource_conflicts=[]
        ),
        ConsolidatedTask(
            task_id="short_desc_task",
            task_name="Short Description Task",
            priority_level="High",
            priority_score=0.70,
            priority_rationale="Insufficient detail",
            parent_task_id=None,
            task_description="Do it",  # Too short
            granularity_level=0,
            estimated_duration=timedelta(hours=2),
            sub_tasks=[],
            dependencies=[],
            resources_required=[],
            resource_conflicts=[]
        ),
    ]
    
    consolidated_data = ConsolidatedTaskData(
        tasks=tasks,
        event_context={'event_type': 'Test Event'},
        processing_metadata={}
    )
    
    try:
        enhanced_tasks = await tool.enhance_tasks(consolidated_data)
        
        logger.info(f"\nProcessed {len(enhanced_tasks)} tasks with potential issues")
        
        flagged_count = sum(1 for t in enhanced_tasks if t.requires_manual_review)
        logger.info(f"Tasks flagged for manual review: {flagged_count}/{len(enhanced_tasks)}")
        
        for enhanced_task in enhanced_tasks:
            logger.info(f"\n--- Task: {enhanced_task.task_id} ---")
            logger.info(f"Description: {enhanced_task.enhanced_description}")
            logger.info(f"Requires Manual Review: {enhanced_task.requires_manual_review}")
        
        if flagged_count > 0:
            logger.info("\n✓ Manual review flagging is working")
            return True
        else:
            logger.warning("\n✗ Expected some tasks to be flagged for manual review")
            return False
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        return False


async def main():
    """Run all tests"""
    logger.info("Starting API/LLM Tool Tests")
    logger.info("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("Basic Enhancement", await test_basic_enhancement()))
    results.append(("Fallback Mechanism", await test_fallback_mechanism()))
    results.append(("Manual Review Flagging", await test_manual_review_flagging()))
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        logger.info(f"{test_name}: {status}")
    
    total_passed = sum(1 for _, passed in results if passed)
    logger.info(f"\nTotal: {total_passed}/{len(results)} tests passed")
    
    return total_passed == len(results)


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
