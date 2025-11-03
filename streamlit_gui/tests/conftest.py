"""
Pytest configuration and fixtures for Streamlit GUI tests
"""
import pytest
import os
import sys
from unittest.mock import MagicMock, patch

# Add the parent directory to the path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture
def mock_streamlit():
    """Mock Streamlit for testing"""
    with patch('streamlit.session_state', {}) as mock_state:
        with patch('streamlit.empty') as mock_empty:
            with patch('streamlit.spinner') as mock_spinner:
                with patch('streamlit.cache_data') as mock_cache:
                    mock_cache.side_effect = lambda *args, **kwargs: lambda func: func
                    yield {
                        'session_state': mock_state,
                        'empty': mock_empty,
                        'spinner': mock_spinner,
                        'cache_data': mock_cache
                    }

@pytest.fixture
def mock_config():
    """Mock configuration for testing"""
    config_mock = MagicMock()
    config_mock.API_BASE_URL = "http://localhost:8000"
    config_mock.API_TIMEOUT = 30
    config_mock.API_RETRY_ATTEMPTS = 3
    config_mock.API_RETRY_DELAY = 1
    config_mock.get_api_url = lambda endpoint: f"http://localhost:8000{endpoint}"
    config_mock.get = lambda key, default=None: {
        'CACHE_TTL': 300,
        'enable_caching': True
    }.get(key, default)
    
    with patch('utils.config.config', config_mock):
        yield config_mock

@pytest.fixture
def sample_plan_data():
    """Sample plan data for testing"""
    return {
        "client_name": "John Doe",
        "client_email": "john@example.com",
        "client_phone": "+1-555-123-4567",
        "event_type": "wedding",
        "event_date": "2024-06-15",
        "location": "New York, NY",
        "guest_count": 100,
        "ceremony_guests": 80,
        "reception_guests": 100,
        "budget": 50000,
        "venue_preferences": ["outdoor", "garden"],
        "catering_preferences": ["italian", "vegetarian_options"],
        "photography_requirements": "full_day_coverage",
        "client_vision": "Elegant outdoor wedding with Italian cuisine"
    }

@pytest.fixture
def sample_combinations():
    """Sample vendor combinations for testing"""
    return [
        {
            "id": "combo-1",
            "fitness_score": 85.5,
            "total_cost": 45000,
            "venue": {
                "id": "venue-1",
                "name": "Garden Paradise",
                "type": "outdoor",
                "cost": 15000,
                "location": "Central Park, NY",
                "amenities": ["garden", "parking", "catering_kitchen"]
            },
            "caterer": {
                "id": "caterer-1", 
                "name": "Italian Delights",
                "cuisine": "italian",
                "cost": 18000,
                "dietary_options": ["vegetarian", "gluten_free"]
            },
            "photographer": {
                "id": "photographer-1",
                "name": "Perfect Moments",
                "style": "romantic",
                "cost": 8000,
                "packages": ["full_day", "engagement_session"]
            },
            "makeup_artist": {
                "id": "makeup-1",
                "name": "Beauty Studio",
                "style": "natural",
                "cost": 4000,
                "services": ["bridal", "bridesmaids"]
            }
        },
        {
            "id": "combo-2",
            "fitness_score": 78.2,
            "total_cost": 42000,
            "venue": {
                "id": "venue-2",
                "name": "Elegant Hall",
                "type": "indoor",
                "cost": 12000,
                "location": "Manhattan, NY",
                "amenities": ["ballroom", "parking", "sound_system"]
            },
            "caterer": {
                "id": "caterer-2",
                "name": "Gourmet Catering",
                "cuisine": "american",
                "cost": 16000,
                "dietary_options": ["vegetarian", "vegan"]
            },
            "photographer": {
                "id": "photographer-2",
                "name": "Classic Photos",
                "style": "traditional",
                "cost": 9000,
                "packages": ["full_day", "album_included"]
            },
            "makeup_artist": {
                "id": "makeup-2",
                "name": "Glamour Artists",
                "style": "glamorous",
                "cost": 5000,
                "services": ["bridal", "trial_session"]
            }
        }
    ]

@pytest.fixture
def sample_blueprint():
    """Sample blueprint data for testing"""
    return {
        "plan_id": "plan-123",
        "client_name": "John Doe",
        "event_date": "2024-06-15",
        "total_cost": 45000,
        "timeline": [
            {
                "time": "09:00",
                "activity": "Venue setup begins",
                "responsible": "venue_coordinator"
            },
            {
                "time": "14:00", 
                "activity": "Ceremony starts",
                "responsible": "officiant"
            },
            {
                "time": "18:00",
                "activity": "Reception begins",
                "responsible": "caterer"
            }
        ],
        "vendors": {
            "venue": {
                "name": "Garden Paradise",
                "contact": "venue@example.com",
                "phone": "+1-555-VENUE"
            },
            "caterer": {
                "name": "Italian Delights", 
                "contact": "catering@example.com",
                "phone": "+1-555-CATER"
            },
            "photographer": {
                "name": "Perfect Moments",
                "contact": "photo@example.com", 
                "phone": "+1-555-PHOTO"
            },
            "makeup_artist": {
                "name": "Beauty Studio",
                "contact": "makeup@example.com",
                "phone": "+1-555-MAKEUP"
            }
        },
        "logistics": {
            "setup_time": "09:00",
            "ceremony_time": "14:00",
            "reception_time": "18:00",
            "cleanup_time": "23:00"
        },
        "next_steps": [
            "Contact venue coordinator to confirm setup time",
            "Schedule tasting with caterer",
            "Book engagement session with photographer",
            "Schedule makeup trial"
        ]
    }

@pytest.fixture
def mock_api_responses():
    """Mock API responses for testing"""
    return {
        "health": {"status": "healthy"},
        "create_plan": {"plan_id": "plan-123", "status": "created"},
        "plan_status": {"status": "in_progress", "progress": 50},
        "plan_results": {"combinations": []},
        "select_combination": {"status": "selected", "blueprint_id": "blueprint-456"},
        "blueprint": {"timeline": [], "vendors": {}, "total_cost": 45000},
        "list_plans": {"plans": [], "total": 0}
    }

@pytest.fixture(autouse=True)
def reset_caches():
    """Reset Streamlit caches between tests"""
    # Clear any cached functions
    yield
    # Cleanup after test
    pass

class MockStreamlitComponent:
    """Mock Streamlit component for testing"""
    
    def __init__(self):
        self.calls = []
    
    def __call__(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return MagicMock()
    
    def reset(self):
        self.calls = []