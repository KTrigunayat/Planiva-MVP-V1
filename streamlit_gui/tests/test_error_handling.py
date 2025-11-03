"""
Tests for error handling utilities
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import streamlit as st

from utils.error_handling import (
    ErrorHandler,
    with_error_handling,
    with_retry,
    LoadingState,
    RetryButton,
    StaleDataWarning,
    validate_form_field,
    Validators
)
from components.api_client import APIError


class TestErrorHandler:
    """Test ErrorHandler class."""
    
    def test_handle_api_error_404(self):
        """Test handling 404 errors."""
        error = APIError("Not found", status_code=404)
        
        with patch('streamlit.error') as mock_error, \
             patch('streamlit.info') as mock_info:
            ErrorHandler.handle_api_error(error, "test context")
            
            assert mock_error.called
            assert mock_info.called
    
    def test_handle_api_error_500(self):
        """Test handling server errors."""
        error = APIError("Server error", status_code=500)
        
        with patch('streamlit.error') as mock_error, \
             patch('streamlit.info') as mock_info:
            ErrorHandler.handle_api_error(error, "test context")
            
            assert mock_error.called
            assert mock_info.called
    
    def test_handle_api_error_connection(self):
        """Test handling connection errors."""
        error = APIError("Cannot connect to server")
        
        with patch('streamlit.error') as mock_error, \
             patch('streamlit.info') as mock_info:
            ErrorHandler.handle_api_error(error, "test context")
            
            assert mock_error.called
            assert mock_info.called
    
    def test_handle_unexpected_error(self):
        """Test handling unexpected errors."""
        error = ValueError("Test error")
        
        with patch('streamlit.error') as mock_error, \
             patch('streamlit.expander') as mock_expander:
            ErrorHandler.handle_unexpected_error(error, "test context")
            
            assert mock_error.called
    
    def test_show_validation_error(self):
        """Test showing validation errors."""
        with patch('streamlit.error') as mock_error:
            ErrorHandler.show_validation_error("email", "Invalid format")
            
            assert mock_error.called
    
    def test_show_success(self):
        """Test showing success messages."""
        with patch('streamlit.success') as mock_success:
            ErrorHandler.show_success("Operation successful")
            
            assert mock_success.called
    
    def test_show_warning(self):
        """Test showing warning messages."""
        with patch('streamlit.warning') as mock_warning:
            ErrorHandler.show_warning("Warning message")
            
            assert mock_warning.called
    
    def test_show_info(self):
        """Test showing info messages."""
        with patch('streamlit.info') as mock_info:
            ErrorHandler.show_info("Info message")
            
            assert mock_info.called


class TestWithErrorHandling:
    """Test with_error_handling decorator."""
    
    def test_successful_execution(self):
        """Test decorator with successful function execution."""
        @with_error_handling(context="test", show_spinner=False)
        def test_func():
            return "success"
        
        result = test_func()
        assert result == "success"
    
    def test_api_error_handling(self):
        """Test decorator handles API errors."""
        @with_error_handling(context="test", show_spinner=False)
        def test_func():
            raise APIError("Test error", status_code=500)
        
        with patch('streamlit.error'), patch('streamlit.info'):
            result = test_func()
            assert result is None
    
    def test_unexpected_error_handling(self):
        """Test decorator handles unexpected errors."""
        @with_error_handling(context="test", show_spinner=False)
        def test_func():
            raise ValueError("Test error")
        
        with patch('streamlit.error'), patch('streamlit.expander'):
            result = test_func()
            assert result is None


class TestWithRetry:
    """Test with_retry decorator."""
    
    def test_successful_first_attempt(self):
        """Test retry decorator with successful first attempt."""
        @with_retry(max_attempts=3)
        def test_func():
            return "success"
        
        result = test_func()
        assert result == "success"
    
    def test_retry_on_server_error(self):
        """Test retry on server errors."""
        call_count = 0
        
        @with_retry(max_attempts=3, delay=0.01)
        def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise APIError("Server error", status_code=500)
            return "success"
        
        result = test_func()
        assert result == "success"
        assert call_count == 3
    
    def test_no_retry_on_client_error(self):
        """Test no retry on client errors."""
        call_count = 0
        
        @with_retry(max_attempts=3)
        def test_func():
            nonlocal call_count
            call_count += 1
            raise APIError("Bad request", status_code=400)
        
        with pytest.raises(APIError):
            test_func()
        
        assert call_count == 1
    
    def test_max_retries_exceeded(self):
        """Test max retries exceeded."""
        @with_retry(max_attempts=2, delay=0.01)
        def test_func():
            raise APIError("Server error", status_code=500)
        
        with pytest.raises(APIError):
            test_func()


class TestValidators:
    """Test Validators class."""
    
    def test_required_validator(self):
        """Test required validator."""
        assert Validators.required("value") is True
        assert Validators.required("") is False
        assert Validators.required(None) is False
        assert Validators.required([]) is False
        assert Validators.required([1, 2]) is True
    
    def test_email_validator(self):
        """Test email validator."""
        assert Validators.email("test@example.com") is True
        assert Validators.email("invalid.email") is False
        assert Validators.email("@example.com") is False
        assert Validators.email("test@") is False
    
    def test_min_length_validator(self):
        """Test min length validator."""
        validator = Validators.min_length(5)
        assert validator("12345") is True
        assert validator("123456") is True
        assert validator("1234") is False
    
    def test_max_length_validator(self):
        """Test max length validator."""
        validator = Validators.max_length(5)
        assert validator("12345") is True
        assert validator("1234") is True
        assert validator("123456") is False
    
    def test_numeric_validator(self):
        """Test numeric validator."""
        assert Validators.numeric("123") is True
        assert Validators.numeric("123.45") is True
        assert Validators.numeric("abc") is False
        assert Validators.numeric(123) is True
    
    def test_positive_validator(self):
        """Test positive validator."""
        assert Validators.positive("123") is True
        assert Validators.positive("0") is False
        assert Validators.positive("-123") is False
        assert Validators.positive(123) is True
    
    def test_in_range_validator(self):
        """Test in range validator."""
        validator = Validators.in_range(0, 100)
        assert validator("50") is True
        assert validator("0") is True
        assert validator("100") is True
        assert validator("-1") is False
        assert validator("101") is False


class TestValidateFormField:
    """Test validate_form_field function."""
    
    def test_all_validators_pass(self):
        """Test when all validators pass."""
        validators = {
            "Required": Validators.required,
            "Email format": Validators.email
        }
        
        with patch('streamlit.error'):
            result = validate_form_field("test@example.com", "email", validators)
            assert result is True
    
    def test_validator_fails(self):
        """Test when a validator fails."""
        validators = {
            "Required": Validators.required,
            "Email format": Validators.email
        }
        
        with patch('streamlit.error') as mock_error:
            result = validate_form_field("invalid", "email", validators)
            assert result is False
            assert mock_error.called


class TestLoadingState:
    """Test LoadingState context manager."""
    
    def test_loading_state_context(self):
        """Test loading state context manager."""
        with patch('streamlit.spinner') as mock_spinner:
            mock_spinner.return_value.__enter__ = Mock()
            mock_spinner.return_value.__exit__ = Mock()
            
            with LoadingState("Loading..."):
                pass
            
            assert mock_spinner.called


class TestRetryButton:
    """Test RetryButton component."""
    
    def test_render_retry_button(self):
        """Test rendering retry button."""
        with patch('streamlit.button', return_value=True) as mock_button:
            result = RetryButton.render("test_key")
            
            assert mock_button.called
            assert result is True


class TestStaleDataWarning:
    """Test StaleDataWarning component."""
    
    def test_no_warning_for_fresh_data(self):
        """Test no warning for fresh data."""
        last_updated = datetime.now()
        
        with patch('streamlit.warning') as mock_warning:
            result = StaleDataWarning.render(last_updated, threshold_seconds=300)
            
            assert not mock_warning.called
            assert result is False
    
    def test_warning_for_stale_data(self):
        """Test warning for stale data."""
        last_updated = datetime.now() - timedelta(seconds=400)
        
        # Create mock columns that support context manager protocol
        mock_col1 = MagicMock()
        mock_col2 = MagicMock()
        mock_col1.__enter__ = MagicMock(return_value=mock_col1)
        mock_col1.__exit__ = MagicMock(return_value=False)
        mock_col2.__enter__ = MagicMock(return_value=mock_col2)
        mock_col2.__exit__ = MagicMock(return_value=False)
        
        with patch('streamlit.warning') as mock_warning, \
             patch('streamlit.columns', return_value=[mock_col1, mock_col2]), \
             patch('streamlit.button', return_value=False):
            result = StaleDataWarning.render(last_updated, threshold_seconds=300)
            
            assert mock_warning.called


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
