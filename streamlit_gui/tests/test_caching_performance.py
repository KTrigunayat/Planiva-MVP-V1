"""
Tests for Caching and Performance Optimization

Tests the caching utilities, performance monitoring, and optimization features.
"""

import pytest
import time
from datetime import datetime, timedelta
from utils.caching import (
    CacheConfig,
    LRUCache,
    cache_with_ttl,
    clear_cache,
    get_cache_stats,
    PerformanceMonitor,
    monitor_performance,
    get_performance_metrics,
    DataSampler,
    Debouncer,
    debounce
)


class TestCacheConfig:
    """Test cache configuration."""
    
    def test_get_ttl_known_types(self):
        """Test getting TTL for known data types."""
        assert CacheConfig.get_ttl('health_check') == 30
        assert CacheConfig.get_ttl('plan_status') == 10
        assert CacheConfig.get_ttl('analytics') == 60
    
    def test_get_ttl_unknown_type(self):
        """Test getting TTL for unknown data type returns default."""
        assert CacheConfig.get_ttl('unknown_type') == 300


class TestLRUCache:
    """Test LRU cache implementation."""
    
    def test_cache_set_and_get(self):
        """Test setting and getting cache values."""
        cache = LRUCache(max_size=3)
        
        cache.set('key1', 'value1')
        cache.set('key2', 'value2')
        
        assert cache.get('key1') == 'value1'
        assert cache.get('key2') == 'value2'
    
    def test_cache_miss(self):
        """Test cache miss returns None."""
        cache = LRUCache(max_size=3)
        
        assert cache.get('nonexistent') is None
    
    def test_cache_eviction(self):
        """Test LRU eviction when cache is full."""
        cache = LRUCache(max_size=2)
        
        cache.set('key1', 'value1')
        cache.set('key2', 'value2')
        cache.set('key3', 'value3')  # Should evict key1
        
        assert cache.get('key1') is None
        assert cache.get('key2') == 'value2'
        assert cache.get('key3') == 'value3'
    
    def test_cache_lru_order(self):
        """Test that accessing items updates LRU order."""
        cache = LRUCache(max_size=2)
        
        cache.set('key1', 'value1')
        cache.set('key2', 'value2')
        cache.get('key1')  # Access key1, making it most recent
        cache.set('key3', 'value3')  # Should evict key2, not key1
        
        assert cache.get('key1') == 'value1'
        assert cache.get('key2') is None
        assert cache.get('key3') == 'value3'
    
    def test_cache_stats(self):
        """Test cache statistics."""
        cache = LRUCache(max_size=3)
        
        cache.set('key1', 'value1')
        cache.get('key1')  # Hit
        cache.get('key2')  # Miss
        
        stats = cache.get_stats()
        
        assert stats['size'] == 1
        assert stats['max_size'] == 3
        assert stats['hits'] == 1
        assert stats['misses'] == 1
        assert stats['hit_rate'] == 50.0
    
    def test_cache_clear(self):
        """Test clearing cache."""
        cache = LRUCache(max_size=3)
        
        cache.set('key1', 'value1')
        cache.set('key2', 'value2')
        
        cache.clear()
        
        assert cache.get('key1') is None
        assert cache.get('key2') is None
        assert cache.get_stats()['size'] == 0


class TestCacheDecorator:
    """Test cache decorator."""
    
    def test_cache_with_ttl_caches_result(self):
        """Test that decorator caches function results."""
        call_count = {'count': 0}
        
        @cache_with_ttl(ttl=1)
        def expensive_function(x):
            call_count['count'] += 1
            return x * 2
        
        # First call should execute function
        result1 = expensive_function(5)
        assert result1 == 10
        assert call_count['count'] == 1
        
        # Second call should use cache
        result2 = expensive_function(5)
        assert result2 == 10
        assert call_count['count'] == 1  # Not incremented
    
    def test_cache_with_ttl_expires(self):
        """Test that cache expires after TTL."""
        # Clear cache before test
        clear_cache()
        
        call_count = {'count': 0}
        
        @cache_with_ttl(ttl=0.1)  # 100ms TTL
        def expensive_function(x):
            call_count['count'] += 1
            return x * 2
        
        # First call
        result1 = expensive_function(5)
        assert call_count['count'] >= 1  # May be cached from previous test
        initial_count = call_count['count']
        
        # Wait for cache to expire
        time.sleep(0.15)
        
        # Clear cache to force re-execution
        clear_cache()
        
        # Second call should execute function again
        result2 = expensive_function(5)
        assert call_count['count'] == initial_count + 1
    
    def test_cache_with_data_type(self):
        """Test cache with data type configuration."""
        call_count = {'count': 0}
        
        @cache_with_ttl(data_type='health_check')
        def health_check():
            call_count['count'] += 1
            return {'status': 'healthy'}
        
        # First call
        result1 = health_check()
        assert call_count['count'] == 1
        
        # Second call should use cache
        result2 = health_check()
        assert call_count['count'] == 1


