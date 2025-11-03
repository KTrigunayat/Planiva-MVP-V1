"""
Configuration management for Streamlit GUI
"""
import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for the Streamlit GUI"""
    
    # API Configuration
    API_BASE_URL: str = os.getenv("API_BASE_URL", "http://localhost:8000")
    API_TIMEOUT: int = int(os.getenv("API_TIMEOUT", "30"))
    API_RETRY_ATTEMPTS: int = int(os.getenv("API_RETRY_ATTEMPTS", "3"))
    API_RETRY_DELAY: float = float(os.getenv("API_RETRY_DELAY", "1.0"))
    
    # UI Configuration
    APP_TITLE: str = os.getenv("APP_TITLE", "Event Planning Agent")
    APP_ICON: str = os.getenv("APP_ICON", "🎉")
    THEME_PRIMARY_COLOR: str = os.getenv("THEME_PRIMARY_COLOR", "#1f77b4")
    
    # Feature Flags
    ENABLE_AUTH: bool = os.getenv("ENABLE_AUTH", "false").lower() == "true"
    ENABLE_ANALYTICS: bool = os.getenv("ENABLE_ANALYTICS", "false").lower() == "true"
    ENABLE_OFFLINE_MODE: bool = os.getenv("ENABLE_OFFLINE_MODE", "false").lower() == "true"
    
    # Performance
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "300"))
    MAX_UPLOAD_SIZE: str = os.getenv("MAX_UPLOAD_SIZE", "10MB")
    SESSION_TIMEOUT: int = int(os.getenv("SESSION_TIMEOUT", "3600"))
    
    # Health Check
    HEALTH_CHECK_INTERVAL: int = int(os.getenv("HEALTH_CHECK_INTERVAL", "30"))
    
    @classmethod
    def get_api_url(cls, endpoint: str) -> str:
        """Get full API URL for an endpoint"""
        return f"{cls.API_BASE_URL.rstrip('/')}/{endpoint.lstrip('/')}"
    
    @classmethod
    def is_development(cls) -> bool:
        """Check if running in development mode"""
        return os.getenv("ENVIRONMENT", "development").lower() == "development"
    
    @classmethod
    def get(cls, key: str, default=None):
        """Get configuration value by key"""
        # First try to get from class attributes
        if hasattr(cls, key):
            return getattr(cls, key)
        
        # Then try environment variables
        env_value = os.getenv(key, default)
        
        # Try to convert to appropriate type
        if env_value is not None and isinstance(env_value, str):
            # Try to convert to int
            if env_value.isdigit():
                return int(env_value)
            # Try to convert to float
            try:
                return float(env_value)
            except ValueError:
                pass
            # Try to convert to bool
            if env_value.lower() in ('true', 'false'):
                return env_value.lower() == 'true'
        
        return env_value

# Global config instance
config = Config()