"""
CRM Analytics Dashboard

Streamlit dashboard for visualizing CRM communication analytics.
Provides interactive charts and metrics for monitoring communication effectiveness.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging

from .analytics import get_analytics
from .export import get_exporter

logger = logging.getLogger(__name__)


def render_dashboard():
    """
    Render the CRM Analytics Dashboard.
    
    Main entry point for the Streamlit dashboard application.
    """
    st.set_page_config(
        page_title="CRM Analytics Dashboard",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("📊 CRM Communication Analytics Dashboard")
    st.markdown("---")
    
    # Sidebar for filters
    with st.sidebar:
        st.header("Filters")
        
        # Date range selector
        date_range = st.selectbox(
            "Date Range",
            ["Last 7 Days", "Last 30 Days", "Last 90 Days", "Custom Range"]
        )
        
        if date_range == "Custom Range":
            start_date = st.date_input("Start Date", datetime.now() - timedelta(days=30))
            end_date = st.date_input("End Date", datetime.now())
        else:
            days_map = {
                "Last 7 Days": 7,
                "Last 30 Days": 30,
                "Last 90 Days": 90
            }
            days = days_map.get(date_range, 30)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
        
        # Convert to datetime
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())
        
        # Export options
        st.markdown("---")
        st.header("Export")
        
        if st.button("Export to CSV"):
            export_to_csv(start_dt, end_dt)
        
        if st.button("Export to PDF"):
            export_to_pdf(start_dt, end_dt)
    
    # Load analytics data
    try:
        analytics = get_analytics()
        data = analytics.get_comprehensive_analytics(start_dt, end_dt)
        
        # Overview Panel
        render_overview_panel(data)
        
        st.markdown("---")
        
        # Channel Comparison
        col1, col2 = st.columns(2)
        
        with col1:
            render_channel_comparison(data)
        
        with col2:
            render_engagement_funnel(data)
        
        st.markdown("---")
        
        # Timeline Chart
        render_timeline_chart(start_dt, end_dt)
        
        st.markdown("---")
        
        # Preference Distribution
        render_preference_distribution(data)
        
    except Exception as e:
        st.error(f"Failed to load analytics data: {e}")
        logger.error(f"Dashboard error: {e}")


def render_overview_panel(data: Dict[str, Any]):
    """Render overview metrics panel"""
    st.header("📈 Overview")
    
    delivery_metrics = data.get('delivery_metrics', {})
    engagement_metrics = data.get('engagement_metrics', {})
    
    # Key metrics in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_sent = delivery_metrics.get('total_sent', 0)
        st.metric("Total Communications", f"{total_sent:,}")
    
    with col2:
        delivery_rate = delivery_metrics.get('delivery_rate', 0)
        st.metric("Delivery Rate", f"{delivery_rate}%")
    
    with col3:
        open_rate = engagement_metrics.get('open_rate', {}).get('open_rate', 0)
        st.metric("Open Rate", f"{open_rate}%")
    
    with col4:
        ctr = engagement_metrics.get('click_through_rate', {}).get('click_through_rate', 0)
        st.metric("Click-Through Rate", f"{ctr}%")
    
    # Additional metrics
    col5, col6, col7, col8 = st.columns(4)
    
    with col5:
        delivered = delivery_metrics.get('delivered_count', 0)
        st.metric("Delivered", f"{delivered:,}")
    
    with col6:
        failed = delivery_metrics.get('failed_count', 0)
        failure_rate = delivery_metrics.get('failure_rate', 0)
        st.metric("Failed", f"{failed:,}", delta=f"-{failure_rate}%", delta_color="inverse")
    
    with col7:
        opened = engagement_metrics.get('open_rate', {}).get('opened_count', 0)
        st.metric("Opened", f"{opened:,}")
    
    with col8:
        clicked = engagement_metrics.get('click_through_rate', {}).get('clicked_count', 0)
        st.metric("Clicked", f"{clicked:,}")


def render_channel_comparison(data: Dict[str, Any]):
    """Render channel performance comparison"""
    st.subheader("📱 Channel Performance")
    
    channel_performance = data.get('channel_performance', {})
    
    if not channel_performance:
        st.info("No channel performance data available")
        return
    
    # Prepare data for chart
    channels = []
    delivery_rates = []
    open_rates = []
    click_rates = []
    total_sent = []
    
    for channel, metrics in channel_performance.items():
        channels.append(channel.upper())
        delivery_rates.append(metrics.get('delivery_rate', 0))
        open_rates.append(metrics.get('open_rate', 0))
        click_rates.append(metrics.get('click_through_rate', 0))
        total_sent.append(metrics.get('total_sent', 0))
    
    # Create grouped bar chart
    fig = go.Figure(data=[
        go.Bar(name='Delivery Rate %', x=channels, y=delivery_rates, marker_color='#3498db'),
        go.Bar(name='Open Rate %', x=channels, y=open_rates, marker_color='#2ecc71'),
        go.Bar(name='Click Rate %', x=channels, y=click_rates, marker_color='#e74c3c')
    ])
    
    fig.update_layout(
        barmode='group',
        xaxis_title="Channel",
        yaxis_title="Rate (%)",
        height=400,
        showlegend=True
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Show detailed table
    with st.expander("View Detailed Metrics"):
        df = pd.DataFrame({
            'Channel': channels,
            'Total Sent': total_sent,
            'Delivery Rate %': delivery_rates,
            'Open Rate %': open_rates,
            'Click Rate %': click_rates
        })
        st.dataframe(df, use_container_width=True)


def render_engagement_funnel(data: Dict[str, Any]):
    """Render engagement funnel visualization"""
    st.subheader("🔄 Engagement Funnel")
    
    funnel_data = data.get('engagement_funnel', {})
    
    if not funnel_data or 'funnel_stages' not in funnel_data:
        st.info("No engagement funnel data available")
        return
    
    stages = funnel_data['funnel_stages']
    conversions = funnel_data.get('conversion_rates', {})
    
    # Prepare funnel data
    funnel_stages = ['Sent', 'Delivered', 'Opened', 'Clicked']
    funnel_values = [
        stages.get('sent', 0),
        stages.get('delivered', 0),
        stages.get('opened', 0),
        stages.get('clicked', 0)
    ]
    
    # Create funnel chart
    fig = go.Figure(go.Funnel(
        y=funnel_stages,
        x=funnel_values,
        textposition="inside",
        textinfo="value+percent initial",
        marker=dict(
            color=['#3498db', '#2ecc71', '#f39c12', '#e74c3c']
        )
    ))
    
    fig.update_layout(
        height=400,
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Show conversion rates
    with st.expander("View Conversion Rates"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Sent → Delivered", f"{conversions.get('sent_to_delivered', 0)}%")
            st.metric("Delivered → Opened", f"{conversions.get('delivered_to_opened', 0)}%")
        
        with col2:
            st.metric("Opened → Clicked", f"{conversions.get('opened_to_clicked', 0)}%")
            st.metric("Overall (Sent → Clicked)", f"{conversions.get('sent_to_clicked', 0)}%")


def render_timeline_chart(start_dt: datetime, end_dt: datetime):
    """Render communication volume timeline"""
    st.header("📅 Communication Timeline")
    
    try:
        analytics = get_analytics()
        
        # Determine granularity based on date range
        days_diff = (end_dt - start_dt).days
        if days_diff <= 7:
            granularity = 'hour'
        elif days_diff <= 90:
            granularity = 'day'
        else:
            granularity = 'week'
        
        timeline_data = analytics.get_timeline_data(start_dt, end_dt, granularity)
        
        if not timeline_data:
            st.info("No timeline data available")
            return
        
        # Convert to DataFrame
        df = pd.DataFrame(timeline_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Create line chart
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['total_sent'],
            mode='lines+markers',
            name='Total Sent',
            line=dict(color='#3498db', width=2)
        ))
        
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['delivered_count'],
            mode='lines+markers',
            name='Delivered',
            line=dict(color='#2ecc71', width=2)
        ))
        
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['opened_count'],
            mode='lines+markers',
            name='Opened',
            line=dict(color='#f39c12', width=2)
        ))
        
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['clicked_count'],
            mode='lines+markers',
            name='Clicked',
            line=dict(color='#e74c3c', width=2)
        ))
        
        fig.update_layout(
            xaxis_title="Time",
            yaxis_title="Count",
            height=400,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Show data table
        with st.expander("View Timeline Data"):
            st.dataframe(df, use_container_width=True)
        
    except Exception as e:
        st.error(f"Failed to load timeline data: {e}")
        logger.error(f"Timeline chart error: {e}")


def render_preference_distribution(data: Dict[str, Any]):
    """Render client preference distribution"""
    st.header("⚙️ Client Preferences")
    
    preference_data = data.get('preference_distribution', {})
    
    if not preference_data:
        st.info("No preference data available")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Channel Preferences")
        
        channel_prefs = preference_data.get('channel_preferences', {})
        
        if channel_prefs:
            channels = list(channel_prefs.keys())
            percentages = [prefs['percentage'] for prefs in channel_prefs.values()]
            
            fig = px.pie(
                values=percentages,
                names=channels,
                title="Preferred Communication Channels",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No channel preference data")
    
    with col2:
        st.subheader("Opt-Out Statistics")
        
        optout_stats = preference_data.get('opt_out_statistics', {})
        
        if optout_stats:
            total_clients = optout_stats.get('total_clients', 0)
            
            st.metric("Total Clients", f"{total_clients:,}")
            
            col_a, col_b, col_c = st.columns(3)
            
            with col_a:
                email_optout = optout_stats.get('email_optout_rate', 0)
                st.metric("Email Opt-Out", f"{email_optout}%")
            
            with col_b:
                sms_optout = optout_stats.get('sms_optout_rate', 0)
                st.metric("SMS Opt-Out", f"{sms_optout}%")
            
            with col_c:
                whatsapp_optout = optout_stats.get('whatsapp_optout_rate', 0)
                st.metric("WhatsApp Opt-Out", f"{whatsapp_optout}%")
        else:
            st.info("No opt-out statistics available")


def export_to_csv(start_dt: datetime, end_dt: datetime):
    """Export analytics to CSV"""
    try:
        analytics = get_analytics()
        data = analytics.get_comprehensive_analytics(start_dt, end_dt)
        
        exporter = get_exporter()
        csv_content = exporter.export_to_csv(data, 'comprehensive')
        
        # Provide download
        st.download_button(
            label="Download CSV",
            data=csv_content,
            file_name=f"crm_analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
        
        st.success("CSV export ready for download!")
        
    except Exception as e:
        st.error(f"Failed to export CSV: {e}")
        logger.error(f"CSV export error: {e}")


def export_to_pdf(start_dt: datetime, end_dt: datetime):
    """Export analytics to PDF"""
    try:
        analytics = get_analytics()
        data = analytics.get_comprehensive_analytics(start_dt, end_dt)
        
        exporter = get_exporter()
        pdf_content = exporter.export_to_pdf(data)
        
        # Provide download
        st.download_button(
            label="Download PDF",
            data=pdf_content,
            file_name=f"crm_analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mime="application/pdf"
        )
        
        st.success("PDF export ready for download!")
        
    except Exception as e:
        st.error(f"Failed to export PDF: {e}")
        logger.error(f"PDF export error: {e}")


if __name__ == "__main__":
    render_dashboard()
