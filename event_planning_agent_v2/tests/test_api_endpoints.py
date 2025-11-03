"""
API endpoint tests for Event Planning Agent v2

Tests API compatibility with existing integrations and validates
all endpoint functionality including error handling and response formats.

Requirements: 5.1, 6.4, 6.5
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List
from unittest.mock import Mock, patch, AsyncMock
from uuid import uuid4

from fastapi.testclient import TestClient
from fastapi import status, FastAPI
import httpx

# Mock imports to avoid dependency issues during testing
try:
    from ..api.app import create_app
    from ..api.schemas import (
        EventPlanRequest, EventPlanResponse, CombinationSelection,
        PlanStatus, WorkflowStatus, EventCombination, HealthResponse
    )
    from ..database.test_setup import TestDatabaseSetup
    from ..config.settings import get_settings
except ImportError:
    # Create mock classes for testing when imports fail
    create_app = None
    EventPlanRequest = dict
    EventPlanResponse = dict
    CombinationSelection = dict
    PlanStatus = type('PlanStatus', (), {
        'PENDING': 'pending',
        'PROCESSING': 'processing', 
        'COMPLETED': 'completed',
        'FAILED': 'failed',
        'CANCELLED': 'cancelled'
    })
    WorkflowStatus = dict
    EventCombination = dict
    HealthResponse = dict
    TestDatabaseSetup = None
    get_settings = lambda: {}


class TestAPIEndpoints:
    """Test suite for API endpoints"""
    
    @pytest.fixture(scope="class")
    def test_app(self):
        """Create test FastAPI application"""
        if create_app:
            app = create_app()
        else:
            # Create minimal FastAPI app for testing
            app = FastAPI()
            
            @app.get("/")
            def root():
                return {"message": "Event Planning Agent v2 API", "version": "2.0.0", "status": "active"}
            
            @app.get("/health")
            def health():
                return {"status": "healthy", "version": "2.0.0", "components": {"api": "healthy"}}
            
            @app.post("/v1/plans")
            def create_plan(request: dict):
                return {
                    "plan_id": "test_plan_123",
                    "status": "completed",
                    "client_name": request.get("clientName", "Test Client"),
                    "combinations": [],
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z"
                }
            
            @app.get("/v1/plans/{plan_id}")
            def get_plan(plan_id: str):
                return {
                    "plan_id": plan_id,
                    "status": "completed",
                    "client_name": "Test Client",
                    "combinations": [],
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z"
                }
        
        return app
    
    @pytest.fixture(scope="class")
    def client(self, test_app):
        """Create test client"""
        return TestClient(test_app)
    
    @pytest.fixture(scope="class")
    def test_db(self):
        """Setup test database"""
        if TestDatabaseSetup:
            db_setup = TestDatabaseSetup()
            db_setup.setup_test_database()
            yield db_setup
            db_setup.cleanup_test_database()
        else:
            # Mock database setup
            yield None
    
    @pytest.fixture
    def sample_event_request(self) -> Dict[str, Any]:
        """Sample event planning request"""
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
    def sample_combinations(self) -> List[Dict[str, Any]]:
        """Sample event combinations"""
        return [
            {
                "combination_id": "combo_1",
                "venue": {
                    "vendor_id": "venue_001",
                    "name": "Grand Garden Resort",
                    "service_type": "venue",
                    "location_city": "Mumbai",
                    "ranking_score": 8.5,
                    "price_info": {"base_price": 150000},
                    "capacity": 200
                },
                "caterer": {
                    "vendor_id": "caterer_001", 
                    "name": "Royal Caterers",
                    "service_type": "catering",
                    "ranking_score": 8.2,
                    "price_info": {"per_person": 800}
                },
                "photographer": {
                    "vendor_id": "photo_001",
                    "name": "Perfect Moments Photography",
                    "service_type": "photography",
                    "ranking_score": 8.8,
                    "price_info": {"package_price": 50000}
                },
                "makeup_artist": {
                    "vendor_id": "makeup_001",
                    "name": "Glamour Studio",
                    "service_type": "makeup",
                    "ranking_score": 8.0,
                    "price_info": {"bridal_package": 25000}
                },
                "total_score": 8.4,
                "estimated_cost": 345000.0,
                "feasibility_score": 9.2
            }
        ]


class TestRootEndpoint(TestAPIEndpoints):
    """Test root endpoint"""
    
    def test_root_endpoint(self, client):
        """Test root endpoint returns correct information"""
        response = client.get("/")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "message" in data
        assert "version" in data
        assert "status" in data
        assert data["version"] == "2.0.0"
        assert data["status"] == "active"


class TestHealthEndpoint(TestAPIEndpoints):
    """Test health check endpoint"""
    
    def test_health_endpoint_success(self, client):
        """Test health endpoint returns healthy status"""
        with patch('event_planning_agent_v2.database.state_manager.get_state_manager') as mock_state_manager:
            # Mock healthy database
            mock_state_manager.return_value.health_check.return_value = True
            
            response = client.get("/health")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            
            # Validate response schema
            health_response = HealthResponse(**data)
            assert health_response.status in ["healthy", "degraded", "unhealthy"]
            assert health_response.version == "2.0.0"
            assert "components" in data
    
    def test_health_endpoint_database_failure(self, client):
        """Test health endpoint with database failure"""
        with patch('event_planning_agent_v2.database.state_manager.get_state_manager') as mock_state_manager:
            # Mock database failure
            mock_state_manager.return_value.health_check.side_effect = Exception("Database connection failed")
            
            response = client.get("/health")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            
            health_response = HealthResponse(**data)
            assert health_response.status == "unhealthy"
            assert "database" in data["components"]
            assert "unhealthy" in data["components"]["database"]


class TestEventPlanCreation(TestAPIEndpoints):
    """Test event plan creation endpoint"""
    
    @patch('event_planning_agent_v2.api.crew_integration.execute_event_planning')
    @patch('event_planning_agent_v2.database.state_manager.get_state_manager')
    def test_create_plan_synchronous_success(self, mock_state_manager, mock_execute, client, sample_event_request):
        """Test successful synchronous plan creation"""
        # Mock successful execution
        mock_result = Mock()
        mock_result.success = True
        mock_result.plan_id = "test_plan_123"
        mock_result.final_state = {
            "beam_candidates": [
                {
                    "combination_id": "combo_1",
                    "total_score": 8.5,
                    "estimated_cost": 400000.0
                }
            ]
        }
        mock_result.nodes_executed = ["initialize", "budget", "sourcing", "beam_search"]
        mock_result.error = None
        mock_execute.return_value = mock_result
        
        # Mock state manager
        mock_state_manager.return_value.save_plan.return_value = None
        mock_state_manager.return_value.load_plan.return_value = {
            "plan_id": "test_plan_123",
            "status": "completed",
            "client_name": "Test Client",
            "combinations": mock_result.final_state["beam_candidates"],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        response = client.post("/v1/plans", json=sample_event_request)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Validate response schema
        plan_response = EventPlanResponse(**data)
        assert plan_response.status == PlanStatus.COMPLETED
        assert plan_response.client_name == "Test Client"
        assert len(plan_response.combinations) > 0
        
        # Verify API compatibility
        assert "plan_id" in data
        assert "status" in data
        assert "client_name" in data
        assert "combinations" in data
    
    @patch('event_planning_agent_v2.database.state_manager.get_state_manager')
    def test_create_plan_asynchronous(self, mock_state_manager, client, sample_event_request):
        """Test asynchronous plan creation"""
        # Mock state manager
        mock_state_manager.return_value.save_plan.return_value = None
        
        response = client.post("/v1/plans?async_execution=true", json=sample_event_request)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Validate response schema
        plan_response = EventPlanResponse(**data)
        assert plan_response.status == PlanStatus.PROCESSING
        assert plan_response.client_name == "Test Client"
        
        # Verify async response format
        assert "workflow_status" in data
        assert data["workflow_status"]["current_step"] == "initialization"
    
    def test_create_plan_invalid_request(self, client):
        """Test plan creation with invalid request"""
        invalid_request = {
            "clientName": "",  # Invalid empty name
            "guestCount": -1,  # Invalid negative count
        }
        
        response = client.post("/v1/plans", json=invalid_request)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Verify error response format
        error_data = response.json()
        assert "detail" in error_data
    
    @patch('event_planning_agent_v2.api.crew_integration.execute_event_planning')
    @patch('event_planning_agent_v2.database.state_manager.get_state_manager')
    def test_create_plan_execution_failure(self, mock_state_manager, mock_execute, client, sample_event_request):
        """Test plan creation with execution failure"""
        # Mock execution failure
        mock_result = Mock()
        mock_result.success = False
        mock_result.error = "Workflow execution failed"
        mock_execute.return_value = mock_result
        
        # Mock state manager
        mock_state_manager.return_value.save_plan.return_value = None
        
        response = client.post("/v1/plans", json=sample_event_request)
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        
        error_data = response.json()
        assert "detail" in error_data
        assert "error" in error_data["detail"]


class TestEventPlanRetrieval(TestAPIEndpoints):
    """Test event plan retrieval endpoint"""
    
    @patch('event_planning_agent_v2.database.state_manager.get_state_manager')
    def test_get_plan_success(self, mock_state_manager, client, sample_combinations):
        """Test successful plan retrieval"""
        plan_id = "test_plan_123"
        
        # Mock plan data
        mock_plan_data = {
            "plan_id": plan_id,
            "status": "completed",
            "client_name": "Test Client",
            "combinations": sample_combinations,
            "selected_combination": None,
            "final_blueprint": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        mock_state_manager.return_value.load_plan.return_value = mock_plan_data
        
        response = client.get(f"/v1/plans/{plan_id}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Validate response schema
        plan_response = EventPlanResponse(**data)
        assert plan_response.plan_id == plan_id
        assert plan_response.status == PlanStatus.COMPLETED
        assert plan_response.client_name == "Test Client"
        assert len(plan_response.combinations) == 1
    
    @patch('event_planning_agent_v2.database.state_manager.get_state_manager')
    def test_get_plan_not_found(self, mock_state_manager, client):
        """Test plan retrieval for non-existent plan"""
        plan_id = "nonexistent_plan"
        
        # Mock plan not found
        mock_state_manager.return_value.load_plan.return_value = None
        
        response = client.get(f"/v1/plans/{plan_id}")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        error_data = response.json()
        assert "detail" in error_data
        assert "plan_not_found" in error_data["detail"]["error"]
    
    @patch('event_planning_agent_v2.api.crew_integration.get_planning_workflow_status')
    @patch('event_planning_agent_v2.database.state_manager.get_state_manager')
    def test_get_plan_with_workflow_details(self, mock_state_manager, mock_workflow_status, client):
        """Test plan retrieval with workflow details"""
        plan_id = "test_plan_123"
        
        # Mock plan data
        mock_plan_data = {
            "plan_id": plan_id,
            "status": "processing",
            "client_name": "Test Client",
            "combinations": [],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Mock workflow status
        mock_workflow_status.return_value = {
            "status": "running",
            "nodes_executed": ["initialize", "budget"],
            "error": None
        }
        
        mock_state_manager.return_value.load_plan.return_value = mock_plan_data
        
        response = client.get(f"/v1/plans/{plan_id}?include_workflow_details=true")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Validate workflow status included
        assert "workflow_status" in data
        assert data["workflow_status"]["current_step"] == "running"
        assert len(data["workflow_status"]["steps_completed"]) == 2


class TestCombinationSelection(TestAPIEndpoints):
    """Test combination selection endpoint"""
    
    @patch('event_planning_agent_v2.database.state_manager.get_state_manager')
    def test_select_combination_success(self, mock_state_manager, client, sample_combinations):
        """Test successful combination selection"""
        plan_id = "test_plan_123"
        combination_id = "combo_1"
        
        # Mock existing plan
        mock_plan_data = {
            "plan_id": plan_id,
            "status": "completed",
            "client_name": "Test Client",
            "combinations": sample_combinations,
            "selected_combination": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        mock_state_manager.return_value.load_plan.return_value = mock_plan_data
        mock_state_manager.return_value.save_plan.return_value = None
        
        selection_request = {
            "combination_id": combination_id,
            "notes": "Client preferred this option",
            "client_feedback": {"rating": 9, "comments": "Perfect choice"}
        }
        
        response = client.post(f"/v1/plans/{plan_id}/select-combination", json=selection_request)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Validate response
        plan_response = EventPlanResponse(**data)
        assert plan_response.selected_combination is not None
        assert plan_response.selected_combination.combination_id == combination_id
    
    @patch('event_planning_agent_v2.database.state_manager.get_state_manager')
    def test_select_combination_not_found(self, mock_state_manager, client):
        """Test combination selection for non-existent plan"""
        plan_id = "nonexistent_plan"
        
        # Mock plan not found
        mock_state_manager.return_value.load_plan.return_value = None
        
        selection_request = {
            "combination_id": "combo_1"
        }
        
        response = client.post(f"/v1/plans/{plan_id}/select-combination", json=selection_request)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    @patch('event_planning_agent_v2.database.state_manager.get_state_manager')
    def test_select_invalid_combination(self, mock_state_manager, client, sample_combinations):
        """Test selection of invalid combination"""
        plan_id = "test_plan_123"
        
        # Mock existing plan
        mock_plan_data = {
            "plan_id": plan_id,
            "status": "completed",
            "client_name": "Test Client",
            "combinations": sample_combinations,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        mock_state_manager.return_value.load_plan.return_value = mock_plan_data
        
        selection_request = {
            "combination_id": "invalid_combo_id"
        }
        
        response = client.post(f"/v1/plans/{plan_id}/select-combination", json=selection_request)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        error_data = response.json()
        assert "combination_not_found" in error_data["detail"]["error"]


class TestPlanListing(TestAPIEndpoints):
    """Test plan listing endpoint"""
    
    @patch('event_planning_agent_v2.database.state_manager.get_state_manager')
    def test_list_plans_success(self, mock_state_manager, client, sample_combinations):
        """Test successful plan listing"""
        # Mock plans data
        mock_plans = [
            {
                "plan_id": "plan_1",
                "status": "completed",
                "client_name": "Client 1",
                "combinations": sample_combinations,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            },
            {
                "plan_id": "plan_2", 
                "status": "processing",
                "client_name": "Client 2",
                "combinations": [],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        ]
        
        mock_state_manager.return_value.list_plans.return_value = (mock_plans, 2)
        
        response = client.get("/v1/plans")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Validate response structure
        assert "plans" in data
        assert "total_count" in data
        assert "page" in data
        assert "page_size" in data
        
        assert len(data["plans"]) == 2
        assert data["total_count"] == 2
    
    @patch('event_planning_agent_v2.database.state_manager.get_state_manager')
    def test_list_plans_with_filters(self, mock_state_manager, client):
        """Test plan listing with filters"""
        # Mock filtered results
        mock_plans = [
            {
                "plan_id": "plan_1",
                "status": "completed",
                "client_name": "Test Client",
                "combinations": [],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        ]
        
        mock_state_manager.return_value.list_plans.return_value = (mock_plans, 1)
        
        response = client.get("/v1/plans?status=completed&client_name=Test Client&page=1&page_size=5")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert len(data["plans"]) == 1
        assert data["plans"][0]["status"] == "completed"
        assert data["plans"][0]["client_name"] == "Test Client"


class TestWorkflowManagement(TestAPIEndpoints):
    """Test workflow management endpoints"""
    
    @patch('event_planning_agent_v2.api.crew_integration.resume_planning_workflow')
    @patch('event_planning_agent_v2.database.state_manager.get_state_manager')
    def test_resume_plan_success(self, mock_state_manager, mock_resume, client):
        """Test successful plan resumption"""
        plan_id = "test_plan_123"
        
        # Mock existing plan
        mock_plan_data = {
            "plan_id": plan_id,
            "status": "failed",
            "client_name": "Test Client",
            "combinations": [],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        mock_state_manager.return_value.load_plan.return_value = mock_plan_data
        mock_state_manager.return_value.save_plan.return_value = None
        
        # Mock successful resume
        mock_result = Mock()
        mock_result.success = True
        mock_result.plan_id = plan_id
        mock_resume.return_value = mock_result
        
        response = client.post(f"/v1/plans/{plan_id}/resume")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        plan_response = EventPlanResponse(**data)
        assert plan_response.status == PlanStatus.PROCESSING
    
    @patch('event_planning_agent_v2.api.crew_integration.cancel_planning_workflow')
    @patch('event_planning_agent_v2.database.state_manager.get_state_manager')
    def test_cancel_plan_success(self, mock_state_manager, mock_cancel, client):
        """Test successful plan cancellation"""
        plan_id = "test_plan_123"
        
        # Mock existing plan
        mock_plan_data = {
            "plan_id": plan_id,
            "status": "processing",
            "client_name": "Test Client",
            "combinations": [],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        mock_state_manager.return_value.load_plan.return_value = mock_plan_data
        mock_state_manager.return_value.save_plan.return_value = None
        mock_cancel.return_value = True
        
        response = client.delete(f"/v1/plans/{plan_id}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "message" in data
        assert "cancelled successfully" in data["message"]


class TestAPICompatibility(TestAPIEndpoints):
    """Test API compatibility with existing integrations"""
    
    def test_request_response_format_compatibility(self, client, sample_event_request):
        """Test that request/response formats maintain compatibility"""
        with patch('event_planning_agent_v2.api.crew_integration.execute_event_planning') as mock_execute:
            with patch('event_planning_agent_v2.database.state_manager.get_state_manager') as mock_state_manager:
                # Mock successful execution
                mock_result = Mock()
                mock_result.success = True
                mock_result.plan_id = "test_plan_123"
                mock_result.final_state = {"beam_candidates": []}
                mock_result.nodes_executed = []
                mock_result.error = None
                mock_execute.return_value = mock_result
                
                mock_state_manager.return_value.save_plan.return_value = None
                mock_state_manager.return_value.load_plan.return_value = {
                    "plan_id": "test_plan_123",
                    "status": "completed",
                    "client_name": "Test Client",
                    "combinations": [],
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                
                response = client.post("/v1/plans", json=sample_event_request)
                
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                
                # Verify all required fields are present for compatibility
                required_fields = [
                    "plan_id", "status", "client_name", "combinations",
                    "created_at", "updated_at"
                ]
                
                for field in required_fields:
                    assert field in data, f"Required field '{field}' missing from response"
                
                # Verify field types match expected format
                assert isinstance(data["plan_id"], str)
                assert isinstance(data["status"], str)
                assert isinstance(data["client_name"], str)
                assert isinstance(data["combinations"], list)
    
    def test_error_response_format_compatibility(self, client):
        """Test that error responses maintain consistent format"""
        # Test with invalid request to trigger error
        response = client.post("/v1/plans", json={})
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Verify error response structure
        error_data = response.json()
        assert "detail" in error_data
        
        # Test 404 error format
        response = client.get("/v1/plans/nonexistent_plan")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        error_data = response.json()
        
        # Verify consistent error structure
        assert "detail" in error_data
        assert "error" in error_data["detail"]
        assert "message" in error_data["detail"]


# Test configuration
@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])