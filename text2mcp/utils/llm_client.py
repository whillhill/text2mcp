"""
LLM client factory module, for creating and managing OpenAI compatible LLM clients
"""
import logging
from typing import Any, Optional

from text2mcp.utils.config import LLMConfig

logger = logging.getLogger(__name__)

class LLMClientFactory:
    """
    LLM client factory class, for creating and managing OpenAI compatible LLM clients
    """
    
    @staticmethod
    def create_client(config: LLMConfig) -> Optional[Any]:
        """
        Create an LLM client instance based on configuration
        
        Args:
            config: LLM configuration object
            
        Returns:
            Any LLM client instance, or None if creation fails
        """
        if not config.api_key:
            logger.warning("Missing API key, cannot initialize LLM client")
            return None
            
        try:
            # Import standard OpenAI client or compatible client
            try:
                from openai import OpenAI
                
                # Create client parameters
                client_args = {"api_key": config.api_key}
                
                # If base_url is provided, add it to parameters
                if config.base_url:
                    client_args["base_url"] = config.base_url
                    logger.info(f"Using custom base URL: {config.base_url}")
                
                # Create OpenAI client
                client = OpenAI(**client_args)
                logger.info(f"Successfully initialized OpenAI {'compatible' if config.base_url else ''} client")
                return client
            except ImportError:
                logger.error("Cannot import openai module, please install: pip install openai")
                return None
                
        except Exception as e:
            logger.error(f"Error initializing LLM client: {e}", exc_info=True)
            return None 
