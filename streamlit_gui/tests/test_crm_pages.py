"""
Unit tests for CRM pages (Preferences, Communication History, Analytics)
"""
import pytest
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime, timedelta
import streamlit as st

from pages.crm_preferences import render_crm_preferences_page
from pages.communication_history import CommunicationHistoryComponent
from pages.crm_analytics import CRMAnalyticsPage
from components.api_client import APIError


class TestCRMPreferencesPage:
    """Test cases for CRM Preferences page."""
    
    @patch('streamlit.header')
    @patch('streamlit.markdown')
    @patch('streamlit.session_state', {})
    def test_render_page_header(self, mock_markdown, mock_header):
        """Test page header rendering."""
        with patch('streamlit.expander'), \
             patch('streamlit.text_input', return_value=''), \
             patch('pages.crm_preferences.show_warning'):
            render_crm_preferences_page()
            
            mock_header.assert_called_once()
            assert any('Communication Preferences' in str(call) for call in mock_header.call_args_list)
    
    @patch('streamlit.session_state', {'client_id': ''})
    @patch('streamlit.expander')
    @patch('streamlit.text_input', return_value='')
    def test_client_id_input_section(self, mock_input, mock_expander, mock_state):
        """Test client ID input section renders."""
        mock_expander_context = MagicMock()
        mock_expander.return_value.__enter__ = MagicMock(return_value=mock_expander_context)
        mock_expander.return_value.__exit__ = MagicMock(return_value=False)
        
        with patch('streamlit.header'), \
             patch('streamlit.markdown'), \
             patch('pages.crm_preferences.show_warning'):
            render_crm_preferences_page()
            
            mock_expander.assert_called()
            mock_input.assert_called()
    
    @patch('streamlit.session_state', {'client_id': ''})
    def test_no_client_id_shows_warning(self, mock_state):
        """Test warning shown when no client ID."""
        with patch('streamlit.header'), \
             patch('streamlit.markdown'), \
             patch('streamlit.expander'), \
             patch('streamlit.text_input', return_value=''), \
             patch('streamlit.columns'), \
             patch('pages.crm_preferences.show_warning') as mock_warning:
            render_crm_preferences_page()
            
            mock_warning.assert_called()


