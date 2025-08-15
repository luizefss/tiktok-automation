# Enhanced TTS Service for TikTok Content Generation
import os
import asyncio
import logging
import re
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import tempfile

try:
    from google.cloud import texttospeech
except ImportError:
    texttospeech = None
    
try:
    import pydub
    from pydub import AudioSegment
except ImportError:
    pydub = None
    AudioSegment = None

logger = logging.getLogger(__name__)

class EnhancedTTSService:
    def __init__(self):
        self.client = None
        self.media_dir = Path("/var/www/tiktok-automation/media/audio")
        self.media_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize Google Cloud TTS if available
        if texttospeech and os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
            try:
                self.client = texttospeech.TextToSpeechClient()
                logger.info("Google Cloud TTS inicializado com sucesso")
            except Exception as e:
                logger.warning(f"Falha ao inicializar Google TTS: {e}")
        else:
            logger.warning("Google Cloud TTS nao disponivel - usando fallback")

    async def generate_audio(
        self,
        text: str,
        voice_profile: str = "male-mature",
        emotion: str = "neutral",
        pitch: float = 0.0,
        speed: float = 1.0,
        volume_gain: float = 0.0,
        accent: str = "pt-BR"
    ) -> Dict[str, Any]:
        """Gera audio TTS com configuracoes avancadas"""
        
        try:
            logger.info(f"Gerando audio TTS - Perfil: {voice_profile}, Emocao: {emotion}")
            
            if self.client and texttospeech:
                return await self._generate_google_tts(
                    text, voice_profile, emotion, pitch, speed, volume_gain, accent
                )
            else:
                return await self._generate_fallback_audio(text)
                
        except Exception as e:
            logger.error(f"Erro na geracao TTS: {e}")
            return {
                "success": False,
                "error": str(e),
                "audio_path": None
            }

    async def _generate_google_tts(
        self,
        text: str,
        voice_profile: str,
        emotion: str,
        pitch: float,
        speed: float,
        volume_gain: float,
        accent: str
    ) -> Dict[str, Any]:
        """Gera audio usando Google Cloud TTS"""
        
        try:
            # Mapear perfis de voz para configuracoes do Google TTS
            voice_config = self._get_google_voice_config(voice_profile, accent)
            
            # Aplicar otimizações SSML para humanização
            ssml_text = self._create_humanized_ssml(text, emotion, voice_profile)
            
            # Configurar parametros de sintese com SSML
            synthesis_input = texttospeech.SynthesisInput(ssml=ssml_text)
            
            voice = texttospeech.VoiceSelectionParams(
                language_code=voice_config["language_code"],
                name=voice_config["name"],
                ssml_gender=voice_config["gender"]
            )
            
            # Configurar parametros de audio com base na emocao e configuracoes
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=max(0.25, min(4.0, speed)),  # Google aceita 0.25 a 4.0
                pitch=max(-20.0, min(20.0, pitch)),        # Google aceita -20 a 20
                volume_gain_db=max(-96.0, min(16.0, volume_gain))  # Google aceita -96 a 16
            )
            
            # Fazer a sintese
            logger.info(f"Executando sintese TTS...")
            response = await asyncio.to_thread(
                self.client.synthesize_speech,
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            # Salvar arquivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"tts_audio_{timestamp}.mp3"
            audio_path = self.media_dir / filename
            
            with open(audio_path, "wb") as out:
                out.write(response.audio_content)
            
            # Aplicar pos-processamento se necessario
            if AudioSegment and (emotion != "neutral" or volume_gain != 0):
                audio_path = await self._post_process_audio(
                    audio_path, emotion, volume_gain
                )
            
            logger.info(f"Audio TTS gerado: {filename}")
            
            return {
                "success": True,
                "audio_path": str(audio_path),
                "audio_url": f"/media/audio/{filename}",
                "duration": await self._get_audio_duration(audio_path),
                "message": "Audio gerado com sucesso"
            }
            
        except Exception as e:
            logger.error(f"Erro na sintese Google TTS: {e}")
            return {
                "success": False,
                "error": f"Erro na sintese TTS: {str(e)}",
                "audio_path": None
            }

    def _get_google_voice_config(self, voice_profile: str, accent: str) -> Dict[str, Any]:
        """Mapeia perfis de voz para configuracoes humanizadas do Google TTS"""
        
        # Mapeamento de idiomas
        language_map = {
            "pt-BR": "pt-BR",
            "pt-PT": "pt-PT", 
            "en-US": "en-US",
            "es-ES": "es-ES"
        }
        
        language_code = language_map.get(accent, "pt-BR")
        
        # Usar vozes mais humanizadas do Google TTS
        if "male" in voice_profile:
            if language_code == "pt-BR":
                # Testar diferentes vozes masculinas humanizadas
                if "mature" in voice_profile:
                    # Tom de meia-idade: Neural2-B com gênero masculino
                    return {
                        "language_code": "pt-BR",
                        "name": "pt-BR-Neural2-B",
                        "gender": texttospeech.SsmlVoiceGender.MALE
                    }
                if "professional" in voice_profile:
                    return {
                        "language_code": "pt-BR",
                        "name": "pt-BR-Neural2-B",  # Neural2 é mais humanizada
                        "gender": texttospeech.SsmlVoiceGender.MALE
                    }
                elif "youthful" in voice_profile:
                    return {
                        "language_code": "pt-BR", 
                        "name": "pt-BR-Wavenet-B",
                        "gender": texttospeech.SsmlVoiceGender.MALE
                    }
                else:
                    # Fallback ainda prefere Neural2-B para manter naturalidade
                    return {
                        "language_code": "pt-BR",
                        "name": "pt-BR-Neural2-B",
                        "gender": texttospeech.SsmlVoiceGender.MALE
                    }
            elif language_code == "en-US":
                return {
                    "language_code": "en-US", 
                    "name": "en-US-Neural2-D",  # Neural2 humanizada
                    "gender": texttospeech.SsmlVoiceGender.MALE
                }
        else:  # female voices
            if language_code == "pt-BR":
                if "warm" in voice_profile or "energetic" in voice_profile:
                    return {
                        "language_code": "pt-BR",
                        "name": "pt-BR-Neural2-A",  # Neural2 feminina humanizada
                        "gender": texttospeech.SsmlVoiceGender.FEMALE
                    }
                elif "professional" in voice_profile:
                    return {
                        "language_code": "pt-BR",
                        "name": "pt-BR-Wavenet-A", 
                        "gender": texttospeech.SsmlVoiceGender.FEMALE
                    }
                else:
                    return {
                        "language_code": "pt-BR",
                        "name": "pt-BR-Standard-A",  # Fallback padrão
                        "gender": texttospeech.SsmlVoiceGender.FEMALE
                    }
            elif language_code == "en-US":
                return {
                    "language_code": "en-US",
                    "name": "en-US-Neural2-F",  # Neural2 humanizada
                    "gender": texttospeech.SsmlVoiceGender.FEMALE
                }
        
        # Fallback para portugues brasileiro masculino humanizado
        return {
            "language_code": "pt-BR",
            "name": "pt-BR-Neural2-B", 
            "gender": texttospeech.SsmlVoiceGender.MALE
        }

    def _create_humanized_ssml(self, text: str, emotion: str, voice_profile: str) -> str:
        """Cria SSML humanizado baseado na emoção e perfil de voz"""
        
        # Aplicar otimizações do script optimizer primeiro
        from script_optimizer import ScriptOptimizer
        optimizer = ScriptOptimizer()
        
        script_data = {'roteiro_completo': text}
        optimized = optimizer.optimize_for_speech(script_data)
        clean_text = optimized['roteiro_completo']
        
        # Limpar texto para SSML válido
        clean_text = re.sub(r'[<>&]', '', clean_text)  # Remover caracteres problemáticos
        clean_text = clean_text.replace('"', '&quot;').replace("'", '&apos;')
        
        # Configurações de prosódia simplificadas para Neural2 (valores numéricos)
        prosody_configs = {
            "dramatic": {"rate": "0.8", "pitch": "-2st"},
            "mysterious": {"rate": "0.7", "pitch": "-3st"},
            "enthusiastic": {"rate": "1.2", "pitch": "+2st"},
            "calm": {"rate": "0.9", "pitch": "-1st"},
            "happy": {"rate": "1.1", "pitch": "+1st"},
            "suspenseful": {"rate": "0.7", "pitch": "-2st"},
            "neutral": {"rate": "1.0", "pitch": "0st"},
        }

        cfg = prosody_configs.get(emotion, prosody_configs["neutral"]).copy()

        # Ajustes sutis para tom de meia-idade (mais humano, menos robótico)
        if "mature" in voice_profile:
            try:
                base_rate = float(cfg.get("rate", "1.0"))
            except Exception:
                base_rate = 1.0
            base_rate = max(0.85, min(1.15, base_rate - 0.04))
            pitch_val = cfg.get("pitch", "0st")
            try:
                semitones = float(pitch_val[:-2]) if isinstance(pitch_val, str) and pitch_val.endswith("st") else 0.0
            except Exception:
                semitones = 0.0
            semitones = max(-4.0, min(4.0, semitones - 0.5))
            cfg = {"rate": f"{base_rate}", "pitch": f"{semitones:+.0f}st"}

        # Inserir pausas naturais curtas entre frases
        def add_natural_breaks(s: str) -> str:
            return re.sub(r"\s*([\.!?])\s+", r"\1 <break time=\"180ms\"/> ", s)

        clean_text = add_natural_breaks(clean_text)

        # Criar SSML válido e simples para Neural2
        ssml_content = (
            f"<speak>\n"
            f"  <prosody rate=\"{cfg['rate']}\" pitch=\"{cfg['pitch']}\">\n"
            f"    {clean_text}\n"
            f"  </prosody>\n"
            f"</speak>"
        )
        
        return ssml_content

    def _add_emphasis_to_keywords(self, sentence: str) -> str:
        """Adiciona ênfases SSML em palavras-chave"""
        
        # Palavras que merecem ênfase
        emphasis_words = {
            "strong": [
                "incrível", "fantástico", "impressionante", "espetacular",
                "revolucionário", "exclusivo", "segredo", "revelação",
                "nunca", "jamais", "sempre", "impossível", "descoberta"
            ],
            "moderate": [
                "importante", "essencial", "fundamental", "crucial",
                "especial", "único", "diferente", "novo", "melhor"
            ]
        }
        
        result = sentence
        
        # Aplicar ênfases fortes
        for word in emphasis_words["strong"]:
            pattern = rf'\b({word})\b'
            replacement = rf'<emphasis level="strong">\1</emphasis>'
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        
        # Aplicar ênfases moderadas
        for word in emphasis_words["moderate"]:
            pattern = rf'\b({word})\b'
            replacement = rf'<emphasis level="moderate">\1</emphasis>'
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        
        return result

    async def _post_process_audio(
        self, 
        audio_path: Path, 
        emotion: str, 
        volume_gain: float
    ) -> Path:
        """Aplica pos-processamento baseado na emocao"""
        
        if not AudioSegment:
            return audio_path
            
        try:
            audio = AudioSegment.from_mp3(str(audio_path))
            
            # Aplicar modificacoes baseadas na emocao
            if emotion == "dramatic":
                # Adicionar reverb e aumentar contraste dinamico
                audio = audio + 2  # Pequeno boost de volume
            elif emotion == "mysterious": 
                # Reduzir volume e adicionar efeito baixo-passa
                audio = audio - 3
            elif emotion == "enthusiastic":
                # Aumentar volume e brilho
                audio = audio + 3
            elif emotion == "calm":
                # Suavizar e reduzir volume
                audio = audio - 1
                
            # Aplicar ganho de volume final
            if volume_gain != 0:
                audio = audio + volume_gain
                
            # Salvar arquivo processado
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            processed_filename = f"tts_processed_{timestamp}.mp3"
            processed_path = self.media_dir / processed_filename
            
            audio.export(str(processed_path), format="mp3", bitrate="192k")
            
            # Remover arquivo original
            audio_path.unlink()
            
            return processed_path
            
        except Exception as e:
            logger.warning(f"Falha no pos-processamento: {e}")
            return audio_path

    async def _get_audio_duration(self, audio_path: Path) -> float:
        """Obtem duracao do audio em segundos"""
        
        if not AudioSegment:
            return 0.0
            
        try:
            audio = AudioSegment.from_mp3(str(audio_path))
            return len(audio) / 1000.0  # Converter de ms para segundos
        except:
            return 0.0

    async def _generate_fallback_audio(self, text: str) -> Dict[str, Any]:
        """Tenta usar Google TTS primeiro, só cria simulado se impossível"""
        
        try:
            logger.info("Tentando usar Google Cloud TTS como fallback")
            
            # Se Google TTS estiver disponível, usar ele
            if self.client and texttospeech:
                logger.info("Google Cloud TTS disponível, usando-o diretamente")
                return await self._generate_google_tts(
                    text=text,
                    voice_profile="male-mature",
                    emotion="neutral",
                    pitch=0.0,
                    speed=1.0,
                    volume_gain=0.0,
                    accent="pt-BR"
                )
            
            # Se não estiver disponível, avisar claramente
            logger.warning("Google Cloud TTS NÃO CONFIGURADO - sistema TTS offline")
            
            return {
                "success": False,
                "error": "Sistema TTS não configurado. Configure Google Cloud TTS para usar áudio.",
                "audio_path": None,
                "message": "Configure as credenciais do Google Cloud TTS"
            }
            
        except Exception as e:
            logger.error(f"Erro no fallback: {e}")
            return {
                "success": False,
                "error": f"TTS indisponível: {str(e)}",
                "audio_path": None
            }

    def test_voice_preview(
        self, 
        voice_profile: str = "male-professional",
        emotion: str = "neutral"
    ) -> str:
        """Retorna texto de teste otimizado para o perfil e emocao"""
        
        test_texts = {
            "neutral": "Esta é uma demonstracao da voz selecionada com as configuracoes atuais.",
            "dramatic": "Prepare-se... porque o que voce vai ouvir... mudara tudo para sempre!",
            "mysterious": "Ha segredos que o mundo nao quer que voce descubra... ate agora.",
            "enthusiastic": "Incrivel! Esta configuracao vai deixar seu conteudo absolutamente fantastico!",
            "calm": "Respire fundo e ouca esta voz suave e tranquila que transmite paz.",
            "happy": "Que alegria poder mostrar como esta voz pode soar feliz e animada!",
            "suspenseful": "Algo esta prestes a acontecer... voce consegue sentir a tensao no ar?"
        }
        
        return test_texts.get(emotion, test_texts["neutral"])