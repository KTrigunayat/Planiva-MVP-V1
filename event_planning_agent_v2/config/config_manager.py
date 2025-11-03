"""
Configuration management utilities with hot-reloading and validation
"""

import json
import logging
import asyncio
import os
from pathlib import Path
from typing import Dict, Any, Optional, Callable
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pydantic import ValidationError

from .settings import Settings, get_settings, reload_settings


logger = logging.getLogger(__name__)


class ConfigFileHandler(FileSystemEventHandler):
    """File system event handler for configuration file changes"""
    
    def __init__(self, callback: Callable[[], None]):
        self.callback = callback
        self.last_modified = {}
    
    def on_modified(self, event):
        """Handle file modification events"""
        if event.is_directory:
            return
        
        file_path = event.src_path
        
        # Only process .env, .json config files
        if not (file_path.endswith('.env') or file_path.endswith('.json')):
            return
        
        # Debounce rapid file changes
        current_time = os.path.getmtime(file_path)
        if file_path in self.last_modified:
            if current_time - self.last_modified[file_path] < 1.0:  # 1 second debounce
                return
        
        self.last_modified[file_path] = current_time
        
        logger.info(f"Configuration file changed: {file_path}")
        
        try:
            self.callback()
        except Exception as e:
            logger.error(f"Error reloading configuration: {e}")


