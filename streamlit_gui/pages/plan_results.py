"""
Plan Results page - Display vendor combinations and handle selection
"""
import streamlit as st
from typing import Dict, List, Optional
import time

from components.api_client import api_client, APIError
from components.results import results_manager, plan_manager
from utils.helpers import show_error, show_success, show_info, format_currency


def render_plan_results_page():
    """Render the main plan results page"""
    st.header("🎯 Plan Results")
    
    # Check if we have a current plan
    current_plan_id = st.session_state.get("current_plan_id")
    
    if not current_plan_id:
        st.warning("No active plan found. Please create a plan or select an existing one.")
        
        # Show plan management interface
        st.subheader("Select an Existing Plan")
        plan_manager.display_plan_management_interface()
        return
    
    # Display current plan info
    st.info(f"📋 Current Plan: {current_plan_id}")
    
    # Main content tabs
    tab1, tab2 = st.tabs(["🎯 Results & Selection", "📋 Plan Management"])
    
    with tab1:
        render_results_tab(current_plan_id)
    
    with tab2:
        plan_manager.display_plan_management_interface()


def render_results_tab(plan_id: str):
    """Render the results and selection tab"""
    
    # Load results if not already loaded
    if not st.session_state.get("plan_combinations"):
        load_plan_results(plan_id)
    
    combinations = st.session_state.get("plan_combinations", [])
    
    if not combinations:
        st.info("No vendor combinations available yet. The planning process may still be in progress.")
        
        # Refresh button
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("🔄 Refresh Results", key="results_refresh"):
                load_plan_results(plan_id)
                st.rerun()
        
        with col2:
            if st.button("📊 Check Plan Status", key="results_check_status"):
                st.session_state.current_page = "plan_status"
                st.rerun()
        
        return
    
    # Display results summary
    display_results_summary(combinations)
    
    # Display combinations with selection interface
    st.subheader("Vendor Combinations")
    
    # Get current view mode from session state
    current_view = st.session_state.get("results_view_mode", "card")
    
    # Display combinations and handle selection
    selected_combination_id = results_manager.display_combinations(combinations, current_view)
    
    # Handle combination selection
    if selected_combination_id:
        handle_combination_selection(plan_id, selected_combination_id)


def load_plan_results(plan_id: str):
    """Load plan results from the API"""
    try:
        with st.spinner("Loading plan results..."):
            response = api_client.get_plan_results(plan_id)
            
            if response.get("status") == "success":
                combinations = response.get("combinations", [])
                st.session_state.plan_combinations = combinations
                
                if combinations:
                    show_success(f"Loaded {len(combinations)} vendor combinations!")
                else:
                    show_info("No combinations available yet.")
            else:
                error_msg = response.get("message", "Unknown error occurred")
                show_error(f"Failed to load results: {error_msg}")
                
    except APIError as e:
        show_error(f"Error loading plan results: {str(e)}")
        
        # If it's a 404, the plan might not have results yet
        if e.status_code == 404:
            st.info("Results not ready yet. The planning process may still be running.")


