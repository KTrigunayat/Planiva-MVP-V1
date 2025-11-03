"""
Unit tests for CRM Analytics Module

Tests metric calculations, filtering, and aggregation for analytics queries.
Covers requirements 10.1, 10.2, 10.3, 10.4, 10.5.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch
from typing import List, Tuple

from event_planning_agent_v2.crm.analytics import CRMAnalytics
from event_planning_agent_v2.crm.models import MessageChannel, MessageType, CommunicationStatus


@pytest.fixture
def mock_db_session():
    """Create a mock database session"""
    session = MagicMock()
    return session


@pytest.fixture
def mock_db_manager(mock_db_session):
    """Create a mock database manager"""
    manager = MagicMock()
    manager.get_sync_session.return_value.__enter__ = Mock(return_value=mock_db_session)
    manager.get_sync_session.return_value.__exit__ = Mock(return_value=None)
    return manager


@pytest.fixture
def analytics(mock_db_manager):
    """Create CRMAnalytics instance with mocked database"""
    return CRMAnalytics(db_manager=mock_db_manager)


class TestDeliveryRateMetrics:
    """Test delivery rate calculations"""
    
    def test_delivery_rate_basic_calculation(self, analytics, mock_db_session):
        """Test basic delivery rate calculation without filters"""
        # Mock query result: total_sent=100, delivered=95, failed=5, avg_time=2.5
        mock_result = Mock()
        mock_result.__getitem__ = lambda self, idx: [100, 95, 5, 2.5][idx]
        mock_db_session.execute.return_value.fetchone.return_value = mock_result
        
        result = analytics.get_delivery_rate()
        
        assert result['total_sent'] == 100
        assert result['delivered_count'] == 95
        assert result['failed_count'] == 5
        assert result['delivery_rate'] == 95.0
        assert result['failure_rate'] == 5.0
        assert result['avg_delivery_time_seconds'] == 2.5
    
    def test_delivery_rate_with_date_filter(self, analytics, mock_db_session):
        """Test delivery rate with date range filtering"""
        mock_result = Mock()
        mock_result.__getitem__ = lambda self, idx: [50, 48, 2, 1.8][idx]
        mock_db_session.execute.return_value.fetchone.return_value = mock_result
        
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        
        result = analytics.get_delivery_rate(start_date=start_date, end_date=end_date)
        
        assert result['total_sent'] == 50
        assert result['delivered_count'] == 48
        assert result['delivery_rate'] == 96.0
        
        # Verify query was called with date parameters
        call_args = mock_db_session.execute.call_args
        assert 'start_date' in call_args[0][1]
        assert 'end_date' in call_args[0][1]
    
    def test_delivery_rate_with_channel_filter(self, analytics, mock_db_session):
        """Test delivery rate filtered by channel"""
        mock_result = Mock()
        mock_result.__getitem__ = lambda self, idx: [60, 59, 1, 1.2][idx]
        mock_db_session.execute.return_value.fetchone.return_value = mock_result
        
        result = analytics.get_delivery_rate(channel=MessageChannel.EMAIL)
        
        assert result['total_sent'] == 60
        assert result['delivery_rate'] == 98.33
        
        # Verify channel parameter was passed
        call_args = mock_db_session.execute.call_args
        assert call_args[0][1]['channel'] == 'email'
    
    def test_delivery_rate_zero_sent(self, analytics, mock_db_session):
        """Test delivery rate when no messages sent"""
        mock_result = Mock()
        mock_result.__getitem__ = lambda self, idx: [0, 0, 0, 0][idx]
        mock_db_session.execute.return_value.fetchone.return_value = mock_result
        
        result = analytics.get_delivery_rate()
        
        assert result['total_sent'] == 0
        assert result['delivery_rate'] == 0
        assert result['failure_rate'] == 0


class TestOpenRateMetrics:
    """Test open rate calculations"""
    
    def test_open_rate_basic_calculation(self, analytics, mock_db_session):
        """Test basic open rate calculation"""
        # Mock result: delivered=100, opened=75, avg_time=300
        mock_result = Mock()
        mock_result.__getitem__ = lambda self, idx: [100, 75, 300.0][idx]
        mock_db_session.execute.return_value.fetchone.return_value = mock_result
        
        result = analytics.get_open_rate()
        
        assert result['delivered_count'] == 100
        assert result['opened_count'] == 75
        assert result['open_rate'] == 75.0
        assert result['avg_time_to_open_seconds'] == 300.0
    
    def test_open_rate_with_message_type_filter(self, analytics, mock_db_session):
        """Test open rate filtered by message type"""
        mock_result = Mock()
        mock_result.__getitem__ = lambda self, idx: [50, 40, 250.0][idx]
        mock_db_session.execute.return_value.fetchone.return_value = mock_result
        
        result = analytics.get_open_rate(message_type=MessageType.BUDGET_SUMMARY)
        
        assert result['open_rate'] == 80.0
        
        # Verify message type parameter
        call_args = mock_db_session.execute.call_args
        assert 'message_type' in call_args[0][1]
    
    def test_open_rate_zero_delivered(self, analytics, mock_db_session):
        """Test open rate when no messages delivered"""
        mock_result = Mock()
        mock_result.__getitem__ = lambda self, idx: [0, 0, 0][idx]
        mock_db_session.execute.return_value.fetchone.return_value = mock_result
        
        result = analytics.get_open_rate()
        
        assert result['open_rate'] == 0


class TestClickThroughRateMetrics:
    """Test click-through rate calculations"""
    
    def test_click_through_rate_basic(self, analytics, mock_db_session):
        """Test basic CTR calculation"""
        # Mock result: opened=100, clicked=25, avg_time=120
        mock_result = Mock()
        mock_result.__getitem__ = lambda self, idx: [100, 25, 120.0][idx]
        mock_db_session.execute.return_value.fetchone.return_value = mock_result
        
        result = analytics.get_click_through_rate()
        
        assert result['opened_count'] == 100
        assert result['clicked_count'] == 25
        assert result['click_through_rate'] == 25.0
        assert result['avg_time_to_click_seconds'] == 120.0
    
    def test_click_through_rate_with_filters(self, analytics, mock_db_session):
        """Test CTR with date and message type filters"""
        mock_result = Mock()
        mock_result.__getitem__ = lambda self, idx: [80, 32, 90.0][idx]
        mock_db_session.execute.return_value.fetchone.return_value = mock_result
        
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        
        result = analytics.get_click_through_rate(
            start_date=start_date,
            end_date=end_date,
            message_type=MessageType.VENDOR_RECOMMENDATION
        )
        
        assert result['click_through_rate'] == 40.0


class TestResponseRateMetrics:
    """Test response rate calculations"""
    
    def test_response_rate_basic(self, analytics, mock_db_session):
        """Test basic response rate calculation"""
        # Mock result: total_sent=100, response_count=30, avg_time=600
        mock_result = Mock()
        mock_result.__getitem__ = lambda self, idx: [100, 30, 600.0][idx]
        mock_db_session.execute.return_value.fetchone.return_value = mock_result
        
        result = analytics.get_response_rate()
        
        assert result['total_sent'] == 100
        assert result['response_count'] == 30
        assert result['response_rate'] == 30.0
        assert result['avg_response_time_seconds'] == 600.0
    
    def test_response_rate_with_channel_filter(self, analytics, mock_db_session):
        """Test response rate filtered by channel"""
        mock_result = Mock()
        mock_result.__getitem__ = lambda self, idx: [50, 20, 450.0][idx]
        mock_db_session.execute.return_value.fetchone.return_value = mock_result
        
        result = analytics.get_response_rate(channel=MessageChannel.SMS)
        
        assert result['response_rate'] == 40.0


class TestChannelPerformance:
    """Test channel performance comparison"""
    
    def test_channel_performance_aggregation(self, analytics, mock_db_session):
        """Test channel performance aggregation across all channels"""
        # Mock results for multiple channels
        mock_results = [
            ('email', 100, 95, 70, 20, 5, 2.5, 300.0),
            ('sms', 50, 48, 0, 0, 2, 1.2, None),
            ('whatsapp', 30, 29, 25, 10, 1, 1.8, 180.0)
        ]
        mock_db_session.execute.return_value.fetchall.return_value = mock_results
        
        result = analytics.get_channel_performance()
        
        assert len(result) == 3
        assert 'email' in result
        assert 'sms' in result
        assert 'whatsapp' in result
        
        # Verify email metrics
        email_metrics = result['email']
        assert email_metrics['total_sent'] == 100
        assert email_metrics['delivery_rate'] == 95.0
        assert email_metrics['open_rate'] == 73.68  # 70/95 * 100
        assert email_metrics['click_through_rate'] == 28.57  # 20/70 * 100
    
    def test_channel_performance_with_date_filter(self, analytics, mock_db_session):
        """Test channel performance with date filtering"""
        mock_results = [
            ('email', 50, 48, 35, 10, 2, 2.0, 250.0)
        ]
        mock_db_session.execute.return_value.fetchall.return_value = mock_results
        
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        
        result = analytics.get_channel_performance(start_date=start_date, end_date=end_date)
        
        assert len(result) == 1
        assert result['email']['delivery_rate'] == 96.0


class TestMessageTypePerformance:
    """Test message type performance analysis"""
    
    def test_message_type_performance_aggregation(self, analytics, mock_db_session):
        """Test message type performance aggregation"""
        mock_results = [
            ('budget_summary', 80, 76, 60, 15, 2.2, 280.0, 100.0),
            ('vendor_recommendation', 60, 58, 45, 20, 2.0, 320.0, 110.0),
            ('timeline_update', 40, 39, 30, 8, 1.8, 240.0, 90.0)
        ]
        mock_db_session.execute.return_value.fetchall.return_value = mock_results
        
        result = analytics.get_message_type_performance()
        
        assert len(result) == 3
        assert 'budget_summary' in result
        assert 'vendor_recommendation' in result
        
        # Verify budget_summary metrics
        budget_metrics = result['budget_summary']
        assert budget_metrics['total_sent'] == 80
        assert budget_metrics['delivery_rate'] == 95.0
        assert budget_metrics['open_rate'] == 78.95  # 60/76 * 100


class TestTimelineData:
    """Test timeline data generation"""
    
    def test_timeline_data_daily_granularity(self, analytics, mock_db_session):
        """Test timeline data with daily granularity"""
        mock_results = [
            (datetime(2024, 1, 1), 50, 48, 35, 10, 2),
            (datetime(2024, 1, 2), 60, 58, 42, 12, 2),
            (datetime(2024, 1, 3), 55, 53, 40, 11, 2)
        ]
        mock_db_session.execute.return_value.fetchall.return_value = mock_results
        
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 3)
        
        result = analytics.get_timeline_data(start_date, end_date, 'day')
        
        assert len(result) == 3
        assert result[0]['total_sent'] == 50
        assert result[0]['delivery_rate'] == 96.0
        assert result[1]['total_sent'] == 60
    
    def test_timeline_data_hourly_granularity(self, analytics, mock_db_session):
        """Test timeline data with hourly granularity"""
        mock_results = [
            (datetime(2024, 1, 1, 10), 10, 9, 7, 2, 1),
            (datetime(2024, 1, 1, 11), 15, 14, 10, 3, 1)
        ]
        mock_db_session.execute.return_value.fetchall.return_value = mock_results
        
        start_date = datetime(2024, 1, 1, 10)
        end_date = datetime(2024, 1, 1, 12)
        
        result = analytics.get_timeline_data(start_date, end_date, 'hour')
        
        assert len(result) == 2


class TestEngagementFunnel:
    """Test engagement funnel metrics"""
    
    def test_engagement_funnel_calculation(self, analytics, mock_db_session):
        """Test engagement funnel stage calculations"""
        # Mock result: sent=1000, delivered=950, opened=700, clicked=200
        mock_result = Mock()
        mock_result.__getitem__ = lambda self, idx: [1000, 950, 700, 200][idx]
        mock_db_session.execute.return_value.fetchone.return_value = mock_result
        
        result = analytics.get_engagement_funnel()
        
        # Verify funnel stages
        assert result['funnel_stages']['sent'] == 1000
        assert result['funnel_stages']['delivered'] == 950
        assert result['funnel_stages']['opened'] == 700
        assert result['funnel_stages']['clicked'] == 200
        
        # Verify conversion rates
        assert result['conversion_rates']['sent_to_delivered'] == 95.0
        assert result['conversion_rates']['delivered_to_opened'] == 73.68
        assert result['conversion_rates']['opened_to_clicked'] == 28.57
        assert result['conversion_rates']['sent_to_clicked'] == 20.0
        
        # Verify drop-off
        assert result['drop_off']['delivery_drop_off'] == 50
        assert result['drop_off']['open_drop_off'] == 250
        assert result['drop_off']['click_drop_off'] == 500


class TestPreferenceDistribution:
    """Test preference distribution analysis"""
    
    def test_preference_distribution_channels(self, analytics, mock_db_session):
        """Test channel preference distribution"""
        # Mock channel preference results
        channel_results = [
            ('email', 150),
            ('sms', 80),
            ('whatsapp', 70)
        ]
        
        # Mock opt-out results
        optout_result = Mock()
        optout_result.__getitem__ = lambda self, idx: [300, 10, 5, 3][idx]
        
        # Mock timezone results
        timezone_results = [
            ('America/New_York', 100),
            ('Europe/London', 80),
            ('Asia/Tokyo', 60)
        ]
        
        # Setup mock to return different results for different queries
        mock_db_session.execute.return_value.fetchall.side_effect = [
            channel_results,
            timezone_results
        ]
        mock_db_session.execute.return_value.fetchone.return_value = optout_result
        
        result = analytics.get_preference_distribution()
        
        # Verify channel preferences
        assert 'channel_preferences' in result
        assert result['channel_preferences']['email']['count'] == 150
        assert result['channel_preferences']['email']['percentage'] == 50.0
        
        # Verify opt-out statistics
        assert result['opt_out_statistics']['total_clients'] == 300
        assert result['opt_out_statistics']['email_optouts'] == 10
        assert result['opt_out_statistics']['email_optout_rate'] == 3.33


class TestComprehensiveAnalytics:
    """Test comprehensive analytics report"""
    
    def test_comprehensive_analytics_integration(self, analytics, mock_db_session):
        """Test comprehensive analytics combines all metrics"""
        # Setup mocks for all sub-queries
        mock_db_session.execute.return_value.fetchone.return_value = Mock()
        mock_db_session.execute.return_value.fetchall.return_value = []
        
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        
        result = analytics.get_comprehensive_analytics(start_date, end_date)
        
        # Verify all sections are present
        assert 'period' in result
        assert 'delivery_metrics' in result
        assert 'engagement_metrics' in result
        assert 'channel_performance' in result
        assert 'message_type_performance' in result
        assert 'engagement_funnel' in result
        assert 'preference_distribution' in result
        
        # Verify period information
        assert result['period']['start_date'] == start_date.isoformat()
        assert result['period']['end_date'] == end_date.isoformat()
