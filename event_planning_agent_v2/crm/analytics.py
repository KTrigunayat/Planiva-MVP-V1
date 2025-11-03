"""
CRM Analytics Module

Provides comprehensive analytics and reporting for CRM Communication Engine.
Includes delivery rates, engagement metrics, channel performance, and message type analysis.
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from contextlib import contextmanager
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database.connection import get_sync_session, DatabaseConnectionManager
from .models import MessageChannel, MessageType, CommunicationStatus

logger = logging.getLogger(__name__)


class CRMAnalytics:
    """
    Analytics engine for CRM Communication Engine.
    
    Provides methods for querying communication effectiveness metrics,
    channel performance, message type analysis, and trend data.
    """
    
    def __init__(self, db_manager: Optional[DatabaseConnectionManager] = None):
        """
        Initialize analytics engine.
        
        Args:
            db_manager: Optional database connection manager
        """
        self.db_manager = db_manager
        logger.info("CRMAnalytics initialized")
    
    @contextmanager
    def _get_session(self):
        """Get database session with proper error handling"""
        if self.db_manager:
            with self.db_manager.get_sync_session() as session:
                yield session
        else:
            with get_sync_session() as session:
                yield session
    
    def get_delivery_rate(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        channel: Optional[MessageChannel] = None,
        message_type: Optional[MessageType] = None
    ) -> Dict[str, Any]:
        """
        Calculate delivery rate metrics.
        
        Args:
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering
            channel: Optional channel filter
            message_type: Optional message type filter
            
        Returns:
            Dictionary with delivery rate metrics
        """
        with self._get_session() as session:
            where_clauses = ["sent_at IS NOT NULL"]
            params = {}
            
            if start_date:
                where_clauses.append("sent_at >= :start_date")
                params['start_date'] = start_date
            
            if end_date:
                where_clauses.append("sent_at <= :end_date")
                params['end_date'] = end_date
            
            if channel:
                where_clauses.append("channel = :channel")
                params['channel'] = channel.value
            
            if message_type:
                where_clauses.append("message_type = :message_type")
                params['message_type'] = message_type.value
            
            where_clause = " AND ".join(where_clauses)
            
            query = text(f"""
                SELECT
                    COUNT(*) as total_sent,
                    COUNT(CASE WHEN status IN ('delivered', 'opened', 'clicked') THEN 1 END) as delivered_count,
                    COUNT(CASE WHEN status IN ('failed', 'bounced') THEN 1 END) as failed_count,
                    AVG(EXTRACT(EPOCH FROM (delivered_at - sent_at))) as avg_delivery_time_seconds
                FROM crm_communications
                WHERE {where_clause}
            """)
            
            result = session.execute(query, params).fetchone()
            
            total_sent = result[0] or 0
            delivered_count = result[1] or 0
            failed_count = result[2] or 0
            avg_delivery_time = result[3] or 0
            
            delivery_rate = (delivered_count / total_sent * 100) if total_sent > 0 else 0
            failure_rate = (failed_count / total_sent * 100) if total_sent > 0 else 0
            
            return {
                'total_sent': total_sent,
                'delivered_count': delivered_count,
                'failed_count': failed_count,
                'delivery_rate': round(delivery_rate, 2),
                'failure_rate': round(failure_rate, 2),
                'avg_delivery_time_seconds': round(avg_delivery_time, 2)
            }
    
    def get_open_rate(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        message_type: Optional[MessageType] = None
    ) -> Dict[str, Any]:
        """
        Calculate email open rate metrics.
        
        Args:
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering
            message_type: Optional message type filter
            
        Returns:
            Dictionary with open rate metrics
        """
        with self._get_session() as session:
            where_clauses = [
                "channel = 'email'",
                "status IN ('delivered', 'opened', 'clicked')"
            ]
            params = {}
            
            if start_date:
                where_clauses.append("delivered_at >= :start_date")
                params['start_date'] = start_date
            
            if end_date:
                where_clauses.append("delivered_at <= :end_date")
                params['end_date'] = end_date
            
            if message_type:
                where_clauses.append("message_type = :message_type")
                params['message_type'] = message_type.value
            
            where_clause = " AND ".join(where_clauses)
            
            query = text(f"""
                SELECT
                    COUNT(*) as delivered_count,
                    COUNT(CASE WHEN status IN ('opened', 'clicked') THEN 1 END) as opened_count,
                    AVG(EXTRACT(EPOCH FROM (opened_at - delivered_at))) as avg_time_to_open_seconds
                FROM crm_communications
                WHERE {where_clause}
            """)
            
            result = session.execute(query, params).fetchone()
            
            delivered_count = result[0] or 0
            opened_count = result[1] or 0
            avg_time_to_open = result[2] or 0
            
            open_rate = (opened_count / delivered_count * 100) if delivered_count > 0 else 0
            
            return {
                'delivered_count': delivered_count,
                'opened_count': opened_count,
                'open_rate': round(open_rate, 2),
                'avg_time_to_open_seconds': round(avg_time_to_open, 2)
            }
    
    def get_click_through_rate(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        message_type: Optional[MessageType] = None
    ) -> Dict[str, Any]:
        """
        Calculate click-through rate metrics.
        
        Args:
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering
            message_type: Optional message type filter
            
        Returns:
            Dictionary with click-through rate metrics
        """
        with self._get_session() as session:
            where_clauses = [
                "channel = 'email'",
                "status IN ('opened', 'clicked')"
            ]
            params = {}
            
            if start_date:
                where_clauses.append("opened_at >= :start_date")
                params['start_date'] = start_date
            
            if end_date:
                where_clauses.append("opened_at <= :end_date")
                params['end_date'] = end_date
            
            if message_type:
                where_clauses.append("message_type = :message_type")
                params['message_type'] = message_type.value
            
            where_clause = " AND ".join(where_clauses)
            
            query = text(f"""
                SELECT
                    COUNT(*) as opened_count,
                    COUNT(CASE WHEN status = 'clicked' THEN 1 END) as clicked_count,
                    AVG(EXTRACT(EPOCH FROM (clicked_at - opened_at))) as avg_time_to_click_seconds
                FROM crm_communications
                WHERE {where_clause}
            """)
            
            result = session.execute(query, params).fetchone()
            
            opened_count = result[0] or 0
            clicked_count = result[1] or 0
            avg_time_to_click = result[2] or 0
            
            click_rate = (clicked_count / opened_count * 100) if opened_count > 0 else 0
            
            return {
                'opened_count': opened_count,
                'clicked_count': clicked_count,
                'click_through_rate': round(click_rate, 2),
                'avg_time_to_click_seconds': round(avg_time_to_click, 2)
            }
    
    def get_response_rate(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        channel: Optional[MessageChannel] = None
    ) -> Dict[str, Any]:
        """
        Calculate response rate based on client actions.
        
        Args:
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering
            channel: Optional channel filter
            
        Returns:
            Dictionary with response rate metrics
        """
        with self._get_session() as session:
            where_clauses = ["sent_at IS NOT NULL"]
            params = {}
            
            if start_date:
                where_clauses.append("sent_at >= :start_date")
                params['start_date'] = start_date
            
            if end_date:
                where_clauses.append("sent_at <= :end_date")
                params['end_date'] = end_date
            
            if channel:
                where_clauses.append("channel = :channel")
                params['channel'] = channel.value
            
            where_clause = " AND ".join(where_clauses)
            
            # Count communications with client responses (clicked or metadata indicating response)
            query = text(f"""
                SELECT
                    COUNT(*) as total_sent,
                    COUNT(CASE WHEN status = 'clicked' OR 
                          (metadata->>'client_responded')::boolean = true THEN 1 END) as response_count,
                    AVG(CASE WHEN status = 'clicked' THEN 
                        EXTRACT(EPOCH FROM (clicked_at - sent_at)) END) as avg_response_time_seconds
                FROM crm_communications
                WHERE {where_clause}
            """)
            
            result = session.execute(query, params).fetchone()
            
            total_sent = result[0] or 0
            response_count = result[1] or 0
            avg_response_time = result[2] or 0
            
            response_rate = (response_count / total_sent * 100) if total_sent > 0 else 0
            
            return {
                'total_sent': total_sent,
                'response_count': response_count,
                'response_rate': round(response_rate, 2),
                'avg_response_time_seconds': round(avg_response_time, 2)
            }
    
    def get_channel_performance(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Compare performance across all channels.
        
        Args:
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering
            
        Returns:
            Dictionary with performance metrics by channel
        """
        with self._get_session() as session:
            where_clauses = ["sent_at IS NOT NULL"]
            params = {}
            
            if start_date:
                where_clauses.append("sent_at >= :start_date")
                params['start_date'] = start_date
            
            if end_date:
                where_clauses.append("sent_at <= :end_date")
                params['end_date'] = end_date
            
            where_clause = " AND ".join(where_clauses)
            
            query = text(f"""
                SELECT
                    channel,
                    COUNT(*) as total_sent,
                    COUNT(CASE WHEN status IN ('delivered', 'opened', 'clicked') THEN 1 END) as delivered_count,
                    COUNT(CASE WHEN status IN ('opened', 'clicked') THEN 1 END) as opened_count,
                    COUNT(CASE WHEN status = 'clicked' THEN 1 END) as clicked_count,
                    COUNT(CASE WHEN status IN ('failed', 'bounced') THEN 1 END) as failed_count,
                    AVG(EXTRACT(EPOCH FROM (delivered_at - sent_at))) as avg_delivery_time_seconds,
                    AVG(CASE WHEN opened_at IS NOT NULL THEN 
                        EXTRACT(EPOCH FROM (opened_at - delivered_at)) END) as avg_time_to_open_seconds
                FROM crm_communications
                WHERE {where_clause}
                GROUP BY channel
                ORDER BY total_sent DESC
            """)
            
            results = session.execute(query, params).fetchall()
            
            channel_performance = {}
            for row in results:
                channel = row[0]
                total_sent = row[1] or 0
                delivered_count = row[2] or 0
                opened_count = row[3] or 0
                clicked_count = row[4] or 0
                failed_count = row[5] or 0
                avg_delivery_time = row[6] or 0
                avg_time_to_open = row[7] or 0
                
                delivery_rate = (delivered_count / total_sent * 100) if total_sent > 0 else 0
                open_rate = (opened_count / delivered_count * 100) if delivered_count > 0 else 0
                click_rate = (clicked_count / opened_count * 100) if opened_count > 0 else 0
                failure_rate = (failed_count / total_sent * 100) if total_sent > 0 else 0
                
                channel_performance[channel] = {
                    'total_sent': total_sent,
                    'delivered_count': delivered_count,
                    'opened_count': opened_count,
                    'clicked_count': clicked_count,
                    'failed_count': failed_count,
                    'delivery_rate': round(delivery_rate, 2),
                    'open_rate': round(open_rate, 2),
                    'click_through_rate': round(click_rate, 2),
                    'failure_rate': round(failure_rate, 2),
                    'avg_delivery_time_seconds': round(avg_delivery_time, 2),
                    'avg_time_to_open_seconds': round(avg_time_to_open, 2)
                }
            
            return channel_performance
    
    def get_message_type_performance(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Analyze performance by message type.
        
        Args:
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering
            
        Returns:
            Dictionary with performance metrics by message type
        """
        with self._get_session() as session:
            where_clauses = ["sent_at IS NOT NULL"]
            params = {}
            
            if start_date:
                where_clauses.append("sent_at >= :start_date")
                params['start_date'] = start_date
            
            if end_date:
                where_clauses.append("sent_at <= :end_date")
                params['end_date'] = end_date
            
            where_clause = " AND ".join(where_clauses)
            
            query = text(f"""
                SELECT
                    message_type,
                    COUNT(*) as total_sent,
                    COUNT(CASE WHEN status IN ('delivered', 'opened', 'clicked') THEN 1 END) as delivered_count,
                    COUNT(CASE WHEN status IN ('opened', 'clicked') THEN 1 END) as opened_count,
                    COUNT(CASE WHEN status = 'clicked' THEN 1 END) as clicked_count,
                    AVG(EXTRACT(EPOCH FROM (delivered_at - sent_at))) as avg_delivery_time_seconds,
                    AVG(CASE WHEN opened_at IS NOT NULL THEN 
                        EXTRACT(EPOCH FROM (opened_at - delivered_at)) END) as avg_time_to_open_seconds,
                    AVG(CASE WHEN clicked_at IS NOT NULL THEN 
                        EXTRACT(EPOCH FROM (clicked_at - opened_at)) END) as avg_time_to_click_seconds
                FROM crm_communications
                WHERE {where_clause}
                GROUP BY message_type
                ORDER BY total_sent DESC
            """)
            
            results = session.execute(query, params).fetchall()
            
            message_type_performance = {}
            for row in results:
                msg_type = row[0]
                total_sent = row[1] or 0
                delivered_count = row[2] or 0
                opened_count = row[3] or 0
                clicked_count = row[4] or 0
                avg_delivery_time = row[5] or 0
                avg_time_to_open = row[6] or 0
                avg_time_to_click = row[7] or 0
                
                delivery_rate = (delivered_count / total_sent * 100) if total_sent > 0 else 0
                open_rate = (opened_count / delivered_count * 100) if delivered_count > 0 else 0
                click_rate = (clicked_count / opened_count * 100) if opened_count > 0 else 0
                
                message_type_performance[msg_type] = {
                    'total_sent': total_sent,
                    'delivered_count': delivered_count,
                    'opened_count': opened_count,
                    'clicked_count': clicked_count,
                    'delivery_rate': round(delivery_rate, 2),
                    'open_rate': round(open_rate, 2),
                    'click_through_rate': round(click_rate, 2),
                    'avg_delivery_time_seconds': round(avg_delivery_time, 2),
                    'avg_time_to_open_seconds': round(avg_time_to_open, 2),
                    'avg_time_to_click_seconds': round(avg_time_to_click, 2)
                }
            
            return message_type_performance
    
    def get_timeline_data(
        self,
        start_date: datetime,
        end_date: datetime,
        granularity: str = 'day'
    ) -> List[Dict[str, Any]]:
        """
        Get communication volume over time.
        
        Args:
            start_date: Start date for timeline
            end_date: End date for timeline
            granularity: Time granularity ('hour', 'day', 'week', 'month')
            
        Returns:
            List of data points with timestamp and metrics
        """
        with self._get_session() as session:
            # Determine date truncation based on granularity
            if granularity == 'hour':
                date_trunc = "date_trunc('hour', sent_at)"
            elif granularity == 'week':
                date_trunc = "date_trunc('week', sent_at)"
            elif granularity == 'month':
                date_trunc = "date_trunc('month', sent_at)"
            else:  # default to day
                date_trunc = "date_trunc('day', sent_at)"
            
            query = text(f"""
                SELECT
                    {date_trunc} as time_bucket,
                    COUNT(*) as total_sent,
                    COUNT(CASE WHEN status IN ('delivered', 'opened', 'clicked') THEN 1 END) as delivered_count,
                    COUNT(CASE WHEN status IN ('opened', 'clicked') THEN 1 END) as opened_count,
                    COUNT(CASE WHEN status = 'clicked' THEN 1 END) as clicked_count,
                    COUNT(CASE WHEN status IN ('failed', 'bounced') THEN 1 END) as failed_count
                FROM crm_communications
                WHERE sent_at BETWEEN :start_date AND :end_date
                GROUP BY time_bucket
                ORDER BY time_bucket
            """)
            
            results = session.execute(query, {
                'start_date': start_date,
                'end_date': end_date
            }).fetchall()
            
            timeline_data = []
            for row in results:
                time_bucket = row[0]
                total_sent = row[1] or 0
                delivered_count = row[2] or 0
                opened_count = row[3] or 0
                clicked_count = row[4] or 0
                failed_count = row[5] or 0
                
                delivery_rate = (delivered_count / total_sent * 100) if total_sent > 0 else 0
                
                timeline_data.append({
                    'timestamp': time_bucket.isoformat() if time_bucket else None,
                    'total_sent': total_sent,
                    'delivered_count': delivered_count,
                    'opened_count': opened_count,
                    'clicked_count': clicked_count,
                    'failed_count': failed_count,
                    'delivery_rate': round(delivery_rate, 2)
                })
            
            return timeline_data
    
    def get_engagement_funnel(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get engagement funnel metrics (sent -> delivered -> opened -> clicked).
        
        Args:
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering
            
        Returns:
            Dictionary with funnel stage counts and conversion rates
        """
        with self._get_session() as session:
            where_clauses = ["sent_at IS NOT NULL"]
            params = {}
            
            if start_date:
                where_clauses.append("sent_at >= :start_date")
                params['start_date'] = start_date
            
            if end_date:
                where_clauses.append("sent_at <= :end_date")
                params['end_date'] = end_date
            
            where_clause = " AND ".join(where_clauses)
            
            query = text(f"""
                SELECT
                    COUNT(*) as sent_count,
                    COUNT(CASE WHEN status IN ('delivered', 'opened', 'clicked') THEN 1 END) as delivered_count,
                    COUNT(CASE WHEN status IN ('opened', 'clicked') THEN 1 END) as opened_count,
                    COUNT(CASE WHEN status = 'clicked' THEN 1 END) as clicked_count
                FROM crm_communications
                WHERE {where_clause}
            """)
            
            result = session.execute(query, params).fetchone()
            
            sent_count = result[0] or 0
            delivered_count = result[1] or 0
            opened_count = result[2] or 0
            clicked_count = result[3] or 0
            
            # Calculate conversion rates
            delivery_conversion = (delivered_count / sent_count * 100) if sent_count > 0 else 0
            open_conversion = (opened_count / delivered_count * 100) if delivered_count > 0 else 0
            click_conversion = (clicked_count / opened_count * 100) if opened_count > 0 else 0
            overall_conversion = (clicked_count / sent_count * 100) if sent_count > 0 else 0
            
            return {
                'funnel_stages': {
                    'sent': sent_count,
                    'delivered': delivered_count,
                    'opened': opened_count,
                    'clicked': clicked_count
                },
                'conversion_rates': {
                    'sent_to_delivered': round(delivery_conversion, 2),
                    'delivered_to_opened': round(open_conversion, 2),
                    'opened_to_clicked': round(click_conversion, 2),
                    'sent_to_clicked': round(overall_conversion, 2)
                },
                'drop_off': {
                    'delivery_drop_off': sent_count - delivered_count,
                    'open_drop_off': delivered_count - opened_count,
                    'click_drop_off': opened_count - clicked_count
                }
            }
    
    def get_preference_distribution(self) -> Dict[str, Any]:
        """
        Get distribution of client preferences.
        
        Returns:
            Dictionary with preference distribution metrics
        """
        with self._get_session() as session:
            # Channel preference distribution
            channel_query = text("""
                SELECT 
                    jsonb_array_elements_text(preferred_channels) as channel,
                    COUNT(*) as client_count
                FROM crm_client_preferences
                GROUP BY channel
                ORDER BY client_count DESC
            """)
            
            channel_results = session.execute(channel_query).fetchall()
            
            channel_distribution = {}
            total_preferences = sum(row[1] for row in channel_results)
            
            for row in channel_results:
                channel = row[0]
                count = row[1]
                percentage = (count / total_preferences * 100) if total_preferences > 0 else 0
                channel_distribution[channel] = {
                    'count': count,
                    'percentage': round(percentage, 2)
                }
            
            # Opt-out statistics
            optout_query = text("""
                SELECT
                    COUNT(*) as total_clients,
                    COUNT(CASE WHEN opt_out_email = true THEN 1 END) as email_optouts,
                    COUNT(CASE WHEN opt_out_sms = true THEN 1 END) as sms_optouts,
                    COUNT(CASE WHEN opt_out_whatsapp = true THEN 1 END) as whatsapp_optouts
                FROM crm_client_preferences
            """)
            
            optout_result = session.execute(optout_query).fetchone()
            
            total_clients = optout_result[0] or 0
            email_optouts = optout_result[1] or 0
            sms_optouts = optout_result[2] or 0
            whatsapp_optouts = optout_result[3] or 0
            
            # Timezone distribution
            timezone_query = text("""
                SELECT 
                    timezone,
                    COUNT(*) as client_count
                FROM crm_client_preferences
                GROUP BY timezone
                ORDER BY client_count DESC
                LIMIT 10
            """)
            
            timezone_results = session.execute(timezone_query).fetchall()
            
            timezone_distribution = {}
            for row in timezone_results:
                timezone = row[0]
                count = row[1]
                percentage = (count / total_clients * 100) if total_clients > 0 else 0
                timezone_distribution[timezone] = {
                    'count': count,
                    'percentage': round(percentage, 2)
                }
            
            return {
                'channel_preferences': channel_distribution,
                'opt_out_statistics': {
                    'total_clients': total_clients,
                    'email_optouts': email_optouts,
                    'sms_optouts': sms_optouts,
                    'whatsapp_optouts': whatsapp_optouts,
                    'email_optout_rate': round((email_optouts / total_clients * 100) if total_clients > 0 else 0, 2),
                    'sms_optout_rate': round((sms_optouts / total_clients * 100) if total_clients > 0 else 0, 2),
                    'whatsapp_optout_rate': round((whatsapp_optouts / total_clients * 100) if total_clients > 0 else 0, 2)
                },
                'timezone_distribution': timezone_distribution
            }
    
    def get_comprehensive_analytics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive analytics report combining all metrics.
        
        Args:
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering
            
        Returns:
            Dictionary with all analytics metrics
        """
        logger.info(f"Generating comprehensive analytics report from {start_date} to {end_date}")
        
        return {
            'period': {
                'start_date': start_date.isoformat() if start_date else None,
                'end_date': end_date.isoformat() if end_date else None
            },
            'delivery_metrics': self.get_delivery_rate(start_date, end_date),
            'engagement_metrics': {
                'open_rate': self.get_open_rate(start_date, end_date),
                'click_through_rate': self.get_click_through_rate(start_date, end_date),
                'response_rate': self.get_response_rate(start_date, end_date)
            },
            'channel_performance': self.get_channel_performance(start_date, end_date),
            'message_type_performance': self.get_message_type_performance(start_date, end_date),
            'engagement_funnel': self.get_engagement_funnel(start_date, end_date),
            'preference_distribution': self.get_preference_distribution()
        }


# Singleton instance
_analytics_instance = None


def get_analytics() -> CRMAnalytics:
    """Get singleton analytics instance"""
    global _analytics_instance
    if _analytics_instance is None:
        _analytics_instance = CRMAnalytics()
    return _analytics_instance
