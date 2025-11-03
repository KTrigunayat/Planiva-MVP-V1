"""
Test suite for Granularity Agent Core

Tests task decomposition functionality including:
- Basic task decomposition
- Granularity level determination
- Duration estimation
- LLM integration
- Error handling
"""

import pytest
import asyncio
from datetime import timedelta
from unittest.mock import Mock, AsyncMock, patch

from .granularity_agent import GranularityAgentCore
from ..models.task_models import PrioritizedTask, GranularTask
from ..exceptions import SubAgentDataError


@pytest.fixture
def sample_prioritized_tasks():
    """Sample prioritized tasks for testing"""
    return [
        PrioritizedTask(
            task_id="task_1",
            task_name="Venue Setup - Grand Ballroom",
            priority_level="Critical",
            priority_score=0.92,
            priority_rationale="Venue must be confirmed early to secure date"
        ),
        PrioritizedTask(
            task_id="task_2",
            task_name="Catering Coordination - Delicious Catering",
            priority_level="High",
            priority_score=0.78,
            priority_rationale="Catering requires advance planning for large guest count"
        ),
        PrioritizedTask(
            task_id="task_3",
            task_name="Photography Session - Pro Photos",
            priority_level="Medium",
            priority_score=0.55,
            priority_rationale="Photography can be scheduled closer to event"
        ),
        PrioritizedTask(
            task_id="task_4",
            task_name="Makeup Services - Beauty Studio",
            priority_level="Low",
            priority_score=0.35,
            priority_rationale="Makeup is flexible and can be scheduled last"
        )
    ]


@pytest.fixture
def sample_state():
    """Sample EventPlanningState for testing"""
    return {
        'client_request': {
            'event_type': 'wedding',
            'guest_count': 150,
            'budget': 50000,
            'location': 'Mumbai',
            'date': '2025-12-15',
            'preferences': {'style': 'traditional'},
            'requirements': {'vegetarian_menu': True}
        },
        'selected_combination': {
            'venue': {'id': 'v1', 'name': 'Grand Ballroom'},
            'caterer': {'id': 'c1', 'name': 'Delicious Catering'},
            'photographer': {'id': 'p1', 'name': 'Pro Photos'},
            'makeup_artist': {'id': 'm1', 'name': 'Beauty Studio'}
        }
    }


@pytest.fixture
def mock_llm_manager():
    """Mock LLM manager for testing"""
    manager = AsyncMock()
    manager.generate_response = AsyncMock()
    return manager


