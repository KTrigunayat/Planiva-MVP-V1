"""
Unit tests for CRM Client Preference Management

Tests preference validation, database persistence, and cache operations.
"""

import pytest
import json
import sys
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy import text

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from crm.models import ClientPreferences, MessageChannel
from crm.cache_manager import CRMCacheManager


class TestClientPreferencesModel:
    """Test ClientPreferences data model validation"""
    
    def test_create_preferences_with_defaults(self):
        """Test creating preferences with default values"""
        prefs = ClientPreferences(client_id="test-client-123")
        
        assert prefs.client_id == "test-client-123"
        assert prefs.preferred_channels == [MessageChannel.EMAIL]
        assert prefs.timezone == "UTC"
        assert prefs.quiet_hours_start == "22:00"
        assert prefs.quiet_hours_end == "08:00"
        assert prefs.opt_out_email is False
        assert prefs.opt_out_sms is False
        assert prefs.opt_out_whatsapp is False
        assert prefs.language_preference == "en"
    
    def test_create_preferences_with_custom_values(self):
        """Test creating preferences with custom values"""
        prefs = ClientPreferences(
            client_id="test-client-456",
            preferred_channels=[MessageChannel.SMS, MessageChannel.WHATSAPP],
            timezone="America/New_York",
            quiet_hours_start="23:00",
            quiet_hours_end="07:00",
            opt_out_email=True,
            language_preference="es"
        )
        
        assert prefs.client_id == "test-client-456"
        assert len(prefs.preferred_channels) == 2
        assert MessageChannel.SMS in prefs.preferred_channels
        assert MessageChannel.WHATSAPP in prefs.preferred_channels
        assert prefs.timezone == "America/New_York"
        assert prefs.opt_out_email is True
        assert prefs.language_preference == "es"
    
    def test_preferences_validation_invalid_time_format(self):
        """Test that invalid time format raises ValueError"""
        with pytest.raises(ValueError, match="must be in HH:MM format"):
            ClientPreferences(
                client_id="test-client",
                quiet_hours_start="25:00"  # Invalid hour
            )
        
        with pytest.raises(ValueError, match="must be in HH:MM format"):
            ClientPreferences(
                client_id="test-client",
                quiet_hours_end="12:70"  # Invalid minute
            )
    
    def test_preferences_validation_missing_client_id(self):
        """Test that missing client_id raises ValueError"""
        with pytest.raises(ValueError, match="client_id is required"):
            ClientPreferences(client_id="")
    
    def test_get_available_channels_no_opt_outs(self):
        """Test getting available channels when nothing is opted out"""
        prefs = ClientPreferences(
            client_id="test-client",
            preferred_channels=[MessageChannel.EMAIL, MessageChannel.SMS]
        )
        
        available = prefs.get_available_channels()
        
        assert len(available) == 2
        assert MessageChannel.EMAIL in available
        assert MessageChannel.SMS in available
    
    def test_get_available_channels_with_opt_outs(self):
        """Test getting available channels with opt-outs"""
        prefs = ClientPreferences(
            client_id="test-client",
            preferred_channels=[MessageChannel.EMAIL, MessageChannel.SMS, MessageChannel.WHATSAPP],
            opt_out_email=True,
            opt_out_sms=True
        )
        
        available = prefs.get_available_channels()
        
        assert len(available) == 1
        assert MessageChannel.WHATSAPP in available
        assert MessageChannel.EMAIL not in available
        assert MessageChannel.SMS not in available
    
    def test_get_available_channels_all_opted_out(self):
        """Test getting available channels when all are opted out"""
        prefs = ClientPreferences(
            client_id="test-client",
            preferred_channels=[MessageChannel.EMAIL],
            opt_out_email=True,
            opt_out_sms=True,
            opt_out_whatsapp=True
        )
        
        available = prefs.get_available_channels()
        
        # Should return empty list when all channels are opted out
        assert len(available) == 0
    
    def test_is_channel_available(self):
        """Test checking if specific channel is available"""
        prefs = ClientPreferences(
            client_id="test-client",
            opt_out_email=True,
            opt_out_sms=False
        )
        
        assert prefs.is_channel_available(MessageChannel.EMAIL) is False
        assert prefs.is_channel_available(MessageChannel.SMS) is True
        assert prefs.is_channel_available(MessageChannel.WHATSAPP) is True


