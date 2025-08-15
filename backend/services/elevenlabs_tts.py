# /var/www/tiktok-automation/backend/services/elevenlabs_tts.py

import os
import logging
import aiohttp
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from config_manager import get_config
import json

logger = logging.getLogger(__name__)
config = get_config()

class ElevenLabsTTS:
    def __init__(self):
        logger.info("🎤 Inicializando ElevenLabs TTS Service...")
        
        self.api_key = config.ELEVEN_API_KEY
        self.base_url = "https://api.elevenlabs.io/v1"
        
        if not self.api_key:
            logger.warning("⚠️ ElevenLabs API Key não encontrada")
            self.enabled = False
        else:
            logger.info("✅ ElevenLabs TTS configurado")
            self.enabled = True
        
        # Vozes pré-configuradas do ElevenLabs
        self.voices = {
            # Vozes masculinas
            "male-professional": {
                "voice_id": "21m00Tcm4TlvDq8ikWAM",  # Rachel (feminina, mas boa para profissional)
                "name": "Professional Male",
                "description": "Voz masculina profissional e clara"
            },
            "male-dramatic": {
                "voice_id": "AZnzlk1XvdvUeBnXmlld",  # Domi (masculina dramática)
                "name": "Dramatic Male", 
                "description": "Voz masculina dramática e envolvente"
            },
            "male-young": {
                "voice_id": "EXAVITQu4vr4xnSDxMaL",  # Bella (feminina jovem)
                "name": "Young Male",
                "description": "Voz masculina jovem e energética"
            },
            # Nova voz solicitada: Victor Power (histórias)
            "victor-power": {
                "voice_id": "YNOujSUmHtgN6anjqXPf",
                "name": "Victor Power",
                "description": "Voz premium para histórias (narrativa forte)"
            },
            # Vozes femininas
            "female-professional": {
                "voice_id": "21m00Tcm4TlvDq8ikWAM",  # Rachel
                "name": "Professional Female",
                "description": "Voz feminina profissional"
            },
            "female-dramatic": {
                "voice_id": "EXAVITQu4vr4xnSDxMaL",  # Bella
                "name": "Dramatic Female",
                "description": "Voz feminina dramática"
            },
            "female-young": {
                "voice_id": "ThT5KcBeYPX3keUQqHPh",  # Dorothy (feminina jovem)
                "name": "Young Female", 
                "description": "Voz feminina jovem e vibrante"
            }
        }
        
        # Alias para compatibilidade com testes
        self.voice_profiles = self.voices
        
        logger.info("✅ ElevenLabs TTS Service inicializado")

    async def generate_audio(
        self, 
        text: str, 
        voice_profile: str = "male-professional",
        voice_settings: Optional[Dict] = None
    ) -> Optional[str]:
        """Gera áudio usando ElevenLabs TTS"""
        
        if not self.enabled:
            logger.error("❌ ElevenLabs TTS não está habilitado")
            return None
            
        try:
            # Limpar o texto (remover tags de direção)
            clean_text = self._clean_text_for_tts(text)
            
            logger.info(f"🎤 Gerando áudio ElevenLabs - Perfil: {voice_profile}")
            logger.info(f"📝 Texto (primeiros 100 chars): {clean_text[:100]}...")
            
            voice_config = self.voices.get(voice_profile, self.voices["male-professional"])
            voice_id = voice_config["voice_id"]
            
            # Configurações padrão de voz
            default_settings = {
                "stability": 0.75,
                "similarity_boost": 0.85,
                "style": 0.20,
                "use_speaker_boost": True
            }
            
            if voice_settings:
                default_settings.update(voice_settings)
            
            # Preparar payload
            payload = {
                "text": clean_text,
                "model_id": "eleven_multilingual_v2",  # Modelo que suporta português
                "voice_settings": default_settings
            }
            
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.api_key
            }
            
            # Fazer requisição para ElevenLabs
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/text-to-speech/{voice_id}"
                
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        # Salvar áudio
                        audio_data = await response.read()
                        
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"elevenlabs_tts_{timestamp}.mp3"
                        file_path = config.AUDIO_DIR / filename
                        
                        with open(file_path, 'wb') as f:
                            f.write(audio_data)
                        
                        logger.info(f"✅ Áudio ElevenLabs gerado: {filename} ({len(audio_data)} bytes)")
                        
                        # Retornar caminho relativo para API
                        return f"/media/audio/{filename}"
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Erro ElevenLabs: {response.status} - {error_text}")
                        return None
                        
        except Exception as e:
            logger.error(f"❌ Erro ao gerar áudio ElevenLabs: {e}")
            return None

    async def get_available_voices(self) -> List[Dict]:
        """Retorna vozes disponíveis do ElevenLabs"""
        
        if not self.enabled:
            return []
            
        try:
            headers = {
                "Accept": "application/json",
                "xi-api-key": self.api_key
            }
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/voices"
                
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Processar vozes retornadas
                        voices = []
                        for voice in data.get("voices", []):
                            voices.append({
                                "voice_id": voice["voice_id"],
                                "name": voice["name"],
                                "category": voice.get("category", "Unknown"),
                                "description": voice.get("description", ""),
                                "preview_url": voice.get("preview_url", ""),
                                "accent": voice.get("labels", {}).get("accent", ""),
                                "age": voice.get("labels", {}).get("age", ""),
                                "gender": voice.get("labels", {}).get("gender", "")
                            })
                        
                        logger.info(f"✅ {len(voices)} vozes ElevenLabs disponíveis")
                        return voices
                    else:
                        logger.error(f"❌ Erro ao buscar vozes: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"❌ Erro ao buscar vozes ElevenLabs: {e}")
            return []

    def get_preconfigured_voices(self) -> List[Dict]:
        """Retorna vozes pré-configuradas"""
        return [
            {
                "id": voice_id,
                "name": voice_data["name"],
                "description": voice_data["description"],
                "type": "elevenlabs"
            }
            for voice_id, voice_data in self.voices.items()
        ]

    def _clean_text_for_tts(self, text: str) -> str:
        """Limpa o texto para TTS, removendo tags de direção"""
        import re
        
        # Remove tags como [GANCHO], [EXPLICAÇÃO], etc.
        cleaned = re.sub(r'\[([^\]]+)\]', '', text)
        
        # Remove espaços múltiplos
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # Remove quebras de linha desnecessárias
        cleaned = cleaned.replace('\n', ' ')
        
        return cleaned.strip()

    async def clone_voice(self, audio_file_path: str, voice_name: str) -> Optional[str]:
        """Clona uma voz a partir de um arquivo de áudio"""
        
        if not self.enabled:
            logger.error("❌ ElevenLabs TTS não está habilitado")
            return None
            
        try:
            logger.info(f"🎭 Clonando voz: {voice_name}")
            
            headers = {
                "Accept": "application/json",
                "xi-api-key": self.api_key
            }
            
            # Preparar arquivo para upload
            with open(audio_file_path, 'rb') as audio_file:
                files = {
                    'files': audio_file,
                }
                data = {
                    'name': voice_name,
                    'description': f'Voz clonada: {voice_name}'
                }
                
                async with aiohttp.ClientSession() as session:
                    url = f"{self.base_url}/voices/add"
                    
                    async with session.post(url, headers=headers, data=data, files=files) as response:
                        if response.status == 200:
                            result = await response.json()
                            voice_id = result.get("voice_id")
                            
                            logger.info(f"✅ Voz clonada com sucesso: {voice_id}")
                            return voice_id
                        else:
                            error_text = await response.text()
                            logger.error(f"❌ Erro ao clonar voz: {response.status} - {error_text}")
                            return None
                            
        except Exception as e:
            logger.error(f"❌ Erro ao clonar voz: {e}")
            return None

    async def get_voice_settings(self, voice_id: str) -> Optional[Dict]:
        """Obtém configurações de uma voz específica"""
        
        if not self.enabled:
            return None
            
        try:
            headers = {
                "Accept": "application/json",
                "xi-api-key": self.api_key
            }
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/voices/{voice_id}/settings"
                
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        settings = await response.json()
                        return settings
                    else:
                        logger.error(f"❌ Erro ao buscar configurações da voz: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"❌ Erro ao buscar configurações da voz: {e}")
            return None
