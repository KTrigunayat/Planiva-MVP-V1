"""
Communication Strategy Tool for intelligent message routing and scheduling.

This module determines the optimal communication strategy based on message type,
urgency, client preferences, and timing constraints.
"""

import logging
from datetime import datetime, time, timedelta
from typing import List, Optional
from zoneinfo import ZoneInfo

from .models import (
    MessageType,
    MessageChannel,
    UrgencyLevel,
    CommunicationStrategy,
    ClientPreferences,
)

logger = logging.getLogger(__name__)


class CommunicationStrategyTool:
    """
    Intelligent decision-making tool for communication routing and scheduling.
    
    Responsibilities:
    - Analyze message type, urgency, and client preferences
    - Determine optimal communication channel(s)
    - Calculate delivery priority and timing
    - Batch non-urgent messages to avoid overwhelming clients
    - Respect client timezone and quiet hours
    """

    def __init__(self):
        """Initialize the Communication Strategy Tool."""
        # Channel priority by urgency level
        self._channel_priority = {
            UrgencyLevel.CRITICAL: [
                MessageChannel.SMS,
                MessageChannel.WHATSAPP,
                MessageChannel.EMAIL,
            ],
            UrgencyLevel.HIGH: [
                MessageChannel.WHATSAPP,
                MessageChannel.EMAIL,
                MessageChannel.SMS,
            ],
            UrgencyLevel.NORMAL: [
                MessageChannel.EMAIL,
                MessageChannel.WHATSAPP,
                MessageChannel.SMS,
            ],
            UrgencyLevel.LOW: [
                MessageChannel.EMAIL,
                MessageChannel.WHATSAPP,
                MessageChannel.SMS,
            ],
        }

        # Message types that require detailed information (prefer email)
        self._detailed_message_types = {
            MessageType.BUDGET_SUMMARY,
            MessageType.VENDOR_OPTIONS,
            MessageType.BLUEPRINT_DELIVERY,
        }

        # Message types that need quick confirmation (prefer SMS/WhatsApp)
        self._quick_confirmation_types = {
            MessageType.SELECTION_CONFIRMATION,
            MessageType.REMINDER,
        }

    def determine_strategy(
        self,
        message_type: MessageType,
        urgency: UrgencyLevel,
        client_preferences: ClientPreferences,
        current_time: Optional[datetime] = None,
    ) -> CommunicationStrategy:
        """
        Determine optimal communication strategy.
        
        Args:
            message_type: Type of message to send
            urgency: Message urgency level
            client_preferences: Client communication preferences
            current_time: Current timestamp (defaults to now)
            
        Returns:
            CommunicationStrategy with channel, timing, and priority
        """
        if current_time is None:
            current_time = datetime.now(ZoneInfo("UTC"))

        logger.debug(
            f"Determining strategy for message_type={message_type}, "
            f"urgency={urgency}, client_id={client_preferences.client_id}"
        )

        # Get available channels (not opted out)
        available_channels = client_preferences.get_available_channels()
        
        if not available_channels:
            logger.warning(
                f"No available channels for client {client_preferences.client_id}, "
                "defaulting to email"
            )
            available_channels = [MessageChannel.EMAIL]

        # Determine channel priority based on message type and urgency
        primary_channel, fallback_channels = self._select_channels(
            message_type=message_type,
            urgency=urgency,
            client_preferences=client_preferences,
            available_channels=available_channels,
        )

        # Calculate optimal send time
        send_time = self.calculate_optimal_send_time(
            client_timezone=client_preferences.timezone,
            urgency=urgency,
            quiet_hours_start=client_preferences.quiet_hours_start,
            quiet_hours_end=client_preferences.quiet_hours_end,
            current_time=current_time,
        )

        # Calculate priority (0-10, higher is more urgent)
        priority = self._calculate_priority(urgency, message_type)

        strategy = CommunicationStrategy(
            primary_channel=primary_channel,
            fallback_channels=fallback_channels,
            send_time=send_time,
            priority=priority,
            batch_with=None,  # Batching handled separately
        )

        logger.info(
            f"Strategy determined: primary={primary_channel}, "
            f"fallbacks={fallback_channels}, send_time={send_time}, priority={priority}"
        )

        return strategy

    def _select_channels(
        self,
        message_type: MessageType,
        urgency: UrgencyLevel,
        client_preferences: ClientPreferences,
        available_channels: List[MessageChannel],
    ) -> tuple[MessageChannel, List[MessageChannel]]:
        """
        Select primary and fallback channels based on message characteristics.
        
        Returns:
            Tuple of (primary_channel, fallback_channels)
        """
        # Start with urgency-based priority
        priority_order = self._channel_priority[urgency].copy()

        # Adjust based on message type
        if message_type in self._detailed_message_types:
            # Detailed messages prefer email
            if MessageChannel.EMAIL in priority_order:
                priority_order.remove(MessageChannel.EMAIL)
                priority_order.insert(0, MessageChannel.EMAIL)
        elif message_type in self._quick_confirmation_types:
            # Quick confirmations prefer SMS/WhatsApp
            if MessageChannel.SMS in priority_order:
                priority_order.remove(MessageChannel.SMS)
                priority_order.insert(0, MessageChannel.SMS)
            elif MessageChannel.WHATSAPP in priority_order:
                priority_order.remove(MessageChannel.WHATSAPP)
                priority_order.insert(0, MessageChannel.WHATSAPP)

        # Filter by client preferences (preferred channels first)
        preferred_available = [
            ch for ch in client_preferences.preferred_channels
            if ch in available_channels
        ]
        other_available = [
            ch for ch in available_channels
            if ch not in preferred_available
        ]

        # Combine: preferred channels first, then others, following priority order
        final_order = []
        for channel in priority_order:
            if channel in preferred_available and channel not in final_order:
                final_order.append(channel)
        for channel in priority_order:
            if channel in other_available and channel not in final_order:
                final_order.append(channel)

        # Ensure we have at least one channel
        if not final_order:
            final_order = available_channels

        primary_channel = final_order[0]
        fallback_channels = final_order[1:] if len(final_order) > 1 else []

        return primary_channel, fallback_channels

    def calculate_optimal_send_time(
        self,
        client_timezone: str,
        urgency: UrgencyLevel,
        quiet_hours_start: str = "22:00",
        quiet_hours_end: str = "08:00",
        current_time: Optional[datetime] = None,
    ) -> datetime:
        """
        Calculate optimal send time based on timezone and urgency.
        
        Args:
            client_timezone: Client's timezone (e.g., 'America/New_York')
            urgency: Message urgency level
            quiet_hours_start: Start of quiet hours (HH:MM format)
            quiet_hours_end: End of quiet hours (HH:MM format)
            current_time: Current timestamp (defaults to now)
            
        Returns:
            Optimal send time in UTC
        """
        if current_time is None:
            current_time = datetime.now(ZoneInfo("UTC"))

        # CRITICAL messages send immediately
        if urgency == UrgencyLevel.CRITICAL:
            logger.debug("CRITICAL urgency: sending immediately")
            return current_time

        # Convert to client timezone
        try:
            client_tz = ZoneInfo(client_timezone)
        except Exception as e:
            logger.warning(
                f"Invalid timezone '{client_timezone}': {e}. Using UTC."
            )
            client_tz = ZoneInfo("UTC")

        now_local = current_time.astimezone(client_tz)

        # Parse quiet hours
        quiet_start = self._parse_time(quiet_hours_start)
        quiet_end = self._parse_time(quiet_hours_end)

        # Check if currently in quiet hours
        in_quiet_hours = self._is_in_quiet_hours(
            now_local.time(), quiet_start, quiet_end
        )

        if in_quiet_hours and urgency != UrgencyLevel.CRITICAL:
            # Schedule for end of quiet hours
            send_local = now_local.replace(
                hour=quiet_end.hour,
                minute=quiet_end.minute,
                second=0,
                microsecond=0,
            )
            
            # If quiet hours end is earlier than current time (e.g., 08:00 < 23:00),
            # it means quiet hours span midnight, so schedule for next day
            if quiet_end < now_local.time():
                send_local += timedelta(days=1)

            logger.debug(
                f"In quiet hours: scheduling for {send_local} ({client_timezone})"
            )
            return send_local.astimezone(ZoneInfo("UTC"))

        # HIGH urgency: send within 1 hour
        if urgency == UrgencyLevel.HIGH:
            send_time = current_time + timedelta(minutes=5)  # Small buffer
            logger.debug(f"HIGH urgency: sending at {send_time}")
            return send_time

        # NORMAL urgency: send during business hours (9 AM - 6 PM)
        if urgency == UrgencyLevel.NORMAL:
            business_start = time(9, 0)
            business_end = time(18, 0)

            if business_start <= now_local.time() <= business_end:
                # Within business hours, send now
                logger.debug("NORMAL urgency: within business hours, sending now")
                return current_time
            else:
                # Outside business hours, schedule for next business start
                if now_local.time() < business_start:
                    # Before business hours today
                    send_local = now_local.replace(
                        hour=business_start.hour,
                        minute=business_start.minute,
                        second=0,
                        microsecond=0,
                    )
                else:
                    # After business hours, schedule for tomorrow
                    send_local = (now_local + timedelta(days=1)).replace(
                        hour=business_start.hour,
                        minute=business_start.minute,
                        second=0,
                        microsecond=0,
                    )
                
                logger.debug(
                    f"NORMAL urgency: outside business hours, "
                    f"scheduling for {send_local} ({client_timezone})"
                )
                return send_local.astimezone(ZoneInfo("UTC"))

        # LOW urgency: batch and send once daily at 9 AM
        if urgency == UrgencyLevel.LOW:
            send_local = now_local.replace(
                hour=9, minute=0, second=0, microsecond=0
            )
            
            # If 9 AM has passed today, schedule for tomorrow
            if now_local.time() >= time(9, 0):
                send_local += timedelta(days=1)

            logger.debug(
                f"LOW urgency: batching for {send_local} ({client_timezone})"
            )
            return send_local.astimezone(ZoneInfo("UTC"))

        # Default: send now
        return current_time

    def should_batch(
        self,
        message_type: MessageType,
        urgency: UrgencyLevel,
        pending_count: int,
        last_message_time: Optional[datetime] = None,
        current_time: Optional[datetime] = None,
    ) -> bool:
        """
        Determine if messages should be batched.
        
        Args:
            message_type: Type of message
            urgency: Message urgency level
            pending_count: Number of pending messages for this client
            last_message_time: Timestamp of last message sent
            current_time: Current timestamp (defaults to now)
            
        Returns:
            True if message should be batched, False otherwise
        """
        if current_time is None:
            current_time = datetime.now(ZoneInfo("UTC"))

        # Never batch CRITICAL or HIGH urgency messages
        if urgency in [UrgencyLevel.CRITICAL, UrgencyLevel.HIGH]:
            logger.debug(f"Not batching: urgency={urgency}")
            return False

        # Don't batch if last message was > 24 hours ago
        if last_message_time:
            time_since_last = current_time - last_message_time
            if time_since_last > timedelta(hours=24):
                logger.debug(
                    f"Not batching: last message was {time_since_last} ago"
                )
                return False

        # Batch LOW priority messages
        if urgency == UrgencyLevel.LOW:
            logger.debug("Batching: LOW urgency message")
            return True

        # Batch if we have multiple pending messages (max 3)
        if pending_count >= 3:
            logger.debug(f"Batching: {pending_count} pending messages")
            return True

        # Don't batch NORMAL urgency by default
        logger.debug("Not batching: NORMAL urgency, low pending count")
        return False

    def _calculate_priority(
        self, urgency: UrgencyLevel, message_type: MessageType
    ) -> int:
        """
        Calculate priority score (0-10, higher is more urgent).
        
        Args:
            urgency: Message urgency level
            message_type: Type of message
            
        Returns:
            Priority score between 0 and 10
        """
        # Base priority from urgency
        base_priority = {
            UrgencyLevel.CRITICAL: 10,
            UrgencyLevel.HIGH: 7,
            UrgencyLevel.NORMAL: 5,
            UrgencyLevel.LOW: 2,
        }

        priority = base_priority.get(urgency, 5)

        # Adjust based on message type
        if message_type == MessageType.ERROR_NOTIFICATION:
            priority = min(10, priority + 2)
        elif message_type == MessageType.BLUEPRINT_DELIVERY:
            priority = min(10, priority + 1)

        return priority

    def _parse_time(self, time_str: str) -> time:
        """
        Parse time string in HH:MM format.
        
        Args:
            time_str: Time string (e.g., "22:00")
            
        Returns:
            time object
        """
        try:
            parts = time_str.split(":")
            hour = int(parts[0])
            minute = int(parts[1])
            return time(hour, minute)
        except (ValueError, IndexError) as e:
            logger.warning(f"Invalid time format '{time_str}': {e}. Using 00:00.")
            return time(0, 0)

    def _is_in_quiet_hours(
        self, current: time, quiet_start: time, quiet_end: time
    ) -> bool:
        """
        Check if current time is within quiet hours.
        
        Handles quiet hours that span midnight (e.g., 22:00 - 08:00).
        
        Args:
            current: Current time
            quiet_start: Start of quiet hours
            quiet_end: End of quiet hours
            
        Returns:
            True if in quiet hours, False otherwise
        """
        if quiet_start < quiet_end:
            # Quiet hours within same day (e.g., 01:00 - 06:00)
            return quiet_start <= current <= quiet_end
        else:
            # Quiet hours span midnight (e.g., 22:00 - 08:00)
            return current >= quiet_start or current <= quiet_end
