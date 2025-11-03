"""
Enhanced configuration settings for Event Planning Agent v2
with validation, hot-reloading, and security features
"""

import os
import json
import logging
import secrets
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
from enum import Enum
from functools import lru_cache
from pydantic import BaseSettings, Field, validator, root_validator
from pydantic.networks import AnyHttpUrl, PostgresDsn


class Environment(str, Enum):
    """Environment types"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class LogLevel(str, Enum):
    """Log levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class DatabaseSettings(BaseSettings):
    """Database configuration settings with performance optimizations"""
    
    url: PostgresDsn = Field(
        default="postgresql://user:password@localhost:5432/eventdb",
        env="DATABASE_URL",
        description="PostgreSQL database URL"
    )
    
    # Optimized connection pool settings
    pool_size: int = Field(default=20, env="DB_POOL_SIZE", ge=1, le=100)
    max_overflow: int = Field(default=40, env="DB_MAX_OVERFLOW", ge=0, le=200)
    pool_timeout: int = Field(default=30, env="DB_POOL_TIMEOUT", ge=1, le=300)
    pool_recycle: int = Field(default=3600, env="DB_POOL_RECYCLE", ge=300)
    pool_pre_ping: bool = Field(default=True, env="DB_POOL_PRE_PING")
    
    # Query optimization settings
    echo: bool = Field(default=False, env="DB_ECHO")
    echo_pool: bool = Field(default=False, env="DB_ECHO_POOL")
    
    # Performance tuning parameters
    statement_timeout: int = Field(default=30000, env="DB_STATEMENT_TIMEOUT", ge=1000, le=300000)  # 30 seconds
    lock_timeout: int = Field(default=10000, env="DB_LOCK_TIMEOUT", ge=1000, le=60000)  # 10 seconds
    idle_in_transaction_session_timeout: int = Field(default=60000, env="DB_IDLE_TIMEOUT", ge=10000, le=300000)  # 60 seconds
    
    # Connection health monitoring
    max_connection_errors: int = Field(default=5, env="DB_MAX_CONNECTION_ERRORS", ge=1, le=20)
    connection_retry_delay: int = Field(default=5, env="DB_CONNECTION_RETRY_DELAY", ge=1, le=60)
    
    # Query caching
    enable_query_cache: bool = Field(default=True, env="DB_ENABLE_QUERY_CACHE")
    query_cache_size: int = Field(default=1000, env="DB_QUERY_CACHE_SIZE", ge=100, le=10000)
    query_cache_ttl: int = Field(default=300, env="DB_QUERY_CACHE_TTL", ge=60, le=3600)  # 5 minutes
    
    class Config:
        env_prefix = "DB_"


