"""
Unit tests for API client functionality
"""
import pytest
import requests_mock
import json
from unittest.mock import patch, MagicMock
from components.api_client import APIClient, APIError

class TestAPIClient:
    """Test cases for APIClient class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.api_client = APIClient()
        self.base_url = "http://localhost:8000"
    
    def test_init(self):
        """Test APIClient initialization"""
        assert self.api_client.base_url is not None
        assert self.api_client.timeout > 0
        assert self.api_client.retry_attempts > 0
    
    @requests_mock.Mocker()
    def test_health_check_success(self, m):
        """Test successful health check"""
        m.get(f"{self.base_url}/health", json={"status": "healthy"})
        
        result = self.api_client.health_check()
        assert result["status"] == "healthy"
    
    @requests_mock.Mocker()
    def test_health_check_failure(self, m):
        """Test health check failure"""
        m.get(f"{self.base_url}/health", status_code=500)
        
        result = self.api_client.health_check()
        assert result["status"] == "unhealthy"
    
    @requests_mock.Mocker()
    def test_create_plan_success(self, m):
        """Test successful plan creation"""
        plan_data = {
            "client_name": "Test Client",
            "event_type": "wedding",
            "budget": 50000
        }
        response_data = {"plan_id": "test-123", "status": "created"}
        
        m.post(f"{self.base_url}/v1/plans", json=response_data)
        
        result = self.api_client.create_plan(plan_data)
        assert result["plan_id"] == "test-123"
        assert result["status"] == "created"
    
    @requests_mock.Mocker()
    def test_create_plan_validation_error(self, m):
        """Test plan creation with validation error"""
        plan_data = {"invalid": "data"}
        m.post(f"{self.base_url}/v1/plans", status_code=422, 
               json={"detail": "Validation error"})
        
        with pytest.raises(APIError) as exc_info:
            self.api_client.create_plan(plan_data)
        
        assert exc_info.value.status_code == 422
    
    @requests_mock.Mocker()
    def test_get_plan_status(self, m):
        """Test getting plan status"""
        plan_id = "test-123"
        status_data = {"status": "in_progress", "progress": 50}
        
        m.get(f"{self.base_url}/v1/plans/{plan_id}/status", json=status_data)
        
        result = self.api_client.get_plan_status(plan_id)
        assert result["status"] == "in_progress"
        assert result["progress"] == 50
    
    @requests_mock.Mocker()
    def test_get_plan_results(self, m):
        """Test getting plan results"""
        plan_id = "test-123"
        results_data = {
            "combinations": [
                {"id": "combo-1", "fitness_score": 85, "total_cost": 45000},
                {"id": "combo-2", "fitness_score": 78, "total_cost": 42000}
            ]
        }
        
        m.get(f"{self.base_url}/v1/plans/{plan_id}/results", json=results_data)
        
        result = self.api_client.get_plan_results(plan_id)
        assert len(result["combinations"]) == 2
        assert result["combinations"][0]["fitness_score"] == 85
    
    @requests_mock.Mocker()
    def test_select_combination(self, m):
        """Test selecting a combination"""
        plan_id = "test-123"
        combination_id = "combo-1"
        response_data = {"status": "selected", "blueprint_id": "blueprint-456"}
        
        m.post(f"{self.base_url}/v1/plans/{plan_id}/select", json=response_data)
        
        result = self.api_client.select_combination(plan_id, combination_id)
        assert result["status"] == "selected"
        assert result["blueprint_id"] == "blueprint-456"
    
    @requests_mock.Mocker()
    def test_get_blueprint(self, m):
        """Test getting blueprint"""
        plan_id = "test-123"
        blueprint_data = {
            "timeline": [],
            "vendors": {},
            "total_cost": 45000
        }
        
        m.get(f"{self.base_url}/v1/plans/{plan_id}/blueprint", json=blueprint_data)
        
        result = self.api_client.get_blueprint(plan_id)
        assert "timeline" in result
        assert "vendors" in result
        assert result["total_cost"] == 45000
    
    @requests_mock.Mocker()
    def test_list_plans(self, m):
        """Test listing plans"""
        plans_data = {
            "plans": [
                {"id": "plan-1", "client_name": "Client 1", "status": "completed"},
                {"id": "plan-2", "client_name": "Client 2", "status": "in_progress"}
            ],
            "total": 2
        }
        
        m.get(f"{self.base_url}/v1/plans", json=plans_data)
        
        result = self.api_client.list_plans()
        assert len(result["plans"]) == 2
        assert result["total"] == 2
    
    @requests_mock.Mocker()
    def test_connection_error_retry(self, m):
        """Test connection error retry logic"""
        m.get(f"{self.base_url}/health", exc=requests.exceptions.ConnectionError)
        
        with pytest.raises(APIError) as exc_info:
            self.api_client.health_check()
        
        assert "Cannot connect to API server" in str(exc_info.value)
    
    @requests_mock.Mocker()
    def test_timeout_retry(self, m):
        """Test timeout retry logic"""
        m.get(f"{self.base_url}/health", exc=requests.exceptions.Timeout)
        
        with pytest.raises(APIError) as exc_info:
            self.api_client.health_check()
        
        assert "Request timeout" in str(exc_info.value)
    
    @requests_mock.Mocker()
    def test_server_error_retry(self, m):
        """Test server error retry logic"""
        # First two attempts return 500, third succeeds
        m.get(f"{self.base_url}/health", [
            {"status_code": 500},
            {"status_code": 500},
            {"json": {"status": "healthy"}}
        ])
        
        result = self.api_client.health_check()
        assert result["status"] == "healthy"
    
    def test_cache_key_generation(self):
        """Test cache key generation"""
        key1 = self.api_client._get_cache_key("GET", "/test", params={"a": 1})
        key2 = self.api_client._get_cache_key("GET", "/test", params={"a": 1})
        key3 = self.api_client._get_cache_key("GET", "/test", params={"a": 2})
        
        assert key1 == key2  # Same parameters should generate same key
        assert key1 != key3  # Different parameters should generate different key
    
    def test_is_cacheable(self):
        """Test caching logic"""
        assert self.api_client._is_cacheable("GET", "/health") == True
        assert self.api_client._is_cacheable("GET", "/v1/plans") == True
        assert self.api_client._is_cacheable("GET", "/v1/plans/123/status") == True
        assert self.api_client._is_cacheable("POST", "/v1/plans") == False
        assert self.api_client._is_cacheable("GET", "/unknown") == False

class TestAPIError:
    """Test cases for APIError exception"""
    
    def test_api_error_creation(self):
        """Test APIError creation"""
        error = APIError("Test error", 400, {"detail": "Bad request"})
        
        assert str(error) == "Test error"
        assert error.status_code == 400
        assert error.response_data["detail"] == "Bad request"
    
    def test_api_error_without_optional_params(self):
        """Test APIError creation without optional parameters"""
        error = APIError("Simple error")
        
        assert str(error) == "Simple error"
        assert error.status_code is None
        assert error.response_data is None

if __name__ == "__main__":
    pytest.main([__file__])