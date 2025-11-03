"""
Communication Repository

Database persistence layer for CRM Communication Engine.
Handles saving and retrieving communication records, client preferences, and analytics.
"""

import logging
import json
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from contextlib import contextmanager
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError
from sqlalchemy.orm import Session
from uuid import UUID

from ..database.connection import get_sync_session, DatabaseConnectionManager
from .models import (
    CommunicationStatus,
    MessageChannel,
    MessageType,
    UrgencyLevel,
    CommunicationResult
)
from .cache_manager import CRMCacheManager

logger = logging.getLogger(__name__)


class CommunicationRepository:
    """
    Repository for persisting CRM Communication Engine data.
    
    Handles database operations for:
    - Communication records (crm_communications table)
    - Communication status updates
    - Communication history queries
    - Communication analytics
    
    Implements retry logic with exponential backoff for transient database errors.
    """
    
    def __init__(
        self, 
        db_manager: Optional[DatabaseConnectionManager] = None,
        cache_manager: Optional[CRMCacheManager] = None
    ):
        """
        Initialize repository with database connection manager and cache.
        
        Args:
            db_manager: Optional database connection manager. If None, uses global instance.
            cache_manager: Optional cache manager for caching preferences and templates.
        """
        self.db_manager = db_manager
        self.cache_manager = cache_manager
        self.max_retries = 3
        self.base_retry_delay = 1.0
        self.max_retry_delay = 30.0
        
        logger.info("CommunicationRepository initialized with caching support")
    
    @contextmanager
    def _get_session(self):
        """Get database session with proper error handling"""
        if self.db_manager:
            with self.db_manager.get_sync_session() as session:
                yield session
        else:
            with get_sync_session() as session:
                yield session
    
    def _execute_with_retry(
        self,
        operation: callable,
        operation_name: str,
        **kwargs
    ) -> Any:
        """
        Execute database operation with retry logic and exponential backoff.
        
        Args:
            operation: Callable to execute
            operation_name: Name of operation for logging
            **kwargs: Arguments to pass to operation
            
        Returns:
            Result of operation
            
        Raises:
            Exception: If operation fails after all retries
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return operation(**kwargs)
            
            except (OperationalError, IntegrityError) as e:
                last_exception = e
                
                # Check if this is a transient error that can be retried
                is_transient = self._is_transient_error(e)
                
                if not is_transient or attempt == self.max_retries - 1:
                    logger.error(
                        f"{operation_name} failed after {attempt + 1} attempts: {e}"
                    )
                    raise
                
                # Calculate delay with exponential backoff
                delay = min(
                    self.base_retry_delay * (2 ** attempt),
                    self.max_retry_delay
                )
                
                logger.warning(
                    f"{operation_name} failed (attempt {attempt + 1}/{self.max_retries}), "
                    f"retrying in {delay:.2f}s: {e}"
                )
                
                time.sleep(delay)
            
            except Exception as e:
                logger.error(f"{operation_name} failed with non-retryable error: {e}")
                raise
        
        # Should not reach here, but just in case
        if last_exception:
            raise last_exception
    
    def _is_transient_error(self, error: Exception) -> bool:
        """
        Check if database error is transient and can be retried.
        
        Args:
            error: Exception to check
            
        Returns:
            True if error is transient, False otherwise
        """
        error_str = str(error).lower()
        
        transient_indicators = [
            'connection',
            'timeout',
            'deadlock',
            'lock',
            'temporary',
            'transient',
            'unavailable'
        ]
        
        return any(indicator in error_str for indicator in transient_indicators)
    
    def save_communication(
        self,
        plan_id: str,
        client_id: str,
        message_type: MessageType,
        channel: MessageChannel,
        urgency: UrgencyLevel,
        subject: Optional[str],
        body: str,
        template_name: Optional[str] = None,
        context_data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Persist a new communication record to the database.
        
        Args:
            plan_id: Event plan ID
            client_id: Client identifier
            message_type: Type of message being sent
            channel: Communication channel used
            urgency: Urgency level of the message
            subject: Message subject (for email)
            body: Message body content
            template_name: Optional template name used
            context_data: Optional context data used for rendering
            metadata: Optional additional metadata
            
        Returns:
            communication_id (UUID as string) of created record
            
        Raises:
            Exception: If save operation fails after retries
        """
        def _save_operation(
            plan_id: str,
            client_id: str,
            message_type: MessageType,
            channel: MessageChannel,
            urgency: UrgencyLevel,
            subject: Optional[str],
            body: str,
            template_name: Optional[str],
            context_data: Optional[Dict[str, Any]],
            metadata: Optional[Dict[str, Any]]
        ) -> str:
            with self._get_session() as session:
                query = text("""
                    INSERT INTO crm_communications 
                    (plan_id, client_id, message_type, channel, urgency, status,
                     subject, body, template_name, context_data, metadata, created_at, updated_at)
                    VALUES (:plan_id, :client_id, :message_type, :channel, :urgency, :status,
                            :subject, :body, :template_name, :context_data, :metadata, :created_at, :updated_at)
                    RETURNING communication_id
                """)
                
                result = session.execute(
                    query,
                    {
                        'plan_id': plan_id,
                        'client_id': client_id,
                        'message_type': message_type.value,
                        'channel': channel.value,
                        'urgency': urgency.value,
                        'status': CommunicationStatus.PENDING.value,
                        'subject': subject,
                        'body': body,
                        'template_name': template_name,
                        'context_data': json.dumps(context_data) if context_data else None,
                        'metadata': json.dumps(metadata) if metadata else None,
                        'created_at': datetime.utcnow(),
                        'updated_at': datetime.utcnow()
                    }
                )
                
                communication_id = str(result.scalar())
                session.commit()
                
                logger.info(
                    f"Saved communication {communication_id} for client {client_id} "
                    f"via {channel.value} with type {message_type.value}"
                )
                
                return communication_id
        
        return self._execute_with_retry(
            operation=_save_operation,
            operation_name="save_communication",
            plan_id=plan_id,
            client_id=client_id,
            message_type=message_type,
            channel=channel,
            urgency=urgency,
            subject=subject,
            body=body,
            template_name=template_name,
            context_data=context_data,
            metadata=metadata
        )

    def update_status(
        self,
        communication_id: str,
        status: CommunicationStatus,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update communication status and timestamps.
        
        Args:
            communication_id: UUID of communication to update
            status: New communication status
            error_message: Optional error message if status is FAILED
            metadata: Optional additional metadata to merge
            
        Returns:
            True if update successful, False otherwise
            
        Raises:
            Exception: If update operation fails after retries
        """
        def _update_operation(
            communication_id: str,
            status: CommunicationStatus,
            error_message: Optional[str],
            metadata: Optional[Dict[str, Any]]
        ) -> bool:
            with self._get_session() as session:
                # Build dynamic update query based on status
                timestamp_field = None
                if status == CommunicationStatus.SENT:
                    timestamp_field = 'sent_at'
                elif status == CommunicationStatus.DELIVERED:
                    timestamp_field = 'delivered_at'
                elif status == CommunicationStatus.OPENED:
                    timestamp_field = 'opened_at'
                elif status == CommunicationStatus.CLICKED:
                    timestamp_field = 'clicked_at'
                elif status == CommunicationStatus.FAILED:
                    timestamp_field = 'failed_at'
                
                # Base update query
                update_parts = [
                    "status = :status",
                    "updated_at = :updated_at"
                ]
                params = {
                    'communication_id': communication_id,
                    'status': status.value,
                    'updated_at': datetime.utcnow()
                }
                
                # Add timestamp update if applicable
                if timestamp_field:
                    update_parts.append(f"{timestamp_field} = :timestamp")
                    params['timestamp'] = datetime.utcnow()
                
                # Add error message if provided
                if error_message:
                    update_parts.append("error_message = :error_message")
                    params['error_message'] = error_message
                
                # Add metadata merge if provided
                if metadata:
                    update_parts.append("metadata = COALESCE(metadata, '{}'::jsonb) || :metadata::jsonb")
                    params['metadata'] = json.dumps(metadata)
                
                query = text(f"""
                    UPDATE crm_communications
                    SET {', '.join(update_parts)}
                    WHERE communication_id = :communication_id
                """)
                
                result = session.execute(query, params)
                session.commit()
                
                updated = result.rowcount > 0
                
                if updated:
                    logger.info(
                        f"Updated communication {communication_id} status to {status.value}"
                    )
                else:
                    logger.warning(f"No communication found with ID {communication_id}")
                
                return updated
        
        return self._execute_with_retry(
            operation=_update_operation,
            operation_name="update_status",
            communication_id=communication_id,
            status=status,
            error_message=error_message,
            metadata=metadata
        )
    
    def get_history(
        self,
        plan_id: Optional[str] = None,
        client_id: Optional[str] = None,
        channel: Optional[MessageChannel] = None,
        date_range: Optional[tuple[datetime, datetime]] = None,
        status: Optional[CommunicationStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Query communication history with filtering.
        
        Args:
            plan_id: Optional filter by plan ID
            client_id: Optional filter by client ID
            channel: Optional filter by communication channel
            date_range: Optional tuple of (start_date, end_date)
            status: Optional filter by communication status
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of communication records as dictionaries
            
        Raises:
            Exception: If query operation fails after retries
        """
        def _get_history_operation(
            plan_id: Optional[str],
            client_id: Optional[str],
            channel: Optional[MessageChannel],
            date_range: Optional[tuple[datetime, datetime]],
            status: Optional[CommunicationStatus],
            limit: int,
            offset: int
        ) -> List[Dict[str, Any]]:
            with self._get_session() as session:
                # Build dynamic WHERE clause
                where_clauses = []
                params = {'limit': limit, 'offset': offset}
                
                if plan_id:
                    where_clauses.append("plan_id = :plan_id")
                    params['plan_id'] = plan_id
                
                if client_id:
                    where_clauses.append("client_id = :client_id")
                    params['client_id'] = client_id
                
                if channel:
                    where_clauses.append("channel = :channel")
                    params['channel'] = channel.value
                
                if status:
                    where_clauses.append("status = :status")
                    params['status'] = status.value
                
                if date_range:
                    where_clauses.append("created_at BETWEEN :start_date AND :end_date")
                    params['start_date'] = date_range[0]
                    params['end_date'] = date_range[1]
                
                where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
                
                query = text(f"""
                    SELECT 
                        communication_id, plan_id, client_id, message_type, channel,
                        urgency, status, subject, body, template_name, context_data,
                        sent_at, delivered_at, opened_at, clicked_at, failed_at,
                        error_message, retry_count, metadata, created_at, updated_at
                    FROM crm_communications
                    WHERE {where_clause}
                    ORDER BY created_at DESC
                    LIMIT :limit OFFSET :offset
                """)
                
                result = session.execute(query, params).fetchall()
                
                communications = []
                for row in result:
                    communications.append({
                        'communication_id': str(row[0]),
                        'plan_id': str(row[1]) if row[1] else None,
                        'client_id': row[2],
                        'message_type': row[3],
                        'channel': row[4],
                        'urgency': row[5],
                        'status': row[6],
                        'subject': row[7],
                        'body': row[8],
                        'template_name': row[9],
                        'context_data': json.loads(row[10]) if row[10] else {},
                        'sent_at': row[11].isoformat() if row[11] else None,
                        'delivered_at': row[12].isoformat() if row[12] else None,
                        'opened_at': row[13].isoformat() if row[13] else None,
                        'clicked_at': row[14].isoformat() if row[14] else None,
                        'failed_at': row[15].isoformat() if row[15] else None,
                        'error_message': row[16],
                        'retry_count': row[17],
                        'metadata': json.loads(row[18]) if row[18] else {},
                        'created_at': row[19].isoformat() if row[19] else None,
                        'updated_at': row[20].isoformat() if row[20] else None
                    })
                
                logger.info(
                    f"Retrieved {len(communications)} communication records "
                    f"(limit={limit}, offset={offset})"
                )
                
                return communications
        
        return self._execute_with_retry(
            operation=_get_history_operation,
            operation_name="get_history",
            plan_id=plan_id,
            client_id=client_id,
            channel=channel,
            date_range=date_range,
            status=status,
            limit=limit,
            offset=offset
        )
    
    def get_analytics(
        self,
        plan_id: Optional[str] = None,
        client_id: Optional[str] = None,
        date_range: Optional[tuple[datetime, datetime]] = None
    ) -> Dict[str, Any]:
        """
        Query communication effectiveness metrics.
        
        Args:
            plan_id: Optional filter by plan ID
            client_id: Optional filter by client ID
            date_range: Optional tuple of (start_date, end_date)
            
        Returns:
            Dictionary containing analytics metrics:
            - total_sent: Total communications sent
            - delivery_rate: Percentage delivered
            - open_rate: Percentage opened (email only)
            - click_rate: Percentage clicked
            - failure_rate: Percentage failed
            - avg_delivery_time_seconds: Average time from sent to delivered
            - by_channel: Metrics broken down by channel
            - by_message_type: Metrics broken down by message type
            
        Raises:
            Exception: If query operation fails after retries
        """
        def _get_analytics_operation(
            plan_id: Optional[str],
            client_id: Optional[str],
            date_range: Optional[tuple[datetime, datetime]]
        ) -> Dict[str, Any]:
            with self._get_session() as session:
                # Build WHERE clause for filtering
                where_clauses = ["sent_at IS NOT NULL"]
                params = {}
                
                if plan_id:
                    where_clauses.append("plan_id = :plan_id")
                    params['plan_id'] = plan_id
                
                if client_id:
                    where_clauses.append("client_id = :client_id")
                    params['client_id'] = client_id
                
                if date_range:
                    where_clauses.append("sent_at BETWEEN :start_date AND :end_date")
                    params['start_date'] = date_range[0]
                    params['end_date'] = date_range[1]
                
                where_clause = " AND ".join(where_clauses)
                
                # Overall metrics query
                overall_query = text(f"""
                    SELECT
                        COUNT(*) as total_sent,
                        COUNT(CASE WHEN status IN ('delivered', 'opened', 'clicked') THEN 1 END) as delivered_count,
                        COUNT(CASE WHEN status IN ('opened', 'clicked') THEN 1 END) as opened_count,
                        COUNT(CASE WHEN status = 'clicked' THEN 1 END) as clicked_count,
                        COUNT(CASE WHEN status IN ('failed', 'bounced') THEN 1 END) as failed_count,
                        AVG(EXTRACT(EPOCH FROM (delivered_at - sent_at))) as avg_delivery_time_seconds
                    FROM crm_communications
                    WHERE {where_clause}
                """)
                
                overall_result = session.execute(overall_query, params).fetchone()
                
                total_sent = overall_result[0] or 0
                delivered_count = overall_result[1] or 0
                opened_count = overall_result[2] or 0
                clicked_count = overall_result[3] or 0
                failed_count = overall_result[4] or 0
                avg_delivery_time = overall_result[5] or 0
                
                # Calculate rates
                delivery_rate = (delivered_count / total_sent * 100) if total_sent > 0 else 0
                open_rate = (opened_count / delivered_count * 100) if delivered_count > 0 else 0
                click_rate = (clicked_count / opened_count * 100) if opened_count > 0 else 0
                failure_rate = (failed_count / total_sent * 100) if total_sent > 0 else 0
                
                # By channel metrics
                channel_query = text(f"""
                    SELECT
                        channel,
                        COUNT(*) as total,
                        COUNT(CASE WHEN status IN ('delivered', 'opened', 'clicked') THEN 1 END) as delivered,
                        COUNT(CASE WHEN status IN ('opened', 'clicked') THEN 1 END) as opened,
                        COUNT(CASE WHEN status = 'clicked' THEN 1 END) as clicked,
                        COUNT(CASE WHEN status IN ('failed', 'bounced') THEN 1 END) as failed
                    FROM crm_communications
                    WHERE {where_clause}
                    GROUP BY channel
                """)
                
                channel_results = session.execute(channel_query, params).fetchall()
                
                by_channel = {}
                for row in channel_results:
                    channel = row[0]
                    total = row[1] or 0
                    delivered = row[2] or 0
                    opened = row[3] or 0
                    clicked = row[4] or 0
                    failed = row[5] or 0
                    
                    by_channel[channel] = {
                        'total_sent': total,
                        'delivered_count': delivered,
                        'opened_count': opened,
                        'clicked_count': clicked,
                        'failed_count': failed,
                        'delivery_rate': (delivered / total * 100) if total > 0 else 0,
                        'open_rate': (opened / delivered * 100) if delivered > 0 else 0,
                        'click_rate': (clicked / opened * 100) if opened > 0 else 0,
                        'failure_rate': (failed / total * 100) if total > 0 else 0
                    }
                
                # By message type metrics
                type_query = text(f"""
                    SELECT
                        message_type,
                        COUNT(*) as total,
                        COUNT(CASE WHEN status IN ('delivered', 'opened', 'clicked') THEN 1 END) as delivered,
                        COUNT(CASE WHEN status IN ('opened', 'clicked') THEN 1 END) as opened,
                        COUNT(CASE WHEN status = 'clicked' THEN 1 END) as clicked
                    FROM crm_communications
                    WHERE {where_clause}
                    GROUP BY message_type
                """)
                
                type_results = session.execute(type_query, params).fetchall()
                
                by_message_type = {}
                for row in type_results:
                    msg_type = row[0]
                    total = row[1] or 0
                    delivered = row[2] or 0
                    opened = row[3] or 0
                    clicked = row[4] or 0
                    
                    by_message_type[msg_type] = {
                        'total_sent': total,
                        'delivered_count': delivered,
                        'opened_count': opened,
                        'clicked_count': clicked,
                        'delivery_rate': (delivered / total * 100) if total > 0 else 0,
                        'open_rate': (opened / delivered * 100) if delivered > 0 else 0,
                        'click_rate': (clicked / opened * 100) if opened > 0 else 0
                    }
                
                analytics = {
                    'total_sent': total_sent,
                    'delivered_count': delivered_count,
                    'opened_count': opened_count,
                    'clicked_count': clicked_count,
                    'failed_count': failed_count,
                    'delivery_rate': round(delivery_rate, 2),
                    'open_rate': round(open_rate, 2),
                    'click_rate': round(click_rate, 2),
                    'failure_rate': round(failure_rate, 2),
                    'avg_delivery_time_seconds': round(avg_delivery_time, 2),
                    'by_channel': by_channel,
                    'by_message_type': by_message_type
                }
                
                logger.info(
                    f"Retrieved analytics: {total_sent} total sent, "
                    f"{delivery_rate:.1f}% delivery rate, {open_rate:.1f}% open rate"
                )
                
                return analytics
        
        return self._execute_with_retry(
            operation=_get_analytics_operation,
            operation_name="get_analytics",
            plan_id=plan_id,
            client_id=client_id,
            date_range=date_range
        )
    
    def save_client_preferences(
        self,
        preferences: 'ClientPreferences'
    ) -> bool:
        """
        Save or update client communication preferences and invalidate cache.
        
        Args:
            preferences: ClientPreferences object to persist
            
        Returns:
            True if save successful, False otherwise
            
        Raises:
            Exception: If save operation fails after retries
        """
        from .models import ClientPreferences
        
        def _save_preferences_operation(preferences: ClientPreferences) -> bool:
            with self._get_session() as session:
                # Use UPSERT (INSERT ... ON CONFLICT UPDATE) for idempotency
                query = text("""
                    INSERT INTO crm_client_preferences 
                    (client_id, preferred_channels, timezone, quiet_hours_start, quiet_hours_end,
                     opt_out_email, opt_out_sms, opt_out_whatsapp, language_preference, 
                     created_at, updated_at)
                    VALUES (:client_id, :preferred_channels, :timezone, :quiet_hours_start, :quiet_hours_end,
                            :opt_out_email, :opt_out_sms, :opt_out_whatsapp, :language_preference,
                            :created_at, :updated_at)
                    ON CONFLICT (client_id) 
                    DO UPDATE SET
                        preferred_channels = EXCLUDED.preferred_channels,
                        timezone = EXCLUDED.timezone,
                        quiet_hours_start = EXCLUDED.quiet_hours_start,
                        quiet_hours_end = EXCLUDED.quiet_hours_end,
                        opt_out_email = EXCLUDED.opt_out_email,
                        opt_out_sms = EXCLUDED.opt_out_sms,
                        opt_out_whatsapp = EXCLUDED.opt_out_whatsapp,
                        language_preference = EXCLUDED.language_preference,
                        updated_at = EXCLUDED.updated_at
                """)
                
                # Convert preferred channels to JSON array
                preferred_channels_json = json.dumps([ch.value for ch in preferences.preferred_channels])
                
                session.execute(
                    query,
                    {
                        'client_id': preferences.client_id,
                        'preferred_channels': preferred_channels_json,
                        'timezone': preferences.timezone,
                        'quiet_hours_start': preferences.quiet_hours_start,
                        'quiet_hours_end': preferences.quiet_hours_end,
                        'opt_out_email': preferences.opt_out_email,
                        'opt_out_sms': preferences.opt_out_sms,
                        'opt_out_whatsapp': preferences.opt_out_whatsapp,
                        'language_preference': preferences.language_preference,
                        'created_at': datetime.utcnow(),
                        'updated_at': datetime.utcnow()
                    }
                )
                
                session.commit()
                
                logger.info(
                    f"Saved preferences for client {preferences.client_id} "
                    f"with channels {[ch.value for ch in preferences.preferred_channels]}"
                )
                
                # Invalidate cache after successful save
                if self.cache_manager:
                    self.cache_manager.invalidate_client_preferences(preferences.client_id)
                
                return True
        
        return self._execute_with_retry(
            operation=_save_preferences_operation,
            operation_name="save_client_preferences",
            preferences=preferences
        )
    
    def get_client_preferences(
        self,
        client_id: str
    ) -> Optional['ClientPreferences']:
        """
        Retrieve client communication preferences with caching.
        
        First checks cache, then falls back to database if not found.
        Caches result for 1 hour.
        
        Args:
            client_id: Client identifier
            
        Returns:
            ClientPreferences object if found, None otherwise
            
        Raises:
            Exception: If query operation fails after retries
        """
        from .models import ClientPreferences, MessageChannel
        
        # Try cache first
        if self.cache_manager:
            cached_prefs = self.cache_manager.get_client_preferences(client_id)
            if cached_prefs:
                return cached_prefs
        
        def _get_preferences_operation(client_id: str) -> Optional[ClientPreferences]:
            with self._get_session() as session:
                query = text("""
                    SELECT 
                        client_id, preferred_channels, timezone, quiet_hours_start, quiet_hours_end,
                        opt_out_email, opt_out_sms, opt_out_whatsapp, language_preference
                    FROM crm_client_preferences
                    WHERE client_id = :client_id
                """)
                
                result = session.execute(query, {'client_id': client_id}).fetchone()
                
                if not result:
                    logger.info(f"No preferences found for client {client_id}, returning defaults")
                    return None
                
                # Parse preferred channels from JSON
                preferred_channels_json = result[1]
                if isinstance(preferred_channels_json, str):
                    preferred_channels_list = json.loads(preferred_channels_json)
                else:
                    preferred_channels_list = preferred_channels_json
                
                preferred_channels = [MessageChannel(ch) for ch in preferred_channels_list]
                
                preferences = ClientPreferences(
                    client_id=result[0],
                    preferred_channels=preferred_channels,
                    timezone=result[2],
                    quiet_hours_start=result[3],
                    quiet_hours_end=result[4],
                    opt_out_email=result[5],
                    opt_out_sms=result[6],
                    opt_out_whatsapp=result[7],
                    language_preference=result[8] if len(result) > 8 else "en"
                )
                
                logger.info(f"Retrieved preferences for client {client_id} from database")
                
                # Cache the result
                if self.cache_manager and preferences:
                    self.cache_manager.set_client_preferences(preferences)
                
                return preferences
        
        return self._execute_with_retry(
            operation=_get_preferences_operation,
            operation_name="get_client_preferences",
            client_id=client_id
        )
    
    def delete_client_preferences(
        self,
        client_id: str
    ) -> bool:
        """
        Delete client communication preferences (for GDPR compliance).
        
        Args:
            client_id: Client identifier
            
        Returns:
            True if deletion successful, False if not found
            
        Raises:
            Exception: If delete operation fails after retries
        """
        def _delete_preferences_operation(client_id: str) -> bool:
            with self._get_session() as session:
                query = text("""
                    DELETE FROM crm_client_preferences
                    WHERE client_id = :client_id
                """)
                
                result = session.execute(query, {'client_id': client_id})
                session.commit()
                
                deleted = result.rowcount > 0
                
                if deleted:
                    logger.info(f"Deleted preferences for client {client_id}")
                else:
                    logger.warning(f"No preferences found to delete for client {client_id}")
                
                return deleted
        
        return self._execute_with_retry(
            operation=_delete_preferences_operation,
            operation_name="delete_client_preferences",
            client_id=client_id
        )
