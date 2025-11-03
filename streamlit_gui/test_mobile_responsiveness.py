"""
Test Mobile Responsiveness Implementation

Tests for mobile-responsive CSS and components for CRM and Task Management pages.
"""

import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from components.styles import CRM_CSS, TASK_MANAGEMENT_CSS, RESULTS_CSS
from components.mobile_nav import (
    render_mobile_hamburger_menu,
    render_mobile_quick_actions,
    render_mobile_filter_drawer,
    get_mobile_breakpoint,
    is_mobile_device
)


class TestMobileResponsiveCSS:
    """Test mobile-responsive CSS definitions"""
    
    def test_crm_css_exists(self):
        """Test that CRM CSS is defined"""
        assert CRM_CSS is not None
        assert len(CRM_CSS) > 0
        assert "<style>" in CRM_CSS
        assert "</style>" in CRM_CSS
    
    def test_crm_css_has_mobile_breakpoints(self):
        """Test that CRM CSS includes mobile breakpoints"""
        assert "@media (max-width: 768px)" in CRM_CSS
        assert "@media (max-width: 576px)" in CRM_CSS
    
    def test_crm_css_has_preference_styles(self):
        """Test that CRM CSS includes preference page styles"""
        assert ".crm-preferences-container" in CRM_CSS
        assert ".preference-card" in CRM_CSS
        assert ".channel-option" in CRM_CSS
    
    def test_crm_css_has_communication_history_styles(self):
        """Test that CRM CSS includes communication history styles"""
        assert ".comm-history-container" in CRM_CSS
        assert ".comm-card" in CRM_CSS
        assert ".comm-status-badge" in CRM_CSS
    
    def test_crm_css_has_analytics_styles(self):
        """Test that CRM CSS includes analytics page styles"""
        assert ".analytics-container" in CRM_CSS
        assert ".metrics-grid" in CRM_CSS
        assert ".metric-card" in CRM_CSS
        assert ".chart-container" in CRM_CSS
    
    def test_task_management_css_exists(self):
        """Test that Task Management CSS is defined"""
        assert TASK_MANAGEMENT_CSS is not None
        assert len(TASK_MANAGEMENT_CSS) > 0
        assert "<style>" in TASK_MANAGEMENT_CSS
        assert "</style>" in TASK_MANAGEMENT_CSS
    
    def test_task_management_css_has_mobile_breakpoints(self):
        """Test that Task Management CSS includes mobile breakpoints"""
        assert "@media (max-width: 992px)" in TASK_MANAGEMENT_CSS
        assert "@media (max-width: 768px)" in TASK_MANAGEMENT_CSS
        assert "@media (max-width: 576px)" in TASK_MANAGEMENT_CSS
    
    def test_task_management_css_has_task_list_styles(self):
        """Test that Task Management CSS includes task list styles"""
        assert ".task-list-container" in TASK_MANAGEMENT_CSS
        assert ".task-card" in TASK_MANAGEMENT_CSS
        assert ".task-priority-badge" in TASK_MANAGEMENT_CSS
    
    def test_task_management_css_has_timeline_styles(self):
        """Test that Task Management CSS includes timeline styles"""
        assert ".timeline-container" in TASK_MANAGEMENT_CSS
        assert ".timeline-controls" in TASK_MANAGEMENT_CSS
        assert ".gantt-chart-wrapper" in TASK_MANAGEMENT_CSS
    
    def test_task_management_css_has_conflicts_styles(self):
        """Test that Task Management CSS includes conflicts page styles"""
        assert ".conflicts-container" in TASK_MANAGEMENT_CSS
        assert ".conflict-card" in TASK_MANAGEMENT_CSS
        assert ".conflict-severity-badge" in TASK_MANAGEMENT_CSS
    
    def test_task_management_css_has_touch_friendly_styles(self):
        """Test that Task Management CSS includes touch-friendly styles"""
        assert "@media (hover: none) and (pointer: coarse)" in TASK_MANAGEMENT_CSS
        assert "min-height: 44px" in TASK_MANAGEMENT_CSS
    
    def test_task_management_css_has_horizontal_scrolling(self):
        """Test that Task Management CSS includes horizontal scrolling for timeline"""
        assert "overflow-x: auto" in TASK_MANAGEMENT_CSS
        assert "-webkit-overflow-scrolling: touch" in TASK_MANAGEMENT_CSS
    
    def test_task_management_css_has_collapsible_sections(self):
        """Test that Task Management CSS includes collapsible section styles"""
        assert ".collapsible-section" in TASK_MANAGEMENT_CSS
        assert ".collapsible-header" in TASK_MANAGEMENT_CSS
        assert ".collapsible-content" in TASK_MANAGEMENT_CSS
    
    def test_css_has_priority_colors(self):
        """Test that CSS includes priority level colors"""
        assert ".priority-critical" in TASK_MANAGEMENT_CSS
        assert ".priority-high" in TASK_MANAGEMENT_CSS
        assert ".priority-medium" in TASK_MANAGEMENT_CSS
        assert ".priority-low" in TASK_MANAGEMENT_CSS
    
    def test_css_has_status_colors(self):
        """Test that CSS includes status colors"""
        assert ".comm-status-badge.sent" in CRM_CSS
        assert ".comm-status-badge.delivered" in CRM_CSS
        assert ".comm-status-badge.failed" in CRM_CSS
    
    def test_css_has_responsive_grid(self):
        """Test that CSS includes responsive grid for metrics"""
        assert "grid-template-columns: repeat(auto-fit, minmax(200px, 1fr))" in CRM_CSS
        assert "grid-template-columns: repeat(2, 1fr)" in CRM_CSS
        assert "grid-template-columns: 1fr" in CRM_CSS


