"""
Performance Dashboard Component

Displays performance metrics, cache statistics, and system health information.
"""

import streamlit as st
from typing import Dict, Any
import logging
from utils.caching import get_cache_stats, get_performance_metrics, clear_cache
from utils.helpers import init_session_state

logger = logging.getLogger(__name__)


class PerformanceDashboard:
    """Component for displaying performance metrics and cache statistics."""
    
    def __init__(self):
        """Initialize performance dashboard."""
        init_session_state('show_performance_dashboard', False)
    
    def render_toggle(self):
        """Render toggle button for performance dashboard."""
        if st.sidebar.button("📊 Performance", key="toggle_performance_dashboard"):
            st.session_state.show_performance_dashboard = not st.session_state.show_performance_dashboard
            st.rerun()
    
    def render(self):
        """Render full performance dashboard."""
        if not st.session_state.get('show_performance_dashboard', False):
            return
        
        with st.sidebar.expander("📊 Performance Metrics", expanded=True):
            # Cache statistics
            self._render_cache_stats()
            
            st.divider()
            
            # Performance metrics
            self._render_performance_metrics()
            
            st.divider()
            
            # Actions
            self._render_actions()
    
    def _render_cache_stats(self):
        """Render cache statistics."""
        st.markdown("**🗄️ Cache Statistics**")
        
        try:
            stats = get_cache_stats()
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Cache Size", f"{stats['size']}/{stats['max_size']}")
                st.metric("Hits", stats['hits'])
            
            with col2:
                st.metric("Hit Rate", f"{stats['hit_rate']:.1f}%")
                st.metric("Misses", stats['misses'])
            
            # Visual hit rate indicator
            hit_rate = stats['hit_rate']
            if hit_rate >= 80:
                st.success(f"✅ Excellent cache performance ({hit_rate:.1f}%)")
            elif hit_rate >= 60:
                st.info(f"ℹ️ Good cache performance ({hit_rate:.1f}%)")
            elif hit_rate >= 40:
                st.warning(f"⚠️ Moderate cache performance ({hit_rate:.1f}%)")
            else:
                st.error(f"❌ Poor cache performance ({hit_rate:.1f}%)")
        
        except Exception as e:
            logger.error(f"Error rendering cache stats: {e}")
            st.error("Unable to load cache statistics")
    
    def _render_performance_metrics(self):
        """Render performance metrics."""
        st.markdown("**⚡ Performance Metrics**")
        
        try:
            metrics = get_performance_metrics()
            
            if not metrics:
                st.info("No performance data available yet")
                return
            
            # Show top 5 slowest operations
            sorted_ops = sorted(
                metrics.items(),
                key=lambda x: x[1].get('avg_time', 0),
                reverse=True
            )[:5]
            
            for op_name, op_metrics in sorted_ops:
                avg_time = op_metrics.get('avg_time', 0)
                count = op_metrics.get('count', 0)
                
                # Color code based on speed
                if avg_time < 0.1:
                    color = "green"
                    icon = "🟢"
                elif avg_time < 0.5:
                    color = "blue"
                    icon = "🔵"
                elif avg_time < 1.0:
                    color = "orange"
                    icon = "🟠"
                else:
                    color = "red"
                    icon = "🔴"
                
                st.markdown(
                    f"{icon} **{op_name}**: {avg_time:.3f}s avg ({count} calls)",
                    help=f"Min: {op_metrics.get('min_time', 0):.3f}s, "
                         f"Max: {op_metrics.get('max_time', 0):.3f}s"
                )
        
        except Exception as e:
            logger.error(f"Error rendering performance metrics: {e}")
            st.error("Unable to load performance metrics")
    
    def _render_actions(self):
        """Render action buttons."""
        st.markdown("**🔧 Actions**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🗑️ Clear Cache", key="clear_cache_button", use_container_width=True):
                try:
                    clear_cache()
                    st.success("Cache cleared!")
                    st.rerun()
                except Exception as e:
                    logger.error(f"Error clearing cache: {e}")
                    st.error("Failed to clear cache")
        
        with col2:
            if st.button("🔄 Refresh", key="refresh_perf_dashboard", use_container_width=True):
                st.rerun()


def render_performance_badge():
    """
    Render a small performance badge in the sidebar.
    
    Shows cache hit rate as a quick indicator.
    """
    try:
        stats = get_cache_stats()
        hit_rate = stats['hit_rate']
        
        # Determine color
        if hit_rate >= 80:
            color = "#00AA00"
            icon = "✅"
        elif hit_rate >= 60:
            color = "#0088FF"
            icon = "ℹ️"
        elif hit_rate >= 40:
            color = "#FFAA00"
            icon = "⚠️"
        else:
            color = "#FF4444"
            icon = "❌"
        
        st.sidebar.markdown(
            f"<div style='text-align: center; padding: 5px; "
            f"background-color: {color}; color: white; border-radius: 5px; "
            f"font-size: 12px; margin-bottom: 10px;'>"
            f"{icon} Cache: {hit_rate:.0f}% hit rate"
            f"</div>",
            unsafe_allow_html=True
        )
    
    except Exception as e:
        logger.debug(f"Could not render performance badge: {e}")


def log_slow_operation(operation: str, duration: float, threshold: float = 1.0):
    """
    Log slow operations for monitoring.
    
    Args:
        operation: Operation name
        duration: Duration in seconds
        threshold: Threshold for logging (default 1.0 second)
    """
    if duration > threshold:
        logger.warning(
            f"Slow operation detected: {operation} took {duration:.2f}s "
            f"(threshold: {threshold}s)"
        )


# Global dashboard instance
_dashboard = PerformanceDashboard()


def render_performance_dashboard():
    """Render the performance dashboard in sidebar."""
    _dashboard.render()


def render_performance_toggle():
    """Render the performance dashboard toggle button."""
    _dashboard.render_toggle()
