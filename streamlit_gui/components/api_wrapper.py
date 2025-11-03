"""
API Wrapper Component with Enhanced Error Handling

Provides wrapped API calls with comprehensive error handling, loading states,
and retry mechanisms for all CRM and Task Management API endpoints.
"""

import streamlit as st
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import logging

from components.api_client import api_client, APIError
from utils.error_handling import (
    error_handler,
    with_error_handling,
    with_retry,
    LoadingState,
    RetryButton,
    StaleDataWarning
)

logger = logging.getLogger(__name__)


class APIWrapper:
    """Wrapper for API calls with enhanced error handling."""
    
    def __init__(self):
        """Initialize API wrapper."""
        self.api_client = api_client
    
    # ========== CRM API Methods with Error Handling ==========
    
    def get_preferences_safe(self, client_id: str, show_loading: bool = True) -> Optional[Dict]:
        """
        Get client preferences with error handling.
        
        Args:
            client_id: Client identifier
            show_loading: Whether to show loading spinner
            
        Returns:
            Preferences dictionary or None on error
        """
        @with_error_handling(
            context="loading communication preferences",
            show_spinner=show_loading,
            spinner_text="Loading preferences..."
        )
        @with_retry(max_attempts=2)
        def _get_preferences():
            return self.api_client.get_preferences(client_id)
        
        return _get_preferences()
    
    def update_preferences_safe(self, preferences_data: Dict, show_loading: bool = True) -> Optional[Dict]:
        """
        Update client preferences with error handling.
        
        Args:
            preferences_data: Preferences data
            show_loading: Whether to show loading spinner
            
        Returns:
            Updated preferences or None on error
        """
        @with_error_handling(
            context="updating communication preferences",
            show_spinner=show_loading,
            spinner_text="Saving preferences..."
        )
        def _update_preferences():
            return self.api_client.update_preferences(preferences_data)
        
        result = _update_preferences()
        
        if result:
            error_handler.show_success("Preferences updated successfully!")
        
        return result
    
    def get_communications_safe(
        self,
        plan_id: Optional[str] = None,
        client_id: Optional[str] = None,
        channel: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        show_loading: bool = True
    ) -> Optional[Dict]:
        """
        Get communications with error handling.
        
        Args:
            plan_id: Optional plan ID filter
            client_id: Optional client ID filter
            channel: Optional channel filter
            status: Optional status filter
            limit: Maximum results
            offset: Pagination offset
            show_loading: Whether to show loading spinner
            
        Returns:
            Communications data or None on error
        """
        @with_error_handling(
            context="loading communication history",
            show_spinner=show_loading,
            spinner_text="Loading communications..."
        )
        @with_retry(max_attempts=2)
        def _get_communications():
            return self.api_client.get_communications(
                plan_id=plan_id,
                client_id=client_id,
                channel=channel,
                status=status,
                limit=limit,
                offset=offset
            )
        
        return _get_communications()
    
    def get_analytics_safe(
        self,
        plan_id: Optional[str] = None,
        client_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        show_loading: bool = True
    ) -> Optional[Dict]:
        """
        Get analytics with error handling.
        
        Args:
            plan_id: Optional plan ID filter
            client_id: Optional client ID filter
            start_date: Optional start date filter
            end_date: Optional end date filter
            show_loading: Whether to show loading spinner
            
        Returns:
            Analytics data or None on error
        """
        @with_error_handling(
            context="loading analytics data",
            show_spinner=show_loading,
            spinner_text="Loading analytics..."
        )
        @with_retry(max_attempts=2)
        def _get_analytics():
            return self.api_client.get_analytics(
                plan_id=plan_id,
                client_id=client_id,
                start_date=start_date,
                end_date=end_date
            )
        
        return _get_analytics()
    
    # ========== Task Management API Methods with Error Handling ==========
    
    def get_extended_task_list_safe(self, plan_id: str, show_loading: bool = True) -> Optional[Dict]:
        """
        Get extended task list with error handling.
        
        Args:
            plan_id: Plan identifier
            show_loading: Whether to show loading spinner
            
        Returns:
            Task list data or None on error
        """
        @with_error_handling(
            context="loading task list",
            show_spinner=show_loading,
            spinner_text="Loading tasks..."
        )
        @with_retry(max_attempts=2)
        def _get_task_list():
            return self.api_client.get_extended_task_list(plan_id)
        
        return _get_task_list()
    
    def get_timeline_data_safe(self, plan_id: str, show_loading: bool = True) -> Optional[Dict]:
        """
        Get timeline data with error handling.
        
        Args:
            plan_id: Plan identifier
            show_loading: Whether to show loading spinner
            
        Returns:
            Timeline data or None on error
        """
        @with_error_handling(
            context="loading timeline data",
            show_spinner=show_loading,
            spinner_text="Loading timeline..."
        )
        @with_retry(max_attempts=2)
        def _get_timeline():
            return self.api_client.get_timeline_data(plan_id)
        
        return _get_timeline()
    
    def get_conflicts_safe(self, plan_id: str, show_loading: bool = True) -> Optional[Dict]:
        """
        Get conflicts with error handling.
        
        Args:
            plan_id: Plan identifier
            show_loading: Whether to show loading spinner
            
        Returns:
            Conflicts data or None on error
        """
        @with_error_handling(
            context="loading conflicts",
            show_spinner=show_loading,
            spinner_text="Loading conflicts..."
        )
        @with_retry(max_attempts=2)
        def _get_conflicts():
            return self.api_client.get_conflicts(plan_id)
        
        return _get_conflicts()
    
    def update_task_status_safe(
        self,
        plan_id: str,
        task_id: str,
        status: str,
        show_loading: bool = True
    ) -> Optional[Dict]:
        """
        Update task status with error handling.
        
        Args:
            plan_id: Plan identifier
            task_id: Task identifier
            status: New status
            show_loading: Whether to show loading spinner
            
        Returns:
            Updated task data or None on error
        """
        @with_error_handling(
            context="updating task status",
            show_spinner=show_loading,
            spinner_text="Updating task..."
        )
        def _update_status():
            return self.api_client.update_task_status(plan_id, task_id, status)
        
        result = _update_status()
        
        if result:
            error_handler.show_success(f"Task status updated to '{status}'")
        
        return result
    
    def resolve_conflict_safe(
        self,
        plan_id: str,
        conflict_id: str,
        resolution: Dict,
        show_loading: bool = True
    ) -> Optional[Dict]:
        """
        Resolve conflict with error handling.
        
        Args:
            plan_id: Plan identifier
            conflict_id: Conflict identifier
            resolution: Resolution data
            show_loading: Whether to show loading spinner
            
        Returns:
            Updated conflict data or None on error
        """
        @with_error_handling(
            context="resolving conflict",
            show_spinner=show_loading,
            spinner_text="Applying resolution..."
        )
        def _resolve_conflict():
            return self.api_client.resolve_conflict(plan_id, conflict_id, resolution)
        
        result = _resolve_conflict()
        
        if result:
            error_handler.show_success("Conflict resolved successfully!")
        
        return result
    
    # ========== Plan API Methods with Error Handling ==========
    
    def get_plan_status_safe(self, plan_id: str, show_loading: bool = True) -> Optional[Dict]:
        """
        Get plan status with error handling.
        
        Args:
            plan_id: Plan identifier
            show_loading: Whether to show loading spinner
            
        Returns:
            Plan status or None on error
        """
        @with_error_handling(
            context="loading plan status",
            show_spinner=show_loading,
            spinner_text="Loading plan status..."
        )
        @with_retry(max_attempts=2)
        def _get_status():
            return self.api_client.get_plan_status(plan_id)
        
        return _get_status()
    
    def get_plan_results_safe(self, plan_id: str, show_loading: bool = True) -> Optional[Dict]:
        """
        Get plan results with error handling.
        
        Args:
            plan_id: Plan identifier
            show_loading: Whether to show loading spinner
            
        Returns:
            Plan results or None on error
        """
        @with_error_handling(
            context="loading plan results",
            show_spinner=show_loading,
            spinner_text="Loading results..."
        )
        @with_retry(max_attempts=2)
        def _get_results():
            return self.api_client.get_plan_results(plan_id)
        
        return _get_results()
    
    def get_blueprint_safe(self, plan_id: str, show_loading: bool = True) -> Optional[Dict]:
        """
        Get blueprint with error handling.
        
        Args:
            plan_id: Plan identifier
            show_loading: Whether to show loading spinner
            
        Returns:
            Blueprint data or None on error
        """
        @with_error_handling(
            context="loading blueprint",
            show_spinner=show_loading,
            spinner_text="Loading blueprint..."
        )
        @with_retry(max_attempts=2)
        def _get_blueprint():
            return self.api_client.get_blueprint(plan_id)
        
        return _get_blueprint()
    
    def create_plan_safe(self, request_data: Dict, show_loading: bool = True) -> Optional[Dict]:
        """
        Create plan with error handling.
        
        Args:
            request_data: Plan request data
            show_loading: Whether to show loading spinner
            
        Returns:
            Created plan data or None on error
        """
        @with_error_handling(
            context="creating event plan",
            show_spinner=show_loading,
            spinner_text="Creating plan..."
        )
        def _create_plan():
            return self.api_client.create_plan(request_data)
        
        result = _create_plan()
        
        if result:
            error_handler.show_success("Event plan created successfully!")
        
        return result
    
    def select_combination_safe(
        self,
        plan_id: str,
        combination_id: str,
        show_loading: bool = True
    ) -> Optional[Dict]:
        """
        Select combination with error handling.
        
        Args:
            plan_id: Plan identifier
            combination_id: Combination identifier
            show_loading: Whether to show loading spinner
            
        Returns:
            Selection result or None on error
        """
        @with_error_handling(
            context="selecting vendor combination",
            show_spinner=show_loading,
            spinner_text="Selecting combination..."
        )
        def _select_combination():
            return self.api_client.select_combination(plan_id, combination_id)
        
        result = _select_combination()
        
        if result:
            error_handler.show_success("Vendor combination selected successfully!")
        
        return result
    
    # ========== Utility Methods ==========
    
    def health_check_safe(self, show_loading: bool = False) -> Optional[Dict]:
        """
        Check API health with error handling.
        
        Args:
            show_loading: Whether to show loading spinner
            
        Returns:
            Health status or None on error
        """
        @with_error_handling(
            context="checking API health",
            show_spinner=show_loading,
            spinner_text="Checking connection..."
        )
        def _health_check():
            return self.api_client.health_check()
        
        return _health_check()
    
    def render_retry_button(self, key: str, callback: Callable) -> None:
        """
        Render a retry button that calls the provided callback.
        
        Args:
            key: Unique key for the button
            callback: Function to call on retry
        """
        if RetryButton.render(key, on_click=callback):
            st.rerun()
    
    def check_stale_data(
        self,
        last_updated: Optional[datetime],
        threshold_seconds: int = 300,
        key: str = "refresh_data"
    ) -> bool:
        """
        Check if data is stale and show warning if needed.
        
        Args:
            last_updated: When data was last updated
            threshold_seconds: Age threshold for showing warning
            key: Unique key for refresh button
            
        Returns:
            True if refresh button was clicked
        """
        if last_updated is None:
            return False
        
        return StaleDataWarning.render(last_updated, threshold_seconds, key)


# Global API wrapper instance
api_wrapper = APIWrapper()
