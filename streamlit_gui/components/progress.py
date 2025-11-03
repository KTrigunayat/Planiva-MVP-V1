"""
Progress tracking components for Event Planning Agent v2 GUI
"""
import streamlit as st
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
import asyncio
from components.api_client import api_client, APIError
from utils.helpers import show_error, show_success, show_warning

class WorkflowSteps:
    """Define workflow steps and their display information"""
    
    STEPS = {
        "initialization": {
            "title": "🚀 Initializing Planning Process",
            "description": "Setting up the planning workflow and validating requirements",
            "agents": ["Orchestrator"],
            "estimated_duration": 30
        },
        "budget_allocation": {
            "title": "💰 Analyzing Budget Requirements",
            "description": "Analyzing budget constraints and allocation strategies",
            "agents": ["Budgeting Agent"],
            "estimated_duration": 60
        },
        "vendor_sourcing": {
            "title": "🔍 Sourcing Vendors",
            "description": "Finding and evaluating potential vendors",
            "agents": ["Sourcing Agent"],
            "estimated_duration": 120
        },
        "beam_search": {
            "title": "🎯 Optimizing Combinations",
            "description": "Finding optimal vendor combinations using beam search",
            "agents": ["Optimization Agent"],
            "estimated_duration": 90
        },
        "client_selection": {
            "title": "👤 Awaiting Selection",
            "description": "Waiting for client to select preferred combination",
            "agents": ["User Interface"],
            "estimated_duration": 0
        },
        "blueprint_generation": {
            "title": "📋 Generating Blueprint",
            "description": "Creating final event blueprint and timeline",
            "agents": ["Blueprint Agent"],
            "estimated_duration": 45
        }
    }
    
    @classmethod
    def get_step_info(cls, step_key: str) -> Dict:
        """Get information about a specific step"""
        return cls.STEPS.get(step_key, {
            "title": f"Unknown Step: {step_key}",
            "description": "Processing...",
            "agents": ["Unknown"],
            "estimated_duration": 60
        })
    
    @classmethod
    def get_step_order(cls) -> List[str]:
        """Get the ordered list of step keys"""
        return list(cls.STEPS.keys())
    
    @classmethod
    def get_step_index(cls, step_key: str) -> int:
        """Get the index of a step in the workflow"""
        try:
            return cls.get_step_order().index(step_key)
        except ValueError:
            return -1
    
    @classmethod
    def calculate_progress_percentage(cls, current_step: str, step_progress: float = 0.0) -> float:
        """Calculate overall progress percentage"""
        step_index = cls.get_step_index(current_step)
        if step_index == -1:
            return 0.0
        
        total_steps = len(cls.STEPS)
        base_progress = (step_index / total_steps) * 100
        step_contribution = (step_progress / total_steps)
        
        return min(100.0, base_progress + step_contribution)

class ProgressBar:
    """Enhanced progress bar component with step indicators"""
    
    @staticmethod
    def render(
        progress: float,
        current_step: str,
        step_progress: float = 0.0,
        show_percentage: bool = True,
        show_steps: bool = True
    ):
        """
        Render an enhanced progress bar with step indicators
        
        Args:
            progress: Overall progress percentage (0-100)
            current_step: Current workflow step key
            step_progress: Progress within current step (0-100)
            show_percentage: Whether to show percentage text
            show_steps: Whether to show step indicators
        """
        
        # Main progress bar
        col1, col2 = st.columns([4, 1])
        
        with col1:
            st.progress(progress / 100.0)
        
        with col2:
            if show_percentage:
                st.write(f"**{progress:.1f}%**")
        
        # Step indicators
        if show_steps:
            st.markdown("---")
            
            steps = WorkflowSteps.get_step_order()
            current_index = WorkflowSteps.get_step_index(current_step)
            
            # Create columns for each step
            cols = st.columns(len(steps))
            
            for i, (col, step_key) in enumerate(zip(cols, steps)):
                step_info = WorkflowSteps.get_step_info(step_key)
                
                with col:
                    # Determine step status
                    if i < current_index:
                        # Completed step
                        st.markdown(f"✅ **{step_info['title'].split(' ', 1)[1]}**")
                        st.caption("Completed")
                    elif i == current_index:
                        # Current step
                        st.markdown(f"🔄 **{step_info['title'].split(' ', 1)[1]}**")
                        if step_progress > 0:
                            st.caption(f"In Progress ({step_progress:.0f}%)")
                        else:
                            st.caption("In Progress")
                    else:
                        # Future step
                        st.markdown(f"⏳ {step_info['title'].split(' ', 1)[1]}")
                        st.caption("Pending")

