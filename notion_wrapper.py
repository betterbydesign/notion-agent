import logging
from typing import Dict, Any, List
from notion_client.client import Client
import time

logger = logging.getLogger(__name__)

class NotionClient:
    def __init__(self, token: str, config: Dict[str, Any]):
        self.client = Client(auth=token)
        self.config = config
        self.supported_blocks = self._get_supported_blocks()
        
    def _get_supported_blocks(self) -> List[str]:
        """Get list of supported block types from config"""
        block_config = self.config.get('block_support', {}).get('supported_types', {})
        return [block.get('@type') for block in block_config.get('block', [])]

    def _implement_retry(self, func, *args, **kwargs):
        """Implement retry logic for API calls"""
        retry_config = self.config.get('error_handling', {}).get('retry_policy', {})
        max_attempts = retry_config.get('max_attempts', 3)
        initial_backoff = retry_config.get('initial_backoff_seconds', 1.0)
        backoff_multiplier = retry_config.get('backoff_multiplier', 2.0)
        
        attempt = 0
        while attempt < max_attempts:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                attempt += 1
                if attempt == max_attempts:
                    raise
                
                wait_time = initial_backoff * (backoff_multiplier ** (attempt - 1))
                logger.warning(f"API call failed, retrying in {wait_time} seconds. Error: {str(e)}")
                time.sleep(wait_time)

    def get_block(self, block_id: str) -> Dict[str, Any]:
        """Get a block from Notion"""
        return self._implement_retry(self.client.blocks.retrieve, block_id)

    def update_block(self, block_id: str, **kwargs) -> Dict[str, Any]:
        """Update a block in Notion"""
        return self._implement_retry(self.client.blocks.update, block_id, **kwargs)

    def create_block(self, parent_id: str, **kwargs) -> Dict[str, Any]:
        """Create a new block in Notion"""
        return self._implement_retry(self.client.blocks.children.append, parent_id, **kwargs)

    def delete_block(self, block_id: str) -> Dict[str, Any]:
        """Delete a block from Notion"""
        return self._implement_retry(self.client.blocks.delete, block_id)

    def is_supported_block(self, block_type: str) -> bool:
        """Check if a block type is supported"""
        return block_type in self.supported_blocks
