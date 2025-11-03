"""
Blueprint display page for final event plans
"""
import streamlit as st
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import base64
from io import BytesIO
import tempfile
import os

from components.api_client import api_client, APIError
from components.styles import RESULTS_CSS
from utils.helpers import show_error, show_success, show_info, format_currency
from utils.config import config


def render_plan_blueprint_page():
    """Main blueprint page rendering function"""
    st.header("📋 Event Blueprint")
    
    # Check if we have a current plan
    if not st.session_state.get('current_plan_id'):
        st.warning("No active plan found. Please create a plan or select an existing one.")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("➕ Create New Plan", use_container_width=True, key="blueprint_create_new_plan"):
                st.session_state.current_page = "create_plan"
                st.rerun()
        
        with col2:
            if st.button("🏠 Go to Home", use_container_width=True, key="blueprint_go_home"):
                st.session_state.current_page = "home"
                st.rerun()
        return
    
    # Check if current_plan_id exists in session state
    if 'current_plan_id' not in st.session_state or not st.session_state.current_plan_id:
        st.warning("No active plan found. Please create a plan first.")
        if st.button("🆕 Create New Plan", key="blueprint_create_plan"):
            st.session_state.current_page = "create_plan"
            st.rerun()
        return
    
    plan_id = st.session_state.current_plan_id
    
    # Load blueprint data
    blueprint_data = load_blueprint_data(plan_id)
    
    if not blueprint_data:
        st.error("Unable to load blueprint data. The plan may not be complete yet.")
        
        if st.button("🔄 Refresh Blueprint", key="blueprint_refresh"):
            st.rerun()
        
        if st.button("← Back to Results", key="blueprint_back_to_results"):
            st.session_state.current_page = "plan_results"
            st.rerun()
        return
    
    # Display blueprint
    blueprint_manager = BlueprintManager()
    blueprint_manager.display_blueprint(blueprint_data)


def load_blueprint_data(plan_id: str) -> Optional[Dict]:
    """Load blueprint data from API or session state"""
    try:
        # Try to get from session state first
        if st.session_state.get('plan_blueprint'):
            return st.session_state.plan_blueprint
        
        # Otherwise fetch from API
        with st.spinner("Loading blueprint data..."):
            blueprint_data = api_client.get_blueprint(plan_id)
            st.session_state.plan_blueprint = blueprint_data
            return blueprint_data
            
    except APIError as e:
        show_error(f"Failed to load blueprint: {str(e)}")
        return None
    except Exception as e:
        show_error(f"Unexpected error loading blueprint: {str(e)}")
        return None


