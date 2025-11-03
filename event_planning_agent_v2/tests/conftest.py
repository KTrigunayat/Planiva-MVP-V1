"""
Pytest configuration and fixtures for Event Planning Agent v2 tests

Provides common fixtures and configuration for API, system health,
and load testing suites.
"""

import pytest
import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch
from typing import Generator, Dict, Any

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Test environment setup
os.environ["TESTING"] = "true"
os.environ["LOG_LEVEL"] = "INFO"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_settings():
    """Test configuration settings"""
    return {
        "database_url": "sqlite:///test_event_planning.db",
        "ollama_base_url": "http://localhost:11434",
        "api_host": "127.0.0.1",
        "api_port": 8000,
        "log_level": "INFO",
        "testing": True
    }


@pytest.fixture
def mock_database():
    """Mock database connections for testing"""
    with patch('event_planning_agent_v2.database.setup.DatabaseSetup') as mock_db:
        mock_instance = Mock()
        mock_instance.get_session.return_value.__enter__ = Mock()
        mock_instance.get_session.return_value.__exit__ = Mock()
        mock_db.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_state_manager():
    """Mock state manager for testing"""
    with patch('event_planning_agent_v2.database.state_manager.get_state_manager') as mock_sm:
        mock_instance = Mock()
        mock_instance.save_plan.return_value = None
        mock_instance.load_plan.return_value = None
        mock_instance.list_plans.return_value = ([], 0)
        mock_instance.health_check.return_value = True
        mock_sm.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_crew_integration():
    """Mock CrewAI integration for testing"""
    with patch('event_planning_agent_v2.api.crew_integration.execute_event_planning') as mock_execute:
        mock_result = Mock()
        mock_result.success = True
        mock_result.plan_id = "test_plan_123"
        mock_result.final_state = {"beam_candidates": []}
        mock_result.nodes_executed = []
        mock_result.error = None
        mock_execute.return_value = mock_result
        yield mock_execute


@pytest.fixture
def mock_health_checker():
    """Mock health checker for testing"""
    with patch('event_planning_agent_v2.observability.health.get_health_checker') as mock_hc:
        mock_instance = Mock()
        mock_instance.run_health_check.return_value = Mock(
            component_name="test_component",
            status="healthy",
            message="Test component is healthy",
            response_time_ms=50.0
        )
        mock_instance.get_system_health.return_value = Mock(
            overall_status="healthy",
            components={},
            timestamp="2024-01-01T00:00:00Z"
        )
        mock_hc.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def sample_event_request() -> Dict[str, Any]:
    """Sample event planning request for testing"""
    return {
        "clientName": "Test Client",
        "guestCount": {"Reception": 150, "Ceremony": 100, "total": 150},
        "clientVision": "Elegant outdoor wedding with modern touches",
        "venuePreferences": ["outdoor", "garden", "resort"],
        "essentialVenueAmenities": ["parking", "catering_kitchen", "sound_system"],
        "decorationAndAmbiance": {
            "desired_theme": "modern_elegant",
            "color_scheme": ["white", "gold", "blush"],
            "style_preferences": ["minimalist", "romantic"]
        },
        "foodAndCatering": {
            "cuisine_preferences": ["indian", "continental"],
            "dietary_options": ["vegetarian", "vegan"],
            "service_style": "buffet"
        },
        "additionalRequirements": {
            "photography": "professional",
            "makeup": "bridal_package"
        },
        "budget": 500000.0,
        "eventDate": "2024-12-15",
        "location": "Mumbai"
    }


@pytest.fixture
def sample_vendor_combination() -> Dict[str, Any]:
    """Sample vendor combination for testing"""
    return {
        "combination_id": "combo_test_123",
        "venue": {
            "vendor_id": "venue_001",
            "name": "Test Garden Resort",
            "service_type": "venue",
            "location_city": "Mumbai",
            "ranking_score": 8.5,
            "price_info": {"base_price": 150000},
            "capacity": 200
        },
        "caterer": {
            "vendor_id": "caterer_001",
            "name": "Test Royal Caterers",
            "service_type": "catering",
            "ranking_score": 8.2,
            "price_info": {"per_person": 800}
        },
        "photographer": {
            "vendor_id": "photo_001",
            "name": "Test Photography Studio",
            "service_type": "photography",
            "ranking_score": 8.8,
            "price_info": {"package_price": 50000}
        },
        "makeup_artist": {
            "vendor_id": "makeup_001",
            "name": "Test Glamour Studio",
            "service_type": "makeup",
            "ranking_score": 8.0,
            "price_info": {"bridal_package": 25000}
        },
        "total_score": 8.4,
        "estimated_cost": 345000.0,
        "feasibility_score": 9.2
    }


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment before each test"""
    # Set test environment variables
    os.environ["TESTING"] = "true"
    os.environ["LOG_LEVEL"] = "WARNING"  # Reduce log noise in tests
    
    yield
    
    # Cleanup after test
    # Remove any test-specific environment variables if needed
    pass


@pytest.fixture
def disable_external_calls():
    """Disable external API calls during testing"""
    with patch('httpx.AsyncClient') as mock_client:
        with patch('httpx.Client') as mock_sync_client:
            # Mock successful responses
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "ok"}
            
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            mock_sync_client.return_value.get.return_value = mock_response
            mock_sync_client.return_value.post.return_value = mock_response
            
            yield


# Pytest markers for test categorization
def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line("markers", "api: API endpoint tests")
    config.addinivalue_line("markers", "health: System health monitoring tests")
    config.addinivalue_line("markers", "load: Load and performance tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "slow: Slow running tests (>30s)")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically"""
    for item in items:
        # Add markers based on test file names
        if "test_api_endpoints" in str(item.fspath):
            item.add_marker(pytest.mark.api)
        elif "test_system_health" in str(item.fspath):
            item.add_marker(pytest.mark.health)
        elif "test_load_testing" in str(item.fspath):
            item.add_marker(pytest.mark.load)
            item.add_marker(pytest.mark.slow)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)


# Test session hooks
def pytest_sessionstart(session):
    """Called after the Session object has been created"""
    print("\n🧪 Starting Event Planning Agent v2 test session")


def pytest_sessionfinish(session, exitstatus):
    """Called after whole test run finished"""
    if exitstatus == 0:
        print("\n✅ All tests completed successfully!")
    else:
        print(f"\n❌ Tests completed with exit status: {exitstatus}")


# Test reporting hooks
def pytest_runtest_logreport(report):
    """Called for each test report"""
    if report.when == "call":
        if report.outcome == "passed":
            print(f"✅ {report.nodeid}")
        elif report.outcome == "failed":
            print(f"❌ {report.nodeid}")
        elif report.outcome == "skipped":
            print(f"⏭️ {report.nodeid}")