class ConfigManager:
    """Configuration manager with hot-reloading and validation"""
    
    def __init__(self):
        self.settings: Optional[Settings] = None
        self.observer: Optional[Observer] = None
        self.reload_callbacks: list[Callable[[Settings], None]] = []
        self._watch_enabled = False
    
    def initialize(self, watch_enabled: bool = True) -> Settings:
        """Initialize configuration manager"""
        self.settings = get_settings()
        self._watch_enabled = watch_enabled and self.settings.config_watch_enabled
        
        if self._watch_enabled:
            self._start_file_watcher()
        
        logger.info(f"Configuration manager initialized (watch_enabled={self._watch_enabled})")
        return self.settings
    
    def get_settings(self) -> Settings:
        """Get current settings"""
        if self.settings is None:
            self.settings = get_settings()
        return self.settings
    
    def reload_configuration(self) -> bool:
        """Reload configuration from files"""
        try:
            old_settings = self.settings
            self.settings = reload_settings()
            
            # Validate new settings
            if not self._validate_settings(self.settings):
                logger.error("New configuration validation failed, keeping old settings")
                self.settings = old_settings
                return False
            
            # Notify callbacks
            for callback in self.reload_callbacks:
                try:
                    callback(self.settings)
                except Exception as e:
                    logger.error(f"Error in reload callback: {e}")
            
            logger.info("Configuration reloaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reload configuration: {e}")
            return False
    
    def add_reload_callback(self, callback: Callable[[Settings], None]):
        """Add callback to be called when configuration is reloaded"""
        self.reload_callbacks.append(callback)
    
    def remove_reload_callback(self, callback: Callable[[Settings], None]):
        """Remove reload callback"""
        if callback in self.reload_callbacks:
            self.reload_callbacks.remove(callback)
    
    def _start_file_watcher(self):
        """Start file system watcher for configuration files"""
        if self.observer is not None:
            return
        
        handler = ConfigFileHandler(self.reload_configuration)
        self.observer = Observer()
        
        # Watch current directory for .env files
        self.observer.schedule(handler, ".", recursive=False)
        
        # Watch config directory for JSON files
        config_dir = Path("config")
        if config_dir.exists():
            self.observer.schedule(handler, str(config_dir), recursive=False)
        
        self.observer.start()
        logger.info("Configuration file watcher started")
    
    def _stop_file_watcher(self):
        """Stop file system watcher"""
        if self.observer is not None:
            self.observer.stop()
            self.observer.join()
            self.observer = None
            logger.info("Configuration file watcher stopped")
    
    def _validate_settings(self, settings: Settings) -> bool:
        """Validate settings configuration"""
        try:
            # Test database URL format
            if not settings.get_database_url():
                logger.error("Invalid database URL")
                return False
            
            # Validate MCP configuration
            mcp_config = settings.get_mcp_config()
            if not self._validate_mcp_config(mcp_config):
                return False
            
            # Environment-specific validations
            if settings.is_production():
                if settings.security.jwt_secret == "your-secret-key":
                    logger.error("JWT secret must be changed in production")
                    return False
            
            return True
            
        except ValidationError as e:
            logger.error(f"Settings validation error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected validation error: {e}")
            return False
    
    def _validate_mcp_config(self, config: Dict[str, Any]) -> bool:
        """Validate MCP server configuration"""
        try:
            if 'mcpServers' not in config:
                logger.error("MCP config missing 'mcpServers' section")
                return False
            
            servers = config['mcpServers']
            required_servers = ['vendor-data-server', 'calculation-server', 'monitoring-server']
            
            for server_name in required_servers:
                if server_name not in servers:
                    logger.error(f"MCP config missing required server: {server_name}")
                    return False
                
                server_config = servers[server_name]
                
                # Validate required fields
                required_fields = ['command', 'args', 'env']
                for field in required_fields:
                    if field not in server_config:
                        logger.error(f"MCP server {server_name} missing required field: {field}")
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"MCP config validation error: {e}")
            return False
    
    def get_environment_config_file(self, base_name: str) -> str:
        """Get environment-specific config file path"""
        settings = self.get_settings()
        env = settings.environment.value
        
        # Try environment-specific file first
        env_file = f"{base_name}.{env}.json"
        if Path(env_file).exists():
            return env_file
        
        # Fall back to base file
        base_file = f"{base_name}.json"
        if Path(base_file).exists():
            return base_file
        
        raise FileNotFoundError(f"No configuration file found for {base_name}")
    
    def load_mcp_config(self) -> Dict[str, Any]:
        """Load MCP configuration with environment-specific overrides"""
        try:
            config_file = self.get_environment_config_file("config/mcp_config")
            
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            # Substitute environment variables
            config_str = json.dumps(config)
            for key, value in os.environ.items():
                config_str = config_str.replace(f"${{{key}}}", value)
                config_str = config_str.replace(f"${{{key}:-", f"${{{key}:-").replace(f"}}", "}")
            
            # Handle default values in environment variable substitution
            import re
            def replace_env_vars(match):
                var_name = match.group(1)
                default_value = match.group(2) if match.group(2) else ""
                return os.environ.get(var_name, default_value)
            
            config_str = re.sub(r'\$\{([^}:]+)(?::-([^}]*))?\}', replace_env_vars, config_str)
            
            return json.loads(config_str)
            
        except Exception as e:
            logger.error(f"Failed to load MCP configuration: {e}")
            raise
    
    def shutdown(self):
        """Shutdown configuration manager"""
        self._stop_file_watcher()
        self.reload_callbacks.clear()
        logger.info("Configuration manager shutdown")


# Global configuration manager instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """Get global configuration manager instance"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def initialize_config(watch_enabled: bool = True) -> Settings:
    """Initialize global configuration"""
    manager = get_config_manager()
    return manager.initialize(watch_enabled)


async def async_config_reload_handler():
    """Async handler for configuration reloads"""
    manager = get_config_manager()
    
    while True:
        try:
            await asyncio.sleep(manager.get_settings().config_watch_interval)
            
            # Check if any config files have been modified
            # This is handled by the file watcher, so we just sleep
            
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in async config reload handler: {e}")
            await asyncio.sleep(5)  # Wait before retrying


def validate_configuration() -> bool:
    """Validate current configuration"""
    try:
        manager = get_config_manager()
        settings = manager.get_settings()
        return manager._validate_settings(settings)
    except Exception as e:
        logger.error(f"Configuration validation failed: {e}")
        return False


def get_mcp_config() -> Dict[str, Any]:
    """Get MCP configuration with environment substitution"""
    manager = get_config_manager()
    return manager.load_mcp_config()