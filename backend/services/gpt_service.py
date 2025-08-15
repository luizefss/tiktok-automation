# /var/www/tiktok-automation/backend/services/gpt_service.py

import os
import json
import logging
from typing import Dict, Any, Optional
import asyncio
import random
import openai
from dotenv import load_dotenv
from config_manager import get_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

config = get_config()


class GPTService:
    def __init__(self):
        self.client = self._initialize_openai()
        # Modelos de topo da OpenAI
        self.available_models = [
            "gpt-4o",
            "gpt-4-turbo"
        ]

    def _initialize_openai(self) -> Optional[openai.AsyncOpenAI]:
        """Inicializa conexão com OpenAI API usando a chave do ConfigManager"""
        openai_api_key = config.OPENAI_API_KEY

        if openai_api_key:
            try:
                client = openai.AsyncOpenAI(api_key=openai_api_key)
                logger.info("✅ Conectado ao OpenAI API")
                return client
            except Exception as e:
                logger.error(f"❌ Erro ao conectar OpenAI API: {e}")

        logger.warning("⚠️ OpenAI API Key não encontrada")
        return None

    async def generate_script(
        self,
        prompt: str,
        model: Optional[str] = None,
        json_schema: Optional[Dict[str, Any]] = None,
        max_retries: int = 3,
        request_timeout: float = 60.0,
    ) -> Optional[str]:
        """Gera roteiro usando GPT com JSON estrito, retries e fallback de modelo.

        Parâmetros:
        - prompt: texto do usuário já contendo instruções de estrutura desejada.
        - model: modelo preferido (opcional). Se falhar, tenta próximos da lista.
        - json_schema: schema opcional para forçar formato (quando suportado).
        - max_retries: tentativas por modelo antes de trocar de modelo.
        - request_timeout: timeout por requisição em segundos.
        """
        if not self.client:
            logger.error("❌ Cliente OpenAI não inicializado")
            return None

        # Ordenar lista de modelos: preferido primeiro, depois os demais
        model_queue = []
        if model and model in self.available_models:
            model_queue.append(model)
        model_queue += [m for m in self.available_models if m not in model_queue]
        if not model_queue:
            logger.error("❌ Nenhum modelo disponível configurado para OpenAI")
            return None

        last_err: Optional[Exception] = None
        for m in model_queue:
            for attempt in range(max_retries):
                try:
                    # Monta kwargs e força JSON
                    kwargs: Dict[str, Any] = {
                        "model": m,
                        "messages": [
                            {
                                "role": "system",
                                "content": (
                                    "Responda APENAS com um objeto JSON válido (RFC 8259), sem markdown, sem comentários, "
                                    "sem texto fora do JSON. Você é um roteirista especializado em conteúdo viral para redes sociais."
                                ),
                            },
                            {"role": "user", "content": prompt},
                        ],
                        "max_tokens": 2000,
                        "temperature": 0.7,
                    }

                    # response_format: prioriza schema quando fornecido
                    try:
                        if json_schema:
                            kwargs["response_format"] = {
                                "type": "json_schema",
                                "json_schema": {
                                    "name": "response",
                                    "schema": json_schema,
                                    "strict": True,
                                },
                            }
                        else:
                            kwargs["response_format"] = {"type": "json_object"}
                    except Exception:
                        # Alguns modelos/SDKs podem não suportar, segue sem explicitamente
                        pass

                    # Timeout por tentativa
                    coro = self.client.chat.completions.create(**kwargs)
                    response = await asyncio.wait_for(coro, timeout=request_timeout)

                    if response and getattr(response, "choices", None):
                        content = response.choices[0].message.content
                        logger.info(f"✅ GPT gerou roteiro com sucesso | modelo={m} tentativa={attempt+1}")
                        return content

                    # Se não veio escolha, considera erro controlado para retry
                    raise RuntimeError("Resposta da OpenAI sem choices")

                except Exception as e:
                    last_err = e
                    backoff = min(4.0, (2 ** attempt) * 0.5) + random.random() * 0.2
                    logger.warning(
                        f"⚠️ Falha GPT (modelo={m}, tentativa={attempt+1}/{max_retries}): {e}. Retry em {backoff:.1f}s"
                    )
                    await asyncio.sleep(backoff)

            # Troca de modelo após esgotar tentativas
            logger.info(f"🔁 Trocando de modelo GPT após {max_retries} tentativas: {m} → próximo")

        logger.error(f"❌ Falha ao gerar roteiro com GPT após {len(model_queue) * max_retries} tentativas: {last_err}")
        return None

    async def check_availability(self, model: str = None) -> bool:
        """Verifica se um modelo específico está disponível"""
        if not self.client:
            return False

        if not model:
            model = self.available_models[0]

        try:
            await self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5
            )
            return True
        except Exception:
            return False


# Instância global do serviço
gpt_service = GPTService()
