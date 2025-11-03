#!/usr/bin/env python3
"""
Test script for database setup and functionality.
Verifies that all database components work correctly.
"""

import os
import sys
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import (
    setup_database,
    test_database_connection,
    create_workflow_state,
    save_workflow_state,
    load_workflow_state,
    record_agent_performance,
    get_system_health_status,
    record_system_health
)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_database_setup():
    """Test basic database setup"""
    logger.info("🧪 Testing database setup...")
    
    try:
        # Test database connection
        connection_status = test_database_connection()
        logger.info(f"Connection status: {connection_status}")
        
        if not connection_status.get('sync_connection'):
            logger.error("❌ Database connection failed")
            return False
        
        logger.info("✅ Database connection successful")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database setup test failed: {e}")
        return False


def test_state_management():
    """Test workflow state management"""
    logger.info("🧪 Testing state management...")
    
    try:
        # Create test workflow state
        client_request = {
            "client_id": "test_client",
            "event_type": "wedding",
            "guest_count": 100,
            "budget": 50000,
            "location": "Bangalore"
        }
        
        state = create_workflow_state(client_request)
        logger.info(f"Created workflow state: {state['plan_id']}")
        
        # Update state
        state['workflow_status'] = 'running'
        state['iteration_count'] = 1
        state['beam_candidates'] = [
            {"combination_id": 1, "score": 0.85},
            {"combination_id": 2, "score": 0.82}
        ]
        
        # Save updated state
        if save_workflow_state(state):
            logger.info("✅ State saved successfully")
        else:
            logger.error("❌ Failed to save state")
            return False
        
        # Load state back
        loaded_state = load_workflow_state(state['plan_id'])
        if loaded_state and loaded_state['workflow_status'] == 'running':
            logger.info("✅ State loaded successfully")
        else:
            logger.error("❌ Failed to load state")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ State management test failed: {e}")
        return False


def test_performance_tracking():
    """Test performance tracking functionality"""
    logger.info("🧪 Testing performance tracking...")
    
    try:
        # Record test agent performance
        success = record_agent_performance(
            plan_id="test-plan-123",
            agent_name="TestAgent",
            task_name="test_task",
            execution_time_ms=150,
            success=True,
            input_data={"test": "data"},
            output_data={"result": "success"}
        )
        
        if success:
            logger.info("✅ Agent performance recorded successfully")
        else:
            logger.error("❌ Failed to record agent performance")
            return False
        
        # Record system health
        health_success = record_system_health(
            component_name="test_component",
            status="healthy",
            response_time_ms=50,
            metadata={"version": "1.0.0"}
        )
        
        if health_success:
            logger.info("✅ System health recorded successfully")
        else:
            logger.error("❌ Failed to record system health")
            return False
        
        # Get system health status
        health_status = get_system_health_status()
        logger.info(f"System health status: {health_status['overall_status']}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Performance tracking test failed: {e}")
        return False


def run_all_tests():
    """Run all database tests"""
    logger.info("🚀 Starting database tests...")
    
    tests = [
        ("Database Setup", test_database_setup),
        ("State Management", test_state_management),
        ("Performance Tracking", test_performance_tracking)
    ]
    
    results = {}
    for test_name, test_func in tests:
        logger.info(f"\n--- Running {test_name} Test ---")
        results[test_name] = test_func()
    
    # Summary
    logger.info("\n📊 Test Results Summary:")
    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        logger.info(f"  {test_name}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        logger.info("\n🎉 All tests passed!")
        return True
    else:
        logger.error("\n💥 Some tests failed!")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Test database setup and functionality')
    parser.add_argument('--setup-only', action='store_true', help='Only run database setup test')
    parser.add_argument('--no-setup', action='store_true', help='Skip database setup, run other tests only')
    
    args = parser.parse_args()
    
    if args.setup_only:
        success = test_database_setup()
        sys.exit(0 if success else 1)
    elif args.no_setup:
        # Run tests without setup
        tests = [
            ("State Management", test_state_management),
            ("Performance Tracking", test_performance_tracking)
        ]
        
        all_passed = True
        for test_name, test_func in tests:
            logger.info(f"\n--- Running {test_name} Test ---")
            if not test_func():
                all_passed = False
        
        sys.exit(0 if all_passed else 1)
    else:
        success = run_all_tests()
        sys.exit(0 if success else 1)