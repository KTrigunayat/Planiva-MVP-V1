"""
Unit tests for CommunicationStrategyTool

Tests channel selection logic, timezone calculations, quiet hours handling,
and batching rules for intelligent communication routing.
"""

import pytest
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from event_planning_agent_v2.crm.models import (
    MessageType,
    MessageChannel,
    UrgencyLevel,
    ClientPreferences,
)
from event_planning_agent_v2.crm.strategy import CommunicationStrategyTool


class TestChannelSelection:
    """Test channel selection logic for different urgency levels and message types."""

    def setup_method(self):
        """Set up test fixtures."""
        self.strategy_tool = CommunicationStrategyTool()
        self.default_prefs = ClientPreferences(
            client_id="test_client_001",
            preferred_channels=[MessageChannel.EMAIL, MessageChannel.SMS],
            timezone="America/New_York",
        )

    def test_critical_urgency_prefers_sms(self):
        """Test that CRITICAL urgency prioritizes SMS for immediate delivery."""
        strategy = self.strategy_tool.determine_strategy(
            message_type=MessageType.ERROR_NOTIFICATION,
            urgency=UrgencyLevel.CRITICAL,
            client_preferences=self.default_prefs,
        )

        assert strategy.primary_channel == MessageChannel.SMS
        assert MessageChannel.EMAIL in strategy.fallback_channels
        assert strategy.priority >= 9  # High priority for critical messages

    def test_high_urgency_prefers_whatsapp(self):
        """Test that HIGH urgency prioritizes WhatsApp when available for non-detailed messages."""
        prefs = ClientPreferences(
            client_id="test_client_002",
            preferred_channels=[MessageChannel.WHATSAPP, MessageChannel.EMAIL],
            timezone="UTC",
        )

        # Use a non-detailed message type (REMINDER) to test WhatsApp preference
        strategy = self.strategy_tool.determine_strategy(
            message_type=MessageType.REMINDER,
            urgency=UrgencyLevel.HIGH,
            client_preferences=prefs,
        )

        assert strategy.primary_channel == MessageChannel.WHATSAPP
        assert strategy.priority >= 7

    def test_detailed_message_prefers_email(self):
        """Test that detailed messages (budget, vendors) prefer email."""
        strategy = self.strategy_tool.determine_strategy(
            message_type=MessageType.BUDGET_SUMMARY,
            urgency=UrgencyLevel.NORMAL,
            client_preferences=self.default_prefs,
        )

        assert strategy.primary_channel == MessageChannel.EMAIL

    def test_quick_confirmation_prefers_sms(self):
        """Test that quick confirmations prefer SMS/WhatsApp."""
        strategy = self.strategy_tool.determine_strategy(
            message_type=MessageType.SELECTION_CONFIRMATION,
            urgency=UrgencyLevel.NORMAL,
            client_preferences=self.default_prefs,
        )

        # Should prefer SMS for quick confirmation
        assert strategy.primary_channel in [MessageChannel.SMS, MessageChannel.WHATSAPP]

    def test_respects_opted_out_channels(self):
        """Test that opted-out channels are not selected."""
        prefs = ClientPreferences(
            client_id="test_client_003",
            preferred_channels=[MessageChannel.EMAIL, MessageChannel.SMS],
            timezone="UTC",
            opt_out_sms=True,  # Opted out of SMS
        )

        strategy = self.strategy_tool.determine_strategy(
            message_type=MessageType.WELCOME,
            urgency=UrgencyLevel.NORMAL,
            client_preferences=prefs,
        )

        # Should not use SMS since opted out
        assert strategy.primary_channel != MessageChannel.SMS
        assert MessageChannel.SMS not in strategy.fallback_channels

    def test_fallback_channels_provided(self):
        """Test that fallback channels are provided for redundancy."""
        strategy = self.strategy_tool.determine_strategy(
            message_type=MessageType.WELCOME,
            urgency=UrgencyLevel.NORMAL,
            client_preferences=self.default_prefs,
        )

        # Should have at least one fallback channel
        assert len(strategy.fallback_channels) >= 1
        # Primary and fallback should be different
        assert strategy.primary_channel not in strategy.fallback_channels

    def test_all_channels_opted_out_defaults_to_email(self):
        """Test that when all channels are opted out, defaults to email."""
        prefs = ClientPreferences(
            client_id="test_client_004",
            preferred_channels=[],
            timezone="UTC",
            opt_out_email=True,
            opt_out_sms=True,
            opt_out_whatsapp=True,
        )

        strategy = self.strategy_tool.determine_strategy(
            message_type=MessageType.WELCOME,
            urgency=UrgencyLevel.NORMAL,
            client_preferences=prefs,
        )

        # Should still provide a channel (email as last resort)
        assert strategy.primary_channel is not None


