"""
Mobile Navigation Component - Hamburger Menu for Sub-Navigation

Provides mobile-friendly navigation with collapsible menus for
CRM and Task Management features.
"""

import streamlit as st
from typing import List, Dict, Optional


def render_mobile_hamburger_menu():
    """
    Render a mobile-friendly hamburger menu for navigation.
    
    This provides collapsible sub-menus for Tasks and Communications
    on mobile devices.
    """
    
    # Mobile navigation CSS
    st.markdown("""
    <style>
        /* Hamburger menu styles */
        .mobile-nav-container {
            display: none;
        }
        
        @media (max-width: 768px) {
            .mobile-nav-container {
                display: block;
                background-color: #f8f9fa;
                border-radius: 8px;
                padding: 0.5rem;
                margin-bottom: 1rem;
            }
        }
        
        .mobile-nav-toggle {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0.75rem 1rem;
            background-color: #007bff;
            color: white;
            border-radius: 6px;
            cursor: pointer;
            font-weight: bold;
            user-select: none;
        }
        
        .mobile-nav-toggle:active {
            background-color: #0056b3;
        }
        
        .mobile-nav-menu {
            background-color: white;
            border-radius: 6px;
            margin-top: 0.5rem;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        
        .mobile-nav-section {
            border-bottom: 1px solid #e0e0e0;
        }
        
        .mobile-nav-section:last-child {
            border-bottom: none;
        }
        
        .mobile-nav-section-header {
            padding: 0.75rem 1rem;
            background-color: #f8f9fa;
            font-weight: bold;
            color: #495057;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            user-select: none;
        }
        
        .mobile-nav-section-header:active {
            background-color: #e9ecef;
        }
        
        .mobile-nav-item {
            padding: 0.75rem 1.5rem;
            color: #495057;
            cursor: pointer;
            transition: background-color 0.2s ease;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            min-height: 44px;
        }
        
        .mobile-nav-item:active {
            background-color: #e7f3ff;
        }
        
        .mobile-nav-item.active {
            background-color: #e7f3ff;
            color: #007bff;
            font-weight: bold;
        }
        
        .mobile-nav-icon {
            font-size: 1.2rem;
        }
        
        .mobile-nav-chevron {
            transition: transform 0.2s ease;
        }
        
        .mobile-nav-chevron.expanded {
            transform: rotate(180deg);
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize session state for menu visibility
    if 'mobile_menu_open' not in st.session_state:
        st.session_state.mobile_menu_open = False
    if 'mobile_tasks_expanded' not in st.session_state:
        st.session_state.mobile_tasks_expanded = False
    if 'mobile_comms_expanded' not in st.session_state:
        st.session_state.mobile_comms_expanded = False
    
    # Mobile navigation container
    with st.container():
        st.markdown('<div class="mobile-nav-container">', unsafe_allow_html=True)
        
        # Hamburger toggle button
        col1, col2 = st.columns([3, 1])
        with col1:
            if st.button(
                "☰ Navigation Menu",
                key="mobile_nav_toggle",
                use_container_width=True,
                type="primary"
            ):
                st.session_state.mobile_menu_open = not st.session_state.mobile_menu_open
        
        # Menu content (shown when open)
        if st.session_state.mobile_menu_open:
            st.markdown('<div class="mobile-nav-menu">', unsafe_allow_html=True)
            
            # Tasks section
            _render_mobile_nav_section(
                "📋 Tasks",
                "mobile_tasks_expanded",
                [
                    {"label": "Task List", "page": "task_list", "icon": "📝"},
                    {"label": "Timeline", "page": "timeline_view", "icon": "📅"},
                    {"label": "Conflicts", "page": "conflicts", "icon": "⚠️"},
                    {"label": "Vendors", "page": "vendors", "icon": "👥"}
                ]
            )
            
            # Communications section
            _render_mobile_nav_section(
                "💬 Communications",
                "mobile_comms_expanded",
                [
                    {"label": "Preferences", "page": "crm_preferences", "icon": "⚙️"},
                    {"label": "History", "page": "communication_history", "icon": "📬"},
                    {"label": "Analytics", "page": "crm_analytics", "icon": "📊"}
                ]
            )
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)


def _render_mobile_nav_section(
    title: str,
    state_key: str,
    items: List[Dict[str, str]]
):
    """
    Render a collapsible navigation section.
    
    Args:
        title: Section title
        state_key: Session state key for expansion
        items: List of navigation items with label, page, and icon
    """
    # Section header
    col1, col2 = st.columns([4, 1])
    with col1:
        if st.button(
            title,
            key=f"nav_section_{state_key}",
            use_container_width=True
        ):
            st.session_state[state_key] = not st.session_state[state_key]
    
    # Section items (shown when expanded)
    if st.session_state[state_key]:
        for item in items:
            icon = item.get("icon", "")
            label = item.get("label", "")
            page = item.get("page", "")
            
            # Check if this is the current page
            current_page = st.session_state.get('current_page', '')
            is_active = current_page == page
            
            button_type = "primary" if is_active else "secondary"
            
            if st.button(
                f"{icon} {label}",
                key=f"nav_item_{page}",
                use_container_width=True,
                type=button_type
            ):
                # Navigate to the page
                st.session_state.current_page = page
                st.session_state.mobile_menu_open = False
                st.switch_page(f"pages/{page}.py")


def render_mobile_quick_actions():
    """
    Render quick action buttons for mobile devices.
    
    Provides easy access to common actions like refresh, export, etc.
    """
    st.markdown("""
    <style>
        .mobile-quick-actions {
            display: none;
        }
        
        @media (max-width: 768px) {
            .mobile-quick-actions {
                display: flex;
                gap: 0.5rem;
                margin-bottom: 1rem;
                overflow-x: auto;
                padding: 0.5rem 0;
            }
        }
        
        .mobile-quick-action-btn {
            flex: 0 0 auto;
            min-width: 100px;
            padding: 0.75rem 1rem;
            background-color: #ffffff;
            border: 1px solid #dee2e6;
            border-radius: 6px;
            text-align: center;
            cursor: pointer;
            transition: all 0.2s ease;
            white-space: nowrap;
        }
        
        .mobile-quick-action-btn:active {
            background-color: #e7f3ff;
            border-color: #007bff;
        }
        
        .mobile-quick-action-icon {
            font-size: 1.5rem;
            display: block;
            margin-bottom: 0.25rem;
        }
        
        .mobile-quick-action-label {
            font-size: 0.8rem;
            color: #495057;
        }
    </style>
    """, unsafe_allow_html=True)


def render_mobile_filter_drawer():
    """
    Render a mobile-friendly filter drawer.
    
    Provides a collapsible drawer for filter controls on mobile devices.
    """
    st.markdown("""
    <style>
        .mobile-filter-drawer {
            display: none;
        }
        
        @media (max-width: 768px) {
            .mobile-filter-drawer {
                display: block;
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                margin-bottom: 1rem;
                overflow: hidden;
            }
        }
        
        .mobile-filter-header {
            padding: 0.75rem 1rem;
            background-color: #f8f9fa;
            font-weight: bold;
            color: #495057;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            user-select: none;
            min-height: 44px;
        }
        
        .mobile-filter-header:active {
            background-color: #e9ecef;
        }
        
        .mobile-filter-content {
            padding: 1rem;
        }
        
        .mobile-filter-actions {
            display: flex;
            gap: 0.5rem;
            margin-top: 1rem;
        }
        
        .mobile-filter-btn {
            flex: 1;
            padding: 0.75rem;
            border-radius: 6px;
            font-weight: bold;
            cursor: pointer;
            text-align: center;
            min-height: 44px;
        }
        
        .mobile-filter-btn.primary {
            background-color: #007bff;
            color: white;
        }
        
        .mobile-filter-btn.secondary {
            background-color: #6c757d;
            color: white;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    if 'mobile_filters_open' not in st.session_state:
        st.session_state.mobile_filters_open = False
    
    # Filter drawer toggle
    if st.button(
        "🔍 Filters",
        key="mobile_filter_toggle",
        use_container_width=True
    ):
        st.session_state.mobile_filters_open = not st.session_state.mobile_filters_open
    
    return st.session_state.mobile_filters_open


def render_mobile_card_layout(items: List[Dict], render_func):
    """
    Render items in a mobile-optimized card layout.
    
    Args:
        items: List of items to render
        render_func: Function to render each item
    """
    st.markdown("""
    <style>
        .mobile-card-container {
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }
        
        @media (max-width: 768px) {
            .mobile-card-container {
                gap: 0.75rem;
            }
        }
    </style>
    """, unsafe_allow_html=True)
    
    for item in items:
        with st.container():
            render_func(item)


def get_mobile_breakpoint() -> str:
    """
    Detect the current mobile breakpoint.
    
    Returns:
        Breakpoint name: 'mobile', 'tablet', or 'desktop'
    """
    # This is a placeholder - Streamlit doesn't have built-in viewport detection
    # In production, you might use JavaScript injection or user agent detection
    return 'desktop'


def is_mobile_device() -> bool:
    """
    Check if the current device is mobile.
    
    Returns:
        True if mobile device, False otherwise
    """
    # Placeholder - in production, use proper device detection
    return False
