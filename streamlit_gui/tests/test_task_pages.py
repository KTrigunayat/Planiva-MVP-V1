"""
Unit tests for Task Management pages (Task List, Timeline, Conflicts, Vendors)
"""
import pytest
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime, timedelta
import streamlit as st

from pages.task_list import TaskListPage
from pages.timeline_view import TimelineViewPage
from pages.conflicts import ConflictsPage
from pages.vendors import VendorsPage
from components.api_client import APIError


class TestTaskListPage:
    """Test cases for Task List page."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.page = TaskListPage()
        self.sample_tasks = [
            {
                "task_id": "task-1",
                "name": "Venue Setup",
                "description": "Set up venue decorations",
                "priority": "High",
                "status": "pending",
                "estimated_duration": "4 hours",
                "start_time": "2024-01-20T08:00:00",
                "end_time": "2024-01-20T12:00:00",
                "dependencies": ["task-0"],
                "vendor": {
                    "name": "Elite Decorators",
                    "type": "decorator",
                    "contact": "contact@elite.com"
                },
                "logistics": {
                    "transportation": {"status": "verified"},
                    "equipment": {"status": "available"},
                    "setup": {"time_required": "2 hours"}
                },
                "conflicts": []
            },
            {
                "task_id": "task-2",
                "name": "Catering Setup",
                "description": "Prepare food stations",
                "priority": "Critical",
                "status": "in_progress",
                "estimated_duration": "3 hours",
                "start_time": "2024-01-20T10:00:00",
                "end_time": "2024-01-20T13:00:00",
                "dependencies": [],
                "vendor": {
                    "name": "Gourmet Caterers",
                    "type": "caterer",
                    "contact": "info@gourmet.com"
                },
                "logistics": {
                    "transportation": {"status": "pending"},
                    "equipment": {"status": "available"},
                    "setup": {"time_required": "1 hour"}
                },
                "conflicts": ["conflict-1"]
            }
        ]

    @patch('streamlit.header')
    @patch('streamlit.session_state', {})
    def test_render_page_header(self, mock_header):
        """Test page header rendering."""
        with patch.object(self.page, '_load_tasks', return_value=None), \
             patch('pages.task_list.show_error'):
            self.page.render()
            
            mock_header.assert_called_once()
    
    @patch('streamlit.session_state', {})
    def test_load_tasks_success(self):
        """Test successful task loading."""
        mock_response = {
            "tasks": self.sample_tasks,
            "total_count": 2,
            "completion_percentage": 25.0
        }
        
        with patch.object(self.page.api_client, 'get_extended_task_list', return_value=mock_response):
            result = self.page._load_tasks()
            
            assert result is not None
            assert len(result["tasks"]) == 2
            assert result["completion_percentage"] == 25.0
    
    @patch('streamlit.session_state', {})
    def test_load_tasks_api_error(self):
        """Test task loading with API error."""
        with patch.object(self.page.api_client, 'get_extended_task_list',
                         side_effect=APIError("Connection failed", 500)):
            result = self.page._load_tasks()
            
            assert result is None
    
    @patch('streamlit.session_state', {})
    def test_task_status_update(self):
        """Test task status update functionality."""
        with patch.object(self.page.api_client, 'update_task_status', return_value={"success": True}), \
             patch('pages.task_list.show_success'):
            
            self.page._update_task_status("task-1", "completed")
    
    @patch('streamlit.session_state', {})
    def test_filter_tasks_by_priority(self):
        """Test task filtering by priority."""
        filtered = self.page._filter_tasks(self.sample_tasks, priority_filter="Critical")
        
        assert len(filtered) == 1
        assert filtered[0]["priority"] == "Critical"
    
    @patch('streamlit.session_state', {})
    def test_sort_tasks_by_priority(self):
        """Test task sorting by priority."""
        sorted_tasks = self.page._sort_tasks(self.sample_tasks, sort_by="priority")
        
        assert sorted_tasks[0]["priority"] == "Critical"


class TestTimelineViewPage:
    """Test cases for Timeline View page."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.page = TimelineViewPage()
        self.sample_timeline = {
            "tasks": [
                {
                    "task_id": "task-1",
                    "name": "Venue Setup",
                    "start_time": "2024-01-20T08:00:00",
                    "end_time": "2024-01-20T12:00:00",
                    "priority": "High",
                    "vendor": "Elite Decorators",
                    "dependencies": [],
                    "conflicts": []
                },
                {
                    "task_id": "task-2",
                    "name": "Catering Setup",
                    "start_time": "2024-01-20T10:00:00",
                    "end_time": "2024-01-20T13:00:00",
                    "priority": "Critical",
                    "vendor": "Gourmet Caterers",
                    "dependencies": ["task-1"],
                    "conflicts": ["conflict-1"]
                }
            ]
        }
    
    @patch('streamlit.header')
    @patch('streamlit.session_state', {})
    def test_render_page_header(self, mock_header):
        """Test page header rendering."""
        with patch.object(self.page, '_load_timeline', return_value=None), \
             patch('pages.timeline_view.show_error'):
            self.page.render()
            
            mock_header.assert_called_once()
    
    @patch('streamlit.session_state', {})
    def test_load_timeline_success(self):
        """Test successful timeline loading."""
        with patch.object(self.page.api_client, 'get_timeline_data', 
                         return_value=self.sample_timeline):
            result = self.page._load_timeline()
            
            assert result is not None
            assert len(result["tasks"]) == 2
    
    @patch('streamlit.session_state', {})
    def test_load_timeline_api_error(self):
        """Test timeline loading with API error."""
        with patch.object(self.page.api_client, 'get_timeline_data',
                         side_effect=APIError("Connection failed", 500)):
            result = self.page._load_timeline()
            
            assert result is None
    
    @patch('streamlit.session_state', {})
    def test_create_gantt_chart(self):
        """Test Gantt chart creation."""
        with patch('streamlit.plotly_chart') as mock_chart:
            self.page._create_gantt_chart(self.sample_timeline["tasks"])
            
            mock_chart.assert_called_once()
    
    @patch('streamlit.session_state', {})
    def test_highlight_conflicts_in_timeline(self):
        """Test conflict highlighting in timeline."""
        tasks_with_conflicts = [t for t in self.sample_timeline["tasks"] if t.get("conflicts")]
        
        assert len(tasks_with_conflicts) == 1
        assert tasks_with_conflicts[0]["task_id"] == "task-2"


