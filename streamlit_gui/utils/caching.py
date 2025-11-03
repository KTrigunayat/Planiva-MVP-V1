"""
Caching and Performance Optimization Utilities

Provides caching decorators, cache management, and performance monitoring
for the Streamlit GUI application.
"""

import streamlit as st
import time
import logging
import functools
import hashlib
import json
from typing import Any, Callable, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import OrderedDict

logger = logging.getLogger(__name__)


class CacheConfig:
    """Cache configuration with TTL settings for different data types."""
    
    # Cache TTL in seconds for different data types
    TTL_SETTINGS = {
        'health_check': 30,           # 30 seconds
        'plan_list': 60,              # 1 minute
        'plan_status': 10,            # 10 seconds (frequently updated)
        'plan_results': 300,          # 5 minutes
        'plan_blueprint': 600,        # 10 minutes
        'task_list': 30,              # 30 seconds
        'timeline_data': 30,          # 30 seconds
        'conflicts': 30,              # 30 seconds
        'crm_preferences': 300,       # 5 minutes
        'communications': 30,         # 30 seconds (real-time updates)
        'analytics': 60,              # 1 minute
        'vendor_data': 600,           # 10 minutes
        'default': 300                # 5 minutes default
    }
    
    @classmethod
    def get_ttl(cls, data_type: str) -> int:
        """
        Get TTL for a specific data type.
        
        Args:
            data_type: Type of data being cached
            
        Returns:
            TTL in seconds
        """
        return cls.TTL_SETTINGS.get(data_type, cls.TTL_SETTINGS['default'])


class LRUCache:
    """
    Simple LRU (Least Recently Used) cache implementation.
    
    Used for in-memory caching with size limits.
    """
    
    def __init__(self, max_size: int = 100):
        """
        Initialize LRU cache.
        
        Args:
            max_size: Maximum number of items to cache
        """
        self.cache = OrderedDict()
        self.max_size = max_size
        self.hits = 0
        self.misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get item from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        if key in self.cache:
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            self.hits += 1
            return self.cache[key]
        
        self.misses += 1
        return None
    
    def set(self, key: str, value: Any):
        """
        Set item in cache.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        if key in self.cache:
            # Update existing item
            self.cache.move_to_end(key)
        else:
            # Add new item
            if len(self.cache) >= self.max_size:
                # Remove least recently used item
                self.cache.popitem(last=False)
        
        self.cache[key] = value
    
    def clear(self):
        """Clear all cached items."""
        self.cache.clear()
        self.hits = 0
        self.misses = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache stats
        """
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': hit_rate
        }


# Global LRU cache instance
_lru_cache = LRUCache(max_size=100)


def cache_with_ttl(ttl: Optional[int] = None, data_type: Optional[str] = None):
    """
    Decorator for caching function results with TTL.
    
    Args:
        ttl: Time to live in seconds (optional)
        data_type: Data type for automatic TTL lookup (optional)
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Determine TTL
            cache_ttl = ttl
            if cache_ttl is None and data_type:
                cache_ttl = CacheConfig.get_ttl(data_type)
            elif cache_ttl is None:
                cache_ttl = CacheConfig.get_ttl('default')
            
            # Generate cache key
            cache_key = _generate_cache_key(func.__name__, args, kwargs)
            
            # Check if cached
            cached_result = _lru_cache.get(cache_key)
            if cached_result is not None:
                cached_value, cached_time = cached_result
                age = (datetime.now() - cached_time).total_seconds()
                
                if age < cache_ttl:
                    logger.debug(f"Cache hit for {func.__name__} (age: {age:.1f}s)")
                    return cached_value
            
            # Execute function
            logger.debug(f"Cache miss for {func.__name__}, executing...")
            result = func(*args, **kwargs)
            
            # Cache result
            _lru_cache.set(cache_key, (result, datetime.now()))
            
            return result
        
        return wrapper
    return decorator


def _generate_cache_key(func_name: str, args: Tuple, kwargs: Dict) -> str:
    """
    Generate a cache key from function name and arguments.
    
    Args:
        func_name: Function name
        args: Positional arguments
        kwargs: Keyword arguments
        
    Returns:
        Cache key string
    """
    # Create a dictionary of all arguments
    key_data = {
        'func': func_name,
        'args': args,
        'kwargs': kwargs
    }
    
    # Serialize to JSON and hash
    try:
        key_string = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_string.encode()).hexdigest()
    except (TypeError, ValueError):
        # Fallback to string representation
        return hashlib.md5(str(key_data).encode()).hexdigest()


def clear_cache(pattern: Optional[str] = None):
    """
    Clear cached data.
    
    Args:
        pattern: Optional pattern to match cache keys (not implemented yet)
    """
    _lru_cache.clear()
    logger.info("Cache cleared")


def get_cache_stats() -> Dict[str, Any]:
    """
    Get cache statistics.
    
    Returns:
        Dictionary with cache statistics
    """
    return _lru_cache.get_stats()


class PerformanceMonitor:
    """Performance monitoring utility for tracking execution times."""
    
    def __init__(self):
        """Initialize performance monitor."""
        self.metrics = {}
    
    def record(self, operation: str, duration: float):
        """
        Record operation duration.
        
        Args:
            operation: Operation name
            duration: Duration in seconds
        """
        if operation not in self.metrics:
            self.metrics[operation] = {
                'count': 0,
                'total_time': 0,
                'min_time': float('inf'),
                'max_time': 0,
                'avg_time': 0
            }
        
        metrics = self.metrics[operation]
        metrics['count'] += 1
        metrics['total_time'] += duration
        metrics['min_time'] = min(metrics['min_time'], duration)
        metrics['max_time'] = max(metrics['max_time'], duration)
        metrics['avg_time'] = metrics['total_time'] / metrics['count']
    
    def get_metrics(self, operation: Optional[str] = None) -> Dict[str, Any]:
        """
        Get performance metrics.
        
        Args:
            operation: Optional operation name to filter
            
        Returns:
            Performance metrics
        """
        if operation:
            return self.metrics.get(operation, {})
        return self.metrics
    
    def clear(self):
        """Clear all metrics."""
        self.metrics.clear()


# Global performance monitor
_performance_monitor = PerformanceMonitor()


def monitor_performance(operation_name: Optional[str] = None):
    """
    Decorator for monitoring function performance.
    
    Args:
        operation_name: Optional operation name (defaults to function name)
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            op_name = operation_name or func.__name__
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                _performance_monitor.record(op_name, duration)
                
                # Log slow operations (> 1 second)
                if duration > 1.0:
                    logger.warning(f"Slow operation: {op_name} took {duration:.2f}s")
        
        return wrapper
    return decorator


