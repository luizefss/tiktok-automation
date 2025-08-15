#!/usr/bin/env python3

import os
import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime

from services.optimized_tts_service import OptimizedTTSService
from services.gemini_tts_service import GeminiTTSService
from config_manager import get_config

logger = logging.getLogger(__name__)
config = get_config()


class EnhancedTTSService:
    """
    Serviço TTS aprimorado que oferece:
    - Geração automática inteligente
    - Controles manuais pós-geração
    - Múltiplas versões do Gemini (Flash/Pro)
    - Ajustes finos de parâmetros
    """
    
    def __init__(self):
        self.optimized_service = OptimizedTTSService()
        self.gemini_service = GeminiTTSService()
        self.audio_dir = "/var/www/tiktok-automation/media/audio"
        os.makedirs(self.audio_dir, exist_ok=True)
        
        # Modelos Gemini disponíveis
        self.gemini_models = {
            "flash": "gemini-2.5-flash-preview-tts",
            "pro": "gemini-2.5-pro-preview-tts"
        }
        
        # Configurações padrão para ajustes manuais
        self.manual_configs = {
            "google_neural2_male": {
                "voice_name": "pt-BR-Neural2-B",
                "gender": "male",
                "rate": 1.0,
                "pitch": 0.0,
                "volume": 1.0
            },
            "google_neural2_female": {
                "voice_name": "pt-BR-Neural2-A",
                "gender": "female", 
                "rate": 1.0,
                "pitch": 0.0,
                "volume": 1.0
            },
            "google_standard_male": {
                "voice_name": "pt-BR-Standard-B",
                "gender": "male",
                "rate": 1.0,
                "pitch": 0.0,
                "volume": 1.0
            }
        }
        
        logger.info("✅ Enhanced TTS Service inicializado")
    
    async def generate_auto_optimized(self, text: str) -> Dict[str, Any]:
        """Gera áudio automaticamente otimizado (como já funciona)"""
        return await self.optimized_service.generate_optimized_audio(text=text)
    
    async def generate_with_manual_controls(self, text: str, config: Dict[str, Any], ssml: Optional[str] = None) -> Dict[str, Any]:
        """
        Gera áudio com controles manuais
        
        Args:
            text: Texto para síntese
            config: Configurações manuais {
                "service": "google" | "gemini_flash" | "gemini_pro",
                "voice": "neural2_male" | "neural2_female" | "standard_male",
                "rate": 0.5-2.0,
                "pitch": -10.0 a 10.0,
                "volume": -5.0 a 5.0,
                "emotion": "neutral" | "enthusiastic" | "dramatic" etc.
            }
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            service_type = config.get("service", "google")
            
            logger.info(f"🎤 Gerando áudio manual - Serviço: {service_type}")
            
            if service_type.startswith("gemini"):
                return await self._generate_gemini_manual(text, config, timestamp)
            else:
                return await self._generate_google_manual(text, config, timestamp)
                
        except Exception as e:
            logger.error(f"❌ Erro na geração manual: {e}")
            return {
                "success": False,
                "error": f"Erro na geração manual: {str(e)}"
            }
    
    async def _generate_gemini_manual(self, text: str, config: Dict[str, Any], timestamp: str) -> Dict[str, Any]:
        """Gera áudio usando Gemini com controles manuais"""
        try:
            service_type = config.get("service", "gemini_flash")
            model = self.gemini_models.get(service_type.replace("gemini_", ""), "gemini-2.5-flash-preview-tts")
            
            # Configurar parâmetros do Gemini
            gemini_config = {
                "model": model,
                "voice_profile": config.get("voice", "male-professional"),
                "emotion": config.get("emotion", "neutral"),
                "rate": config.get("rate", 1.0),
                "pitch": config.get("pitch", 0.0),
                "volume": config.get("volume", 1.0)
            }
            
            logger.info(f"🤖 Usando Gemini {model}")
            
            # Usar o serviço Gemini existente
            result = await self.gemini_service.generate_tts_audio(
                text=text,
                voice_profile=gemini_config["voice_profile"],
                emotion=gemini_config["emotion"],
                pitch=gemini_config["pitch"],
                speed=gemini_config["rate"],
                volume_gain=gemini_config["volume"]
            )
            
            if result.get("success"):
                # Renomear arquivo para incluir modelo
                original_path = result.get("file_path")
                if original_path and os.path.exists(original_path):
                    new_filename = f"enhanced_{model.replace('-', '_')}_{timestamp}.mp3"
                    new_path = os.path.join(self.audio_dir, new_filename)
                    
                    import shutil
                    shutil.copy2(original_path, new_path)
                    
                    return {
                        "success": True,
                        "audio_url": f"/media/audio/{new_filename}",
                        "file_path": new_path,
                        "duration": result.get("duration", 0),
                        "service": service_type,
                        "model": model,
                        "config": gemini_config,
                        "message": f"Áudio gerado com {model}"
                    }
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Erro no Gemini manual: {e}")
            return {"success": False, "error": str(e)}
    
    async def _generate_google_manual(self, text: str, config: Dict[str, Any], timestamp: str) -> Dict[str, Any]:
        """Gera áudio usando Google Cloud TTS com controles manuais"""
        try:
            voice_type = config.get("voice", "neural2_male")
            voice_config = self.manual_configs.get(f"google_{voice_type}", self.manual_configs["google_neural2_male"])
            
            # Aplicar ajustes manuais
            voice_config = voice_config.copy()
            voice_config["rate"] = config.get("rate", 1.0)
            voice_config["pitch"] = config.get("pitch", 0.0) 
            voice_config["volume"] = config.get("volume", 1.0)
            
            logger.info(f"🎙️ Usando Google {voice_config['voice_name']}")
            
            # Usar o método interno para gerar com configuração manual
            result = await self._generate_google_tts_with_config(
                text=text,
                voice_config=voice_config
            )
            
            if result.get("success"):
                # Renomear arquivo para incluir configuração
                original_path = result.get("file_path")
                if original_path and os.path.exists(original_path):
                    new_filename = f"enhanced_google_{voice_type}_{timestamp}.mp3"
                    new_path = os.path.join(self.audio_dir, new_filename)
                    
                    import shutil
                    shutil.copy2(original_path, new_path)
                    
                    return {
                        "success": True,
                        "audio_url": f"/media/audio/{new_filename}",
                        "file_path": new_path,
                        "duration": result.get("duration", 0),
                        "service": "google",
                        "voice": voice_config["voice_name"],
                        "config": voice_config,
                        "message": f"Áudio gerado com {voice_config['voice_name']}"
                    }
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Erro no Google manual: {e}")
            return {"success": False, "error": str(e)}
    
    async def _generate_google_tts_with_config(self, text: str, voice_config: Dict) -> Dict[str, Any]:
        """Método auxiliar para gerar Google TTS com config específica"""
        try:
            from google.cloud import texttospeech
            import io
            
            if not hasattr(self.optimized_service, 'client') or not self.optimized_service.client:
                return {"success": False, "error": "Google Cloud TTS não disponível"}
            
            # Criar SSML otimizado
            rate_percent = int((voice_config["rate"] - 1.0) * 100)
            pitch_hz = voice_config["pitch"] * 50  # Converter para Hz
            
            ssml_text = f"""
            <speak>
                <prosody rate="{rate_percent:+d}%" pitch="{pitch_hz:+.1f}Hz" volume="+{voice_config['volume']:.1f}dB">
                    {text}
                </prosody>
            </speak>
            """.strip()
            
            # Configurar síntese
            synthesis_input = texttospeech.SynthesisInput(ssml=ssml_text)
            voice = texttospeech.VoiceSelectionParams(
                language_code="pt-BR",
                name=voice_config["voice_name"]
            )
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                effects_profile_id=["telephony-class-application"],
                speaking_rate=voice_config["rate"],
                pitch=voice_config["pitch"],
                volume_gain_db=voice_config["volume"]
            )
            
            # Executar síntese
            response = self.optimized_service.client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            # Salvar arquivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"google_manual_{timestamp}.mp3"
            file_path = os.path.join(self.audio_dir, filename)
            
            with open(file_path, "wb") as out:
                out.write(response.audio_content)
            
            # Calcular duração estimada
            # Estimativa baseada em velocidade média de fala em português brasileiro
            words = len(text.split())
            chars = len(text)
            # Aproximadamente 2.5 palavras por segundo ou 150 palavras por minuto
            duration = max(words / 2.5, chars / 12.0)  # Usar o maior entre os dois métodos
            
            file_size = os.path.getsize(file_path)
            
            return {
                "success": True,
                "file_path": file_path,
                "audio_url": f"/media/audio/{filename}",
                "duration": duration,
                "file_size": file_size
            }
            
        except Exception as e:
            logger.error(f"❌ Erro na síntese manual Google: {e}")
            return {"success": False, "error": str(e)}