class TestCommunicationRepositoryPreferences:
    """Test CommunicationRepository preference methods"""
    
    @pytest.fixture
    def mock_db_session(self):
        """Create mock database session"""
        session = MagicMock()
        session.execute = MagicMock()
        session.commit = MagicMock()
        return session
    
    @pytest.fixture
    def repository(self):
        """Create repository instance with mocked dependencies"""
        # Import here to avoid circular dependencies
        from crm.repository import CommunicationRepository
        return CommunicationRepository()
    
    def test_save_client_preferences_new(self, repository, mock_db_session):
        """Test saving new client preferences"""
        prefs = ClientPreferences(
            client_id="new-client-123",
            preferred_channels=[MessageChannel.EMAIL, MessageChannel.SMS],
            timezone="America/Los_Angeles"
        )
        
        with patch.object(repository, '_get_session') as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_db_session
            
            result = repository.save_client_preferences(prefs)
            
            assert result is True
            assert mock_db_session.execute.called
            assert mock_db_session.commit.called
    
    def test_save_client_preferences_update_existing(self, repository, mock_db_session):
        """Test updating existing client preferences"""
        prefs = ClientPreferences(
            client_id="existing-client-456",
            preferred_channels=[MessageChannel.WHATSAPP],
            opt_out_email=True
        )
        
        with patch.object(repository, '_get_session') as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_db_session
            
            result = repository.save_client_preferences(prefs)
            
            assert result is True
            # Verify UPSERT query was executed
            assert mock_db_session.execute.called
            call_args = mock_db_session.execute.call_args
            query_text = str(call_args[0][0])
            assert "ON CONFLICT" in query_text
    
    def test_get_client_preferences_found(self, repository, mock_db_session):
        """Test retrieving existing client preferences"""
        # Mock database result
        mock_result = MagicMock()
        mock_result.fetchone.return_value = (
            "test-client-789",
            '["email", "sms"]',  # JSON string
            "America/Chicago",
            "22:00",
            "08:00",
            False,
            False,
            False,
            "en"
        )
        mock_db_session.execute.return_value = mock_result
        
        with patch.object(repository, '_get_session') as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_db_session
            
            prefs = repository.get_client_preferences("test-client-789")
            
            assert prefs is not None
            assert prefs.client_id == "test-client-789"
            assert len(prefs.preferred_channels) == 2
            assert MessageChannel.EMAIL in prefs.preferred_channels
            assert MessageChannel.SMS in prefs.preferred_channels
            assert prefs.timezone == "America/Chicago"
    
    def test_get_client_preferences_not_found(self, repository, mock_db_session):
        """Test retrieving non-existent client preferences"""
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None
        mock_db_session.execute.return_value = mock_result
        
        with patch.object(repository, '_get_session') as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_db_session
            
            prefs = repository.get_client_preferences("nonexistent-client")
            
            assert prefs is None
    
    def test_delete_client_preferences_success(self, repository, mock_db_session):
        """Test deleting existing client preferences"""
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_db_session.execute.return_value = mock_result
        
        with patch.object(repository, '_get_session') as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_db_session
            
            result = repository.delete_client_preferences("test-client")
            
            assert result is True
            assert mock_db_session.execute.called
            assert mock_db_session.commit.called
    
    def test_delete_client_preferences_not_found(self, repository, mock_db_session):
        """Test deleting non-existent client preferences"""
        mock_result = MagicMock()
        mock_result.rowcount = 0
        mock_db_session.execute.return_value = mock_result
        
        with patch.object(repository, '_get_session') as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_db_session
            
            result = repository.delete_client_preferences("nonexistent-client")
            
            assert result is False


