"""
Performance optimization utilities for Streamlit GUI
"""
import time
import functools
from typing import Any, Callable, Dict, Optional
import streamlit as st
import asyncio
from concurrent.futures import ThreadPoolExecutor

class PerformanceMonitor:
    """Monitor and optimize performance of Streamlit operations"""
    
    def __init__(self):
        self.metrics = {}
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    def time_operation(self, operation_name: str):
        """Decorator to time operations"""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    execution_time = time.time() - start_time
                    self.metrics[operation_name] = {
                        'last_execution_time': execution_time,
                        'status': 'success'
                    }
                    return result
                except Exception as e:
                    execution_time = time.time() - start_time
                    self.metrics[operation_name] = {
                        'last_execution_time': execution_time,
                        'status': 'error',
                        'error': str(e)
                    }
                    raise
            return wrapper
        return decorator
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        return self.metrics.copy()
    
    def run_in_background(self, func: Callable, *args, **kwargs):
        """Run function in background thread"""
        return self.executor.submit(func, *args, **kwargs)

# Global performance monitor
perf_monitor = PerformanceMonitor()

@st.cache_data(ttl=600, show_spinner=False)
def cached_data_processing(data: Any, operation: str) -> Any:
    """Cache expensive data processing operations"""
    if operation == "sort_combinations":
        return sorted(data, key=lambda x: x.get('fitness_score', 0), reverse=True)
    elif operation == "filter_combinations":
        return [item for item in data if item.get('fitness_score', 0) >= 60]
    elif operation == "format_currency":
        if isinstance(data, (int, float)):
            return f"${data:,.2f}"
        return data
    return data

@st.cache_resource
def get_cached_api_client():
    """Get cached API client instance"""
    from components.api_client import APIClient
    return APIClient()

def optimize_dataframe_display(df, max_rows: int = 100):
    """Optimize dataframe display for large datasets"""
    if len(df) > max_rows:
        st.warning(f"Showing first {max_rows} rows of {len(df)} total rows")
        return df.head(max_rows)
    return df

def lazy_load_component(component_func: Callable, placeholder_text: str = "Loading..."):
    """Lazy load heavy components"""
    placeholder = st.empty()
    placeholder.text(placeholder_text)
    
    try:
        result = component_func()
        placeholder.empty()
        return result
    except Exception as e:
        placeholder.error(f"Error loading component: {str(e)}")
        return None

class LoadingSpinner:
    """Context manager for loading spinners"""
    
    def __init__(self, message: str = "Loading..."):
        self.message = message
        self.placeholder = None
    
    def __enter__(self):
        self.placeholder = st.empty()
        with self.placeholder:
            st.spinner(self.message)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.placeholder:
            self.placeholder.empty()

def debounce_input(key: str, delay: float = 0.5):
    """Debounce user input to reduce API calls"""
    if f"debounce_{key}" not in st.session_state:
        st.session_state[f"debounce_{key}"] = {
            'last_input': None,
            'last_time': 0,
            'timer': None
        }
    
    def should_process(current_input):
        debounce_state = st.session_state[f"debounce_{key}"]
        current_time = time.time()
        
        if (current_input != debounce_state['last_input'] and 
            current_time - debounce_state['last_time'] > delay):
            debounce_state['last_input'] = current_input
            debounce_state['last_time'] = current_time
            return True
        return False
    
    return should_process

def batch_api_calls(api_calls: list, batch_size: int = 5):
    """Batch multiple API calls for better performance"""
    results = []
    
    for i in range(0, len(api_calls), batch_size):
        batch = api_calls[i:i + batch_size]
        batch_results = []
        
        # Execute batch concurrently
        futures = []
        for call_func, args, kwargs in batch:
            future = perf_monitor.run_in_background(call_func, *args, **kwargs)
            futures.append(future)
        
        # Collect results
        for future in futures:
            try:
                result = future.result(timeout=30)
                batch_results.append(result)
            except Exception as e:
                batch_results.append({'error': str(e)})
        
        results.extend(batch_results)
    
    return results

def progressive_loading(items: list, chunk_size: int = 10, delay: float = 0.1):
    """Progressively load items to improve perceived performance"""
    container = st.container()
    
    for i in range(0, len(items), chunk_size):
        chunk = items[i:i + chunk_size]
        
        with container:
            for item in chunk:
                yield item
        
        if i + chunk_size < len(items):
            time.sleep(delay)

class MemoryOptimizer:
    """Optimize memory usage in Streamlit sessions"""
    
    @staticmethod
    def cleanup_session_state(keep_keys: list = None):
        """Clean up session state to free memory"""
        if keep_keys is None:
            keep_keys = ['api_client', 'current_plan_id', 'user_preferences']
        
        keys_to_remove = []
        for key in st.session_state.keys():
            if key not in keep_keys:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del st.session_state[key]
    
    @staticmethod
    def optimize_large_data(data: Any, max_size: int = 1000):
        """Optimize large data structures"""
        if isinstance(data, list) and len(data) > max_size:
            return data[:max_size]
        elif isinstance(data, dict) and len(data) > max_size:
            return dict(list(data.items())[:max_size])
        return data

def async_component(async_func: Callable):
    """Decorator to run async functions in Streamlit"""
    @functools.wraps(async_func)
    def wrapper(*args, **kwargs):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(async_func(*args, **kwargs))
        finally:
            loop.close()
    return wrapper

# Performance configuration
PERFORMANCE_CONFIG = {
    'enable_caching': True,
    'cache_ttl': 300,
    'max_concurrent_requests': 5,
    'request_timeout': 30,
    'enable_compression': True,
    'lazy_loading': True,
    'progressive_loading_chunk_size': 10,
    'memory_cleanup_interval': 300,  # 5 minutes
}

def get_performance_config(key: str, default: Any = None) -> Any:
    """Get performance configuration value"""
    return PERFORMANCE_CONFIG.get(key, default)