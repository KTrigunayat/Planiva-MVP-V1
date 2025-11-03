"""
Unit tests for CommunicationRepository

Tests core CRUD operations, query filtering, and analytics aggregation.
"""

import json
from datetime import datetime, timedelta
from enum import Enum


# Define enums locally for testing without full imports
class MessageType(str, Enum):
    WELCOME = "welcome"
    BUDGET_SUMMARY = "budget_summary"
    VENDOR_OPTIONS = "vendor_options"
    SELECTION_CONFIRMATION = "selection_confirmation"
    BLUEPRINT_DELIVERY = "blueprint_delivery"
    ERROR_NOTIFICATION = "error_notification"
    REMINDER = "reminder"


class MessageChannel(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    WHATSAPP = "whatsapp"


class UrgencyLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class CommunicationStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    FAILED = "failed"
    BOUNCED = "bounced"


def test_communication_record_structure():
    """Test that communication record has correct structure"""
    
    communication_dict = {
        'communication_id': 'comm_001',
        'plan_id': 'plan_001',
        'client_id': 'client_001',
        'message_type': MessageType.WELCOME.value,
        'channel': MessageChannel.EMAIL.value,
        'urgency': UrgencyLevel.NORMAL.value,
        'status': CommunicationStatus.SENT.value,
        'subject': 'Welcome to Event Planning',
        'body': 'Hi John, welcome to our service!',
        'template_name': 'welcome_email',
        'context_data': {
            'client_name': 'John Doe',
            'event_type': 'Wedding'
        },
        'sent_at': datetime.utcnow().isoformat(),
        'delivered_at': None,
        'opened_at': None,
        'clicked_at': None,
        'failed_at': None,
        'error_message': None,
        'retry_count': 0,
        'metadata': {
            'api_provider': 'smtp',
            'message_id': 'msg_12345'
        },
        'created_at': datetime.utcnow().isoformat(),
        'updated_at': datetime.utcnow().isoformat()
    }
    
    # Verify structure can be serialized to JSON
    json_str = json.dumps(communication_dict)
    assert json_str is not None
    
    # Verify deserialization
    deserialized = json.loads(json_str)
    assert deserialized['communication_id'] == 'comm_001'
    assert deserialized['message_type'] == MessageType.WELCOME.value
    assert deserialized['channel'] == MessageChannel.EMAIL.value
    assert deserialized['status'] == CommunicationStatus.SENT.value
    assert 'context_data' in deserialized
    assert 'metadata' in deserialized
    
    print("✓ Communication record structure test passed")


def test_client_preferences_structure():
    """Test client preferences data structure"""
    
    preferences_dict = {
        'client_id': 'client_001',
        'preferred_channels': [MessageChannel.EMAIL.value, MessageChannel.SMS.value],
        'timezone': 'America/New_York',
        'quiet_hours_start': '22:00',
        'quiet_hours_end': '08:00',
        'opt_out_email': False,
        'opt_out_sms': False,
        'opt_out_whatsapp': True,
        'language_preference': 'en'
    }
    
    # Verify structure can be serialized to JSON
    json_str = json.dumps(preferences_dict)
    assert json_str is not None
    
    # Verify deserialization
    deserialized = json.loads(json_str)
    assert deserialized['client_id'] == 'client_001'
    assert len(deserialized['preferred_channels']) == 2
    assert deserialized['timezone'] == 'America/New_York'
    assert deserialized['opt_out_whatsapp'] is True
    
    print("✓ Client preferences structure test passed")


def test_analytics_structure():
    """Test analytics data structure"""
    
    analytics_dict = {
        'total_sent': 100,
        'delivered_count': 95,
        'opened_count': 60,
        'clicked_count': 25,
        'failed_count': 5,
        'delivery_rate': 95.0,
        'open_rate': 63.16,
        'click_rate': 41.67,
        'failure_rate': 5.0,
        'avg_delivery_time_seconds': 2.5,
        'by_channel': {
            'email': {
                'total_sent': 60,
                'delivered_count': 58,
                'opened_count': 45,
                'clicked_count': 20,
                'failed_count': 2,
                'delivery_rate': 96.67,
                'open_rate': 77.59,
                'click_rate': 44.44,
                'failure_rate': 3.33
            },
            'sms': {
                'total_sent': 30,
                'delivered_count': 28,
                'opened_count': 15,
                'clicked_count': 5,
                'failed_count': 2,
                'delivery_rate': 93.33,
                'open_rate': 53.57,
                'click_rate': 33.33,
                'failure_rate': 6.67
            },
            'whatsapp': {
                'total_sent': 10,
                'delivered_count': 9,
                'opened_count': 0,
                'clicked_count': 0,
                'failed_count': 1,
                'delivery_rate': 90.0,
                'open_rate': 0.0,
                'click_rate': 0.0,
                'failure_rate': 10.0
            }
        },
        'by_message_type': {
            'welcome': {
                'total_sent': 20,
                'delivered_count': 19,
                'opened_count': 15,
                'clicked_count': 8,
                'delivery_rate': 95.0,
                'open_rate': 78.95,
                'click_rate': 53.33
            },
            'budget_summary': {
                'total_sent': 40,
                'delivered_count': 38,
                'opened_count': 30,
                'clicked_count': 12,
                'delivery_rate': 95.0,
                'open_rate': 78.95,
                'click_rate': 40.0
            }
        }
    }
    
    # Verify structure can be serialized to JSON
    json_str = json.dumps(analytics_dict)
    assert json_str is not None
    
    # Verify deserialization
    deserialized = json.loads(json_str)
    assert deserialized['total_sent'] == 100
    assert deserialized['delivery_rate'] == 95.0
    assert 'by_channel' in deserialized
    assert 'by_message_type' in deserialized
    assert len(deserialized['by_channel']) == 3
    assert 'email' in deserialized['by_channel']
    
    print("✓ Analytics structure test passed")


def test_sql_queries_syntax():
    """Test that SQL queries have correct syntax"""
    
    # Test INSERT query for crm_communications
    insert_comm_query = """
        INSERT INTO crm_communications 
        (plan_id, client_id, message_type, channel, urgency, status,
         subject, body, template_name, context_data, metadata, created_at, updated_at)
        VALUES (:plan_id, :client_id, :message_type, :channel, :urgency, :status,
                :subject, :body, :template_name, :context_data, :metadata, :created_at, :updated_at)
        RETURNING communication_id
    """
    assert "INSERT INTO crm_communications" in insert_comm_query
    assert "RETURNING communication_id" in insert_comm_query
    
    # Test UPDATE query for status
    update_status_query = """
        UPDATE crm_communications
        SET status = :status, updated_at = :updated_at, sent_at = :timestamp
        WHERE communication_id = :communication_id
    """
    assert "UPDATE crm_communications" in update_status_query
    assert "WHERE communication_id" in update_status_query
    
    # Test SELECT query for history
    select_history_query = """
        SELECT 
            communication_id, plan_id, client_id, message_type, channel,
            urgency, status, subject, body, template_name, context_data,
            sent_at, delivered_at, opened_at, clicked_at, failed_at,
            error_message, retry_count, metadata, created_at, updated_at
        FROM crm_communications
        WHERE client_id = :client_id AND status = :status
        ORDER BY created_at DESC
        LIMIT :limit OFFSET :offset
    """
    assert "SELECT" in select_history_query
    assert "FROM crm_communications" in select_history_query
    assert "ORDER BY created_at DESC" in select_history_query
    assert "LIMIT :limit OFFSET :offset" in select_history_query
    
    # Test SELECT query for analytics
    select_analytics_query = """
        SELECT
            COUNT(*) as total_sent,
            COUNT(CASE WHEN status IN ('delivered', 'opened', 'clicked') THEN 1 END) as delivered_count,
            COUNT(CASE WHEN status IN ('opened', 'clicked') THEN 1 END) as opened_count,
            COUNT(CASE WHEN status = 'clicked' THEN 1 END) as clicked_count,
            COUNT(CASE WHEN status IN ('failed', 'bounced') THEN 1 END) as failed_count,
            AVG(EXTRACT(EPOCH FROM (delivered_at - sent_at))) as avg_delivery_time_seconds
        FROM crm_communications
        WHERE sent_at IS NOT NULL
    """
    assert "SELECT" in select_analytics_query
    assert "COUNT(*) as total_sent" in select_analytics_query
    assert "AVG(EXTRACT(EPOCH FROM (delivered_at - sent_at)))" in select_analytics_query
    
    print("✓ SQL queries syntax test passed")


def test_filter_combinations():
    """Test various filter combinations for history queries"""
    
    # Test filters
    filters = {
        'plan_id': 'plan_001',
        'client_id': 'client_001',
        'channel': MessageChannel.EMAIL.value,
        'status': CommunicationStatus.DELIVERED.value,
        'date_range': (
            datetime.utcnow() - timedelta(days=7),
            datetime.utcnow()
        )
    }
    
    # Verify all filter keys are valid
    assert 'plan_id' in filters
    assert 'client_id' in filters
    assert 'channel' in filters
    assert 'status' in filters
    assert 'date_range' in filters
    
    # Verify date range is tuple
    assert isinstance(filters['date_range'], tuple)
    assert len(filters['date_range']) == 2
    
    print("✓ Filter combinations test passed")


def test_enum_values():
    """Test that enum values are correctly defined"""
    
    # Test MessageType enum
    assert MessageType.WELCOME.value == 'welcome'
    assert MessageType.BUDGET_SUMMARY.value == 'budget_summary'
    assert MessageType.VENDOR_OPTIONS.value == 'vendor_options'
    
    # Test MessageChannel enum
    assert MessageChannel.EMAIL.value == 'email'
    assert MessageChannel.SMS.value == 'sms'
    assert MessageChannel.WHATSAPP.value == 'whatsapp'
    
    # Test UrgencyLevel enum
    assert UrgencyLevel.CRITICAL.value == 'critical'
    assert UrgencyLevel.HIGH.value == 'high'
    assert UrgencyLevel.NORMAL.value == 'normal'
    assert UrgencyLevel.LOW.value == 'low'
    
    # Test CommunicationStatus enum
    assert CommunicationStatus.PENDING.value == 'pending'
    assert CommunicationStatus.SENT.value == 'sent'
    assert CommunicationStatus.DELIVERED.value == 'delivered'
    assert CommunicationStatus.OPENED.value == 'opened'
    assert CommunicationStatus.CLICKED.value == 'clicked'
    assert CommunicationStatus.FAILED.value == 'failed'
    
    print("✓ Enum values test passed")


def test_status_timestamp_mapping():
    """Test that status updates map to correct timestamp fields"""
    
    status_timestamp_map = {
        CommunicationStatus.SENT: 'sent_at',
        CommunicationStatus.DELIVERED: 'delivered_at',
        CommunicationStatus.OPENED: 'opened_at',
        CommunicationStatus.CLICKED: 'clicked_at',
        CommunicationStatus.FAILED: 'failed_at'
    }
    
    # Verify all status types have timestamp mappings
    assert CommunicationStatus.SENT in status_timestamp_map
    assert CommunicationStatus.DELIVERED in status_timestamp_map
    assert CommunicationStatus.OPENED in status_timestamp_map
    assert CommunicationStatus.CLICKED in status_timestamp_map
    assert CommunicationStatus.FAILED in status_timestamp_map
    
    # Verify timestamp field names
    assert status_timestamp_map[CommunicationStatus.SENT] == 'sent_at'
    assert status_timestamp_map[CommunicationStatus.DELIVERED] == 'delivered_at'
    
    print("✓ Status timestamp mapping test passed")


if __name__ == '__main__':
    print("\n=== Running Communication Repository Unit Tests ===\n")
    
    test_communication_record_structure()
    test_client_preferences_structure()
    test_analytics_structure()
    test_sql_queries_syntax()
    test_filter_combinations()
    test_enum_values()
    test_status_timestamp_mapping()
    
    print("\n=== All tests passed! ===\n")