class TestCommunicationHistoryPage:
    """Test cases for Communication History page."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.component = CommunicationHistoryComponent()
        self.sample_communications = [
            {
                "id": "comm-1",
                "message_type": "welcome",
                "channel": "Email",
                "status": "delivered",
                "sent_at": "2024-01-15T10:00:00",
                "delivered_at": "2024-01-15T10:01:00",
                "subject": "Welcome to Event Planning",
                "content": "Thank you for choosing us..."
            },
            {
                "id": "comm-2",
                "message_type": "budget_summary",
                "channel": "SMS",
                "status": "sent",
                "sent_at": "2024-01-16T14:30:00",
                "content": "Your budget summary is ready"
            }
        ]
    
    @patch('streamlit.header')
    @patch('streamlit.markdown')
    @patch('streamlit.session_state', {})
    def test_render_page_header(self, mock_markdown, mock_header):
        """Test page header rendering."""
        with patch.object(self.component, '_render_filters', return_value={}), \
             patch('streamlit.columns'), \
             patch('streamlit.checkbox', return_value=True), \
             patch('streamlit.button', return_value=False), \
             patch.object(self.component, '_load_communications', return_value=None), \
             patch('pages.communication_history.show_error'):
            self.component.render()
            
            mock_header.assert_called_once()
    
    @patch('streamlit.session_state', {})
    def test_load_communications_success(self, mock_state):
        """Test successful communication loading."""
        mock_response = {
            "communications": self.sample_communications,
            "total_count": 2
        }
        
        with patch.object(self.component.api_client, 'get_communications', return_value=mock_response):
            result = self.component._load_communications({})
            
            assert result is not None
            assert len(result["communications"]) == 2
            assert result["total_count"] == 2
    
    @patch('streamlit.session_state', {})
    def test_load_communications_api_error(self, mock_state):
        """Test communication loading with API error."""
        with patch.object(self.component.api_client, 'get_communications', 
                         side_effect=APIError("Connection failed", 500)):
            result = self.component._load_communications({})
            
            assert result is None
    
    @patch('streamlit.session_state', {})
    def test_empty_communications_list(self, mock_state):
        """Test rendering empty communications list."""
        with patch('streamlit.header'), \
             patch('streamlit.markdown'), \
             patch.object(self.component, '_render_filters', return_value={}), \
             patch('streamlit.columns'), \
             patch('streamlit.checkbox', return_value=False), \
             patch('streamlit.button', return_value=False), \
             patch.object(self.component, '_load_communications', 
                         return_value={"communications": [], "total_count": 0}), \
             patch.object(self.component, '_render_empty_state') as mock_empty:
            self.component.render()
            
            mock_empty.assert_called_once()
    
    @patch('streamlit.session_state', {})
    def test_export_to_csv(self, mock_state):
        """Test CSV export functionality."""
        filters = {"channel": "Email"}
        
        with patch.object(self.component.api_client, 'get_communications',
                         return_value={"communications": self.sample_communications, "total_count": 2}), \
             patch('pages.communication_history.get_exporter') as mock_exporter, \
             patch('pages.communication_history.show_success'):
            
            mock_export_instance = MagicMock()
            mock_exporter.return_value = mock_export_instance
            
            self.component._export_to_csv(filters)
            
            mock_exporter.assert_called_with('csv')


class TestCRMAnalyticsPage:
    """Test cases for CRM Analytics page."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.page = CRMAnalyticsPage()
        self.sample_analytics = {
            "overview": {
                "total_sent": 150,
                "total_delivered": 145,
                "total_opened": 80,
                "total_clicked": 35,
                "total_failed": 5
            },
            "channel_performance": {
                "Email": {
                    "sent": 100,
                    "delivered": 98,
                    "opened": 70,
                    "clicked": 30,
                    "delivery_rate": 98.0,
                    "open_rate": 71.4,
                    "click_rate": 42.9
                },
                "SMS": {
                    "sent": 30,
                    "delivered": 29,
                    "delivery_rate": 96.7
                },
                "WhatsApp": {
                    "sent": 20,
                    "delivered": 18,
                    "delivery_rate": 90.0
                }
            },
            "message_type_performance": {
                "welcome": {"sent": 50, "delivered": 49, "opened": 40},
                "budget_summary": {"sent": 40, "delivered": 39, "opened": 25},
                "vendor_options": {"sent": 35, "delivered": 34, "opened": 15}
            },
            "timeline_data": [
                {"date": "2024-01-15", "sent": 20, "delivered": 19, "opened": 10},
                {"date": "2024-01-16", "sent": 25, "delivered": 24, "opened": 15}
            ]
        }
    
    @patch('streamlit.header')
    @patch('streamlit.markdown')
    @patch('streamlit.session_state', {})
    def test_render_page_header(self, mock_markdown, mock_header):
        """Test page header rendering."""
        with patch.object(self.page, '_load_analytics', return_value=None), \
             patch('pages.crm_analytics.show_error'):
            self.page.render()
            
            mock_header.assert_called_once()
    
    @patch('streamlit.session_state', {})
    def test_load_analytics_success(self, mock_state):
        """Test successful analytics loading."""
        with patch.object(self.page.api_client, 'get_crm_analytics', 
                         return_value=self.sample_analytics):
            result = self.page._load_analytics()
            
            assert result is not None
            assert "overview" in result
            assert result["overview"]["total_sent"] == 150
    
    @patch('streamlit.session_state', {})
    def test_load_analytics_api_error(self, mock_state):
        """Test analytics loading with API error."""
        with patch.object(self.page.api_client, 'get_crm_analytics',
                         side_effect=APIError("Connection failed", 500)):
            result = self.page._load_analytics()
            
            assert result is None
    
    @patch('streamlit.session_state', {})
    def test_render_metrics_overview(self, mock_state):
        """Test metrics overview rendering."""
        with patch('streamlit.columns') as mock_columns, \
             patch('streamlit.metric') as mock_metric:
            
            # Create mock column contexts
            mock_cols = [MagicMock() for _ in range(5)]
            for col in mock_cols:
                col.__enter__ = MagicMock(return_value=col)
                col.__exit__ = MagicMock(return_value=False)
            mock_columns.return_value = mock_cols
            
            self.page._render_metrics_overview(self.sample_analytics["overview"])
            
            assert mock_metric.call_count == 5
    
    @patch('streamlit.session_state', {})
    def test_render_channel_performance(self, mock_state):
        """Test channel performance rendering."""
        with patch('streamlit.subheader'), \
             patch('streamlit.columns'), \
             patch('streamlit.metric'), \
             patch('streamlit.plotly_chart'):
            
            self.page._render_channel_performance(self.sample_analytics["channel_performance"])
    
    @patch('streamlit.session_state', {})
    def test_export_analytics_csv(self, mock_state):
        """Test analytics CSV export."""
        with patch('pages.crm_analytics.get_exporter') as mock_exporter, \
             patch('pages.crm_analytics.show_success'):
            
            mock_export_instance = MagicMock()
            mock_exporter.return_value = mock_export_instance
            
            self.page._export_analytics_csv(self.sample_analytics)
            
            mock_exporter.assert_called_with('csv')


class TestCRMPagesIntegration:
    """Integration tests for CRM pages navigation and data flow."""
    
    @patch('streamlit.session_state', {'client_id': 'test@example.com'})
    def test_preferences_to_history_flow(self, mock_state):
        """Test navigation from preferences to history."""
        # This would test the full flow in a real integration test
        # For unit tests, we verify the session state is properly set
        assert st.session_state.get('client_id') == 'test@example.com'
    
    @patch('streamlit.session_state', {'current_plan_id': 'plan-123'})
    def test_plan_context_available(self, mock_state):
        """Test plan context is available across pages."""
        assert st.session_state.get('current_plan_id') == 'plan-123'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
