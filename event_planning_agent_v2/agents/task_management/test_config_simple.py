"""
Simple test script to verify Task Management configuration without dependencies.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def test_configuration_standalone():
    """Test configuration as standalone module"""
    print("=" * 80)
    print("Testing Task Management Configuration (Standalone)")
    print("=" * 80)
    
    try:
        # Import configuration module
        print("\n1. Importing configuration module...")
        from config.task_management_config import (
            TaskManagementConfig,
            LLMModel,
            LogLevel,
            TASK_MANAGEMENT_CONFIG,
            DEVELOPMENT_CONFIG,
            PRODUCTION_CONFIG,
            TESTING_CONFIG,
            get_config
        )
        print("   ✓ Configuration module imported successfully")
        
        # Test default configuration
        print("\n2. Testing default configuration...")
        config = TASK_MANAGEMENT_CONFIG
        print(f"   ✓ Default config loaded")
        print(f"   - LLM Model: {config.llm_model}")
        print(f"   - Log Level: {config.log_level}")
        print(f"   - Max Retries: {config.max_retries}")
        print(f"   - Timeout: {config.timeout_seconds}s")
        print(f"   - Parallel Execution: {config.parallel_tool_execution}")
        print(f"   - Enable LLM Enhancement: {config.enable_llm_enhancement}")
        print(f"   - Enable Conflict Detection: {config.enable_conflict_detection}")
        print(f"   - Enable Logistics Check: {config.enable_logistics_check}")
        print(f"   - Enable Venue Lookup: {config.enable_venue_lookup}")
        
        # Test environment-specific configurations
        print("\n3. Testing environment-specific configurations...")
        
        dev_config = get_config("development")
        print(f"   ✓ Development config:")
        print(f"     - Log Level: {dev_config.log_level}")
        print(f"     - Debug Logging: {dev_config.enable_debug_logging}")
        print(f"     - Performance Logging: {dev_config.enable_performance_logging}")
        
        prod_config = get_config("production")
        print(f"   ✓ Production config:")
        print(f"     - Log Level: {prod_config.log_level}")
        print(f"     - Debug Logging: {prod_config.enable_debug_logging}")
        print(f"     - Timeout: {prod_config.timeout_seconds}s")
        
        test_config = get_config("testing")
        print(f"   ✓ Testing config:")
        print(f"     - Log Level: {test_config.log_level}")
        print(f"     - LLM Enabled: {test_config.enable_llm_enhancement}")
        print(f"     - Caching: {test_config.enable_caching}")
        
        # Test configuration validation
        print("\n4. Testing configuration validation...")
        try:
            config.validate()
            print("   ✓ Default configuration validation passed")
            
            dev_config.validate()
            print("   ✓ Development configuration validation passed")
            
            prod_config.validate()
            print("   ✓ Production configuration validation passed")
            
            test_config.validate()
            print("   ✓ Testing configuration validation passed")
        except Exception as e:
            print(f"   ✗ Configuration validation failed: {e}")
            return False
        
        # Test configuration serialization
        print("\n5. Testing configuration serialization...")
        config_dict = config.to_dict()
        print(f"   ✓ Configuration serialized to dict with {len(config_dict)} keys")
        print(f"   - Keys: {', '.join(list(config_dict.keys())[:10])}...")
        
        # Test configuration deserialization
        print("\n6. Testing configuration deserialization...")
        new_config = TaskManagementConfig.from_dict(config_dict)
        print(f"   ✓ Configuration deserialized from dict")
        print(f"   - LLM Model: {new_config.llm_model}")
        print(f"   - Log Level: {new_config.log_level}")
        
        # Test custom configuration
        print("\n7. Testing custom configuration...")
        custom_config = TaskManagementConfig(
            enable_llm_enhancement=False,
            llm_model=LLMModel.TINYLLAMA.value,
            max_retries=5,
            timeout_seconds=60,
            log_level=LogLevel.WARNING.value,
            parallel_tool_execution=True
        )
        custom_config.validate()
        print(f"   ✓ Custom configuration created and validated")
        print(f"   - LLM Model: {custom_config.llm_model}")
        print(f"   - Max Retries: {custom_config.max_retries}")
        print(f"   - Parallel Execution: {custom_config.parallel_tool_execution}")
        
        # Test invalid configuration
        print("\n8. Testing invalid configuration handling...")
        try:
            invalid_config = TaskManagementConfig(
                timeout_seconds=500,  # Invalid: > 300
            )
            invalid_config.validate()
            print("   ✗ Invalid configuration should have failed validation")
            return False
        except ValueError as e:
            print(f"   ✓ Invalid configuration correctly rejected: {e}")
        
        print("\n" + "=" * 80)
        print("✓ All configuration tests passed!")
        print("=" * 80)
        return True
        
    except Exception as e:
        print(f"\n✗ Configuration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run tests"""
    success = test_configuration_standalone()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