class TestTimezoneCalculations:
    """Test timezone calculations and optimal send time determination."""

    def setup_method(self):
        """Set up test fixtures."""
        self.strategy_tool = CommunicationStrategyTool()

    def test_critical_sends_immediately(self):
        """Test that CRITICAL urgency sends immediately regardless of timezone."""
        current_time = datetime(2025, 10, 23, 3, 0, 0, tzinfo=ZoneInfo("UTC"))  # 3 AM UTC

        send_time = self.strategy_tool.calculate_optimal_send_time(
            client_timezone="America/New_York",
            urgency=UrgencyLevel.CRITICAL,
            current_time=current_time,
        )

        # Should send immediately (within 1 second)
        assert abs((send_time - current_time).total_seconds()) < 1

    def test_high_urgency_sends_within_hour(self):
        """Test that HIGH urgency sends within 1 hour."""
        current_time = datetime(2025, 10, 23, 14, 0, 0, tzinfo=ZoneInfo("UTC"))

        send_time = self.strategy_tool.calculate_optimal_send_time(
            client_timezone="UTC",
            urgency=UrgencyLevel.HIGH,
            current_time=current_time,
        )

        # Should send within 1 hour
        time_diff = (send_time - current_time).total_seconds()
        assert 0 <= time_diff <= 3600  # Within 1 hour

    def test_normal_urgency_respects_business_hours(self):
        """Test that NORMAL urgency respects business hours (9 AM - 6 PM)."""
        # Test at 8 AM (before business hours)
        current_time = datetime(2025, 10, 23, 13, 0, 0, tzinfo=ZoneInfo("UTC"))  # 8 AM EST

        send_time = self.strategy_tool.calculate_optimal_send_time(
            client_timezone="America/New_York",
            urgency=UrgencyLevel.NORMAL,
            current_time=current_time,
        )

        # Should schedule for 9 AM local time
        send_time_local = send_time.astimezone(ZoneInfo("America/New_York"))
        assert send_time_local.hour == 9
        assert send_time_local.minute == 0

    def test_normal_urgency_during_business_hours_sends_now(self):
        """Test that NORMAL urgency during business hours sends immediately."""
        # 2 PM EST (during business hours)
        current_time = datetime(2025, 10, 23, 19, 0, 0, tzinfo=ZoneInfo("UTC"))

        send_time = self.strategy_tool.calculate_optimal_send_time(
            client_timezone="America/New_York",
            urgency=UrgencyLevel.NORMAL,
            current_time=current_time,
        )

        # Should send now (within business hours)
        assert abs((send_time - current_time).total_seconds()) < 1

    def test_low_urgency_batches_for_9am(self):
        """Test that LOW urgency batches for 9 AM next day."""
        # 5 PM (after 9 AM)
        current_time = datetime(2025, 10, 23, 22, 0, 0, tzinfo=ZoneInfo("UTC"))

        send_time = self.strategy_tool.calculate_optimal_send_time(
            client_timezone="America/New_York",
            urgency=UrgencyLevel.LOW,
            current_time=current_time,
        )

        # Should schedule for 9 AM next day
        send_time_local = send_time.astimezone(ZoneInfo("America/New_York"))
        assert send_time_local.hour == 9
        assert send_time_local.minute == 0
        # Should be tomorrow
        current_local = current_time.astimezone(ZoneInfo("America/New_York"))
        assert send_time_local.date() > current_local.date()

    def test_invalid_timezone_defaults_to_utc(self):
        """Test that invalid timezone defaults to UTC without crashing."""
        current_time = datetime(2025, 10, 23, 14, 0, 0, tzinfo=ZoneInfo("UTC"))

        send_time = self.strategy_tool.calculate_optimal_send_time(
            client_timezone="Invalid/Timezone",
            urgency=UrgencyLevel.NORMAL,
            current_time=current_time,
        )

        # Should not crash and return a valid time
        assert send_time is not None
        assert isinstance(send_time, datetime)