class BlueprintManager:
    """Manages blueprint display and export functionality"""
    
    def __init__(self):
        self.export_formats = ["PDF", "JSON", "Text", "HTML"]
    
    def display_blueprint(self, blueprint_data: Dict):
        """Display the complete blueprint with all sections"""
        # Add CSS styling
        st.markdown(RESULTS_CSS, unsafe_allow_html=True)
        
        # Blueprint header with export options
        self._render_blueprint_header(blueprint_data)
        
        # Main blueprint content in tabs
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "📋 Overview", 
            "📅 Timeline", 
            "👥 Vendors", 
            "💰 Budget", 
            "📞 Contacts",
            "✅ Tasks"
        ])
        
        with tab1:
            self._render_overview_section(blueprint_data)
        
        with tab2:
            self._render_timeline_section(blueprint_data)
        
        with tab3:
            self._render_vendors_section(blueprint_data)
        
        with tab4:
            self._render_budget_section(blueprint_data)
        
        with tab5:
            self._render_contacts_section(blueprint_data)
        
        with tab6:
            self._render_tasks_section(blueprint_data)
        
        # Next steps and actions
        self._render_next_steps_section(blueprint_data)
    
    def _render_blueprint_header(self, blueprint_data: Dict):
        """Render the blueprint header with export options"""
        event_info = blueprint_data.get('event_info', {})
        client_name = event_info.get('client_name', 'Unknown Client')
        event_type = event_info.get('event_type', 'Event')
        event_date = event_info.get('event_date', 'TBD')
        
        # Header section
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            border-radius: 10px;
            margin-bottom: 2rem;
            text-align: center;
        ">
            <h1 style="margin: 0; font-size: 2.5rem;">🎉 {event_type}</h1>
            <h2 style="margin: 0.5rem 0; font-size: 1.5rem;">for {client_name}</h2>
            <p style="margin: 0; font-size: 1.2rem; opacity: 0.9;">📅 {event_date}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Export options
        st.subheader("📥 Export Options")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            if st.button("📄 Export PDF", use_container_width=True, key="blueprint_export_pdf"):
                self._export_blueprint(blueprint_data, "PDF")
        
        with col2:
            if st.button("📊 Export JSON", use_container_width=True, key="blueprint_export_json"):
                self._export_blueprint(blueprint_data, "JSON")
        
        with col3:
            if st.button("📝 Export Text", use_container_width=True, key="blueprint_export_text"):
                self._export_blueprint(blueprint_data, "Text")
        
        with col4:
            if st.button("🌐 Export HTML", use_container_width=True, key="blueprint_export_html"):
                self._export_blueprint(blueprint_data, "HTML")
        
        with col5:
            if st.button("📧 Email Blueprint", use_container_width=True, key="blueprint_email"):
                self._show_email_dialog(blueprint_data)
    
    def _render_overview_section(self, blueprint_data: Dict):
        """Render the overview section"""
        st.subheader("📋 Event Overview")
        
        event_info = blueprint_data.get('event_info', {})
        selected_combination = blueprint_data.get('selected_combination', {})
        
        # Event details
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Event Details")
            st.write(f"**Client:** {event_info.get('client_name', 'N/A')}")
            st.write(f"**Event Type:** {event_info.get('event_type', 'N/A')}")
            st.write(f"**Date:** {event_info.get('event_date', 'N/A')}")
            st.write(f"**Time:** {event_info.get('event_time', 'N/A')}")
            st.write(f"**Guest Count:** {event_info.get('guest_count', 'N/A')}")
            
            if event_info.get('location'):
                st.write(f"**Location:** {event_info['location']}")
        
        with col2:
            st.markdown("### Plan Summary")
            fitness_score = selected_combination.get('fitness_score', 0)
            total_cost = selected_combination.get('total_cost', 0)
            
            st.metric("Overall Fitness Score", f"{fitness_score:.1f}%")
            st.metric("Total Investment", format_currency(total_cost))
            
            # Budget utilization
            budget = event_info.get('budget', 0)
            if budget > 0:
                utilization = (total_cost / budget) * 100
                st.metric("Budget Utilization", f"{utilization:.1f}%")
        
        # Client vision
        client_vision = event_info.get('client_vision', '')
        if client_vision:
            st.markdown("### Client Vision")
            st.info(client_vision)
        
        # Key highlights
        st.markdown("### Key Highlights")
        highlights = self._generate_key_highlights(blueprint_data)
        for highlight in highlights:
            st.write(f"✨ {highlight}")
    
    def _render_timeline_section(self, blueprint_data: Dict):
        """Render the timeline section"""
        st.subheader("📅 Event Timeline")
        
        timeline = blueprint_data.get('timeline', {})
        
        if not timeline:
            st.info("Timeline information is being generated...")
            return
        
        # Pre-event timeline
        st.markdown("### Pre-Event Schedule")
        pre_event = timeline.get('pre_event', [])
        
        if pre_event:
            for item in pre_event:
                date = item.get('date', 'TBD')
                time = item.get('time', '')
                task = item.get('task', '')
                responsible = item.get('responsible', '')
                
                with st.container():
                    st.markdown(f"""
                    <div style="
                        border-left: 4px solid #007bff;
                        padding-left: 1rem;
                        margin-bottom: 1rem;
                        background-color: #f8f9fa;
                        border-radius: 0 8px 8px 0;
                    ">
                        <strong>{date} {time}</strong><br>
                        {task}<br>
                        <small><em>Responsible: {responsible}</em></small>
                    </div>
                    """, unsafe_allow_html=True)
        
        # Event day timeline
        st.markdown("### Event Day Schedule")
        event_day = timeline.get('event_day', [])
        
        if event_day:
            for item in event_day:
                time = item.get('time', '')
                activity = item.get('activity', '')
                vendor = item.get('vendor', '')
                notes = item.get('notes', '')
                
                with st.container():
                    st.markdown(f"""
                    <div style="
                        border-left: 4px solid #28a745;
                        padding-left: 1rem;
                        margin-bottom: 1rem;
                        background-color: #f8fff9;
                        border-radius: 0 8px 8px 0;
                    ">
                        <strong>{time}</strong> - {activity}<br>
                        {f'<em>Vendor: {vendor}</em><br>' if vendor else ''}
                        {f'<small>{notes}</small>' if notes else ''}
                    </div>
                    """, unsafe_allow_html=True)
        
        # Post-event tasks
        st.markdown("### Post-Event Tasks")
        post_event = timeline.get('post_event', [])
        
        if post_event:
            for item in post_event:
                task = item.get('task', '')
                deadline = item.get('deadline', '')
                responsible = item.get('responsible', '')
                
                st.write(f"📋 **{task}**")
                if deadline:
                    st.write(f"   ⏰ Deadline: {deadline}")
                if responsible:
                    st.write(f"   👤 Responsible: {responsible}")
                st.write("")
    
    def _render_vendors_section(self, blueprint_data: Dict):
        """Render the vendors section"""
        st.subheader("👥 Vendor Information")
        
        selected_combination = blueprint_data.get('selected_combination', {})
        vendors = ['venue', 'caterer', 'photographer', 'makeup_artist']
        vendor_icons = {
            'venue': '🏛️',
            'caterer': '🍽️', 
            'photographer': '📸',
            'makeup_artist': '💄'
        }
        
        for vendor_type in vendors:
            vendor = selected_combination.get(vendor_type, {})
            if not vendor.get('name'):
                continue
            
            icon = vendor_icons.get(vendor_type, '📋')
            vendor_name = vendor_type.replace('_', ' ').title()
            
            with st.expander(f"{icon} {vendor_name}: {vendor['name']}", expanded=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Contact Information**")
                    st.write(f"**Name:** {vendor.get('name', 'N/A')}")
                    st.write(f"**Phone:** {vendor.get('contact_phone', 'N/A')}")
                    st.write(f"**Email:** {vendor.get('contact_email', 'N/A')}")
                    
                    if vendor.get('website'):
                        st.write(f"**Website:** {vendor['website']}")
                    
                    if vendor.get('location'):
                        st.write(f"**Location:** {vendor['location']}")
                
                with col2:
                    st.markdown("**Service Details**")
                    st.write(f"**Cost:** {format_currency(vendor.get('cost', 0))}")
                    
                    # Service-specific details
                    if vendor_type == 'venue':
                        capacity = vendor.get('capacity', {})
                        if capacity:
                            st.write(f"**Capacity:** {capacity.get('max_guests', 'N/A')} guests")
                        
                        amenities = vendor.get('amenities', [])
                        if amenities:
                            st.write("**Amenities:**")
                            for amenity in amenities[:5]:
                                st.write(f"• {amenity}")
                    
                    elif vendor_type == 'caterer':
                        cuisine_types = vendor.get('cuisine_types', [])
                        if cuisine_types:
                            st.write(f"**Cuisine:** {', '.join(cuisine_types[:3])}")
                        
                        service_style = vendor.get('service_style', '')
                        if service_style:
                            st.write(f"**Service Style:** {service_style}")
                    
                    elif vendor_type == 'photographer':
                        packages = vendor.get('packages', [])
                        if packages:
                            st.write("**Packages Available:**")
                            for package in packages[:3]:
                                st.write(f"• {package}")
                    
                    elif vendor_type == 'makeup_artist':
                        services = vendor.get('services', [])
                        if services:
                            st.write("**Services:**")
                            for service in services[:3]:
                                st.write(f"• {service}")
                
                # Special notes or requirements
                notes = vendor.get('notes', '')
                if notes:
                    st.markdown("**Special Notes:**")
                    st.info(notes)
    
    def _render_budget_section(self, blueprint_data: Dict):
        """Render the budget breakdown section"""
        st.subheader("💰 Budget Breakdown")
        
        selected_combination = blueprint_data.get('selected_combination', {})
        event_info = blueprint_data.get('event_info', {})
        
        # Budget overview
        total_cost = selected_combination.get('total_cost', 0)
        original_budget = event_info.get('budget', 0)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Cost", format_currency(total_cost))
        
        with col2:
            st.metric("Original Budget", format_currency(original_budget))
        
        with col3:
            if original_budget > 0:
                difference = total_cost - original_budget
                st.metric(
                    "Difference", 
                    format_currency(abs(difference)),
                    delta=format_currency(difference)
                )
        
        # Vendor cost breakdown
        st.markdown("### Cost by Vendor")
        
        vendor_costs = []
        vendors = ['venue', 'caterer', 'photographer', 'makeup_artist']
        vendor_names = {
            'venue': 'Venue',
            'caterer': 'Catering',
            'photographer': 'Photography', 
            'makeup_artist': 'Makeup & Beauty'
        }
        
        for vendor_type in vendors:
            vendor = selected_combination.get(vendor_type, {})
            if vendor.get('cost'):
                vendor_costs.append({
                    'Category': vendor_names[vendor_type],
                    'Vendor': vendor.get('name', 'N/A'),
                    'Cost': vendor['cost'],
                    'Percentage': (vendor['cost'] / total_cost * 100) if total_cost > 0 else 0
                })
        
        if vendor_costs:
            # Create a visual breakdown
            for item in vendor_costs:
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    st.write(f"**{item['Category']}**")
                    st.write(f"*{item['Vendor']}*")
                
                with col2:
                    st.write(format_currency(item['Cost']))
                
                with col3:
                    st.write(f"{item['Percentage']:.1f}%")
                
                # Progress bar for visual representation
                st.progress(item['Percentage'] / 100)
                st.write("")
        
        # Additional costs (if any)
        additional_costs = blueprint_data.get('additional_costs', [])
        if additional_costs:
            st.markdown("### Additional Costs")
            
            for cost_item in additional_costs:
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**{cost_item.get('description', 'Additional Cost')}**")
                
                with col2:
                    st.write(format_currency(cost_item.get('amount', 0)))
        
        # Payment schedule (if available)
        payment_schedule = blueprint_data.get('payment_schedule', [])
        if payment_schedule:
            st.markdown("### Suggested Payment Schedule")
            
            for payment in payment_schedule:
                due_date = payment.get('due_date', 'TBD')
                amount = payment.get('amount', 0)
                description = payment.get('description', 'Payment')
                
                st.write(f"📅 **{due_date}**: {format_currency(amount)} - {description}")
    
    def _render_contacts_section(self, blueprint_data: Dict):
        """Render the contacts section"""
        st.subheader("📞 Contact Directory")
        
        selected_combination = blueprint_data.get('selected_combination', {})
        
        # Emergency contacts
        st.markdown("### Emergency Contacts")
        st.info("Keep these contacts handy on the event day!")
        
        vendors = ['venue', 'caterer', 'photographer', 'makeup_artist']
        vendor_icons = {
            'venue': '🏛️',
            'caterer': '🍽️',
            'photographer': '📸', 
            'makeup_artist': '💄'
        }
        
        for vendor_type in vendors:
            vendor = selected_combination.get(vendor_type, {})
            if not vendor.get('name'):
                continue
            
            icon = vendor_icons.get(vendor_type, '📋')
            
            with st.container():
                st.markdown(f"""
                <div style="
                    border: 1px solid #dee2e6;
                    border-radius: 8px;
                    padding: 1rem;
                    margin-bottom: 1rem;
                    background-color: #ffffff;
                ">
                    <h4>{icon} {vendor['name']}</h4>
                    <p><strong>Phone:</strong> {vendor.get('contact_phone', 'N/A')}</p>
                    <p><strong>Email:</strong> {vendor.get('contact_email', 'N/A')}</p>
                    {f"<p><strong>Emergency:</strong> {vendor.get('emergency_contact', 'Same as above')}</p>" if vendor.get('emergency_contact') else ""}
                </div>
                """, unsafe_allow_html=True)
        
        # Download contact list
        if st.button("📱 Download Contact List", use_container_width=True, key="blueprint_download_contacts"):
            self._generate_contact_list(selected_combination)
    
    def _render_tasks_section(self, blueprint_data: Dict):
        """Render the extended task list section"""
        st.subheader("✅ Extended Task List")
        
        # Get plan ID
        plan_id = st.session_state.get('current_plan_id')
        
        if not plan_id:
            st.warning("No plan ID available.")
            return
        
        # Try to load extended task list
        try:
            with st.spinner("Loading extended task list..."):
                task_data = api_client.get_extended_task_list(plan_id)
            
            if not task_data or not task_data.get('tasks'):
                st.info("⏳ Tasks are being generated. This may take a few moments. Please check back shortly.")
                return
            
            tasks = task_data.get('tasks', [])
            conflicts = task_data.get('conflicts', [])
            
            # Display task summary
            st.markdown("### Task Summary")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_tasks = len(tasks)
                st.metric("Total Tasks", total_tasks)
            
            with col2:
                critical_tasks = len([t for t in tasks if t.get('priority') == 'Critical'])
                st.metric("Critical Tasks", critical_tasks)
            
            with col3:
                completed_tasks = len([t for t in tasks if t.get('status') == 'completed'])
                completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
                st.metric("Completed", f"{completion_rate:.0f}%")
            
            with col4:
                conflict_count = len(conflicts)
                st.metric("Conflicts", conflict_count, delta="⚠️" if conflict_count > 0 else "✅")
            
            # Display conflicts if any
            if conflicts:
                st.markdown("### ⚠️ Conflicts Detected")
                st.warning(f"Found {len(conflicts)} conflict(s) that need attention.")
                
                for conflict in conflicts[:5]:  # Show first 5 conflicts
                    severity = conflict.get('severity', 'Medium')
                    conflict_type = conflict.get('type', 'Unknown')
                    description = conflict.get('description', 'No description')
                    
                    severity_colors = {
                        'Critical': '🔴',
                        'High': '🟠',
                        'Medium': '🟡',
                        'Low': '🟢'
                    }
                    
                    severity_icon = severity_colors.get(severity, '🟡')
                    
                    with st.expander(f"{severity_icon} {conflict_type} - {severity} Severity"):
                        st.write(f"**Description:** {description}")
                        
                        # Show affected tasks
                        affected_tasks = conflict.get('affected_tasks', [])
                        if affected_tasks:
                            st.write("**Affected Tasks:**")
                            for task_id in affected_tasks:
                                task = next((t for t in tasks if t.get('id') == task_id), None)
                                if task:
                                    st.write(f"• {task.get('name', 'Unknown Task')}")
                        
                        # Show suggested resolution
                        resolution = conflict.get('suggested_resolution', '')
                        if resolution:
                            st.info(f"**Suggested Resolution:** {resolution}")
                
                if len(conflicts) > 5:
                    st.info(f"Showing 5 of {len(conflicts)} conflicts. View all conflicts in the Conflicts page.")
            
            # Display tasks organized by priority
            st.markdown("### Tasks by Priority")
            
            priority_order = ['Critical', 'High', 'Medium', 'Low']
            
            for priority in priority_order:
                priority_tasks = [t for t in tasks if t.get('priority') == priority]
                
                if not priority_tasks:
                    continue
                
                priority_icons = {
                    'Critical': '🔴',
                    'High': '🟠',
                    'Medium': '🟡',
                    'Low': '🟢'
                }
                
                icon = priority_icons.get(priority, '📋')
                
                with st.expander(f"{icon} {priority} Priority ({len(priority_tasks)} tasks)", expanded=(priority == 'Critical')):
                    for task in priority_tasks:
                        task_name = task.get('name', 'Unnamed Task')
                        task_description = task.get('description', '')
                        estimated_duration = task.get('estimated_duration', 'N/A')
                        status = task.get('status', 'pending')
                        
                        # Task card
                        status_emoji = {
                            'completed': '✅',
                            'in_progress': '🔄',
                            'pending': '⏳',
                            'blocked': '🚫'
                        }
                        
                        status_icon = status_emoji.get(status, '⏳')
                        
                        st.markdown(f"**{status_icon} {task_name}**")
                        
                        if task_description:
                            st.write(f"*{task_description}*")
                        
                        # Task details in columns
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.write(f"⏱️ Duration: {estimated_duration}")
                        
                        with col2:
                            start_date = task.get('start_date', 'TBD')
                            st.write(f"📅 Start: {start_date}")
                        
                        with col3:
                            end_date = task.get('end_date', 'TBD')
                            st.write(f"🏁 End: {end_date}")
                        
                        # Vendor assignment
                        vendor = task.get('assigned_vendor', {})
                        if vendor and vendor.get('name'):
                            st.write(f"👤 **Vendor:** {vendor['name']} ({vendor.get('type', 'N/A')})")
                        
                        # Dependencies
                        dependencies = task.get('dependencies', [])
                        if dependencies:
                            st.write(f"🔗 **Dependencies:** {', '.join(dependencies)}")
                        
                        # Logistics status
                        logistics = task.get('logistics', {})
                        if logistics:
                            logistics_status = []
                            
                            if logistics.get('transportation_verified'):
                                logistics_status.append("✅ Transportation")
                            elif logistics.get('transportation_required'):
                                logistics_status.append("⚠️ Transportation needed")
                            
                            if logistics.get('equipment_verified'):
                                logistics_status.append("✅ Equipment")
                            elif logistics.get('equipment_required'):
                                logistics_status.append("⚠️ Equipment needed")
                            
                            if logistics.get('setup_verified'):
                                logistics_status.append("✅ Setup")
                            elif logistics.get('setup_required'):
                                logistics_status.append("⚠️ Setup needed")
                            
                            if logistics_status:
                                st.write(f"🚚 **Logistics:** {' | '.join(logistics_status)}")
                        
                        st.markdown("---")
            
            # Link to detailed task pages
            st.markdown("### View More Details")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📋 Full Task List", use_container_width=True, key="blueprint_goto_tasks"):
                    st.session_state.current_page = "task_list"
                    st.rerun()
            
            with col2:
                if st.button("📊 Timeline View", use_container_width=True, key="blueprint_goto_timeline"):
                    st.session_state.current_page = "timeline_view"
                    st.rerun()
            
            with col3:
                if st.button("⚠️ Resolve Conflicts", use_container_width=True, key="blueprint_goto_conflicts"):
                    st.session_state.current_page = "conflicts"
                    st.rerun()
        
        except APIError as e:
            if e.status_code == 404:
                st.info("⏳ Extended task list is being generated. This process may take a few moments.")
                st.write("The task list will include:")
                st.write("• Detailed task breakdown with priorities")
                st.write("• Vendor assignments for each task")
                st.write("• Task dependencies and timeline")
                st.write("• Logistics requirements and status")
                st.write("• Conflict detection and resolution suggestions")
                
                if st.button("🔄 Check Again", key="blueprint_refresh_tasks"):
                    st.rerun()
            else:
                st.error(f"Failed to load task list: {str(e)}")
                st.write("⚠️ Note: Task information may be incomplete or unavailable.")
        
        except Exception as e:
            st.error(f"Unexpected error loading tasks: {str(e)}")
            st.write("⚠️ Note: Task information may be incomplete or unavailable.")
    
    def _render_next_steps_section(self, blueprint_data: Dict):
        """Render the next steps and action items"""
        st.subheader("🎯 Next Steps")
        
        # Generate next steps based on timeline and current date
        next_steps = self._generate_next_steps(blueprint_data)
        
        if next_steps:
            st.markdown("### Immediate Action Items")
            
            for i, step in enumerate(next_steps, 1):
                priority = step.get('priority', 'medium')
                task = step.get('task', '')
                deadline = step.get('deadline', '')
                responsible = step.get('responsible', 'Client')
                
                # Priority color coding
                priority_colors = {
                    'high': '🔴',
                    'medium': '🟡', 
                    'low': '🟢'
                }
                
                priority_icon = priority_colors.get(priority, '🟡')
                
                with st.container():
                    col1, col2 = st.columns([4, 1])
                    
                    with col1:
                        st.markdown(f"{priority_icon} **{i}. {task}**")
                        if deadline:
                            st.write(f"   ⏰ **Deadline:** {deadline}")
                        if responsible:
                            st.write(f"   👤 **Responsible:** {responsible}")
                    
                    with col2:
                        if st.button("✅ Done", key=f"step_{i}"):
                            st.success(f"Marked step {i} as complete!")
        
        # Additional recommendations
        st.markdown("### Recommendations")
        recommendations = [
            "📋 Create a detailed day-of timeline with your vendors",
            "📞 Confirm all vendor details 1 week before the event",
            "🎁 Prepare vendor tip envelopes in advance",
            "📸 Share your photography shot list with the photographer",
            "🍽️ Confirm final guest count with the caterer 48 hours prior",
            "🚗 Arrange transportation and parking logistics",
            "💄 Schedule a makeup trial if not already done"
        ]
        
        for rec in recommendations:
            st.write(rec)
        
        # Final actions
        st.markdown("### Final Actions")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 Regenerate Blueprint", use_container_width=True, key="blueprint_regenerate"):
                # Clear cached blueprint and reload
                if 'plan_blueprint' in st.session_state:
                    del st.session_state['plan_blueprint']
                st.rerun()
        
        with col2:
            if st.button("📝 Create New Plan", use_container_width=True, key="blueprint_create_new"):
                st.session_state.current_page = "create_plan"
                st.rerun()
        
        with col3:
            if st.button("🏠 Back to Home", use_container_width=True, key="blueprint_back_home"):
                st.session_state.current_page = "home"
                st.rerun()
    
    def _generate_key_highlights(self, blueprint_data: Dict) -> List[str]:
        """Generate key highlights for the event"""
        highlights = []
        
        selected_combination = blueprint_data.get('selected_combination', {})
        event_info = blueprint_data.get('event_info', {})
        
        # Fitness score highlight
        fitness_score = selected_combination.get('fitness_score', 0)
        if fitness_score >= 90:
            highlights.append(f"Excellent vendor match with {fitness_score:.1f}% fitness score")
        elif fitness_score >= 75:
            highlights.append(f"Great vendor combination with {fitness_score:.1f}% compatibility")
        
        # Budget highlight
        total_cost = selected_combination.get('total_cost', 0)
        budget = event_info.get('budget', 0)
        if budget > 0:
            if total_cost <= budget * 0.95:
                savings = budget - total_cost
                highlights.append(f"Under budget by {format_currency(savings)}")
            elif total_cost <= budget:
                highlights.append("Plan fits perfectly within budget")
        
        # Venue highlight
        venue = selected_combination.get('venue', {})
        if venue.get('name'):
            highlights.append(f"Beautiful venue: {venue['name']}")
        
        # Special features
        caterer = selected_combination.get('caterer', {})
        if caterer.get('cuisine_types'):
            cuisine = caterer['cuisine_types'][0] if caterer['cuisine_types'] else 'specialty'
            highlights.append(f"Delicious {cuisine} cuisine included")
        
        return highlights[:5]  # Limit to 5 highlights
    
    def _generate_next_steps(self, blueprint_data: Dict) -> List[Dict]:
        """Generate next steps based on event timeline"""
        next_steps = []
        
        event_info = blueprint_data.get('event_info', {})
        event_date_str = event_info.get('event_date', '')
        
        # Default next steps
        steps = [
            {
                'task': 'Contact all vendors to confirm details and timeline',
                'priority': 'high',
                'deadline': 'Within 2 days',
                'responsible': 'Client'
            },
            {
                'task': 'Finalize guest count and dietary restrictions',
                'priority': 'high', 
                'deadline': '1 week before event',
                'responsible': 'Client'
            },
            {
                'task': 'Create detailed day-of timeline with vendors',
                'priority': 'medium',
                'deadline': '1 week before event',
                'responsible': 'Client + Vendors'
            },
            {
                'task': 'Prepare vendor payments and tip envelopes',
                'priority': 'medium',
                'deadline': '2 days before event',
                'responsible': 'Client'
            },
            {
                'task': 'Confirm setup and breakdown logistics',
                'priority': 'medium',
                'deadline': '3 days before event',
                'responsible': 'Venue + Vendors'
            }
        ]
        
        return steps
    
    def _export_blueprint(self, blueprint_data: Dict, format_type: str):
        """Export blueprint in the specified format"""
        try:
            if format_type == "PDF":
                self._export_pdf(blueprint_data)
            elif format_type == "JSON":
                self._export_json(blueprint_data)
            elif format_type == "Text":
                self._export_text(blueprint_data)
            elif format_type == "HTML":
                self._export_html(blueprint_data)
            else:
                show_error(f"Unsupported export format: {format_type}")
                
        except Exception as e:
            show_error(f"Export failed: {str(e)}")
    
    def _export_pdf(self, blueprint_data: Dict):
        """Export blueprint as PDF"""
        try:
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.lib import colors
            
            # Create PDF buffer
            buffer = BytesIO()
            
            # Create document
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            styles = getSampleStyleSheet()
            story = []
            
            # Title
            event_info = blueprint_data.get('event_info', {})
            title = f"Event Blueprint: {event_info.get('event_type', 'Event')} for {event_info.get('client_name', 'Client')}"
            story.append(Paragraph(title, styles['Title']))
            story.append(Spacer(1, 12))
            
            # Event details
            story.append(Paragraph("Event Details", styles['Heading1']))
            details = [
                f"Date: {event_info.get('event_date', 'TBD')}",
                f"Guest Count: {event_info.get('guest_count', 'TBD')}",
                f"Budget: {format_currency(event_info.get('budget', 0))}",
                f"Location: {event_info.get('location', 'TBD')}"
            ]
            
            for detail in details:
                story.append(Paragraph(detail, styles['Normal']))
            
            story.append(Spacer(1, 12))
            
            # Vendor information
            story.append(Paragraph("Selected Vendors", styles['Heading1']))
            
            selected_combination = blueprint_data.get('selected_combination', {})
            vendors = ['venue', 'caterer', 'photographer', 'makeup_artist']
            
            for vendor_type in vendors:
                vendor = selected_combination.get(vendor_type, {})
                if vendor.get('name'):
                    story.append(Paragraph(f"{vendor_type.replace('_', ' ').title()}: {vendor['name']}", styles['Heading2']))
                    story.append(Paragraph(f"Cost: {format_currency(vendor.get('cost', 0))}", styles['Normal']))
                    story.append(Paragraph(f"Contact: {vendor.get('contact_phone', 'N/A')}", styles['Normal']))
                    story.append(Spacer(1, 6))
            
            # Add task list section
            story.append(Spacer(1, 12))
            story.append(Paragraph("Extended Task List", styles['Heading1']))
            
            plan_id = st.session_state.get('current_plan_id')
            if plan_id:
                try:
                    task_data = api_client.get_extended_task_list(plan_id)
                    tasks = task_data.get('tasks', [])
                    conflicts = task_data.get('conflicts', [])
                    
                    if tasks:
                        # Task summary
                        total_tasks = len(tasks)
                        critical_tasks = len([t for t in tasks if t.get('priority') == 'Critical'])
                        completed_tasks = len([t for t in tasks if t.get('status') == 'completed'])
                        
                        story.append(Paragraph(f"Total Tasks: {total_tasks}", styles['Normal']))
                        story.append(Paragraph(f"Critical Tasks: {critical_tasks}", styles['Normal']))
                        story.append(Paragraph(f"Completed: {completed_tasks} ({completed_tasks/total_tasks*100:.0f}%)", styles['Normal']))
                        story.append(Spacer(1, 6))
                        
                        # Conflicts
                        if conflicts:
                            story.append(Paragraph(f"Conflicts Detected: {len(conflicts)}", styles['Heading2']))
                            for conflict in conflicts[:5]:
                                severity = conflict.get('severity', 'Medium')
                                conflict_type = conflict.get('type', 'Unknown')
                                description = conflict.get('description', 'No description')
                                story.append(Paragraph(f"• [{severity}] {conflict_type}: {description}", styles['Normal']))
                            story.append(Spacer(1, 6))
                        
                        # Tasks by priority
                        for priority in ['Critical', 'High', 'Medium', 'Low']:
                            priority_tasks = [t for t in tasks if t.get('priority') == priority]
                            if priority_tasks:
                                story.append(Paragraph(f"{priority} Priority Tasks ({len(priority_tasks)})", styles['Heading2']))
                                for task in priority_tasks[:10]:  # Limit to 10 per priority
                                    task_name = task.get('name', 'Unnamed Task')
                                    vendor = task.get('assigned_vendor', {})
                                    vendor_name = vendor.get('name', 'Unassigned')
                                    story.append(Paragraph(f"• {task_name} - Vendor: {vendor_name}", styles['Normal']))
                                story.append(Spacer(1, 6))
                    else:
                        story.append(Paragraph("Tasks are being generated. Please check back shortly.", styles['Normal']))
                
                except APIError:
                    story.append(Paragraph("Task information is being generated and will be available shortly.", styles['Normal']))
                except Exception:
                    story.append(Paragraph("Note: Task information may be incomplete or unavailable.", styles['Normal']))
            
            # Build PDF
            doc.build(story)
            
            # Prepare download
            buffer.seek(0)
            
            # Generate filename
            client_name = event_info.get('client_name', 'Client').replace(' ', '_')
            event_type = event_info.get('event_type', 'Event').replace(' ', '_')
            filename = f"{client_name}_{event_type}_Blueprint.pdf"
            
            # Create download button
            st.download_button(
                label="📄 Download PDF Blueprint",
                data=buffer.getvalue(),
                file_name=filename,
                mime="application/pdf"
            )
            
            show_success("PDF blueprint generated successfully!")
            
        except ImportError:
            show_error("PDF export requires reportlab. Please install it: pip install reportlab")
        except Exception as e:
            show_error(f"PDF export failed: {str(e)}")
    
    def _export_json(self, blueprint_data: Dict):
        """Export blueprint as JSON"""
        try:
            # Clean and format the data
            export_data = {
                'export_info': {
                    'generated_at': datetime.now().isoformat(),
                    'format': 'JSON',
                    'version': '1.0'
                },
                'blueprint': blueprint_data
            }
            
            # Add task data if available
            plan_id = st.session_state.get('current_plan_id')
            if plan_id:
                try:
                    task_data = api_client.get_extended_task_list(plan_id)
                    export_data['extended_task_list'] = task_data
                except APIError:
                    export_data['extended_task_list'] = {
                        'status': 'generating',
                        'message': 'Task list is being generated'
                    }
                except Exception:
                    export_data['extended_task_list'] = {
                        'status': 'unavailable',
                        'message': 'Task information may be incomplete'
                    }
            
            # Convert to JSON
            json_data = json.dumps(export_data, indent=2, default=str)
            
            # Generate filename
            event_info = blueprint_data.get('event_info', {})
            client_name = event_info.get('client_name', 'Client').replace(' ', '_')
            event_type = event_info.get('event_type', 'Event').replace(' ', '_')
            filename = f"{client_name}_{event_type}_Blueprint.json"
            
            # Create download button
            st.download_button(
                label="📊 Download JSON Blueprint",
                data=json_data,
                file_name=filename,
                mime="application/json"
            )
            
            show_success("JSON blueprint generated successfully!")
            
        except Exception as e:
            show_error(f"JSON export failed: {str(e)}")
    
    def _export_text(self, blueprint_data: Dict):
        """Export blueprint as formatted text"""
        try:
            # Generate text content
            lines = []
            
            # Header
            event_info = blueprint_data.get('event_info', {})
            lines.append("=" * 60)
            lines.append(f"EVENT BLUEPRINT")
            lines.append("=" * 60)
            lines.append("")
            lines.append(f"Event: {event_info.get('event_type', 'Event')}")
            lines.append(f"Client: {event_info.get('client_name', 'Client')}")
            lines.append(f"Date: {event_info.get('event_date', 'TBD')}")
            lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append("")
            
            # Event details
            lines.append("EVENT DETAILS")
            lines.append("-" * 20)
            lines.append(f"Guest Count: {event_info.get('guest_count', 'TBD')}")
            lines.append(f"Budget: {format_currency(event_info.get('budget', 0))}")
            lines.append(f"Location: {event_info.get('location', 'TBD')}")
            lines.append("")
            
            # Vendors
            lines.append("SELECTED VENDORS")
            lines.append("-" * 20)
            
            selected_combination = blueprint_data.get('selected_combination', {})
            vendors = ['venue', 'caterer', 'photographer', 'makeup_artist']
            
            for vendor_type in vendors:
                vendor = selected_combination.get(vendor_type, {})
                if vendor.get('name'):
                    lines.append(f"{vendor_type.replace('_', ' ').title()}:")
                    lines.append(f"  Name: {vendor['name']}")
                    lines.append(f"  Cost: {format_currency(vendor.get('cost', 0))}")
                    lines.append(f"  Phone: {vendor.get('contact_phone', 'N/A')}")
                    lines.append(f"  Email: {vendor.get('contact_email', 'N/A')}")
                    lines.append("")
            
            # Total cost
            total_cost = selected_combination.get('total_cost', 0)
            lines.append(f"TOTAL COST: {format_currency(total_cost)}")
            lines.append("")
            
            # Add task list section
            lines.append("EXTENDED TASK LIST")
            lines.append("-" * 20)
            
            plan_id = st.session_state.get('current_plan_id')
            if plan_id:
                try:
                    task_data = api_client.get_extended_task_list(plan_id)
                    tasks = task_data.get('tasks', [])
                    conflicts = task_data.get('conflicts', [])
                    
                    if tasks:
                        # Task summary
                        total_tasks = len(tasks)
                        critical_tasks = len([t for t in tasks if t.get('priority') == 'Critical'])
                        completed_tasks = len([t for t in tasks if t.get('status') == 'completed'])
                        
                        lines.append(f"Total Tasks: {total_tasks}")
                        lines.append(f"Critical Tasks: {critical_tasks}")
                        lines.append(f"Completed: {completed_tasks} ({completed_tasks/total_tasks*100:.0f}%)")
                        lines.append("")
                        
                        # Conflicts
                        if conflicts:
                            lines.append(f"CONFLICTS DETECTED: {len(conflicts)}")
                            lines.append("")
                            for conflict in conflicts:
                                severity = conflict.get('severity', 'Medium')
                                conflict_type = conflict.get('type', 'Unknown')
                                description = conflict.get('description', 'No description')
                                lines.append(f"  [{severity}] {conflict_type}")
                                lines.append(f"    {description}")
                                
                                resolution = conflict.get('suggested_resolution', '')
                                if resolution:
                                    lines.append(f"    Resolution: {resolution}")
                                lines.append("")
                        
                        # Tasks by priority
                        for priority in ['Critical', 'High', 'Medium', 'Low']:
                            priority_tasks = [t for t in tasks if t.get('priority') == priority]
                            if priority_tasks:
                                lines.append(f"{priority.upper()} PRIORITY TASKS ({len(priority_tasks)})")
                                lines.append("")
                                for task in priority_tasks:
                                    task_name = task.get('name', 'Unnamed Task')
                                    task_description = task.get('description', '')
                                    estimated_duration = task.get('estimated_duration', 'N/A')
                                    start_date = task.get('start_date', 'TBD')
                                    end_date = task.get('end_date', 'TBD')
                                    status = task.get('status', 'pending')
                                    
                                    lines.append(f"  • {task_name}")
                                    if task_description:
                                        lines.append(f"    Description: {task_description}")
                                    lines.append(f"    Duration: {estimated_duration} | Start: {start_date} | End: {end_date}")
                                    lines.append(f"    Status: {status}")
                                    
                                    # Vendor
                                    vendor = task.get('assigned_vendor', {})
                                    if vendor and vendor.get('name'):
                                        lines.append(f"    Vendor: {vendor['name']} ({vendor.get('type', 'N/A')})")
                                    
                                    # Dependencies
                                    dependencies = task.get('dependencies', [])
                                    if dependencies:
                                        lines.append(f"    Dependencies: {', '.join(dependencies)}")
                                    
                                    lines.append("")
                    else:
                        lines.append("Tasks are being generated. Please check back shortly.")
                        lines.append("")
                
                except APIError:
                    lines.append("Task information is being generated and will be available shortly.")
                    lines.append("")
                except Exception:
                    lines.append("Note: Task information may be incomplete or unavailable.")
                    lines.append("")
            
            # Footer
            lines.append("=" * 60)
            lines.append("Generated by Event Planning Agent v2")
            lines.append("=" * 60)
            
            # Join lines
            text_content = "\n".join(lines)
            
            # Generate filename
            client_name = event_info.get('client_name', 'Client').replace(' ', '_')
            event_type = event_info.get('event_type', 'Event').replace(' ', '_')
            filename = f"{client_name}_{event_type}_Blueprint.txt"
            
            # Create download button
            st.download_button(
                label="📝 Download Text Blueprint",
                data=text_content,
                file_name=filename,
                mime="text/plain"
            )
            
            show_success("Text blueprint generated successfully!")
            
        except Exception as e:
            show_error(f"Text export failed: {str(e)}")
    
    def _export_html(self, blueprint_data: Dict):
        """Export blueprint as HTML"""
        try:
            # Generate HTML content
            event_info = blueprint_data.get('event_info', {})
            selected_combination = blueprint_data.get('selected_combination', {})
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Event Blueprint - {event_info.get('client_name', 'Client')}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; }}
                    .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                             color: white; padding: 20px; border-radius: 10px; text-align: center; }}
                    .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 8px; }}
                    .vendor {{ background-color: #f8f9fa; margin: 10px 0; padding: 15px; border-radius: 5px; }}
                    .task {{ background-color: #fff; margin: 10px 0; padding: 10px; border-left: 4px solid #007bff; }}
                    .task.critical {{ border-left-color: #dc3545; }}
                    .task.high {{ border-left-color: #fd7e14; }}
                    .task.medium {{ border-left-color: #ffc107; }}
                    .task.low {{ border-left-color: #28a745; }}
                    .conflict {{ background-color: #fff3cd; padding: 10px; margin: 10px 0; border-left: 4px solid #ffc107; }}
                    .cost {{ font-weight: bold; color: #007bff; }}
                    .total {{ font-size: 1.2em; font-weight: bold; color: #28a745; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>🎉 {event_info.get('event_type', 'Event')}</h1>
                    <h2>for {event_info.get('client_name', 'Client')}</h2>
                    <p>📅 {event_info.get('event_date', 'TBD')}</p>
                </div>
                
                <div class="section">
                    <h2>Event Details</h2>
                    <p><strong>Guest Count:</strong> {event_info.get('guest_count', 'TBD')}</p>
                    <p><strong>Budget:</strong> {format_currency(event_info.get('budget', 0))}</p>
                    <p><strong>Location:</strong> {event_info.get('location', 'TBD')}</p>
                </div>
                
                <div class="section">
                    <h2>Selected Vendors</h2>
            """
            
            # Add vendor information
            vendors = ['venue', 'caterer', 'photographer', 'makeup_artist']
            vendor_icons = {'venue': '🏛️', 'caterer': '🍽️', 'photographer': '📸', 'makeup_artist': '💄'}
            
            for vendor_type in vendors:
                vendor = selected_combination.get(vendor_type, {})
                if vendor.get('name'):
                    icon = vendor_icons.get(vendor_type, '📋')
                    html_content += f"""
                    <div class="vendor">
                        <h3>{icon} {vendor_type.replace('_', ' ').title()}</h3>
                        <p><strong>Name:</strong> {vendor['name']}</p>
                        <p><strong>Cost:</strong> <span class="cost">{format_currency(vendor.get('cost', 0))}</span></p>
                        <p><strong>Phone:</strong> {vendor.get('contact_phone', 'N/A')}</p>
                        <p><strong>Email:</strong> {vendor.get('contact_email', 'N/A')}</p>
                    </div>
                    """
            
            # Add total cost
            total_cost = selected_combination.get('total_cost', 0)
            html_content += f"""
                </div>
                
                <div class="section">
                    <h2>Summary</h2>
                    <p class="total">Total Investment: {format_currency(total_cost)}</p>
                    <p><strong>Fitness Score:</strong> {selected_combination.get('fitness_score', 0):.1f}%</p>
                </div>
            """
            
            # Add task list section
            plan_id = st.session_state.get('current_plan_id')
            if plan_id:
                try:
                    task_data = api_client.get_extended_task_list(plan_id)
                    tasks = task_data.get('tasks', [])
                    conflicts = task_data.get('conflicts', [])
                    
                    if tasks:
                        html_content += """
                <div class="section">
                    <h2>Extended Task List</h2>
                        """
                        
                        # Task summary
                        total_tasks = len(tasks)
                        critical_tasks = len([t for t in tasks if t.get('priority') == 'Critical'])
                        completed_tasks = len([t for t in tasks if t.get('status') == 'completed'])
                        
                        html_content += f"""
                    <p><strong>Total Tasks:</strong> {total_tasks}</p>
                    <p><strong>Critical Tasks:</strong> {critical_tasks}</p>
                    <p><strong>Completed:</strong> {completed_tasks} ({completed_tasks/total_tasks*100:.0f}%)</p>
                        """
                        
                        # Conflicts
                        if conflicts:
                            html_content += f"""
                    <h3>⚠️ Conflicts Detected ({len(conflicts)})</h3>
                            """
                            for conflict in conflicts[:5]:
                                severity = conflict.get('severity', 'Medium')
                                conflict_type = conflict.get('type', 'Unknown')
                                description = conflict.get('description', 'No description')
                                resolution = conflict.get('suggested_resolution', '')
                                
                                html_content += f"""
                    <div class="conflict">
                        <strong>[{severity}] {conflict_type}</strong><br>
                        {description}<br>
                        {f'<em>Resolution: {resolution}</em>' if resolution else ''}
                    </div>
                                """
                        
                        # Tasks by priority
                        for priority in ['Critical', 'High', 'Medium', 'Low']:
                            priority_tasks = [t for t in tasks if t.get('priority') == priority]
                            if priority_tasks:
                                html_content += f"""
                    <h3>{priority} Priority Tasks ({len(priority_tasks)})</h3>
                                """
                                for task in priority_tasks[:10]:  # Limit to 10 per priority
                                    task_name = task.get('name', 'Unnamed Task')
                                    task_description = task.get('description', '')
                                    estimated_duration = task.get('estimated_duration', 'N/A')
                                    vendor = task.get('assigned_vendor', {})
                                    vendor_name = vendor.get('name', 'Unassigned')
                                    
                                    html_content += f"""
                    <div class="task {priority.lower()}">
                        <strong>{task_name}</strong><br>
                        {f'{task_description}<br>' if task_description else ''}
                        <small>Duration: {estimated_duration} | Vendor: {vendor_name}</small>
                    </div>
                                    """
                        
                        html_content += """
                </div>
                        """
                    else:
                        html_content += """
                <div class="section">
                    <h2>Extended Task List</h2>
                    <p>Tasks are being generated. Please check back shortly.</p>
                </div>
                        """
                
                except APIError:
                    html_content += """
                <div class="section">
                    <h2>Extended Task List</h2>
                    <p>Task information is being generated and will be available shortly.</p>
                </div>
                    """
                except Exception:
                    html_content += """
                <div class="section">
                    <h2>Extended Task List</h2>
                    <p>Note: Task information may be incomplete or unavailable.</p>
                </div>
                    """
            
            html_content += f"""
                <div class="section">
                    <p><em>Generated by Event Planning Agent v2 on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</em></p>
                </div>
            </body>
            </html>
            """
            
            # Generate filename
            client_name = event_info.get('client_name', 'Client').replace(' ', '_')
            event_type = event_info.get('event_type', 'Event').replace(' ', '_')
            filename = f"{client_name}_{event_type}_Blueprint.html"
            
            # Create download button
            st.download_button(
                label="🌐 Download HTML Blueprint",
                data=html_content,
                file_name=filename,
                mime="text/html"
            )
            
            show_success("HTML blueprint generated successfully!")
            
        except Exception as e:
            show_error(f"HTML export failed: {str(e)}")
    
    def _show_email_dialog(self, blueprint_data: Dict):
        """Show email sharing dialog"""
        st.subheader("📧 Email Blueprint")
        
        with st.form("email_form"):
            recipient_email = st.text_input("Recipient Email", placeholder="client@example.com")
            subject = st.text_input("Subject", value=f"Your Event Blueprint - {blueprint_data.get('event_info', {}).get('event_type', 'Event')}")
            
            message = st.text_area(
                "Message",
                value="Please find attached your event blueprint with all the details for your upcoming event. If you have any questions, please don't hesitate to reach out!",
                height=100
            )
            
            include_attachments = st.multiselect(
                "Include Attachments",
                options=["PDF Blueprint", "Contact List", "Timeline"],
                default=["PDF Blueprint"]
            )
            
            if st.form_submit_button("Send Email"):
                if recipient_email:
                    # In a real implementation, this would send the email
                    show_info(f"Email would be sent to {recipient_email} with selected attachments.")
                    st.info("Email functionality requires SMTP configuration. This is a demo.")
                else:
                    show_error("Please enter a recipient email address.")
    
    def _generate_contact_list(self, selected_combination: Dict):
        """Generate and download contact list"""
        try:
            # Generate contact list content
            lines = []
            lines.append("EVENT VENDOR CONTACTS")
            lines.append("=" * 30)
            lines.append("")
            
            vendors = ['venue', 'caterer', 'photographer', 'makeup_artist']
            vendor_icons = {'venue': '🏛️', 'caterer': '🍽️', 'photographer': '📸', 'makeup_artist': '💄'}
            
            for vendor_type in vendors:
                vendor = selected_combination.get(vendor_type, {})
                if vendor.get('name'):
                    icon = vendor_icons.get(vendor_type, '📋')
                    lines.append(f"{icon} {vendor_type.replace('_', ' ').title().upper()}")
                    lines.append(f"Name: {vendor['name']}")
                    lines.append(f"Phone: {vendor.get('contact_phone', 'N/A')}")
                    lines.append(f"Email: {vendor.get('contact_email', 'N/A')}")
                    
                    if vendor.get('emergency_contact'):
                        lines.append(f"Emergency: {vendor['emergency_contact']}")
                    
                    lines.append("")
            
            lines.append("=" * 30)
            lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            contact_list = "\n".join(lines)
            
            # Create download button
            st.download_button(
                label="📱 Download Contact List",
                data=contact_list,
                file_name="Event_Vendor_Contacts.txt",
                mime="text/plain"
            )
            
            show_success("Contact list generated successfully!")
            
        except Exception as e:
            show_error(f"Failed to generate contact list: {str(e)}")