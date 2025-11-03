"""
Task List Page - Extended Task List Viewer

Displays extended task list with hierarchical structure, priorities, dependencies,
vendor assignments, logistics status, and conflict indicators.
"""

import streamlit as st
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from components.api_client import api_client, APIError
from components.task_components import (
    priority_badge,
    task_status_badge,
    dependency_indicator,
    conflict_indicator,
    vendor_badge,
    logistics_status_indicator,
    progress_bar,
    task_card
)
from components.pagination import PaginationComponent
from utils.helpers import (
    show_error,
    show_success,
    show_warning,
    show_info,
    init_session_state,
    truncate_text,
    calculate_task_progress,
    calculate_progress_by_priority,
    calculate_progress_by_vendor,
    get_overdue_tasks,
    get_dependent_tasks,
    check_prerequisites_complete
)
from utils.export import get_exporter
from utils.caching import DataSampler

logger = logging.getLogger(__name__)


class TaskListPage:
    """
    Task List Page component for displaying and managing extended task lists.
    
    Features:
    - Hierarchical task display with parent-child relationships
    - Task filtering by priority, status, and vendor
    - Task sorting by multiple criteria
    - Expandable task details with dependencies, vendors, logistics
    - Task completion checkboxes
    - Overall progress tracking
    - Error/warning highlighting
    """
    
    def __init__(self):
        """Initialize task list page."""
        self.api_client = api_client
        self.pagination = PaginationComponent('task_list', page_size=25)
        self._initialize_session_state()
    
    def _initialize_session_state(self):
        """Initialize session state variables for task list."""
        init_session_state('task_list_data', None)
        init_session_state('task_list_last_loaded', None)
        init_session_state('task_filter_priority', ['Critical', 'High', 'Medium', 'Low'])
        init_session_state('task_filter_status', ['Pending', 'In Progress', 'Blocked'])
        init_session_state('task_filter_vendor', '')
        init_session_state('task_sort_by', 'priority')
        init_session_state('expanded_tasks', set())
    
    def render(self):
        """Main rendering function for task list page."""
        st.header("📋 Extended Task List")
        st.markdown("View and manage all tasks for your event with priorities, dependencies, and assignments.")
        
        # Get current plan ID
        plan_id = st.session_state.get('current_plan_id')
        
        if not plan_id:
            self._render_no_plan_message()
            return
        
        # Load task list data
        task_data = self._load_task_list(plan_id)
        
        if task_data is None:
            show_error("Failed to load task list. Please check your connection and try again.")
            if st.button("🔄 Retry", key="retry_load_tasks"):
                st.session_state.task_list_data = None
                st.rerun()
            return
        
        # Check if task list is empty
        tasks = task_data.get('tasks', [])
        if not tasks:
            self._render_empty_task_list()
            return
        
        # Render controls and filters
        self._render_controls(plan_id)
        
        st.divider()
        
        # Render overall progress
        self._render_overall_progress(tasks)
        
        st.divider()
        
        # Apply filters and sorting
        filtered_tasks = self._apply_filters(tasks)
        sorted_tasks = self._apply_sorting(filtered_tasks)
        
        # Render pagination controls
        if sorted_tasks:
            current_page = self.pagination.render_controls(len(sorted_tasks))
            
            st.divider()
            
            # Get paginated tasks
            paginated_tasks = self.pagination.paginate_data(sorted_tasks)
            
            # Display task count
            page_size = st.session_state.get('task_list_page_size', 25)
            start_idx = (current_page - 1) * page_size + 1
            end_idx = min(current_page * page_size, len(sorted_tasks))
            st.markdown(f"**Showing {start_idx}-{end_idx} of {len(sorted_tasks)} tasks** (filtered from {len(tasks)} total)")
            
            # Render task list
            self._render_task_list(paginated_tasks, plan_id)
        else:
            show_info("No tasks match the current filters. Try adjusting your filter criteria.")
    
    def _render_no_plan_message(self):
        """Render message when no plan is selected."""
        st.info("ℹ️ No event plan selected.")
        
        st.markdown("""
        ### Getting Started with Task Management
        
        To view your extended task list:
        
        1. **Create a Plan**: Go to "➕ Create Plan" to start a new event plan
        2. **Wait for Processing**: The system will generate vendor combinations
        3. **Select Combination**: Choose your preferred vendor combination
        4. **View Tasks**: Return here to see your comprehensive task list
        
        The extended task list includes:
        - ✅ Prioritized tasks with timelines
        - 👤 Vendor assignments
        - 🔗 Task dependencies
        - 🚚 Logistics status
        - ⚠️ Conflict detection
        """)
        
        if st.button("➕ Create New Plan", key="create_plan_from_tasks"):
            st.session_state.current_page = 'create_plan'
            st.rerun()
    
    def _render_empty_task_list(self):
        """Render message when task list is empty."""
        st.warning("⚠️ No tasks have been generated yet.")
        
        st.markdown("""
        ### Task Generation Status
        
        Tasks are automatically generated after you select a vendor combination.
        
        **Next Steps:**
        1. Ensure you have selected a vendor combination in "🎯 Results"
        2. Wait for the task generation process to complete
        3. Return here to view your tasks
        
        If you've already selected a combination and tasks haven't appeared,
        the system may still be processing. Please check back in a few moments.
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
        cached_data = st.session_state.get('task_list_data')
        last_loaded = st.session_state.get('task_list_last_loaded')
        
        # Use cache if less than 30 seconds old
        if cached_data and last_loaded:
            age = (datetime.now() - last_loaded).total_seconds()
            if age < 30:
                return cached_data
        
        # Load from API
        try:
            with st.spinner("Loading task list..."):
                task_data = self.api_client.get_extended_task_list(plan_id)
                
                # Cache the data
                st.session_state.task_list_data = task_data
                st.session_state.task_list_last_loaded = datetime.now()
                
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
    
    def _render_controls(self, plan_id: str):
        """
        Render control buttons and filters.
        
        Args:
            plan_id: Plan identifier
        """
        col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
        
        with col1:
            # Refresh button
            if st.button("🔄 Refresh", key="refresh_tasks", use_container_width=True):
                st.session_state.task_list_data = None
                st.rerun()
        
        with col2:
            # View timeline button
            if st.button("📊 View Timeline", key="view_timeline", use_container_width=True):
                st.session_state.current_page = 'timeline_view'
                st.rerun()
        
        with col3:
            # View conflicts button
            if st.button("⚠️ View Conflicts", key="view_conflicts", use_container_width=True):
                st.session_state.current_page = 'conflicts'
                st.rerun()
        
        with col4:
            # Export button
            if st.button("📥 Export", key="export_tasks", use_container_width=True):
                self._export_tasks_to_csv(plan_id)
        
        st.markdown("---")
        
        # Filters
        st.subheader("🔍 Filters & Sorting")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            priority_filter = st.multiselect(
                "Priority",
                options=["Critical", "High", "Medium", "Low"],
                default=st.session_state.task_filter_priority,
                key="priority_filter_select"
            )
            st.session_state.task_filter_priority = priority_filter
        
        with col2:
            status_filter = st.multiselect(
                "Status",
                options=["Pending", "In Progress", "Completed", "Blocked", "Overdue"],
                default=st.session_state.task_filter_status,
                key="status_filter_select"
            )
            st.session_state.task_filter_status = status_filter
        
        with col3:
            vendor_filter = st.text_input(
                "Vendor Name",
                value=st.session_state.task_filter_vendor,
                placeholder="Filter by vendor...",
                key="vendor_filter_input"
            )
            st.session_state.task_filter_vendor = vendor_filter
        
        with col4:
            sort_by = st.selectbox(
                "Sort By",
                options=["priority", "start_date", "duration", "name", "status"],
                index=["priority", "start_date", "duration", "name", "status"].index(
                    st.session_state.task_sort_by
                ),
                key="sort_by_select"
            )
            st.session_state.task_sort_by = sort_by
    
    def _render_overall_progress(self, tasks: List[Dict[str, Any]]):
        """
        Render overall progress metrics with enhanced tracking.
        
        Args:
            tasks: List of all tasks
        """
        st.subheader("📊 Overall Progress")
        
        # Calculate overall progress metrics
        progress = calculate_task_progress(tasks)
        
        # Display key metrics
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Total Tasks", progress['total_tasks'])
        
        with col2:
            st.metric(
                "Completed", 
                progress['completed_tasks'], 
                delta=f"{progress['completion_percentage']:.0f}%"
            )
        
        with col3:
            st.metric("In Progress", progress['in_progress_tasks'])
        
        with col4:
            st.metric(
                "Blocked", 
                progress['blocked_tasks'], 
                delta="⚠️" if progress['blocked_tasks'] > 0 else None
            )
        
        with col5:
            st.metric(
                "Overdue", 
                progress['overdue_tasks'], 
                delta="🚨" if progress['overdue_tasks'] > 0 else None
            )
        
        # Overall progress bar
        render_progress_bar(
            progress['completed_tasks'], 
            progress['total_tasks'], 
            "Overall Completion"
        )
        
        # Progress by priority
        with st.expander("📈 Progress by Priority", expanded=False):
            priority_progress = calculate_progress_by_priority(tasks)
            
            for priority in ["Critical", "High", "Medium", "Low"]:
                priority_data = priority_progress.get(priority, {})
                
                if priority_data.get('total', 0) > 0:
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        render_progress_bar(
                            priority_data['completed'],
                            priority_data['total'],
                            f"{priority} Priority"
                        )
                    
                    with col2:
                        # Show overdue count if any
                        if priority_data.get('overdue', 0) > 0:
                            st.markdown(
                                f"<span style='color: #ff4444;'>🚨 {priority_data['overdue']} overdue</span>",
                                unsafe_allow_html=True
                            )
        
        # Progress by vendor
        with st.expander("👥 Progress by Vendor", expanded=False):
            vendor_progress = calculate_progress_by_vendor(tasks)
            
            if vendor_progress:
                for vendor_name, vendor_data in sorted(
                    vendor_progress.items(), 
                    key=lambda x: x[1]['completion_percentage'],
                    reverse=True
                ):
                    col1, col2, col3 = st.columns([2, 2, 1])
                    
                    with col1:
                        st.markdown(f"**{vendor_name}**")
                        st.caption(f"Type: {vendor_data.get('vendor_type', 'N/A')}")
                    
                    with col2:
                        render_progress_bar(
                            vendor_data['completed'],
                            vendor_data['total'],
                            ""
                        )
                    
                    with col3:
                        st.markdown(
                            f"{vendor_data['completed']}/{vendor_data['total']} tasks"
                        )
                        if vendor_data.get('overdue', 0) > 0:
                            st.markdown(
                                f"<span style='color: #ff4444;'>🚨 {vendor_data['overdue']} overdue</span>",
                                unsafe_allow_html=True
                            )
            else:
                st.info("No vendor assignments yet")
        
        # Overdue tasks section
        overdue_tasks = get_overdue_tasks(tasks)
        if overdue_tasks:
            with st.expander(f"🚨 Overdue Tasks ({len(overdue_tasks)})", expanded=True):
                for task in overdue_tasks:
                    days_overdue = task.get('days_overdue', 0)
                    task_name = task.get('name', 'Unnamed Task')
                    priority = task.get('priority', 'medium')
                    
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        st.markdown(f"**{task_name}**")
                    
                    with col2:
                        st.markdown(priority_badge(priority), unsafe_allow_html=True)
                    
                    with col3:
                        st.markdown(
                            f"<span style='color: #ff0000; font-weight: bold;'>{days_overdue} days overdue</span>",
                            unsafe_allow_html=True
                        )
    
    def _apply_filters(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Apply filters to task list.
        
        Args:
            tasks: List of tasks
            
        Returns:
            Filtered list of tasks
        """
        filtered = tasks
        
        # Priority filter
        if st.session_state.task_filter_priority:
            filtered = [
                t for t in filtered
                if t.get('priority', '').title() in st.session_state.task_filter_priority
            ]
        
        # Status filter
        if st.session_state.task_filter_status:
            filtered = [
                t for t in filtered
                if t.get('status', '').replace('_', ' ').title() in st.session_state.task_filter_status
            ]
        
        # Vendor filter
        if st.session_state.task_filter_vendor:
            vendor_query = st.session_state.task_filter_vendor.lower()
            filtered = [
                t for t in filtered
                if vendor_query in str(t.get('assigned_vendor', {}).get('name', '')).lower()
            ]
        
        return filtered
    
    def _apply_sorting(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Apply sorting to task list.
        
        Args:
            tasks: List of tasks
            
        Returns:
            Sorted list of tasks
        """
        sort_by = st.session_state.task_sort_by
        
        # Define sort keys
        sort_keys = {
            'priority': lambda t: {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}.get(
                t.get('priority', 'medium').lower(), 4
            ),
            'start_date': lambda t: t.get('start_date', '9999-12-31'),
            'duration': lambda t: t.get('estimated_duration_hours', 0),
            'name': lambda t: t.get('name', ''),
            'status': lambda t: t.get('status', '')
        }
        
        if sort_by in sort_keys:
            return sorted(tasks, key=sort_keys[sort_by])
        
        return tasks
    
    def _render_task_list(self, tasks: List[Dict[str, Any]], plan_id: str):
        """
        Render the task list with hierarchical structure.
        
        Args:
            tasks: List of tasks to render
            plan_id: Plan identifier
        """
        st.subheader("📝 Tasks")
        
        # Group tasks by parent-child relationships
        parent_tasks = [t for t in tasks if not t.get('parent_task_id')]
        child_tasks_map = {}
        
        for task in tasks:
            parent_id = task.get('parent_task_id')
            if parent_id:
                if parent_id not in child_tasks_map:
                    child_tasks_map[parent_id] = []
                child_tasks_map[parent_id].append(task)
        
        # Render parent tasks and their children
        for task in parent_tasks:
            self._render_task_card(task, plan_id, child_tasks_map)
    
    def _render_task_card(self, task: Dict[str, Any], plan_id: str, 
                         child_tasks_map: Dict[str, List[Dict[str, Any]]]):
        """
        Render a single task card with expandable details.
        
        Args:
            task: Task data
            plan_id: Plan identifier
            child_tasks_map: Map of parent task IDs to child tasks
        """
        task_id = task.get('id', task.get('task_id', ''))
        task_name = task.get('name', 'Unnamed Task')
        description = task.get('description', '')
        priority = task.get('priority', 'medium')
        status = task.get('status', 'pending')
        is_overdue = task.get('is_overdue', False)
        has_errors = task.get('has_errors', False)
        has_warnings = task.get('has_warnings', False)
        
        # Check if prerequisites are complete
        task_data = st.session_state.get('task_list_data', {})
        all_tasks = task_data.get('tasks', [])
        prerequisites_complete = check_prerequisites_complete(task, all_tasks)
        
        # Calculate days overdue if applicable
        days_overdue = 0
        if is_overdue:
            from datetime import datetime, date
            end_date_str = task.get('end_date')
            if end_date_str:
                try:
                    today = date.today()
                    if isinstance(end_date_str, str):
                        end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00')).date()
                    elif isinstance(end_date_str, datetime):
                        end_date = end_date_str.date()
                    elif isinstance(end_date_str, date):
                        end_date = end_date_str
                    else:
                        end_date = today
                    days_overdue = (today - end_date).days
                except:
                    days_overdue = 0
        
        # Determine card styling based on status
        if has_errors:
            card_style = "border-left: 4px solid #ff4444;"
        elif has_warnings:
            card_style = "border-left: 4px solid #ffaa00;"
        elif is_overdue:
            card_style = "border-left: 4px solid #ff0000;"
        elif status.lower() == 'completed':
            card_style = "border-left: 4px solid #00aa00;"
        else:
            card_style = "border-left: 4px solid #cccccc;"
        
        # Create container with styling
        with st.container():
            st.markdown(f'<div style="{card_style} padding-left: 10px;">', unsafe_allow_html=True)
            
            # Task header
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            
            with col1:
                # Completion checkbox
                is_completed = status.lower() == 'completed'
                checkbox_key = f"task_complete_{task_id}"
                
                # Disable checkbox if prerequisites not complete
                checkbox_disabled = is_completed or not prerequisites_complete
                
                if st.checkbox(
                    task_name,
                    value=is_completed,
                    key=checkbox_key,
                    disabled=checkbox_disabled,
                    help="Complete prerequisite tasks first" if not prerequisites_complete else None
                ):
                    if not is_completed:
                        self._mark_task_complete(plan_id, task_id)
                
                # Show description preview
                if description:
                    st.caption(truncate_text(description, 100))
                
                # Show overdue indicator
                if is_overdue and days_overdue > 0:
                    st.markdown(
                        f"<span style='color: #ff0000; font-weight: bold;'>🚨 {days_overdue} days overdue</span>",
                        unsafe_allow_html=True
                    )
                
                # Show prerequisites warning
                if not prerequisites_complete and status.lower() != 'completed':
                    st.markdown(
                        "<span style='color: #ffaa00;'>⏳ Waiting for prerequisites</span>",
                        unsafe_allow_html=True
                    )
            
            with col2:
                st.markdown(priority_badge(priority), unsafe_allow_html=True)
            
            with col3:
                st.markdown(task_status_badge(status), unsafe_allow_html=True)
            
            with col4:
                # Expand/collapse button
                expand_key = f"expand_{task_id}"
                is_expanded = task_id in st.session_state.expanded_tasks
                
                if st.button(
                    "📖 Details" if not is_expanded else "📕 Hide",
                    key=expand_key,
                    use_container_width=True
                ):
                    if is_expanded:
                        st.session_state.expanded_tasks.remove(task_id)
                    else:
                        st.session_state.expanded_tasks.add(task_id)
                    st.rerun()
            
            # Show errors/warnings
            if has_errors:
                st.error(f"❌ Errors: {task.get('error_message', 'Unknown error')}")
            elif has_warnings:
                st.warning(f"⚠️ Warnings: {task.get('warning_message', 'Unknown warning')}")
            
            # Expandable details
            if is_expanded:
                self._render_task_details(task)
            
            # Render child tasks if any
            child_tasks = child_tasks_map.get(task_id, [])
            if child_tasks:
                st.markdown("**Sub-tasks:**")
                for child_task in child_tasks:
                    with st.container():
                        st.markdown("&nbsp;&nbsp;&nbsp;&nbsp;↳", unsafe_allow_html=True)
                        self._render_task_card(child_task, plan_id, child_tasks_map)
            
            st.markdown('</div>', unsafe_allow_html=True)
            st.divider()
    
    def _render_task_details(self, task: Dict[str, Any]):
        """
        Render detailed task information.
        
        Args:
            task: Task data
        """
        with st.expander("📋 Task Details", expanded=True):
            # Basic information
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**Start Date:** {task.get('start_date', 'N/A')}")
                st.markdown(f"**End Date:** {task.get('end_date', 'N/A')}")
                st.markdown(f"**Duration:** {task.get('estimated_duration', 'N/A')}")
            
            with col2:
                st.markdown(f"**Task Type:** {task.get('task_type', 'N/A')}")
                st.markdown(f"**Created:** {task.get('created_at', 'N/A')}")
                st.markdown(f"**Updated:** {task.get('updated_at', 'N/A')}")
            
            # Full description
            description = task.get('description', '')
            if description:
                st.markdown("**Description:**")
                st.markdown(description)
            
            st.divider()
            
            # Dependencies
            dependencies = task.get('dependencies', [])
            if dependencies:
                st.markdown("**🔗 Dependencies:**")
                render_dependency_indicator(dependencies)
            else:
                st.markdown("**🔗 Dependencies:** None")
            
            st.divider()
            
            # Vendor assignment
            vendor = task.get('assigned_vendor')
            if vendor:
                render_vendor_assignment_card(task)
            else:
                st.warning("⚠️ No vendor assigned - manual assignment required")
            
            st.divider()
            
            # Logistics status
            logistics = task.get('logistics')
            if logistics:
                render_logistics_status_card(task)
            else:
                st.info("ℹ️ No logistics information available")
            
            st.divider()
            
            # Conflicts
            conflicts = task.get('conflicts', [])
            if conflicts:
                st.markdown("**⚠️ Conflicts:**")
                render_conflict_indicator(conflicts)
            else:
                st.success("✅ No conflicts detected")
    
    def _mark_task_complete(self, plan_id: str, task_id: str):
        """
        Mark a task as complete via API and update dependent tasks.
        
        Args:
            plan_id: Plan identifier
            task_id: Task identifier
        """
        try:
            with st.spinner("Updating task status..."):
                result = self.api_client.update_task_status(plan_id, task_id, "completed")
                
                # Get all tasks to check for dependent tasks
                task_data = st.session_state.get('task_list_data')
                if task_data:
                    all_tasks = task_data.get('tasks', [])
                    dependent_tasks = get_dependent_tasks(all_tasks, task_id)
                    
                    if dependent_tasks:
                        # Show info about dependent tasks that can now proceed
                        dependent_names = [t.get('name', 'Unnamed') for t in dependent_tasks[:3]]
                        if len(dependent_tasks) > 3:
                            dependent_names.append(f"and {len(dependent_tasks) - 3} more")
                        
                        show_success(
                            f"Task marked as complete! "
                            f"Dependent tasks can now proceed: {', '.join(dependent_names)}"
                        )
                    else:
                        show_success("Task marked as complete!")
                else:
                    show_success("Task marked as complete!")
                
                # Clear cache to force reload
                st.session_state.task_list_data = None
                st.rerun()
                
        except APIError as e:
            logger.error(f"Error updating task status: {e.message}")
            show_error(f"Failed to update task: {e.message}")
        except Exception as e:
            logger.error(f"Unexpected error updating task: {e}")
            show_error("An unexpected error occurred. Please try again.")
    
    def _export_tasks_to_csv(self, plan_id: str):
        """
        Export tasks to CSV format.
        
        Args:
            plan_id: Plan identifier
        """
        try:
            # Get task data
            task_data = st.session_state.get('task_list_data')
            
            if not task_data:
                show_warning("No task data available to export")
                return
            
            tasks = task_data.get('tasks', [])
            
            if not tasks:
                show_warning("No tasks to export")
                return
            
            # Export to CSV
            with st.spinner("Preparing export..."):
                exporter = get_exporter()
                csv_data = exporter.export_tasks_to_csv(tasks)
                
                # Create download button
                st.download_button(
                    label="📥 Download Tasks CSV",
                    data=csv_data,
                    file_name=f"tasks_{plan_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    key="download_tasks_csv"
                )
                
                show_success(f"Exported {len(tasks)} tasks. Click the download button above.")
                
        except Exception as e:
            logger.error(f"Error exporting tasks: {e}")
            show_error(f"Failed to export tasks: {str(e)}")


def render_task_list_page():
    """Main entry point for task list page."""
    page = TaskListPage()
    page.render()


# For standalone execution
if __name__ == "__main__":
    st.set_page_config(
        page_title="Task List - Event Planning Agent",
        page_icon="📋",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    render_task_list_page()
