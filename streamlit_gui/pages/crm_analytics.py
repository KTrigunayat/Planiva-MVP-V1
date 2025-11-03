"""
CRM Analytics Page - Communication Analytics Dashboard

Displays comprehensive analytics for CRM communications including metrics,
channel performance, message type analysis, and timeline visualizations.
"""

import streamlit as st
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta, date
import logging
import csv
import io

from components.api_client import api_client, APIError
from components.crm_components import (
    metrics_card,
    channel_icon
)
from utils.helpers import (
    show_error, show_success, show_warning, show_info,
    init_session_state, format_date,
    calculate_task_progress,
    calculate_progress_by_priority,
    calculate_progress_by_vendor
)
from utils.export import get_exporter
from utils.caching import DataSampler

logger = logging.getLogger(__name__)


class CRMAnalyticsComponent:
    """Component for displaying CRM analytics dashboard."""
    
    def __init__(self):
        """Initialize CRM analytics component."""
        self.api_client = api_client
    
    def render(self, plan_id: Optional[str] = None, client_id: Optional[str] = None):
        """
        Render the CRM analytics dashboard.
        
        Args:
            plan_id: Optional plan ID filter
            client_id: Optional client ID filter
        """
        st.header("📊 Communication Analytics")
        st.markdown("Monitor communication effectiveness and engagement metrics.")
        
        # Initialize session state
        init_session_state('analytics_date_range', (
            date.today() - timedelta(days=30),
            date.today()
        ))
        init_session_state('analytics_data', None)
        init_session_state('analytics_last_refresh', None)
        
        # Date range selector
        self._render_date_range_selector()
        
        # Refresh and export controls
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        
        with col2:
            if st.button("🔄 Refresh", use_container_width=True, key="refresh_analytics"):
                st.session_state.analytics_data = None
                st.rerun()
        
        with col3:
            if st.button("📥 CSV", use_container_width=True, key="export_analytics_csv"):
                self._export_analytics_csv()
        
        with col4:
            if st.button("📄 PDF", use_container_width=True, key="export_analytics_pdf"):
                self._export_analytics_pdf()
        
        # Load analytics data
        analytics_data = self._load_analytics(plan_id, client_id)
        
        if analytics_data is None:
            show_error("Failed to load analytics data. Please check your connection.")
            if st.button("🔄 Retry", key="retry_load_analytics"):
                st.rerun()
            return
        
        # Display analytics sections
        self._render_key_metrics(analytics_data)
        st.markdown("---")
        
        # Add task progress metrics if plan_id is available
        if plan_id:
            self._render_task_progress_metrics(plan_id)
            st.markdown("---")
        
        self._render_channel_performance(analytics_data)
        st.markdown("---")
        
        self._render_message_type_performance(analytics_data)
        st.markdown("---")
        
        self._render_timeline_charts(analytics_data)
        st.markdown("---")
        
        self._render_channel_comparison(analytics_data)
    
    def _render_date_range_selector(self):
        """Render date range selector for filtering analytics."""
        with st.expander("📅 Date Range", expanded=False):
            col1, col2, col3 = st.columns([2, 2, 1])
            
            current_range = st.session_state.analytics_date_range
            
            with col1:
                start_date = st.date_input(
                    "From Date",
                    value=current_range[0],
                    key="analytics_start_date"
                )
            
            with col2:
                end_date = st.date_input(
                    "To Date",
                    value=current_range[1],
                    key="analytics_end_date"
                )
            
            with col3:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Apply", use_container_width=True, type="primary", key="apply_date_range"):
                    st.session_state.analytics_date_range = (start_date, end_date)
                    st.session_state.analytics_data = None
                    st.rerun()
            
            # Quick date range buttons
            st.markdown("**Quick Select:**")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("Last 7 Days", use_container_width=True, key="quick_7days"):
                    st.session_state.analytics_date_range = (
                        date.today() - timedelta(days=7),
                        date.today()
                    )
                    st.session_state.analytics_data = None
                    st.rerun()
            
            with col2:
                if st.button("Last 30 Days", use_container_width=True, key="quick_30days"):
                    st.session_state.analytics_date_range = (
                        date.today() - timedelta(days=30),
                        date.today()
                    )
                    st.session_state.analytics_data = None
                    st.rerun()
            
            with col3:
                if st.button("Last 90 Days", use_container_width=True, key="quick_90days"):
                    st.session_state.analytics_date_range = (
                        date.today() - timedelta(days=90),
                        date.today()
                    )
                    st.session_state.analytics_data = None
                    st.rerun()
            
            with col4:
                if st.button("All Time", use_container_width=True, key="quick_alltime"):
                    st.session_state.analytics_date_range = (
                        date.today() - timedelta(days=365),
                        date.today()
                    )
                    st.session_state.analytics_data = None
                    st.rerun()
    
    def _load_analytics(self, plan_id: Optional[str], client_id: Optional[str]) -> Optional[Dict[str, Any]]:
        """
        Load analytics data from API.
        
        Args:
            plan_id: Optional plan ID filter
            client_id: Optional client ID filter
            
        Returns:
            Analytics data or None on error
        """
        # Check if we should use cached data
        last_refresh = st.session_state.analytics_last_refresh
        if (st.session_state.analytics_data is not None and 
            last_refresh is not None and
            (datetime.now() - last_refresh).total_seconds() < 60):
            return st.session_state.analytics_data
        
        # Load from API
        try:
            with st.spinner("Loading analytics..."):
                date_range = st.session_state.analytics_date_range
                
                data = self.api_client.get_analytics(
                    plan_id=plan_id,
                    client_id=client_id,
                    start_date=date_range[0].isoformat() if date_range[0] else None,
                    end_date=date_range[1].isoformat() if date_range[1] else None
                )
                
                # Cache the data
                st.session_state.analytics_data = data
                st.session_state.analytics_last_refresh = datetime.now()
                
                return data
        except APIError as e:
            logger.error(f"Error loading analytics: {e.message}")
            if e.status_code == 404:
                # No analytics data found - return empty result
                return self._get_empty_analytics()
            return None
        except Exception as e:
            logger.error(f"Unexpected error loading analytics: {e}")
            return None
    
    def _get_empty_analytics(self) -> Dict[str, Any]:
        """Return empty analytics structure."""
        return {
            "metrics": {
                "total_sent": 0,
                "total_delivered": 0,
                "total_opened": 0,
                "total_clicked": 0,
                "total_failed": 0
            },
            "channel_performance": [],
            "message_type_performance": [],
            "timeline_data": [],
            "channel_comparison": []
        }
    
    def _render_task_progress_metrics(self, plan_id: str):
        """
        Render task progress metrics section.
        
        Args:
            plan_id: Plan identifier
        """
        st.subheader("✅ Task Progress Metrics")
        
        try:
            # Load task list data
            task_data = self.api_client.get_extended_task_list(plan_id)
            tasks = task_data.get('tasks', [])
            
            if not tasks:
                show_info("No tasks available for this plan")
                return
            
            # Calculate progress metrics
            progress = calculate_task_progress(tasks)
            priority_progress = calculate_progress_by_priority(tasks)
            vendor_progress = calculate_progress_by_vendor(tasks)
            
            # Display overall progress
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Total Tasks",
                    progress['total_tasks'],
                    help="Total number of tasks in the plan"
                )
            
            with col2:
                st.metric(
                    "Completed",
                    progress['completed_tasks'],
                    delta=f"{progress['completion_percentage']:.0f}%",
                    help="Number and percentage of completed tasks"
                )
            
            with col3:
                st.metric(
                    "In Progress",
                    progress['in_progress_tasks'],
                    help="Tasks currently being worked on"
                )
            
            with col4:
                st.metric(
                    "Overdue",
                    progress['overdue_tasks'],
                    delta="⚠️" if progress['overdue_tasks'] > 0 else None,
                    help="Tasks past their due date"
                )
            
            # Progress by priority (compact view)
            with st.expander("📊 Progress by Priority", expanded=False):
                for priority in ["Critical", "High", "Medium", "Low"]:
                    priority_data = priority_progress.get(priority, {})
                    if priority_data.get('total', 0) > 0:
                        completion_pct = priority_data['completion_percentage']
                        st.progress(
                            completion_pct / 100,
                            text=f"{priority}: {priority_data['completed']}/{priority_data['total']} ({completion_pct:.0f}%)"
                        )
            
            # Top vendors by completion
            with st.expander("👥 Top Vendors by Completion", expanded=False):
                # Sort vendors by completion percentage
                sorted_vendors = sorted(
                    vendor_progress.items(),
                    key=lambda x: x[1]['completion_percentage'],
                    reverse=True
                )[:5]  # Top 5
                
                for vendor_name, vendor_data in sorted_vendors:
                    completion_pct = vendor_data['completion_percentage']
                    st.progress(
                        completion_pct / 100,
                        text=f"{vendor_name}: {vendor_data['completed']}/{vendor_data['total']} ({completion_pct:.0f}%)"
                    )
        
        except APIError as e:
            if e.status_code == 404:
                show_info("Task list not yet generated for this plan")
            else:
                logger.error(f"Error loading task progress: {e.message}")
                show_warning("Unable to load task progress metrics")
        except Exception as e:
            logger.error(f"Unexpected error loading task progress: {e}")
            show_warning("Unable to load task progress metrics")
    
    def _render_key_metrics(self, analytics_data: Dict[str, Any]):
        """
        Render key metrics cards.
        
        Args:
            analytics_data: Analytics data
        """
        st.subheader("📈 Key Metrics")
        
        metrics = analytics_data.get("metrics", {})
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            total_sent = metrics.get("total_sent", 0)
            st.metric(
                label="📤 Total Sent",
                value=f"{total_sent:,}",
                help="Total number of communications sent"
            )
        
        with col2:
            total_delivered = metrics.get("total_delivered", 0)
            delivery_rate = (total_delivered / total_sent * 100) if total_sent > 0 else 0
            st.metric(
                label="✅ Delivered",
                value=f"{total_delivered:,}",
                delta=f"{delivery_rate:.1f}%",
                help="Successfully delivered communications"
            )
        
        with col3:
            total_opened = metrics.get("total_opened", 0)
            open_rate = (total_opened / total_delivered * 100) if total_delivered > 0 else 0
            st.metric(
                label="👁️ Opened",
                value=f"{total_opened:,}",
                delta=f"{open_rate:.1f}%",
                help="Communications opened by recipients (email only)"
            )
        
        with col4:
            total_clicked = metrics.get("total_clicked", 0)
            click_rate = (total_clicked / total_opened * 100) if total_opened > 0 else 0
            st.metric(
                label="🖱️ Clicked",
                value=f"{total_clicked:,}",
                delta=f"{click_rate:.1f}%",
                help="Communications with link clicks (email only)"
            )
        
        with col5:
            total_failed = metrics.get("total_failed", 0)
            failure_rate = (total_failed / total_sent * 100) if total_sent > 0 else 0
            st.metric(
                label="❌ Failed",
                value=f"{total_failed:,}",
                delta=f"-{failure_rate:.1f}%",
                delta_color="inverse",
                help="Failed communications"
            )
        
        # Additional calculated metrics
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                label="📊 Delivery Rate",
                value=f"{delivery_rate:.1f}%",
                help="Percentage of sent communications that were delivered"
            )
        
        with col2:
            st.metric(
                label="📊 Open Rate",
                value=f"{open_rate:.1f}%",
                help="Percentage of delivered communications that were opened"
            )
        
        with col3:
            st.metric(
                label="📊 Click-Through Rate",
                value=f"{click_rate:.1f}%",
                help="Percentage of opened communications that had clicks"
            )
    
    def _render_channel_performance(self, analytics_data: Dict[str, Any]):
        """
        Render channel performance section.
        
        Args:
            analytics_data: Analytics data
        """
        st.subheader("📡 Channel Performance")
        
        channel_performance = analytics_data.get("channel_performance", [])
        
        if not channel_performance:
            show_info("No channel performance data available")
            return
        
        # Create columns for each channel
        cols = st.columns(len(channel_performance))
        
        for idx, channel_data in enumerate(channel_performance):
            with cols[idx]:
                channel = channel_data.get("channel", "unknown")
                icon = channel_icon(channel)
                
                st.markdown(f"### {icon} {channel.upper()}")
                
                sent = channel_data.get("sent", 0)
                delivered = channel_data.get("delivered", 0)
                opened = channel_data.get("opened", 0)
                clicked = channel_data.get("clicked", 0)
                failed = channel_data.get("failed", 0)
                
                delivery_rate = (delivered / sent * 100) if sent > 0 else 0
                open_rate = (opened / delivered * 100) if delivered > 0 else 0
                click_rate = (clicked / opened * 100) if opened > 0 else 0
                
                st.metric("Sent", f"{sent:,}")
                st.metric("Delivery Rate", f"{delivery_rate:.1f}%")
                
                if channel == "email":
                    st.metric("Open Rate", f"{open_rate:.1f}%")
                    st.metric("CTR", f"{click_rate:.1f}%")
                
                if failed > 0:
                    st.metric("Failed", f"{failed:,}", delta_color="inverse")
    
    def _render_message_type_performance(self, analytics_data: Dict[str, Any]):
        """
        Render message type performance section.
        
        Args:
            analytics_data: Analytics data
        """
        st.subheader("📝 Message Type Performance")
        
        message_type_performance = analytics_data.get("message_type_performance", [])
        
        if not message_type_performance:
            show_info("No message type performance data available")
            return
        
        # Create a table for message type performance
        for msg_type_data in message_type_performance:
            with st.expander(f"📧 {msg_type_data.get('message_type', 'Unknown')}", expanded=False):
                col1, col2, col3, col4 = st.columns(4)
                
                sent = msg_type_data.get("sent", 0)
                delivered = msg_type_data.get("delivered", 0)
                opened = msg_type_data.get("opened", 0)
                clicked = msg_type_data.get("clicked", 0)
                
                with col1:
                    st.metric("Sent", f"{sent:,}")
                
                with col2:
                    delivery_rate = (delivered / sent * 100) if sent > 0 else 0
                    st.metric("Delivered", f"{delivered:,}", delta=f"{delivery_rate:.1f}%")
                
                with col3:
                    open_rate = (opened / delivered * 100) if delivered > 0 else 0
                    st.metric("Opened", f"{opened:,}", delta=f"{open_rate:.1f}%")
                
                with col4:
                    click_rate = (clicked / opened * 100) if opened > 0 else 0
                    st.metric("Clicked", f"{clicked:,}", delta=f"{click_rate:.1f}%")
    
    def _render_timeline_charts(self, analytics_data: Dict[str, Any]):
        """
        Render timeline charts using Plotly.
        
        Args:
            analytics_data: Analytics data
        """
        st.subheader("📈 Communication Timeline")
        
        timeline_data = analytics_data.get("timeline_data", [])
        
        if not timeline_data:
            show_info("No timeline data available")
            return
        
        try:
            import plotly.graph_objects as go
            from plotly.subplots import make_subplots
            
            # Sample data for large datasets to improve performance
            sampled_timeline = DataSampler.sample_for_chart(timeline_data, max_points=500)
            
            # Extract data for charts
            dates = [item.get("date") for item in sampled_timeline]
            sent_counts = [item.get("sent", 0) for item in sampled_timeline]
            delivered_counts = [item.get("delivered", 0) for item in sampled_timeline]
            opened_counts = [item.get("opened", 0) for item in sampled_timeline]
            clicked_counts = [item.get("clicked", 0) for item in sampled_timeline]
            
            # Show sampling info if data was sampled
            if len(sampled_timeline) < len(timeline_data):
                st.caption(f"ℹ️ Showing {len(sampled_timeline)} sampled points from {len(timeline_data)} total data points for better performance")
            
            # Create subplots
            fig = make_subplots(
                rows=2, cols=1,
                subplot_titles=("Communication Volume", "Engagement Metrics"),
                vertical_spacing=0.15
            )
            
            # Volume chart
            fig.add_trace(
                go.Scatter(
                    x=dates, y=sent_counts,
                    name="Sent",
                    mode='lines+markers',
                    line=dict(color='#1f77b4', width=2)
                ),
                row=1, col=1
            )
            
            fig.add_trace(
                go.Scatter(
                    x=dates, y=delivered_counts,
                    name="Delivered",
                    mode='lines+markers',
                    line=dict(color='#2ca02c', width=2)
                ),
                row=1, col=1
            )
            
            # Engagement chart
            fig.add_trace(
                go.Scatter(
                    x=dates, y=opened_counts,
                    name="Opened",
                    mode='lines+markers',
                    line=dict(color='#ff7f0e', width=2)
                ),
                row=2, col=1
            )
            
            fig.add_trace(
                go.Scatter(
                    x=dates, y=clicked_counts,
                    name="Clicked",
                    mode='lines+markers',
                    line=dict(color='#d62728', width=2)
                ),
                row=2, col=1
            )
            
            # Update layout
            fig.update_layout(
                height=600,
                showlegend=True,
                hovermode='x unified'
            )
            
            fig.update_xaxes(title_text="Date", row=2, col=1)
            fig.update_yaxes(title_text="Count", row=1, col=1)
            fig.update_yaxes(title_text="Count", row=2, col=1)
            
            st.plotly_chart(fig, use_container_width=True)
            
        except ImportError:
            show_warning("Plotly is not installed. Install it with: pip install plotly")
            self._render_timeline_fallback(timeline_data)
        except Exception as e:
            logger.error(f"Error rendering timeline chart: {e}")
            show_error(f"Failed to render timeline chart: {str(e)}")
            self._render_timeline_fallback(timeline_data)
    
    def _render_timeline_fallback(self, timeline_data: List[Dict[str, Any]]):
        """
        Render timeline data as a table (fallback when Plotly is not available).
        
        Args:
            timeline_data: Timeline data
        """
        st.markdown("**Timeline Data (Table View)**")
        
        # Create a simple table
        import pandas as pd
        
        df = pd.DataFrame(timeline_data)
        st.dataframe(df, use_container_width=True)
    
    def _render_channel_comparison(self, analytics_data: Dict[str, Any]):
        """
        Render channel comparison visualizations.
        
        Args:
            analytics_data: Analytics data
        """
        st.subheader("📊 Channel Comparison")
        
        channel_performance = analytics_data.get("channel_performance", [])
        
        if not channel_performance:
            show_info("No channel comparison data available")
            return
        
        try:
            import plotly.graph_objects as go
            from plotly.subplots import make_subplots
            
            # Extract data
            channels = [item.get("channel", "unknown") for item in channel_performance]
            sent = [item.get("sent", 0) for item in channel_performance]
            delivered = [item.get("delivered", 0) for item in channel_performance]
            opened = [item.get("opened", 0) for item in channel_performance]
            clicked = [item.get("clicked", 0) for item in channel_performance]
            
            # Create subplots
            fig = make_subplots(
                rows=1, cols=2,
                subplot_titles=("Volume by Channel", "Engagement by Channel"),
                specs=[[{"type": "bar"}, {"type": "pie"}]]
            )
            
            # Bar chart for volume
            fig.add_trace(
                go.Bar(
                    x=channels,
                    y=sent,
                    name="Sent",
                    marker_color='#1f77b4'
                ),
                row=1, col=1
            )
            
            fig.add_trace(
                go.Bar(
                    x=channels,
                    y=delivered,
                    name="Delivered",
                    marker_color='#2ca02c'
                ),
                row=1, col=1
            )
            
            # Pie chart for engagement
            total_engagement = [o + c for o, c in zip(opened, clicked)]
            fig.add_trace(
                go.Pie(
                    labels=channels,
                    values=total_engagement,
                    name="Engagement"
                ),
                row=1, col=2
            )
            
            # Update layout
            fig.update_layout(
                height=400,
                showlegend=True
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        except ImportError:
            show_warning("Plotly is not installed. Install it with: pip install plotly")
            self._render_channel_comparison_fallback(channel_performance)
        except Exception as e:
            logger.error(f"Error rendering channel comparison: {e}")
            show_error(f"Failed to render channel comparison: {str(e)}")
            self._render_channel_comparison_fallback(channel_performance)
    
    def _render_channel_comparison_fallback(self, channel_performance: List[Dict[str, Any]]):
        """
        Render channel comparison as a table (fallback).
        
        Args:
            channel_performance: Channel performance data
        """
        st.markdown("**Channel Comparison (Table View)**")
        
        import pandas as pd
        
        df = pd.DataFrame(channel_performance)
        st.dataframe(df, use_container_width=True)
    
    def _export_analytics_csv(self):
        """Export analytics data to CSV."""
        analytics_data = st.session_state.analytics_data
        
        if not analytics_data:
            show_warning("No analytics data to export")
            return
        
        try:
            with st.spinner("Preparing CSV export..."):
                exporter = get_exporter()
                csv_data = exporter.export_analytics_to_csv(analytics_data)
            
            # Create download button
            st.download_button(
                label="📥 Download Analytics CSV",
                data=csv_data,
                file_name=f"crm_analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                key="download_analytics_csv"
            )
            
            show_success("Analytics CSV ready for download. Click the button above.")
            
        except Exception as e:
            logger.error(f"Error exporting analytics to CSV: {e}")
            show_error(f"Failed to export CSV: {str(e)}")
    
    def _export_analytics_pdf(self):
        """Export analytics data to PDF."""
        analytics_data = st.session_state.analytics_data
        
        if not analytics_data:
            show_warning("No analytics data to export")
            return
        
        try:
            with st.spinner("Generating PDF report..."):
                exporter = get_exporter()
                pdf_data = exporter.export_analytics_to_pdf(
                    analytics_data,
                    title="Communication Analytics Report"
                )
            
            # Create download button
            st.download_button(
                label="📄 Download Analytics PDF",
                data=pdf_data,
                file_name=f"crm_analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/pdf",
                key="download_analytics_pdf"
            )
            
            show_success("Analytics PDF ready for download. Click the button above.")
            
        except ImportError:
            show_error(
                "PDF export requires ReportLab. "
                "Install it with: pip install reportlab"
            )
        except Exception as e:
            logger.error(f"Error exporting analytics to PDF: {e}")
            show_error(f"Failed to export PDF: {str(e)}")


def render_crm_analytics_page():
    """Main rendering function for CRM analytics page."""
    
    st.header("📊 Communication Analytics")
    st.markdown("Monitor communication effectiveness and engagement metrics.")
    
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
    with st.expander("🔑 Filter by Client/Plan", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            input_client_id = st.text_input(
                "Client ID (optional)",
                value=client_id,
                help="Filter analytics by client ID",
                key="client_id_input_analytics"
            )
        
        with col2:
            input_plan_id = st.text_input(
                "Plan ID (optional)",
                value=plan_id or "",
                help="Filter analytics by plan ID",
                key="plan_id_input_analytics"
            )
        
        if st.button("Apply ID Filters", key="apply_id_filters_analytics"):
            if input_client_id:
                st.session_state.client_id = input_client_id
                client_id = input_client_id
            if input_plan_id:
                st.session_state.current_plan_id = input_plan_id
                plan_id = input_plan_id
            st.session_state.analytics_data = None
            st.rerun()
    
    # Render the component
    component = CRMAnalyticsComponent()
    component.render(plan_id=plan_id, client_id=client_id)
    
    # Additional information
    st.markdown("---")
    
    with st.expander("ℹ️ About Analytics Metrics"):
        st.markdown("""
        **Understanding Analytics Metrics**
        
        - **Total Sent**: Total number of communications sent across all channels
        - **Delivered**: Communications successfully delivered to recipients
        - **Opened**: Email communications opened by recipients (email only)
        - **Clicked**: Email communications with link clicks (email only)
        - **Failed**: Communications that failed to deliver
        
        **Rates**
        
        - **Delivery Rate**: (Delivered / Sent) × 100%
        - **Open Rate**: (Opened / Delivered) × 100%
        - **Click-Through Rate (CTR)**: (Clicked / Opened) × 100%
        
        **Channel Performance**
        
        Compare effectiveness across Email, SMS, and WhatsApp channels.
        Each channel has different capabilities and metrics.
        
        **Message Type Performance**
        
        Analyze performance by message type (welcome, budget_summary, vendor_options, etc.)
        to identify which communications resonate best with clients.
        
        **Timeline Charts**
        
        Visualize communication volume and engagement trends over time
        to identify patterns and optimize sending schedules.
        """)


# For standalone execution
if __name__ == "__main__":
    st.set_page_config(
        page_title="Communication Analytics - Event Planning Agent",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    render_crm_analytics_page()
