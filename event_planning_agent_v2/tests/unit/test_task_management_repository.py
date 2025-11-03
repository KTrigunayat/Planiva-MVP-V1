"""
Unit tests for Task Management Repository

Tests database persistence operations for Task Management Agent.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy.exc import OperationalError

from event_planning_agent_v2.database.task_management_repository import TaskManagementRepository
from event_planning_agent_v2.agents.task_management.models.extended_models import (
    ExtendedTaskList,
    ExtendedTask,
    ProcessingSummary
)
from event_planning_agent_v2.agents.task_management.models.data_models import (
    Resource,
    TaskTimeline,
    VendorAssignment,
    LogisticsStatus,
    Conflict,
    VenueInfo
)


@pytest.fixture
def mock_db_manager():
    """Create mock database manager"""
    manager = Mock()
    session = MagicMock()
    
    # Setup context manager behavior
    manager.get_sync_session.return_value.__enter__ = Mock(return_value=session)
    manager.get_sync_session.return_value.__exit__ = Mock(return_value=False)
    
    return manager, session


@pytest.fixture
def sample_processing_summary():
    """Create sample processing summary"""
    return ProcessingSummary(
        total_tasks=5,
        tasks_with_errors=1,
        tasks_with_warnings=2,
        tasks_requiring_review=1,
        processing_time=45.5,
        tool_execution_status={
            'timeline_calculation': 'success',
            'llm_enhancement': 'success',
            'vendor_assignment': 'partial',
            'logistics_check': 'success',
            'conflict_check': 'success',
            'venue_lookup': 'success'
        }
    )


@pytest.fixture
def sample_extended_task():
    """Create sample extended task"""
    return ExtendedTask(
        task_id='task_001',
        task_name='Setup Venue',
        task_description='Prepare venue for ceremony',
        priority_level='High',
        priority_score=0.85,
        granularity_level=1,
        parent_task_id=None,
        sub_tasks=['task_001_1', 'task_001_2'],
        dependencies=['task_000'],
        resources_required=[
            Resource(
                resource_type='equipment',
                resource_id='eq_001',
                resource_name='Sound System',
                quantity_required=1,
                availability_constraint='morning_only'
            )
        ],
        timeline=TaskTimeline(
            task_id='task_001',
            start_time=datetime(2024, 6, 15, 9, 0),
            end_time=datetime(2024, 6, 15, 12, 0),
            duration=timedelta(hours=3),
            buffer_time=timedelta(minutes=30),
            scheduling_constraints=['morning_preferred']
        ),
        llm_enhancements={
            'enhanced_description': 'Comprehensive venue setup including audio, lighting, and seating',
            'suggestions': ['Arrive early', 'Test equipment'],
            'potential_issues': ['Weather dependent'],
            'best_practices': ['Have backup plan']
        },
        assigned_vendors=[
            VendorAssignment(
                task_id='task_001',
                vendor_id='vendor_001',
                vendor_name='Elite Venues',
                vendor_type='venue',
                fitness_score=0.92,
                assignment_rationale='Best match for capacity and location',
                requires_manual_assignment=False
            )
        ],
        logistics_status=LogisticsStatus(
            task_id='task_001',
            transportation_status='verified',
            transportation_notes='Accessible by main road',
            equipment_status='verified',
            equipment_notes='All equipment available on-site',
            setup_status='verified',
            setup_notes='2 hours setup time required',
            overall_feasibility='feasible',
            issues=[]
        ),
        conflicts=[
            Conflict(
                conflict_id='conflict_001',
                conflict_type='timeline',
                severity='medium',
                affected_tasks=['task_001', 'task_002'],
                conflict_description='Overlapping setup times',
                suggested_resolutions=['Adjust task_002 start time by 1 hour']
            )
        ],
        venue_info=VenueInfo(
            task_id='task_001',
            venue_id='venue_001',
            venue_name='Grand Ballroom',
            venue_type='indoor',
            capacity=500,
            available_equipment=['projector', 'sound_system', 'stage'],
            setup_time_required=timedelta(hours=2),
            teardown_time_required=timedelta(hours=1),
            access_restrictions=['no_outdoor_access'],
            requires_venue_selection=False
        ),
        has_errors=False,
        has_warnings=True,
        requires_manual_review=False,
        error_messages=[],
        warning_messages=['Weather dependent - have backup plan']
    )


@pytest.fixture
def sample_extended_task_list(sample_extended_task, sample_processing_summary):
    """Create sample extended task list"""
    return ExtendedTaskList(
        tasks=[sample_extended_task],
        processing_summary=sample_processing_summary,
        metadata={'event_type': 'wedding', 'guest_count': 200}
    )


class TestTaskManagementRepository:
    """Test suite for TaskManagementRepository"""
    
    def test_initialization(self):
        """Test repository initialization"""
        repo = TaskManagementRepository()
        
        assert repo is not None
        assert repo.max_retries == 3
        assert repo.base_retry_delay == 1.0
        assert repo.recovery_manager is not None
    
    def test_is_transient_error(self):
        """Test transient error detection"""
        repo = TaskManagementRepository()
        
        # Test transient errors
        assert repo._is_transient_error(Exception("connection timeout"))
        assert repo._is_transient_error(Exception("deadlock detected"))
        assert repo._is_transient_error(Exception("temporary unavailable"))
        
        # Test non-transient errors
        assert not repo._is_transient_error(Exception("syntax error"))
        assert not repo._is_transient_error(Exception("invalid column"))
    
    def test_serialize_extended_task(self, sample_extended_task):
        """Test extended task serialization"""
        repo = TaskManagementRepository()
        
        task_dict = repo._serialize_extended_task(sample_extended_task)
        
        # Verify basic fields
        assert task_dict['task_id'] == 'task_001'
        assert task_dict['task_name'] == 'Setup Venue'
        assert task_dict['priority_level'] == 'High'
        assert task_dict['priority_score'] == 0.85
        
        # Verify resources
        assert len(task_dict['resources_required']) == 1
        assert task_dict['resources_required'][0]['resource_type'] == 'equipment'
        
        # Verify timeline
        assert task_dict['timeline'] is not None
        assert task_dict['timeline']['task_id'] == 'task_001'
        assert 'start_time' in task_dict['timeline']
        
        # Verify vendors
        assert len(task_dict['assigned_vendors']) == 1
        assert task_dict['assigned_vendors'][0]['vendor_name'] == 'Elite Venues'
        
        # Verify logistics
        assert task_dict['logistics_status'] is not None
        assert task_dict['logistics_status']['overall_feasibility'] == 'feasible'
        
        # Verify conflicts
        assert len(task_dict['conflicts']) == 1
        assert task_dict['conflicts'][0]['conflict_type'] == 'timeline'
        
        # Verify venue info
        assert task_dict['venue_info'] is not None
        assert task_dict['venue_info']['venue_name'] == 'Grand Ballroom'
        
        # Verify status flags
        assert task_dict['has_errors'] is False
        assert task_dict['has_warnings'] is True
    
    @patch('event_planning_agent_v2.database.task_management_repository.get_sync_session')
    def test_save_task_management_run_success(
        self,
        mock_get_session,
        sample_processing_summary
    ):
        """Test successful save of task management run"""
        # Setup mock
        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = 123
        mock_session.execute.return_value = mock_result
        
        mock_get_session.return_value.__enter__ = Mock(return_value=mock_session)
        mock_get_session.return_value.__exit__ = Mock(return_value=False)
        
        # Execute
        repo = TaskManagementRepository()
        run_id = repo.save_task_management_run(
            event_id='event_123',
            processing_summary=sample_processing_summary,
            status='completed'
        )
        
        # Verify
        assert run_id == 123
        assert mock_session.execute.called
        assert mock_session.commit.called
    
    @patch('event_planning_agent_v2.database.task_management_repository.get_sync_session')
    def test_save_extended_tasks_success(
        self,
        mock_get_session,
        sample_extended_task_list
    ):
        """Test successful save of extended tasks"""
        # Setup mock
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__ = Mock(return_value=mock_session)
        mock_get_session.return_value.__exit__ = Mock(return_value=False)
        
        # Execute
        repo = TaskManagementRepository()
        count = repo.save_extended_tasks(
            task_management_run_id=123,
            extended_task_list=sample_extended_task_list
        )
        
        # Verify
        assert count == 1
        assert mock_session.execute.called
        assert mock_session.commit.called
    
    @patch('event_planning_agent_v2.database.task_management_repository.get_sync_session')
    def test_save_conflicts_success(self, mock_get_session):
        """Test successful save of conflicts"""
        # Setup mock
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__ = Mock(return_value=mock_session)
        mock_get_session.return_value.__exit__ = Mock(return_value=False)
        
        conflicts = [
            Conflict(
                conflict_id='conflict_001',
                conflict_type='timeline',
                severity='high',
                affected_tasks=['task_001', 'task_002'],
                conflict_description='Overlapping times',
                suggested_resolutions=['Adjust timing']
            )
        ]
        
        # Execute
        repo = TaskManagementRepository()
        count = repo.save_conflicts(
            task_management_run_id=123,
            conflicts=conflicts
        )
        
        # Verify
        assert count == 1
        assert mock_session.execute.called
        assert mock_session.commit.called
    
    @patch('event_planning_agent_v2.database.task_management_repository.get_sync_session')
    def test_get_task_management_run_success(self, mock_get_session):
        """Test successful retrieval of task management run"""
        # Setup mock
        mock_session = MagicMock()
        
        # Mock run data
        mock_run_result = MagicMock()
        mock_run_result.__getitem__ = lambda self, i: [
            123,  # id
            'event_123',  # event_id
            datetime(2024, 6, 15, 10, 0),  # run_timestamp
            '{"total_tasks": 5}',  # processing_summary
            'completed',  # status
            None  # error_log
        ][i]
        
        # Mock tasks data
        mock_tasks_result = []
        
        # Mock conflicts data
        mock_conflicts_result = []
        
        mock_session.execute.side_effect = [
            MagicMock(fetchone=lambda: mock_run_result),
            MagicMock(fetchall=lambda: mock_tasks_result),
            MagicMock(fetchall=lambda: mock_conflicts_result)
        ]
        
        mock_get_session.return_value.__enter__ = Mock(return_value=mock_session)
        mock_get_session.return_value.__exit__ = Mock(return_value=False)
        
        # Execute
        repo = TaskManagementRepository()
        run_data = repo.get_task_management_run(event_id='event_123')
        
        # Verify
        assert run_data is not None
        assert run_data['id'] == 123
        assert run_data['event_id'] == 'event_123'
        assert run_data['status'] == 'completed'
        assert 'tasks' in run_data
        assert 'conflicts' in run_data
    
    @patch('event_planning_agent_v2.database.task_management_repository.get_sync_session')
    def test_save_complete_task_management_data_success(
        self,
        mock_get_session,
        sample_extended_task_list
    ):
        """Test successful save of complete task management data"""
        # Setup mock
        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = 123
        mock_session.execute.return_value = mock_result
        
        mock_get_session.return_value.__enter__ = Mock(return_value=mock_session)
        mock_get_session.return_value.__exit__ = Mock(return_value=False)
        
        # Execute
        repo = TaskManagementRepository()
        result = repo.save_complete_task_management_data(
            event_id='event_123',
            extended_task_list=sample_extended_task_list,
            status='completed'
        )
        
        # Verify
        assert result['run_id'] == 123
        assert result['tasks_saved'] == 1
        assert result['conflicts_saved'] == 1
        assert result['status'] == 'completed'
        assert mock_session.commit.called
    
    @patch('event_planning_agent_v2.database.task_management_repository.get_sync_session')
    def test_retry_on_transient_error(self, mock_get_session):
        """Test retry logic on transient database errors"""
        # Setup mock to fail once then succeed
        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = 123
        
        call_count = [0]
        
        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise OperationalError("connection timeout", None, None)
            return mock_result
        
        mock_session.execute.side_effect = side_effect
        
        mock_get_session.return_value.__enter__ = Mock(return_value=mock_session)
        mock_get_session.return_value.__exit__ = Mock(return_value=False)
        
        # Execute
        repo = TaskManagementRepository()
        
        with patch('time.sleep'):  # Skip actual sleep
            run_id = repo.save_task_management_run(
                event_id='event_123',
                processing_summary=ProcessingSummary(
                    total_tasks=1,
                    tasks_with_errors=0,
                    tasks_with_warnings=0,
                    tasks_requiring_review=0,
                    processing_time=1.0
                ),
                status='completed'
            )
        
        # Verify retry happened
        assert run_id == 123
        assert call_count[0] == 2  # Failed once, succeeded on retry


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
