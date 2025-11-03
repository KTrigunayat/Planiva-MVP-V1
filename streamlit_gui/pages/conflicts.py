"""
Conflicts Resolution Page - Conflict Detection and Resolution Interface

Displays detected conflicts with severity indicators, affected tasks, and
suggested resolutions. Allows users to apply resolutions to conflicts.
"""

import streamlit as st
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from components.api_client import api_client, APIError
from components.task_components import (
    priority_badge,
    conflict_indicator
)
from utils.helpers import (
    show_error,
    show_success,
    show_warning,
    show_info,
    init_session_state
)

logger = logging.getLogger(__name__)


class ConflictsPage:
    """
    Conflicts Resolution Page component for viewing and resolving conflicts.
    
    Features:
    - Display conflicts with severity indicators
    - Show conflict type, affected tasks, and descriptions
    - Display suggested resolutions from Conflict Check Tool
    - Apply resolutions to conflicts
    - Filter conflicts by type and severity
    - Highlight timeline and resource conflicts
    - Show venue availability conflicts
    - Success message when no conflicts exist
    """
    
    # Severity color mapping
    SEVERITY_COLORS = {
        'critical': '🔴',
        'high': '🟠',
        'medium': '🟡',
        'low': '🟢'
    }
    
    # Conflict type icons
    CONFLICT_TYPE_ICONS = {
        'timeline': '⏰',
        'resource': '👥',
        'venue': '🏛️',
        'vendor': '👤',
        'logistics': '🚚',
        'budget': '💰',
        'dependency': '🔗'
    }
    
    def __init__(self):
        """Initialize conflicts page."""
        self.api_client = api_client
        self._initialize_session_state()
    
    def _initialize_session_state(self):
        """Initialize session state variables for conflicts page."""
        init_session_state('conflicts_data', None)
        init_session_state('conflicts_last_loaded', None)
        init_session_state('conflicts_filter_type', [])
        init_session_state('conflicts_filter_severity', ['Critical', 'High', 'Medium', 'Low'])
        init_session_state('expanded_conflicts', set())
        init_session_state('selected_resolutions', {})
    
    def render(self):
        """Main rendering function for conflicts page."""
        st.header("⚠️ Conflicts Resolution")
        st.markdown("Identify and resolve scheduling, resource, and venue conflicts in your event plan.")
        
        # Get current plan ID
        plan_id = st.session_state.get('current_plan_id')
        
        if not plan_id:
            self._render_no_plan_message()
            return
        
        # Load conflicts data
        conflicts_data = self._load_conflicts(plan_id)
        
        if conflicts_data is None:
            show_error("Failed to load conflicts data. Please check your connection and try again.")
            if st.button("🔄 Retry", key="retry_load_conflicts"):
                st.session_state.conflicts_data = None
                st.rerun()
            return
        
        # Get conflicts list
        conflicts = conflicts_data.get('conflicts', [])
        
        # Check if there are no conflicts
        if not conflicts:
            self._render_no_conflicts_message()
            return
        
        # Render controls
        self._render_controls(plan_id)
        
        st.divider()
        
        # Apply filters
        filtered_conflicts = self._apply_filters(conflicts)
        
        # Display conflict count
        st.markdown(f"**Showing {len(filtered_conflicts)} of {len(conflicts)} conflicts**")
        
        # Render conflicts summary
        self._render_conflicts_summary(filtered_conflicts)
        
        st.divider()
        
        # Render conflict list
        if filtered_conflicts:
            self._render_conflicts_list(filtered_conflicts, plan_id)
        else:
            show_info("No conflicts match the current filters. Try adjusting your filter criteria.")
    
    def _render_no_plan_message(self):
        """Render message when no plan is selected."""
        st.info("ℹ️ No event plan selected.")
        
        st.markdown("""
        ### Getting Started with Conflict Resolution
        
        To view and resolve conflicts:
        
        1. **Create a Plan**: Go to "➕ Create Plan" to start a new event plan
        2. **Wait for Processing**: The system will generate vendor combinations
        3. **Select Combination**: Choose your preferred vendor combination
        4. **View Conflicts**: Return here to see detected conflicts
        
        The conflict detection system identifies:
        - ⏰ **Timeline Conflicts**: Overlapping task schedules
        - 👥 **Resource Conflicts**: Double-booked vendors or equipment
        - 🏛️ **Venue Conflicts**: Availability and capacity issues
        - 🔗 **Dependency Conflicts**: Broken task dependencies
        - 🚚 **Logistics Conflicts**: Transportation and setup issues
        """)
        
        if st.button("➕ Create New Plan", key="create_plan_from_conflicts"):
            st.session_state.current_page = 'create_plan'
            st.rerun()
    
    def _render_no_conflicts_message(self):
        """Render success message when no conflicts exist."""
        st.success("✅ **No conflicts detected!**")
        
        st.markdown("""
        ### Your Event Plan is Conflict-Free
        
        Great news! The system has analyzed your event plan and found no conflicts.
        
        **What this means:**
        - ✅ All tasks have compatible schedules
        - ✅ No resource double-bookings
        - ✅ Venue availability confirmed
        - ✅ All dependencies are satisfied
        - ✅ Logistics are properly coordinated
        
        **Next Steps:**
        - 📋 Review your [Task List](#) to verify all assignments
        - 📊 Check the [Timeline](#) to visualize your schedule
        - 📄 Generate your [Final Blueprint](#) when ready
        """)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📋 View Task List", key="goto_tasks_from_no_conflicts", use_container_width=True):
                st.session_state.current_page = 'task_list'
                st.rerun()
        
        with col2:
            if st.button("📊 View Timeline", key="goto_timeline_from_no_conflicts", use_container_width=True):
                st.session_state.current_page = 'timeline_view'
                st.rerun()
        
        with col3:
            if st.button("📄 View Blueprint", key="goto_blueprint_from_no_conflicts", use_container_width=True):
                st.session_state.current_page = 'plan_blueprint'
                st.rerun()
    
    def _load_conflicts(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """
        Load conflicts from API with caching.
        
        Args:
            plan_id: Plan identifier
            
        Returns:
            Conflicts data or None on error
        """
        # Check cache
        cached_data = st.session_state.get('conflicts_data')
        last_loaded = st.session_state.get('conflicts_last_loaded')
        
        # Use cache if less than 30 seconds old
        if cached_data and last_loaded:
            age = (datetime.now() - last_loaded).total_seconds()
            if age < 30:
                return cached_data
        
        # Load from API
        try:
            with st.spinner("Loading conflicts..."):
                conflicts_data = self.api_client.get_conflicts(plan_id)
                
                # Cache the data
                st.session_state.conflicts_data = conflicts_data
                st.session_state.conflicts_last_loaded = datetime.now()
                
                return conflicts_data
                
        except APIError as e:
            logger.error(f"Error loading conflicts: {e.message}")
            
            # Return cached data if available
            if cached_data:
                show_warning("Using cached data. Unable to fetch latest updates.")
                return cached_data
            
            return None
        except Exception as e:
            logger.error(f"Unexpected error loading conflicts: {e}")
            return None
    
    def _render_controls(self, plan_id: str):
        """
        Render control buttons and filters.
        
        Args:
            plan_id: Plan identifier
        """
        col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
        
        with col1:
            # Refresh button
            if st.button("🔄 Refresh", key="refresh_conflicts", use_container_width=True):
                st.session_state.conflicts_data = None
                st.rerun()
        
        with col2:
            # View task list button
            if st.button("📋 View Task List", key="view_tasks_from_conflicts", use_container_width=True):
                st.session_state.current_page = 'task_list'
                st.rerun()
        
        with col3:
            # View timeline button
            if st.button("📊 View Timeline", key="view_timeline_from_conflicts", use_container_width=True):
                st.session_state.current_page = 'timeline_view'
                st.rerun()
        
        with col4:
            # Export button (placeholder)
            if st.button("📥 Export", key="export_conflicts", use_container_width=True):
                show_info("Export functionality coming soon!")
        
        st.markdown("---")
        
        # Filters
        st.subheader("🔍 Filters")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Get unique conflict types from data
            conflicts_data = st.session_state.get('conflicts_data', {})
            all_conflicts = conflicts_data.get('conflicts', [])
            available_types = list(set(c.get('type', 'unknown').title() for c in all_conflicts))
            available_types.sort()
            
            type_filter = st.multiselect(
                "Conflict Type",
                options=available_types if available_types else ["Timeline", "Resource", "Venue", "Vendor", "Logistics", "Budget", "Dependency"],
                default=st.session_state.conflicts_filter_type,
                key="conflicts_type_filter"
            )
            st.session_state.conflicts_filter_type = type_filter
        
        with col2:
            severity_filter = st.multiselect(
                "Severity",
                options=["Critical", "High", "Medium", "Low"],
                default=st.session_state.conflicts_filter_severity,
                key="conflicts_severity_filter"
            )
            st.session_state.conflicts_filter_severity = severity_filter
    
    def _apply_filters(self, conflicts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Apply filters to conflicts list.
        
        Args:
            conflicts: List of conflicts
            
        Returns:
            Filtered list of conflicts
        """
        filtered = conflicts
        
        # Type filter
        if st.session_state.conflicts_filter_type:
            filtered = [
                c for c in filtered
                if c.get('type', '').title() in st.session_state.conflicts_filter_type
            ]
        
        # Severity filter
        if st.session_state.conflicts_filter_severity:
            filtered = [
                c for c in filtered
                if c.get('severity', '').title() in st.session_state.conflicts_filter_severity
            ]
        
        return filtered
    
    def _render_conflicts_summary(self, conflicts: List[Dict[str, Any]]):
        """
        Render summary metrics for conflicts.
        
        Args:
            conflicts: List of conflicts
        """
        st.subheader("📊 Conflicts Overview")
        
        # Calculate metrics
        total_conflicts = len(conflicts)
        critical_conflicts = sum(1 for c in conflicts if c.get('severity', '').lower() == 'critical')
        high_conflicts = sum(1 for c in conflicts if c.get('severity', '').lower() == 'high')
        medium_conflicts = sum(1 for c in conflicts if c.get('severity', '').lower() == 'medium')
        low_conflicts = sum(1 for c in conflicts if c.get('severity', '').lower() == 'low')
        
        # Count by type
        type_counts = {}
        for conflict in conflicts:
            conflict_type = conflict.get('type', 'unknown').title()
            type_counts[conflict_type] = type_counts.get(conflict_type, 0) + 1
        
        # Display metrics
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Total Conflicts", total_conflicts)
        
        with col2:
            st.metric("🔴 Critical", critical_conflicts)
        
        with col3:
            st.metric("🟠 High", high_conflicts)
        
        with col4:
            st.metric("🟡 Medium", medium_conflicts)
        
        with col5:
            st.metric("🟢 Low", low_conflicts)
        
        # Display type breakdown
        if type_counts:
            with st.expander("📋 Conflicts by Type"):
                for conflict_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
                    icon = self.CONFLICT_TYPE_ICONS.get(conflict_type.lower(), '⚠️')
                    st.markdown(f"{icon} **{conflict_type}**: {count} conflicts")
    
    def _render_conflicts_list(self, conflicts: List[Dict[str, Any]], plan_id: str):
        """
        Render list of conflicts with details and resolution options.
        
        Args:
            conflicts: List of conflicts
            plan_id: Plan identifier
        """
        st.subheader("🔧 Conflict Details & Resolutions")
        
        # Sort conflicts by severity
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        sorted_conflicts = sorted(
            conflicts,
            key=lambda c: severity_order.get(c.get('severity', 'low').lower(), 4)
        )
        
        # Render each conflict
        for idx, conflict in enumerate(sorted_conflicts, 1):
            self._render_conflict_card(conflict, idx, plan_id)
    
    def _render_conflict_card(self, conflict: Dict[str, Any], index: int, plan_id: str):
        """
        Render a single conflict card with details and resolution options.
        
        Args:
            conflict: Conflict data
            index: Conflict index for display
            plan_id: Plan identifier
        """
        conflict_id = conflict.get('id', conflict.get('conflict_id', f'conflict_{index}'))
        conflict_type = conflict.get('type', 'unknown').title()
        severity = conflict.get('severity', 'medium').title()
        description = conflict.get('description', 'No description available')
        affected_tasks = conflict.get('affected_tasks', [])
        affected_task_names = conflict.get('affected_task_names', [])
        
        # Get severity icon
        severity_icon = self.SEVERITY_COLORS.get(severity.lower(), '⚪')
        
        # Get type icon
        type_icon = self.CONFLICT_TYPE_ICONS.get(conflict_type.lower(), '⚠️')
        
        # Determine card styling based on severity
        if severity.lower() == 'critical':
            card_style = "border-left: 5px solid #ff4444; background-color: #fff5f5;"
        elif severity.lower() == 'high':
            card_style = "border-left: 5px solid #ffaa00; background-color: #fffaf0;"
        elif severity.lower() == 'medium':
            card_style = "border-left: 5px solid #ffff00; background-color: #fffff0;"
        else:
            card_style = "border-left: 5px solid #00aa00; background-color: #f0fff0;"
        
        # Create container with styling
        with st.container():
            st.markdown(f'<div style="{card_style} padding: 15px; border-radius: 5px; margin-bottom: 15px;">', unsafe_allow_html=True)
            
            # Conflict header
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.markdown(f"### {type_icon} Conflict #{index}: {conflict_type}")
                st.markdown(f"**{description}**")
            
            with col2:
                st.markdown(f"**Severity**")
                st.markdown(f"{severity_icon} {severity}")
            
            with col3:
                # Expand/collapse button
                expand_key = f"expand_conflict_{conflict_id}"
                is_expanded = conflict_id in st.session_state.expanded_conflicts
                
                if st.button(
                    "📖 Details" if not is_expanded else "📕 Hide",
                    key=expand_key,
                    use_container_width=True
                ):
                    if is_expanded:
                        st.session_state.expanded_conflicts.remove(conflict_id)
                    else:
                        st.session_state.expanded_conflicts.add(conflict_id)
                    st.rerun()
            
            # Affected tasks summary
            if affected_task_names:
                st.markdown(f"**Affected Tasks ({len(affected_task_names)}):**")
                # Show first 3 tasks, with "and X more" if there are more
                display_tasks = affected_task_names[:3]
                for task_name in display_tasks:
                    st.markdown(f"  • {task_name}")
                if len(affected_task_names) > 3:
                    st.markdown(f"  • *...and {len(affected_task_names) - 3} more*")
            elif affected_tasks:
                st.markdown(f"**Affected Tasks:** {len(affected_tasks)} tasks")
            
            # Expandable details
            if is_expanded:
                st.divider()
                self._render_conflict_details(conflict, plan_id)
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    def _render_conflict_details(self, conflict: Dict[str, Any], plan_id: str):
        """
        Render detailed conflict information and resolution options.
        
        Args:
            conflict: Conflict data
            plan_id: Plan identifier
        """
        conflict_id = conflict.get('id', conflict.get('conflict_id', ''))
        conflict_type = conflict.get('type', 'unknown').lower()
        
        # Render type-specific details
        if conflict_type == 'timeline':
            self._render_timeline_conflict_details(conflict)
        elif conflict_type == 'resource':
            self._render_resource_conflict_details(conflict)
        elif conflict_type == 'venue':
            self._render_venue_conflict_details(conflict)
        else:
            self._render_generic_conflict_details(conflict)
        
        st.divider()
        
        # Render suggested resolutions
        self._render_resolution_options(conflict, plan_id)
    
    def _render_timeline_conflict_details(self, conflict: Dict[str, Any]):
        """
        Render details specific to timeline conflicts.
        
        Args:
            conflict: Conflict data
        """
        st.markdown("#### ⏰ Timeline Conflict Details")
        
        details = conflict.get('details', {})
        overlapping_tasks = details.get('overlapping_tasks', [])
        
        if overlapping_tasks:
            st.markdown("**Overlapping Tasks:**")
            for task in overlapping_tasks:
                task_name = task.get('name', 'Unknown')
                start_time = task.get('start_time', 'N/A')
                end_time = task.get('end_time', 'N/A')
                st.markdown(f"  • **{task_name}**: {start_time} - {end_time}")
        
        overlap_duration = details.get('overlap_duration', '')
        if overlap_duration:
            st.warning(f"⚠️ **Overlap Duration:** {overlap_duration}")
        
        # Additional timeline info
        affected_vendor = details.get('affected_vendor', '')
        if affected_vendor:
            st.markdown(f"**Affected Vendor:** {affected_vendor}")
    
    def _render_resource_conflict_details(self, conflict: Dict[str, Any]):
        """
        Render details specific to resource conflicts.
        
        Args:
            conflict: Conflict data
        """
        st.markdown("#### 👥 Resource Conflict Details")
        
        details = conflict.get('details', {})
        resource_type = details.get('resource_type', 'Unknown')
        resource_name = details.get('resource_name', 'Unknown')
        double_bookings = details.get('double_bookings', [])
        
        st.markdown(f"**Resource Type:** {resource_type}")
        st.markdown(f"**Resource Name:** {resource_name}")
        
        if double_bookings:
            st.markdown("**Double-Booked Time Slots:**")
            for booking in double_bookings:
                time_slot = booking.get('time_slot', 'N/A')
                tasks = booking.get('tasks', [])
                st.markdown(f"  • **{time_slot}**: {len(tasks)} tasks")
                for task in tasks:
                    st.markdown(f"    - {task}")
        
        availability = details.get('availability', '')
        if availability:
            st.info(f"ℹ️ **Availability:** {availability}")
    
    def _render_venue_conflict_details(self, conflict: Dict[str, Any]):
        """
        Render details specific to venue conflicts.
        
        Args:
            conflict: Conflict data
        """
        st.markdown("#### 🏛️ Venue Conflict Details")
        
        details = conflict.get('details', {})
        venue_name = details.get('venue_name', 'Unknown')
        conflict_reason = details.get('reason', 'Unknown')
        availability_info = details.get('availability', {})
        
        st.markdown(f"**Venue:** {venue_name}")
        st.markdown(f"**Issue:** {conflict_reason}")
        
        if availability_info:
            st.markdown("**Availability Information:**")
            
            available_dates = availability_info.get('available_dates', [])
            if available_dates:
                st.markdown(f"  • **Available Dates:** {', '.join(available_dates)}")
            
            capacity = availability_info.get('capacity', '')
            if capacity:
                st.markdown(f"  • **Capacity:** {capacity}")
            
            restrictions = availability_info.get('restrictions', [])
            if restrictions:
                st.markdown(f"  • **Restrictions:** {', '.join(restrictions)}")
    
    def _render_generic_conflict_details(self, conflict: Dict[str, Any]):
        """
        Render generic conflict details.
        
        Args:
            conflict: Conflict data
        """
        st.markdown("#### ⚠️ Conflict Details")
        
        details = conflict.get('details', {})
        
        if details:
            for key, value in details.items():
                if isinstance(value, (list, dict)):
                    st.markdown(f"**{key.replace('_', ' ').title()}:**")
                    st.json(value)
                else:
                    st.markdown(f"**{key.replace('_', ' ').title()}:** {value}")
        else:
            st.info("No additional details available for this conflict.")
    
    def _render_resolution_options(self, conflict: Dict[str, Any], plan_id: str):
        """
        Render suggested resolutions and application interface.
        
        Args:
            conflict: Conflict data
            plan_id: Plan identifier
        """
        conflict_id = conflict.get('id', conflict.get('conflict_id', ''))
        suggested_resolutions = conflict.get('suggested_resolutions', [])
        
        st.markdown("#### 🔧 Suggested Resolutions")
        
        if not suggested_resolutions:
            st.info("ℹ️ No automatic resolutions available. Manual intervention may be required.")
            return
        
        # Display resolution options
        resolution_key = f"resolution_select_{conflict_id}"
        
        # Format resolution options for display
        resolution_options = []
        for idx, resolution in enumerate(suggested_resolutions):
            title = resolution.get('title', f'Resolution {idx + 1}')
            description = resolution.get('description', '')
            impact = resolution.get('impact', '')
            
            option_text = f"{title}"
            if impact:
                option_text += f" (Impact: {impact})"
            
            resolution_options.append(option_text)
        
        # Select resolution
        selected_resolution_text = st.selectbox(
            "Choose a resolution:",
            options=["-- Select a resolution --"] + resolution_options,
            key=resolution_key
        )
        
        # Show selected resolution details
        if selected_resolution_text != "-- Select a resolution --":
            selected_idx = resolution_options.index(selected_resolution_text)
            selected_resolution = suggested_resolutions[selected_idx]
            
            st.markdown("**Resolution Details:**")
            st.markdown(f"**Description:** {selected_resolution.get('description', 'N/A')}")
            
            impact = selected_resolution.get('impact', '')
            if impact:
                st.markdown(f"**Impact:** {impact}")
            
            steps = selected_resolution.get('steps', [])
            if steps:
                st.markdown("**Steps:**")
                for step_idx, step in enumerate(steps, 1):
                    st.markdown(f"  {step_idx}. {step}")
            
            # Store selected resolution in session state
            st.session_state.selected_resolutions[conflict_id] = selected_resolution
            
            # Apply resolution button
            col1, col2 = st.columns([1, 3])
            
            with col1:
                if st.button("✅ Apply Resolution", key=f"apply_resolution_{conflict_id}", use_container_width=True):
                    self._apply_resolution(plan_id, conflict_id, selected_resolution)
            
            with col2:
                st.caption("⚠️ Applying this resolution will update your event plan. This action may affect other tasks.")
    
    def _apply_resolution(self, plan_id: str, conflict_id: str, resolution: Dict[str, Any]):
        """
        Apply a resolution to a conflict via API.
        
        Args:
            plan_id: Plan identifier
            conflict_id: Conflict identifier
            resolution: Resolution data to apply
        """
        try:
            with st.spinner("Applying resolution..."):
                result = self.api_client.resolve_conflict(plan_id, conflict_id, resolution)
                
                # Clear cache to force reload
                st.session_state.conflicts_data = None
                st.session_state.task_list_data = None
                st.session_state.timeline_data = None
                
                # Remove from expanded conflicts
                if conflict_id in st.session_state.expanded_conflicts:
                    st.session_state.expanded_conflicts.remove(conflict_id)
                
                # Remove from selected resolutions
                if conflict_id in st.session_state.selected_resolutions:
                    del st.session_state.selected_resolutions[conflict_id]
                
                show_success(f"✅ Resolution applied successfully! The conflict has been resolved.")
                st.rerun()
                
        except APIError as e:
            logger.error(f"Error applying resolution: {e.message}")
            show_error(f"Failed to apply resolution: {e.message}")
        except Exception as e:
            logger.error(f"Unexpected error applying resolution: {e}")
            show_error("An unexpected error occurred. Please try again.")


def render_conflicts_page():
    """Main entry point for conflicts page."""
    page = ConflictsPage()
    page.render()


# For standalone execution
if __name__ == "__main__":
    st.set_page_config(
        page_title="Conflicts Resolution - Event Planning Agent",
        page_icon="⚠️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    render_conflicts_page()
