"""
Results display components for vendor combinations and plan management
"""
import streamlit as st
from typing import Dict, List, Optional, Any
import pandas as pd
from datetime import datetime
import json

from components.api_client import api_client, APIError
from components.styles import RESULTS_CSS, get_fitness_score_class, get_plan_status_class
from utils.helpers import show_error, show_success, show_info, format_currency


class ResultsDisplayManager:
    """Manages the display of vendor combinations and results"""
    
    def __init__(self):
        self.view_modes = ["card", "table", "comparison"]
        self.sort_options = ["fitness_score", "total_cost", "venue_name", "location"]
        
    def display_combinations(self, combinations: List[Dict], view_mode: str = "card") -> Optional[str]:
        """
        Display vendor combinations in the specified view mode
        Returns selected combination ID if any
        """
        # Add CSS styling
        st.markdown(RESULTS_CSS, unsafe_allow_html=True)
        
        if not combinations:
            st.info("No vendor combinations available yet.")
            return None
            
        # View mode selector
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            selected_view = st.selectbox(
                "View Mode",
                options=self.view_modes,
                index=self.view_modes.index(view_mode),
                format_func=lambda x: x.title()
            )
        
        with col2:
            sort_by = st.selectbox(
                "Sort By",
                options=self.sort_options,
                format_func=lambda x: x.replace("_", " ").title()
            )
        
        with col3:
            reverse_sort = st.checkbox("Descending", value=True if sort_by == "fitness_score" else False)
        
        # Sort combinations
        sorted_combinations = self._sort_combinations(combinations, sort_by, reverse_sort)
        
        # Display based on view mode
        if selected_view == "card":
            return self._display_card_view(sorted_combinations)
        elif selected_view == "table":
            return self._display_table_view(sorted_combinations)
        elif selected_view == "comparison":
            return self._display_comparison_view(sorted_combinations)
        
        return None
    
    def _sort_combinations(self, combinations: List[Dict], sort_by: str, reverse: bool) -> List[Dict]:
        """Sort combinations by the specified criteria"""
        try:
            if sort_by == "fitness_score":
                return sorted(combinations, key=lambda x: x.get("fitness_score", 0), reverse=reverse)
            elif sort_by == "total_cost":
                return sorted(combinations, key=lambda x: x.get("total_cost", 0), reverse=reverse)
            elif sort_by == "venue_name":
                return sorted(combinations, key=lambda x: x.get("venue", {}).get("name", ""), reverse=reverse)
            elif sort_by == "location":
                return sorted(combinations, key=lambda x: x.get("venue", {}).get("location", ""), reverse=reverse)
            else:
                return combinations
        except Exception as e:
            st.error(f"Error sorting combinations: {str(e)}")
            return combinations
    
    def _display_card_view(self, combinations: List[Dict]) -> Optional[str]:
        """Display combinations in card format"""
        selected_combination = None
        
        # Display combinations in a grid
        cols_per_row = 2
        for i in range(0, len(combinations), cols_per_row):
            cols = st.columns(cols_per_row)
            
            for j, col in enumerate(cols):
                if i + j < len(combinations):
                    combination = combinations[i + j]
                    
                    with col:
                        if self._render_combination_card(combination, i + j):
                            selected_combination = combination.get("combination_id")
        
        return selected_combination
    
    def _render_combination_card(self, combination: Dict, index: int) -> bool:
        """Render a single combination card"""
        try:
            # Extract data
            fitness_score = combination.get("fitness_score", 0)
            total_cost = combination.get("total_cost", 0)
            venue = combination.get("venue", {})
            caterer = combination.get("caterer", {})
            photographer = combination.get("photographer", {})
            makeup_artist = combination.get("makeup_artist", {})
            
            # Create card container
            with st.container():
                st.markdown(f"""
                <div style="
                    border: 1px solid #ddd;
                    border-radius: 10px;
                    padding: 1rem;
                    margin-bottom: 1rem;
                    background-color: white;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                ">
                """, unsafe_allow_html=True)
                
                # Header with score and cost
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Fitness Score", f"{fitness_score:.1f}%")
                with col2:
                    st.metric("Total Cost", format_currency(total_cost))
                
                # Vendor summary
                st.markdown("**Vendors:**")
                vendors_info = []
                if venue.get("name"):
                    vendors_info.append(f"🏛️ **Venue:** {venue['name']}")
                if caterer.get("name"):
                    vendors_info.append(f"🍽️ **Caterer:** {caterer['name']}")
                if photographer.get("name"):
                    vendors_info.append(f"📸 **Photographer:** {photographer['name']}")
                if makeup_artist.get("name"):
                    vendors_info.append(f"💄 **Makeup:** {makeup_artist['name']}")
                
                for info in vendors_info:
                    st.markdown(info)
                
                # Location info
                if venue.get("location"):
                    st.markdown(f"📍 **Location:** {venue['location']}")
                
                # Action buttons
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("View Details", key=f"details_{index}"):
                        self._show_combination_details(combination)
                
                with col2:
                    select_button = st.button(
                        "Select This Plan",
                        key=f"select_{index}",
                        type="primary"
                    )
                
                st.markdown("</div>", unsafe_allow_html=True)
                
                return select_button
                
        except Exception as e:
            st.error(f"Error rendering combination card: {str(e)}")
            return False
    
    def _display_table_view(self, combinations: List[Dict]) -> Optional[str]:
        """Display combinations in table format"""
        try:
            # Prepare data for table
            table_data = []
            for i, combination in enumerate(combinations):
                row = {
                    "Index": i + 1,
                    "Fitness Score": f"{combination.get('fitness_score', 0):.1f}%",
                    "Total Cost": format_currency(combination.get('total_cost', 0)),
                    "Venue": combination.get('venue', {}).get('name', 'N/A'),
                    "Caterer": combination.get('caterer', {}).get('name', 'N/A'),
                    "Photographer": combination.get('photographer', {}).get('name', 'N/A'),
                    "Makeup Artist": combination.get('makeup_artist', {}).get('name', 'N/A'),
                    "Location": combination.get('venue', {}).get('location', 'N/A')
                }
                table_data.append(row)
            
            # Display table
            df = pd.DataFrame(table_data)
            
            # Use st.dataframe for interactive table
            event = st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row"
            )
            
            # Handle selection
            if event.selection and event.selection.rows:
                selected_index = event.selection.rows[0]
                selected_combination = combinations[selected_index]
                
                # Show selected combination details
                st.subheader("Selected Combination Details")
                self._show_combination_details(selected_combination)
                
                # Selection button
                if st.button("Confirm Selection", type="primary"):
                    return selected_combination.get("combination_id")
            
            return None
            
        except Exception as e:
            st.error(f"Error displaying table view: {str(e)}")
            return None
    
    def _display_comparison_view(self, combinations: List[Dict]) -> Optional[str]:
        """Display combinations in side-by-side comparison format"""
        if len(combinations) < 2:
            st.info("Need at least 2 combinations for comparison view.")
            return self._display_card_view(combinations)
        
        # Select combinations to compare
        st.subheader("Select Combinations to Compare")
        
        # Limit to top 4 for comparison
        compare_combinations = combinations[:4]
        
        # Create comparison columns
        cols = st.columns(len(compare_combinations))
        
        selected_combination = None
        
        for i, (col, combination) in enumerate(zip(cols, compare_combinations)):
            with col:
                st.markdown(f"### Option {i + 1}")
                
                # Key metrics
                fitness_score = combination.get("fitness_score", 0)
                total_cost = combination.get("total_cost", 0)
                
                st.metric("Fitness Score", f"{fitness_score:.1f}%")
                st.metric("Total Cost", format_currency(total_cost))
                
                # Vendors
                st.markdown("**Vendors:**")
                venue = combination.get("venue", {})
                caterer = combination.get("caterer", {})
                photographer = combination.get("photographer", {})
                makeup_artist = combination.get("makeup_artist", {})
                
                st.write(f"🏛️ {venue.get('name', 'N/A')}")
                st.write(f"🍽️ {caterer.get('name', 'N/A')}")
                st.write(f"📸 {photographer.get('name', 'N/A')}")
                st.write(f"💄 {makeup_artist.get('name', 'N/A')}")
                
                # Location
                if venue.get("location"):
                    st.write(f"📍 {venue['location']}")
                
                # Selection button
                if st.button(f"Select Option {i + 1}", key=f"compare_select_{i}", type="primary"):
                    selected_combination = combination.get("combination_id")
        
        return selected_combination
    
    def _show_combination_details(self, combination: Dict):
        """Show detailed information about a combination in a modal/expander"""
        with st.expander("Detailed Information", expanded=True):
            # Fitness score breakdown
            st.subheader("Fitness Score Breakdown")
            fitness_details = combination.get("fitness_details", {})
            if fitness_details:
                for category, score in fitness_details.items():
                    st.write(f"**{category.replace('_', ' ').title()}:** {score:.1f}%")
            
            # Vendor details
            vendors = ["venue", "caterer", "photographer", "makeup_artist"]
            vendor_icons = {"venue": "🏛️", "caterer": "🍽️", "photographer": "📸", "makeup_artist": "💄"}
            
            for vendor_type in vendors:
                vendor = combination.get(vendor_type, {})
                if vendor.get("name"):
                    st.subheader(f"{vendor_icons.get(vendor_type, '📋')} {vendor_type.replace('_', ' ').title()}")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Name:** {vendor.get('name', 'N/A')}")
                        st.write(f"**Cost:** {format_currency(vendor.get('cost', 0))}")
                        if vendor.get('location'):
                            st.write(f"**Location:** {vendor['location']}")
                        if vendor.get('contact_phone'):
                            st.write(f"**Phone:** {vendor['contact_phone']}")
                        if vendor.get('contact_email'):
                            st.write(f"**Email:** {vendor['contact_email']}")
                    
                    with col2:
                        # Amenities/features
                        amenities = vendor.get('amenities', [])
                        if amenities:
                            st.write("**Amenities/Features:**")
                            for amenity in amenities[:5]:  # Show top 5
                                st.write(f"• {amenity}")
                        
                        # Cuisine types for caterers
                        if vendor_type == "caterer" and vendor.get('cuisine_types'):
                            st.write("**Cuisine Types:**")
                            for cuisine in vendor['cuisine_types'][:3]:
                                st.write(f"• {cuisine}")


