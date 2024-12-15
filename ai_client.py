import logging
from typing import Dict, Any, Optional
import anthropic
import openai

logger = logging.getLogger(__name__)

class AIClient:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.current_provider = config.get('ai_models', {}).get('default', {}).get('provider', 'anthropic')
        self.current_model = config.get('ai_models', {}).get('default', {}).get('model', 'claude-3-sonnet-20240229')
        
        # Initialize clients
        self.anthropic_client = anthropic.Anthropic()
        self.openai_client = openai.OpenAI()
        
    def switch_model(self, provider: str, model: str) -> bool:
        """Switch the active AI model"""
        providers = self.config.get('ai_models', {}).get('providers', {})
        
        if provider not in providers:
            logger.error(f"Invalid provider: {provider}")
            return False
            
        provider_models = providers[provider].get('models', {})
        if not any(m.get('name') == model for m in provider_models.get('model', [])):
            logger.error(f"Invalid model: {model}")
            return False
            
        self.current_provider = provider
        self.current_model = model
        logger.info(f"Switched to {provider} model {model}")
        return True

    async def generate_text(self, prompt: str, max_tokens: Optional[int] = None) -> str:
        """Generate text using the current AI model"""
        try:
            if self.current_provider == 'anthropic':
                return self._generate_anthropic(prompt, max_tokens)
            elif self.current_provider == 'openai':
                return await self._generate_openai(prompt, max_tokens)
            else:
                raise ValueError(f"Unsupported provider: {self.current_provider}")
        except Exception as e:
            logger.error(f"Text generation failed: {str(e)}")
            raise

    def _generate_anthropic(self, prompt: str, max_tokens: Optional[int] = None) -> str:
        """Generate text using Anthropic's API"""
        if max_tokens is None:
            max_tokens = self.config.get('ai_models', {}).get('providers', {}).get('anthropic', {}).get('models', {}).get('model', [])[0].get('capabilities', {}).get('text_generation', {}).get('max_tokens', 4096)

        try:
            response = self.anthropic_client.messages.create(
                model=self.current_model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Anthropic API error: {str(e)}")
            raise

    async def _generate_openai(self, prompt: str, max_tokens: Optional[int] = None) -> str:
        """Generate text using OpenAI's API"""
        if max_tokens is None:
            max_tokens = self.config.get('ai_models', {}).get('providers', {}).get('openai', {}).get('models', {}).get('model', [])[0].get('capabilities', {}).get('text_generation', {}).get('max_tokens', 4096)

        try:
            response = await self.openai_client.chat.completions.create(
                model=self.current_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise
