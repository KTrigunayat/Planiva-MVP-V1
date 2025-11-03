"""
Health monitoring and connection status management
"""
import time
from datetime import datetime, timedelta
from typing import Dict, Optional
import streamlit as st
from components.api_client import api_client, APIError
from utils.config import config
from utils.helpers import init_session_state

class HealthMonitor:
    """
    Monitors API connection health and provides status information
    """
    
    def __init__(self):
        self.last_check_time: Optional[datetime] = None
        self.check_interval = config.HEALTH_CHECK_INTERVAL
        
    def check_connection(self, force: bool = False) -> Dict:
        """
        Check API connection health
        
        Args:
            force: Force a new check even if recently checked
            
        Returns:
            Dict with status information
        """
        now = datetime.now()
        
        # Check if we need to perform a new health check
        if not force and self.last_check_time:
            time_since_check = (now - self.last_check_time).total_seconds()
            if time_since_check < self.check_interval:
                # Return cached status if available
                return st.session_state.get('api_health_status', {
                    'status': 'unknown',
                    'message': 'Health check pending'
                })
        
        try:
            # Perform health check
            health_data = api_client.health_check()
            
            status = {
                'status': 'healthy',
                'message': 'API server is responding',
                'server_status': health_data.get('status', 'unknown'),
                'server_info': health_data,
                'last_check': now.isoformat(),
                'response_time': None
            }
            
            # Measure response time
            start_time = time.time()
            api_client.health_check()
            response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            status['response_time'] = round(response_time, 2)
            
        except APIError as e:
            status = {
                'status': 'unhealthy',
                'message': f'API server error: {e.message}',
                'error': str(e),
                'last_check': now.isoformat(),
                'response_time': None
            }
        except Exception as e:
            status = {
                'status': 'error',
                'message': f'Connection error: {str(e)}',
                'error': str(e),
                'last_check': now.isoformat(),
                'response_time': None
            }
        
        # Cache the status
        st.session_state['api_health_status'] = status
        self.last_check_time = now
        
        return status
    
    def get_status_color(self, status: str) -> str:
        """Get color for status display"""
        colors = {
            'healthy': '#28a745',    # Green
            'unhealthy': '#dc3545',  # Red
            'error': '#ffc107',      # Yellow
            'unknown': '#6c757d'     # Gray
        }
        return colors.get(status, '#6c757d')
    
    def get_status_icon(self, status: str) -> str:
        """Get icon for status display"""
        icons = {
            'healthy': '🟢',
            'unhealthy': '🔴',
            'error': '🟡',
            'unknown': '⚪'
        }
        return icons.get(status, '⚪')
    
    def display_status_widget(self, show_details: bool = False, key_suffix: str = "main"):
        """
        Display connection status widget in Streamlit
        
        Args:
            show_details: Whether to show detailed status information
            key_suffix: Unique suffix for button keys to avoid conflicts
        """
        # Initialize session state
        init_session_state('api_health_status', {'status': 'unknown', 'message': 'Not checked'})
        
        # Get current status
        status = st.session_state.get('api_health_status', {})
        
        # Create status display
        col1, col2, col3 = st.columns([1, 3, 1])
        
        with col1:
            if st.button("🔄", help="Refresh connection status", key=f"health_refresh_{key_suffix}"):
                with st.spinner("Checking connection..."):
                    status = self.check_connection(force=True)
        
        with col2:
            status_text = status.get('status', 'unknown').title()
            icon = self.get_status_icon(status.get('status', 'unknown'))
            st.write(f"{icon} **API Status:** {status_text}")
        
        with col3:
            if status.get('response_time'):
                st.write(f"⏱️ {status['response_time']}ms")
        
        # Show detailed information if requested
        if show_details and status:
            with st.expander("Connection Details"):
                st.json(status)
        
        # Show error message if unhealthy
        if status.get('status') in ['unhealthy', 'error']:
            st.error(f"⚠️ {status.get('message', 'Connection issue')}")
            
            # Provide troubleshooting suggestions
            st.info("""
            **Troubleshooting:**
            - Check if the Event Planning Agent v2 server is running
            - Verify the API_BASE_URL configuration
            - Check network connectivity
            - Review server logs for errors
            """)
    
    def ensure_connection(self) -> bool:
        """
        Ensure API connection is healthy, show error if not
        
        Returns:
            True if connection is healthy, False otherwise
        """
        status = self.check_connection()
        
        if status.get('status') != 'healthy':
            st.error(f"❌ Cannot connect to API server: {status.get('message', 'Unknown error')}")
            
            # Show retry button
            if st.button("🔄 Retry Connection", key="health_retry_connection"):
                st.rerun()
            
            return False
        
        return True
    
    def auto_check_connection(self):
        """
        Automatically check connection status periodically
        This should be called in the main app loop
        """
        # Check if enough time has passed since last check
        status = st.session_state.get('api_health_status', {})
        last_check = status.get('last_check')
        
        if last_check:
            try:
                last_check_time = datetime.fromisoformat(last_check)
                time_since_check = (datetime.now() - last_check_time).total_seconds()
                
                if time_since_check >= self.check_interval:
                    # Perform background check
                    self.check_connection()
            except:
                # If there's an error parsing the timestamp, just do a new check
                self.check_connection()
        else:
            # No previous check, do initial check
            self.check_connection()

# Global health monitor instance
health_monitor = HealthMonitor()