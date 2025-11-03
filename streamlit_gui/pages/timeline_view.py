"""
Timeline Visualization Page - Gantt Chart for Task Management

Displays task timeline as an interactive Gantt chart with dependencies,
conflicts, and filtering capabilities.
"""

import streamlit as st
import plotly.figure_factory as ff
import plotly.graph_objects as go
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import pandas as pd

from components.api_client import api_client, APIError
from components.task_components import (
    priority_badge,
    conflict_indicator,
    timeline_legend
)
from utils.helpers import (
    show_error,
    show_success,
    show_warning,
    show_info,
    init_session_state
)

logger = logging.getLogger(__name__)


class TimelineViewPage:
    """
    Timeline Visualization Page component for displaying task schedules.
    
    Features:
    - Interactive Gantt chart with Plotly
    - Color coding by priority level
    - Hover tooltips with task details
    - Dependency lines between tasks
    - Conflict highlighting
    - Zoom and pan controls
    - Filtering by vendor, priority, task type
    - Mobile-responsive design
    """
    
    # Priority color mapping
    PRIORITY_COLORS = {
        'critical': '#FF4444',  # Red
        'high': '#FFAA00',      # Orange
        'medium': '#FFFF00',    # Yellow
        'low': '#00AA00'        # Green
    }
    
    # Time scale options
    TIME_SCALES = {
        'day': 1,
        'week': 7,
        'month': 30
    }
    
    def __init__(self):
        """Initialize timeline view page."""
        self.api_client = api_client
        self._initialize_session_state()
    
    def _initialize_session_state(self):
        """Initialize session state variables for timeline view."""
        init_session_state('timeline_data', None)
        init_session_state('timeline_last_loaded', None)
        init_session_state('timeline_filter_vendor', '')
        init_session_state('timeline_filter_priority', ['Critical', 'High', 'Medium', 'Low'])
        init_session_state('timeline_filter_task_type', '')
        init_session_state('timeline_zoom_level', 'week')
        init_session_state('timeline_show_dependencies', True)
        init_session_state('timeline_show_conflicts', True)
    
    def render(self):
        """Main rendering function for timeline view page."""
        st.header("📊 Task Timeline")
        st.markdown("Visualize your event tasks on an interactive Gantt chart with dependencies and conflicts.")
        
        # Get current plan ID
        plan_id = st.session_state.get('current_plan_id')
        
        if not plan_id:
            self._render_no_plan_message()
            return
        
        # Load timeline data
        timeline_data = self._load_timeline_data(plan_id)
        
        if timeline_data is None:
            show_error("Failed to load timeline data. Please check your connection and try again.")
            if st.button("🔄 Retry", key="retry_load_timeline"):
                st.session_state.timeline_data = None
                st.rerun()
            return
        
        # Check if timeline has tasks
        tasks = timeline_data.get('tasks', [])
        if not tasks:
            self._render_empty_timeline()
            return
        
        # Render controls
        self._render_controls(plan_id)
        
        st.divider()
        
        # Apply filters
        filtered_tasks = self._apply_filters(tasks)
        
        if not filtered_tasks:
            show_info("No tasks match the current filters. Try adjusting your filter criteria.")
            return
        
        # Display task count
        st.markdown(f"**Showing {len(filtered_tasks)} of {len(tasks)} tasks**")
        
        # Render Gantt chart
        self._render_gantt_chart(filtered_tasks, timeline_data)
        
        # Render legend
        self._render_legend()
        
        # Render conflicts summary if any
        conflicts = timeline_data.get('conflicts', [])
        if conflicts and st.session_state.timeline_show_conflicts:
            st.divider()
            self._render_conflicts_summary(conflicts, filtered_tasks)
    
    def _render_no_plan_message(self):
        """Render message when no plan is selected."""
        st.info("ℹ️ No event plan selected.")
        
        st.markdown("""
        ### Getting Started with Timeline View
        
        To view your task timeline:
        
        1. **Create a Plan**: Go to "➕ Create Plan" to start a new event plan
        2. **Wait for Processing**: The system will generate vendor combinations
        3. **Select Combination**: Choose your preferred vendor combination
        4. **View Timeline**: Return here to see your task schedule
        
        The timeline visualization includes:
        - 📊 Interactive Gantt chart
        - 🎨 Color-coded priorities
        - 🔗 Task dependencies
        - ⚠️ Conflict indicators
        - 🔍 Zoom and filter controls
        """)
        
        if st.button("➕ Create New Plan", key="create_plan_from_timeline"):
            st.session_state.current_page = 'create_plan'
            st.rerun()
    
    def _render_empty_timeline(self):
        """Render message when timeline is empty."""
        st.warning("⚠️ No tasks have been generated yet.")
        
        st.markdown("""
        ### Timeline Generation Status
        
        The timeline is automatically generated after you select a vendor combination.
        
        **Next Steps:**
        1. Ensure you have selected a vendor combination in "🎯 Results"
        2. Wait for the task generation process to complete
        3. Return here to view your timeline
        
        If you've already selected a combination and the timeline hasn't appeared,
        the system may still be processing. Please check back in a few moments.
        """)
    
    def _load_timeline_data(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """
        Load timeline data from API with caching.
        
        Args:
            plan_id: Plan identifier
            
        Returns:
            Timeline data or None on error
        """
        # Check cache
        cached_data = st.session_state.get('timeline_data')
        last_loaded = st.session_state.get('timeline_last_loaded')
        
        # Use cache if less than 30 seconds old
        if cached_data and last_loaded:
            age = (datetime.now() - last_loaded).total_seconds()
            if age < 30:
                return cached_data
        
        # Load from API
        try:
            with st.spinner("Loading timeline data..."):
                timeline_data = self.api_client.get_timeline_data(plan_id)
                
                # Cache the data
                st.session_state.timeline_data = timeline_data
                st.session_state.timeline_last_loaded = datetime.now()
                
                return timeline_data
                
        except APIError as e:
            logger.error(f"Error loading timeline data: {e.message}")
            
            # Return cached data if available
            if cached_data:
                show_warning("Using cached data. Unable to fetch latest updates.")
                return cached_data
            
            return None
        except Exception as e:
            logger.error(f"Unexpected error loading timeline data: {e}")
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
            if st.button("🔄 Refresh", key="refresh_timeline", use_container_width=True):
                st.session_state.timeline_data = None
                st.rerun()
        
        with col2:
            # View task list button
            if st.button("📝 View Task List", key="view_task_list", use_container_width=True):
                st.session_state.current_page = 'task_list'
                st.rerun()
        
        with col3:
            # View conflicts button
            if st.button("⚠️ View Conflicts", key="view_conflicts_from_timeline", use_container_width=True):
                st.session_state.current_page = 'conflicts'
                st.rerun()
        
        with col4:
            # Export button (placeholder)
            if st.button("📥 Export", key="export_timeline", use_container_width=True):
                show_info("Export functionality coming soon!")
        
        st.markdown("---")
        
        # Filters and controls
        st.subheader("🔍 Filters & Controls")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            priority_filter = st.multiselect(
                "Priority",
                options=["Critical", "High", "Medium", "Low"],
                default=st.session_state.timeline_filter_priority,
                key="timeline_priority_filter"
            )
            st.session_state.timeline_filter_priority = priority_filter
        
        with col2:
            vendor_filter = st.text_input(
                "Vendor Name",
                value=st.session_state.timeline_filter_vendor,
                placeholder="Filter by vendor...",
                key="timeline_vendor_filter"
            )
            st.session_state.timeline_filter_vendor = vendor_filter
        
        with col3:
            task_type_filter = st.text_input(
                "Task Type",
                value=st.session_state.timeline_filter_task_type,
                placeholder="Filter by type...",
                key="timeline_task_type_filter"
            )
            st.session_state.timeline_filter_task_type = task_type_filter
        
        with col4:
            zoom_level = st.selectbox(
                "Time Scale",
                options=["day", "week", "month"],
                index=["day", "week", "month"].index(st.session_state.timeline_zoom_level),
                key="timeline_zoom_select"
            )
            st.session_state.timeline_zoom_level = zoom_level
        
        # Additional controls
        col1, col2 = st.columns(2)
        
        with col1:
            show_dependencies = st.checkbox(
                "Show Dependencies",
                value=st.session_state.timeline_show_dependencies,
                key="timeline_show_deps"
            )
            st.session_state.timeline_show_dependencies = show_dependencies
        
        with col2:
            show_conflicts = st.checkbox(
                "Show Conflicts",
                value=st.session_state.timeline_show_conflicts,
                key="timeline_show_conflicts_check"
            )
            st.session_state.timeline_show_conflicts = show_conflicts
    
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
        if st.session_state.timeline_filter_priority:
            filtered = [
                t for t in filtered
                if t.get('priority', '').title() in st.session_state.timeline_filter_priority
            ]
        
        # Vendor filter
        if st.session_state.timeline_filter_vendor:
            vendor_query = st.session_state.timeline_filter_vendor.lower()
            filtered = [
                t for t in filtered
                if vendor_query in str(t.get('assigned_vendor', {}).get('name', '')).lower()
            ]
        
        # Task type filter
        if st.session_state.timeline_filter_task_type:
            type_query = st.session_state.timeline_filter_task_type.lower()
            filtered = [
                t for t in filtered
                if type_query in str(t.get('task_type', '')).lower()
            ]
        
        return filtered
    
    def _render_gantt_chart(self, tasks: List[Dict[str, Any]], timeline_data: Dict[str, Any]):
        """
        Render interactive Gantt chart using Plotly.
        
        Args:
            tasks: List of tasks to display
            timeline_data: Full timeline data including dependencies and conflicts
        """
        # Prepare data for Gantt chart
        chart_data = self._prepare_chart_data(tasks)
        
        if not chart_data:
            show_warning("No valid task data to display in timeline.")
            return
        
        # Create Gantt chart
        fig = self._create_gantt_figure(chart_data, tasks, timeline_data)
        
        # Display the chart
        st.plotly_chart(fig, use_container_width=True, config={
            'displayModeBar': True,
            'displaylogo': False,
            'modeBarButtonsToRemove': ['lasso2d', 'select2d'],
            'toImageButtonOptions': {
                'format': 'png',
                'filename': 'event_timeline',
                'height': 800,
                'width': 1200,
                'scale': 2
            }
        })
    
    def _prepare_chart_data(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Prepare task data for Gantt chart.
        
        Args:
            tasks: List of tasks
            
        Returns:
            List of chart data dictionaries
        """
        chart_data = []
        
        for task in tasks:
            task_id = task.get('id', task.get('task_id', ''))
            task_name = task.get('name', 'Unnamed Task')
            start_date = task.get('start_date')
            end_date = task.get('end_date')
            priority = task.get('priority', 'medium').lower()
            
            # Skip tasks without valid dates
            if not start_date or not end_date:
                logger.warning(f"Task {task_id} missing start or end date")
                continue
            
            # Parse dates
            try:
                start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            except (ValueError, AttributeError) as e:
                logger.warning(f"Invalid date format for task {task_id}: {e}")
                continue
            
            # Get color based on priority
            color = self.PRIORITY_COLORS.get(priority, '#CCCCCC')
            
            # Build hover text
            vendor_name = task.get('assigned_vendor', {}).get('name', 'Unassigned')
            duration = task.get('estimated_duration', 'N/A')
            dependencies = task.get('dependencies', [])
            dep_text = f"{len(dependencies)} dependencies" if dependencies else "No dependencies"
            
            hover_text = (
                f"<b>{task_name}</b><br>"
                f"Priority: {priority.title()}<br>"
                f"Duration: {duration}<br>"
                f"Vendor: {vendor_name}<br>"
                f"Dependencies: {dep_text}<br>"
                f"Start: {start.strftime('%Y-%m-%d')}<br>"
                f"End: {end.strftime('%Y-%m-%d')}"
            )
            
            chart_data.append({
                'Task': task_name,
                'Start': start,
                'Finish': end,
                'Resource': priority.title(),
                'Color': color,
                'HoverText': hover_text,
                'TaskID': task_id,
                'Priority': priority,
                'HasConflict': task.get('has_conflicts', False)
            })
        
        return chart_data
    
    def _create_gantt_figure(self, chart_data: List[Dict[str, Any]], 
                            tasks: List[Dict[str, Any]], 
                            timeline_data: Dict[str, Any]) -> go.Figure:
        """
        Create Plotly Gantt chart figure.
        
        Args:
            chart_data: Prepared chart data
            tasks: Original task list
            timeline_data: Full timeline data
            
        Returns:
            Plotly Figure object
        """
        # Create base Gantt chart
        df = pd.DataFrame(chart_data)
        
        # Create figure
        fig = go.Figure()
        
        # Add bars for each task
        for idx, row in df.iterrows():
            # Determine bar styling
            line_width = 3 if row['HasConflict'] else 0
            line_color = '#FF0000' if row['HasConflict'] else row['Color']
            
            fig.add_trace(go.Bar(
                name=row['Resource'],
                x=[row['Finish'] - row['Start']],
                y=[row['Task']],
                base=row['Start'],
                orientation='h',
                marker=dict(
                    color=row['Color'],
                    line=dict(
                        color=line_color,
                        width=line_width
                    )
                ),
                hovertext=row['HoverText'],
                hoverinfo='text',
                showlegend=False
            ))
        
        # Add dependency lines if enabled
        if st.session_state.timeline_show_dependencies:
            self._add_dependency_lines(fig, tasks, chart_data)
        
        # Add conflict indicators if enabled
        if st.session_state.timeline_show_conflicts:
            self._add_conflict_indicators(fig, timeline_data.get('conflicts', []), chart_data)
        
        # Update layout
        fig.update_layout(
            title={
                'text': 'Event Task Timeline',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 20, 'color': '#333333'}
            },
            xaxis=dict(
                title='Timeline',
                type='date',
                tickformat='%Y-%m-%d',
                gridcolor='#E0E0E0',
                showgrid=True
            ),
            yaxis=dict(
                title='Tasks',
                autorange='reversed',
                gridcolor='#E0E0E0',
                showgrid=True
            ),
            plot_bgcolor='white',
            paper_bgcolor='white',
            height=max(400, len(chart_data) * 40),  # Dynamic height based on task count
            margin=dict(l=200, r=50, t=80, b=80),
            hovermode='closest',
            dragmode='pan',
            # Enable zoom and pan
            xaxis_rangeslider_visible=True,
            xaxis_rangeslider_thickness=0.05
        )
        
        # Add mobile responsiveness
        fig.update_layout(
            autosize=True,
            font=dict(size=10)
        )
        
        return fig
    
    def _add_dependency_lines(self, fig: go.Figure, tasks: List[Dict[str, Any]], 
                             chart_data: List[Dict[str, Any]]):
        """
        Add dependency lines between tasks.
        
        Args:
            fig: Plotly figure
            tasks: List of tasks
            chart_data: Chart data with task positions
        """
        # Create task ID to position mapping
        task_positions = {item['TaskID']: idx for idx, item in enumerate(chart_data)}
        task_names = {item['TaskID']: item['Task'] for item in chart_data}
        
        # Add lines for dependencies
        for task in tasks:
            task_id = task.get('id', task.get('task_id', ''))
            dependencies = task.get('dependencies', [])
            
            if not dependencies or task_id not in task_positions:
                continue
            
            task_y = task_positions[task_id]
            task_start = None
            
            # Find task start date
            for item in chart_data:
                if item['TaskID'] == task_id:
                    task_start = item['Start']
                    break
            
            if not task_start:
                continue
            
            # Draw line from each dependency
            for dep_id in dependencies:
                if dep_id not in task_positions:
                    continue
                
                dep_y = task_positions[dep_id]
                dep_end = None
                
                # Find dependency end date
                for item in chart_data:
                    if item['TaskID'] == dep_id:
                        dep_end = item['Finish']
                        break
                
                if not dep_end:
                    continue
                
                # Add arrow line
                fig.add_trace(go.Scatter(
                    x=[dep_end, task_start],
                    y=[dep_y, task_y],
                    mode='lines+markers',
                    line=dict(color='#666666', width=1, dash='dot'),
                    marker=dict(size=6, symbol='arrow', angleref='previous'),
                    showlegend=False,
                    hoverinfo='skip'
                ))
    
    def _add_conflict_indicators(self, fig: go.Figure, conflicts: List[Dict[str, Any]], 
                                 chart_data: List[Dict[str, Any]]):
        """
        Add visual indicators for conflicts.
        
        Args:
            fig: Plotly figure
            conflicts: List of conflicts
            chart_data: Chart data with task positions
        """
        # Create task ID to position mapping
        task_positions = {item['TaskID']: idx for idx, item in enumerate(chart_data)}
        
        # Add warning icons for conflicting tasks
        for conflict in conflicts:
            affected_tasks = conflict.get('affected_tasks', [])
            
            for task_id in affected_tasks:
                if task_id not in task_positions:
                    continue
                
                # Find task data
                task_data = None
                for item in chart_data:
                    if item['TaskID'] == task_id:
                        task_data = item
                        break
                
                if not task_data:
                    continue
                
                # Add warning marker at task start
                fig.add_trace(go.Scatter(
                    x=[task_data['Start']],
                    y=[task_positions[task_id]],
                    mode='markers+text',
                    marker=dict(
                        size=15,
                        color='#FF0000',
                        symbol='x',
                        line=dict(color='#FFFFFF', width=2)
                    ),
                    text='⚠️',
                    textposition='middle center',
                    showlegend=False,
                    hovertext=f"Conflict: {conflict.get('description', 'Unknown conflict')}",
                    hoverinfo='text'
                ))
    
    def _render_legend(self):
        """Render legend for priority colors."""
        st.markdown("### 🎨 Priority Legend")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("🔴 **Critical**")
        
        with col2:
            st.markdown("🟠 **High**")
        
        with col3:
            st.markdown("🟡 **Medium**")
        
        with col4:
            st.markdown("🟢 **Low**")
        
        st.caption("Tasks with red borders indicate conflicts. Dotted lines show dependencies.")
    
    def _render_conflicts_summary(self, conflicts: List[Dict[str, Any]], 
                                  filtered_tasks: List[Dict[str, Any]]):
        """
        Render summary of conflicts affecting visible tasks.
        
        Args:
            conflicts: List of all conflicts
            filtered_tasks: List of currently visible tasks
        """
        # Filter conflicts to only those affecting visible tasks
        visible_task_ids = {t.get('id', t.get('task_id', '')) for t in filtered_tasks}
        
        relevant_conflicts = [
            c for c in conflicts
            if any(task_id in visible_task_ids for task_id in c.get('affected_tasks', []))
        ]
        
        if not relevant_conflicts:
            st.success("✅ No conflicts detected in visible tasks")
            return
        
        st.subheader("⚠️ Conflicts Summary")
        st.warning(f"**{len(relevant_conflicts)} conflicts detected** in the visible timeline")
        
        with st.expander("View Conflict Details", expanded=False):
            for idx, conflict in enumerate(relevant_conflicts, 1):
                conflict_type = conflict.get('type', 'Unknown')
                severity = conflict.get('severity', 'Medium')
                description = conflict.get('description', 'No description')
                affected_tasks = conflict.get('affected_tasks', [])
                
                st.markdown(f"**{idx}. {conflict_type}** ({severity} severity)")
                st.markdown(f"   {description}")
                st.markdown(f"   Affected tasks: {len(affected_tasks)}")
                st.divider()
            
            if st.button("🔧 Go to Conflict Resolution", key="goto_conflicts"):
                st.session_state.current_page = 'conflicts'
                st.rerun()


def render_timeline_view_page():
    """Main entry point for timeline view page."""
    page = TimelineViewPage()
    page.render()


# For standalone execution
if __name__ == "__main__":
    st.set_page_config(
        page_title="Timeline View - Event Planning Agent",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    render_timeline_view_page()