class TestGranularityAgentCore:
    """Test suite for GranularityAgentCore"""
    
    def test_initialization(self):
        """Test agent initialization"""
        agent = GranularityAgentCore()
        assert agent.llm_model is not None
        assert agent.llm_manager is None  # Not initialized until first use
    
    def test_initialization_with_custom_model(self):
        """Test agent initialization with custom LLM model"""
        agent = GranularityAgentCore(llm_model="tinyllama")
        assert agent.llm_model == "tinyllama"
    
    @pytest.mark.asyncio
    async def test_decompose_tasks_empty_list(self, sample_state):
        """Test decomposition with empty task list"""
        agent = GranularityAgentCore()
        result = await agent.decompose_tasks([], sample_state)
        assert result == []
    
    @pytest.mark.asyncio
    async def test_decompose_tasks_basic(self, sample_prioritized_tasks, sample_state, mock_llm_manager):
        """Test basic task decomposition"""
        agent = GranularityAgentCore()
        agent.llm_manager = mock_llm_manager
        
        # Mock LLM response
        mock_llm_manager.generate_response.return_value = """
Sub-task 1: Confirm venue booking and contract
Description: Finalize venue contract and payment

Sub-task 2: Coordinate venue setup requirements
Description: Discuss layout, equipment, and timing

Sub-task 3: Schedule venue walkthrough
Description: Visit venue to confirm arrangements
"""
        
        result = await agent.decompose_tasks(sample_prioritized_tasks[:1], sample_state)
        
        # Should have parent task + sub-tasks
        assert len(result) > 1
        
        # First task should be parent
        parent = result[0]
        assert parent.task_id == "task_1"
        assert parent.parent_task_id is None
        assert parent.granularity_level == GranularityAgentCore.LEVEL_TOP
        assert len(parent.sub_tasks) > 0
        
        # Remaining tasks should be children
        for child in result[1:]:
            assert child.parent_task_id == "task_1"
            assert child.granularity_level == GranularityAgentCore.LEVEL_SUB
            assert child.task_id.startswith("task_1_sub_")
    
    def test_determine_granularity_level_critical(self):
        """Test granularity level determination for critical tasks"""
        agent = GranularityAgentCore()
        
        task = PrioritizedTask(
            task_id="t1",
            task_name="Critical Task",
            priority_level="Critical",
            priority_score=0.95,
            priority_rationale="Very important"
        )
        
        level = agent._determine_granularity_level(task)
        assert level == 1  # Should break down critical tasks
    
    def test_determine_granularity_level_high(self):
        """Test granularity level determination for high priority tasks"""
        agent = GranularityAgentCore()
        
        task = PrioritizedTask(
            task_id="t1",
            task_name="High Priority Task",
            priority_level="High",
            priority_score=0.75,
            priority_rationale="Important"
        )
        
        level = agent._determine_granularity_level(task)
        assert level == 1  # Should break down high priority tasks
    
    def test_determine_granularity_level_low(self):
        """Test granularity level determination for low priority tasks"""
        agent = GranularityAgentCore()
        
        task = PrioritizedTask(
            task_id="t1",
            task_name="Low Priority Task",
            priority_level="Low",
            priority_score=0.25,
            priority_rationale="Can wait"
        )
        
        level = agent._determine_granularity_level(task)
        assert level == 0  # Low priority tasks don't need breakdown
    
    def test_determine_granularity_level_already_granular(self):
        """Test granularity level for already granular tasks"""
        agent = GranularityAgentCore()
        
        task = PrioritizedTask(
            task_id="t1",
            task_name="Confirm venue booking",
            priority_level="High",
            priority_score=0.75,
            priority_rationale="Important"
        )
        
        level = agent._determine_granularity_level(task)
        assert level == 0  # Already granular (contains 'confirm')
    
    def test_estimate_duration_venue(self, sample_state):
        """Test duration estimation for venue tasks"""
        agent = GranularityAgentCore()
        
        task = PrioritizedTask(
            task_id="t1",
            task_name="Venue Setup - Grand Ballroom",
            priority_level="High",
            priority_score=0.75,
            priority_rationale="Important"
        )
        
        duration = agent._estimate_duration(task, sample_state['client_request'], 0)
        
        # Venue tasks should be around 4 hours base
        assert duration.total_seconds() > 0
        assert duration.total_seconds() / 3600 >= 4  # At least 4 hours
    
    def test_estimate_duration_catering(self, sample_state):
        """Test duration estimation for catering tasks"""
        agent = GranularityAgentCore()
        
        task = PrioritizedTask(
            task_id="t1",
            task_name="Catering Coordination",
            priority_level="High",
            priority_score=0.75,
            priority_rationale="Important"
        )
        
        duration = agent._estimate_duration(task, sample_state['client_request'], 0)
        
        # Catering tasks should be around 6 hours base
        assert duration.total_seconds() > 0
        assert duration.total_seconds() / 3600 >= 6  # At least 6 hours
    
    def test_estimate_duration_with_large_guest_count(self):
        """Test duration estimation adjusts for large guest count"""
        agent = GranularityAgentCore()
        
        task = PrioritizedTask(
            task_id="t1",
            task_name="Venue Setup",
            priority_level="High",
            priority_score=0.75,
            priority_rationale="Important"
        )
        
        small_event = {'guest_count': 50}
        large_event = {'guest_count': 250}
        
        small_duration = agent._estimate_duration(task, small_event, 0)
        large_duration = agent._estimate_duration(task, large_event, 0)
        
        # Large events should take longer
        assert large_duration > small_duration
    
    def test_estimate_duration_from_description_quick(self, sample_state):
        """Test duration estimation for quick tasks"""
        agent = GranularityAgentCore()
        
        duration = agent._estimate_duration_from_description(
            "Confirm venue booking",
            "Quick confirmation call",
            sample_state['client_request']
        )
        
        # Quick tasks should be under 1 hour
        assert duration.total_seconds() / 3600 <= 1
    
    def test_estimate_duration_from_description_medium(self, sample_state):
        """Test duration estimation for medium tasks"""
        agent = GranularityAgentCore()
        
        duration = agent._estimate_duration_from_description(
            "Coordinate catering setup",
            "Discuss menu and timing",
            sample_state['client_request']
        )
        
        # Medium tasks should be 1-2 hours
        hours = duration.total_seconds() / 3600
        assert 1 <= hours <= 2
    
    def test_estimate_duration_from_description_long(self, sample_state):
        """Test duration estimation for long tasks"""
        agent = GranularityAgentCore()
        
        duration = agent._estimate_duration_from_description(
            "Setup venue decorations",
            "Install and arrange all decorations",
            sample_state['client_request']
        )
        
        # Long tasks should be 2-4 hours
        hours = duration.total_seconds() / 3600
        assert hours >= 2
    
    def test_fallback_decomposition_venue(self, sample_state):
        """Test fallback decomposition for venue tasks"""
        agent = GranularityAgentCore()
        
        task = PrioritizedTask(
            task_id="t1",
            task_name="Venue Setup - Grand Ballroom",
            priority_level="High",
            priority_score=0.75,
            priority_rationale="Important"
        )
        
        sub_tasks = agent._fallback_decomposition(task, sample_state['client_request'])
        
        assert len(sub_tasks) > 0
        assert all('name' in st and 'description' in st for st in sub_tasks)
        # Should have venue-specific sub-tasks
        assert any('venue' in st['name'].lower() for st in sub_tasks)
    
    def test_fallback_decomposition_catering(self, sample_state):
        """Test fallback decomposition for catering tasks"""
        agent = GranularityAgentCore()
        
        task = PrioritizedTask(
            task_id="t1",
            task_name="Catering Coordination",
            priority_level="High",
            priority_score=0.75,
            priority_rationale="Important"
        )
        
        sub_tasks = agent._fallback_decomposition(task, sample_state['client_request'])
        
        assert len(sub_tasks) > 0
        # Should have catering-specific sub-tasks
        assert any('menu' in st['name'].lower() or 'cater' in st['description'].lower() 
                  for st in sub_tasks)
    
    def test_fallback_decomposition_photography(self, sample_state):
        """Test fallback decomposition for photography tasks"""
        agent = GranularityAgentCore()
        
        task = PrioritizedTask(
            task_id="t1",
            task_name="Photography Session",
            priority_level="Medium",
            priority_score=0.55,
            priority_rationale="Standard priority"
        )
        
        sub_tasks = agent._fallback_decomposition(task, sample_state['client_request'])
        
        assert len(sub_tasks) > 0
        # Should have photography-specific sub-tasks
        assert any('photo' in st['name'].lower() or 'shot' in st['name'].lower() 
                  for st in sub_tasks)
    
    def test_fallback_decomposition_generic(self, sample_state):
        """Test fallback decomposition for generic tasks"""
        agent = GranularityAgentCore()
        
        task = PrioritizedTask(
            task_id="t1",
            task_name="Generic Task",
            priority_level="Medium",
            priority_score=0.55,
            priority_rationale="Standard priority"
        )
        
        sub_tasks = agent._fallback_decomposition(task, sample_state['client_request'])
        
        assert len(sub_tasks) > 0
        # Should have generic sub-tasks (plan, coordinate, execute, verify)
        assert len(sub_tasks) == 4
    
    def test_parse_decomposition_response_valid(self):
        """Test parsing valid LLM decomposition response"""
        agent = GranularityAgentCore()
        
        task = PrioritizedTask(
            task_id="t1",
            task_name="Test Task",
            priority_level="High",
            priority_score=0.75,
            priority_rationale="Test"
        )
        
        response = """
Sub-task 1: First sub-task
Description: Description of first sub-task

Sub-task 2: Second sub-task
Description: Description of second sub-task

Sub-task 3: Third sub-task
Description: Description of third sub-task
"""
        
        sub_tasks = agent._parse_decomposition_response(response, task)
        
        assert len(sub_tasks) == 3
        assert sub_tasks[0]['name'] == 'First sub-task'
        assert sub_tasks[0]['description'] == 'Description of first sub-task'
        assert sub_tasks[1]['name'] == 'Second sub-task'
        assert sub_tasks[2]['name'] == 'Third sub-task'
    
    def test_parse_decomposition_response_invalid(self):
        """Test parsing invalid LLM response falls back to rule-based"""
        agent = GranularityAgentCore()
        
        task = PrioritizedTask(
            task_id="t1",
            task_name="Venue Setup",
            priority_level="High",
            priority_score=0.75,
            priority_rationale="Test"
        )
        
        response = "This is not a valid response format"
        
        sub_tasks = agent._parse_decomposition_response(response, task)
        
        # Should fall back to rule-based decomposition
        assert len(sub_tasks) > 0
        assert all('name' in st and 'description' in st for st in sub_tasks)
    
    def test_create_default_granular_task(self):
        """Test creation of default granular task on error"""
        agent = GranularityAgentCore()
        
        task = PrioritizedTask(
            task_id="t1",
            task_name="Test Task",
            priority_level="High",
            priority_score=0.75,
            priority_rationale="Test rationale"
        )
        
        error_msg = "Test error message"
        default_task = agent._create_default_granular_task(task, error_msg)
        
        assert isinstance(default_task, GranularTask)
        assert default_task.task_id == "t1"
        assert default_task.parent_task_id is None
        assert default_task.granularity_level == GranularityAgentCore.LEVEL_TOP
        assert error_msg in default_task.task_description
        assert default_task.estimated_duration > timedelta(0)
    
    @pytest.mark.asyncio
    async def test_decompose_tasks_with_error_handling(self, sample_state, mock_llm_manager):
        """Test that decomposition continues even if one task fails"""
        agent = GranularityAgentCore()
        agent.llm_manager = mock_llm_manager
        
        # Create tasks where one will fail
        tasks = [
            PrioritizedTask(
                task_id="t1",
                task_name="Valid Task",
                priority_level="High",
                priority_score=0.75,
                priority_rationale="Test"
            ),
            PrioritizedTask(
                task_id="t2",
                task_name="Task That Will Fail",
                priority_level="Critical",
                priority_score=0.95,
                priority_rationale="Test"
            )
        ]
        
        # Mock LLM to fail on second task
        call_count = [0]
        
        async def mock_generate(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 2:
                raise Exception("LLM error")
            return """
Sub-task 1: Test sub-task
Description: Test description
"""
        
        mock_llm_manager.generate_response.side_effect = mock_generate
        
        result = await agent.decompose_tasks(tasks, sample_state)
        
        # Should still return results for both tasks (with fallback for failed one)
        assert len(result) > 0
    
    def test_extract_event_context(self, sample_state):
        """Test extraction of event context from state"""
        agent = GranularityAgentCore()
        
        context = agent._extract_event_context(sample_state)
        
        assert context['event_type'] == 'wedding'
        assert context['guest_count'] == 150
        assert context['budget'] == 50000
        assert context['location'] == 'Mumbai'
        assert 'preferences' in context
        assert 'requirements' in context
        assert 'selected_combination' in context


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
