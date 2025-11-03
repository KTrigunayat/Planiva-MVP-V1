"""
GDPR Compliance Module

Implements GDPR (General Data Protection Regulation) compliance features:
- Right to be forgotten (data deletion)
- Right to data portability (data export)
- Data access logging
- Consent management
"""

import logging
import json
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import text
from sqlalchemy.orm import Session

from .models import ClientPreferences


logger = logging.getLogger(__name__)


class GDPRComplianceManager:
    """
    Manages GDPR compliance operations for client data.
    
    Implements:
    - Right to erasure (right to be forgotten)
    - Right to data portability
    - Data access audit logging
    - Consent tracking
    """
    
    def __init__(self, session: Session):
        """
        Initialize GDPR compliance manager.
        
        Args:
            session: SQLAlchemy database session
        """
        self.session = session
    
    def request_data_deletion(
        self,
        client_id: str,
        deletion_reason: str = "Client request - Right to be forgotten",
        requester_info: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Request deletion of client data (GDPR Right to be Forgotten).
        
        This marks the data for deletion and anonymizes communications.
        Actual deletion happens after a grace period.
        
        Args:
            client_id: Client identifier
            deletion_reason: Reason for deletion request
            requester_info: Optional dict with ip_address, user_agent
            
        Returns:
            True if deletion request successful, False otherwise
        """
        try:
            # Call database function for GDPR-compliant deletion
            query = text("""
                SELECT gdpr_delete_client_data(:client_id, :deletion_reason)
            """)
            
            result = self.session.execute(
                query,
                {
                    'client_id': client_id,
                    'deletion_reason': deletion_reason
                }
            ).scalar()
            
            self.session.commit()
            
            # Log the deletion request
            self._log_data_access(
                client_id=client_id,
                access_type='delete',
                accessed_by='system',
                purpose=deletion_reason,
                ip_address=requester_info.get('ip_address') if requester_info else None,
                user_agent=requester_info.get('user_agent') if requester_info else None
            )
            
            if result:
                logger.info(
                    f"GDPR deletion request processed for client {client_id}: {deletion_reason}"
                )
            else:
                logger.error(f"GDPR deletion request failed for client {client_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to process GDPR deletion request: {e}")
            self.session.rollback()
            return False
    
    def export_client_data(
        self,
        client_id: str,
        requester_info: Optional[Dict[str, str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Export all client data (GDPR Right to Data Portability).
        
        Args:
            client_id: Client identifier
            requester_info: Optional dict with ip_address, user_agent
            
        Returns:
            Dictionary with all client data or None if export fails
        """
        try:
            # Call database function for GDPR-compliant export
            query = text("""
                SELECT gdpr_export_client_data(:client_id)
            """)
            
            result = self.session.execute(
                query,
                {'client_id': client_id}
            ).scalar()
            
            if result:
                # Parse JSON result
                export_data = json.loads(result) if isinstance(result, str) else result
                
                # Log the export
                self._log_data_access(
                    client_id=client_id,
                    access_type='export',
                    accessed_by='system',
                    purpose='GDPR data portability request',
                    ip_address=requester_info.get('ip_address') if requester_info else None,
                    user_agent=requester_info.get('user_agent') if requester_info else None
                )
                
                logger.info(f"GDPR data export completed for client {client_id}")
                return export_data
            else:
                logger.warning(f"No data found to export for client {client_id}")
                return None
            
        except Exception as e:
            logger.error(f"Failed to export client data: {e}")
            return None
    
    def log_data_access(
        self,
        client_id: str,
        access_type: str,
        accessed_by: str,
        purpose: str,
        data_fields: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> bool:
        """
        Log access to client data for GDPR audit trail.
        
        Args:
            client_id: Client identifier
            access_type: Type of access ('read', 'write', 'delete', 'export')
            accessed_by: User or system identifier
            purpose: Purpose of data access
            data_fields: Optional dict of fields accessed
            ip_address: Optional IP address of requester
            user_agent: Optional user agent string
            
        Returns:
            True if logging successful, False otherwise
        """
        return self._log_data_access(
            client_id=client_id,
            access_type=access_type,
            accessed_by=accessed_by,
            purpose=purpose,
            data_fields=data_fields,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    def _log_data_access(
        self,
        client_id: str,
        access_type: str,
        accessed_by: str,
        purpose: str,
        data_fields: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> bool:
        """Internal method to log data access"""
        try:
            query = text("""
                INSERT INTO crm_data_access_log (
                    client_id,
                    access_type,
                    accessed_by,
                    purpose,
                    data_fields,
                    ip_address,
                    user_agent,
                    access_timestamp
                ) VALUES (
                    :client_id,
                    :access_type,
                    :accessed_by,
                    :purpose,
                    :data_fields,
                    :ip_address,
                    :user_agent,
                    :access_timestamp
                )
            """)
            
            self.session.execute(
                query,
                {
                    'client_id': client_id,
                    'access_type': access_type,
                    'accessed_by': accessed_by,
                    'purpose': purpose,
                    'data_fields': json.dumps(data_fields) if data_fields else None,
                    'ip_address': ip_address,
                    'user_agent': user_agent,
                    'access_timestamp': datetime.utcnow()
                }
            )
            
            self.session.commit()
            
            logger.debug(
                f"Logged {access_type} access to client {client_id} data by {accessed_by}"
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to log data access: {e}")
            self.session.rollback()
            return False
    
    def get_data_access_log(
        self,
        client_id: str,
        limit: int = 100
    ) -> list:
        """
        Retrieve data access log for a client.
        
        Args:
            client_id: Client identifier
            limit: Maximum number of log entries to return
            
        Returns:
            List of access log entries
        """
        try:
            query = text("""
                SELECT 
                    log_id,
                    access_type,
                    accessed_by,
                    access_timestamp,
                    purpose,
                    data_fields,
                    ip_address,
                    user_agent
                FROM crm_data_access_log
                WHERE client_id = :client_id
                ORDER BY access_timestamp DESC
                LIMIT :limit
            """)
            
            result = self.session.execute(
                query,
                {'client_id': client_id, 'limit': limit}
            ).fetchall()
            
            access_log = []
            for row in result:
                access_log.append({
                    'log_id': str(row[0]),
                    'access_type': row[1],
                    'accessed_by': row[2],
                    'access_timestamp': row[3].isoformat() if row[3] else None,
                    'purpose': row[4],
                    'data_fields': json.loads(row[5]) if row[5] else {},
                    'ip_address': str(row[6]) if row[6] else None,
                    'user_agent': row[7]
                })
            
            logger.info(f"Retrieved {len(access_log)} access log entries for client {client_id}")
            return access_log
            
        except Exception as e:
            logger.error(f"Failed to retrieve data access log: {e}")
            return []
    
    def check_deletion_status(self, client_id: str) -> Optional[Dict[str, Any]]:
        """
        Check if client has requested data deletion.
        
        Args:
            client_id: Client identifier
            
        Returns:
            Dictionary with deletion status or None if no deletion requested
        """
        try:
            query = text("""
                SELECT 
                    deletion_requested_at,
                    deleted_at,
                    deletion_reason,
                    data_retention_until
                FROM crm_client_preferences
                WHERE client_id = :client_id
            """)
            
            result = self.session.execute(query, {'client_id': client_id}).fetchone()
            
            if not result:
                return None
            
            deletion_requested_at = result[0]
            deleted_at = result[1]
            deletion_reason = result[2]
            data_retention_until = result[3]
            
            if not deletion_requested_at and not deleted_at:
                return None
            
            status = {
                'deletion_requested': deletion_requested_at is not None,
                'deletion_requested_at': deletion_requested_at.isoformat() if deletion_requested_at else None,
                'deleted': deleted_at is not None,
                'deleted_at': deleted_at.isoformat() if deleted_at else None,
                'deletion_reason': deletion_reason,
                'data_retention_until': data_retention_until.isoformat() if data_retention_until else None
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to check deletion status: {e}")
            return None
    
    def set_data_retention_period(
        self,
        client_id: str,
        retention_days: int = 730  # 2 years default
    ) -> bool:
        """
        Set data retention period for client data.
        
        Args:
            client_id: Client identifier
            retention_days: Number of days to retain data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            retention_until = datetime.utcnow() + timedelta(days=retention_days)
            
            query = text("""
                UPDATE crm_client_preferences
                SET data_retention_until = :retention_until
                WHERE client_id = :client_id
            """)
            
            result = self.session.execute(
                query,
                {
                    'client_id': client_id,
                    'retention_until': retention_until
                }
            )
            
            self.session.commit()
            
            updated = result.rowcount > 0
            if updated:
                logger.info(
                    f"Set data retention period for client {client_id} to {retention_days} days"
                )
            
            return updated
            
        except Exception as e:
            logger.error(f"Failed to set data retention period: {e}")
            self.session.rollback()
            return False
    
    def cleanup_expired_data(self) -> int:
        """
        Clean up data that has exceeded retention period.
        
        Returns:
            Number of clients whose data was cleaned up
        """
        try:
            # Find clients with expired data retention
            query = text("""
                SELECT client_id
                FROM crm_client_preferences
                WHERE data_retention_until < NOW()
                AND deleted_at IS NULL
            """)
            
            expired_clients = self.session.execute(query).fetchall()
            
            cleanup_count = 0
            for row in expired_clients:
                client_id = row[0]
                if self.request_data_deletion(
                    client_id=client_id,
                    deletion_reason="Automatic deletion - Data retention period expired"
                ):
                    cleanup_count += 1
            
            logger.info(f"Cleaned up expired data for {cleanup_count} clients")
            return cleanup_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired data: {e}")
            return 0
