"""
Test Export Functionality

Tests for data export utilities including CSV and PDF exports.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

import pytest
from datetime import datetime
from utils.export import get_exporter, DataExporter


class TestDataExporter:
    """Test suite for DataExporter class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.exporter = get_exporter()
    
    # ========== Task Export Tests ==========
    
    def test_export_tasks_to_csv_basic(self):
        """Test basic task export to CSV."""
        tasks = [
            {
                'id': 'task-1',
                'name': 'Setup Venue',
                'description': 'Arrange venue setup',
                'priority': 'high',
                'status': 'pending',
                'start_date': '2024-01-15',
                'end_date': '2024-01-16',
                'estimated_duration': '2 days',
                'estimated_duration_hours': 16,
                'task_type': 'venue',
                'is_overdue': False,
                'has_errors': False,
                'has_warnings': False
            },
            {
                'id': 'task-2',
                'name': 'Catering Setup',
                'description': 'Setup catering area',
                'priority': 'medium',
                'status': 'in_progress',
                'start_date': '2024-01-17',
                'end_date': '2024-01-17',
                'estimated_duration': '1 day',
                'estimated_duration_hours': 8,
                'task_type': 'catering',
                'is_overdue': False,
                'has_errors': False,
                'has_warnings': False
            }
        ]
        
        csv_data = self.exporter.export_tasks_to_csv(tasks)
        
        # Verify CSV contains expected data
        assert 'Task Id' in csv_data or 'task_id' in csv_data.lower()
        assert 'Setup Venue' in csv_data
        assert 'Catering Setup' in csv_data
        assert 'high' in csv_data.lower()
        assert 'medium' in csv_data.lower()
        assert len(csv_data.split('\n')) > 2  # Header + at least 2 data rows
    
    def test_export_tasks_with_vendor(self):
        """Test task export with vendor information."""
        tasks = [
            {
                'id': 'task-1',
                'name': 'Photography',
                'description': 'Event photography',
                'priority': 'high',
                'status': 'pending',
                'assigned_vendor': {
                    'name': 'Pro Photos Inc',
                    'type': 'photographer',
                    'contact': 'contact@prophotos.com',
                    'fitness_score': 95
                }
            }
        ]
        
        csv_data = self.exporter.export_tasks_to_csv(tasks)
        
        assert 'Pro Photos Inc' in csv_data
        assert 'photographer' in csv_data.lower()
    
    def test_export_tasks_with_dependencies(self):
        """Test task export with dependencies."""
        tasks = [
            {
                'id': 'task-1',
                'name': 'Task with Dependencies',
                'description': 'Test task',
                'priority': 'high',
                'status': 'pending',
                'dependencies': [
                    {'task_id': 'dep-1', 'task_name': 'Dependency 1'},
                    {'task_id': 'dep-2', 'task_name': 'Dependency 2'}
                ]
            }
        ]
        
        csv_data = self.exporter.export_tasks_to_csv(tasks)
        
        assert 'Dependency 1' in csv_data
        assert 'Dependency 2' in csv_data
    
    def test_export_empty_tasks(self):
        """Test exporting empty task list."""
        tasks = []
        
        csv_data = self.exporter.export_tasks_to_csv(tasks)
        
        # Should still have header
        assert len(csv_data) > 0
        assert 'Task Id' in csv_data or 'task_id' in csv_data.lower()
    
    # ========== Communication Export Tests ==========
    
    def test_export_communications_to_csv_basic(self):
        """Test basic communication export to CSV."""
        communications = [
            {
                'communication_id': 'comm-1',
                'plan_id': 'plan-123',
                'client_id': 'client-456',
                'channel': 'email',
                'message_type': 'welcome',
                'status': 'sent',
                'delivery_status': 'delivered',
                'recipient': 'client@example.com',
                'subject': 'Welcome to Event Planning',
                'sent_at': '2024-01-15T10:00:00Z',
                'delivered_at': '2024-01-15T10:01:00Z',
                'open_count': 1,
                'click_count': 0
            },
            {
                'communication_id': 'comm-2',
                'plan_id': 'plan-123',
                'client_id': 'client-456',
                'channel': 'sms',
                'message_type': 'reminder',
                'status': 'sent',
                'delivery_status': 'delivered',
                'recipient': '+1234567890',
                'sent_at': '2024-01-16T09:00:00Z',
                'delivered_at': '2024-01-16T09:00:30Z'
            }
        ]
        
        csv_data = self.exporter.export_communications_to_csv(communications)
        
        # Verify CSV contains expected data
        assert 'comm-1' in csv_data
        assert 'comm-2' in csv_data
        assert 'email' in csv_data.lower()
        assert 'sms' in csv_data.lower()
        assert 'client@example.com' in csv_data
        assert len(csv_data.split('\n')) > 2  # Header + at least 2 data rows
    
    def test_export_communications_empty(self):
        """Test exporting empty communication list."""
        communications = []
        
        csv_data = self.exporter.export_communications_to_csv(communications)
        
        # Should still have header
        assert len(csv_data) > 0
        assert 'Communication Id' in csv_data or 'communication_id' in csv_data.lower()
    
    # ========== Analytics Export Tests ==========
    
    def test_export_analytics_to_csv_basic(self):
        """Test basic analytics export to CSV."""
        analytics_data = {
            'metrics': {
                'total_sent': 100,
                'total_delivered': 95,
                'total_opened': 80,
                'total_clicked': 40,
                'total_failed': 5
            },
            'channel_performance': [
                {
                    'channel': 'email',
                    'sent': 60,
                    'delivered': 58,
                    'opened': 50,
                    'clicked': 30,
                    'delivery_rate': 96.7,
                    'open_rate': 86.2,
                    'click_through_rate': 60.0
                },
                {
                    'channel': 'sms',
                    'sent': 40,
                    'delivered': 37,
                    'opened': 30,
                    'clicked': 10,
                    'delivery_rate': 92.5,
                    'open_rate': 81.1,
                    'click_through_rate': 33.3
                }
            ],
            'message_type_performance': [
                {
                    'message_type': 'welcome',
                    'sent': 50,
                    'delivered': 48,
                    'opened': 40,
                    'clicked': 20,
                    'delivery_rate': 96.0,
                    'open_rate': 83.3,
                    'click_through_rate': 50.0
                }
            ],
            'timeline_data': [
                {
                    'date': '2024-01-15',
                    'sent': 30,
                    'delivered': 28,
                    'opened': 25,
                    'clicked': 15
                }
            ]
        }
        
        csv_data = self.exporter.export_analytics_to_csv(analytics_data)
        
        # Verify CSV contains expected sections
        assert 'KEY METRICS' in csv_data
        assert 'CHANNEL PERFORMANCE' in csv_data
        assert 'MESSAGE TYPE PERFORMANCE' in csv_data
        assert 'TIMELINE DATA' in csv_data
        
        # Verify data values
        assert '100' in csv_data  # total_sent
        assert 'email' in csv_data.lower()
        assert 'sms' in csv_data.lower()
        assert 'welcome' in csv_data.lower()
    
    def test_export_analytics_to_csv_dict_format(self):
        """Test analytics export with dict format for channel/message performance."""
        analytics_data = {
            'metrics': {
                'total_sent': 50
            },
            'channel_performance': {
                'email': {
                    'total_sent': 30,
                    'delivered_count': 28,
                    'delivery_rate': 93.3
                },
                'sms': {
                    'total_sent': 20,
                    'delivered_count': 19,
                    'delivery_rate': 95.0
                }
            },
            'message_type_performance': {
                'welcome': {
                    'total_sent': 25,
                    'delivered_count': 24,
                    'delivery_rate': 96.0
                }
            }
        }
        
        csv_data = self.exporter.export_analytics_to_csv(analytics_data)
        
        assert 'email' in csv_data.lower()
        assert 'sms' in csv_data.lower()
        assert 'welcome' in csv_data.lower()
    
    def test_export_analytics_to_pdf_basic(self):
        """Test basic analytics export to PDF."""
        analytics_data = {
            'metrics': {
                'total_sent': 100,
                'total_delivered': 95,
                'total_opened': 80
            },
            'channel_performance': [
                {
                    'channel': 'email',
                    'sent': 60,
                    'delivered': 58,
                    'delivery_rate': 96.7,
                    'open_rate': 86.2,
                    'click_through_rate': 60.0
                }
            ]
        }
        
        try:
            pdf_data = self.exporter.export_analytics_to_pdf(analytics_data)
            
            # Verify PDF was generated
            assert isinstance(pdf_data, bytes)
            assert len(pdf_data) > 0
            
            # PDF should start with PDF header
            assert pdf_data[:4] == b'%PDF'
            
        except ImportError:
            # ReportLab not installed - skip test
            pytest.skip("ReportLab not installed")
    
    def test_export_analytics_to_pdf_with_title(self):
        """Test PDF export with custom title."""
        analytics_data = {
            'metrics': {
                'total_sent': 50
            }
        }
        
        try:
            pdf_data = self.exporter.export_analytics_to_pdf(
                analytics_data,
                title="Custom Analytics Report"
            )
            
            assert isinstance(pdf_data, bytes)
            assert len(pdf_data) > 0
            
        except ImportError:
            pytest.skip("ReportLab not installed")
    
    # ========== Singleton Tests ==========
    
    def test_get_exporter_singleton(self):
        """Test that get_exporter returns singleton instance."""
        exporter1 = get_exporter()
        exporter2 = get_exporter()
        
        assert exporter1 is exporter2
        assert isinstance(exporter1, DataExporter)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