def get_performance_metrics(operation: Optional[str] = None) -> Dict[str, Any]:
    """
    Get performance metrics.
    
    Args:
        operation: Optional operation name to filter
        
    Returns:
        Performance metrics
    """
    return _performance_monitor.get_metrics(operation)


class DataSampler:
    """Utility for sampling large datasets for visualization."""
    
    @staticmethod
    def sample_for_chart(data: List[Any], max_points: int = 1000) -> List[Any]:
        """
        Sample data for chart rendering to improve performance.
        
        Args:
            data: Original data list
            max_points: Maximum number of points to include
            
        Returns:
            Sampled data list
        """
        if len(data) <= max_points:
            return data
        
        # Calculate sampling interval
        interval = len(data) / max_points
        
        # Sample data
        sampled = []
        for i in range(max_points):
            index = int(i * interval)
            if index < len(data):
                sampled.append(data[index])
        
        logger.info(f"Sampled {len(sampled)} points from {len(data)} total")
        return sampled
    
    @staticmethod
    def paginate(data: List[Any], page: int = 1, page_size: int = 50) -> Tuple[List[Any], Dict[str, Any]]:
        """
        Paginate data for lazy loading.
        
        Args:
            data: Original data list
            page: Page number (1-indexed)
            page_size: Number of items per page
            
        Returns:
            Tuple of (paginated data, pagination metadata)
        """
        total_items = len(data)
        total_pages = (total_items + page_size - 1) // page_size
        
        # Validate page number
        page = max(1, min(page, total_pages))
        
        # Calculate slice indices
        start_idx = (page - 1) * page_size
        end_idx = min(start_idx + page_size, total_items)
        
        # Get page data
        page_data = data[start_idx:end_idx]
        
        # Create metadata
        metadata = {
            'page': page,
            'page_size': page_size,
            'total_items': total_items,
            'total_pages': total_pages,
            'has_previous': page > 1,
            'has_next': page < total_pages,
            'start_index': start_idx + 1,
            'end_index': end_idx
        }
        
        return page_data, metadata


class Debouncer:
    """Utility for debouncing user inputs."""
    
    def __init__(self, delay: float = 0.5):
        """
        Initialize debouncer.
        
        Args:
            delay: Delay in seconds before executing
        """
        self.delay = delay
        self.last_call = {}
    
    def should_execute(self, key: str) -> bool:
        """
        Check if enough time has passed since last call.
        
        Args:
            key: Unique key for the operation
            
        Returns:
            True if should execute, False otherwise
        """
        now = time.time()
        last_time = self.last_call.get(key, 0)
        
        if now - last_time >= self.delay:
            self.last_call[key] = now
            return True
        
        return False


# Global debouncer instance
_debouncer = Debouncer(delay=0.5)


def debounce(key: str, delay: float = 0.5) -> bool:
    """
    Check if operation should be debounced.
    
    Args:
        key: Unique key for the operation
        delay: Delay in seconds
        
    Returns:
        True if should execute, False if should skip
    """
    debouncer = Debouncer(delay=delay)
    return debouncer.should_execute(key)


def init_session_cache():
    """Initialize session-level cache in Streamlit session state."""
    if 'cache_initialized' not in st.session_state:
        st.session_state.cache_initialized = True
        st.session_state.cache_data = {}
        st.session_state.cache_timestamps = {}
        logger.info("Session cache initialized")


def get_session_cache(key: str, ttl: int = 300) -> Optional[Any]:
    """
    Get data from session cache.
    
    Args:
        key: Cache key
        ttl: Time to live in seconds
        
    Returns:
        Cached value or None if expired/not found
    """
    init_session_cache()
    
    if key in st.session_state.cache_data:
        timestamp = st.session_state.cache_timestamps.get(key)
        if timestamp:
            age = (datetime.now() - timestamp).total_seconds()
            if age < ttl:
                return st.session_state.cache_data[key]
    
    return None


def set_session_cache(key: str, value: Any):
    """
    Set data in session cache.
    
    Args:
        key: Cache key
        value: Value to cache
    """
    init_session_cache()
    
    st.session_state.cache_data[key] = value
    st.session_state.cache_timestamps[key] = datetime.now()


def clear_session_cache(key: Optional[str] = None):
    """
    Clear session cache.
    
    Args:
        key: Optional specific key to clear (clears all if None)
    """
    init_session_cache()
    
    if key:
        st.session_state.cache_data.pop(key, None)
        st.session_state.cache_timestamps.pop(key, None)
    else:
        st.session_state.cache_data.clear()
        st.session_state.cache_timestamps.clear()
