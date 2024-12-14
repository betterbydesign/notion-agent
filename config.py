import os
import yaml
import logging
from logging.handlers import RotatingFileHandler
from typing import Dict, Any

class Config:
    def __init__(self, config_path: str = "config.yaml"):
        self.config = self._load_config(config_path)
        self._setup_logging()
        self._validate_env_vars()
    
    def _load_config(self, config_path: str) -> Dict[Any, Any]:
        """Load and parse YAML configuration"""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            raise RuntimeError(f"Failed to load configuration: {str(e)}")

    def _setup_logging(self):
        """Initialize logging system"""
        log_config = self.config.get('logging', {})
        log_dir = os.path.dirname(log_config.get('output', {}).get('file', {}).get('path', 'logs/notion_agent.log'))
        
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # Configure root logger
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)

        # Console handler
        if log_config.get('output', {}).get('console', True):
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

        # File handler
        if log_config.get('output', {}).get('file', {}).get('enabled', True):
            file_config = log_config['output']['file']
            file_handler = RotatingFileHandler(
                file_config['path'],
                maxBytes=file_config['rotation']['max_size_mb'] * 1024 * 1024,
                backupCount=file_config['rotation']['backup_count']
            )
            file_handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    def _validate_env_vars(self):
        """Validate required environment variables"""
        required_vars = [
            'NOTION_WORKSPACE_A_TOKEN',
            'OPENAI_API_KEY',
            'ANTHROPIC_API_KEY'
        ]
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            raise RuntimeError(f"Missing required environment variables: {', '.join(missing_vars)}")

    def get_setting(self, path: str, default: Any = None) -> Any:
        """Get a configuration setting using dot notation"""
        keys = path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key, default)
            else:
                return default
                
        return value