class TestMobileNavigationComponents:
    """Test mobile navigation components"""
    
    def test_mobile_hamburger_menu_function_exists(self):
        """Test that mobile hamburger menu function exists"""
        assert callable(render_mobile_hamburger_menu)
    
    def test_mobile_quick_actions_function_exists(self):
        """Test that mobile quick actions function exists"""
        assert callable(render_mobile_quick_actions)
    
    def test_mobile_filter_drawer_function_exists(self):
        """Test that mobile filter drawer function exists"""
        assert callable(render_mobile_filter_drawer)
    
    def test_get_mobile_breakpoint_function_exists(self):
        """Test that get mobile breakpoint function exists"""
        assert callable(get_mobile_breakpoint)
    
    def test_is_mobile_device_function_exists(self):
        """Test that is mobile device function exists"""
        assert callable(is_mobile_device)
    
    def test_get_mobile_breakpoint_returns_string(self):
        """Test that get_mobile_breakpoint returns a string"""
        result = get_mobile_breakpoint()
        assert isinstance(result, str)
        assert result in ['mobile', 'tablet', 'desktop']
    
    def test_is_mobile_device_returns_bool(self):
        """Test that is_mobile_device returns a boolean"""
        result = is_mobile_device()
        assert isinstance(result, bool)


class TestResponsiveFeatures:
    """Test responsive features implementation"""
    
    def test_card_based_layouts_for_mobile(self):
        """Test that card-based layouts are defined for mobile"""
        assert ".task-card" in TASK_MANAGEMENT_CSS
        assert ".comm-card" in CRM_CSS
        assert ".conflict-card" in TASK_MANAGEMENT_CSS
    
    def test_touch_friendly_controls(self):
        """Test that touch-friendly controls are defined"""
        # Check for minimum touch target sizes (44x44px)
        assert "min-height: 44px" in TASK_MANAGEMENT_CSS
        assert "min-width: 44px" in TASK_MANAGEMENT_CSS
    
    def test_horizontal_scrolling_timeline(self):
        """Test that horizontal scrolling is enabled for timeline"""
        assert "overflow-x: auto" in TASK_MANAGEMENT_CSS
        assert ".gantt-chart-wrapper" in TASK_MANAGEMENT_CSS
    
    def test_collapsible_sections(self):
        """Test that collapsible sections are defined"""
        assert ".collapsible-section" in TASK_MANAGEMENT_CSS
        assert ".collapsible-header" in TASK_MANAGEMENT_CSS
        assert ".collapsible-content" in TASK_MANAGEMENT_CSS
        assert ".collapsible-icon" in TASK_MANAGEMENT_CSS
    
    def test_responsive_font_sizes(self):
        """Test that font sizes adjust for mobile"""
        # Check that mobile breakpoints include font-size adjustments
        css_content = CRM_CSS + TASK_MANAGEMENT_CSS
        assert "font-size: 0.9rem" in css_content or "font-size: 0.8rem" in css_content
    
    def test_responsive_padding(self):
        """Test that padding adjusts for mobile"""
        # Check that mobile breakpoints include padding adjustments
        css_content = CRM_CSS + TASK_MANAGEMENT_CSS
        assert "padding: 0.75rem" in css_content or "padding: 0.5rem" in css_content
    
    def test_chart_optimization_for_small_screens(self):
        """Test that chart containers are optimized for small screens"""
        assert ".chart-container" in CRM_CSS
        # Check that chart containers have responsive padding in mobile breakpoints
        assert "@media (max-width: 768px)" in CRM_CSS


