# /var/www/tiktok-automation/backend/services/claude_service.py

import os
import json
import logging
import asyncio
from typing import Dict, Any, Optional
import anthropic
from dotenv import load_dotenv
from config_manager import get_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

config = get_config()


class ClaudeService:
    def __init__(self):
        self.client = self._initialize_claude()
        # Modelos atualizados para refletir as versões mais recentes
        self.available_models = [
            "claude-3-5-sonnet-20240620",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
        ]

    def _initialize_claude(self) -> Optional[anthropic.AsyncAnthropic]:
        """Inicializa conexão com Claude API usando a chave do ConfigManager"""
        claude_api_key = config.CLAUDE_API_KEY

        logger.info(
            f"🔍 Tentando inicializar Claude com key: {claude_api_key[:10] if claude_api_key else 'None'}...")

        if claude_api_key:
            try:
                client = anthropic.AsyncAnthropic(api_key=claude_api_key)
                logger.info("✅ Conectado ao Claude API")
                return client
            except Exception as e:
                logger.error(f"❌ Erro ao conectar Claude API: {e}")

        logger.warning("⚠️ Claude API Key não encontrada")
        return None

    async def generate_script(self, prompt: str, model: str = None) -> Optional[str]:
        """Gera roteiro usando Claude"""
        if not self.client:
            logger.error("❌ Cliente Claude não inicializado")
            return None

        # Usa o modelo mais avançado se nenhum for especificado
        if not model:
            model = self.available_models[0]

        try:
            message = await self.client.messages.create(
                model=model,
                max_tokens=2000,
                temperature=0.7,
                system="Responda APENAS com um único JSON válido. Sem markdown, sem backticks, sem comentários.",
                messages=[{"role": "user", "content": prompt}]
            )

            if message and message.content:
                content = message.content[0].text if isinstance(
                    message.content, list) else message.content
                logger.info(
                    f"✅ Roteiro gerado com sucesso pelo Claude ({model})")
                return content

        except Exception as e:
            logger.error(f"❌ Erro ao gerar roteiro com Claude: {e}")

        return None

    async def check_availability(self, model: str = None) -> bool:
        """Verifica se um modelo específico está disponível"""
        if not self.client:
            return False

        if not model:
            model = self.available_models[0]

        try:
            # Tenta uma chamada de teste
            await self.client.messages.create(
                model=model,
                max_tokens=10,
                messages=[{"role": "user", "content": "test"}]
            )
            return True
        except Exception:
            return False


# Instância global do serviço
claude_service = ClaudeService()
