"""
Unit tests for performance optimization utilities
"""
import pytest
import time
from unittest.mock import patch, MagicMock
from utils.performance import (
    PerformanceMonitor, cached_data_processing, LoadingSpinner,
    debounce_input, batch_api_calls, MemoryOptimizer, get_performance_config
)

class TestPerformanceMonitor:
    """Test cases for PerformanceMonitor class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.monitor = PerformanceMonitor()
    
    def test_time_operation_success(self):
        """Test timing successful operations"""
        @self.monitor.time_operation("test_operation")
        def test_function():
            time.sleep(0.1)
            return "success"
        
        result = test_function()
        
        assert result == "success"
        assert "test_operation" in self.monitor.metrics
        assert self.monitor.metrics["test_operation"]["status"] == "success"
        assert self.monitor.metrics["test_operation"]["last_execution_time"] >= 0.1
    
    def test_time_operation_error(self):
        """Test timing operations that raise errors"""
        @self.monitor.time_operation("error_operation")
        def error_function():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            error_function()
        
        assert "error_operation" in self.monitor.metrics
        assert self.monitor.metrics["error_operation"]["status"] == "error"
        assert "Test error" in self.monitor.metrics["error_operation"]["error"]
    
    def test_get_metrics(self):
        """Test getting performance metrics"""
        @self.monitor.time_operation("metric_test")
        def test_function():
            return "done"
        
        test_function()
        metrics = self.monitor.get_metrics()
        
        assert isinstance(metrics, dict)
        assert "metric_test" in metrics
        assert metrics["metric_test"]["status"] == "success"
    
    def test_run_in_background(self):
        """Test running functions in background"""
        def slow_function(duration):
            time.sleep(duration)
            return f"completed after {duration}s"
        
        future = self.monitor.run_in_background(slow_function, 0.1)
        result = future.result(timeout=1)
        
        assert result == "completed after 0.1s"

class TestCachedDataProcessing:
    """Test cases for cached data processing functions"""
    
    def test_sort_combinations(self):
        """Test sorting combinations by fitness score"""
        data = [
            {"fitness_score": 75, "name": "combo1"},
            {"fitness_score": 90, "name": "combo2"},
            {"fitness_score": 60, "name": "combo3"}
        ]
        
        result = cached_data_processing(data, "sort_combinations")
        
        assert len(result) == 3
        assert result[0]["fitness_score"] == 90
        assert result[1]["fitness_score"] == 75
        assert result[2]["fitness_score"] == 60
    
    def test_filter_combinations(self):
        """Test filtering combinations by fitness score"""
        data = [
            {"fitness_score": 75, "name": "combo1"},
            {"fitness_score": 90, "name": "combo2"},
            {"fitness_score": 45, "name": "combo3"}
        ]
        
        result = cached_data_processing(data, "filter_combinations")
        
        assert len(result) == 2
        assert all(item["fitness_score"] >= 60 for item in result)
    
    def test_format_currency(self):
        """Test currency formatting"""
        assert cached_data_processing(1234.56, "format_currency") == "$1,234.56"
        assert cached_data_processing(1000000, "format_currency") == "$1,000,000.00"
        assert cached_data_processing("invalid", "format_currency") == "invalid"
    
    def test_unknown_operation(self):
        """Test unknown operation returns original data"""
        data = [1, 2, 3]
        result = cached_data_processing(data, "unknown_operation")
        assert result == data

class TestLoadingSpinner:
    """Test cases for LoadingSpinner context manager"""
    
    @patch('streamlit.empty')
    @patch('streamlit.spinner')
    def test_loading_spinner_context(self, mock_spinner, mock_empty):
        """Test LoadingSpinner context manager"""
        mock_placeholder = MagicMock()
        mock_empty.return_value = mock_placeholder
        
        with LoadingSpinner("Testing...") as spinner:
            assert spinner is not None
        
        mock_empty.assert_called_once()
        mock_placeholder.empty.assert_called_once()

class TestDebounceInput:
    """Test cases for input debouncing"""
    
    @patch('streamlit.session_state', {})
    def test_debounce_input_first_call(self):
        """Test first call to debounced input"""
        should_process = debounce_input("test_key", delay=0.1)
        
        # First call should process
        assert should_process("test_input") == True
    
    @patch('streamlit.session_state', {})
    def test_debounce_input_rapid_calls(self):
        """Test rapid calls to debounced input"""
        should_process = debounce_input("test_key", delay=0.5)
        
        # First call processes
        assert should_process("input1") == True
        
        # Immediate second call should not process
        assert should_process("input2") == False
        
        # Wait and try again
        time.sleep(0.6)
        assert should_process("input3") == True

class TestBatchAPICalls:
    """Test cases for batching API calls"""
    
    def test_batch_api_calls_success(self):
        """Test successful batch API calls"""
        def mock_api_call(value):
            return {"result": value * 2}
        
        api_calls = [
            (mock_api_call, (1,), {}),
            (mock_api_call, (2,), {}),
            (mock_api_call, (3,), {})
        ]
        
        results = batch_api_calls(api_calls, batch_size=2)
        
        assert len(results) == 3
        assert results[0]["result"] == 2
        assert results[1]["result"] == 4
        assert results[2]["result"] == 6
    
    def test_batch_api_calls_with_errors(self):
        """Test batch API calls with some errors"""
        def mock_api_call(value):
            if value == 2:
                raise ValueError("Test error")
            return {"result": value * 2}
        
        api_calls = [
            (mock_api_call, (1,), {}),
            (mock_api_call, (2,), {}),
            (mock_api_call, (3,), {})
        ]
        
        results = batch_api_calls(api_calls, batch_size=3)
        
        assert len(results) == 3
        assert results[0]["result"] == 2
        assert "error" in results[1]
        assert results[2]["result"] == 6

class TestMemoryOptimizer:
    """Test cases for memory optimization utilities"""
    
    @patch('streamlit.session_state', {'key1': 'value1', 'key2': 'value2', 'api_client': 'client'})
    def test_cleanup_session_state(self):
        """Test session state cleanup"""
        import streamlit as st
        
        MemoryOptimizer.cleanup_session_state(keep_keys=['api_client'])
        
        # Should keep api_client but remove others
        assert 'api_client' in st.session_state
        assert 'key1' not in st.session_state
        assert 'key2' not in st.session_state
    
    def test_optimize_large_data_list(self):
        """Test optimizing large lists"""
        large_list = list(range(2000))
        optimized = MemoryOptimizer.optimize_large_data(large_list, max_size=1000)
        
        assert len(optimized) == 1000
        assert optimized == list(range(1000))
    
    def test_optimize_large_data_dict(self):
        """Test optimizing large dictionaries"""
        large_dict = {f"key_{i}": f"value_{i}" for i in range(2000)}
        optimized = MemoryOptimizer.optimize_large_data(large_dict, max_size=1000)
        
        assert len(optimized) == 1000
        assert isinstance(optimized, dict)
    
    def test_optimize_small_data(self):
        """Test that small data is not modified"""
        small_list = [1, 2, 3]
        optimized = MemoryOptimizer.optimize_large_data(small_list, max_size=1000)
        
        assert optimized == small_list

class TestPerformanceConfig:
    """Test cases for performance configuration"""
    
    def test_get_performance_config_existing(self):
        """Test getting existing configuration values"""
        assert get_performance_config('enable_caching') == True
        assert get_performance_config('cache_ttl') == 300
        assert get_performance_config('max_concurrent_requests') == 5
    
    def test_get_performance_config_default(self):
        """Test getting configuration with default value"""
        assert get_performance_config('nonexistent_key', 'default') == 'default'
        assert get_performance_config('nonexistent_key') is None

class TestAsyncComponent:
    """Test cases for async component decorator"""
    
    def test_async_component_decorator(self):
        """Test async component decorator"""
        from utils.performance import async_component
        
        @async_component
        async def async_function(value):
            return value * 2
        
        result = async_function(5)
        assert result == 10

if __name__ == "__main__":
    pytest.main([__file__])