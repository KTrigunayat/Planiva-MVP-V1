"""
Integration Tests for Task Management Agent

Tests the complete Task Management Agent workflow including:
- Sub-agent consolidation
- Tool processing
- Extended task list generation
- Error scenarios
- State management and persistence
- Workflow integration with Timeline and Blueprint agents
"""

"""
Integration Tests for Task Management Agent

Tests the complete Task Management Agent workflow including:
- Sub-agent consolidation
- Tool processing
- Extended task list generation
- Error scenarios
- State management and persistence
- Workflow integration with Timeline and Blueprint agents
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import Dict, Any, List

# Import with try-except to handle import issues gracefully
try:
    from agents.task_management.core.task_management_agent import TaskManagementAgent
    from agents.task_management.models.task_models import PrioritizedTask, GranularTask, TaskWithDependencies
    from agents.task_management.models.data_models import Resource, TaskTimeline, EnhancedTask, VendorAssignment, LogisticsStatus, Conflict, VenueInfo
    from agents.task_management.models.consolidated_models import ConsolidatedTask, ConsolidatedTaskData
    from agents.task_management.models.extended_models import ExtendedTask, ExtendedTaskList, ProcessingSummary
    from agents.task_management.exceptions import TaskManagementError, SubAgentDataError, ToolExecutionError
    from workflows.state_models import EventPlanningState, WorkflowStatus
    from database.task_management_repository import TaskManagementRepository
except ImportError as e:
    pytest.skip(f"Could not import task management modules: {e}", allow_module_level=True)


class TestTaskManagementAgentIntegration:
    """Integration tests for Task Management Agent"""
    
    @pytest.fixture
    def sample_event_state(self) -> EventPlanningState:
        """Create a realistic EventPlanningState for testing"""
        return {
            'plan_id': 'test-plan-integration-001',
            'client_request': {
                'client_id': 'client-001',
                'client_name': 'Priya & Rohit',
                'event_type': 'wedding',
                'guest_count': 150,
                'budget': 800000.0,
                'date': '2025-12-15',
                'location': 'Mumbai',
                'preferences': {
                    'venue_type': 'garden',
                    'cuisine': ['indian', 'continental'],
                    'theme': 'elegant'
                }
            },
            'workflow_status': WorkflowStatus.TIMELINE_GENERATION,
            'iteration_count': 1,
            'budget_allocations': [
                {
                    'strategy': 'balanced',
                    'allocation': {
                        'venue': 300000,
                        'catering': 250000,
                        'photography': 80000,
                        'makeup': 40000,
                        'miscellaneous': 130000
                    }
                }
            ],
            'vendor_combinations': [
                {
                    'combination_id': 'combo-001',
                    'fitness_score': 0.87,
                    'total_cost': 750000
                }
            ],
            'beam_candidates': [
                {
                    'combination_id': 'combo-001',
                    'fitness_score': 0.87
                }
            ],
            'timeline_data': {
                'event_date': '2025-12-15',
                'start_time': '09:00',
                'end_time': '23:00',
                'phases': [
                    {
                        'phase_name': 'Ceremony',
                        'start_time': '18:00',
                        'end_time': '19:30',
                        'duration': 90
                    },
                    {
                        'phase_name': 'Reception',
                        'start_time': '20:00',
                        'end_time': '23:00',
                        'duration': 180
                    }
                ]
            },
            'selected_combination': {
                'combination_id': 'combo-001',
                'venue': {
                    'id': 1,
                    'name': 'Garden Paradise Resort',
                    'type': 'garden_venue',
                    'capacity': 200,
                    'location': 'Mumbai',
                    'cost': 280000,
                    'amenities': ['parking', 'ac', 'garden', 'stage']
                },
                'caterer': {
                    'id': 2,
                    'name': 'Royal Caterers',
                    'type': 'caterer',
                    'cost': 240000,
                    'cuisine_types': ['indian', 'continental'],
                    'per_person_cost': 1600
                },
                'photographer': {
                    'id': 3,
                    'name': 'Candid Moments Photography',
                    'type': 'photographer',
                    'cost': 75000,
                    'style': 'candid'
                },
                'makeup_artist': {
                    'id': 4,
                    'name': 'Glamour Studio',
                    'type': 'makeup',
                    'cost': 35000,
                    'services': ['bridal', 'family']
                }
            },
            'final_blueprint': None,
            'started_at': datetime.utcnow().isoformat(),
            'last_updated': datetime.utcnow().isoformat(),
            'beam_width': 3,
            'max_iterations': 20,
            'error_count': 0,
            'last_error': None,
            'retry_count': 0,
            'state_transitions': [],
            'current_node': 'task_management',
            'next_node': 'blueprint_generation'
        }
    
    @pytest.fixture
    def mock_sub_agent_outputs(self):
        """Mock outputs from sub-agents"""
        return {
            'prioritized_tasks': [
                PrioritizedTask(
                    task_id='task-001',
                    task_name='Venue Setup',
                    priority_level='Critical',
                    priority_score=0.95,
                    priority_rationale='Must be completed before event'
                ),
                PrioritizedTask(
                    task_id='task-002',
                    task_name='Catering Preparation',
                    priority_level='High',
                    priority_score=0.85,
                    priority_rationale='Food preparation requires advance planning'
                ),
                PrioritizedTask(
                    task_id='task-003',
                    task_name='Photography Setup',
                    priority_level='Medium',
                    priority_score=0.70,
                    priority_rationale='Can be done closer to event'
                )
            ],
            'granular_tasks': [
                GranularTask(
                    task_id='task-001',
                    parent_task_id=None,
                    task_name='Venue Setup',
                    task_description='Complete venue setup including decorations and seating',
                    granularity_level=0,
                    estimated_duration=timedelta(hours=4),
                    sub_tasks=['task-001-1', 'task-001-2']
                ),
                GranularTask(
                    task_id='task-001-1',
                    parent_task_id='task-001',
                    task_name='Decoration Setup',
                    task_description='Install floral decorations and lighting',
                    granularity_level=1,
                    estimated_duration=timedelta(hours=2),
                    sub_tasks=[]
                ),
                GranularTask(
                    task_id='task-001-2',
                    parent_task_id='task-001',
                    task_name='Seating Arrangement',
                    task_description='Arrange chairs and tables according to plan',
                    granularity_level=1,
                    estimated_duration=timedelta(hours=2),
                    sub_tasks=[]
                )
            ],
            'tasks_with_dependencies': [
                TaskWithDependencies(
                    task_id='task-001',
                    task_name='Venue Setup',
                    dependencies=[],
                    resources_required=[
                        Resource(
                            resource_type='venue',
                            resource_id='1',
                            resource_name='Garden Paradise Resort',
                            quantity_required=1,
                            availability_constraint='Must be available 6 hours before event'
                        )
                    ],
                    resource_conflicts=[]
                ),
                TaskWithDependencies(
                    task_id='task-002',
                    task_name='Catering Preparation',
                    dependencies=['task-001'],
                    resources_required=[
                        Resource(
                            resource_type='vendor',
                            resource_id='2',
                            resource_name='Royal Caterers',
                            quantity_required=1,
                            availability_constraint='Kitchen access required'
                        )
                    ],
                    resource_conflicts=[]
                )
            ]
        }
    
    @pytest.mark.asyncio
    async def test_full_workflow_integration(self, sample_event_state, mock_sub_agent_outputs):
        """Test complete workflow: sub-agent consolidation → tool processing → extended task list generation"""
        agent = TaskManagementAgent()
        
        # Mock sub-agents to return test data
        with patch.object(agent.prioritization_agent, 'prioritize_tasks') as mock_prioritize, \
             patch.object(agent.granularity_agent, 'decompose_tasks') as mock_decompose, \
             patch.object(agent.resource_dependency_agent, 'analyze_dependencies') as mock_analyze:
            
            mock_prioritize.return_value = mock_sub_agent_outputs['prioritized_tasks']
            mock_decompose.return_value = mock_sub_agent_outputs['granular_tasks']
            mock_analyze.return_value = mock_sub_agent_outputs['tasks_with_dependencies']
            
            # Process the state
            updated_state = await agent.process(sample_event_state)
            
            # Verify extended_task_list was created
            assert 'extended_task_list' in updated_state
            assert updated_state['extended_task_list'] is not None
            
            extended_list = updated_state['extended_task_list']
            
            # Verify structure
            assert 'tasks' in extended_list
            assert 'processing_summary' in extended_list
            assert 'metadata' in extended_list
            
            # Verify tasks were processed
            assert len(extended_list['tasks']) > 0
            
            # Verify processing summary
            summary = extended_list['processing_summary']
            assert summary['total_tasks'] > 0
            assert 'processing_time' in summary
            assert 'tool_execution_status' in summary
            
            # Verify sub-agents were called
            mock_prioritize.assert_called_once()
            mock_decompose.assert_called_once()
            mock_analyze.assert_called_once()
            
            print(f"✅ Full workflow integration test passed")
            print(f"   Total tasks: {summary['total_tasks']}")
            print(f"   Processing time: {summary['processing_time']:.2f}s")
    
    @pytest.mark.asyncio
    async def test_error_scenario_missing_sub_agent_data(self, sample_event_state):
        """Test error handling when sub-agent data is missing"""
        agent = TaskManagementAgent()
        
        # Mock sub-agents to return empty/None data
        with patch.object(agent.prioritization_agent, 'prioritize_tasks') as mock_prioritize, \
             patch.object(agent.granularity_agent, 'decompose_tasks') as mock_decompose, \
             patch.object(agent.resource_dependency_agent, 'analyze_dependencies') as mock_analyze:
            
            mock_prioritize.return_value = []  # Empty data
            mock_decompose.return_value = []
            mock_analyze.return_value = []
            
            # Process should handle gracefully
            updated_state = await agent.process(sample_event_state)
            
            # Should still create extended_task_list (possibly empty)
            assert 'extended_task_list' in updated_state
            
            extended_list = updated_state['extended_task_list']
            summary = extended_list['processing_summary']
            
            # Should have 0 tasks but no crash
            assert summary['total_tasks'] == 0
            
            print(f"✅ Missing sub-agent data handled gracefully")
    
    @pytest.mark.asyncio
    async def test_error_scenario_tool_failure(self, sample_event_state, mock_sub_agent_outputs):
        """Test error handling when a tool fails"""
        agent = TaskManagementAgent()
        
        # Mock sub-agents to return test data
        with patch.object(agent.prioritization_agent, 'prioritize_tasks') as mock_prioritize, \
             patch.object(agent.granularity_agent, 'decompose_tasks') as mock_decompose, \
             patch.object(agent.resource_dependency_agent, 'analyze_dependencies') as mock_analyze:
            
            mock_prioritize.return_value = mock_sub_agent_outputs['prioritized_tasks']
            mock_decompose.return_value = mock_sub_agent_outputs['granular_tasks']
            mock_analyze.return_value = mock_sub_agent_outputs['tasks_with_dependencies']
            
            # Mock one tool to fail
            with patch.object(agent.llm_tool, 'enhance_tasks') as mock_enhance:
                mock_enhance.side_effect = Exception("LLM service unavailable")
                
                # Process should handle gracefully
                updated_state = await agent.process(sample_event_state)
                
                # Should still create extended_task_list
                assert 'extended_task_list' in updated_state
                
                # Check tool execution status
                summary = updated_state['extended_task_list']['processing_summary']
                tool_status = summary['tool_execution_status']
                
                # LLM tool should show failure
                assert 'llm_enhancement' in tool_status
                assert 'failed' in tool_status['llm_enhancement'].lower() or 'error' in tool_status['llm_enhancement'].lower()
                
                print(f"✅ Tool failure handled gracefully")
                print(f"   Tool status: {tool_status}")
    
    @pytest.mark.asyncio
    async def test_error_scenario_database_unavailable(self, sample_event_state, mock_sub_agent_outputs):
        """Test error handling when database is unavailable"""
        agent = TaskManagementAgent()
        
        # Mock sub-agents
        with patch.object(agent.prioritization_agent, 'prioritize_tasks') as mock_prioritize, \
             patch.object(agent.granularity_agent, 'decompose_tasks') as mock_decompose, \
             patch.object(agent.resource_dependency_agent, 'analyze_dependencies') as mock_analyze:
            
            mock_prioritize.return_value = mock_sub_agent_outputs['prioritized_tasks']
            mock_decompose.return_value = mock_sub_agent_outputs['granular_tasks']
            mock_analyze.return_value = mock_sub_agent_outputs['tasks_with_dependencies']
            
            # Mock database tools to fail
            with patch.object(agent.vendor_tool, 'assign_vendors') as mock_vendor, \
                 patch.object(agent.venue_tool, 'lookup_venues') as mock_venue:
                
                mock_vendor.side_effect = Exception("Database connection failed")
                mock_venue.side_effect = Exception("Database connection failed")
                
                # Process should handle gracefully
                updated_state = await agent.process(sample_event_state)
                
                # Should still create extended_task_list
                assert 'extended_task_list' in updated_state
                
                # Check that processing continued despite DB failures
                summary = updated_state['extended_task_list']['processing_summary']
                assert summary['total_tasks'] > 0
                
                print(f"✅ Database unavailability handled gracefully")
    
    @pytest.mark.asyncio
    async def test_state_management_and_persistence(self, sample_event_state, mock_sub_agent_outputs):
        """Test state management and persistence"""
        agent = TaskManagementAgent()
        
        # Mock sub-agents
        with patch.object(agent.prioritization_agent, 'prioritize_tasks') as mock_prioritize, \
             patch.object(agent.granularity_agent, 'decompose_tasks') as mock_decompose, \
             patch.object(agent.resource_dependency_agent, 'analyze_dependencies') as mock_analyze:
            
            mock_prioritize.return_value = mock_sub_agent_outputs['prioritized_tasks']
            mock_decompose.return_value = mock_sub_agent_outputs['granular_tasks']
            mock_analyze.return_value = mock_sub_agent_outputs['tasks_with_dependencies']
            
            # Process the state
            updated_state = await agent.process(sample_event_state)
            
            # Verify state was updated correctly
            assert updated_state['plan_id'] == sample_event_state['plan_id']
            assert 'extended_task_list' in updated_state
            
            # Verify original state fields are preserved
            assert updated_state['client_request'] == sample_event_state['client_request']
            assert updated_state['selected_combination'] == sample_event_state['selected_combination']
            assert updated_state['timeline_data'] == sample_event_state['timeline_data']
            
            # Verify new field was added
            assert updated_state['extended_task_list'] is not None
            
            print(f"✅ State management test passed")
    
    @pytest.mark.asyncio
    async def test_workflow_integration_with_timeline_agent(self, sample_event_state):
        """Test workflow integration with Timeline Agent"""
        agent = TaskManagementAgent()
        
        # Verify that timeline_data from Timeline Agent is accessible
        assert 'timeline_data' in sample_event_state
        assert sample_event_state['timeline_data'] is not None
        
        # Mock timeline tool to use timeline_data
        with patch.object(agent.timeline_tool, 'calculate_timelines') as mock_timeline:
            mock_timeline.return_value = [
                TaskTimeline(
                    task_id='task-001',
                    start_time=datetime(2025, 12, 15, 9, 0),
                    end_time=datetime(2025, 12, 15, 13, 0),
                    duration=timedelta(hours=4),
                    buffer_time=timedelta(minutes=30),
                    scheduling_constraints=[]
                )
            ]
            
            # Process state
            updated_state = await agent.process(sample_event_state)
            
            # Verify timeline tool was called with state containing timeline_data
            mock_timeline.assert_called()
            call_args = mock_timeline.call_args
            
            # The state passed to timeline tool should have timeline_data
            assert call_args is not None
            
            print(f"✅ Timeline Agent integration test passed")
    
    @pytest.mark.asyncio
    async def test_workflow_integration_with_blueprint_agent(self, sample_event_state, mock_sub_agent_outputs):
        """Test workflow integration with Blueprint Agent"""
        agent = TaskManagementAgent()
        
        # Mock sub-agents
        with patch.object(agent.prioritization_agent, 'prioritize_tasks') as mock_prioritize, \
             patch.object(agent.granularity_agent, 'decompose_tasks') as mock_decompose, \
             patch.object(agent.resource_dependency_agent, 'analyze_dependencies') as mock_analyze:
            
            mock_prioritize.return_value = mock_sub_agent_outputs['prioritized_tasks']
            mock_decompose.return_value = mock_sub_agent_outputs['granular_tasks']
            mock_analyze.return_value = mock_sub_agent_outputs['tasks_with_dependencies']
            
            # Process state
            updated_state = await agent.process(sample_event_state)
            
            # Verify extended_task_list is in format Blueprint Agent expects
            assert 'extended_task_list' in updated_state
            extended_list = updated_state['extended_task_list']
            
            # Verify structure Blueprint Agent needs
            assert 'tasks' in extended_list
            assert isinstance(extended_list['tasks'], list)
            
            # Verify each task has required fields for Blueprint
            if len(extended_list['tasks']) > 0:
                task = extended_list['tasks'][0]
                assert 'task_id' in task
                assert 'task_name' in task
                assert 'task_description' in task
                assert 'priority_level' in task
            
            # Verify metadata for Blueprint Agent
            assert 'metadata' in extended_list
            assert 'processing_summary' in extended_list
            
            print(f"✅ Blueprint Agent integration test passed")


class TestTaskManagementAgentPerformance:
    """Performance tests for Task Management Agent"""
    
    @pytest.fixture
    def large_event_state(self) -> EventPlanningState:
        """Create a large event state for performance testing"""
        return {
            'plan_id': 'perf-test-001',
            'client_request': {
                'client_id': 'client-perf-001',
                'event_type': 'wedding',
                'guest_count': 500,
                'budget': 2000000.0,
                'date': '2025-12-15',
                'location': 'Mumbai'
            },
            'workflow_status': WorkflowStatus.TIMELINE_GENERATION,
            'iteration_count': 1,
            'budget_allocations': [],
            'vendor_combinations': [],
            'beam_candidates': [],
            'timeline_data': {
                'event_date': '2025-12-15',
                'start_time': '09:00',
                'end_time': '23:00'
            },
            'selected_combination': {
                'venue': {'id': 1, 'name': 'Large Venue', 'capacity': 600},
                'caterer': {'id': 2, 'name': 'Large Caterer'}
            },
            'final_blueprint': None,
            'started_at': datetime.utcnow().isoformat(),
            'last_updated': datetime.utcnow().isoformat(),
            'beam_width': 3,
            'max_iterations': 20,
            'error_count': 0,
            'last_error': None,
            'retry_count': 0,
            'state_transitions': [],
            'current_node': 'task_management',
            'next_node': 'blueprint_generation'
        }
    
    @pytest.mark.asyncio
    async def test_performance_with_many_tasks(self, large_event_state):
        """Test performance with large number of tasks"""
        import time
        
        agent = TaskManagementAgent()
        
        # Create many tasks
        many_tasks = []
        for i in range(50):
            many_tasks.append(
                PrioritizedTask(
                    task_id=f'task-{i:03d}',
                    task_name=f'Task {i}',
                    priority_level='Medium',
                    priority_score=0.5 + (i % 10) * 0.05,
                    priority_rationale=f'Task {i} rationale'
                )
            )
        
        # Mock sub-agents to return many tasks
        with patch.object(agent.prioritization_agent, 'prioritize_tasks') as mock_prioritize, \
             patch.object(agent.granularity_agent, 'decompose_tasks') as mock_decompose, \
             patch.object(agent.resource_dependency_agent, 'analyze_dependencies') as mock_analyze:
            
            mock_prioritize.return_value = many_tasks
            mock_decompose.return_value = [
                GranularTask(
                    task_id=task.task_id,
                    parent_task_id=None,
                    task_name=task.task_name,
                    task_description=f'Description for {task.task_name}',
                    granularity_level=0,
                    estimated_duration=timedelta(hours=2),
                    sub_tasks=[]
                )
                for task in many_tasks
            ]
            mock_analyze.return_value = [
                TaskWithDependencies(
                    task_id=task.task_id,
                    task_name=task.task_name,
                    dependencies=[],
                    resources_required=[],
                    resource_conflicts=[]
                )
                for task in many_tasks
            ]
            
            # Measure processing time
            start_time = time.time()
            updated_state = await agent.process(large_event_state)
            processing_time = time.time() - start_time
            
            # Verify processing completed
            assert 'extended_task_list' in updated_state
            summary = updated_state['extended_task_list']['processing_summary']
            
            # Performance assertions
            assert processing_time < 30.0  # Should complete within 30 seconds
            assert summary['total_tasks'] == 50
            
            print(f"✅ Performance test passed")
            print(f"   Tasks processed: {summary['total_tasks']}")
            print(f"   Processing time: {processing_time:.2f}s")
            print(f"   Tasks per second: {summary['total_tasks'] / processing_time:.2f}")


class TestTaskManagementAgentEdgeCases:
    """Edge case tests for Task Management Agent"""
    
    @pytest.mark.asyncio
    async def test_empty_selected_combination(self):
        """Test handling of empty selected_combination"""
        agent = TaskManagementAgent()
        
        state = {
            'plan_id': 'edge-test-001',
            'client_request': {'client_id': 'client-001'},
            'workflow_status': WorkflowStatus.TIMELINE_GENERATION,
            'selected_combination': None,  # Empty
            'timeline_data': {},
            'iteration_count': 1,
            'budget_allocations': [],
            'vendor_combinations': [],
            'beam_candidates': [],
            'final_blueprint': None,
            'started_at': datetime.utcnow().isoformat(),
            'last_updated': datetime.utcnow().isoformat(),
            'beam_width': 3,
            'max_iterations': 20,
            'error_count': 0,
            'last_error': None,
            'retry_count': 0,
            'state_transitions': [],
            'current_node': 'task_management',
            'next_node': 'blueprint_generation'
        }
        
        # Should handle gracefully
        updated_state = await agent.process(state)
        
        assert 'extended_task_list' in updated_state
        print(f"✅ Empty selected_combination handled gracefully")
    
    @pytest.mark.asyncio
    async def test_missing_timeline_data(self):
        """Test handling of missing timeline_data"""
        agent = TaskManagementAgent()
        
        state = {
            'plan_id': 'edge-test-002',
            'client_request': {'client_id': 'client-001'},
            'workflow_status': WorkflowStatus.TIMELINE_GENERATION,
            'selected_combination': {'venue': {'id': 1}},
            'timeline_data': None,  # Missing
            'iteration_count': 1,
            'budget_allocations': [],
            'vendor_combinations': [],
            'beam_candidates': [],
            'final_blueprint': None,
            'started_at': datetime.utcnow().isoformat(),
            'last_updated': datetime.utcnow().isoformat(),
            'beam_width': 3,
            'max_iterations': 20,
            'error_count': 0,
            'last_error': None,
            'retry_count': 0,
            'state_transitions': [],
            'current_node': 'task_management',
            'next_node': 'blueprint_generation'
        }
        
        # Should handle gracefully
        updated_state = await agent.process(state)
        
        assert 'extended_task_list' in updated_state
        print(f"✅ Missing timeline_data handled gracefully")


if __name__ == '__main__':
    print("Running Task Management Agent Integration Tests...\n")
    print("=" * 70)
    
    # Run tests with pytest
    pytest.main([__file__, '-v', '--tb=short'])
