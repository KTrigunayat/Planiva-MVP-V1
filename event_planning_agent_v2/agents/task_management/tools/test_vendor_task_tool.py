"""
Test suite for VendorTaskTool

Tests vendor assignment functionality including:
- Vendor extraction from selected combination
- Task-vendor matching
- Manual assignment flagging
- Database integration
"""

import pytest
from datetime import timedelta
from unittest.mock import Mock, MagicMock, patch

from .vendor_task_tool import VendorTaskTool
from ..models.data_models import Resource, VendorAssignment
from ..models.task_models import PrioritizedTask, GranularTask, TaskWithDependencies
from ..models.consolidated_models import ConsolidatedTask, ConsolidatedTaskData
from ..exceptions import ToolExecutionError


@pytest.fixture
def mock_db_manager():
    """Mock database manager"""
    manager = Mock()
    session = MagicMock()
    manager.get_sync_session.return_value.__enter__ = Mock(return_value=session)
    manager.get_sync_session.return_value.__exit__ = Mock(return_value=None)
    return manager


@pytest.fixture
def vendor_task_tool(mock_db_manager):
    """Create VendorTaskTool instance with mocked dependencies"""
    with patch('event_planning_agent_v2.agents.task_management.tools.vendor_task_tool.get_connection_manager', return_value=mock_db_manager):
        tool = VendorTaskTool(db_connection=mock_db_manager, use_mcp=False)
        return tool


@pytest.fixture
def sample_state():
    """Sample EventPlanningState with selected combination"""
    return {
        'plan_id': 'test-plan-123',
        'client_request': {
            'client_id': 'client-1',
            'event_type': 'wedding',
            'guest_count': 200,
            'budget': 500000,
            'date': '2024-12-15',
            'location': 'Mumbai'
        },
        'selected_combination': {
            'combination_id': 'combo-1',
            'venue': {
                'vendor_id': 'venue-1',
                'name': 'Grand Palace Hotel',
                'location_city': 'Mumbai',
                'max_seating_capacity': 300,
                'rental_cost': 150000
            },
            'caterer': {
                'vendor_id': 'caterer-1',
                'name': 'Royal Caterers',
                'location_city': 'Mumbai',
                'min_veg_price': 800,
                'veg_only': False
            },
            'photographer': {
                'vendor_id': 'photographer-1',
                'name': 'Perfect Moments Photography',
                'location_city': 'Mumbai',
                'photo_package_price': 50000,
                'video_available': True
            },
            'makeup_artist': {
                'vendor_id': 'makeup-1',
                'name': 'Glamour Studio',
                'location_city': 'Mumbai',
                'bridal_makeup_price': 25000,
                'on_site_service': True
            },
            'fitness_score': 0.85,
            'total_cost': 450000
        },
        'workflow_status': 'client_selection'
    }


