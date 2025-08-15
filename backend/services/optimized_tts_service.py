# Serviço TTS Otimizado - Seleção Automática da Melhor Voz
import os
import asyncio
import logging
import re
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import random

try:
    from google.cloud import texttospeech
except ImportError:
    texttospeech = None

logger = logging.getLogger(__name__)

class OptimizedTTSService:
    def __init__(self):
        self.client = None
        self.media_dir = Path("/var/www/tiktok-automation/media/audio")
        self.media_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize Google Cloud TTS
        if texttospeech and os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
            try:
                self.client = texttospeech.TextToSpeechClient()
                logger.info("✅ Google Cloud TTS inicializado para sistema otimizado")
            except Exception as e:
                logger.warning(f"⚠️ Falha ao inicializar Google TTS: {e}")
        else:
            logger.warning("⚠️ Google Cloud TTS não configurado")

        # Configurações otimizadas baseadas nos testes
        self.voice_profiles = {
            "mystery": {
                "name": "pt-BR-Neural2-B",  # Voz masculina mais grossa
                "pitch": -2.0,  # Tom mais grave
                "speed": 0.9,   # Mais lento e dramático
                "volume": 1.0,
                "description": "Voz grossa e séria para mistérios"
            },
            "tech": {
                "name": "pt-BR-Neural2-C",  # Voz jovem
                "pitch": 0.5,   # Levemente mais agudo
                "speed": 1.2,   # Mais rápido e dinâmico
                "volume": 0.5,
                "description": "Voz jovem e dinâmica para tecnologia"
            },
            "story": {
                "name": "pt-BR-Neural2-A",  # Voz feminina narrativa
                "pitch": 0.0,   # Tom neutro
                "speed": 1.0,   # Velocidade normal
                "volume": 0.0,
                "description": "Voz narrativa e envolvente"
            },
            "tutorial": {
                "name": "pt-BR-Neural2-B",  # Voz masculina clara
                "pitch": 0.5,   # Levemente mais agudo para clareza
                "speed": 1.0,   # Velocidade padrão
                "volume": 0.0,
                "description": "Voz clara e didática para tutoriais"
            },
            "comedy": {
                "name": "pt-BR-Neural2-A",  # Voz feminina expressiva
                "pitch": 1.0,   # Tom mais agudo e animado
                "speed": 1.3,   # Mais rápido e energético
                "volume": 1.0,
                "description": "Voz animada e expressiva para comédia"
            }
        }

        self.best_voices = {
            "male": {
                "neural2": "pt-BR-Neural2-B",
                "wavenet": "pt-BR-Wavenet-B",
                "standard": "pt-BR-Standard-B"
            },
            "female": {
                "neural2": "pt-BR-Neural2-A", 
                "wavenet": "pt-BR-Wavenet-A",
                "standard": "pt-BR-Standard-A"
            }
        }

    def _analyze_content_emotion(self, text: str) -> str:
        """Analisa o texto e detecta a emoção automaticamente"""
        
        text_lower = text.lower()
        
        # Palavras-chave para diferentes emoções
        emotion_keywords = {
            "enthusiastic": ["incrível", "fantástico", "uau", "demais", "massa", "top", "show", "genial", "arrasou"],
            "dramatic": ["nunca", "jamais", "impossível", "chocante", "revelação", "segredo", "oculto", "descoberta"],
            "mysterious": ["mistério", "enigma", "escondido", "sussurro", "sombra", "secreto", "revelar", "ocultar"],
            "calm": ["tranquilo", "calma", "relaxar", "suave", "gentil", "peace", "sereno", "equilibrio"],
            "happy": ["alegria", "feliz", "sorriso", "diversão", "festa", "celebrar", "positivo", "otimista"]
        }
        
        # Contar ocorrências de cada emoção
        emotion_scores = {}
        for emotion, keywords in emotion_keywords.items():
            score = sum(1 for word in keywords if word in text_lower)
            if score > 0:
                emotion_scores[emotion] = score
        
        # Retornar a emoção com maior score
        if emotion_scores:
            return max(emotion_scores, key=emotion_scores.get)
        
        # Análise por pontuação
        if "!" in text and text.count("!") > 1:
            return "enthusiastic"
        elif "?" in text and "..." in text:
            return "mysterious"
        elif "." in text and len(text.split(".")) > 3:
            return "calm"
        
        return "neutral"

    def _choose_optimal_voice(self, content: str) -> Dict[str, Any]:
        """Escolhe automaticamente a melhor voz baseada no conteúdo"""
        
        # Analisar emoção do conteúdo
        detected_emotion = self._analyze_content_emotion(content)
        
        # Baseado no feedback: focar sempre nas vozes masculinas que tiveram melhor qualidade
        # As vozes masculinas (Neural2-B e Standard-B) foram aprovadas pelo usuário
        gender = "male"  # Sempre usar voz masculina conforme preferência do usuário
        
        # Sempre tentar Neural2 primeiro (melhor qualidade)
        voice_name = self.best_voices[gender]["neural2"]
        
        # Configurações mais naturais e menos robóticas
        emotion_configs = {
            "enthusiastic": {
                "rate": 1.08,
                "pitch": 0.5,
                "volume": 1.8
            },
            "dramatic": {
                "rate": 0.92,
                "pitch": -0.3,
                "volume": 1.5
            },
            "mysterious": {
                "rate": 0.88,
                "pitch": -0.8,
                "volume": 0.8
            },
            "calm": {
                "rate": 0.98,
                "pitch": -0.1,
                "volume": 1.2
            },
            "happy": {
                "rate": 1.05,
                "pitch": 0.4,
                "volume": 1.4
            },
            "neutral": {
                "rate": 1.02,
                "pitch": 0.1,
                "volume": 1.3
            },
            "preferred": {  # Tom que você gostou!
                "rate": 1.1,
                "pitch": 0.15,
                "volume": 1.5
            }
        }
        
        config = emotion_configs.get(detected_emotion, emotion_configs["neutral"])
        
        return {
            "voice_name": voice_name,
            "gender": texttospeech.SsmlVoiceGender.MALE if gender == "male" else texttospeech.SsmlVoiceGender.FEMALE,
            "emotion": detected_emotion,
            "rate": config["rate"],
            "pitch": config["pitch"],
            "volume": config["volume"],
            "description": f"{gender.title()} Neural2 - {detected_emotion}"
        }

    def _create_optimized_ssml(self, text: str, voice_config: Dict[str, Any]) -> str:
        """Cria SSML simplificado e compatível"""
        
        # Limpar texto completamente
        clean_text = re.sub(r'[<>&"\'`]', '', text)
        clean_text = re.sub(r'[^\w\s\.,!?áàâãéêíóôõúçüÁÀÂÃÉÊÍÓÔÕÚÇÜ-]', '', clean_text)
        clean_text = clean_text.strip()
        
        # SSML mínimo e seguro para Neural2
        rate_value = max(0.25, min(4.0, voice_config["rate"]))
        pitch_value = max(-20, min(20, voice_config["pitch"]))
        
        ssml = f'''<speak>
<prosody rate="{rate_value}" pitch="{pitch_value:+.0f}st">
{clean_text}
</prosody>
</speak>'''
        
        return ssml

    async def generate_optimized_audio(self, text: str, voice_profile: str = None, custom_speed: float = None) -> Dict[str, Any]:
        """Gera áudio com configurações automaticamente otimizadas ou perfil específico"""
        
        try:
            if voice_profile and voice_profile in self.voice_profiles:
                logger.info(f"� Gerando áudio com perfil: {voice_profile}")
                profile = self.voice_profiles[voice_profile]
                voice_config = {
                    "voice_name": profile["name"],
                    "gender": texttospeech.SsmlVoiceGender.MALE if "B" in profile["name"] or "C" in profile["name"] else texttospeech.SsmlVoiceGender.FEMALE,
                    "emotion": voice_profile,
                    "rate": custom_speed if custom_speed else profile["speed"],
                    "pitch": profile["pitch"],
                    "volume": profile["volume"]
                }
            else:
                logger.info("�🎯 Gerando áudio com seleção automática da melhor voz")
                voice_config = self._choose_optimal_voice(text)
                if custom_speed:
                    voice_config["rate"] = custom_speed
            
            if not self.client:
                return {
                    "success": False,
                    "error": "Google Cloud TTS não configurado",
                    "audio_path": None
                }
            
            # Escolher automaticamente a configuração ótima
            voice_config = self._choose_optimal_voice(text)
            
            logger.info(f"🎤 Voz selecionada: {voice_config['description']}")
            
            # Criar SSML otimizado
            ssml_text = self._create_optimized_ssml(text, voice_config)
            
            # Configurar síntese
            synthesis_input = texttospeech.SynthesisInput(ssml=ssml_text)
            
            voice_params = texttospeech.VoiceSelectionParams(
                language_code="pt-BR",
                name=voice_config["voice_name"],
                ssml_gender=voice_config["gender"]
            )
            
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=max(0.25, min(4.0, voice_config["rate"])),
                pitch=max(-20.0, min(20.0, voice_config["pitch"])),
                volume_gain_db=max(-96.0, min(16.0, voice_config["volume"]))
            )
            
            # Executar síntese
            logger.info("🎙️ Executando síntese TTS otimizada...")
            response = await asyncio.to_thread(
                self.client.synthesize_speech,
                input=synthesis_input,
                voice=voice_params,
                audio_config=audio_config
            )
            
            # Salvar arquivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"optimized_tts_{timestamp}.mp3"
            audio_path = self.media_dir / filename
            
            with open(audio_path, "wb") as f:
                f.write(response.audio_content)
            
            file_size = os.path.getsize(audio_path)
            
            logger.info(f"✅ Áudio otimizado gerado: {filename} ({file_size} bytes)")
            
            return {
                "success": True,
                "audio_path": str(audio_path),
                "audio_url": f"/media/audio/{filename}",
                "duration": self._estimate_duration(text),
                "voice_used": voice_config["description"],
                "emotion_detected": voice_config["emotion"],
                "message": f"Áudio gerado com {voice_config['description']}"
            }
            
        except Exception as e:
            logger.error(f"❌ Erro na síntese otimizada: {e}")
            return {
                "success": False,
                "error": str(e),
                "audio_path": None
            }

    def _estimate_duration(self, text: str) -> float:
        """Estima duração baseada no texto"""
        # Média de 150 palavras por minuto para português brasileiro
        words = len(text.split())
        duration = (words / 150) * 60
        return max(3.0, duration)

    def get_voice_summary(self) -> Dict[str, Any]:
        """Retorna resumo das vozes disponíveis"""
        return {
            "service": "Google Cloud TTS Neural2",
            "quality": "Máxima (Neural2)",
            "languages": ["pt-BR"],
            "voices": {
                "male": "pt-BR-Neural2-B (Masculina profissional)",
                "female": "pt-BR-Neural2-A (Feminina natural)"
            },
            "features": [
                "Seleção automática de voz",
                "Detecção automática de emoção", 
                "Otimização SSML para TikTok",
                "Pausas e ênfases inteligentes"
            ]
        }