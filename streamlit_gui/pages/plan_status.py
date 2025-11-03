"""
Plan Status page for Event Planning Agent v2 GUI
Real-time progress tracking and workflow monitoring
"""
import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, Optional
import time

from components.progress import (
    render_progress_page,
    RealTimeStatusUpdater,
    WorkflowSteps,
    ProgressBar,
    AgentActivityDisplay,
    ErrorDisplay,
    WorkflowController
)
from components.api_client import api_client, APIError
from utils.helpers import show_error, show_success, show_warning, show_info
from utils.config import config

def render_plan_status_page():
    """Main function to render the plan status page"""
    
    st.title("📊 Plan Status & Progress Monitoring")
    
    # Check if we have an active plan
    current_plan_id = st.session_state.get('current_plan_id')
    
    if not current_plan_id:
        render_no_active_plan()
        return
    
    # Initialize session state for monitoring
    if 'monitoring_initialized' not in st.session_state:
        st.session_state.monitoring_initialized = True
        st.session_state.monitoring_active = True
        st.session_state.last_status_check = None
        st.session_state.status_check_count = 0
        st.session_state.monitoring_errors = []
    
    # Render the main progress tracking interface
    render_main_progress_interface(current_plan_id)

def render_no_active_plan():
    """Render interface when no active plan exists"""
    
    st.info("👋 No active plan found. You can:")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Start New Plan")
        st.markdown("Create a new event plan to begin the planning process.")
        
        if st.button("➕ Create New Plan", type="primary", use_container_width=True, key="status_create_new_plan"):
            st.session_state.current_page = 'create_plan'
            st.rerun()
    
    with col2:
        st.markdown("### Load Existing Plan")
        st.markdown("Enter a plan ID to monitor an existing planning process.")
        
        plan_id_input = st.text_input(
            "Plan ID",
            placeholder="Enter plan ID...",
            key="load_plan_id"
        )
        
        if st.button("📋 Load Plan", use_container_width=True, key="status_load_plan"):
            if plan_id_input.strip():
                load_existing_plan(plan_id_input.strip())
            else:
                show_error("Please enter a valid plan ID")
    
    # Show recent plans if available
    render_recent_plans_section()

def load_existing_plan(plan_id: str):
    """Load an existing plan for monitoring"""
    
    try:
        # Verify plan exists and get status
        status_data = api_client.get_plan_status(plan_id)
        
        # Update session state
        st.session_state.current_plan_id = plan_id
        st.session_state.plan_status = status_data.get('status')
        st.session_state.plan_data = status_data
        
        show_success(f"Successfully loaded plan: {plan_id}")
        st.rerun()
        
    except APIError as e:
        if e.status_code == 404:
            show_error(f"Plan not found: {plan_id}")
        else:
            show_error(f"Failed to load plan: {str(e)}")
    except Exception as e:
        show_error(f"Unexpected error loading plan: {str(e)}")

def render_recent_plans_section():
    """Render section showing recent plans"""
    
    try:
        # Get list of recent plans
        plans_data = api_client.list_plans(limit=5)
        plans = plans_data.get('plans', [])
        
        if plans:
            st.markdown("### 📋 Recent Plans")
            
            for plan in plans:
                plan_id = plan.get('id')
                status = plan.get('status', 'unknown')
                created_at = plan.get('created_at')
                client_name = plan.get('client_name', 'Unknown Client')
                
                with st.expander(f"Plan {plan_id} - {client_name} ({status})"):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.write(f"**Status:** {status}")
                        if created_at:
                            st.write(f"**Created:** {created_at}")
                        st.write(f"**Client:** {client_name}")
                    
                    with col2:
                        if st.button(f"Load Plan", key=f"load_{plan_id}"):
                            load_existing_plan(plan_id)
    
    except APIError:
        st.caption("Unable to load recent plans")
    except Exception:
        pass  # Silently fail for recent plans

def render_main_progress_interface(plan_id: str):
    """Render the main progress tracking interface"""
    
    # Plan header
    render_plan_header(plan_id)
    
    # Status updater
    updater = RealTimeStatusUpdater(plan_id, update_interval=2)
    
    # Control panel
    render_control_panel(updater)
    
    # Get current status
    status_data = get_current_status(plan_id, updater)
    
    if not status_data:
        render_status_error()
        return
    
    # Main progress display
    render_progress_display(status_data, plan_id)
    
    # Handle auto-refresh
    handle_auto_refresh(updater)

def render_plan_header(plan_id: str):
    """Render the plan header with basic information"""
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.markdown(f"### 📋 Plan: `{plan_id}`")
    
    with col2:
        # Plan actions
        if st.button("📊 View Results", key="view_results"):
            st.session_state.current_page = 'plan_results'
            st.rerun()
    
    with col3:
        # Navigation actions
        if st.button("🏠 Back to Home", key="back_home"):
            st.session_state.current_page = 'home'
            st.rerun()