@pytest.fixture
def sample_tasks():
    """Sample consolidated tasks"""
    tasks = [
        ConsolidatedTask(
            task_id='task-1',
            task_name='Venue Setup and Decoration',
            priority_level='Critical',
            priority_score=0.95,
            priority_rationale='Essential for event success',
            parent_task_id=None,
            task_description='Set up venue with decorations, seating arrangements, and stage',
            granularity_level=0,
            estimated_duration=timedelta(hours=6),
            sub_tasks=['task-1-1', 'task-1-2'],
            dependencies=[],
            resources_required=[
                Resource(
                    resource_type='vendor',
                    resource_id='venue-1',
                    resource_name='Venue',
                    quantity_required=1
                )
            ],
            resource_conflicts=[]
        ),
        ConsolidatedTask(
            task_id='task-2',
            task_name='Catering Menu Finalization',
            priority_level='High',
            priority_score=0.85,
            priority_rationale='Important for guest satisfaction',
            parent_task_id=None,
            task_description='Finalize menu with caterer, including vegetarian and non-vegetarian options',
            granularity_level=0,
            estimated_duration=timedelta(hours=2),
            sub_tasks=[],
            dependencies=[],
            resources_required=[
                Resource(
                    resource_type='vendor',
                    resource_id='caterer-1',
                    resource_name='Caterer',
                    quantity_required=1
                )
            ],
            resource_conflicts=[]
        ),
        ConsolidatedTask(
            task_id='task-3',
            task_name='Photography and Videography Coverage',
            priority_level='High',
            priority_score=0.80,
            priority_rationale='Captures memories of the event',
            parent_task_id=None,
            task_description='Coordinate with photographer for photo and video coverage throughout the event',
            granularity_level=0,
            estimated_duration=timedelta(hours=8),
            sub_tasks=[],
            dependencies=[],
            resources_required=[
                Resource(
                    resource_type='vendor',
                    resource_id='photographer-1',
                    resource_name='Photographer',
                    quantity_required=1
                )
            ],
            resource_conflicts=[]
        ),
        ConsolidatedTask(
            task_id='task-4',
            task_name='Bridal Makeup Trial',
            priority_level='Medium',
            priority_score=0.70,
            priority_rationale='Ensures bride is satisfied with look',
            parent_task_id=None,
            task_description='Schedule and conduct makeup trial with bride',
            granularity_level=0,
            estimated_duration=timedelta(hours=2),
            sub_tasks=[],
            dependencies=[],
            resources_required=[
                Resource(
                    resource_type='vendor',
                    resource_id='makeup-1',
                    resource_name='Makeup Artist',
                    quantity_required=1
                )
            ],
            resource_conflicts=[]
        ),
        ConsolidatedTask(
            task_id='task-5',
            task_name='Guest List Management',
            priority_level='Medium',
            priority_score=0.65,
            priority_rationale='Organizational task',
            parent_task_id=None,
            task_description='Manage guest list, RSVPs, and seating arrangements',
            granularity_level=0,
            estimated_duration=timedelta(hours=4),
            sub_tasks=[],
            dependencies=[],
            resources_required=[],
            resource_conflicts=[]
        )
    ]
    
    return ConsolidatedTaskData(
        tasks=tasks,
        event_context={'event_type': 'wedding', 'guest_count': 200},
        processing_metadata={'timestamp': '2024-01-15T10:00:00'}
    )