class AgentActivityDisplay:
    """Component to display current agent activity"""
    
    AGENT_ICONS = {
        "Orchestrator": "🎭",
        "Budgeting Agent": "💰",
        "Sourcing Agent": "🔍",
        "Optimization Agent": "🎯",
        "Blueprint Agent": "📋",
        "User Interface": "👤",
        "Unknown": "🤖"
    }
    
    @staticmethod
    def render(current_step: str, active_agents: List[str] = None, last_activity: str = None):
        """
        Render agent activity display
        
        Args:
            current_step: Current workflow step
            active_agents: List of currently active agents
            last_activity: Description of last activity
        """
        
        step_info = WorkflowSteps.get_step_info(current_step)
        
        if active_agents is None:
            active_agents = step_info.get("agents", ["Unknown"])
        
        st.markdown("### 🤖 Agent Activity")
        
        # Current step info
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"**Current Step:** {step_info['title']}")
            st.caption(step_info['description'])
        
        with col2:
            # Estimated time remaining
            estimated_duration = step_info.get("estimated_duration", 60)
            if estimated_duration > 0:
                st.metric("Est. Duration", f"{estimated_duration}s")
        
        # Active agents
        st.markdown("**Active Agents:**")
        
        agent_cols = st.columns(min(len(active_agents), 4))
        
        for i, agent in enumerate(active_agents):
            col_index = i % len(agent_cols)
            with agent_cols[col_index]:
                icon = AgentActivityDisplay.AGENT_ICONS.get(agent, "🤖")
                st.markdown(f"{icon} **{agent}**")
                st.caption("Working...")
        
        # Last activity
        if last_activity:
            st.markdown("**Latest Activity:**")
            st.info(last_activity)

class ErrorDisplay:
    """Component for displaying errors with recovery options"""
    
    @staticmethod
    def render(
        error_message: str,
        error_type: str = "error",
        show_retry: bool = True,
        show_restart: bool = True,
        retry_callback: Callable = None,
        restart_callback: Callable = None
    ):
        """
        Render error display with recovery options
        
        Args:
            error_message: The error message to display
            error_type: Type of error (error, warning, info)
            show_retry: Whether to show retry button
            show_restart: Whether to show restart button
            retry_callback: Function to call on retry
            restart_callback: Function to call on restart
        """
        
        # Error message
        if error_type == "error":
            st.error(f"❌ **Error:** {error_message}")
        elif error_type == "warning":
            st.warning(f"⚠️ **Warning:** {error_message}")
        else:
            st.info(f"ℹ️ **Info:** {error_message}")
        
        # Recovery options
        if show_retry or show_restart:
            st.markdown("**Recovery Options:**")
            
            col1, col2, col3 = st.columns([1, 1, 2])
            
            with col1:
                if show_retry and st.button("🔄 Retry", key="error_retry"):
                    if retry_callback:
                        retry_callback()
                    else:
                        st.rerun()
            
            with col2:
                if show_restart and st.button("🔁 Restart", key="error_restart"):
                    if restart_callback:
                        restart_callback()
                    else:
                        # Clear session state and restart
                        for key in ['current_plan_id', 'plan_status', 'plan_data']:
                            if key in st.session_state:
                                del st.session_state[key]
                        st.rerun()

class WorkflowController:
    """Controller for workflow cancellation and restart functionality"""
    
    @staticmethod
    def render_controls(plan_id: str, current_status: str):
        """
        Render workflow control buttons
        
        Args:
            plan_id: Current plan ID
            current_status: Current workflow status
        """
        
        if not plan_id:
            return
        
        st.markdown("### 🎛️ Workflow Controls")
        
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            # Cancel button (only if workflow is running)
            if current_status in ["running", "in_progress", "processing"]:
                if st.button("⏹️ Cancel", key="cancel_workflow", type="secondary"):
                    if WorkflowController._confirm_cancel():
                        WorkflowController._cancel_workflow(plan_id)
        
        with col2:
            # Restart button (if workflow failed or completed)
            if current_status in ["failed", "error", "cancelled"]:
                if st.button("🔁 Restart", key="restart_workflow", type="primary"):
                    if WorkflowController._confirm_restart():
                        WorkflowController._restart_workflow(plan_id)
    
    @staticmethod
    def _confirm_cancel() -> bool:
        """Confirm workflow cancellation"""
        if 'confirm_cancel' not in st.session_state:
            st.session_state.confirm_cancel = False
        
        if not st.session_state.confirm_cancel:
            st.session_state.confirm_cancel = True
            st.warning("⚠️ Click Cancel again to confirm workflow cancellation")
            return False
        
        st.session_state.confirm_cancel = False
        return True
    
    @staticmethod
    def _confirm_restart() -> bool:
        """Confirm workflow restart"""
        if 'confirm_restart' not in st.session_state:
            st.session_state.confirm_restart = False
        
        if not st.session_state.confirm_restart:
            st.session_state.confirm_restart = True
            st.warning("⚠️ Click Restart again to confirm workflow restart")
            return False
        
        st.session_state.confirm_restart = False
        return True
    
    @staticmethod
    def _cancel_workflow(plan_id: str):
        """Cancel the current workflow"""
        try:
            # Call API to cancel workflow (if endpoint exists)
            # For now, just update local state
            st.session_state.plan_status = "cancelled"
            show_warning(f"Workflow cancelled for plan {plan_id}")
            
        except Exception as e:
            show_error(f"Failed to cancel workflow: {str(e)}")
    
    @staticmethod
    def _restart_workflow(plan_id: str):
        """Restart the current workflow"""
        try:
            # Call API to restart workflow (if endpoint exists)
            # For now, just reset local state
            st.session_state.plan_status = "restarting"
            show_success(f"Restarting workflow for plan {plan_id}")
            
        except Exception as e:
            show_error(f"Failed to restart workflow: {str(e)}")