class APISettings(BaseSettings):
    """API configuration settings"""
    
    host: str = Field(default="0.0.0.0", env="API_HOST")
    port: int = Field(default=8000, env="API_PORT", ge=1, le=65535)
    workers: int = Field(default=1, env="API_WORKERS", ge=1, le=16)
    reload: bool = Field(default=False, env="API_RELOAD")
    debug: bool = Field(default=False, env="DEBUG")
    
    # CORS Configuration
    cors_origins: List[str] = Field(
        default=["*"],
        env="CORS_ORIGINS",
        description="Allowed CORS origins (comma-separated)"
    )
    cors_methods: List[str] = Field(
        default=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        env="CORS_METHODS"
    )
    cors_headers: List[str] = Field(
        default=["*"],
        env="CORS_HEADERS"
    )
    
    @validator('cors_origins', pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v
    
    class Config:
        env_prefix = "API_"


class SecuritySettings(BaseSettings):
    """Security configuration settings"""
    
    auth_enabled: bool = Field(default=True, env="AUTH_ENABLED")
    jwt_secret: str = Field(default_factory=lambda: secrets.token_urlsafe(32), env="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    token_expiry_hours: int = Field(default=24, env="TOKEN_EXPIRY_HOURS", ge=1, le=168)
    
    # Rate Limiting
    rate_limiting_enabled: bool = Field(default=True, env="RATE_LIMITING_ENABLED")
    rate_limit_per_minute: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE", ge=1)
    rate_limit_per_hour: int = Field(default=1000, env="RATE_LIMIT_PER_HOUR", ge=1)
    rate_limit_burst: int = Field(default=10, env="RATE_LIMIT_BURST", ge=1)
    
    # Security Headers
    enable_security_headers: bool = Field(default=True, env="ENABLE_SECURITY_HEADERS")
    allowed_hosts: List[str] = Field(default=["*"], env="ALLOWED_HOSTS")
    
    @validator('jwt_secret')
    def validate_jwt_secret(cls, v):
        if len(v) < 32:
            raise ValueError('JWT secret must be at least 32 characters long')
        return v
    
    @validator('allowed_hosts', pre=True)
    def parse_allowed_hosts(cls, v):
        if isinstance(v, str):
            return [host.strip() for host in v.split(',')]
        return v
    
    class Config:
        env_prefix = "SECURITY_"


class LLMSettings(BaseSettings):
    """LLM configuration settings with performance optimizations"""
    
    ollama_base_url: AnyHttpUrl = Field(default="http://localhost:11434", env="OLLAMA_BASE_URL")
    gemma_model: str = Field(default="gemma:2b", env="GEMMA_MODEL")
    tinyllama_model: str = Field(default="tinyllama", env="TINYLLAMA_MODEL")
    
    # Model loading and caching optimizations
    model_timeout: int = Field(default=180, env="MODEL_TIMEOUT", ge=30, le=1800)  # Reduced from 300s
    model_retries: int = Field(default=3, env="MODEL_RETRIES", ge=1, le=10)
    model_warmup_enabled: bool = Field(default=True, env="MODEL_WARMUP_ENABLED")
    model_keep_alive: int = Field(default=300, env="MODEL_KEEP_ALIVE", ge=60, le=3600)  # 5 minutes
    
    # Response caching
    enable_response_cache: bool = Field(default=True, env="LLM_ENABLE_RESPONSE_CACHE")
    response_cache_size: int = Field(default=2000, env="LLM_RESPONSE_CACHE_SIZE", ge=100, le=10000)
    response_cache_ttl: int = Field(default=1800, env="LLM_RESPONSE_CACHE_TTL", ge=300, le=7200)  # 30 minutes
    
    # Batch processing
    enable_batch_processing: bool = Field(default=True, env="LLM_ENABLE_BATCH_PROCESSING")
    batch_size: int = Field(default=5, env="LLM_BATCH_SIZE", ge=1, le=20)
    batch_timeout: int = Field(default=60, env="LLM_BATCH_TIMEOUT", ge=10, le=300)
    
    # Connection optimization
    max_connections: int = Field(default=10, env="LLM_MAX_CONNECTIONS", ge=1, le=50)
    connection_timeout: int = Field(default=30, env="LLM_CONNECTION_TIMEOUT", ge=5, le=120)
    read_timeout: int = Field(default=120, env="LLM_READ_TIMEOUT", ge=30, le=600)
    
    # Model-specific optimizations
    use_gpu: bool = Field(default=True, env="LLM_USE_GPU")
    gpu_memory_fraction: float = Field(default=0.8, env="LLM_GPU_MEMORY_FRACTION", ge=0.1, le=1.0)
    
    class Config:
        env_prefix = "LLM_"


class WorkflowSettings(BaseSettings):
    """Workflow configuration settings with performance optimizations"""
    
    # CrewAI Configuration
    crew_verbose: bool = Field(default=False, env="CREW_VERBOSE")  # Disabled for performance
    max_iterations: int = Field(default=8, env="MAX_ITERATIONS", ge=1, le=100)  # Reduced from 10
    
    # Optimized LangGraph Configuration
    beam_width: int = Field(default=3, env="BEAM_WIDTH", ge=1, le=10)  # Preserved k=3 optimization
    max_workflow_iterations: int = Field(default=15, env="MAX_WORKFLOW_ITERATIONS", ge=1, le=100)  # Reduced from 20
    
    # Enhanced State Management
    state_checkpoint_interval: int = Field(default=3, env="STATE_CHECKPOINT_INTERVAL", ge=1, le=50)  # More frequent checkpoints
    max_beam_history_size: int = Field(default=50, env="MAX_BEAM_HISTORY_SIZE", ge=10, le=1000)  # Reduced memory usage
    enable_state_compression: bool = Field(default=True, env="ENABLE_STATE_COMPRESSION")
    
    # Optimized timeout settings
    agent_timeout: int = Field(default=240, env="AGENT_TIMEOUT", ge=30, le=1800)  # Reduced from 300s
    workflow_timeout: int = Field(default=1200, env="WORKFLOW_TIMEOUT", ge=300, le=7200)  # Reduced from 1800s
    
    # Parallel execution settings
    enable_parallel_agents: bool = Field(default=True, env="ENABLE_PARALLEL_AGENTS")
    max_parallel_agents: int = Field(default=3, env="MAX_PARALLEL_AGENTS", ge=1, le=10)
    
    # Early termination optimization
    enable_early_termination: bool = Field(default=True, env="ENABLE_EARLY_TERMINATION")
    early_termination_threshold: float = Field(default=0.9, env="EARLY_TERMINATION_THRESHOLD", ge=0.7, le=1.0)
    min_iterations_before_termination: int = Field(default=3, env="MIN_ITERATIONS_BEFORE_TERMINATION", ge=1, le=10)
    
    # Convergence detection
    enable_convergence_detection: bool = Field(default=True, env="ENABLE_CONVERGENCE_DETECTION")
    convergence_threshold: float = Field(default=0.05, env="CONVERGENCE_THRESHOLD", ge=0.01, le=0.2)
    convergence_window: int = Field(default=3, env="CONVERGENCE_WINDOW", ge=2, le=10)
    
    # Memory optimization
    enable_memory_optimization: bool = Field(default=True, env="ENABLE_MEMORY_OPTIMIZATION")
    max_memory_usage_mb: int = Field(default=2048, env="MAX_MEMORY_USAGE_MB", ge=512, le=8192)
    
    class Config:
        env_prefix = "WORKFLOW_"


class MCPSettings(BaseSettings):
    """MCP server configuration settings"""
    
    config_file: str = Field(
        default="config/mcp_config.json",
        env="MCP_SERVERS_CONFIG"
    )
    auto_approve_tools: List[str] = Field(default=[], env="MCP_AUTO_APPROVE_TOOLS")
    connection_timeout: int = Field(default=30, env="MCP_CONNECTION_TIMEOUT", ge=5, le=300)
    request_timeout: int = Field(default=60, env="MCP_REQUEST_TIMEOUT", ge=10, le=600)
    
    @validator('auto_approve_tools', pre=True)
    def parse_auto_approve_tools(cls, v):
        if isinstance(v, str):
            return [tool.strip() for tool in v.split(',') if tool.strip()]
        return v
    
    class Config:
        env_prefix = "MCP_"


class ObservabilitySettings(BaseSettings):
    """Observability configuration settings"""
    
    log_level: LogLevel = Field(default=LogLevel.INFO, env="LOG_LEVEL")
    enable_tracing: bool = Field(default=True, env="ENABLE_TRACING")
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    
    # External Services
    prometheus_url: Optional[AnyHttpUrl] = Field(default=None, env="PROMETHEUS_URL")
    jaeger_endpoint: Optional[AnyHttpUrl] = Field(default=None, env="JAEGER_ENDPOINT")
    
    # Logging Configuration
    log_format: str = Field(default="json", env="LOG_FORMAT")
    log_file: Optional[str] = Field(default=None, env="LOG_FILE")
    log_rotation: str = Field(default="1 day", env="LOG_ROTATION")
    log_retention: str = Field(default="30 days", env="LOG_RETENTION")
    
    class Config:
        env_prefix = "OBSERVABILITY_"


class Settings(BaseSettings):
    """Main application settings with enhanced validation and hot-reloading"""
    
    # Environment
    environment: Environment = Field(default=Environment.DEVELOPMENT, env="ENVIRONMENT")
    
    # Sub-configurations
    database: DatabaseSettings = DatabaseSettings()
    api: APISettings = APISettings()
    security: SecuritySettings = SecuritySettings()
    llm: LLMSettings = LLMSettings()
    workflow: WorkflowSettings = WorkflowSettings()
    mcp: MCPSettings = MCPSettings()
    observability: ObservabilitySettings = ObservabilitySettings()
    
    # Application metadata
    app_name: str = Field(default="Event Planning Agent v2", env="APP_NAME")
    app_version: str = Field(default="2.0.0", env="APP_VERSION")
    
    # File watching for hot reload
    config_watch_enabled: bool = Field(default=True, env="CONFIG_WATCH_ENABLED")
    config_watch_interval: int = Field(default=5, env="CONFIG_WATCH_INTERVAL", ge=1, le=60)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        validate_assignment = True
        
    @root_validator
    def validate_environment_specific_settings(cls, values):
        """Validate settings based on environment"""
        env = values.get('environment')
        
        if env == Environment.PRODUCTION:
            # Production-specific validations
            security = values.get('security', {})
            if isinstance(security, SecuritySettings):
                if security.jwt_secret == "your-secret-key":
                    raise ValueError("JWT secret must be changed in production")
                if not security.auth_enabled:
                    logging.warning("Authentication is disabled in production")
        
        return values
    
    def get_mcp_config(self) -> Dict[str, Any]:
        """Load and validate MCP configuration"""
        config_path = Path(self.mcp.config_file)
        
        if not config_path.exists():
            raise FileNotFoundError(f"MCP config file not found: {config_path}")
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Validate MCP configuration structure
            if 'mcpServers' not in config:
                raise ValueError("MCP config must contain 'mcpServers' key")
            
            return config
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in MCP config file: {e}")
    
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.environment == Environment.DEVELOPMENT
    
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.environment == Environment.PRODUCTION
    
    def get_database_url(self) -> str:
        """Get database URL as string"""
        return str(self.database.url)
    
    def get_cors_origins(self) -> List[str]:
        """Get CORS origins list"""
        return self.api.cors_origins
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary (excluding sensitive data)"""
        data = self.dict()
        
        # Remove sensitive information
        if 'security' in data and 'jwt_secret' in data['security']:
            data['security']['jwt_secret'] = '***REDACTED***'
        
        return data


# Global settings instance with caching
_settings: Optional[Settings] = None
_settings_file_mtime: Optional[float] = None


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    global _settings, _settings_file_mtime
    
    # Check if .env file has been modified
    env_file = Path('.env')
    current_mtime = env_file.stat().st_mtime if env_file.exists() else 0
    
    if _settings is None or (
        _settings_file_mtime is not None and 
        current_mtime > _settings_file_mtime
    ):
        _settings = Settings()
        _settings_file_mtime = current_mtime
        
        # Log configuration reload
        logging.info(f"Configuration loaded/reloaded for environment: {_settings.environment}")
    
    return _settings


def reload_settings() -> Settings:
    """Force reload settings from environment"""
    global _settings, _settings_file_mtime
    
    # Clear cache
    get_settings.cache_clear()
    
    _settings = Settings()
    _settings_file_mtime = Path('.env').stat().st_mtime if Path('.env').exists() else 0
    
    logging.info(f"Configuration forcefully reloaded for environment: {_settings.environment}")
    return _settings


def validate_settings() -> bool:
    """Validate current settings configuration"""
    try:
        settings = get_settings()
        
        # Test database connection string
        from sqlalchemy import create_engine
        engine = create_engine(settings.get_database_url())
        engine.dispose()
        
        # Validate MCP configuration
        settings.get_mcp_config()
        
        logging.info("Settings validation passed")
        return True
        
    except Exception as e:
        logging.error(f"Settings validation failed: {e}")
        return False


# Environment-specific configuration loaders
def load_development_config() -> Settings:
    """Load development-specific configuration"""
    os.environ.setdefault('ENVIRONMENT', 'development')
    os.environ.setdefault('DEBUG', 'true')
    os.environ.setdefault('LOG_LEVEL', 'DEBUG')
    os.environ.setdefault('API_RELOAD', 'true')
    return get_settings()


def load_production_config() -> Settings:
    """Load production-specific configuration"""
    os.environ.setdefault('ENVIRONMENT', 'production')
    os.environ.setdefault('DEBUG', 'false')
    os.environ.setdefault('LOG_LEVEL', 'INFO')
    os.environ.setdefault('API_RELOAD', 'false')
    os.environ.setdefault('API_WORKERS', '4')
    return get_settings()