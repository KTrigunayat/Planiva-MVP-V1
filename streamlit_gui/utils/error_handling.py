"""
Error Handling Utilities for Streamlit GUI

Provides comprehensive error handling, user feedback, and recovery mechanisms
for API calls and user interactions.
"""

import streamlit as st
import logging
import traceback
from typing import Callable, Any, Optional, Dict, TypeVar, ParamSpec
from functools import wraps
from datetime import datetime
import time

from components.api_client import APIError

# Set up logging
logger = logging.getLogger(__name__)

# Type variables for generic decorators
P = ParamSpec('P')
T = TypeVar('T')


class ErrorHandler:
    """Centralized error handling for the application."""
    
    @staticmethod
    def handle_api_error(error: APIError, context: str = "") -> None:
        """
        Handle API errors with user-friendly messages.
        
        Args:
            error: The APIError exception
            context: Additional context about what was being attempted
        """
        error_message = error.message
        status_code = error.status_code
        
        # Build user-friendly message based on error type
        if status_code == 404:
            st.error(f"❌ **Not Found**\n\n{context or 'The requested resource was not found.'}")
            st.info("💡 **Suggestion**: Check that the ID is correct or try refreshing the page.")
            
        elif status_code == 400:
            st.error(f"❌ **Invalid Request**\n\n{error_message}")
            st.info("💡 **Suggestion**: Please check your input and try again.")
            
        elif status_code == 401:
            st.error(f"🔒 **Authentication Required**\n\nYou need to be logged in to access this resource.")
            st.info("💡 **Suggestion**: Please log in and try again.")
            
        elif status_code == 403:
            st.error(f"🚫 **Access Denied**\n\nYou don't have permission to access this resource.")
            st.info("💡 **Suggestion**: Contact support if you believe this is an error.")
            
        elif status_code and status_code >= 500:
            st.error(f"🔥 **Server Error**\n\nThe server encountered an error processing your request.")
            st.info("💡 **Suggestion**: Please try again in a few moments. If the problem persists, contact support.")
            
        elif "Cannot connect" in error_message or "Connection" in error_message:
            st.error(f"🔌 **Connection Error**\n\nCannot connect to the server.")
            st.info("💡 **Suggestion**: Check your internet connection and verify the server is running.")
            
        elif "timeout" in error_message.lower():
            st.error(f"⏱️ **Request Timeout**\n\nThe request took too long to complete.")
            st.info("💡 **Suggestion**: The server may be busy. Please try again.")
            
        else:
            st.error(f"❌ **Error**\n\n{error_message}")
            st.info("💡 **Suggestion**: Please try again or contact support if the problem persists.")
        
        # Log the error
        logger.error(f"API Error in {context}: {error_message} (Status: {status_code})")
    
    @staticmethod
    def handle_unexpected_error(error: Exception, context: str = "") -> None:
        """
        Handle unexpected errors with generic user message.
        
        Args:
            error: The exception
            context: Additional context about what was being attempted
        """
        error_type = type(error).__name__
        error_message = str(error)
        
        st.error(f"❌ **Unexpected Error**\n\nAn unexpected error occurred: {error_type}")
        
        # Show error details in expander for debugging
        with st.expander("🔍 Error Details (for support)"):
            st.code(f"{error_type}: {error_message}")
            st.code(traceback.format_exc())
        
        st.info("💡 **Suggestion**: Please try again or contact support with the error details above.")
        
        # Log the full error
        logger.error(f"Unexpected error in {context}: {error_type}: {error_message}\n{traceback.format_exc()}")
    
    @staticmethod
    def show_validation_error(field_name: str, message: str) -> None:
        """
        Show field-level validation error.
        
        Args:
            field_name: Name of the field with error
            message: Validation error message
        """
        st.error(f"❌ **{field_name}**: {message}")
    
    @staticmethod
    def show_success(message: str, details: Optional[str] = None) -> None:
        """
        Show success message.
        
        Args:
            message: Success message
            details: Optional additional details
        """
        st.success(f"✅ {message}")
        if details:
            st.caption(details)
    
    @staticmethod
    def show_warning(message: str, details: Optional[str] = None) -> None:
        """
        Show warning message.
        
        Args:
            message: Warning message
            details: Optional additional details
        """
        st.warning(f"⚠️ {message}")
        if details:
            st.caption(details)
    
    @staticmethod
    def show_info(message: str, details: Optional[str] = None) -> None:
        """
        Show info message.
        
        Args:
            message: Info message
            details: Optional additional details
        """
        st.info(f"ℹ️ {message}")
        if details:
            st.caption(details)


def with_error_handling(context: str = "", show_spinner: bool = True, spinner_text: str = "Loading..."):
    """
    Decorator to add error handling to functions.
    
    Args:
        context: Description of what the function does (for error messages)
        show_spinner: Whether to show a loading spinner
        spinner_text: Text to show in the spinner
    
    Returns:
        Decorated function with error handling
    """
    def decorator(func: Callable[P, T]) -> Callable[P, Optional[T]]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> Optional[T]:
            try:
                if show_spinner:
                    with st.spinner(spinner_text):
                        return func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
                    
            except APIError as e:
                ErrorHandler.handle_api_error(e, context)
                return None
                
            except Exception as e:
                ErrorHandler.handle_unexpected_error(e, context)
                return None
        
        return wrapper
    return decorator


