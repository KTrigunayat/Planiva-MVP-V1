"""
Unit tests for Redis Cache Manager.

Tests cache operations for client preferences, email templates, and rate limiting.
"""

import pytest
import json
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from event_planning_agent_v2.crm.cache_manager import CRMCacheManager
from event_planning_agent_v2.crm.models import ClientPreferences, MessageChannel


class TestCRMCacheManager:
    """Test suite for CRM Cache Manager."""
    
    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis client."""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.get.return_value = None
        mock_client.set.return_value = True
        mock_client.setex.return_value = True
        mock_client.delete.return_value = 1
        mock_client.incr.return_value = 1
        mock_client.expire.return_value = True
        mock_client.dbsize.return_value = 10
        mock_client.info.return_value = {
            'keyspace_hits': 100,
            'keyspace_misses': 20
        }
        mock_client.keys.return_value = []
        return mock_client
    
    @pytest.fixture
    def mock_connection_pool(self):
        """Create a mock connection pool."""
        mock_pool = MagicMock()
        mock_pool.max_connections = 10
        mock_pool.connection_kwargs = {
            'socket_timeout': 5,
            'socket_connect_timeout': 5
        }
        mock_pool.disconnect.return_value = None
        return mock_pool
    
    @pytest.fixture
    def cache_manager(self, mock_redis, mock_connection_pool):
        """Create cache manager with mocked Redis."""
        with patch('event_planning_agent_v2.crm.cache_manager.REDIS_AVAILABLE', True):
            with patch('event_planning_agent_v2.crm.cache_manager.redis') as mock_redis_module:
                with patch('event_planning_agent_v2.crm.cache_manager.ConnectionPool') as mock_pool_class:
                    mock_redis_module.Redis.return_value = mock_redis
                    mock_redis_module.RedisError = Exception
                    mock_redis_module.ConnectionError = ConnectionError
                    mock_redis_module.TimeoutError = TimeoutError
                    mock_pool_class.from_url.return_value = mock_connection_pool
                    
                    manager = CRMCacheManager(
                        redis_url="redis://localhost:6379/0",
                        enabled=True,
                        max_connections=10
                    )
                    manager.redis_client = mock_redis
                    manager.connection_pool = mock_connection_pool
                    manager.enabled = True
                    
                    return manager
    
    @pytest.fixture
    def sample_preferences(self):
        """Create sample client preferences."""
        return ClientPreferences(
            client_id="client-123",
            preferred_channels=[MessageChannel.EMAIL, MessageChannel.WHATSAPP],
            timezone="America/New_York",
            quiet_hours_start="22:00",
            quiet_hours_end="08:00",
            opt_out_email=False,
            opt_out_sms=False,
            opt_out_whatsapp=False,
            language_preference="en"
        )
    
    def test_initialization_with_connection_pool(self, mock_redis, mock_connection_pool):
        """Test cache manager initializes with connection pooling."""
        with patch('event_planning_agent_v2.crm.cache_manager.REDIS_AVAILABLE', True):
            with patch('event_planning_agent_v2.crm.cache_manager.redis') as mock_redis_module:
                with patch('event_planning_agent_v2.crm.cache_manager.ConnectionPool') as mock_pool_class:
                    mock_redis_module.Redis.return_value = mock_redis
                    mock_redis_module.ConnectionError = ConnectionError
                    mock_redis_module.TimeoutError = TimeoutError
                    mock_pool_class.from_url.return_value = mock_connection_pool
                    
                    manager = CRMCacheManager(
                        redis_url="redis://localhost:6379/0",
                        enabled=True,
                        max_connections=20,
                        socket_timeout=10
                    )
                    
                    assert manager.enabled is True
                    assert manager.redis_client is not None
                    assert manager.connection_pool is not None
                    mock_pool_class.from_url.assert_called_once()
    
    def test_get_client_preferences_cache_hit(self, cache_manager, sample_preferences, mock_redis):
        """Test getting client preferences from cache (cache hit)."""
        # Setup mock to return cached data
        cached_data = json.dumps({
            'client_id': sample_preferences.client_id,
            'preferred_channels': [ch.value for ch in sample_preferences.preferred_channels],
            'timezone': sample_preferences.timezone,
            'quiet_hours_start': sample_preferences.quiet_hours_start,
            'quiet_hours_end': sample_preferences.quiet_hours_end,
            'opt_out_email': sample_preferences.opt_out_email,
            'opt_out_sms': sample_preferences.opt_out_sms,
            'opt_out_whatsapp': sample_preferences.opt_out_whatsapp,
            'language_preference': sample_preferences.language_preference
        })
        mock_redis.get.return_value = cached_data
        
        # Get preferences
        result = cache_manager.get_client_preferences("client-123")
        
        # Verify
        assert result is not None
        assert result.client_id == sample_preferences.client_id
        assert result.timezone == sample_preferences.timezone
        assert cache_manager.cache_hits == 1
        assert cache_manager.cache_misses == 0
    
    def test_get_client_preferences_cache_miss(self, cache_manager, mock_redis):
        """Test getting client preferences when not in cache (cache miss)."""
        mock_redis.get.return_value = None
        
        result = cache_manager.get_client_preferences("client-456")
        
        assert result is None
        assert cache_manager.cache_hits == 0
        assert cache_manager.cache_misses == 1
    
    def test_set_client_preferences(self, cache_manager, sample_preferences, mock_redis):
        """Test caching client preferences with TTL."""
        success = cache_manager.set_client_preferences(sample_preferences)
        
        assert success is True
        mock_redis.setex.assert_called_once()
        
        # Verify TTL is set correctly
        call_args = mock_redis.setex.call_args
        assert call_args[0][1] == cache_manager.PREFERENCE_TTL  # 1 hour
    
    def test_invalidate_client_preferences(self, cache_manager, mock_redis):
        """Test invalidating cached client preferences."""
        mock_redis.delete.return_value = 1
        
        success = cache_manager.invalidate_client_preferences("client-123")
        
        assert success is True
        mock_redis.delete.assert_called_once()
    
    def test_get_template_cache_hit(self, cache_manager, mock_redis):
        """Test getting template from cache (cache hit)."""
        template_content = "<html><body>Welcome {{client_name}}!</body></html>"
        mock_redis.get.return_value = template_content
        
        result = cache_manager.get_template("welcome", "email")
        
        assert result == template_content
        assert cache_manager.cache_hits == 1
    
    def test_get_template_cache_miss(self, cache_manager, mock_redis):
        """Test getting template when not in cache (cache miss)."""
        mock_redis.get.return_value = None
        
        result = cache_manager.get_template("budget_summary", "email")
        
        assert result is None
        assert cache_manager.cache_misses == 1
    
    def test_set_template(self, cache_manager, mock_redis):
        """Test caching template with indefinite TTL."""
        template_content = "<html><body>Test template</body></html>"
        
        success = cache_manager.set_template("test", "email", template_content)
        
        assert success is True
        mock_redis.set.assert_called_once()
    
    def test_invalidate_template(self, cache_manager, mock_redis):
        """Test invalidating cached template."""
        mock_redis.delete.return_value = 1
        
        success = cache_manager.invalidate_template("welcome", "email")
        
        assert success is True
        mock_redis.delete.assert_called_once()
    
    def test_check_rate_limit_allowed(self, cache_manager, mock_redis):
        """Test rate limit check when under limit."""
        mock_redis.incr.return_value = 5  # Under limit
        
        allowed, count = cache_manager.check_rate_limit("whatsapp", limit=10, window=60)
        
        assert allowed is True
        assert count == 5
        mock_redis.incr.assert_called_once()
    
    def test_check_rate_limit_exceeded(self, cache_manager, mock_redis):
        """Test rate limit check when limit exceeded."""
        mock_redis.incr.return_value = 15  # Over limit
        
        allowed, count = cache_manager.check_rate_limit("twilio", limit=10, window=60)
        
        assert allowed is False
        assert count == 15
    
    def test_check_rate_limit_first_request(self, cache_manager, mock_redis):
        """Test rate limit check sets expiry on first request."""
        mock_redis.incr.return_value = 1  # First request
        
        allowed, count = cache_manager.check_rate_limit("smtp", limit=100, window=3600)
        
        assert allowed is True
        assert count == 1
        mock_redis.expire.assert_called_once_with(
            cache_manager._get_rate_limit_key("smtp", "3600"),
            3600
        )
    
    def test_get_cache_stats(self, cache_manager, mock_redis, mock_connection_pool):
        """Test getting cache statistics."""
        cache_manager.cache_hits = 50
        cache_manager.cache_misses = 10
        
        stats = cache_manager.get_cache_stats()
        
        assert stats['enabled'] is True
        assert stats['connected'] is True
        assert stats['total_keys'] == 10
        assert stats['redis_hits'] == 100
        assert stats['redis_misses'] == 20
        assert stats['local_hits'] == 50
        assert stats['local_misses'] == 10
        assert 'connection_pool' in stats
    
    def test_clear_all(self, cache_manager, mock_redis):
        """Test clearing all CRM cache entries."""
        mock_redis.keys.side_effect = [
            ['crm:prefs:client1', 'crm:prefs:client2'],
            ['crm:template:email:welcome'],
            ['crm:ratelimit:whatsapp:60']
        ]
        mock_redis.delete.return_value = 4
        
        success = cache_manager.clear_all()
        
        assert success is True
        assert mock_redis.keys.call_count == 3
    
    def test_health_check_healthy(self, cache_manager, mock_redis):
        """Test health check when Redis is healthy."""
        # Reset the mock to clear the ping call from initialization
        mock_redis.ping.reset_mock()
        mock_redis.ping.return_value = True
        
        is_healthy = cache_manager.health_check()
        
        assert is_healthy is True
        mock_redis.ping.assert_called_once()
    
    def test_health_check_unhealthy(self, cache_manager, mock_redis):
        """Test health check when Redis is unhealthy."""
        with patch('event_planning_agent_v2.crm.cache_manager.redis') as mock_redis_module:
            # Mock RedisError exception class
            mock_redis_module.RedisError = Exception
            mock_redis.ping.side_effect = Exception("Connection failed")
            
            is_healthy = cache_manager.health_check()
            
            assert is_healthy is False
    
    def test_close_connection_pool(self, cache_manager, mock_connection_pool):
        """Test closing connection pool on cleanup."""
        cache_manager.close()
        
        mock_connection_pool.disconnect.assert_called_once()
        assert cache_manager.redis_client is None
        assert cache_manager.connection_pool is None
    
    def test_context_manager(self, mock_redis, mock_connection_pool):
        """Test cache manager as context manager."""
        with patch('event_planning_agent_v2.crm.cache_manager.REDIS_AVAILABLE', True):
            with patch('event_planning_agent_v2.crm.cache_manager.redis') as mock_redis_module:
                with patch('event_planning_agent_v2.crm.cache_manager.ConnectionPool') as mock_pool_class:
                    mock_redis_module.Redis.return_value = mock_redis
                    mock_redis_module.ConnectionError = ConnectionError
                    mock_redis_module.TimeoutError = TimeoutError
                    mock_pool_class.from_url.return_value = mock_connection_pool
                    
                    with CRMCacheManager(redis_url="redis://localhost:6379/0") as manager:
                        assert manager.enabled is True
                    
                    # Verify cleanup was called
                    mock_connection_pool.disconnect.assert_called_once()
    
    def test_disabled_cache_manager(self):
        """Test cache manager when caching is disabled."""
        manager = CRMCacheManager(enabled=False)
        
        assert manager.enabled is False
        assert manager.redis_client is None
        
        # All operations should return None/False gracefully
        assert manager.get_client_preferences("client-123") is None
        assert manager.set_client_preferences(Mock()) is False
        assert manager.get_template("welcome", "email") is None
        
        # Rate limit should allow all requests when disabled
        allowed, count = manager.check_rate_limit("api", 10, 60)
        assert allowed is True
        assert count == 0
