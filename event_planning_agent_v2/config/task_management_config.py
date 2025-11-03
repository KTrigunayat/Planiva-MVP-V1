"""
Task Management Agent Configuration

Configuration settings for the Task Management Agent including
LLM settings, tool enablement flags, and logging configuration.
"""

from typing import Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass, field


class LLMModel(str, Enum):
    """Available LLM models for task management"""
    GEMMA_2B = "gemma:2b"
    TINYLLAMA = "tinyllama"


class LogLevel(str, Enum):
    """Log levels for task management"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class TaskManagementConfig:
    """Task Management Agent configuration"""
    
    # LLM Enhancement Settings
    enable_llm_enhancement: bool = True
    llm_model: str = LLMModel.GEMMA_2B.value
    max_retries: int = 3
    timeout_seconds: int = 30
    
    # Tool Enablement Flags
    enable_conflict_detection: bool = True
    enable_logistics_check: bool = True
    enable_venue_lookup: bool = True
    enable_vendor_assignment: bool = True
    enable_timeline_calculation: bool = True
    
    # Processing Settings
    parallel_tool_execution: bool = False  # Sequential by default
    
    # Logging Configuration
    log_level: str = LogLevel.INFO.value
    enable_debug_logging: bool = False
    enable_performance_logging: bool = True
    log_sub_agent_outputs: bool = True
    log_tool_results: bool = True
    
    # Sub-Agent Settings
    enable_prioritization_agent: bool = True
    enable_granularity_agent: bool = True
    enable_resource_dependency_agent: bool = True
    
    # Error Handling
    continue_on_sub_agent_error: bool = True
    continue_on_tool_error: bool = True
    max_tool_retries: int = 2
    
    # Performance Optimization
    enable_caching: bool = True
    cache_ttl_seconds: int = 300  # 5 minutes
    batch_processing_enabled: bool = False
    
    # Validation Settings
    validate_consolidated_data: bool = True
    strict_validation: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            "enable_llm_enhancement": self.enable_llm_enhancement,
            "llm_model": self.llm_model,
            "max_retries": self.max_retries,
            "timeout_seconds": self.timeout_seconds,
            "enable_conflict_detection": self.enable_conflict_detection,
            "enable_logistics_check": self.enable_logistics_check,
            "enable_venue_lookup": self.enable_venue_lookup,
            "enable_vendor_assignment": self.enable_vendor_assignment,
            "enable_timeline_calculation": self.enable_timeline_calculation,
            "parallel_tool_execution": self.parallel_tool_execution,
            "log_level": self.log_level,
            "enable_debug_logging": self.enable_debug_logging,
            "enable_performance_logging": self.enable_performance_logging,
            "log_sub_agent_outputs": self.log_sub_agent_outputs,
            "log_tool_results": self.log_tool_results,
            "enable_prioritization_agent": self.enable_prioritization_agent,
            "enable_granularity_agent": self.enable_granularity_agent,
            "enable_resource_dependency_agent": self.enable_resource_dependency_agent,
            "continue_on_sub_agent_error": self.continue_on_sub_agent_error,
            "continue_on_tool_error": self.continue_on_tool_error,
            "max_tool_retries": self.max_tool_retries,
            "enable_caching": self.enable_caching,
            "cache_ttl_seconds": self.cache_ttl_seconds,
            "batch_processing_enabled": self.batch_processing_enabled,
            "validate_consolidated_data": self.validate_consolidated_data,
            "strict_validation": self.strict_validation,
        }
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'TaskManagementConfig':
        """Create configuration from dictionary"""
        return cls(**{k: v for k, v in config_dict.items() if k in cls.__annotations__})
    
    def validate(self) -> bool:
        """Validate configuration settings"""
        # Validate timeout
        if self.timeout_seconds < 1 or self.timeout_seconds > 300:
            raise ValueError("timeout_seconds must be between 1 and 300")
        
        # Validate retries
        if self.max_retries < 0 or self.max_retries > 10:
            raise ValueError("max_retries must be between 0 and 10")
        
        # Validate LLM model
        if self.llm_model not in [LLMModel.GEMMA_2B.value, LLMModel.TINYLLAMA.value]:
            raise ValueError(f"llm_model must be one of: {[m.value for m in LLMModel]}")
        
        # Validate log level
        if self.log_level not in [level.value for level in LogLevel]:
            raise ValueError(f"log_level must be one of: {[level.value for level in LogLevel]}")
        
        # Validate cache TTL
        if self.cache_ttl_seconds < 0:
            raise ValueError("cache_ttl_seconds must be non-negative")
        
        return True


# Default configuration instance
TASK_MANAGEMENT_CONFIG = TaskManagementConfig()


# Configuration presets for different environments
DEVELOPMENT_CONFIG = TaskManagementConfig(
    enable_llm_enhancement=True,
    llm_model=LLMModel.GEMMA_2B.value,
    max_retries=3,
    timeout_seconds=30,
    enable_conflict_detection=True,
    enable_logistics_check=True,
    enable_venue_lookup=True,
    enable_vendor_assignment=True,
    enable_timeline_calculation=True,
    parallel_tool_execution=False,
    log_level=LogLevel.DEBUG.value,
    enable_debug_logging=True,
    enable_performance_logging=True,
    log_sub_agent_outputs=True,
    log_tool_results=True,
    continue_on_sub_agent_error=True,
    continue_on_tool_error=True,
    enable_caching=True,
    cache_ttl_seconds=300,
)


PRODUCTION_CONFIG = TaskManagementConfig(
    enable_llm_enhancement=True,
    llm_model=LLMModel.GEMMA_2B.value,
    max_retries=3,
    timeout_seconds=60,
    enable_conflict_detection=True,
    enable_logistics_check=True,
    enable_venue_lookup=True,
    enable_vendor_assignment=True,
    enable_timeline_calculation=True,
    parallel_tool_execution=False,
    log_level=LogLevel.INFO.value,
    enable_debug_logging=False,
    enable_performance_logging=True,
    log_sub_agent_outputs=False,
    log_tool_results=False,
    continue_on_sub_agent_error=True,
    continue_on_tool_error=True,
    enable_caching=True,
    cache_ttl_seconds=600,
)


TESTING_CONFIG = TaskManagementConfig(
    enable_llm_enhancement=False,  # Disable LLM for faster tests
    llm_model=LLMModel.TINYLLAMA.value,
    max_retries=1,
    timeout_seconds=10,
    enable_conflict_detection=True,
    enable_logistics_check=True,
    enable_venue_lookup=True,
    enable_vendor_assignment=True,
    enable_timeline_calculation=True,
    parallel_tool_execution=False,
    log_level=LogLevel.WARNING.value,
    enable_debug_logging=False,
    enable_performance_logging=False,
    log_sub_agent_outputs=False,
    log_tool_results=False,
    continue_on_sub_agent_error=True,
    continue_on_tool_error=True,
    enable_caching=False,
    cache_ttl_seconds=0,
)


def get_config(environment: str = "development") -> TaskManagementConfig:
    """
    Get configuration for specified environment
    
    Args:
        environment: Environment name (development, production, testing)
        
    Returns:
        TaskManagementConfig instance for the environment
    """
    env_lower = environment.lower()
    
    if env_lower == "production":
        return PRODUCTION_CONFIG
    elif env_lower == "testing":
        return TESTING_CONFIG
    else:
        return DEVELOPMENT_CONFIG


def load_config_from_env() -> TaskManagementConfig:
    """
    Load configuration from environment variables
    
    Environment variables:
        TASK_MGMT_ENABLE_LLM_ENHANCEMENT: Enable LLM enhancement (true/false)
        TASK_MGMT_LLM_MODEL: LLM model to use (gemma:2b/tinyllama)
        TASK_MGMT_MAX_RETRIES: Maximum retry attempts
        TASK_MGMT_TIMEOUT_SECONDS: Timeout in seconds
        TASK_MGMT_ENABLE_CONFLICT_DETECTION: Enable conflict detection (true/false)
        TASK_MGMT_ENABLE_LOGISTICS_CHECK: Enable logistics check (true/false)
        TASK_MGMT_ENABLE_VENUE_LOOKUP: Enable venue lookup (true/false)
        TASK_MGMT_PARALLEL_EXECUTION: Enable parallel tool execution (true/false)
        TASK_MGMT_LOG_LEVEL: Logging level (DEBUG/INFO/WARNING/ERROR/CRITICAL)
    
    Returns:
        TaskManagementConfig instance with environment variable overrides
    """
    import os
    
    config = TaskManagementConfig()
    
    # LLM settings
    if os.getenv("TASK_MGMT_ENABLE_LLM_ENHANCEMENT"):
        config.enable_llm_enhancement = os.getenv("TASK_MGMT_ENABLE_LLM_ENHANCEMENT", "true").lower() == "true"
    
    if os.getenv("TASK_MGMT_LLM_MODEL"):
        config.llm_model = os.getenv("TASK_MGMT_LLM_MODEL", LLMModel.GEMMA_2B.value)
    
    if os.getenv("TASK_MGMT_MAX_RETRIES"):
        config.max_retries = int(os.getenv("TASK_MGMT_MAX_RETRIES", "3"))
    
    if os.getenv("TASK_MGMT_TIMEOUT_SECONDS"):
        config.timeout_seconds = int(os.getenv("TASK_MGMT_TIMEOUT_SECONDS", "30"))
    
    # Tool enablement
    if os.getenv("TASK_MGMT_ENABLE_CONFLICT_DETECTION"):
        config.enable_conflict_detection = os.getenv("TASK_MGMT_ENABLE_CONFLICT_DETECTION", "true").lower() == "true"
    
    if os.getenv("TASK_MGMT_ENABLE_LOGISTICS_CHECK"):
        config.enable_logistics_check = os.getenv("TASK_MGMT_ENABLE_LOGISTICS_CHECK", "true").lower() == "true"
    
    if os.getenv("TASK_MGMT_ENABLE_VENUE_LOOKUP"):
        config.enable_venue_lookup = os.getenv("TASK_MGMT_ENABLE_VENUE_LOOKUP", "true").lower() == "true"
    
    # Processing settings
    if os.getenv("TASK_MGMT_PARALLEL_EXECUTION"):
        config.parallel_tool_execution = os.getenv("TASK_MGMT_PARALLEL_EXECUTION", "false").lower() == "true"
    
    # Logging
    if os.getenv("TASK_MGMT_LOG_LEVEL"):
        config.log_level = os.getenv("TASK_MGMT_LOG_LEVEL", LogLevel.INFO.value)
    
    # Validate configuration
    config.validate()
    
    return config


# Export configuration utilities
__all__ = [
    "TaskManagementConfig",
    "LLMModel",
    "LogLevel",
    "TASK_MANAGEMENT_CONFIG",
    "DEVELOPMENT_CONFIG",
    "PRODUCTION_CONFIG",
    "TESTING_CONFIG",
    "get_config",
    "load_config_from_env",
]