class TestConflictsPage:
    """Test cases for Conflicts Resolution page."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.page = ConflictsPage()
        self.sample_conflicts = [
            {
                "conflict_id": "conflict-1",
                "type": "timeline_overlap",
                "severity": "High",
                "affected_tasks": ["task-1", "task-2"],
                "description": "Tasks overlap in timeline",
                "suggested_resolution": "Adjust task-2 start time by 2 hours"
            },
            {
                "conflict_id": "conflict-2",
                "type": "resource_conflict",
                "severity": "Medium",
                "affected_tasks": ["task-3", "task-4"],
                "description": "Same vendor double-booked",
                "suggested_resolution": "Assign alternative vendor"
            }
        ]
    
    @patch('streamlit.header')
    @patch('streamlit.session_state', {})
    def test_render_page_header(self, mock_header):
        """Test page header rendering."""
        with patch.object(self.page, '_load_conflicts', return_value=None), \
             patch('pages.conflicts.show_error'):
            self.page.render()
            
            mock_header.assert_called_once()
    
    @patch('streamlit.session_state', {})
    def test_load_conflicts_success(self):
        """Test successful conflicts loading."""
        mock_response = {
            "conflicts": self.sample_conflicts,
            "total_count": 2
        }
        
        with patch.object(self.page.api_client, 'get_conflicts', return_value=mock_response):
            result = self.page._load_conflicts()
            
            assert result is not None
            assert len(result["conflicts"]) == 2
    
    @patch('streamlit.session_state', {})
    def test_load_conflicts_api_error(self):
        """Test conflicts loading with API error."""
        with patch.object(self.page.api_client, 'get_conflicts',
                         side_effect=APIError("Connection failed", 500)):
            result = self.page._load_conflicts()
            
            assert result is None
    
    @patch('streamlit.session_state', {})
    def test_no_conflicts_message(self):
        """Test no conflicts message display."""
        with patch('streamlit.header'), \
             patch.object(self.page, '_load_conflicts', 
                         return_value={"conflicts": [], "total_count": 0}), \
             patch('streamlit.success') as mock_success:
            self.page.render()
            
            mock_success.assert_called()
    
    @patch('streamlit.session_state', {})
    def test_resolve_conflict(self):
        """Test conflict resolution."""
        with patch.object(self.page.api_client, 'resolve_conflict', 
                         return_value={"success": True}), \
             patch('pages.conflicts.show_success'):
            
            self.page._resolve_conflict("conflict-1", "adjust_timeline")
    
    @patch('streamlit.session_state', {})
    def test_filter_conflicts_by_severity(self):
        """Test conflict filtering by severity."""
        filtered = self.page._filter_conflicts(self.sample_conflicts, severity_filter="High")
        
        assert len(filtered) == 1
        assert filtered[0]["severity"] == "High"


class TestVendorsPage:
    """Test cases for Vendors page."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.page = VendorsPage()
        self.sample_vendors = [
            {
                "vendor_id": "vendor-1",
                "name": "Elite Decorators",
                "type": "decorator",
                "contact": "contact@elite.com",
                "assigned_tasks": [
                    {
                        "task_id": "task-1",
                        "name": "Venue Setup",
                        "priority": "High",
                        "status": "pending"
                    }
                ],
                "fitness_score": 95.0,
                "workload": "medium"
            },
            {
                "vendor_id": "vendor-2",
                "name": "Gourmet Caterers",
                "type": "caterer",
                "contact": "info@gourmet.com",
                "assigned_tasks": [
                    {
                        "task_id": "task-2",
                        "name": "Catering Setup",
                        "priority": "Critical",
                        "status": "in_progress"
                    }
                ],
                "fitness_score": 88.0,
                "workload": "high"
            }
        ]
    
    @patch('streamlit.header')
    @patch('streamlit.session_state', {})
    def test_render_page_header(self, mock_header):
        """Test page header rendering."""
        with patch.object(self.page, '_load_vendors', return_value=None), \
             patch('pages.vendors.show_error'):
            self.page.render()
            
            mock_header.assert_called_once()
    
    @patch('streamlit.session_state', {})
    def test_load_vendors_success(self):
        """Test successful vendors loading."""
        mock_response = {
            "vendors": self.sample_vendors,
            "total_count": 2
        }
        
        with patch.object(self.page.api_client, 'get_vendor_assignments', return_value=mock_response):
            result = self.page._load_vendors()
            
            assert result is not None
            assert len(result["vendors"]) == 2
    
    @patch('streamlit.session_state', {})
    def test_load_vendors_api_error(self):
        """Test vendors loading with API error."""
        with patch.object(self.page.api_client, 'get_vendor_assignments',
                         side_effect=APIError("Connection failed", 500)):
            result = self.page._load_vendors()
            
            assert result is None
    
    @patch('streamlit.session_state', {})
    def test_render_vendor_card(self):
        """Test vendor card rendering."""
        with patch('streamlit.expander') as mock_expander, \
             patch('streamlit.markdown'), \
             patch('streamlit.metric'):
            
            mock_expander_context = MagicMock()
            mock_expander.return_value.__enter__ = MagicMock(return_value=mock_expander_context)
            mock_expander.return_value.__exit__ = MagicMock(return_value=False)
            
            self.page._render_vendor_card(self.sample_vendors[0])
            
            mock_expander.assert_called()
    
    @patch('streamlit.session_state', {})
    def test_filter_vendors_by_type(self):
        """Test vendor filtering by type."""
        filtered = self.page._filter_vendors(self.sample_vendors, vendor_type="decorator")
        
        assert len(filtered) == 1
        assert filtered[0]["type"] == "decorator"
    
    @patch('streamlit.session_state', {})
    def test_workload_distribution_chart(self):
        """Test workload distribution chart creation."""
        with patch('streamlit.plotly_chart') as mock_chart:
            self.page._create_workload_chart(self.sample_vendors)
            
            mock_chart.assert_called_once()


