"""
Pagination Component for Lazy Loading

Provides pagination controls and utilities for displaying large datasets
in manageable chunks.
"""

import streamlit as st
from typing import List, Any, Dict, Callable, Optional
from utils.caching import DataSampler
from utils.helpers import init_session_state


class PaginationComponent:
    """
    Reusable pagination component for lazy loading large datasets.
    
    Features:
    - Page navigation controls
    - Configurable page size
    - Jump to page functionality
    - Display of current page info
    """
    
    def __init__(self, key_prefix: str, page_size: int = 50):
        """
        Initialize pagination component.
        
        Args:
            key_prefix: Unique prefix for session state keys
            page_size: Number of items per page
        """
        self.key_prefix = key_prefix
        self.page_size = page_size
        
        # Initialize session state
        init_session_state(f'{key_prefix}_current_page', 1)
        init_session_state(f'{key_prefix}_page_size', page_size)
    
    def render_controls(self, total_items: int) -> int:
        """
        Render pagination controls.
        
        Args:
            total_items: Total number of items
            
        Returns:
            Current page number
        """
        current_page = st.session_state.get(f'{self.key_prefix}_current_page', 1)
        page_size = st.session_state.get(f'{self.key_prefix}_page_size', self.page_size)
        
        total_pages = max(1, (total_items + page_size - 1) // page_size)
        
        # Ensure current page is valid
        current_page = max(1, min(current_page, total_pages))
        st.session_state[f'{self.key_prefix}_current_page'] = current_page
        
        # Calculate display range
        start_idx = (current_page - 1) * page_size + 1
        end_idx = min(current_page * page_size, total_items)
        
        # Render controls
        col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
        
        with col1:
            if st.button("⏮️ First", key=f"{self.key_prefix}_first", 
                        disabled=current_page == 1, use_container_width=True):
                st.session_state[f'{self.key_prefix}_current_page'] = 1
                st.rerun()
        
        with col2:
            if st.button("◀️ Prev", key=f"{self.key_prefix}_prev", 
                        disabled=current_page == 1, use_container_width=True):
                st.session_state[f'{self.key_prefix}_current_page'] = current_page - 1
                st.rerun()
        
        with col3:
            st.markdown(
                f"<div style='text-align: center; padding: 8px;'>"
                f"<b>Page {current_page} of {total_pages}</b><br>"
                f"<small>Showing {start_idx}-{end_idx} of {total_items} items</small>"
                f"</div>",
                unsafe_allow_html=True
            )
        
        with col4:
            if st.button("Next ▶️", key=f"{self.key_prefix}_next", 
                        disabled=current_page == total_pages, use_container_width=True):
                st.session_state[f'{self.key_prefix}_current_page'] = current_page + 1
                st.rerun()
        
        with col5:
            if st.button("Last ⏭️", key=f"{self.key_prefix}_last", 
                        disabled=current_page == total_pages, use_container_width=True):
                st.session_state[f'{self.key_prefix}_current_page'] = total_pages
                st.rerun()
        
        # Jump to page
        with st.expander("⚙️ Page Settings", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                jump_page = st.number_input(
                    "Jump to page",
                    min_value=1,
                    max_value=total_pages,
                    value=current_page,
                    key=f"{self.key_prefix}_jump_input"
                )
                
                if st.button("Go", key=f"{self.key_prefix}_jump_button"):
                    st.session_state[f'{self.key_prefix}_current_page'] = jump_page
                    st.rerun()
            
            with col2:
                new_page_size = st.selectbox(
                    "Items per page",
                    options=[10, 25, 50, 100, 200],
                    index=[10, 25, 50, 100, 200].index(page_size),
                    key=f"{self.key_prefix}_page_size_select"
                )
                
                if new_page_size != page_size:
                    st.session_state[f'{self.key_prefix}_page_size'] = new_page_size
                    st.session_state[f'{self.key_prefix}_current_page'] = 1
                    st.rerun()
        
        return current_page
    
    def paginate_data(self, data: List[Any]) -> List[Any]:
        """
        Get current page of data.
        
        Args:
            data: Full dataset
            
        Returns:
            Paginated data for current page
        """
        current_page = st.session_state.get(f'{self.key_prefix}_current_page', 1)
        page_size = st.session_state.get(f'{self.key_prefix}_page_size', self.page_size)
        
        page_data, _ = DataSampler.paginate(data, current_page, page_size)
        return page_data


def render_paginated_list(
    data: List[Any],
    render_item: Callable[[Any], None],
    key_prefix: str,
    page_size: int = 50,
    empty_message: str = "No items to display"
):
    """
    Render a paginated list with controls.
    
    Args:
        data: Full dataset
        render_item: Function to render each item
        key_prefix: Unique prefix for pagination keys
        page_size: Number of items per page
        empty_message: Message to display when list is empty
    """
    if not data:
        st.info(empty_message)
        return
    
    # Create pagination component
    pagination = PaginationComponent(key_prefix, page_size)
    
    # Render controls
    pagination.render_controls(len(data))
    
    st.divider()
    
    # Get current page data
    page_data = pagination.paginate_data(data)
    
    # Render items
    for item in page_data:
        render_item(item)


class VirtualScrollList:
    """
    Virtual scrolling implementation for very large lists.
    
    Only renders visible items plus a buffer, improving performance
    for lists with thousands of items.
    """
    
    def __init__(self, key_prefix: str, item_height: int = 100, buffer_size: int = 10):
        """
        Initialize virtual scroll list.
        
        Args:
            key_prefix: Unique prefix for session state keys
            item_height: Approximate height of each item in pixels
            buffer_size: Number of items to render above/below visible area
        """
        self.key_prefix = key_prefix
        self.item_height = item_height
        self.buffer_size = buffer_size
        
        # Initialize session state
        init_session_state(f'{key_prefix}_scroll_position', 0)
        init_session_state(f'{key_prefix}_viewport_height', 800)
    
    def render(
        self,
        data: List[Any],
        render_item: Callable[[Any, int], None],
        viewport_height: int = 800
    ):
        """
        Render virtual scroll list.
        
        Args:
            data: Full dataset
            render_item: Function to render each item (receives item and index)
            viewport_height: Height of viewport in pixels
        """
        if not data:
            st.info("No items to display")
            return
        
        total_items = len(data)
        total_height = total_items * self.item_height
        
        # Get scroll position
        scroll_position = st.session_state.get(f'{self.key_prefix}_scroll_position', 0)
        
        # Calculate visible range
        first_visible = max(0, int(scroll_position / self.item_height) - self.buffer_size)
        last_visible = min(
            total_items,
            int((scroll_position + viewport_height) / self.item_height) + self.buffer_size
        )
        
        # Render scroll controls
        new_scroll = st.slider(
            "Scroll Position",
            min_value=0,
            max_value=max(0, total_height - viewport_height),
            value=scroll_position,
            key=f"{self.key_prefix}_scroll_slider",
            label_visibility="collapsed"
        )
        
        if new_scroll != scroll_position:
            st.session_state[f'{self.key_prefix}_scroll_position'] = new_scroll
            st.rerun()
        
        # Render visible items
        st.markdown(f"Showing items {first_visible + 1} to {last_visible} of {total_items}")
        
        for idx in range(first_visible, last_visible):
            render_item(data[idx], idx)


def render_infinite_scroll(
    data: List[Any],
    render_item: Callable[[Any], None],
    key_prefix: str,
    initial_load: int = 50,
    load_more_count: int = 25
):
    """
    Render list with infinite scroll (load more) functionality.
    
    Args:
        data: Full dataset
        render_item: Function to render each item
        key_prefix: Unique prefix for session state keys
        initial_load: Number of items to load initially
        load_more_count: Number of items to load when "Load More" is clicked
    """
    if not data:
        st.info("No items to display")
        return
    
    # Initialize session state
    init_session_state(f'{key_prefix}_loaded_count', initial_load)
    
    loaded_count = st.session_state.get(f'{key_prefix}_loaded_count', initial_load)
    loaded_count = min(loaded_count, len(data))
    
    # Render loaded items
    for item in data[:loaded_count]:
        render_item(item)
    
    # Show load more button if there are more items
    if loaded_count < len(data):
        remaining = len(data) - loaded_count
        load_count = min(load_more_count, remaining)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button(
                f"⬇️ Load {load_count} More ({remaining} remaining)",
                key=f"{self.key_prefix}_load_more",
                use_container_width=True
            ):
                st.session_state[f'{key_prefix}_loaded_count'] = loaded_count + load_count
                st.rerun()
    else:
        st.success(f"✅ All {len(data)} items loaded")