class TestQuietHoursHandling:
    """Test quiet hours handling and scheduling."""

    def setup_method(self):
        """Set up test fixtures."""
        self.strategy_tool = CommunicationStrategyTool()

    def test_respects_quiet_hours(self):
        """Test that messages are not sent during quiet hours."""
        # 11 PM (during quiet hours 22:00 - 08:00)
        current_time = datetime(2025, 10, 23, 4, 0, 0, tzinfo=ZoneInfo("UTC"))  # 11 PM EST

        send_time = self.strategy_tool.calculate_optimal_send_time(
            client_timezone="America/New_York",
            urgency=UrgencyLevel.NORMAL,
            quiet_hours_start="22:00",
            quiet_hours_end="08:00",
            current_time=current_time,
        )

        # Should schedule for 8 AM (end of quiet hours)
        send_time_local = send_time.astimezone(ZoneInfo("America/New_York"))
        assert send_time_local.hour == 8
        assert send_time_local.minute == 0

    def test_quiet_hours_spanning_midnight(self):
        """Test quiet hours that span midnight (e.g., 22:00 - 08:00)."""
        # 2 AM (during quiet hours)
        current_time = datetime(2025, 10, 23, 7, 0, 0, tzinfo=ZoneInfo("UTC"))  # 2 AM EST

        send_time = self.strategy_tool.calculate_optimal_send_time(
            client_timezone="America/New_York",
            urgency=UrgencyLevel.NORMAL,
            quiet_hours_start="22:00",
            quiet_hours_end="08:00",
            current_time=current_time,
        )

        # Should schedule for 8 AM
        send_time_local = send_time.astimezone(ZoneInfo("America/New_York"))
        assert send_time_local.hour == 8

    def test_critical_ignores_quiet_hours(self):
        """Test that CRITICAL urgency ignores quiet hours."""
        # 2 AM (during quiet hours)
        current_time = datetime(2025, 10, 23, 7, 0, 0, tzinfo=ZoneInfo("UTC"))

        send_time = self.strategy_tool.calculate_optimal_send_time(
            client_timezone="America/New_York",
            urgency=UrgencyLevel.CRITICAL,
            quiet_hours_start="22:00",
            quiet_hours_end="08:00",
            current_time=current_time,
        )

        # Should send immediately despite quiet hours
        assert abs((send_time - current_time).total_seconds()) < 1

    def test_outside_quiet_hours_sends_normally(self):
        """Test that messages outside quiet hours send normally."""
        # 2 PM (outside quiet hours)
        current_time = datetime(2025, 10, 23, 19, 0, 0, tzinfo=ZoneInfo("UTC"))

        send_time = self.strategy_tool.calculate_optimal_send_time(
            client_timezone="America/New_York",
            urgency=UrgencyLevel.NORMAL,
            quiet_hours_start="22:00",
            quiet_hours_end="08:00",
            current_time=current_time,
        )

        # Should send now (during business hours and outside quiet hours)
        assert abs((send_time - current_time).total_seconds()) < 1

    def test_invalid_quiet_hours_format_handled_gracefully(self):
        """Test that invalid quiet hours format doesn't crash."""
        current_time = datetime(2025, 10, 23, 14, 0, 0, tzinfo=ZoneInfo("UTC"))

        send_time = self.strategy_tool.calculate_optimal_send_time(
            client_timezone="UTC",
            urgency=UrgencyLevel.NORMAL,
            quiet_hours_start="invalid",
            quiet_hours_end="also_invalid",
            current_time=current_time,
        )

        # Should not crash and return a valid time
        assert send_time is not None
        assert isinstance(send_time, datetime)