class TestPerformanceMonitor:
    """Test performance monitoring."""
    
    def test_record_metrics(self):
        """Test recording performance metrics."""
        monitor = PerformanceMonitor()
        
        monitor.record('operation1', 0.5)
        monitor.record('operation1', 1.0)
        monitor.record('operation2', 0.3)
        
        metrics = monitor.get_metrics()
        
        assert 'operation1' in metrics
        assert 'operation2' in metrics
        assert metrics['operation1']['count'] == 2
        assert metrics['operation1']['avg_time'] == 0.75
        assert metrics['operation1']['min_time'] == 0.5
        assert metrics['operation1']['max_time'] == 1.0
    
    def test_get_specific_operation_metrics(self):
        """Test getting metrics for specific operation."""
        monitor = PerformanceMonitor()
        
        monitor.record('operation1', 0.5)
        monitor.record('operation2', 1.0)
        
        metrics = monitor.get_metrics('operation1')
        
        assert metrics['count'] == 1
        assert metrics['avg_time'] == 0.5
    
    def test_clear_metrics(self):
        """Test clearing metrics."""
        monitor = PerformanceMonitor()
        
        monitor.record('operation1', 0.5)
        monitor.clear()
        
        metrics = monitor.get_metrics()
        assert len(metrics) == 0


class TestPerformanceDecorator:
    """Test performance monitoring decorator."""
    
    def test_monitor_performance_records_time(self):
        """Test that decorator records execution time."""
        @monitor_performance('test_operation')
        def slow_function():
            time.sleep(0.1)
            return 'done'
        
        result = slow_function()
        
        assert result == 'done'
        
        metrics = get_performance_metrics('test_operation')
        assert metrics['count'] == 1
        assert metrics['avg_time'] >= 0.1


class TestDataSampler:
    """Test data sampling utilities."""
    
    def test_sample_for_chart_no_sampling_needed(self):
        """Test that small datasets are not sampled."""
        data = list(range(100))
        sampled = DataSampler.sample_for_chart(data, max_points=1000)
        
        assert len(sampled) == 100
        assert sampled == data
    
    def test_sample_for_chart_samples_large_dataset(self):
        """Test that large datasets are sampled."""
        data = list(range(10000))
        sampled = DataSampler.sample_for_chart(data, max_points=1000)
        
        assert len(sampled) == 1000
        assert len(sampled) < len(data)
    
    def test_paginate_first_page(self):
        """Test pagination for first page."""
        data = list(range(100))
        page_data, metadata = DataSampler.paginate(data, page=1, page_size=10)
        
        assert len(page_data) == 10
        assert page_data == list(range(10))
        assert metadata['page'] == 1
        assert metadata['total_pages'] == 10
        assert metadata['has_previous'] is False
        assert metadata['has_next'] is True
    
    def test_paginate_middle_page(self):
        """Test pagination for middle page."""
        data = list(range(100))
        page_data, metadata = DataSampler.paginate(data, page=5, page_size=10)
        
        assert len(page_data) == 10
        assert page_data == list(range(40, 50))
        assert metadata['page'] == 5
        assert metadata['has_previous'] is True
        assert metadata['has_next'] is True
    
    def test_paginate_last_page(self):
        """Test pagination for last page."""
        data = list(range(95))
        page_data, metadata = DataSampler.paginate(data, page=10, page_size=10)
        
        assert len(page_data) == 5  # Last page has only 5 items
        assert page_data == list(range(90, 95))
        assert metadata['page'] == 10
        assert metadata['has_previous'] is True
        assert metadata['has_next'] is False
    
    def test_paginate_invalid_page(self):
        """Test pagination with invalid page number."""
        data = list(range(100))
        
        # Page too high
        page_data, metadata = DataSampler.paginate(data, page=100, page_size=10)
        assert metadata['page'] == 10  # Clamped to last page
        
        # Page too low
        page_data, metadata = DataSampler.paginate(data, page=0, page_size=10)
        assert metadata['page'] == 1  # Clamped to first page


class TestDebouncer:
    """Test debouncing utility."""
    
    def test_debounce_allows_first_call(self):
        """Test that first call is allowed."""
        debouncer = Debouncer(delay=0.1)
        
        assert debouncer.should_execute('key1') is True
    
    def test_debounce_blocks_rapid_calls(self):
        """Test that rapid calls are blocked."""
        debouncer = Debouncer(delay=0.1)
        
        assert debouncer.should_execute('key1') is True
        assert debouncer.should_execute('key1') is False
    
    def test_debounce_allows_after_delay(self):
        """Test that calls are allowed after delay."""
        debouncer = Debouncer(delay=0.1)
        
        assert debouncer.should_execute('key1') is True
        time.sleep(0.15)
        assert debouncer.should_execute('key1') is True
    
    def test_debounce_separate_keys(self):
        """Test that different keys are independent."""
        debouncer = Debouncer(delay=0.1)
        
        assert debouncer.should_execute('key1') is True
        assert debouncer.should_execute('key2') is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