class PlanManager:
    """Manages multiple event plans - listing, searching, filtering"""
    
    def __init__(self):
        self.plans_cache = {}
        self.last_refresh = None
    
    def display_plan_management_interface(self):
        """Display the main plan management interface"""
        st.header("📋 Plan Management")
        
        # Action buttons
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            if st.button("🔄 Refresh Plans", use_container_width=True):
                self._refresh_plans()
        
        with col2:
            if st.button("➕ Create New Plan", use_container_width=True):
                st.session_state.current_page = "create_plan"
                st.rerun()
        
        with col3:
            show_archived = st.checkbox("Show Archived")
        
        # Search and filter
        search_term = st.text_input("🔍 Search plans", placeholder="Search by name, type, or status...")
        
        col1, col2 = st.columns(2)
        with col1:
            status_filter = st.multiselect(
                "Filter by Status",
                options=["pending", "in_progress", "completed", "failed", "cancelled"],
                default=["pending", "in_progress", "completed"]
            )
        
        with col2:
            date_range = st.date_input(
                "Filter by Date Range",
                value=None,
                help="Select date range for plan creation"
            )
        
        # Load and display plans
        plans = self._load_plans()
        
        if plans:
            # Apply filters
            filtered_plans = self._filter_plans(plans, search_term, status_filter, show_archived)
            
            if filtered_plans:
                self._display_plans_list(filtered_plans)
            else:
                st.info("No plans match the current filters.")
        else:
            st.info("No plans found. Create your first plan to get started!")
    
    def _refresh_plans(self):
        """Refresh the plans list from the API"""
        try:
            with st.spinner("Refreshing plans..."):
                response = api_client.list_plans(limit=100)
                self.plans_cache = response
                self.last_refresh = datetime.now()
                show_success("Plans refreshed successfully!")
        except APIError as e:
            show_error(f"Failed to refresh plans: {str(e)}")
    
    def _load_plans(self) -> List[Dict]:
        """Load plans from cache or API"""
        # Auto-refresh if cache is empty or old
        if not self.plans_cache or not self.last_refresh or \
           (datetime.now() - self.last_refresh).seconds > 300:  # 5 minutes
            self._refresh_plans()
        
        return self.plans_cache.get("plans", [])
    
    def _filter_plans(self, plans: List[Dict], search_term: str, status_filter: List[str], show_archived: bool) -> List[Dict]:
        """Apply filters to the plans list"""
        filtered = plans
        
        # Status filter
        if status_filter:
            filtered = [p for p in filtered if p.get("status") in status_filter]
        
        # Archived filter
        if not show_archived:
            filtered = [p for p in filtered if not p.get("archived", False)]
        
        # Search filter
        if search_term:
            search_lower = search_term.lower()
            filtered = [
                p for p in filtered
                if search_lower in p.get("client_name", "").lower() or
                   search_lower in p.get("event_type", "").lower() or
                   search_lower in p.get("status", "").lower() or
                   search_lower in str(p.get("plan_id", "")).lower()
            ]
        
        return filtered
    
    def _display_plans_list(self, plans: List[Dict]):
        """Display the filtered plans list"""
        st.subheader(f"Plans ({len(plans)})")
        
        for plan in plans:
            with st.container():
                self._render_plan_card(plan)
    
    def _render_plan_card(self, plan: Dict):
        """Render a single plan card"""
        plan_id = plan.get("plan_id", "Unknown")
        client_name = plan.get("client_name", "Unknown Client")
        event_type = plan.get("event_type", "Unknown Event")
        status = plan.get("status", "unknown")
        created_at = plan.get("created_at", "")
        event_date = plan.get("event_date", "")
        
        # Status color mapping
        status_colors = {
            "pending": "🟡",
            "in_progress": "🔵", 
            "completed": "🟢",
            "failed": "🔴",
            "cancelled": "⚫"
        }
        
        status_icon = status_colors.get(status, "⚪")
        
        # Create card
        with st.expander(f"{status_icon} {client_name} - {event_type} ({plan_id})", expanded=False):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write(f"**Status:** {status.title()}")
                st.write(f"**Event Type:** {event_type}")
                if event_date:
                    st.write(f"**Event Date:** {event_date}")
            
            with col2:
                st.write(f"**Plan ID:** {plan_id}")
                if created_at:
                    st.write(f"**Created:** {created_at}")
                
                # Budget info if available
                budget = plan.get("budget")
                if budget:
                    st.write(f"**Budget:** {format_currency(budget)}")
            
            with col3:
                # Action buttons
                if st.button("Open Plan", key=f"open_{plan_id}"):
                    st.session_state.current_plan_id = plan_id
                    st.session_state.plan_data = plan
                    
                    # Navigate based on status
                    if status == "completed":
                        st.session_state.current_page = "plan_results"
                    elif status in ["pending", "in_progress"]:
                        st.session_state.current_page = "plan_status"
                    else:
                        st.session_state.current_page = "plan_status"
                    
                    st.rerun()
                
                if st.button("Delete", key=f"delete_{plan_id}"):
                    if st.session_state.get(f"confirm_delete_{plan_id}"):
                        self._delete_plan(plan_id)
                    else:
                        st.session_state[f"confirm_delete_{plan_id}"] = True
                        st.warning("Click again to confirm deletion")
    
    def _delete_plan(self, plan_id: str):
        """Delete a plan"""
        try:
            api_client.delete_plan(plan_id)
            show_success(f"Plan {plan_id} deleted successfully!")
            self._refresh_plans()
            st.rerun()
        except APIError as e:
            show_error(f"Failed to delete plan: {str(e)}")


# Global instances
results_manager = ResultsDisplayManager()
plan_manager = PlanManager()