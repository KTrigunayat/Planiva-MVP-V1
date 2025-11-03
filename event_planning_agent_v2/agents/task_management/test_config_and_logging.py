"""
Test script to verify Task Management configuration and logging integration.

This script tests:
1. Configuration loading and validation
2. Logging initialization and output
3. Integration with Task Management Agent
"""

import sys
import os
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.task_management_config import (
    TASK_MANAGEMENT_CONFIG,
    DEVELOPMENT_CONFIG,
    PRODUCTION_CONFIG,
    TESTING_CONFIG,
    get_config,
    load_config_from_env,
    TaskManagementConfig,
    LLMModel,
    LogLevel
)
from observability.logging import get_logger, setup_default_logging


def test_configuration():
    """Test configuration loading and validation"""
    print("=" * 80)
    print("Testing Task Management Configuration")
    print("=" * 80)
    
    # Test default configuration
    print("\n1. Testing default configuration...")
    config = TASK_MANAGEMENT_CONFIG
    print(f"   ✓ Default config loaded")
    print(f"   - LLM Model: {config.llm_model}")
    print(f"   - Log Level: {config.log_level}")
    print(f"   - Parallel Execution: {config.parallel_tool_execution}")
    print(f"   - Enable LLM Enhancement: {config.enable_llm_enhancement}")
    
    # Test environment-specific configurations
    print("\n2. Testing environment-specific configurations...")
    dev_config = get_config("development")
    print(f"   ✓ Development config: log_level={dev_config.log_level}, debug={dev_config.enable_debug_logging}")
    
    prod_config = get_config("production")
    print(f"   ✓ Production config: log_level={prod_config.log_level}, debug={prod_config.enable_debug_logging}")
    
    test_config = get_config("testing")
    print(f"   ✓ Testing config: log_level={test_config.log_level}, llm_enabled={test_config.enable_llm_enhancement}")
    
    # Test configuration validation
    print("\n3. Testing configuration validation...")
    try:
        config.validate()
        print("   ✓ Configuration validation passed")
    except Exception as e:
        print(f"   ✗ Configuration validation failed: {e}")
        return False
    
    # Test configuration serialization
    print("\n4. Testing configuration serialization...")
    config_dict = config.to_dict()
    print(f"   ✓ Configuration serialized to dict with {len(config_dict)} keys")
    
    # Test configuration deserialization
    new_config = TaskManagementConfig.from_dict(config_dict)
    print(f"   ✓ Configuration deserialized from dict")
    
    # Test environment variable loading
    print("\n5. Testing environment variable loading...")
    os.environ["TASK_MGMT_LLM_MODEL"] = "tinyllama"
    os.environ["TASK_MGMT_LOG_LEVEL"] = "DEBUG"
    env_config = load_config_from_env()
    print(f"   ✓ Config from env: model={env_config.llm_model}, log_level={env_config.log_level}")
    
    # Clean up environment variables
    del os.environ["TASK_MGMT_LLM_MODEL"]
    del os.environ["TASK_MGMT_LOG_LEVEL"]
    
    print("\n✓ All configuration tests passed!")
    return True


def test_logging():
    """Test logging initialization and output"""
    print("\n" + "=" * 80)
    print("Testing Logging Integration")
    print("=" * 80)
    
    # Setup logging
    print("\n1. Setting up structured logging...")
    setup_default_logging(level=LogLevel.DEBUG, log_directory="logs/test")
    print("   ✓ Logging initialized")
    
    # Get logger for task management
    print("\n2. Creating task management logger...")
    logger = get_logger("task_management_test", component="task_management")
    print("   ✓ Logger created")
    
    # Test different log levels
    print("\n3. Testing log levels...")
    logger.debug("Debug message test", operation="test_debug")
    logger.info("Info message test", operation="test_info")
    logger.warning("Warning message test", operation="test_warning")
    logger.error("Error message test", operation="test_error")
    print("   ✓ All log levels tested")
    
    # Test structured logging with metadata
    print("\n4. Testing structured logging with metadata...")
    logger.info(
        "Processing task management request",
        operation="test_metadata",
        metadata={
            "plan_id": "test-123",
            "task_count": 10,
            "config": {"llm_model": "gemma:2b"}
        }
    )
    print("   ✓ Structured logging with metadata tested")
    
    # Test performance logging
    print("\n5. Testing performance logging...")
    logger.log_performance(
        operation="test_operation",
        duration_ms=123.45,
        success=True,
        metadata={"test": "data"}
    )
    print("   ✓ Performance logging tested")
    
    # Test agent interaction logging
    print("\n6. Testing agent interaction logging...")
    logger.log_agent_interaction(
        agent_name="TestAgent",
        action="test_action",
        duration_ms=50.0,
        success=True,
        input_data={"input": "test"},
        output_data={"output": "result"}
    )
    print("   ✓ Agent interaction logging tested")
    
    print("\n✓ All logging tests passed!")
    return True


async def test_integration():
    """Test integration with Task Management Agent"""
    print("\n" + "=" * 80)
    print("Testing Task Management Agent Integration")
    print("=" * 80)
    
    try:
        # Import Task Management Agent
        print("\n1. Importing Task Management Agent...")
        from agents.task_management.core.task_management_agent import TaskManagementAgent
        print("   ✓ Task Management Agent imported")
        
        # Create agent with custom configuration
        print("\n2. Creating Task Management Agent with custom config...")
        config_dict = {
            "enable_llm_enhancement": False,  # Disable for testing
            "llm_model": "tinyllama",
            "log_level": "DEBUG",
            "enable_debug_logging": True,
            "log_sub_agent_outputs": True,
            "log_tool_results": True,
            "parallel_tool_execution": False
        }
        
        agent = TaskManagementAgent(config=config_dict)
        print("   ✓ Task Management Agent created with custom config")
        print(f"   - LLM Model: {agent.config.llm_model}")
        print(f"   - Log Level: {agent.config.log_level}")
        print(f"   - Debug Logging: {agent.config.enable_debug_logging}")
        
        # Verify configuration is applied
        print("\n3. Verifying configuration...")
        assert agent.config.llm_model == "tinyllama", "LLM model not set correctly"
        assert agent.config.log_level == "DEBUG", "Log level not set correctly"
        assert agent.config.enable_debug_logging == True, "Debug logging not enabled"
        print("   ✓ Configuration verified")
        
        print("\n✓ Integration tests passed!")
        return True
        
    except Exception as e:
        print(f"\n✗ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("Task Management Configuration and Logging Test Suite")
    print("=" * 80)
    
    results = []
    
    # Run configuration tests
    results.append(("Configuration", test_configuration()))
    
    # Run logging tests
    results.append(("Logging", test_logging()))
    
    # Run integration tests
    results.append(("Integration", asyncio.run(test_integration())))
    
    # Print summary
    print("\n" + "=" * 80)
    print("Test Summary")
    print("=" * 80)
    
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n✓ All tests passed!")
        return 0
    else:
        print("\n✗ Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