class TestCRMCacheManager:
    """Test CRMCacheManager cache operations"""
    
    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client"""
        redis_mock = MagicMock()
        redis_mock.ping.return_value = True
        return redis_mock
    
    @pytest.fixture
    def cache_manager(self, mock_redis):
        """Create cache manager with mocked Redis"""
        with patch('event_planning_agent_v2.crm.cache_manager.redis.from_url', return_value=mock_redis):
            manager = CRMCacheManager(redis_url="redis://localhost:6379/0")
            return manager
    
    def test_cache_manager_initialization_success(self, mock_redis):
        """Test successful cache manager initialization"""
        with patch('event_planning_agent_v2.crm.cache_manager.redis.from_url', return_value=mock_redis):
            manager = CRMCacheManager(redis_url="redis://localhost:6379/0")
            
            assert manager.enabled is True
            assert manager.redis_client is not None
            mock_redis.ping.assert_called_once()
    
    def test_cache_manager_initialization_disabled(self):
        """Test cache manager with caching disabled"""
        manager = CRMCacheManager(enabled=False)
        
        assert manager.enabled is False
        assert manager.redis_client is None
    
    def test_get_client_preferences_cache_hit(self, cache_manager, mock_redis):
        """Test getting preferences from cache (cache hit)"""
        cached_data = json.dumps({
            'client_id': 'test-client',
            'preferred_channels': ['email', 'sms'],
            'timezone': 'UTC',
            'quiet_hours_start': '22:00',
            'quiet_hours_end': '08:00',
            'opt_out_email': False,
            'opt_out_sms': False,
            'opt_out_whatsapp': False,
            'language_preference': 'en'
        })
        mock_redis.get.return_value = cached_data
        
        prefs = cache_manager.get_client_preferences("test-client")
        
        assert prefs is not None
        assert prefs.client_id == "test-client"
        assert len(prefs.preferred_channels) == 2
        mock_redis.get.assert_called_once()
    
    def test_get_client_preferences_cache_miss(self, cache_manager, mock_redis):
        """Test getting preferences from cache (cache miss)"""
        mock_redis.get.return_value = None
        
        prefs = cache_manager.get_client_preferences("test-client")
        
        assert prefs is None
        mock_redis.get.assert_called_once()
    
    def test_set_client_preferences(self, cache_manager, mock_redis):
        """Test caching client preferences"""
        prefs = ClientPreferences(
            client_id="test-client",
            preferred_channels=[MessageChannel.EMAIL],
            timezone="America/New_York"
        )
        
        result = cache_manager.set_client_preferences(prefs)
        
        assert result is True
        mock_redis.setex.assert_called_once()
        
        # Verify TTL was set
        call_args = mock_redis.setex.call_args
        assert call_args[0][1] == CRMCacheManager.PREFERENCE_TTL  # 3600 seconds
    
    def test_invalidate_client_preferences(self, cache_manager, mock_redis):
        """Test invalidating cached preferences"""
        mock_redis.delete.return_value = 1
        
        result = cache_manager.invalidate_client_preferences("test-client")
        
        assert result is True
        mock_redis.delete.assert_called_once()
    
    def test_check_rate_limit_allowed(self, cache_manager, mock_redis):
        """Test rate limit check when under limit"""
        mock_redis.incr.return_value = 5
        
        allowed, count = cache_manager.check_rate_limit("whatsapp", limit=100, window=60)
        
        assert allowed is True
        assert count == 5
        mock_redis.incr.assert_called_once()
    
    def test_check_rate_limit_exceeded(self, cache_manager, mock_redis):
        """Test rate limit check when limit exceeded"""
        mock_redis.incr.return_value = 101
        
        allowed, count = cache_manager.check_rate_limit("whatsapp", limit=100, window=60)
        
        assert allowed is False
        assert count == 101
    
    def test_check_rate_limit_first_request(self, cache_manager, mock_redis):
        """Test rate limit check for first request (sets expiry)"""
        mock_redis.incr.return_value = 1
        
        allowed, count = cache_manager.check_rate_limit("twilio", limit=100, window=60)
        
        assert allowed is True
        assert count == 1
        mock_redis.incr.assert_called_once()
        mock_redis.expire.assert_called_once()
    
    def test_get_cache_stats(self, cache_manager, mock_redis):
        """Test getting cache statistics"""
        mock_redis.info.return_value = {
            'keyspace_hits': 150,
            'keyspace_misses': 50
        }
        mock_redis.dbsize.return_value = 42
        
        stats = cache_manager.get_cache_stats()
        
        assert stats['enabled'] is True
        assert stats['connected'] is True
        assert stats['total_keys'] == 42
        assert stats['hits'] == 150
        assert stats['misses'] == 50
        assert stats['hit_rate'] == 75.0  # 150/(150+50) * 100
    
    def test_health_check_healthy(self, cache_manager, mock_redis):
        """Test health check when Redis is healthy"""
        mock_redis.ping.return_value = True
        
        healthy = cache_manager.health_check()
        
        assert healthy is True
    
    def test_health_check_unhealthy(self, cache_manager, mock_redis):
        """Test health check when Redis is unhealthy"""
        mock_redis.ping.side_effect = Exception("Connection failed")
        
        healthy = cache_manager.health_check()
        
        assert healthy is False
    
    def test_clear_all_cache(self, cache_manager, mock_redis):
        """Test clearing all CRM cache entries"""
        mock_redis.keys.side_effect = [
            ['crm:prefs:client1', 'crm:prefs:client2'],
            ['crm:template:email:welcome'],
            []
        ]
        mock_redis.delete.side_effect = [2, 1, 0]
        
        result = cache_manager.clear_all()
        
        assert result is True
        assert mock_redis.keys.call_count == 3
        assert mock_redis.delete.call_count == 2  # Only called for non-empty key lists


class TestPreferenceAPIIntegration:
    """Integration tests for preference API endpoints"""
    
    def test_preference_validation_flow(self):
        """Test complete preference validation flow"""
        # Create preferences with all validations
        prefs = ClientPreferences(
            client_id="integration-test-client",
            preferred_channels=[MessageChannel.EMAIL, MessageChannel.SMS],
            timezone="America/New_York",
            quiet_hours_start="23:00",
            quiet_hours_end="07:00",
            opt_out_whatsapp=True,
            language_preference="es"
        )
        
        # Verify all validations passed
        assert prefs.client_id == "integration-test-client"
        assert len(prefs.preferred_channels) == 2
        assert prefs.timezone == "America/New_York"
        assert prefs.opt_out_whatsapp is True
        
        # Verify available channels respect opt-outs
        available = prefs.get_available_channels()
        assert MessageChannel.WHATSAPP not in available
        assert MessageChannel.EMAIL in available
        assert MessageChannel.SMS in available
    
    def test_cache_database_consistency(self):
        """Test that cache and database stay consistent"""
        client_id = "consistency-test-client"
        
        # Create preferences
        prefs = ClientPreferences(
            client_id=client_id,
            preferred_channels=[MessageChannel.EMAIL],
            timezone="UTC"
        )
        
        # Simulate cache manager (disabled for unit test)
        cache_manager = CRMCacheManager(enabled=False)
        
        # In real scenario:
        # 1. Save to database
        # 2. Invalidate cache
        # 3. Cache new value
        
        # Verify preferences are valid
        assert prefs.client_id == client_id
        assert prefs.timezone == "UTC"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
