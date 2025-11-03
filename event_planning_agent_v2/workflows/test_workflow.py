"""
Test script for LangGraph workflow implementation.
Validates workflow creation and basic functionality.
"""

import json
import logging
from typing import Dict, Any

from .state_models import create_initial_state, EventPlanningState, WorkflowStatus
from .planning_workflow import create_event_planning_workflow
from .execution_engine import ExecutionConfig, ExecutionMode, get_execution_engine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_test_client_request() -> Dict[str, Any]:
    """Create a test client request for workflow testing"""
    return {
        "client_id": "test_client_001",
        "event_type": "wedding",
        "guest_count": 150,
        "budget": 500000,  # ₹5,00,000
        "date": "2024-06-15T18:00:00Z",
        "location": "Mumbai, Maharashtra",
        "preferences": {
            "style": "traditional",
            "cuisine": ["North Indian", "South Indian"],
            "venue_type": "banquet_hall",
            "photography_style": "candid"
        },
        "requirements": {
            "vegetarian_menu": True,
            "alcohol_service": False,
            "parking_required": True,
            "ac_required": True
        }
    }


def test_state_creation():
    """Test workflow state creation and validation"""
    logger.info("Testing workflow state creation...")
    
    client_request = create_test_client_request()
    
    # Create initial state
    initial_state = create_initial_state(
        client_request=client_request,
        plan_id="test_plan_001"
    )
    
    # Validate state structure
    assert initial_state['plan_id'] == "test_plan_001"
    assert initial_state['client_request'] == client_request
    assert initial_state['workflow_status'] == WorkflowStatus.INITIALIZED.value
    assert initial_state['iteration_count'] == 0
    assert initial_state['beam_width'] == 3
    
    logger.info("✓ State creation test passed")
    return initial_state


def test_workflow_graph_creation():
    """Test workflow graph creation and compilation"""
    logger.info("Testing workflow graph creation...")
    
    try:
        # Create workflow graph
        workflow_graph = create_event_planning_workflow()
        
        # Verify nodes exist
        expected_nodes = [
            "initialize", 
            "budget_allocation", 
            "vendor_sourcing", 
            "beam_search", 
            "client_selection", 
            "blueprint_generation"
        ]
        
        # Get actual nodes from the graph
        actual_nodes = list(workflow_graph.nodes.keys())
        
        for node in expected_nodes:
            assert node in actual_nodes, f"Missing node: {node}"
        
        logger.info("✓ Workflow graph creation test passed")
        return workflow_graph
        
    except Exception as e:
        logger.error(f"✗ Workflow graph creation test failed: {e}")
        raise


def test_workflow_compilation():
    """Test workflow compilation"""
    logger.info("Testing workflow compilation...")
    
    try:
        # Create and compile workflow
        workflow_graph = create_event_planning_workflow()
        compiled_workflow = workflow_graph.compile()
        
        # Verify compilation succeeded
        assert compiled_workflow is not None
        
        logger.info("✓ Workflow compilation test passed")
        return compiled_workflow
        
    except Exception as e:
        logger.error(f"✗ Workflow compilation test failed: {e}")
        raise


def test_execution_engine_creation():
    """Test execution engine creation and configuration"""
    logger.info("Testing execution engine creation...")
    
    try:
        # Create execution config
        config = ExecutionConfig(
            mode=ExecutionMode.SYNCHRONOUS,
            max_retries=2,
            timeout=60.0,
            enable_checkpointing=False,  # Disable for testing
            debug_mode=True
        )
        
        # Create execution engine
        engine = get_execution_engine(config)
        
        # Verify engine configuration
        assert engine.config.mode == ExecutionMode.SYNCHRONOUS
        assert engine.config.max_retries == 2
        assert engine.config.timeout == 60.0
        
        logger.info("✓ Execution engine creation test passed")
        return engine
        
    except Exception as e:
        logger.error(f"✗ Execution engine creation test failed: {e}")
        raise


def test_workflow_initialization():
    """Test workflow initialization node"""
    logger.info("Testing workflow initialization...")
    
    try:
        from .planning_workflow import EventPlanningWorkflowNodes
        
        # Create workflow nodes
        nodes = EventPlanningWorkflowNodes()
        
        # Create test state
        client_request = create_test_client_request()
        initial_state = create_initial_state(client_request, "test_init_001")
        
        # Test initialization node
        result_state = nodes.initialize_planning(initial_state)
        
        # Verify initialization results
        assert result_state['workflow_status'] == WorkflowStatus.RUNNING.value
        assert result_state['next_node'] == 'budget_allocation'
        assert len(result_state.get('state_transitions', [])) > 0
        
        logger.info("✓ Workflow initialization test passed")
        return result_state
        
    except Exception as e:
        logger.error(f"✗ Workflow initialization test failed: {e}")
        raise


