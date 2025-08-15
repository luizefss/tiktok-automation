# Gemini TTS Service - Ultra Humanizado para TikTok
import os
import asyncio
import logging
import tempfile
import uuid
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime

try:
    import google.generativeai as genai
except ImportError:
    genai = None

logger = logging.getLogger(__name__)

class GeminiTTSService:
    def __init__(self):
        self.client = None
        self.media_dir = Path("/var/www/tiktok-automation/media/audio")
        self.media_dir.mkdir(parents=True, exist_ok=True)
        
        # Inicializar Gemini TTS
        from config_manager import get_config
        config = get_config()
        
        if genai and config.GEMINI_API_KEY:
            try:
                genai.configure(api_key=config.GEMINI_API_KEY)
                # Usar modelo TTS específico
                self.model = genai.GenerativeModel("gemini-2.5-pro-preview-tts")
                logger.info("Gemini TTS Ultra-Humanizado inicializado com sucesso")
                self.client = True
            except Exception as e:
                logger.warning(f"Falha ao inicializar Gemini TTS: {e}")
                self.client = None
        else:
            logger.warning("Gemini API Key nao encontrada - TTS nao disponivel")
            self.client = None

    async def generate_humanized_audio(
        self,
        text: str,
        voice_profile: str = "male-professional",
        emotion: str = "neutral",
        pitch: float = 0.0,
        speed: float = 1.0,
        volume_gain: float = 0.0,
        accent: str = "pt-BR"
    ) -> Dict[str, Any]:
        """Gera audio ultra-humanizado com o Gemini TTS"""
        
        try:
            logger.info(f"Gerando audio humanizado - Perfil: {voice_profile}, Emocao: {emotion}")
            
            if not self.client:
                logger.warning("Gemini TTS nao disponivel, usando fallback")
                return await self._generate_fallback_audio(text)
            
            # Usar otimizador profissional de roteiros
            from script_optimizer import ScriptOptimizer
            optimizer = ScriptOptimizer()
            
            # Otimizar texto para fala natural
            script_data = {'roteiro_completo': text}
            optimized_script = optimizer.optimize_for_speech(script_data)
            processed_text = optimized_script['roteiro_completo']
            
            # Auto-detectar emoção se não foi especificada ou é neutral
            if emotion == "neutral":
                detected_emotion = optimizer.analyze_emotion_from_content(text)
                if detected_emotion != "neutral":
                    emotion = detected_emotion
                    logger.info(f"Emocao auto-detectada: {emotion}")
            
            # Aplicar processamento adicional específico para TTS
            processed_text = self._apply_tts_specific_processing(processed_text, emotion)
            
            # Configurar instruções específicas para humanização
            tts_instructions = self._build_humanization_instructions(
                voice_profile, emotion, pitch, speed, accent
            )
            
            # Gerar audio com Gemini TTS
            return await self._generate_with_gemini_tts(
                processed_text, tts_instructions, voice_profile, emotion
            )
            
        except Exception as e:
            logger.error(f"Erro na geracao de audio humanizado: {e}")
            return {
                "success": False,
                "error": str(e),
                "audio_path": None
            }

    def _apply_tts_specific_processing(self, text: str, emotion: str) -> str:
        """Aplica processamento específico para TTS baseado na emoção"""
        
        # Ajustes específicos por emoção para o Gemini TTS
        if emotion == "dramatic":
            # Adicionar pausas dramáticas e ênfases
            text = text.replace(".", "... <break time=\"1.2s\"/>")
            text = text.replace("!", "! <break time=\"1s\"/>")
            
        elif emotion == "mysterious":
            # Tom mais baixo e pausas longas
            text = f'<prosody rate="0.9" pitch="-2st">{text}</prosody>'
            text = text.replace("...", "... <break time=\"2s\"/>")
            
        elif emotion == "enthusiastic":
            # Velocidade e energia aumentadas
            text = f'<prosody rate="1.2" pitch="+1st" volume="+3dB">{text}</prosody>'
            text = text.replace("!", "! <break time=\"0.3s\"/>")
            
        elif emotion == "suspenseful":
            # Pausas tensas e ritmo lento
            text = f'<prosody rate="0.8" pitch="-1st">{text}</prosody>'
            text = text.replace(".", ". <break time=\"1.5s\"/>")
            
        return text

    def _optimize_text_for_speech(self, text: str, emotion: str, voice_profile: str) -> str:
        """Otimiza texto para leitura mais natural e humanizada"""
        
        # Remover marcações de tempo antigas se existirem
        text = text.replace("[VOZ:", "").replace("[PAUSA:", "").replace("[Ênfase:", "")
        
        # Limpar formatação desnecessária
        text = text.replace("→", "").replace("■", "").replace("●", "")
        
        # Adicionar pausas naturais
        if emotion == "dramatic":
            # Para dramático: pausas longas e ênfases
            text = text.replace(".", "... <break time=\"1s\"/>")
            text = text.replace("!", "! <break time=\"0.8s\"/>")
            text = text.replace("?", "? <break time=\"0.7s\"/>")
            
        elif emotion == "mysterious":
            # Para misterioso: pausas sussurrantes
            text = text.replace(".", ". <break time=\"0.5s\"/>")
            text = text.replace("...", "... <break time=\"1.5s\"/>")
            
        elif emotion == "enthusiastic":
            # Para entusiasmado: ritmo mais rápido com pausas curtas
            text = text.replace(".", ". <break time=\"0.3s\"/>")
            text = text.replace("!", "! <break time=\"0.4s\"/>")
            
        elif emotion == "suspenseful":
            # Para suspense: pausas tensas
            text = text.replace(".", "... <break time=\"2s\"/>")
            text = text.replace("!", "! <break time=\"1.5s\"/>")
            
        else:  # neutral
            # Pausas naturais normais
            text = text.replace(".", ". <break time=\"0.5s\"/>")
            text = text.replace(",", ", <break time=\"0.3s\"/>")
        
        # Adicionar ênfases em palavras-chave
        emphasis_words = [
            "incrível", "fantástico", "inacreditável", "impressionante",
            "secreto", "mistério", "revelação", "descoberta",
            "nunca", "sempre", "jamais", "impossível"
        ]
        
        for word in emphasis_words:
            text = text.replace(word, f'<emphasis level="strong">{word}</emphasis>')
            
        return text

    def _build_humanization_instructions(
        self, 
        voice_profile: str, 
        emotion: str, 
        pitch: float, 
        speed: float, 
        accent: str
    ) -> str:
        """Constrói instruções específicas para humanização da voz"""
        
        instructions = []
        
        # Perfil de voz
        if "male" in voice_profile:
            if "professional" in voice_profile:
                instructions.append("Use uma voz masculina profissional, autoritativa e confiante")
            elif "youthful" in voice_profile:
                instructions.append("Use uma voz masculina jovem, energética e moderna")
            elif "mature" in voice_profile:
                instructions.append("Use uma voz masculina madura, experiente e sábia")
            elif "casual" in voice_profile:
                instructions.append("Use uma voz masculina casual, amigável e descontraída")
            elif "dramatic" in voice_profile:
                instructions.append("Use uma voz masculina dramática, intensa e emocional")
        else:  # female
            if "warm" in voice_profile:
                instructions.append("Use uma voz feminina calorosa, acolhedora e maternal")
            elif "professional" in voice_profile:
                instructions.append("Use uma voz feminina executiva, direta e competente")
            elif "energetic" in voice_profile:
                instructions.append("Use uma voz feminina energética, vibrante e motivadora")
            elif "storyteller" in voice_profile:
                instructions.append("Use uma voz feminina narradora, envolvente para histórias")
            elif "youthful" in voice_profile:
                instructions.append("Use uma voz feminina jovem, fresca e moderna")
        
        # Emoção específica
        emotion_instructions = {
            "dramatic": "Fale de forma dramática com pausas teatrais e intensidade emocional",
            "mysterious": "Use tom misterioso, sussurrante e enigmático",
            "enthusiastic": "Seja extremamente animado, energético e empolgante",
            "calm": "Mantenha tom calmo, tranquilo e relaxante",
            "suspenseful": "Crie suspense com pausas tensas e tom grave",
            "happy": "Use tom alegre, otimista e sorridente",
            "sad": "Fale com melancolia e emotividade",
            "angry": "Use tom intenso, firme e expressivo"
        }
        
        if emotion in emotion_instructions:
            instructions.append(emotion_instructions[emotion])
        
        # Sotaque/Regionalismo
        if accent == "pt-BR":
            instructions.append("Use sotaque brasileiro natural e coloquial")
        elif accent == "pt-PT":
            instructions.append("Use sotaque português de Portugal")
        elif accent == "en-US":
            instructions.append("Fale em inglês americano")
        elif accent == "es-ES":
            instructions.append("Fale em espanhol")
        
        # Ajustes de velocidade e tom
        if speed > 1.1:
            instructions.append("Fale mais rápido que o normal")
        elif speed < 0.9:
            instructions.append("Fale mais devagar, de forma pausada")
            
        if pitch > 2:
            instructions.append("Use um tom de voz mais agudo")
        elif pitch < -2:
            instructions.append("Use um tom de voz mais grave")
        
        # Instruções de naturalidade
        instructions.extend([
            "Seja extremamente natural e humano na fala",
            "Adicione variações sutis no tom e ritmo",
            "Use respiração natural entre as frases",
            "Evite robôs - seja autêntico e expressivo",
            "Adapte a entonação ao conteúdo do texto"
        ])
        
        return ". ".join(instructions) + "."

    async def _generate_with_gemini_tts(
        self,
        processed_text: str,
        instructions: str,
        voice_profile: str,
        emotion: str
    ) -> Dict[str, Any]:
        """Gera áudio usando Gemini TTS com instruções de humanização"""
        
        try:
            # Prompt completo para o Gemini TTS
            full_prompt = f"""
INSTRUÇÕES DE VOZ: {instructions}

TEXTO PARA NARRAÇÃO:
{processed_text}

Gere um áudio natural, humanizado e expressivo seguindo exatamente as instruções de voz fornecidas.
"""
            
            logger.info("Enviando para Gemini TTS...")
            
            # Configurar para resposta de áudio (obrigatório para modelos TTS)
            generation_config = genai.GenerationConfig(
                response_modalities=["AUDIO"],
                temperature=0.7
            )
            
            # Gerar áudio com o modelo TTS
            response = await asyncio.to_thread(
                self.model.generate_content,
                full_prompt,
                generation_config=generation_config
            )
            
            # O Gemini TTS retorna dados de áudio
            if hasattr(response, 'audio_data') or hasattr(response, 'audio'):
                # Salvar arquivo de áudio
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"gemini_tts_{timestamp}.mp3"
                audio_path = self.media_dir / filename
                
                # Extrair dados de áudio
                audio_data = getattr(response, 'audio_data', None) or getattr(response, 'audio', None)
                
                if audio_data:
                    with open(audio_path, "wb") as f:
                        f.write(audio_data)
                    
                    logger.info(f"Audio Gemini TTS gerado: {filename}")
                    
                    return {
                        "success": True,
                        "audio_path": str(audio_path),
                        "audio_url": f"/media/audio/{filename}",
                        "duration": await self._estimate_duration(processed_text),
                        "message": "Audio ultra-humanizado gerado com Gemini TTS"
                    }
                else:
                    raise Exception("Nenhum dados de audio retornados pelo Gemini")
            else:
                # Se não retornar áudio, usar fallback
                logger.warning("Gemini nao retornou audio, usando fallback")
                return await self._generate_fallback_audio(processed_text)
                
        except Exception as e:
            logger.error(f"Erro no Gemini TTS: {e}")
            return await self._generate_fallback_audio(processed_text)

    async def _estimate_duration(self, text: str) -> float:
        """Estima duração do áudio baseado no texto"""
        # Média de 150 palavras por minuto para fala natural
        words = len(text.split())
        duration = (words / 150) * 60  # em segundos
        return max(5.0, duration)  # mínimo de 5 segundos

    async def _generate_fallback_audio(self, text: str) -> Dict[str, Any]:
        """Usa Google Cloud TTS humanizado como fallback"""
        
        try:
            logger.info("Usando Google Cloud TTS humanizado como fallback")
            
            # Importar o serviço Google TTS aprimorado
            from services.tts_service_enhanced import EnhancedTTSService
            google_tts = EnhancedTTSService()
            
            # Usar Google TTS com configurações humanizadas
            result = await google_tts.generate_audio(
                text=text,
                voice_profile="male-mature",
                emotion="enthusiastic",
                pitch=0.0,
                speed=1.0,
                volume_gain=0.0,
                accent="pt-BR"
            )
            
            if result.get('success'):
                # Renomear para indicar fallback humanizado
                original_path = result.get('audio_path')
                if original_path and os.path.exists(original_path):
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    new_filename = f"humanized_fallback_{timestamp}.mp3"
                    new_path = self.media_dir / new_filename
                    
                    import shutil
                    shutil.copy2(original_path, new_path)
                    
                    # Remover arquivo original para evitar duplicação
                    try:
                        os.remove(original_path)
                    except:
                        pass
                    
                    result['audio_path'] = str(new_path)
                    result['audio_url'] = f"/media/audio/{new_filename}"
                    result['message'] = "Audio humanizado gerado com Google Cloud TTS"
                
                return result
            else:
                return {
                    "success": False,
                    "error": "TTS não disponível no momento",
                    "audio_path": None
                }
            
        except Exception as e:
            logger.error(f"Erro no fallback humanizado: {e}")
            return {
                "success": False,
                "error": str(e),
                "audio_path": None
            }

    def get_voice_test_text(self, emotion: str = "neutral") -> str:
        """Retorna texto de teste otimizado para cada emoção"""
        
        test_texts = {
            "neutral": "Esta é uma demonstração da sua nova voz selecionada. Como você pode ouvir, o som está claro e natural.",
            "dramatic": "Prepare-se... porque o que você está prestes a ouvir... mudará TUDO para sempre!",
            "mysterious": "Existem segredos... que o mundo não quer que você descubra. Mas hoje... você descobrirá a verdade.",
            "enthusiastic": "UAU! Esta configuração vai deixar o seu conteúdo ABSOLUTAMENTE incrível e super envolvente!",
            "calm": "Respire fundo e relaxe. Esta voz suave e tranquila transmite uma sensação de paz completa.",
            "suspenseful": "Algo está acontecendo... Você consegue sentir? A tensão está crescendo... devagar...",
            "happy": "Que alegria fantástica! Esta voz soa super animada e vai contagiar todos que ouvirem!",
            "sad": "Às vezes... a vida nos ensina lições difíceis... mas sempre há esperança no amanhã.",
            "angry": "Chega! Não aceite mais isso! É hora de tomar uma atitude e mudar tudo agora!"
        }
        
        return test_texts.get(emotion, test_texts["neutral"])