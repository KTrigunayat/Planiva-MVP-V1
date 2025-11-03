"""
Communication History Page - View and Filter Communication History

Displays all communications for a client/plan with filtering, pagination,
and real-time status updates.
"""

import streamlit as st
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta, date
import time
import logging

from components.api_client import api_client, APIError
from components.crm_components import (
    communication_status_badge,
    channel_icon
)
from utils.helpers import (
    show_error, show_success, show_warning, show_info,
    init_session_state, format_date
)
from utils.export import get_exporter

logger = logging.getLogger(__name__)


class CommunicationHistoryComponent:
    """Component for displaying and managing communication history."""
    
    def __init__(self):
        """Initialize communication history component."""
        self.api_client = api_client
        self.page_size = 20  # Items per page
    
    def render(self, plan_id: Optional[str] = None, client_id: Optional[str] = None):
        """
        Render the communication history page.
        
        Args:
            plan_id: Optional plan ID filter
            client_id: Optional client ID filter
        """
        st.header("📬 Communication History")
        st.markdown("View all communications and their delivery status.")
        
        # Initialize session state
        init_session_state('comm_history_page', 0)
        init_session_state('comm_history_filters', {})
        init_session_state('comm_history_data', None)
        init_session_state('comm_history_last_refresh', None)
        init_session_state('comm_history_auto_refresh', True)
        
        # Render filter controls
        filters = self._render_filters(plan_id, client_id)
        
        # Auto-refresh toggle
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            auto_refresh = st.checkbox(
                "🔄 Auto-refresh (every 30 seconds)",
                value=st.session_state.comm_history_auto_refresh,
                key="auto_refresh_toggle"
            )
            st.session_state.comm_history_auto_refresh = auto_refresh
        
        with col2:
            if st.button("🔄 Refresh Now", use_container_width=True):
                st.session_state.comm_history_data = None
                st.rerun()
        
        with col3:
            if st.button("📥 Export CSV", use_container_width=True):
                self._export_to_csv(filters)
        
        # Load communications
        communications_data = self._load_communications(filters)
        
        if communications_data is None:
            show_error("Failed to load communication history. Please check your connection.")
            if st.button("🔄 Retry", key="retry_load_comms"):
                st.rerun()
            return
        
        communications = communications_data.get("communications", [])
        total_count = communications_data.get("total_count", 0)
        
        # Display communications
        if not communications:
            self._render_empty_state()
        else:
            self._render_communications_list(communications)
            self._render_pagination(total_count)
        
        # Auto-refresh logic
        if auto_refresh:
            self._handle_auto_refresh()
    
    def _render_filters(self, plan_id: Optional[str], client_id: Optional[str]) -> Dict[str, Any]:
        """
        Render filter controls.
        
        Args:
            plan_id: Optional plan ID
            client_id: Optional client ID
            
        Returns:
            Dictionary of active filters
        """
        with st.expander("🔍 Filters", expanded=True):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                channel_filter = st.multiselect(
                    "Channel",
                    options=["email", "sms", "whatsapp"],
                    default=st.session_state.comm_history_filters.get("channel", []),
                    format_func=lambda x: f"{channel_icon(x)} {x.upper()}",
                    key="filter_channel"
                )
            
            with col2:
                status_filter = st.multiselect(
                    "Status",
                    options=["sent", "delivered", "opened", "clicked", "failed", "pending"],
                    default=st.session_state.comm_history_filters.get("status", []),
                    key="filter_status"
                )
            
            with col3:
                # Date range filter
                date_from = st.date_input(
                    "From Date",
                    value=st.session_state.comm_history_filters.get(
                        "date_from",
                        date.today() - timedelta(days=30)
                    ),
                    key="filter_date_from"
                )
            
            with col4:
                date_to = st.date_input(
                    "To Date",
                    value=st.session_state.comm_history_filters.get(
                        "date_to",
                        date.today()
                    ),
                    key="filter_date_to"
                )
            
            # Apply filters button
            if st.button("Apply Filters", use_container_width=True, type="primary"):
                st.session_state.comm_history_filters = {
                    "channel": channel_filter,
                    "status": status_filter,
                    "date_from": date_from,
                    "date_to": date_to
                }
                st.session_state.comm_history_page = 0
                st.session_state.comm_history_data = None
                st.rerun()
        
        # Build filters dictionary
        filters = {
            "plan_id": plan_id,
            "client_id": client_id,
            "limit": self.page_size,
            "offset": st.session_state.comm_history_page * self.page_size
        }
        
        if channel_filter:
            filters["channel"] = channel_filter[0] if len(channel_filter) == 1 else None
        
        if status_filter:
            filters["status"] = status_filter[0] if len(status_filter) == 1 else None
        
        return filters
    
    def _load_communications(self, filters: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Load communications from API with caching.
        
        Args:
            filters: Filter parameters
            
        Returns:
            Communications data or None on error
        """
        # Check if we should use cached data
        last_refresh = st.session_state.comm_history_last_refresh
        if (st.session_state.comm_history_data is not None and 
            last_refresh is not None and
            (datetime.now() - last_refresh).total_seconds() < 30):
            return st.session_state.comm_history_data
        
        # Load from API
        try:
            with st.spinner("Loading communications..."):
                data = self.api_client.get_communications(**filters)
                
                # Cache the data
                st.session_state.comm_history_data = data
                st.session_state.comm_history_last_refresh = datetime.now()
                
                return data
        except APIError as e:
            logger.error(f"Error loading communications: {e.message}")
            if e.status_code == 404:
                # No communications found - return empty result
                return {"communications": [], "total_count": 0}
            return None
        except Exception as e:
            logger.error(f"Unexpected error loading communications: {e}")
            return None
    
    def _render_communications_list(self, communications: List[Dict[str, Any]]):
        """
        Render the list of communications.
        
        Args:
            communications: List of communication records
        """
        st.markdown(f"### 📋 Communications ({len(communications)} shown)")
        
        for comm in communications:
            self._render_communication_card(comm)
    
    def _render_communication_card(self, comm: Dict[str, Any]):
        """
        Render a single communication card.
        
        Args:
            comm: Communication data
        """
        # Create a container for the card
        with st.container():
            # Header row
            col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
            
            with col1:
                channel = comm.get("channel", "email")
                message_type = comm.get("message_type", "Unknown")
                st.markdown(f"**{channel_icon(channel)} {channel.upper()}** - {message_type}")
            
            with col2:
                sent_at = comm.get("sent_at")
                if sent_at:
                    try:
                        sent_dt = datetime.fromisoformat(sent_at.replace('Z', '+00:00'))
                        st.markdown(f"📅 {sent_dt.strftime('%Y-%m-%d %H:%M')}")
                    except:
                        st.markdown(f"📅 {sent_at}")
            
            with col3:
                status = comm.get("status", "pending")
                st.markdown(communication_status_badge(status), unsafe_allow_html=True)
            
            with col4:
                # Delivery status indicator
                delivery_status = comm.get("delivery_status", "unknown")
                if delivery_status == "delivered":
                    st.markdown("✅")
                elif delivery_status == "failed":
                    st.markdown("❌")
                else:
                    st.markdown("⏳")
            
            # Expandable details section
            with st.expander("📄 View Details"):
                self._render_communication_details(comm)
            
            st.divider()
    
    def _render_communication_details(self, comm: Dict[str, Any]):
        """
        Render detailed information for a communication.
        
        Args:
            comm: Communication data
        """
        # Basic information
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Communication ID:**")
            st.code(comm.get("communication_id", "N/A"))
            
            st.markdown("**Recipient:**")
            st.text(comm.get("recipient", "N/A"))
            
            st.markdown("**Subject:**")
            st.text(comm.get("subject", "N/A"))
        
        with col2:
            st.markdown("**Plan ID:**")
            st.code(comm.get("plan_id", "N/A"))
            
            st.markdown("**Client ID:**")
            st.code(comm.get("client_id", "N/A"))
            
            st.markdown("**Priority:**")
            priority = comm.get("priority", "normal")
            priority_emoji = {"high": "🔴", "normal": "🟡", "low": "🟢"}.get(priority, "⚪")
            st.text(f"{priority_emoji} {priority.upper()}")
        
        # Message content
        st.markdown("**Message Content:**")
        message_content = comm.get("message_content", "No content available")
        st.text_area(
            "Message",
            value=message_content,
            height=150,
            disabled=True,
            key=f"msg_content_{comm.get('communication_id', 'unknown')}"
        )
        
        # Email-specific tracking (if applicable)
        if comm.get("channel") == "email":
            self._render_email_tracking(comm)
        
        # Error information (if failed)
        if comm.get("status") == "failed":
            self._render_error_info(comm)
        
        # Timestamps
        st.markdown("**Timeline:**")
        timeline_data = []
        
        if comm.get("created_at"):
            timeline_data.append(f"📝 Created: {comm['created_at']}")
        if comm.get("sent_at"):
            timeline_data.append(f"📤 Sent: {comm['sent_at']}")
        if comm.get("delivered_at"):
            timeline_data.append(f"✅ Delivered: {comm['delivered_at']}")
        if comm.get("opened_at"):
            timeline_data.append(f"👁️ Opened: {comm['opened_at']}")
        if comm.get("clicked_at"):
            timeline_data.append(f"🖱️ Clicked: {comm['clicked_at']}")
        
        for item in timeline_data:
            st.text(item)
    
    def _render_email_tracking(self, comm: Dict[str, Any]):
        """
        Render email-specific tracking information.
        
        Args:
            comm: Communication data
        """
        st.markdown("---")
        st.markdown("**📧 Email Tracking:**")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            open_count = comm.get("open_count", 0)
            st.metric("Opens", open_count)
            if comm.get("opened_at"):
                st.caption(f"First opened: {comm['opened_at']}")
        
        with col2:
            click_count = comm.get("click_count", 0)
            st.metric("Clicks", click_count)
            if comm.get("clicked_at"):
                st.caption(f"First clicked: {comm['clicked_at']}")
        
        with col3:
            # Calculate engagement rate
            if open_count > 0:
                engagement = "High" if click_count > 0 else "Medium"
            else:
                engagement = "None"
            st.metric("Engagement", engagement)
    
    def _render_error_info(self, comm: Dict[str, Any]):
        """
        Render error information for failed communications.
        
        Args:
            comm: Communication data
        """
        st.markdown("---")
        st.markdown("**❌ Error Information:**")
        
        error_message = comm.get("error_message", "Unknown error")
        st.error(error_message)
        
        # Retry information
        retry_count = comm.get("retry_count", 0)
        max_retries = comm.get("max_retries", 3)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Retry Attempts", f"{retry_count}/{max_retries}")
        
        with col2:
            retry_status = comm.get("retry_status", "not_retrying")
            if retry_status == "retrying":
                st.warning("🔄 Retry scheduled")
            elif retry_status == "max_retries_reached":
                st.error("❌ Max retries reached")
            else:
                st.info("ℹ️ No retry scheduled")
    
    def _render_empty_state(self):
        """Render empty state when no communications exist."""
        st.info("📭 No communications found")
        
        st.markdown("""
        ### Why might this be empty?
        
        - No communications have been sent yet for this event plan
        - Your filters may be too restrictive
        - Communications are still being processed
        
        ### What can you do?
        
        - Adjust your filters to see more results
        - Check back later as communications are sent
        - Contact support if you expect to see communications here
        """)
    
    def _render_pagination(self, total_count: int):
        """
        Render pagination controls.
        
        Args:
            total_count: Total number of communications
        """
        total_pages = (total_count + self.page_size - 1) // self.page_size
        current_page = st.session_state.comm_history_page
        
        if total_pages <= 1:
            return
        
        st.markdown("---")
        
        col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
        
        with col1:
            if st.button("⏮️ First", disabled=current_page == 0, key="page_first"):
                st.session_state.comm_history_page = 0
                st.session_state.comm_history_data = None
                st.rerun()
        
        with col2:
            if st.button("◀️ Previous", disabled=current_page == 0, key="page_prev"):
                st.session_state.comm_history_page = max(0, current_page - 1)
                st.session_state.comm_history_data = None
                st.rerun()
        
        with col3:
            st.markdown(f"<div style='text-align: center; padding-top: 8px;'>Page {current_page + 1} of {total_pages} ({total_count} total)</div>", unsafe_allow_html=True)
        
        with col4:
            if st.button("Next ▶️", disabled=current_page >= total_pages - 1, key="page_next"):
                st.session_state.comm_history_page = min(total_pages - 1, current_page + 1)
                st.session_state.comm_history_data = None
                st.rerun()
        
        with col5:
            if st.button("Last ⏭️", disabled=current_page >= total_pages - 1, key="page_last"):
                st.session_state.comm_history_page = total_pages - 1
                st.session_state.comm_history_data = None
                st.rerun()
    
    def _handle_auto_refresh(self):
        """Handle auto-refresh logic with 30-second polling."""
        last_refresh = st.session_state.comm_history_last_refresh
        
        if last_refresh is None:
            return
        
        seconds_since_refresh = (datetime.now() - last_refresh).total_seconds()
        
        # Show countdown
        if seconds_since_refresh < 30:
            remaining = int(30 - seconds_since_refresh)
            st.caption(f"🔄 Auto-refresh in {remaining} seconds...")
        else:
            # Time to refresh
            st.session_state.comm_history_data = None
            time.sleep(0.5)  # Small delay to show the refresh
            st.rerun()
    
    def _export_to_csv(self, filters: Dict[str, Any]):
        """
        Export communications to CSV.
        
        Args:
            filters: Current filters
        """
        try:
            # Load all communications (without pagination)
            export_filters = filters.copy()
            export_filters["limit"] = 10000  # Large limit for export
            export_filters["offset"] = 0
            
            with st.spinner("Loading communications for export..."):
                data = self.api_client.get_communications(**export_filters)
                communications = data.get("communications", [])
            
            if not communications:
                show_warning("No communications to export")
                return
            
            # Export using the export utility
            with st.spinner("Preparing export..."):
                exporter = get_exporter()
                csv_data = exporter.export_communications_to_csv(communications)
            
            # Create download button
            st.download_button(
                label="📥 Download Communications CSV",
                data=csv_data,
                file_name=f"communications_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                key="download_csv_button"
            )
            
            show_success(f"Exported {len(communications)} communications. Click the download button above.")
            
        except Exception as e:
            logger.error(f"Error exporting communications: {e}")
            show_error(f"Failed to export: {str(e)}")


def render_communication_history_page():
    """Main rendering function for communication history page."""
    
    st.header("📬 Communication History")
    st.markdown("View all communications and track their delivery status.")
    
    # Initialize session state
    init_session_state('client_id', '')
    init_session_state('current_plan_id', None)
    
    # Get identifiers from session state
    client_id = st.session_state.get('client_id', '')
    plan_id = st.session_state.get('current_plan_id')
    
    # If we have a current plan, try to get client ID from plan data
    if not client_id and plan_id:
        plan_data = st.session_state.get('plan_data', {})
        client_id = plan_data.get('client_id', '')
    
    # Client/Plan ID input section
    with st.expander("🔑 Filter by Client/Plan", expanded=not bool(client_id or plan_id)):
        col1, col2 = st.columns(2)
        
        with col1:
            input_client_id = st.text_input(
                "Client ID (optional)",
                value=client_id,
                help="Filter communications by client ID",
                key="client_id_input_history"
            )
        
        with col2:
            input_plan_id = st.text_input(
                "Plan ID (optional)",
                value=plan_id or "",
                help="Filter communications by plan ID",
                key="plan_id_input_history"
            )
        
        if st.button("Apply ID Filters", key="apply_id_filters"):
            if input_client_id:
                st.session_state.client_id = input_client_id
                client_id = input_client_id
            if input_plan_id:
                st.session_state.current_plan_id = input_plan_id
                plan_id = input_plan_id
            st.rerun()
    
    # Render the component
    component = CommunicationHistoryComponent()
    component.render(plan_id=plan_id, client_id=client_id)
    
    # Additional information
    st.markdown("---")
    
    with st.expander("ℹ️ About Communication History"):
        st.markdown("""
        **Understanding Communication Status**
        
        - **🟡 Sent**: Message has been sent to the communication provider
        - **🟢 Delivered**: Message was successfully delivered to recipient
        - **🔵 Opened**: Email was opened by recipient (email only)
        - **🟣 Clicked**: Link in email was clicked (email only)
        - **🔴 Failed**: Message delivery failed
        - **⚪ Pending**: Message is queued for sending
        
        **Auto-Refresh**
        
        Enable auto-refresh to automatically update the communication status every 30 seconds.
        This is useful for monitoring active communications in real-time.
        
        **Filtering**
        
        Use filters to narrow down communications by:
        - Channel (Email, SMS, WhatsApp)
        - Status (Sent, Delivered, Opened, etc.)
        - Date range
        
        **Export**
        
        Export your communication history to CSV for offline analysis or record keeping.
        """)


# For standalone execution
if __name__ == "__main__":
    st.set_page_config(
        page_title="Communication History - Event Planning Agent",
        page_icon="📬",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    render_communication_history_page()