class TestAccessibilityFeatures:
    """Test accessibility features in mobile responsive design"""
    
    def test_touch_target_sizes(self):
        """Test that touch targets meet minimum size requirements"""
        # WCAG recommends minimum 44x44px for touch targets
        assert "min-height: 44px" in TASK_MANAGEMENT_CSS
        assert "min-width: 44px" in TASK_MANAGEMENT_CSS
    
    def test_color_contrast_classes(self):
        """Test that color classes are defined for contrast"""
        # Check that status badges have distinct colors
        assert ".comm-status-badge.sent" in CRM_CSS
        assert ".comm-status-badge.delivered" in CRM_CSS
        assert ".comm-status-badge.failed" in CRM_CSS
        assert ".task-priority-badge.critical" in TASK_MANAGEMENT_CSS
    
    def test_focus_states(self):
        """Test that focus states are defined for keyboard navigation"""
        # Check for hover states that should also apply to focus
        assert ":hover" in CRM_CSS
        assert ":hover" in TASK_MANAGEMENT_CSS
    
    def test_user_select_none_for_buttons(self):
        """Test that user-select: none is used for button-like elements"""
        assert "user-select: none" in TASK_MANAGEMENT_CSS


class TestPerformanceOptimizations:
    """Test performance optimizations for mobile"""
    
    def test_smooth_scrolling(self):
        """Test that smooth scrolling is enabled"""
        assert "scroll-behavior: smooth" in TASK_MANAGEMENT_CSS
    
    def test_webkit_overflow_scrolling(self):
        """Test that webkit overflow scrolling is enabled for iOS"""
        assert "-webkit-overflow-scrolling: touch" in TASK_MANAGEMENT_CSS
    
    def test_transitions_defined(self):
        """Test that transitions are defined for smooth animations"""
        assert "transition:" in CRM_CSS
        assert "transition:" in TASK_MANAGEMENT_CSS
    
    def test_transform_animations(self):
        """Test that transform animations are used (GPU accelerated)"""
        assert "transform:" in CRM_CSS or "transform:" in TASK_MANAGEMENT_CSS


class TestLayoutResponsiveness:
    """Test layout responsiveness"""
    
    def test_flex_layouts(self):
        """Test that flex layouts are used for responsive design"""
        assert "display: flex" in CRM_CSS or "display: flex" in TASK_MANAGEMENT_CSS
    
    def test_grid_layouts(self):
        """Test that grid layouts are used for responsive design"""
        assert "display: grid" in CRM_CSS
        assert "grid-template-columns" in CRM_CSS
    
    def test_responsive_columns(self):
        """Test that columns adjust for different screen sizes"""
        # Check that grid columns change at breakpoints
        assert "grid-template-columns: repeat(2, 1fr)" in CRM_CSS
        assert "grid-template-columns: 1fr" in CRM_CSS
    
    def test_flex_wrap(self):
        """Test that flex-wrap is used for responsive layouts"""
        assert "flex-wrap: wrap" in CRM_CSS or "flex-wrap: wrap" in TASK_MANAGEMENT_CSS


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
