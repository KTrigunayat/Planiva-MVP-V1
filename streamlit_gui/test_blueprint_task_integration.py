"""
Test blueprint task integration
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

import pytest
from unittest.mock import Mock, patch, MagicMock
import streamlit as st

# Import after path is set
from pages.plan_blueprint import BlueprintManager
from components.api_client import APIError


@pytest.fixture
def mock_session_state():
    """Mock Streamlit session state"""
    return {
        'current_plan_id': 'test-plan-123'
    }


@pytest.fixture
def sample_blueprint_data():
    """Sample blueprint data"""
    return {
        'event_info': {
            'client_name': 'Test Client',
            'event_type': 'Wedding',
            'event_date': '2025-06-15',
            'guest_count': 150,
            'budget': 50000,
            'location': 'Test Venue'
        },
        'selected_combination': {
            'venue': {
                'name': 'Test Venue',
                'cost': 15000,
                'contact_phone': '555-1234',
                'contact_email': 'venue@test.com'
            },
            'caterer': {
                'name': 'Test Caterer',
                'cost': 12000,
                'contact_phone': '555-5678',
                'contact_email': 'caterer@test.com'
            },
            'total_cost': 45000,
            'fitness_score': 92.5
        }
    }


@pytest.fixture
def sample_task_data():
    """Sample task data"""
    return {
        'tasks': [
            {
                'id': 'task-1',
                'name': 'Book Venue',
                'description': 'Confirm venue booking',
                'priority': 'Critical',
                'status': 'completed',
                'estimated_duration': '2 hours',
                'start_date': '2025-01-15',
                'end_date': '2025-01-15',
                'assigned_vendor': {
                    'name': 'Test Venue',
                    'type': 'venue'
                },
                'dependencies': [],
                'logistics': {
                    'transportation_verified': True,
                    'equipment_verified': True,
                    'setup_verified': True
                }
            },
            {
                'id': 'task-2',
                'name': 'Finalize Menu',
                'description': 'Select final menu options',
                'priority': 'High',
                'status': 'in_progress',
                'estimated_duration': '3 hours',
                'start_date': '2025-02-01',
                'end_date': '2025-02-01',
                'assigned_vendor': {
                    'name': 'Test Caterer',
                    'type': 'caterer'
                },
                'dependencies': ['task-1'],
                'logistics': {
                    'transportation_required': True,
                    'equipment_required': True,
                    'setup_required': True
                }
            }
        ],
        'conflicts': [
            {
                'id': 'conflict-1',
                'type': 'Timeline Conflict',
                'severity': 'High',
                'description': 'Two tasks scheduled at the same time',
                'affected_tasks': ['task-2', 'task-3'],
                'suggested_resolution': 'Reschedule one task to a different time slot'
            }
        ]
    }


class TestBlueprintTaskIntegration:
    """Test blueprint task integration"""
    
    @patch('streamlit.session_state')
    @patch('pages.plan_blueprint.api_client')
    @patch('streamlit.subheader')
    @patch('streamlit.spinner')
    @patch('streamlit.markdown')
    @patch('streamlit.columns')
    @patch('streamlit.metric')
    def test_render_tasks_section_with_tasks(
        self, mock_metric, mock_columns, mock_markdown, mock_spinner,
        mock_subheader, mock_api_client, mock_session_state,
        sample_blueprint_data, sample_task_data
    ):
        """Test rendering tasks section with available tasks"""
        # Setup
        mock_session_state.get.return_value = 'test-plan-123'
        mock_api_client.get_extended_task_list.return_value = sample_task_data
        mock_spinner.return_value.__enter__ = Mock()
        mock_spinner.return_value.__exit__ = Mock()
        
        # Mock columns
        mock_col = Mock()
        mock_columns.return_value = [mock_col, mock_col, mock_col, mock_col]
        
        manager = BlueprintManager()
        
        # Execute
        manager._render_tasks_section(sample_blueprint_data)
        
        # Verify
        mock_api_client.get_extended_task_list.assert_called_once_with('test-plan-123')
        mock_subheader.assert_called()
        assert mock_markdown.call_count > 0
    
    @patch('streamlit.session_state')
    @patch('pages.plan_blueprint.api_client')
    @patch('streamlit.info')
    def test_render_tasks_section_no_tasks(
        self, mock_info, mock_api_client, mock_session_state,
        sample_blueprint_data
    ):
        """Test rendering tasks section when no tasks available"""
        # Setup
        mock_session_state.get.return_value = 'test-plan-123'
        mock_api_client.get_extended_task_list.return_value = {'tasks': []}
        
        manager = BlueprintManager()
        
        # Execute
        manager._render_tasks_section(sample_blueprint_data)
        
        # Verify
        mock_info.assert_called()
    
    @patch('streamlit.session_state')
    @patch('pages.plan_blueprint.api_client')
    @patch('streamlit.info')
    def test_render_tasks_section_api_error_404(
        self, mock_info, mock_api_client, mock_session_state,
        sample_blueprint_data
    ):
        """Test rendering tasks section when API returns 404"""
        # Setup
        mock_session_state.get.return_value = 'test-plan-123'
        mock_api_client.get_extended_task_list.side_effect = APIError("Not found", 404)
        
        manager = BlueprintManager()
        
        # Execute
        manager._render_tasks_section(sample_blueprint_data)
        
        # Verify - should show info message about tasks being generated
        mock_info.assert_called()
    
    @patch('streamlit.session_state')
    @patch('pages.plan_blueprint.api_client')
    @patch('streamlit.error')
    def test_render_tasks_section_api_error_other(
        self, mock_error, mock_api_client, mock_session_state,
        sample_blueprint_data
    ):
        """Test rendering tasks section when API returns other error"""
        # Setup
        mock_session_state.get.return_value = 'test-plan-123'
        mock_api_client.get_extended_task_list.side_effect = APIError("Server error", 500)
        
        manager = BlueprintManager()
        
        # Execute
        manager._render_tasks_section(sample_blueprint_data)
        
        # Verify - should show error message
        mock_error.assert_called()
    
    @patch('streamlit.session_state')
    @patch('pages.plan_blueprint.api_client')
    def test_export_json_includes_tasks(
        self, mock_api_client, mock_session_state,
        sample_blueprint_data, sample_task_data
    ):
        """Test JSON export includes task data"""
        # Setup
        mock_session_state.get.return_value = 'test-plan-123'
        mock_api_client.get_extended_task_list.return_value = sample_task_data
        
        manager = BlueprintManager()
        
        # Execute - this will be tested by checking the API call
        with patch('streamlit.download_button'):
            with patch('pages.plan_blueprint.show_success'):
                manager._export_json(sample_blueprint_data)
        
        # Verify
        mock_api_client.get_extended_task_list.assert_called_once_with('test-plan-123')
    
    @patch('streamlit.session_state')
    @patch('pages.plan_blueprint.api_client')
    def test_export_text_includes_tasks(
        self, mock_api_client, mock_session_state,
        sample_blueprint_data, sample_task_data
    ):
        """Test text export includes task data"""
        # Setup
        mock_session_state.get.return_value = 'test-plan-123'
        mock_api_client.get_extended_task_list.return_value = sample_task_data
        
        manager = BlueprintManager()
        
        # Execute
        with patch('streamlit.download_button'):
            with patch('pages.plan_blueprint.show_success'):
                manager._export_text(sample_blueprint_data)
        
        # Verify
        mock_api_client.get_extended_task_list.assert_called_once_with('test-plan-123')
    
    @patch('streamlit.session_state')
    @patch('pages.plan_blueprint.api_client')
    def test_export_html_includes_tasks(
        self, mock_api_client, mock_session_state,
        sample_blueprint_data, sample_task_data
    ):
        """Test HTML export includes task data"""
        # Setup
        mock_session_state.get.return_value = 'test-plan-123'
        mock_api_client.get_extended_task_list.return_value = sample_task_data
        
        manager = BlueprintManager()
        
        # Execute
        with patch('streamlit.download_button'):
            with patch('pages.plan_blueprint.show_success'):
                manager._export_html(sample_blueprint_data)
        
        # Verify
        mock_api_client.get_extended_task_list.assert_called_once_with('test-plan-123')
    
    @patch('streamlit.session_state')
    @patch('pages.plan_blueprint.api_client')
    def test_export_pdf_includes_tasks(
        self, mock_api_client, mock_session_state,
        sample_blueprint_data, sample_task_data
    ):
        """Test PDF export includes task data"""
        # Setup
        mock_session_state.get.return_value = 'test-plan-123'
        mock_api_client.get_extended_task_list.return_value = sample_task_data
        
        manager = BlueprintManager()
        
        # Execute
        with patch('streamlit.download_button'):
            with patch('pages.plan_blueprint.show_success'):
                with patch('reportlab.platypus.SimpleDocTemplate'):
                    manager._export_pdf(sample_blueprint_data)
        
        # Verify
        mock_api_client.get_extended_task_list.assert_called_once_with('test-plan-123')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
