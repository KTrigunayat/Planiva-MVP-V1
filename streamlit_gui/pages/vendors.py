"""
Vendors Page - Vendor-Centric Task View

Displays all tasks organized by vendor with workload distribution and analytics.
"""

import streamlit as st
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from components.api_client import api_client, APIError
from components.task_components import (
    vendor_badge,
    priority_badge,
    task_status_badge,
    task_summary_metrics
)
from utils.helpers import (
    show_error,
    show_success,
    show_warning,
    show_info,
    init_session_state
)

logger = logging.getLogger(__name__)


class VendorsPage:
    """
    Vendors Page component for displaying vendor-centric task views.
    
    Features:
    - Vendor-centric task organization
    - Workload distribution charts
    - Vendor filtering and search
    - Task completion tracking per vendor
    - Vendor contact information
    """
    
    def __init__(self):
        """Initialize vendors page."""
        self.api_client = api_client
        self._initialize_session_state()
    
    def _initialize_session_state(self):
        """Initialize session state variables for vendors page."""
        init_session_state('vendors_task_data', None)
        init_session_state('vendors_last_loaded', None)
        init_session_state('selected_vendor_filter', None)
    
    def render(self):
        """Main rendering function for vendors page."""
        st.header("👥 Vendor Assignments")
        st.markdown("View all tasks organized by assigned vendors with workload distribution.")
        
        # Get current plan ID
        plan_id = st.session_state.get('current_plan_id')
        
        if not plan_id:
            self._render_no_plan_message()
            return
        
        # Load task list data
        task_data = self._load_task_list(plan_id)
        
        if task_data is None:
            show_error("Failed to load task data. Please check your connection and try again.")
            if st.button("🔄 Retry", key="retry_load_vendor_tasks"):
                st.session_state.vendors_task_data = None
                st.rerun()
            return
        
        # Check if task list is empty
        tasks = task_data.get('tasks', [])
        if not tasks:
            self._render_empty_task_list()
            return
        
        # Render controls
        self._render_controls()
        
        st.divider()
        
        # Render workload distribution chart
        render_vendor_workload_chart(tasks)
        
        st.divider()
        
        # Render vendor-centric view
        selected_vendor = st.session_state.get('selected_vendor_filter')
        render_vendor_centric_view(tasks, selected_vendor)
    
    def _render_no_plan_message(self):
        """Render message when no plan is selected."""
        st.info("ℹ️ No event plan selected.")
        
        st.markdown("""
        ### Getting Started with Vendor Management
        
        To view vendor assignments:
        
        1. **Create a Plan**: Go to "➕ Create Plan" to start a new event plan
        2. **Wait for Processing**: The system will generate vendor combinations
        3. **Select Combination**: Choose your preferred vendor combination
        4. **View Vendors**: Return here to see vendor assignments and workload
        
        The vendor view includes:
        - 👤 All assigned vendors with contact details
        - 📊 Workload distribution charts
        - ✅ Task completion tracking per vendor
        - 🎯 Priority distribution analysis
        """)
        
        if st.button("➕ Create New Plan", key="create_plan_from_vendors"):
            st.session_state.current_page = 'create_plan'
            st.rerun()
    
    def _render_empty_task_list(self):
        """Render message when task list is empty."""
        st.warning("⚠️ No tasks have been generated yet.")
        
        st.markdown("""
        ### Task Generation Status
        
        Vendor assignments are created when tasks are generated after selecting a vendor combination.
        
        **Next Steps:**
        1. Ensure you have selected a vendor combination in "🎯 Results"
        2. Wait for the task generation process to complete
        3. Return here to view vendor assignments
        """)
    
    def _load_task_list(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """
        Load task list from API with caching.
        
        Args:
            plan_id: Plan identifier
            
        Returns:
            Task list data or None on error
        """
        # Check cache
        cached_data = st.session_state.get('vendors_task_data')
        last_loaded = st.session_state.get('vendors_last_loaded')
        
        # Use cache if less than 30 seconds old
        if cached_data and last_loaded:
            age = (datetime.now() - last_loaded).total_seconds()
            if age < 30:
                return cached_data
        
        # Load from API
        try:
            with st.spinner("Loading vendor assignments..."):
                task_data = self.api_client.get_extended_task_list(plan_id)
                
                # Cache the data
                st.session_state.vendors_task_data = task_data
                st.session_state.vendors_last_loaded = datetime.now()
                
                return task_data
                
        except APIError as e:
            logger.error(f"Error loading task list: {e.message}")
            
            # Return cached data if available
            if cached_data:
                show_warning("Using cached data. Unable to fetch latest updates.")
                return cached_data
            
            return None
        except Exception as e:
            logger.error(f"Unexpected error loading task list: {e}")
            return None
    
    def _render_controls(self):
        """Render control buttons."""
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Refresh button
            if st.button("🔄 Refresh", key="refresh_vendors", use_container_width=True):
                st.session_state.vendors_task_data = None
                st.rerun()
        
        with col2:
            # View task list button
            if st.button("📋 View Task List", key="view_task_list", use_container_width=True):
                st.session_state.current_page = 'task_list'
                st.rerun()
        
        with col3:
            # View timeline button
            if st.button("📊 View Timeline", key="view_timeline_from_vendors", use_container_width=True):
                st.session_state.current_page = 'timeline_view'
                st.rerun()
        
        with col4:
            # Export button (placeholder)
            if st.button("📥 Export", key="export_vendors", use_container_width=True):
                show_info("Export functionality coming soon!")


def render_vendors_page():
    """Main entry point for vendors page."""
    page = VendorsPage()
    page.render()


# For standalone execution
if __name__ == "__main__":
    st.set_page_config(
        page_title="Vendor Assignments - Event Planning Agent",
        page_icon="👥",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    render_vendors_page()