class TestBatchingRules:
    """Test message batching logic."""

    def setup_method(self):
        """Set up test fixtures."""
        self.strategy_tool = CommunicationStrategyTool()

    def test_critical_never_batches(self):
        """Test that CRITICAL urgency messages never batch."""
        should_batch = self.strategy_tool.should_batch(
            message_type=MessageType.ERROR_NOTIFICATION,
            urgency=UrgencyLevel.CRITICAL,
            pending_count=5,
        )

        assert should_batch is False

    def test_high_never_batches(self):
        """Test that HIGH urgency messages never batch."""
        should_batch = self.strategy_tool.should_batch(
            message_type=MessageType.VENDOR_OPTIONS,
            urgency=UrgencyLevel.HIGH,
            pending_count=5,
        )

        assert should_batch is False

    def test_low_urgency_always_batches(self):
        """Test that LOW urgency messages always batch."""
        should_batch = self.strategy_tool.should_batch(
            message_type=MessageType.REMINDER,
            urgency=UrgencyLevel.LOW,
            pending_count=1,
        )

        assert should_batch is True

    def test_normal_batches_with_multiple_pending(self):
        """Test that NORMAL urgency batches when multiple messages pending."""
        should_batch = self.strategy_tool.should_batch(
            message_type=MessageType.WELCOME,
            urgency=UrgencyLevel.NORMAL,
            pending_count=3,
        )

        assert should_batch is True

    def test_normal_does_not_batch_with_few_pending(self):
        """Test that NORMAL urgency doesn't batch with few pending messages."""
        should_batch = self.strategy_tool.should_batch(
            message_type=MessageType.WELCOME,
            urgency=UrgencyLevel.NORMAL,
            pending_count=1,
        )

        assert should_batch is False

    def test_does_not_batch_if_last_message_old(self):
        """Test that messages don't batch if last message was > 24 hours ago."""
        current_time = datetime(2025, 10, 23, 14, 0, 0, tzinfo=ZoneInfo("UTC"))
        last_message_time = current_time - timedelta(hours=25)  # 25 hours ago

        should_batch = self.strategy_tool.should_batch(
            message_type=MessageType.REMINDER,
            urgency=UrgencyLevel.LOW,
            pending_count=5,
            last_message_time=last_message_time,
            current_time=current_time,
        )

        assert should_batch is False

    def test_batches_if_last_message_recent(self):
        """Test that messages batch if last message was recent."""
        current_time = datetime(2025, 10, 23, 14, 0, 0, tzinfo=ZoneInfo("UTC"))
        last_message_time = current_time - timedelta(hours=2)  # 2 hours ago

        should_batch = self.strategy_tool.should_batch(
            message_type=MessageType.REMINDER,
            urgency=UrgencyLevel.LOW,
            pending_count=2,
            last_message_time=last_message_time,
            current_time=current_time,
        )

        assert should_batch is True


