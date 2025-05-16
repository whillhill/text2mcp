"""
Configuration management module, used to load and manage Text2MCP configurations
"""
import os
import logging
import toml
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Default configuration values
DEFAULT_CONFIG = {
    "heartbeat_interval": 60,  # Heartbeat check interval (seconds)
    "heartbeat_timeout": 180,  # Heartbeat timeout (seconds)
    "http_timeout": 10,        # HTTP timeout (seconds)
    "reconnection_interval": 60, # Reconnection interval (seconds)
}

# Default configuration file path
USER_CONFIG_DIR = os.path.expanduser("~/.text2mcp")
DEFAULT_CONFIG_FILE = os.path.join(USER_CONFIG_DIR, "config.toml")

@dataclass
class LLMConfig:
    """LLM configuration class"""
    api_key: str
    model: str
    base_url: Optional[str] = None  # Not required for standard OpenAI, needed for compatible mode

def load_llm_config_from_env() -> Optional[LLMConfig]:
    """
    Load LLM configuration from environment variables
    
    Returns:
        Optional[LLMConfig]: Configuration object if API key exists in environment variables, otherwise None
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None
        
    logger.info("Loading OpenAI configuration from environment variables")
    return LLMConfig(
        api_key=api_key,
        model=os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo"),
        base_url=os.environ.get("OPENAI_BASE_URL")
    )

def load_llm_config_from_toml(toml_config: Dict[str, Any]) -> Optional[LLMConfig]:
    """
    Load LLM settings from TOML configuration dictionary
    
    Args:
        toml_config: Dictionary containing configuration
        
    Returns:
        Optional[LLMConfig]: Configuration object if LLM configuration is found, otherwise None
    """
    # Try to load configuration from tool.llm
    llm_config = toml_config.get("tool", {}).get("llm", {})
    if not llm_config or not llm_config.get("api_key"):
        return None
        
    logger.info("Loading OpenAI configuration from configuration file")
    return LLMConfig(
        api_key=llm_config.get("api_key", ""),
        model=llm_config.get("model", "gpt-3.5-turbo"),
        base_url=llm_config.get("base_url")
    )

def load_timing_config(toml_config: Dict[str, Any], default_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Load timing settings configuration
    
    Args:
        toml_config: TOML configuration dictionary
        default_config: Default configuration dictionary
        
    Returns:
        Dict[str, Any]: Updated configuration dictionary
    """
    timing_config = toml_config.get("tool", {}).get("timing", {})
    if not timing_config:
        return default_config
        
    logger.info("Loading timing settings from configuration file")
    config = default_config.copy()
    config["heartbeat_interval"] = timing_config.get("heartbeat_interval_seconds", 
                                                    config["heartbeat_interval"])
    config["heartbeat_timeout"] = timing_config.get("heartbeat_timeout_seconds", 
                                                  config["heartbeat_timeout"])
    config["http_timeout"] = timing_config.get("http_timeout_seconds", 
                                              config["http_timeout"])
    config["reconnection_interval"] = timing_config.get("reconnection_interval_seconds", 
                                                       config["reconnection_interval"])
    return config

def load_config(config_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Load Text2MCP configuration
    
    Configuration loading priority:
    1. Configuration in environment variables (higher priority)
    2. Configuration in the specified configuration file (lower priority)
    3. Default configuration (if neither of the above exists)
    
    Note: Directly passed parameters have the highest priority, but are handled in the CodeGenerator class
    
    Args:
        config_file: Optional configuration file path
        
    Returns:
        Dict[str, Any]: Configuration dictionary
    """
    # Set default configuration
    config_data = DEFAULT_CONFIG.copy()
    llm_config = None
    
    # First try to load LLM configuration from environment variables (higher priority)
    env_llm_config = load_llm_config_from_env()
    if env_llm_config:
        logger.info("Using LLM configuration from environment variables (higher priority)")
        llm_config = env_llm_config
    
    # Then try to load from specified configuration file (as backup or supplement)
    if config_file and os.path.exists(config_file):
        try:
            logger.info(f"Attempting to load configuration from specified file: {config_file}")
            with open(config_file, "r", encoding="utf-8") as f:
                toml_config = toml.load(f)
                
            # If there is no LLM configuration in environment variables, try to load from configuration file
            if not llm_config:
                file_llm_config = load_llm_config_from_toml(toml_config)
                if file_llm_config:
                    llm_config = file_llm_config
                
            # Load timing settings (these settings are not in environment variables)
            config_data = load_timing_config(toml_config, config_data)
        except Exception as e:
            logger.error(f"Error loading configuration file {config_file}: {e}", exc_info=True)
    elif config_file:
        logger.warning(f"Specified configuration file {config_file} does not exist")
    
    # Set LLM configuration (if found)
    if llm_config:
        config_data["llm_config"] = llm_config
    
    logger.debug(f"Final loaded configuration: {config_data}")
    return config_data

def ensure_config_dir():
    """Ensure configuration directory exists"""
    if not os.path.exists(USER_CONFIG_DIR):
        try:
            os.makedirs(USER_CONFIG_DIR)
            logger.info(f"Created configuration directory: {USER_CONFIG_DIR}")
        except OSError as e:
            logger.error(f"Cannot create configuration directory {USER_CONFIG_DIR}: {e}")
            raise

def save_config(config: Dict[str, Any], config_file: Optional[str] = None):
    """
    Save configuration to file
    
    Args:
        config: Configuration dictionary to save
        config_file: Optional configuration file path, defaults to ~/.text2mcp/config.toml
    """
    if not config_file:
        ensure_config_dir()
        config_file = DEFAULT_CONFIG_FILE
    
    # Ensure target directory exists
    target_dir = os.path.dirname(os.path.abspath(config_file))
    if not os.path.exists(target_dir):
        try:
            os.makedirs(target_dir)
            logger.info(f"Created directory: {target_dir}")
        except OSError as e:
            logger.error(f"Cannot create directory {target_dir}: {e}")
            raise
    
    try:
        # Get LLM configuration, or use empty values if it doesn't exist
        llm_config = config.get("llm_config")
        if not llm_config:
            logger.warning("LLM configuration not found when saving configuration")
            return
            
        # Convert configuration to TOML format
        config_toml = {
            "tool": {
                "llm": {
                    "api_key": llm_config.api_key,
                    "model": llm_config.model
                },
                "timing": {
                    "heartbeat_interval_seconds": config.get("heartbeat_interval", DEFAULT_CONFIG["heartbeat_interval"]),
                    "heartbeat_timeout_seconds": config.get("heartbeat_timeout", DEFAULT_CONFIG["heartbeat_timeout"]),
                    "http_timeout_seconds": config.get("http_timeout", DEFAULT_CONFIG["http_timeout"]),
                    "reconnection_interval_seconds": config.get("reconnection_interval", DEFAULT_CONFIG["reconnection_interval"])
                }
            }
        }
        
        # Always save base_url field, even if it is None
        config_toml["tool"]["llm"]["base_url"] = llm_config.base_url
        
        # Save to file
        with open(config_file, "w", encoding="utf-8") as f:
            toml.dump(config_toml, f)
        
        logger.info(f"Configuration saved to: {config_file}")
    except Exception as e:
        logger.error(f"Error saving configuration to {config_file}: {e}", exc_info=True)
        raise 