def run_basic_workflow_tests():
    """Run basic workflow functionality tests"""
    logger.info("Starting basic workflow tests...")
    
    try:
        # Test 1: State creation
        initial_state = test_state_creation()
        
        # Test 2: Workflow graph creation
        workflow_graph = test_workflow_graph_creation()
        
        # Test 3: Workflow compilation
        compiled_workflow = test_workflow_compilation()
        
        # Test 4: Execution engine creation
        execution_engine = test_execution_engine_creation()
        
        # Test 5: Workflow initialization
        initialized_state = test_workflow_initialization()
        
        logger.info("✓ All basic workflow tests passed!")
        
        return {
            "success": True,
            "tests_passed": 5,
            "initial_state": initial_state,
            "workflow_graph": workflow_graph,
            "compiled_workflow": compiled_workflow,
            "execution_engine": execution_engine,
            "initialized_state": initialized_state
        }
        
    except Exception as e:
        logger.error(f"✗ Workflow tests failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def test_workflow_state_transitions():
    """Test workflow state transitions and validation"""
    logger.info("Testing workflow state transitions...")
    
    try:
        from .state_models import validate_state_transition, WorkflowStatus
        
        # Test valid transitions
        valid_transitions = [
            (WorkflowStatus.INITIALIZED, WorkflowStatus.RUNNING),
            (WorkflowStatus.RUNNING, WorkflowStatus.BUDGET_ALLOCATION),
            (WorkflowStatus.BUDGET_ALLOCATION, WorkflowStatus.VENDOR_SOURCING),
            (WorkflowStatus.VENDOR_SOURCING, WorkflowStatus.BEAM_SEARCH),
            (WorkflowStatus.BEAM_SEARCH, WorkflowStatus.CLIENT_SELECTION),
            (WorkflowStatus.CLIENT_SELECTION, WorkflowStatus.BLUEPRINT_GENERATION),
            (WorkflowStatus.BLUEPRINT_GENERATION, WorkflowStatus.COMPLETED)
        ]
        
        for from_status, to_status in valid_transitions:
            assert validate_state_transition(from_status.value, to_status.value), \
                f"Valid transition {from_status} -> {to_status} failed validation"
        
        # Test invalid transitions
        invalid_transitions = [
            (WorkflowStatus.COMPLETED, WorkflowStatus.RUNNING),
            (WorkflowStatus.INITIALIZED, WorkflowStatus.COMPLETED),
            (WorkflowStatus.BUDGET_ALLOCATION, WorkflowStatus.BLUEPRINT_GENERATION)
        ]
        
        for from_status, to_status in invalid_transitions:
            assert not validate_state_transition(from_status.value, to_status.value), \
                f"Invalid transition {from_status} -> {to_status} passed validation"
        
        logger.info("✓ State transition validation test passed")
        
    except Exception as e:
        logger.error(f"✗ State transition validation test failed: {e}")
        raise


def run_comprehensive_workflow_tests():
    """Run comprehensive workflow tests"""
    logger.info("Starting comprehensive workflow tests...")
    
    try:
        # Run basic tests
        basic_results = run_basic_workflow_tests()
        if not basic_results["success"]:
            return basic_results
        
        # Test state transitions
        test_workflow_state_transitions()
        
        logger.info("✓ All comprehensive workflow tests passed!")
        
        return {
            "success": True,
            "basic_tests": basic_results,
            "additional_tests": ["state_transitions"]
        }
        
    except Exception as e:
        logger.error(f"✗ Comprehensive workflow tests failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }


if __name__ == "__main__":
    """Run workflow tests when executed directly"""
    print("Running LangGraph Workflow Tests...")
    print("=" * 50)
    
    results = run_comprehensive_workflow_tests()
    
    print("\nTest Results:")
    print("=" * 50)
    
    if results["success"]:
        print("✓ All tests passed successfully!")
        print(f"✓ Basic tests: {results['basic_tests']['tests_passed']} passed")
        print(f"✓ Additional tests: {len(results.get('additional_tests', []))} passed")
    else:
        print(f"✗ Tests failed: {results.get('error', 'Unknown error')}")
    
    print("\nWorkflow implementation is ready for integration!")