class RealTimeStatusUpdater:
    """Handles real-time status updates using API polling"""
    
    def __init__(self, plan_id: str, update_interval: int = 2):
        self.plan_id = plan_id
        self.update_interval = update_interval
        self.is_running = False
        self.last_update = None
        self.error_count = 0
        self.max_errors = 5
    
    def start_monitoring(self):
        """Start real-time monitoring"""
        if 'monitoring_active' not in st.session_state:
            st.session_state.monitoring_active = False
        
        if not st.session_state.monitoring_active:
            st.session_state.monitoring_active = True
            self.is_running = True
    
    def stop_monitoring(self):
        """Stop real-time monitoring"""
        st.session_state.monitoring_active = False
        self.is_running = False
    
    def update_status(self) -> Optional[Dict]:
        """
        Fetch and update plan status
        
        Returns:
            Updated status data or None if error
        """
        try:
            status_data = api_client.get_plan_status(self.plan_id)
            
            # Update session state
            st.session_state.plan_status = status_data.get('status')
            st.session_state.plan_data.update(status_data)
            
            # Reset error count on success
            self.error_count = 0
            self.last_update = datetime.now()
            
            return status_data
            
        except APIError as e:
            self.error_count += 1
            
            if self.error_count >= self.max_errors:
                show_error(f"Too many API errors. Stopping monitoring: {str(e)}")
                self.stop_monitoring()
            
            return None
        
        except Exception as e:
            show_error(f"Unexpected error updating status: {str(e)}")
            return None
    
    def render_auto_refresh_controls(self):
        """Render controls for auto-refresh functionality"""
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.session_state.get('monitoring_active', False):
                if st.button("⏸️ Pause Updates", key="pause_monitoring"):
                    self.stop_monitoring()
            else:
                if st.button("▶️ Resume Updates", key="resume_monitoring"):
                    self.start_monitoring()
        
        with col2:
            if st.button("🔄 Refresh Now", key="manual_refresh"):
                self.update_status()
                st.rerun()
        
        with col3:
            if self.last_update:
                st.caption(f"Last updated: {self.last_update.strftime('%H:%M:%S')}")
            
            if st.session_state.get('monitoring_active', False):
                st.caption("🟢 Auto-refresh active")
            else:
                st.caption("🔴 Auto-refresh paused")

def render_progress_page(plan_id: str):
    """
    Main function to render the complete progress tracking page
    
    Args:
        plan_id: The ID of the plan to monitor
    """
    
    if not plan_id:
        st.warning("No active plan to monitor. Please create a plan first.")
        return
    
    # Initialize status updater
    updater = RealTimeStatusUpdater(plan_id)
    
    # Auto-refresh controls
    updater.render_auto_refresh_controls()
    
    # Get current status
    status_data = updater.update_status()
    
    if not status_data:
        ErrorDisplay.render(
            "Unable to fetch plan status",
            error_type="error",
            retry_callback=lambda: updater.update_status()
        )
        return
    
    # Extract status information
    current_status = status_data.get('status', 'unknown')
    current_step = status_data.get('current_step', 'initialization')
    step_progress = status_data.get('step_progress', 0.0)
    active_agents = status_data.get('active_agents', [])
    last_activity = status_data.get('last_activity')
    error_message = status_data.get('error')
    
    # Calculate overall progress
    overall_progress = WorkflowSteps.calculate_progress_percentage(current_step, step_progress)
    
    # Render progress components
    st.markdown(f"## 📊 Plan Status: {plan_id}")
    
    # Progress bar
    ProgressBar.render(
        progress=overall_progress,
        current_step=current_step,
        step_progress=step_progress
    )
    
    st.markdown("---")
    
    # Agent activity
    AgentActivityDisplay.render(
        current_step=current_step,
        active_agents=active_agents,
        last_activity=last_activity
    )
    
    st.markdown("---")
    
    # Error handling
    if error_message:
        ErrorDisplay.render(
            error_message,
            error_type="error",
            retry_callback=lambda: updater.update_status(),
            restart_callback=lambda: WorkflowController._restart_workflow(plan_id)
        )
    
    # Workflow controls
    WorkflowController.render_controls(plan_id, current_status)
    
    # Auto-refresh if monitoring is active
    if st.session_state.get('monitoring_active', False):
        time.sleep(updater.update_interval)
        st.rerun()