def render_control_panel(updater: RealTimeStatusUpdater):
    """Render the monitoring control panel"""
    
    st.markdown("### 🎛️ Monitoring Controls")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Auto-refresh toggle
        monitoring_active = st.session_state.get('monitoring_active', False)
        
        if monitoring_active:
            if st.button("⏸️ Pause Auto-Refresh", key="pause_auto_refresh"):
                st.session_state.monitoring_active = False
                updater.stop_monitoring()
                show_info("Auto-refresh paused")
        else:
            if st.button("▶️ Start Auto-Refresh", key="start_auto_refresh"):
                st.session_state.monitoring_active = True
                updater.start_monitoring()
                show_info("Auto-refresh started")
    
    with col2:
        # Manual refresh
        if st.button("🔄 Refresh Now", key="manual_refresh"):
            status_data = updater.update_status()
            if status_data:
                show_success("Status updated")
            st.rerun()
    
    with col3:
        # Refresh interval
        refresh_interval = st.selectbox(
            "Refresh Interval",
            options=[1, 2, 5, 10, 30],
            index=1,  # Default to 2 seconds
            format_func=lambda x: f"{x}s",
            key="refresh_interval"
        )
        updater.update_interval = refresh_interval
    
    with col4:
        # Status indicator
        if st.session_state.get('monitoring_active', False):
            st.success("🟢 Monitoring Active")
        else:
            st.warning("🔴 Monitoring Paused")
    
    # Last update info
    last_update = st.session_state.get('last_status_check')
    if last_update:
        st.caption(f"Last updated: {last_update.strftime('%H:%M:%S')}")

def get_current_status(plan_id: str, updater: RealTimeStatusUpdater) -> Optional[Dict]:
    """Get current plan status with error handling"""
    
    try:
        status_data = updater.update_status()
        st.session_state.last_status_check = datetime.now()
        st.session_state.status_check_count = st.session_state.get('status_check_count', 0) + 1
        
        # Clear any previous errors
        if 'monitoring_errors' in st.session_state:
            st.session_state.monitoring_errors = []
        
        return status_data
        
    except APIError as e:
        error_msg = f"API Error: {str(e)}"
        st.session_state.monitoring_errors = st.session_state.get('monitoring_errors', [])
        st.session_state.monitoring_errors.append({
            'timestamp': datetime.now(),
            'error': error_msg,
            'type': 'api_error'
        })
        return None
        
    except Exception as e:
        error_msg = f"Unexpected Error: {str(e)}"
        st.session_state.monitoring_errors = st.session_state.get('monitoring_errors', [])
        st.session_state.monitoring_errors.append({
            'timestamp': datetime.now(),
            'error': error_msg,
            'type': 'system_error'
        })
        return None

def render_status_error():
    """Render error state when status cannot be retrieved"""
    
    st.error("❌ Unable to retrieve plan status")
    
    errors = st.session_state.get('monitoring_errors', [])
    
    if errors:
        latest_error = errors[-1]
        
        ErrorDisplay.render(
            error_message=latest_error['error'],
            error_type="error",
            show_retry=True,
            show_restart=True,
            retry_callback=lambda: st.rerun(),
            restart_callback=lambda: restart_monitoring()
        )
        
        # Show error history
        if len(errors) > 1:
            with st.expander(f"Error History ({len(errors)} errors)"):
                for i, error in enumerate(reversed(errors[-5:])):  # Show last 5 errors
                    st.write(f"**{error['timestamp'].strftime('%H:%M:%S')}** - {error['error']}")

def restart_monitoring():
    """Restart the monitoring process"""
    
    # Clear error state
    st.session_state.monitoring_errors = []
    st.session_state.monitoring_active = True
    st.session_state.last_status_check = None
    
    show_info("Monitoring restarted")
    st.rerun()

def render_progress_display(status_data: Dict, plan_id: str):
    """Render the main progress display components"""
    
    # Extract status information
    current_status = status_data.get('status', 'unknown')
    current_step = status_data.get('current_step', 'initialization')
    step_progress = status_data.get('step_progress', 0.0)
    active_agents = status_data.get('active_agents', [])
    last_activity = status_data.get('last_activity')
    error_message = status_data.get('error')
    workflow_data = status_data.get('workflow_data', {})
    
    # Calculate overall progress
    overall_progress = WorkflowSteps.calculate_progress_percentage(current_step, step_progress)
    
    # Status overview
    render_status_overview(current_status, overall_progress, workflow_data)
    
    st.markdown("---")
    
    # Progress bar with step indicators
    st.markdown("### 📊 Progress Overview")
    ProgressBar.render(
        progress=overall_progress,
        current_step=current_step,
        step_progress=step_progress,
        show_percentage=True,
        show_steps=True
    )
    
    st.markdown("---")
    
    # Agent activity display
    AgentActivityDisplay.render(
        current_step=current_step,
        active_agents=active_agents,
        last_activity=last_activity
    )
    
    st.markdown("---")
    
    # Detailed workflow information
    render_workflow_details(workflow_data, current_step)
    
    # Error handling
    if error_message:
        st.markdown("---")
        ErrorDisplay.render(
            error_message=error_message,
            error_type="error",
            show_retry=True,
            show_restart=True,
            retry_callback=lambda: st.rerun(),
            restart_callback=lambda: WorkflowController._restart_workflow(plan_id)
        )
    
    # Workflow controls
    st.markdown("---")
    WorkflowController.render_controls(plan_id, current_status)
    
    # Handle workflow completion
    handle_workflow_completion(current_status, plan_id)