def display_results_summary(combinations: List[Dict]):
    """Display a summary of the results"""
    if not combinations:
        return
    
    st.subheader("Results Summary")
    
    # Calculate summary statistics
    total_combinations = len(combinations)
    avg_fitness_score = sum(c.get("fitness_score", 0) for c in combinations) / total_combinations
    avg_cost = sum(c.get("total_cost", 0) for c in combinations) / total_combinations
    
    # Find best and worst options
    best_fitness = max(combinations, key=lambda x: x.get("fitness_score", 0))
    lowest_cost = min(combinations, key=lambda x: x.get("total_cost", float('inf')))
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Options", total_combinations)
    
    with col2:
        st.metric("Avg Fitness Score", f"{avg_fitness_score:.1f}%")
    
    with col3:
        st.metric("Avg Cost", format_currency(avg_cost))
    
    with col4:
        st.metric("Best Fitness", f"{best_fitness.get('fitness_score', 0):.1f}%")
    
    # Highlight recommendations
    with st.expander("🏆 Recommendations", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**🎯 Best Overall Match**")
            st.write(f"Fitness Score: {best_fitness.get('fitness_score', 0):.1f}%")
            st.write(f"Cost: {format_currency(best_fitness.get('total_cost', 0))}")
            
            # Show key vendors
            venue = best_fitness.get('venue', {})
            if venue.get('name'):
                st.write(f"Venue: {venue['name']}")
        
        with col2:
            st.markdown("**💰 Most Budget-Friendly**")
            st.write(f"Cost: {format_currency(lowest_cost.get('total_cost', 0))}")
            st.write(f"Fitness Score: {lowest_cost.get('fitness_score', 0):.1f}%")
            
            # Show key vendors
            venue = lowest_cost.get('venue', {})
            if venue.get('name'):
                st.write(f"Venue: {venue['name']}")


def handle_combination_selection(plan_id: str, combination_id: str):
    """Handle the selection of a vendor combination"""
    
    # Confirmation dialog
    st.subheader("Confirm Selection")
    st.warning("⚠️ Once you select a combination, it cannot be changed. Are you sure you want to proceed?")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("✅ Confirm Selection", type="primary", key="results_confirm_selection"):
            select_combination(plan_id, combination_id)
    
    with col2:
        if st.button("❌ Cancel", key="results_cancel_selection"):
            st.rerun()


def select_combination(plan_id: str, combination_id: str):
    """Select a vendor combination via API"""
    try:
        with st.spinner("Selecting combination and generating blueprint..."):
            response = api_client.select_combination(plan_id, combination_id)
            
            if response.get("status") == "success":
                # Update session state
                st.session_state.selected_combination = combination_id
                
                # Show success message
                show_success("Combination selected successfully! Generating your event blueprint...")
                
                # Wait a moment for blueprint generation
                time.sleep(2)
                
                # Navigate to blueprint page
                st.session_state.current_page = "plan_blueprint"
                st.rerun()
                
            else:
                error_msg = response.get("message", "Unknown error occurred")
                show_error(f"Failed to select combination: {error_msg}")
                
    except APIError as e:
        show_error(f"Error selecting combination: {str(e)}")


def render_combination_comparison():
    """Render side-by-side combination comparison (helper function)"""
    combinations = st.session_state.get("plan_combinations", [])
    
    if len(combinations) < 2:
        st.info("Need at least 2 combinations for comparison.")
        return
    
    st.subheader("Compare Combinations")
    
    # Select combinations to compare
    selected_indices = st.multiselect(
        "Select combinations to compare (max 4)",
        options=list(range(len(combinations))),
        format_func=lambda x: f"Option {x + 1} - {combinations[x].get('venue', {}).get('name', 'Unknown')}",
        max_selections=4
    )
    
    if len(selected_indices) >= 2:
        # Create comparison columns
        cols = st.columns(len(selected_indices))
        
        for i, (col, idx) in enumerate(zip(cols, selected_indices)):
            combination = combinations[idx]
            
            with col:
                st.markdown(f"### Option {idx + 1}")
                
                # Key metrics
                fitness_score = combination.get("fitness_score", 0)
                total_cost = combination.get("total_cost", 0)
                
                st.metric("Fitness Score", f"{fitness_score:.1f}%")
                st.metric("Total Cost", format_currency(total_cost))
                
                # Vendors summary
                st.markdown("**Vendors:**")
                venue = combination.get("venue", {})
                caterer = combination.get("caterer", {})
                photographer = combination.get("photographer", {})
                makeup_artist = combination.get("makeup_artist", {})
                
                if venue.get("name"):
                    st.write(f"🏛️ {venue['name']}")
                if caterer.get("name"):
                    st.write(f"🍽️ {caterer['name']}")
                if photographer.get("name"):
                    st.write(f"📸 {photographer['name']}")
                if makeup_artist.get("name"):
                    st.write(f"💄 {makeup_artist['name']}")
                
                # Selection button
                if st.button(f"Select Option {idx + 1}", key=f"compare_select_{idx}", type="primary"):
                    handle_combination_selection(
                        st.session_state.current_plan_id,
                        combination.get("combination_id")
                    )


# Additional utility functions for the results page

def export_results_to_csv():
    """Export results to CSV format"""
    combinations = st.session_state.get("plan_combinations", [])
    
    if not combinations:
        st.error("No results to export")
        return
    
    try:
        import pandas as pd
        
        # Prepare data for export
        export_data = []
        for i, combo in enumerate(combinations):
            row = {
                "Option": i + 1,
                "Fitness_Score": combo.get("fitness_score", 0),
                "Total_Cost": combo.get("total_cost", 0),
                "Venue_Name": combo.get("venue", {}).get("name", ""),
                "Venue_Cost": combo.get("venue", {}).get("cost", 0),
                "Venue_Location": combo.get("venue", {}).get("location", ""),
                "Caterer_Name": combo.get("caterer", {}).get("name", ""),
                "Caterer_Cost": combo.get("caterer", {}).get("cost", 0),
                "Photographer_Name": combo.get("photographer", {}).get("name", ""),
                "Photographer_Cost": combo.get("photographer", {}).get("cost", 0),
                "Makeup_Artist_Name": combo.get("makeup_artist", {}).get("name", ""),
                "Makeup_Artist_Cost": combo.get("makeup_artist", {}).get("cost", 0),
            }
            export_data.append(row)
        
        df = pd.DataFrame(export_data)
        
        # Convert to CSV
        csv = df.to_csv(index=False)
        
        # Download button
        st.download_button(
            label="📥 Download Results as CSV",
            data=csv,
            file_name=f"event_plan_results_{st.session_state.current_plan_id}.csv",
            mime="text/csv"
        )
        
    except ImportError:
        st.error("Pandas not available for CSV export")
    except Exception as e:
        st.error(f"Error exporting results: {str(e)}")


def filter_combinations_by_budget(combinations: List[Dict], max_budget: float) -> List[Dict]:
    """Filter combinations by budget constraint"""
    return [c for c in combinations if c.get("total_cost", 0) <= max_budget]


def filter_combinations_by_location(combinations: List[Dict], preferred_locations: List[str]) -> List[Dict]:
    """Filter combinations by preferred locations"""
    if not preferred_locations:
        return combinations
    
    filtered = []
    for combo in combinations:
        venue_location = combo.get("venue", {}).get("location", "").lower()
        if any(loc.lower() in venue_location for loc in preferred_locations):
            filtered.append(combo)
    
    return filtered