def with_retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    Decorator to add retry logic to functions.
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries (seconds)
        backoff: Multiplier for delay on each retry
    
    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable[P, T]) -> Callable[P, Optional[T]]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> Optional[T]:
            current_delay = delay
            last_error = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                    
                except APIError as e:
                    last_error = e
                    
                    # Don't retry on client errors (4xx)
                    if e.status_code and 400 <= e.status_code < 500:
                        raise
                    
                    # Retry on server errors (5xx) and connection errors
                    if attempt < max_attempts - 1:
                        logger.warning(f"Attempt {attempt + 1} failed, retrying in {current_delay}s...")
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        raise
                        
                except Exception as e:
                    last_error = e
                    
                    # Don't retry on unexpected errors
                    raise
            
            # If we get here, all retries failed
            if last_error:
                raise last_error
            
            return None
        
        return wrapper
    return decorator


class LoadingState:
    """Context manager for showing loading state."""
    
    def __init__(self, message: str = "Loading...", show_progress: bool = False):
        """
        Initialize loading state.
        
        Args:
            message: Loading message to display
            show_progress: Whether to show a progress bar
        """
        self.message = message
        self.show_progress = show_progress
        self.spinner = None
        self.progress_bar = None
    
    def __enter__(self):
        """Enter loading state."""
        self.spinner = st.spinner(self.message)
        self.spinner.__enter__()
        
        if self.show_progress:
            self.progress_bar = st.progress(0)
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit loading state."""
        if self.spinner:
            self.spinner.__exit__(exc_type, exc_val, exc_tb)
        
        if self.progress_bar:
            self.progress_bar.empty()
        
        return False
    
    def update_progress(self, value: float, text: Optional[str] = None):
        """
        Update progress bar.
        
        Args:
            value: Progress value (0.0 to 1.0)
            text: Optional text to update
        """
        if self.progress_bar:
            self.progress_bar.progress(value)
        
        if text and self.spinner:
            # Update spinner text (note: Streamlit doesn't support this directly)
            pass


class RetryButton:
    """Component for showing a retry button after errors."""
    
    @staticmethod
    def render(key: str, label: str = "🔄 Retry", on_click: Optional[Callable] = None) -> bool:
        """
        Render a retry button.
        
        Args:
            key: Unique key for the button
            label: Button label
            on_click: Optional callback function
        
        Returns:
            True if button was clicked
        """
        if st.button(label, key=key, type="primary"):
            if on_click:
                on_click()
            return True
        return False


class StaleDataWarning:
    """Component for showing stale data warnings."""
    
    @staticmethod
    def render(last_updated: datetime, threshold_seconds: int = 300, key: str = "refresh_data") -> bool:
        """
        Render a stale data warning if data is old.
        
        Args:
            last_updated: When the data was last updated
            threshold_seconds: Age threshold for showing warning
            key: Unique key for the refresh button
        
        Returns:
            True if refresh button was clicked
        """
        age_seconds = (datetime.now() - last_updated).total_seconds()
        
        if age_seconds > threshold_seconds:
            col1, col2 = st.columns([3, 1])
            
            with col1:
                minutes_old = int(age_seconds / 60)
                st.warning(f"⚠️ Data may be stale (last updated {minutes_old} minutes ago)")
            
            with col2:
                if st.button("🔄 Refresh", key=key, type="primary"):
                    return True
        
        return False


def validate_form_field(value: Any, field_name: str, validators: Dict[str, Callable[[Any], bool]]) -> bool:
    """
    Validate a form field with multiple validators.
    
    Args:
        value: Field value to validate
        field_name: Name of the field
        validators: Dictionary of validator name to validator function
    
    Returns:
        True if all validations pass, False otherwise
    """
    for validator_name, validator_func in validators.items():
        try:
            if not validator_func(value):
                ErrorHandler.show_validation_error(field_name, validator_name)
                return False
        except Exception as e:
            ErrorHandler.show_validation_error(field_name, f"Validation error: {str(e)}")
            return False
    
    return True


# Common validators
class Validators:
    """Common validation functions."""
    
    @staticmethod
    def required(value: Any) -> bool:
        """Check if value is not empty."""
        if value is None:
            return False
        if isinstance(value, str) and not value.strip():
            return False
        if isinstance(value, (list, dict)) and not value:
            return False
        return True
    
    @staticmethod
    def email(value: str) -> bool:
        """Check if value is a valid email."""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, value))
    
    @staticmethod
    def min_length(min_len: int) -> Callable[[str], bool]:
        """Create a minimum length validator."""
        def validator(value: str) -> bool:
            return len(value) >= min_len
        return validator
    
    @staticmethod
    def max_length(max_len: int) -> Callable[[str], bool]:
        """Create a maximum length validator."""
        def validator(value: str) -> bool:
            return len(value) <= max_len
        return validator
    
    @staticmethod
    def numeric(value: Any) -> bool:
        """Check if value is numeric."""
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def positive(value: Any) -> bool:
        """Check if value is positive."""
        try:
            return float(value) > 0
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def in_range(min_val: float, max_val: float) -> Callable[[Any], bool]:
        """Create a range validator."""
        def validator(value: Any) -> bool:
            try:
                num_value = float(value)
                return min_val <= num_value <= max_val
            except (ValueError, TypeError):
                return False
        return validator


# Global error handler instance
error_handler = ErrorHandler()