class TestVendorTaskTool:
    """Test suite for VendorTaskTool"""
    
    def test_initialization(self, vendor_task_tool):
        """Test tool initialization"""
        assert vendor_task_tool is not None
        assert vendor_task_tool.use_mcp is False
        assert vendor_task_tool.mcp_available is False
    
    def test_extract_vendors_from_combination(self, vendor_task_tool, sample_state):
        """Test vendor extraction from selected combination"""
        selected_combination = sample_state['selected_combination']
        vendors = vendor_task_tool._extract_vendors_from_combination(selected_combination)
        
        assert len(vendors) == 4
        assert 'venue' in vendors
        assert 'caterer' in vendors
        assert 'photographer' in vendors
        assert 'makeup_artist' in vendors
        
        # Check venue details
        assert vendors['venue']['name'] == 'Grand Palace Hotel'
        assert vendors['venue']['vendor_type'] == 'venue'
        assert vendors['venue']['vendor_id'] == 'venue-1'
    
    def test_identify_required_vendor_types(self, vendor_task_tool, sample_tasks):
        """Test identification of required vendor types from task"""
        # Test venue task
        venue_task = sample_tasks.tasks[0]
        required_types = vendor_task_tool._identify_required_vendor_types(venue_task)
        assert 'venue' in required_types
        
        # Test catering task
        catering_task = sample_tasks.tasks[1]
        required_types = vendor_task_tool._identify_required_vendor_types(catering_task)
        assert 'caterer' in required_types
        
        # Test photography task
        photo_task = sample_tasks.tasks[2]
        required_types = vendor_task_tool._identify_required_vendor_types(photo_task)
        assert 'photographer' in required_types
        
        # Test makeup task
        makeup_task = sample_tasks.tasks[3]
        required_types = vendor_task_tool._identify_required_vendor_types(makeup_task)
        assert 'makeup_artist' in required_types
        
        # Test non-vendor task
        admin_task = sample_tasks.tasks[4]
        required_types = vendor_task_tool._identify_required_vendor_types(admin_task)
        assert len(required_types) == 0
    
    def test_match_vendor_to_task(self, vendor_task_tool, sample_tasks, sample_state):
        """Test vendor-task matching score calculation"""
        task = sample_tasks.tasks[0]  # Venue task
        vendors = vendor_task_tool._extract_vendors_from_combination(
            sample_state['selected_combination']
        )
        vendor = vendors['venue']
        vendor_details = {
            'max_seating_capacity': 300,
            'rental_cost': 150000
        }
        
        match_score = vendor_task_tool._match_vendor_to_task(
            task, vendor, vendor_details
        )
        
        assert 0.0 <= match_score <= 1.0
        assert match_score > 0.5  # Should be a good match
    
    def test_flag_manual_assignment(self, vendor_task_tool, sample_tasks):
        """Test manual assignment flagging"""
        task = sample_tasks.tasks[0]
        assignment = vendor_task_tool._flag_manual_assignment(task, 'venue')
        
        assert isinstance(assignment, VendorAssignment)
        assert assignment.requires_manual_assignment is True
        assert assignment.vendor_id == ""
        assert 'Manual Assignment Required' in assignment.vendor_name
        assert assignment.fitness_score == 0.0
    
    def test_assign_vendors_success(self, vendor_task_tool, sample_tasks, sample_state):
        """Test successful vendor assignment"""
        # Mock database queries
        with patch.object(vendor_task_tool, '_query_vendor_details', return_value={}):
            assignments = vendor_task_tool.assign_vendors(sample_tasks, sample_state)
        
        assert len(assignments) > 0
        
        # Check that assignments were created for vendor-related tasks
        task_ids_with_assignments = {a.task_id for a in assignments}
        assert 'task-1' in task_ids_with_assignments  # Venue task
        assert 'task-2' in task_ids_with_assignments  # Catering task
        assert 'task-3' in task_ids_with_assignments  # Photography task
        assert 'task-4' in task_ids_with_assignments  # Makeup task
        
        # Check that non-vendor task doesn't have assignment
        assert 'task-5' not in task_ids_with_assignments
    
    def test_assign_vendors_no_combination(self, vendor_task_tool, sample_tasks):
        """Test vendor assignment with no selected combination"""
        state_no_combo = {
            'plan_id': 'test-plan-123',
            'selected_combination': None
        }
        
        assignments = vendor_task_tool.assign_vendors(sample_tasks, state_no_combo)
        
        # Should return empty assignments or manual assignment flags
        assert isinstance(assignments, list)
    
    def test_assign_vendors_empty_combination(self, vendor_task_tool, sample_tasks):
        """Test vendor assignment with empty combination"""
        state_empty_combo = {
            'plan_id': 'test-plan-123',
            'selected_combination': {}
        }
        
        assignments = vendor_task_tool.assign_vendors(sample_tasks, state_empty_combo)
        
        # Should handle gracefully
        assert isinstance(assignments, list)
    
    def test_generate_assignment_rationale(self, vendor_task_tool, sample_tasks):
        """Test assignment rationale generation"""
        task = sample_tasks.tasks[0]
        vendor = {
            'name': 'Grand Palace Hotel',
            'vendor_type': 'venue',
            'fitness_score': 0.85
        }
        vendor_details = {
            'max_seating_capacity': 300,
            'location_city': 'Mumbai'
        }
        match_score = 0.90
        
        rationale = vendor_task_tool._generate_assignment_rationale(
            task, vendor, vendor_details, match_score
        )
        
        assert isinstance(rationale, str)
        assert len(rationale) > 0
        assert 'Grand Palace Hotel' in rationale
        assert 'match score' in rationale.lower()
    
    def test_create_empty_assignments(self, vendor_task_tool, sample_tasks):
        """Test creation of empty assignments"""
        assignments = vendor_task_tool._create_empty_assignments(sample_tasks.tasks)
        
        assert isinstance(assignments, list)
        
        # Should create manual assignments for tasks requiring vendors
        for assignment in assignments:
            assert assignment.requires_manual_assignment is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