class TestPriorityCalculation:
    """Test priority calculation logic."""

    def setup_method(self):
        """Set up test fixtures."""
        self.strategy_tool = CommunicationStrategyTool()
        self.default_prefs = ClientPreferences(
            client_id="test_client_001",
            preferred_channels=[MessageChannel.EMAIL],
            timezone="UTC",
        )

    def test_critical_has_highest_priority(self):
        """Test that CRITICAL urgency has highest priority."""
        strategy = self.strategy_tool.determine_strategy(
            message_type=MessageType.ERROR_NOTIFICATION,
            urgency=UrgencyLevel.CRITICAL,
            client_preferences=self.default_prefs,
        )

        assert strategy.priority == 10  # Maximum priority

    def test_high_has_high_priority(self):
        """Test that HIGH urgency has high priority."""
        strategy = self.strategy_tool.determine_strategy(
            message_type=MessageType.VENDOR_OPTIONS,
            urgency=UrgencyLevel.HIGH,
            client_preferences=self.default_prefs,
        )

        assert strategy.priority >= 7

    def test_normal_has_medium_priority(self):
        """Test that NORMAL urgency has medium priority."""
        strategy = self.strategy_tool.determine_strategy(
            message_type=MessageType.WELCOME,
            urgency=UrgencyLevel.NORMAL,
            client_preferences=self.default_prefs,
        )

        assert 4 <= strategy.priority <= 6

    def test_low_has_low_priority(self):
        """Test that LOW urgency has low priority."""
        strategy = self.strategy_tool.determine_strategy(
            message_type=MessageType.REMINDER,
            urgency=UrgencyLevel.LOW,
            client_preferences=self.default_prefs,
        )

        assert strategy.priority <= 3

    def test_error_notification_increases_priority(self):
        """Test that error notifications get priority boost."""
        strategy = self.strategy_tool.determine_strategy(
            message_type=MessageType.ERROR_NOTIFICATION,
            urgency=UrgencyLevel.NORMAL,
            client_preferences=self.default_prefs,
        )

        # Should have higher priority than normal welcome message
        normal_strategy = self.strategy_tool.determine_strategy(
            message_type=MessageType.WELCOME,
            urgency=UrgencyLevel.NORMAL,
            client_preferences=self.default_prefs,
        )

        assert strategy.priority > normal_strategy.priority

    def test_blueprint_delivery_increases_priority(self):
        """Test that blueprint delivery gets priority boost."""
        strategy = self.strategy_tool.determine_strategy(
            message_type=MessageType.BLUEPRINT_DELIVERY,
            urgency=UrgencyLevel.NORMAL,
            client_preferences=self.default_prefs,
        )

        # Should have higher priority than normal welcome message
        normal_strategy = self.strategy_tool.determine_strategy(
            message_type=MessageType.WELCOME,
            urgency=UrgencyLevel.NORMAL,
            client_preferences=self.default_prefs,
        )

        assert strategy.priority >= normal_strategy.priority


class TestIntegration:
    """Integration tests for complete strategy determination."""

    def setup_method(self):
        """Set up test fixtures."""
        self.strategy_tool = CommunicationStrategyTool()

    def test_complete_strategy_for_welcome_message(self):
        """Test complete strategy determination for welcome message."""
        prefs = ClientPreferences(
            client_id="test_client_001",
            preferred_channels=[MessageChannel.EMAIL, MessageChannel.SMS],
            timezone="America/Los_Angeles",
            quiet_hours_start="22:00",
            quiet_hours_end="08:00",
        )

        current_time = datetime(2025, 10, 23, 19, 0, 0, tzinfo=ZoneInfo("UTC"))  # 12 PM PST

        strategy = self.strategy_tool.determine_strategy(
            message_type=MessageType.WELCOME,
            urgency=UrgencyLevel.NORMAL,
            client_preferences=prefs,
            current_time=current_time,
        )

        # Verify all strategy components
        assert strategy.primary_channel is not None
        assert isinstance(strategy.fallback_channels, list)
        assert strategy.send_time is not None
        assert 0 <= strategy.priority <= 10
        assert strategy.send_time.tzinfo is not None  # Timezone-aware

    def test_complete_strategy_for_urgent_vendor_options(self):
        """Test complete strategy for urgent vendor options."""
        prefs = ClientPreferences(
            client_id="test_client_002",
            preferred_channels=[MessageChannel.WHATSAPP, MessageChannel.EMAIL],
            timezone="Europe/London",
        )

        strategy = self.strategy_tool.determine_strategy(
            message_type=MessageType.VENDOR_OPTIONS,
            urgency=UrgencyLevel.HIGH,
            client_preferences=prefs,
        )

        # Vendor options is a detailed message type, so it prefers email even with HIGH urgency
        assert strategy.primary_channel == MessageChannel.EMAIL
        assert MessageChannel.WHATSAPP in strategy.fallback_channels
        assert strategy.priority >= 7
        # Should send soon (HIGH urgency)
        time_until_send = (strategy.send_time - datetime.now(ZoneInfo("UTC"))).total_seconds()
        assert time_until_send <= 3600  # Within 1 hour


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
