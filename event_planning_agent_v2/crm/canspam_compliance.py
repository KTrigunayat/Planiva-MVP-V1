"""
CAN-SPAM Compliance Module

Implements CAN-SPAM Act compliance features for email communications:
- Opt-out handling
- Unsubscribe link generation
- Opt-out tracking
- Physical address inclusion
- Accurate header information
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.orm import Session

from .models import MessageChannel


logger = logging.getLogger(__name__)


class CANSPAMComplianceManager:
    """
    Manages CAN-SPAM Act compliance for email communications.
    
    Implements:
    - Opt-out/unsubscribe handling
    - Opt-out tracking and logging
    - Unsubscribe link generation
    - Physical address management
    """
    
    # Physical mailing address for CAN-SPAM compliance
    PHYSICAL_ADDRESS = {
        'company_name': 'Event Planning Services',
        'street': '123 Event Plaza',
        'city': 'San Francisco',
        'state': 'CA',
        'zip': '94102',
        'country': 'USA'
    }
    
    def __init__(self, session: Session):
        """
        Initialize CAN-SPAM compliance manager.
        
        Args:
            session: SQLAlchemy database session
        """
        self.session = session
    
    def process_opt_out(
        self,
        client_id: str,
        channel: MessageChannel,
        opt_out_info: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Process client opt-out request for a communication channel.
        
        Args:
            client_id: Client identifier
            channel: Communication channel to opt out from
            opt_out_info: Optional dict with ip_address, user_agent
            
        Returns:
            True if opt-out processed successfully, False otherwise
        """
        try:
            # Determine which opt-out flag to set
            opt_out_field = None
            if channel == MessageChannel.EMAIL:
                opt_out_field = 'opt_out_email'
            elif channel == MessageChannel.SMS:
                opt_out_field = 'opt_out_sms'
            elif channel == MessageChannel.WHATSAPP:
                opt_out_field = 'opt_out_whatsapp'
            else:
                logger.error(f"Invalid channel for opt-out: {channel}")
                return False
            
            # Update opt-out status
            query = text(f"""
                UPDATE crm_client_preferences
                SET 
                    {opt_out_field} = TRUE,
                    opt_out_timestamp = :opt_out_timestamp,
                    opt_out_ip_address = :ip_address,
                    opt_out_user_agent = :user_agent,
                    updated_at = :updated_at
                WHERE client_id = :client_id
            """)
            
            result = self.session.execute(
                query,
                {
                    'client_id': client_id,
                    'opt_out_timestamp': datetime.utcnow(),
                    'ip_address': opt_out_info.get('ip_address') if opt_out_info else None,
                    'user_agent': opt_out_info.get('user_agent') if opt_out_info else None,
                    'updated_at': datetime.utcnow()
                }
            )
            
            self.session.commit()
            
            updated = result.rowcount > 0
            if updated:
                logger.info(
                    f"Processed opt-out for client {client_id} on channel {channel.value}"
                )
                
                # Log the opt-out in data access log
                self._log_opt_out(client_id, channel, opt_out_info)
            else:
                logger.warning(f"No client found with ID {client_id} for opt-out")
            
            return updated
            
        except Exception as e:
            logger.error(f"Failed to process opt-out: {e}")
            self.session.rollback()
            return False
    
    def process_opt_in(
        self,
        client_id: str,
        channel: MessageChannel
    ) -> bool:
        """
        Process client opt-in request (re-subscribe) for a communication channel.
        
        Args:
            client_id: Client identifier
            channel: Communication channel to opt in to
            
        Returns:
            True if opt-in processed successfully, False otherwise
        """
        try:
            # Determine which opt-out flag to clear
            opt_out_field = None
            if channel == MessageChannel.EMAIL:
                opt_out_field = 'opt_out_email'
            elif channel == MessageChannel.SMS:
                opt_out_field = 'opt_out_sms'
            elif channel == MessageChannel.WHATSAPP:
                opt_out_field = 'opt_out_whatsapp'
            else:
                logger.error(f"Invalid channel for opt-in: {channel}")
                return False
            
            # Update opt-in status
            query = text(f"""
                UPDATE crm_client_preferences
                SET 
                    {opt_out_field} = FALSE,
                    updated_at = :updated_at
                WHERE client_id = :client_id
            """)
            
            result = self.session.execute(
                query,
                {
                    'client_id': client_id,
                    'updated_at': datetime.utcnow()
                }
            )
            
            self.session.commit()
            
            updated = result.rowcount > 0
            if updated:
                logger.info(
                    f"Processed opt-in for client {client_id} on channel {channel.value}"
                )
            
            return updated
            
        except Exception as e:
            logger.error(f"Failed to process opt-in: {e}")
            self.session.rollback()
            return False
    
    def check_opt_out_status(
        self,
        client_id: str,
        channel: MessageChannel
    ) -> bool:
        """
        Check if client has opted out of a communication channel.
        
        Args:
            client_id: Client identifier
            channel: Communication channel to check
            
        Returns:
            True if client has opted out, False otherwise
        """
        try:
            # Determine which opt-out field to check
            opt_out_field = None
            if channel == MessageChannel.EMAIL:
                opt_out_field = 'opt_out_email'
            elif channel == MessageChannel.SMS:
                opt_out_field = 'opt_out_sms'
            elif channel == MessageChannel.WHATSAPP:
                opt_out_field = 'opt_out_whatsapp'
            else:
                logger.error(f"Invalid channel for opt-out check: {channel}")
                return False
            
            query = text(f"""
                SELECT {opt_out_field}
                FROM crm_client_preferences
                WHERE client_id = :client_id
            """)
            
            result = self.session.execute(query, {'client_id': client_id}).scalar()
            
            # If no preferences found, assume not opted out
            if result is None:
                return False
            
            return bool(result)
            
        except Exception as e:
            logger.error(f"Failed to check opt-out status: {e}")
            # Fail safe: assume opted out if we can't check
            return True
    
    def generate_unsubscribe_link(
        self,
        client_id: str,
        communication_id: str,
        base_url: str = "https://eventplanning.example.com"
    ) -> str:
        """
        Generate unsubscribe link for email footer.
        
        Args:
            client_id: Client identifier
            communication_id: Communication identifier
            base_url: Base URL for unsubscribe endpoint
            
        Returns:
            Unsubscribe URL
        """
        # In production, this should include a secure token
        import hashlib
        import hmac
        
        # Generate secure token (simplified - use proper JWT in production)
        token_data = f"{client_id}:{communication_id}"
        token = hashlib.sha256(token_data.encode()).hexdigest()[:16]
        
        unsubscribe_url = f"{base_url}/api/crm/unsubscribe?client_id={client_id}&token={token}"
        
        return unsubscribe_url
    
    def generate_email_footer(
        self,
        client_id: str,
        communication_id: str,
        base_url: str = "https://eventplanning.example.com"
    ) -> str:
        """
        Generate CAN-SPAM compliant email footer.
        
        Includes:
        - Physical mailing address
        - Unsubscribe link
        - Company information
        
        Args:
            client_id: Client identifier
            communication_id: Communication identifier
            base_url: Base URL for unsubscribe endpoint
            
        Returns:
            HTML email footer
        """
        unsubscribe_link = self.generate_unsubscribe_link(
            client_id, communication_id, base_url
        )
        
        address = self.PHYSICAL_ADDRESS
        
        footer_html = f"""
        <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #e0e0e0; font-size: 12px; color: #666;">
            <p style="margin: 5px 0;">
                <strong>{address['company_name']}</strong><br>
                {address['street']}<br>
                {address['city']}, {address['state']} {address['zip']}<br>
                {address['country']}
            </p>
            <p style="margin: 15px 0 5px 0;">
                You are receiving this email because you are using our event planning services.
            </p>
            <p style="margin: 5px 0;">
                <a href="{unsubscribe_link}" style="color: #0066cc; text-decoration: underline;">
                    Unsubscribe from these emails
                </a> | 
                <a href="{base_url}/privacy-policy" style="color: #0066cc; text-decoration: underline;">
                    Privacy Policy
                </a>
            </p>
        </div>
        """
        
        return footer_html
    
    def _log_opt_out(
        self,
        client_id: str,
        channel: MessageChannel,
        opt_out_info: Optional[Dict[str, str]] = None
    ):
        """Log opt-out event in data access log"""
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
                    'write',
                    'client',
                    :purpose,
                    :data_fields,
                    :ip_address,
                    :user_agent,
                    :access_timestamp
                )
            """)
            
            import json
            self.session.execute(
                query,
                {
                    'client_id': client_id,
                    'purpose': f'CAN-SPAM opt-out from {channel.value}',
                    'data_fields': json.dumps({'channel': channel.value, 'opted_out': True}),
                    'ip_address': opt_out_info.get('ip_address') if opt_out_info else None,
                    'user_agent': opt_out_info.get('user_agent') if opt_out_info else None,
                    'access_timestamp': datetime.utcnow()
                }
            )
            
            self.session.commit()
            
        except Exception as e:
            logger.error(f"Failed to log opt-out event: {e}")
    
    def get_opt_out_statistics(self) -> Dict[str, Any]:
        """
        Get statistics on opt-out rates by channel.
        
        Returns:
            Dictionary with opt-out statistics
        """
        try:
            query = text("""
                SELECT 
                    COUNT(*) as total_clients,
                    SUM(CASE WHEN opt_out_email THEN 1 ELSE 0 END) as email_opt_outs,
                    SUM(CASE WHEN opt_out_sms THEN 1 ELSE 0 END) as sms_opt_outs,
                    SUM(CASE WHEN opt_out_whatsapp THEN 1 ELSE 0 END) as whatsapp_opt_outs,
                    COUNT(CASE WHEN opt_out_timestamp IS NOT NULL THEN 1 END) as total_opt_outs
                FROM crm_client_preferences
                WHERE deleted_at IS NULL
            """)
            
            result = self.session.execute(query).fetchone()
            
            if not result:
                return {}
            
            total_clients = result[0] or 0
            email_opt_outs = result[1] or 0
            sms_opt_outs = result[2] or 0
            whatsapp_opt_outs = result[3] or 0
            total_opt_outs = result[4] or 0
            
            statistics = {
                'total_clients': total_clients,
                'email_opt_outs': email_opt_outs,
                'sms_opt_outs': sms_opt_outs,
                'whatsapp_opt_outs': whatsapp_opt_outs,
                'total_opt_outs': total_opt_outs,
                'email_opt_out_rate': (email_opt_outs / total_clients * 100) if total_clients > 0 else 0,
                'sms_opt_out_rate': (sms_opt_outs / total_clients * 100) if total_clients > 0 else 0,
                'whatsapp_opt_out_rate': (whatsapp_opt_outs / total_clients * 100) if total_clients > 0 else 0
            }
            
            logger.info(f"Retrieved opt-out statistics: {total_opt_outs} total opt-outs")
            return statistics
            
        except Exception as e:
            logger.error(f"Failed to get opt-out statistics: {e}")
            return {}
    
    def validate_email_compliance(
        self,
        email_html: str,
        client_id: str,
        communication_id: str
    ) -> tuple[bool, list]:
        """
        Validate that email content is CAN-SPAM compliant.
        
        Args:
            email_html: Email HTML content
            client_id: Client identifier
            communication_id: Communication identifier
            
        Returns:
            Tuple of (is_compliant, list_of_issues)
        """
        issues = []
        
        # Check for unsubscribe link
        if 'unsubscribe' not in email_html.lower():
            issues.append("Missing unsubscribe link")
        
        # Check for physical address
        address_components = [
            self.PHYSICAL_ADDRESS['street'],
            self.PHYSICAL_ADDRESS['city'],
            self.PHYSICAL_ADDRESS['zip']
        ]
        
        has_address = any(component in email_html for component in address_components)
        if not has_address:
            issues.append("Missing physical mailing address")
        
        # Check for accurate "From" information (this should be validated at send time)
        # This is a placeholder - actual validation happens in email sending logic
        
        is_compliant = len(issues) == 0
        
        if not is_compliant:
            logger.warning(
                f"Email {communication_id} for client {client_id} has CAN-SPAM compliance issues: {issues}"
            )
        
        return is_compliant, issues