def render_status_overview(status: str, progress: float, workflow_data: Dict):
    """Render high-level status overview"""
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Status indicator
        status_color = {
            'running': '🟢',
            'in_progress': '🟡',
            'completed': '✅',
            'failed': '❌',
            'cancelled': '⏹️',
            'pending': '⏳'
        }.get(status, '❓')
        
        st.metric("Status", f"{status_color} {status.title()}")
    
    with col2:
        # Overall progress
        st.metric("Progress", f"{progress:.1f}%")
    
    with col3:
        # Elapsed time
        start_time = workflow_data.get('start_time')
        if start_time:
            try:
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                elapsed = datetime.now() - start_dt.replace(tzinfo=None)
                elapsed_str = str(elapsed).split('.')[0]  # Remove microseconds
                st.metric("Elapsed Time", elapsed_str)
            except:
                st.metric("Elapsed Time", "Unknown")
        else:
            st.metric("Elapsed Time", "Not started")
    
    with col4:
        # Estimated remaining time
        current_step = workflow_data.get('current_step', 'initialization')
        step_info = WorkflowSteps.get_step_info(current_step)
        estimated_remaining = step_info.get('estimated_duration', 0)
        
        if estimated_remaining > 0:
            st.metric("Est. Remaining", f"{estimated_remaining}s")
        else:
            st.metric("Est. Remaining", "Unknown")

def render_workflow_details(workflow_data: Dict, current_step: str):
    """Render detailed workflow information"""
    
    st.markdown("### 📋 Workflow Details")
    
    # Current step details
    step_info = WorkflowSteps.get_step_info(current_step)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown(f"**Current Step:** {step_info['title']}")
        st.write(step_info['description'])
        
        # Step-specific information
        if workflow_data:
            render_step_specific_info(current_step, workflow_data)
    
    with col2:
        # Step statistics
        st.markdown("**Step Info:**")
        st.write(f"• **Agents:** {', '.join(step_info['agents'])}")
        st.write(f"• **Est. Duration:** {step_info['estimated_duration']}s")
        
        # Progress within step
        step_progress = workflow_data.get('step_progress', 0.0)
        if step_progress > 0:
            st.write(f"• **Step Progress:** {step_progress:.1f}%")

def render_step_specific_info(current_step: str, workflow_data: Dict):
    """Render information specific to the current workflow step"""
    
    if current_step == "budget_allocation":
        budget_info = workflow_data.get('budget_analysis', {})
        if budget_info:
            st.markdown("**Budget Analysis:**")
            total_budget = budget_info.get('total_budget')
            if total_budget:
                st.write(f"• Total Budget: ${total_budget:,.2f}")
            
            allocations = budget_info.get('allocations', {})
            for category, amount in allocations.items():
                st.write(f"• {category.title()}: ${amount:,.2f}")
    
    elif current_step == "vendor_sourcing":
        sourcing_info = workflow_data.get('sourcing_progress', {})
        if sourcing_info:
            st.markdown("**Sourcing Progress:**")
            for vendor_type, count in sourcing_info.items():
                st.write(f"• {vendor_type.title()}: {count} found")
    
    elif current_step == "beam_search":
        optimization_info = workflow_data.get('optimization_progress', {})
        if optimization_info:
            st.markdown("**Optimization Progress:**")
            combinations_evaluated = optimization_info.get('combinations_evaluated', 0)
            best_score = optimization_info.get('best_score', 0)
            st.write(f"• Combinations Evaluated: {combinations_evaluated}")
            st.write(f"• Best Score: {best_score:.2f}")

def handle_workflow_completion(status: str, plan_id: str):
    """Handle workflow completion states"""
    
    if status == "completed":
        st.success("🎉 **Workflow Completed Successfully!**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🎯 View Results", type="primary", use_container_width=True):
                st.session_state.current_page = 'plan_results'
                st.rerun()
        
        with col2:
            if st.button("📋 View Blueprint", use_container_width=True):
                st.session_state.current_page = 'plan_blueprint'
                st.rerun()
    
    elif status == "failed":
        st.error("❌ **Workflow Failed**")
        st.write("The planning process encountered an error and could not complete.")
        
        if st.button("🔁 Restart Workflow", type="primary", key="status_restart_workflow_failed"):
            WorkflowController._restart_workflow(plan_id)
    
    elif status == "cancelled":
        st.warning("⏹️ **Workflow Cancelled**")
        st.write("The planning process was cancelled by the user.")
        
        if st.button("🔁 Restart Workflow", type="primary", key="status_restart_workflow_cancelled"):
            WorkflowController._restart_workflow(plan_id)

def handle_auto_refresh(updater: RealTimeStatusUpdater):
    """Handle auto-refresh functionality"""
    
    if st.session_state.get('monitoring_active', False):
        # Add a small delay and rerun to create auto-refresh effect
        time.sleep(updater.update_interval)
        st.rerun()

# Main entry point
if __name__ == "__main__":
    render_plan_status_page()