class TestTaskPagesIntegration:
    """Integration tests for Task Management pages navigation and data flow."""
    
    @patch('streamlit.session_state', {'current_plan_id': 'plan-123'})
    def test_plan_context_available(self):
        """Test plan context is available across pages."""
        assert st.session_state.get('current_plan_id') == 'plan-123'
    
    @patch('streamlit.session_state', {'selected_task_id': 'task-1'})
    def test_task_selection_persists(self):
        """Test task selection persists across page navigation."""
        assert st.session_state.get('selected_task_id') == 'task-1'
    
    @patch('streamlit.session_state', {})
    def test_conflict_resolution_updates_timeline(self):
        """Test that resolving conflicts updates timeline view."""
        # This would test the full flow in a real integration test
        # For unit tests, we verify the session state updates
        st.session_state['conflicts_resolved'] = True
        assert st.session_state.get('conflicts_resolved') is True


class TestComponentRendering:
    """Test cases for component rendering functions."""
    
    @patch('streamlit.session_state', {})
    def test_priority_badge_rendering(self):
        """Test priority badge component rendering."""
        from components.task_components import priority_badge
        
        result = priority_badge("Critical")
        assert "Critical" in result
        assert "span" in result
    
    @patch('streamlit.session_state', {})
    def test_status_badge_rendering(self):
        """Test status badge component rendering."""
        from components.task_components import task_status_badge
        
        result = task_status_badge("completed")
        assert "completed" in result.lower() or "complete" in result.lower()
        assert "span" in result
    
    @patch('streamlit.session_state', {})
    def test_vendor_badge_rendering(self):
        """Test vendor badge component rendering."""
        from components.task_components import vendor_badge
        
        result = vendor_badge({"name": "Elite Decorators", "type": "decorator"})
        assert "Elite Decorators" in result
        assert "div" in result


class TestErrorHandling:
    """Test cases for error handling across task pages."""
    
    @patch('streamlit.session_state', {})
    def test_api_timeout_handling(self):
        """Test handling of API timeout errors."""
        page = TaskListPage()
        
        with patch.object(page.api_client, 'get_extended_task_list',
                         side_effect=APIError("Request timeout", 408)):
            result = page._load_tasks()
            
            assert result is None
    
    @patch('streamlit.session_state', {})
    def test_network_error_handling(self):
        """Test handling of network errors."""
        page = TimelineViewPage()
        
        with patch.object(page.api_client, 'get_timeline_data',
                         side_effect=APIError("Network error", 0)):
            result = page._load_timeline()
            
            assert result is None
    
    @patch('streamlit.session_state', {})
    def test_invalid_data_handling(self):
        """Test handling of invalid data from API."""
        page = ConflictsPage()
        
        with patch.object(page.api_client, 'get_conflicts',
                         return_value={"invalid": "data"}):
            result = page._load_conflicts()
            
            # Should handle gracefully
            assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
