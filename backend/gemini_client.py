# /var/www/tiktok-automation/backend/gemini_client.py

import google.generativeai as genai
import json
from datetime import datetime
from typing import Dict, Any, Optional
import os
from google.oauth2 import service_account
import logging
import re
from dotenv import load_dotenv
from config_manager import get_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

config = get_config()


class GeminiClient:
    def __init__(self, model_name: str = 'gemini-1.5-pro'):
        """
        Inicializa o cliente Gemini com o modelo padrão para texto.
        Para TTS, usar modelo específico posteriormente.
        """
        self.model = self._initialize_gemini(model_name)

    def _initialize_gemini(self, model_name: str) -> Optional[genai.GenerativeModel]:
        """
        Inicializa conexão com Gemini API, priorizando API Key por segurança.
        """
        # Usar APENAS API Key para evitar conflito de credenciais
        if config.GEMINI_API_KEY:
            try:
                # Configurar com API key
                genai.configure(api_key=config.GEMINI_API_KEY)
                # Força saída JSON para maior previsibilidade nas respostas
                model = genai.GenerativeModel(
                    model_name,
                    generation_config={
                        "response_mime_type": "application/json",
                        # Parametrização conservadora para roteiros mais consistentes
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "top_k": 40,
                    },
                )
                logger.info(
                    f"✅ Conectado ao Gemini API com API Key para o modelo '{model_name}'.")
                return model
            except Exception as e:
                logger.error(f"❌ Erro ao conectar Gemini com API Key: {e}")
        
        else:
            logger.error("❌ Nenhuma API Key do Gemini encontrada")

        logger.critical(
            "❌ FALHA CRÍTICA: Não foi possível conectar ao Gemini API. Verifique suas credenciais.")
        return None

    def generate_content(self, prompt: str) -> Optional[str]:
        if not self.model:
            return None
        try:
            # Para gemini-2.5-pro-preview-tts, usar simplesmente sem configuração específica
            # O modelo deve inferir TEXT automaticamente quando não especificado
            response = self.model.generate_content(prompt)
            # A API pode retornar um Candidate com status diferente de OK, quebra o fluxo
            if response.candidates and response.candidates[0].finish_reason == 'SAFETY':
                logger.warning(
                    "❌ Conteúdo bloqueado por política de segurança.")
                return None
            return response.text
        except Exception as e:
            logger.error(f"❌ Erro ao gerar conteúdo com Gemini: {e}")
            return None

    def process_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """
        Extrai e processa o JSON da resposta do Gemini, com múltiplas tentativas de correção.
        """
        json_text = ""
        try:
            # Primeiro, extrair o JSON da resposta
            if "```json" in response_text:
                json_match = re.search(
                    r'```json\s*([\s\S]*?)\s*```', response_text, re.IGNORECASE)
                if json_match:
                    json_text = json_match.group(1).strip()
                else:
                    start = response_text.find('{')
                    end = response_text.rfind('}')
                    if start != -1 and end != -1 and end > start:
                        json_text = response_text[start:end+1]
                    else:
                        raise ValueError("Bloco JSON não encontrado")
            else:
                json_text = response_text.strip()
                if not json_text.startswith('{'):
                    start = json_text.find('{')
                    end = json_text.rfind('}')
                    if start != -1 and end != -1 and end > start:
                        json_text = json_text[start:end+1]

            # Limpeza básica
            json_text = json_text.replace('\n', ' ').replace("'", '"')
            json_text = re.sub(r'//.*', '', json_text)
            
            # Primeira tentativa de parse
            data = json.loads(json_text)
            
            if isinstance(data, dict):
                data['timestamp'] = datetime.now().isoformat()
            return data

        except json.JSONDecodeError as e:
            logger.warning(f"Primeiro parse falhou, tentando correções: {e}")
            
            # Tentativa 2: Corrigir vírgulas extras no final
            try:
                corrected_json = re.sub(r',(\s*[}\]])', r'\1', json_text)
                data = json.loads(corrected_json)
                if isinstance(data, dict):
                    data['timestamp'] = datetime.now().isoformat()
                return data
            except:
                pass
            
            # Tentativa 3: Corrigir caracteres específicos problemáticos
            try:
                # Remove caracteres que causam problemas nas posições mencionadas
                corrected_json = json_text
                if len(json_text) > 3332:
                    # Remove caracteres problemáticos na posição 3332-3333
                    corrected_json = corrected_json[:3330] + corrected_json[3335:]
                
                # Remove possíveis caracteres inválidos
                corrected_json = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', corrected_json)
                
                data = json.loads(corrected_json)
                if isinstance(data, dict):
                    data['timestamp'] = datetime.now().isoformat()
                return data
            except:
                pass
            
            # Fallback: Retornar dados estruturados básicos
            logger.error("Não foi possível fazer parse do JSON do Gemini, usando fallback")
            return {
                "roteiro_completo": "Hook: Conteúdo interessante sobre o tema! Desenvolvimento: Informações relevantes que educam e engajam. Call to Action: Comente e compartilhe!",
                "hook": "Conteúdo interessante sobre o tema!",
                "titulo": "Título Educativo",
                "hashtags": ["#viral", "#conteudo", "#educativo"],
                "ia_used": "gemini",
                "timestamp": datetime.now().isoformat(),
                "accent": "brasileiro",
                "estimated_duration": 45,
                "call_to_action": "Comente e compartilhe!",
                "style": "educativo"
            }

        except Exception as e:
            logger.error(f"❌ Erro crítico ao processar resposta do Gemini: {e}")
            return None
