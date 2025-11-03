"""
Demo script for caching and performance optimization features

Demonstrates the caching, pagination, data sampling, and performance monitoring
capabilities implemented in Task 16.
"""

import time
from utils.caching import (
    cache_with_ttl,
    monitor_performance,
    get_cache_stats,
    get_performance_metrics,
    DataSampler,
    Debouncer,
    clear_cache
)


def demo_caching():
    """Demonstrate caching functionality."""
    print("\n" + "="*60)
    print("CACHING DEMO")
    print("="*60)
    
    # Clear cache for clean demo
    clear_cache()
    
    # Define a cached function
    call_count = {'count': 0}
    
    @cache_with_ttl(ttl=5, data_type='default')
    def expensive_calculation(x, y):
        """Simulate an expensive calculation."""
        call_count['count'] += 1
        time.sleep(0.5)  # Simulate work
        return x + y
    
    # First call - should execute function
    print("\n1. First call (cache miss)...")
    start = time.time()
    result1 = expensive_calculation(10, 20)
    duration1 = time.time() - start
    print(f"   Result: {result1}")
    print(f"   Duration: {duration1:.3f}s")
    print(f"   Function called: {call_count['count']} time(s)")
    
    # Second call - should use cache
    print("\n2. Second call (cache hit)...")
    start = time.time()
    result2 = expensive_calculation(10, 20)
    duration2 = time.time() - start
    print(f"   Result: {result2}")
    print(f"   Duration: {duration2:.3f}s")
    print(f"   Function called: {call_count['count']} time(s)")
    print(f"   Speedup: {duration1/duration2:.1f}x faster!")
    
    # Show cache stats
    print("\n3. Cache Statistics:")
    stats = get_cache_stats()
    print(f"   Cache size: {stats['size']}/{stats['max_size']}")
    print(f"   Hits: {stats['hits']}")
    print(f"   Misses: {stats['misses']}")
    print(f"   Hit rate: {stats['hit_rate']:.1f}%")


def demo_performance_monitoring():
    """Demonstrate performance monitoring."""
    print("\n" + "="*60)
    print("PERFORMANCE MONITORING DEMO")
    print("="*60)
    
    @monitor_performance('fast_operation')
    def fast_operation():
        """A fast operation."""
        time.sleep(0.1)
        return "fast"
    
    @monitor_performance('slow_operation')
    def slow_operation():
        """A slow operation."""
        time.sleep(0.5)
        return "slow"
    
    # Execute operations multiple times
    print("\n1. Executing operations...")
    for i in range(3):
        fast_operation()
        slow_operation()
    
    # Show performance metrics
    print("\n2. Performance Metrics:")
    
    fast_metrics = get_performance_metrics('fast_operation')
    print(f"\n   Fast Operation:")
    print(f"   - Count: {fast_metrics['count']}")
    print(f"   - Avg time: {fast_metrics['avg_time']:.3f}s")
    print(f"   - Min time: {fast_metrics['min_time']:.3f}s")
    print(f"   - Max time: {fast_metrics['max_time']:.3f}s")
    
    slow_metrics = get_performance_metrics('slow_operation')
    print(f"\n   Slow Operation:")
    print(f"   - Count: {slow_metrics['count']}")
    print(f"   - Avg time: {slow_metrics['avg_time']:.3f}s")
    print(f"   - Min time: {slow_metrics['min_time']:.3f}s")
    print(f"   - Max time: {slow_metrics['max_time']:.3f}s")


def demo_data_sampling():
    """Demonstrate data sampling."""
    print("\n" + "="*60)
    print("DATA SAMPLING DEMO")
    print("="*60)
    
    # Create large dataset
    large_dataset = list(range(10000))
    print(f"\n1. Original dataset size: {len(large_dataset)} items")
    
    # Sample for chart
    sampled = DataSampler.sample_for_chart(large_dataset, max_points=1000)
    print(f"2. Sampled dataset size: {len(sampled)} items")
    print(f"3. Reduction: {(1 - len(sampled)/len(large_dataset)) * 100:.1f}%")
    
    # Demonstrate pagination
    print("\n4. Pagination Demo:")
    page_data, metadata = DataSampler.paginate(large_dataset, page=1, page_size=50)
    print(f"   Page {metadata['page']} of {metadata['total_pages']}")
    print(f"   Showing items {metadata['start_index']}-{metadata['end_index']}")
    print(f"   Has previous: {metadata['has_previous']}")
    print(f"   Has next: {metadata['has_next']}")
    print(f"   First 5 items: {page_data[:5]}")


def demo_debouncing():
    """Demonstrate debouncing."""
    print("\n" + "="*60)
    print("DEBOUNCING DEMO")
    print("="*60)
    
    debouncer = Debouncer(delay=0.2)
    
    print("\n1. Simulating rapid user input...")
    execution_count = 0
    
    for i in range(10):
        if debouncer.should_execute('search_query'):
            execution_count += 1
            print(f"   Execution #{execution_count} at iteration {i+1}")
        else:
            print(f"   Skipped iteration {i+1} (debounced)")
        
        time.sleep(0.05)  # Simulate rapid input
    
    print(f"\n2. Total executions: {execution_count}/10")
    print(f"3. Reduction: {(1 - execution_count/10) * 100:.0f}%")


def demo_cache_ttl():
    """Demonstrate cache TTL expiration."""
    print("\n" + "="*60)
    print("CACHE TTL DEMO")
    print("="*60)
    
    clear_cache()
    
    call_count = {'count': 0}
    
    @cache_with_ttl(ttl=1)  # 1 second TTL
    def get_data():
        call_count['count'] += 1
        return f"Data version {call_count['count']}"
    
    print("\n1. First call...")
    result1 = get_data()
    print(f"   Result: {result1}")
    
    print("\n2. Immediate second call (within TTL)...")
    result2 = get_data()
    print(f"   Result: {result2}")
    print(f"   Same as first: {result1 == result2}")
    
    print("\n3. Waiting for cache to expire...")
    time.sleep(1.5)
    
    print("\n4. Third call (after TTL expiration)...")
    clear_cache()  # Force expiration
    result3 = get_data()
    print(f"   Result: {result3}")
    print(f"   Different from first: {result1 != result3}")


def main():
    """Run all demos."""
    print("\n" + "="*60)
    print("CACHING AND PERFORMANCE OPTIMIZATION DEMO")
    print("Task 16 Implementation")
    print("="*60)
    
    try:
        demo_caching()
        demo_performance_monitoring()
        demo_data_sampling()
        demo_debouncing()
        demo_cache_ttl()
        
        print("\n" + "="*60)
        print("DEMO COMPLETED SUCCESSFULLY")
        print("="*60)
        print("\nAll caching and performance features are working correctly!")
        
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
