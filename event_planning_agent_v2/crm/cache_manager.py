"""
Redis Cache Manager for CRM Communication Engine

Handles caching of client preferences and email templates with TTL management.
Includes connection pooling for better performance and reliability.
"""

import logging
import json
from typing import Optional, Any
from datetime import timedelta

try:
    import redis
    from redis.connection import ConnectionPool
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None
    ConnectionPool = None

from .models import ClientPreferences, MessageChannel

logger = logging.getLogger(__name__)


class CRMCacheManager:
    """
    Redis cache manager for CRM data.
    
    Caches:
    - Client preferences (1-hour TTL)
    - Email templates (indefinite TTL with manual invalidation)
    - Rate limit counters (API quota tracking)
    """
    
    # Cache key prefixes
    PREF_KEY_PREFIX = "crm:prefs:"
    TEMPLATE_KEY_PREFIX = "crm:template:"
    RATE_LIMIT_KEY_PREFIX = "crm:ratelimit:"
    
    # TTL values (in seconds)
    PREFERENCE_TTL = 3600  # 1 hour
    TEMPLATE_TTL = None  # Indefinite (manual invalidation)
    RATE_LIMIT_TTL = 60  # 1 minute
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        enabled: bool = True,
        max_connections: int = 10,
        socket_timeout: int = 5,
        socket_connect_timeout: int = 5
    ):
        """
        Initialize cache manager with Redis connection pooling.
        
        Args:
            redis_url: Redis connection URL
            enabled: Whether caching is enabled (for testing/development)
            max_connections: Maximum connections in the pool
            socket_timeout: Socket timeout in seconds
            socket_connect_timeout: Socket connect timeout in seconds
        """
        self.enabled = enabled and REDIS_AVAILABLE
        self.redis_client = None
        self.connection_pool = None
        self.redis_url = redis_url
        
        # Cache statistics
        self.cache_hits = 0
        self.cache_misses = 0
        
        if not REDIS_AVAILABLE:
            logger.warning("Redis module not available, caching disabled")
            self.enabled = False
            return
        
        if self.enabled:
            try:
                # Create connection pool for better performance
                self.connection_pool = ConnectionPool.from_url(
                    redis_url,
                    max_connections=max_connections,
                    socket_timeout=socket_timeout,
                    socket_connect_timeout=socket_connect_timeout,
                    decode_responses=True
                )
                
                # Create Redis client with connection pool
                self.redis_client = redis.Redis(
                    connection_pool=self.connection_pool
                )
                
                # Test connection
                self.redis_client.ping()
                logger.info(
                    f"Redis cache manager initialized with connection pool: "
                    f"{redis_url} (max_connections={max_connections})"
                )
            except (redis.ConnectionError, redis.TimeoutError) as e:
                logger.warning(f"Failed to connect to Redis, caching disabled: {e}")
                self.enabled = False
                self.redis_client = None
                self.connection_pool = None
        else:
            logger.info("Redis cache manager disabled")
    
    def _get_preference_key(self, client_id: str) -> str:
        """Generate cache key for client preferences"""
        return f"{self.PREF_KEY_PREFIX}{client_id}"
    
    def _get_template_key(self, template_name: str, channel: str) -> str:
        """Generate cache key for templates"""
        return f"{self.TEMPLATE_KEY_PREFIX}{channel}:{template_name}"
    
    def _get_rate_limit_key(self, api: str, window: str) -> str:
        """Generate cache key for rate limits"""
        return f"{self.RATE_LIMIT_KEY_PREFIX}{api}:{window}"
    
    def get_client_preferences(
        self,
        client_id: str
    ) -> Optional[ClientPreferences]:
        """
        Get client preferences from cache.
        
        Args:
            client_id: Client identifier
            
        Returns:
            ClientPreferences if found in cache, None otherwise
        """
        if not self.enabled or not self.redis_client:
            return None
        
        try:
            key = self._get_preference_key(client_id)
            cached_data = self.redis_client.get(key)
            
            if cached_data:
                self.cache_hits += 1
                logger.debug(f"Cache HIT for client preferences: {client_id}")
                data = json.loads(cached_data)
                
                # Reconstruct ClientPreferences object
                preferences = ClientPreferences(
                    client_id=data['client_id'],
                    preferred_channels=[MessageChannel(ch) for ch in data['preferred_channels']],
                    timezone=data['timezone'],
                    quiet_hours_start=data['quiet_hours_start'],
                    quiet_hours_end=data['quiet_hours_end'],
                    opt_out_email=data['opt_out_email'],
                    opt_out_sms=data['opt_out_sms'],
                    opt_out_whatsapp=data['opt_out_whatsapp'],
                    language_preference=data.get('language_preference', 'en')
                )
                
                return preferences
            else:
                self.cache_misses += 1
                logger.debug(f"Cache MISS for client preferences: {client_id}")
                return None
                
        except (redis.RedisError, json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to get preferences from cache: {e}")
            return None
    
    def set_client_preferences(
        self,
        preferences: ClientPreferences
    ) -> bool:
        """
        Store client preferences in cache with TTL.
        
        Args:
            preferences: ClientPreferences object to cache
            
        Returns:
            True if cached successfully, False otherwise
        """
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            key = self._get_preference_key(preferences.client_id)
            
            # Serialize preferences to JSON
            data = {
                'client_id': preferences.client_id,
                'preferred_channels': [ch.value for ch in preferences.preferred_channels],
                'timezone': preferences.timezone,
                'quiet_hours_start': preferences.quiet_hours_start,
                'quiet_hours_end': preferences.quiet_hours_end,
                'opt_out_email': preferences.opt_out_email,
                'opt_out_sms': preferences.opt_out_sms,
                'opt_out_whatsapp': preferences.opt_out_whatsapp,
                'language_preference': preferences.language_preference
            }
            
            cached_data = json.dumps(data)
            
            # Set with TTL
            self.redis_client.setex(
                key,
                self.PREFERENCE_TTL,
                cached_data
            )
            
            logger.debug(f"Cached client preferences: {preferences.client_id} (TTL: {self.PREFERENCE_TTL}s)")
            return True
            
        except (redis.RedisError, json.JSONEncodeError) as e:
            logger.warning(f"Failed to cache preferences: {e}")
            return False
    
    def invalidate_client_preferences(
        self,
        client_id: str
    ) -> bool:
        """
        Invalidate cached client preferences.
        
        Args:
            client_id: Client identifier
            
        Returns:
            True if invalidated successfully, False otherwise
        """
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            key = self._get_preference_key(client_id)
            deleted = self.redis_client.delete(key)
            
            if deleted:
                logger.debug(f"Invalidated cache for client preferences: {client_id}")
            
            return bool(deleted)
            
        except redis.RedisError as e:
            logger.warning(f"Failed to invalidate preferences cache: {e}")
            return False
    
    def get_template(
        self,
        template_name: str,
        channel: str
    ) -> Optional[str]:
        """
        Get template content from cache.
        
        Args:
            template_name: Name of the template
            channel: Communication channel (email, sms, whatsapp)
            
        Returns:
            Template content if found, None otherwise
        """
        if not self.enabled or not self.redis_client:
            return None
        
        try:
            key = self._get_template_key(template_name, channel)
            cached_template = self.redis_client.get(key)
            
            if cached_template:
                self.cache_hits += 1
                logger.debug(f"Cache HIT for template: {template_name} ({channel})")
                return cached_template
            else:
                self.cache_misses += 1
                logger.debug(f"Cache MISS for template: {template_name} ({channel})")
                return None
                
        except redis.RedisError as e:
            logger.warning(f"Failed to get template from cache: {e}")
            return None
    
    def set_template(
        self,
        template_name: str,
        channel: str,
        content: str
    ) -> bool:
        """
        Store template content in cache (indefinite TTL).
        
        Args:
            template_name: Name of the template
            channel: Communication channel
            content: Template content
            
        Returns:
            True if cached successfully, False otherwise
        """
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            key = self._get_template_key(template_name, channel)
            self.redis_client.set(key, content)
            
            logger.debug(f"Cached template: {template_name} ({channel})")
            return True
            
        except redis.RedisError as e:
            logger.warning(f"Failed to cache template: {e}")
            return False
    
    def invalidate_template(
        self,
        template_name: str,
        channel: str
    ) -> bool:
        """
        Invalidate cached template.
        
        Args:
            template_name: Name of the template
            channel: Communication channel
            
        Returns:
            True if invalidated successfully, False otherwise
        """
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            key = self._get_template_key(template_name, channel)
            deleted = self.redis_client.delete(key)
            
            if deleted:
                logger.debug(f"Invalidated cache for template: {template_name} ({channel})")
            
            return bool(deleted)
            
        except redis.RedisError as e:
            logger.warning(f"Failed to invalidate template cache: {e}")
            return False
    
    def check_rate_limit(
        self,
        api: str,
        limit: int,
        window: int = 60
    ) -> tuple[bool, int]:
        """
        Check if API rate limit allows request.
        
        Args:
            api: API identifier (e.g., 'whatsapp', 'twilio')
            limit: Maximum requests allowed in window
            window: Time window in seconds (default: 60)
            
        Returns:
            Tuple of (allowed: bool, current_count: int)
        """
        if not self.enabled or not self.redis_client:
            # If cache disabled, allow all requests
            return True, 0
        
        try:
            key = self._get_rate_limit_key(api, str(window))
            
            # Increment counter
            current = self.redis_client.incr(key)
            
            # Set expiry on first increment
            if current == 1:
                self.redis_client.expire(key, window)
            
            allowed = current <= limit
            
            if not allowed:
                logger.warning(
                    f"Rate limit exceeded for {api}: {current}/{limit} in {window}s window"
                )
            
            return allowed, current
            
        except redis.RedisError as e:
            logger.warning(f"Failed to check rate limit: {e}")
            # On error, allow request
            return True, 0
    
    def get_cache_stats(self) -> dict:
        """
        Get cache statistics including local and Redis stats.
        
        Returns:
            Dictionary with cache statistics
        """
        if not self.enabled or not self.redis_client:
            return {
                'enabled': False,
                'connected': False
            }
        
        try:
            info = self.redis_client.info('stats')
            
            # Get connection pool stats
            pool_stats = {}
            if self.connection_pool:
                pool_stats = {
                    'max_connections': self.connection_pool.max_connections,
                    'connection_kwargs': {
                        'socket_timeout': self.connection_pool.connection_kwargs.get('socket_timeout'),
                        'socket_connect_timeout': self.connection_pool.connection_kwargs.get('socket_connect_timeout')
                    }
                }
            
            return {
                'enabled': True,
                'connected': True,
                'total_keys': self.redis_client.dbsize(),
                'redis_hits': info.get('keyspace_hits', 0),
                'redis_misses': info.get('keyspace_misses', 0),
                'redis_hit_rate': self._calculate_hit_rate(
                    info.get('keyspace_hits', 0),
                    info.get('keyspace_misses', 0)
                ),
                'local_hits': self.cache_hits,
                'local_misses': self.cache_misses,
                'local_hit_rate': self._calculate_hit_rate(
                    self.cache_hits,
                    self.cache_misses
                ),
                'connection_pool': pool_stats
            }
            
        except redis.RedisError as e:
            logger.warning(f"Failed to get cache stats: {e}")
            return {
                'enabled': True,
                'connected': False,
                'error': str(e)
            }
    
    def _calculate_hit_rate(self, hits: int, misses: int) -> float:
        """Calculate cache hit rate percentage"""
        total = hits + misses
        if total == 0:
            return 0.0
        return round((hits / total) * 100, 2)
    
    def clear_all(self) -> bool:
        """
        Clear all CRM cache entries (use with caution).
        
        Returns:
            True if cleared successfully, False otherwise
        """
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            # Delete all keys matching CRM prefixes
            patterns = [
                f"{self.PREF_KEY_PREFIX}*",
                f"{self.TEMPLATE_KEY_PREFIX}*",
                f"{self.RATE_LIMIT_KEY_PREFIX}*"
            ]
            
            total_deleted = 0
            for pattern in patterns:
                keys = self.redis_client.keys(pattern)
                if keys:
                    deleted = self.redis_client.delete(*keys)
                    total_deleted += deleted
            
            logger.info(f"Cleared {total_deleted} CRM cache entries")
            return True
            
        except redis.RedisError as e:
            logger.warning(f"Failed to clear cache: {e}")
            return False
    
    def health_check(self) -> bool:
        """
        Check if Redis connection is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            self.redis_client.ping()
            return True
        except redis.RedisError:
            return False
    
    def close(self) -> None:
        """
        Close Redis connection and cleanup connection pool.
        Should be called on application shutdown.
        """
        if self.connection_pool:
            try:
                self.connection_pool.disconnect()
                logger.info("Redis connection pool closed")
            except Exception as e:
                logger.warning(f"Error closing connection pool: {e}")
        
        self.redis_client = None
        self.connection_pool = None
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup resources"""
        self.close()
        return False


# Global cache manager instance
_cache_manager: Optional[CRMCacheManager] = None


def get_cache_manager(redis_url: str = "redis://localhost:6379/0") -> CRMCacheManager:
    """
    Get or create global cache manager instance.
    
    Args:
        redis_url: Redis connection URL
        
    Returns:
        CRMCacheManager instance
    """
    global _cache_manager
    
    if _cache_manager is None:
        _cache_manager = CRMCacheManager(redis_url=redis_url)
    
    return _cache_manager
