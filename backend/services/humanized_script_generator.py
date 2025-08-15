#!/usr/bin/env python3

import os
import logging
import json
from typing import Dict, Any, List, Optional
import re
from datetime import datetime

from services.claude_service import ClaudeService
from services.gpt_service import GPTService
from gemini_client import GeminiClient

logger = logging.getLogger(__name__)


class HumanizedScriptGenerator:
    """
    Gerador de roteiros humanizados com:
    - Pausas naturais marcadas
    - Variações de emoção
    - Respiração e ritmo
    - Ênfases específicas
    - Estrutura otimizada para TTS
    """
    
    def __init__(self):
        self.claude_service = ClaudeService()
        self.gpt_service = GPTService()
        self.gemini_client = GeminiClient()
        
        # Marcadores de pausa e emoção para TTS
        self.tts_markers = {
            "pause_short": "... ",      # Pausa curta (0.5s)
            "pause_medium": "...... ",   # Pausa média (1s) 
            "pause_long": "......... ",  # Pausa longa (1.5s)
            "emphasis_start": "[ÊNFASE]",
            "emphasis_end": "[/ÊNFASE]",
            "emotion_excited": "[EMPOLGADO]",
            "emotion_mysterious": "[MISTERIOSO]", 
            "emotion_dramatic": "[DRAMÁTICO]",
            "emotion_calm": "[CALMO]",
            "breath": "[RESPIRAÇÃO]",
            "voice_up": "[VOZ_ALTA]",
            "voice_down": "[VOZ_BAIXA]"
        }
        
        # SSML templates para controle avançado
        self.ssml_templates = {
            "pause_short": '<break time="0.5s"/>',
            "pause_medium": '<break time="1.0s"/>',
            "pause_long": '<break time="1.5s"/>',
            "emphasis_strong": '<emphasis level="strong">{text}</emphasis>',
            "emphasis_moderate": '<emphasis level="moderate">{text}</emphasis>',
            "prosody_fast": '<prosody rate="fast">{text}</prosody>',
            "prosody_slow": '<prosody rate="slow">{text}</prosody>',
            "prosody_high": '<prosody pitch="high">{text}</prosody>',
            "prosody_low": '<prosody pitch="low">{text}</prosody>',
            "volume_loud": '<prosody volume="loud">{text}</prosody>',
            "volume_soft": '<prosody volume="soft">{text}</prosody>'
        }
        
        logger.info("✅ Humanized Script Generator inicializado")
    
    def _get_humanization_prompt(self, topic: str, tone: str, duration: int) -> str:
        """Cria prompt especializado para roteiros humanizados"""
        return f"""
        Você é um especialista em roteiros para TikTok e síntese de voz (TTS). Sua tarefa é criar um roteiro sobre "{topic}" que seja EXTREMAMENTE humanizado e natural para narração.

        CARACTERÍSTICAS OBRIGATÓRIAS:
        
        🎭 EMOCIONALIDADE:
        - Use variações de tom emocional ao longo do roteiro
        - Marque momentos de empolgação, mistério, drama
        - Inclua exclamações naturais e interjeições
        - Varie entre momentos calmos e intensos
        
        ⏸️ PAUSAS E RITMO:
        - Adicione pausas estratégicas usando "..." (curta), "......" (média), "........." (longa)
        - Coloque pausas após revelações importantes
        - Use pausas para criar suspense e respiração
        - Varie o ritmo: rápido em momentos tensos, lento em revelações
        
        🗣️ LINGUAGEM NATURAL:
        - Use contrações ("não é" → "não é mesmo", "você vai" → "cê vai")
        - Inclua expressões brasileiras naturais
        - Use "né?", "sabe?", "olha só", "imagina só"
        - Adicione hesitações naturais: "então... como eu ia dizendo..."
        
        📍 ESTRUTURA TTS:
        - Marque ênfases importantes com [ÊNFASE]palavra importante[/ÊNFASE]
        - Indique mudanças de emoção: [EMPOLGADO], [MISTERIOSO], [DRAMÁTICO], [CALMO]
        - Adicione [RESPIRAÇÃO] em momentos de pausa natural
        - Use [VOZ_ALTA] e [VOZ_BAIXA] para sussurros ou gritos
        
        ⏰ DURAÇÃO: Aproximadamente {duration} segundos
        🎯 TOM: {tone}
        
        EXEMPLO DE FORMATAÇÃO:
        "Olha só gente... [RESPIRAÇÃO] eu vou contar uma coisa que vocês [ÊNFASE]não vão acreditar[/ÊNFASE]!
        
        [MISTERIOSO] Aconteceu algo incrível ontem à noite...... e eu ainda tô tentando processar tudo isso, sabe?
        
        [EMPOLGADO] Imaginem só: [VOZ_ALTA] era duas da manhã [/VOZ_ALTA] quando eu escutei um barulho estranho lá fora......... 
        
        [CALMO] No começo, pensei... 'ah, deve ser só o vento mesmo, né?' [RESPIRAÇÃO] Mas aí..."
        
        IMPORTANTE: Escreva APENAS o roteiro final, sem explicações ou comentários adicionais.
        """
    
    async def generate_humanized_script(self, topic: str, tone: str = "enthusiastic", 
                                      duration: int = 60, ai_model: str = "claude") -> Dict[str, Any]:
        """
        Gera roteiro humanizado otimizado para TTS
        
        Args:
            topic: Tópico/tema do roteiro
            tone: Tom emocional (enthusiastic, mysterious, dramatic, educational)
            duration: Duração estimada em segundos
            ai_model: Modelo de IA (claude, gpt, gemini)
        """
        try:
            logger.info(f"📝 Gerando roteiro humanizado: {topic} ({tone}, {duration}s)")
            
            prompt = self._get_humanization_prompt(topic, tone, duration)
            
            # Escolher serviço de IA
            if ai_model == "claude":
                script_result = await self.claude_service.generate_script(prompt)
                response = {"success": script_result is not None, "content": script_result}
            elif ai_model == "gpt":
                script_result = await self.gpt_service.generate_script(prompt)
                response = {"success": script_result is not None, "content": script_result}
            elif ai_model == "gemini":
                script_result = await self.gemini_client.generate_script(prompt)
                response = {"success": script_result is not None, "content": script_result}
            else:
                return {"success": False, "error": f"Modelo {ai_model} não suportado"}
            
            if response.get("success") and response.get("content"):
                script_content = response["content"].strip()
                
                # Processar e validar o roteiro
                processed_script = self._process_script_markers(script_content)
                analysis = self._analyze_script_quality(processed_script)
                ssml_version = self.convert_to_ssml(script_content)
                
                return {
                    "success": True,
                    "script": script_content,
                    "ssml": ssml_version,
                    "processed_script": processed_script,
                    "analysis": analysis,
                    "ai_model": ai_model,
                    "estimated_duration": self._estimate_duration(script_content),
                    "word_count": len(script_content.split()),
                    "markers_found": self._count_markers(script_content)
                }
            else:
                return {
                    "success": False,
                    "error": response.get("error", "Falha na geração do roteiro")
                }
                
        except Exception as e:
            logger.error(f"❌ Erro na geração humanizada: {e}")
            return {"success": False, "error": f"Erro interno: {str(e)}"}
    
    def _process_script_markers(self, script: str) -> Dict[str, Any]:
        """Processa marcadores TTS para estrutura utilizável"""
        # Identificar segmentos com marcadores
        segments = []
        current_segment = {"text": "", "emotion": "neutral", "pauses": [], "emphasis": []}
        
        # Regex para encontrar marcadores
        marker_pattern = r'\[([A-Z_]+)\]([^[]*?)(?:\[/[A-Z_]+\]|(?=\[)|$)'
        pause_pattern = r'(\.{3,9})'
        
        # Processar texto
        lines = script.split('\n')
        for line in lines:
            if line.strip():
                # Contar pausas
                pauses = re.findall(pause_pattern, line)
                pause_count = {
                    "short": len([p for p in pauses if len(p) == 3]),
                    "medium": len([p for p in pauses if len(p) == 6]),
                    "long": len([p for p in pauses if len(p) == 9])
                }
                
                # Identificar emoções
                emotions = re.findall(r'\[([A-Z]+)\]', line)
                
                segments.append({
                    "text": line.strip(),
                    "pauses": pause_count,
                    "emotions": emotions,
                    "length": len(line.split())
                })
        
        return {
            "segments": segments,
            "total_pauses": sum([sum(s["pauses"].values()) for s in segments]),
            "emotions_used": list(set([e for s in segments for e in s["emotions"]])),
            "total_words": sum([s["length"] for s in segments])
        }
    
    def _analyze_script_quality(self, processed: Dict[str, Any]) -> Dict[str, Any]:
        """Analisa qualidade do roteiro humanizado"""
        total_words = processed["total_words"]
        total_pauses = processed["total_pauses"]
        emotions = processed["emotions_used"]
        
        # Calcular scores
        pause_density = total_pauses / max(total_words, 1) * 100  # Pausas por 100 palavras
        emotion_variety = len(emotions)
        
        # Classificar qualidade
        quality_score = 0
        feedback = []
        
        # Score de pausas (ideal: 5-15 por 100 palavras)
        if 5 <= pause_density <= 15:
            quality_score += 30
            feedback.append("✅ Densidade de pausas ideal")
        elif pause_density < 5:
            quality_score += 15
            feedback.append("⚠️ Poucas pausas - pode soar robótico")
        else:
            quality_score += 10
            feedback.append("⚠️ Muitas pausas - pode ficar lento")
        
        # Score de variedade emocional
        if emotion_variety >= 3:
            quality_score += 30
            feedback.append("✅ Boa variedade emocional")
        elif emotion_variety >= 2:
            quality_score += 20
            feedback.append("✅ Variedade emocional adequada")
        else:
            quality_score += 10
            feedback.append("⚠️ Pouca variedade emocional")
        
        # Score de estrutura
        if total_words >= 50:
            quality_score += 25
            feedback.append("✅ Extensão adequada")
        else:
            quality_score += 15
            feedback.append("⚠️ Roteiro muito curto")
        
        # Score de marcadores TTS
        has_emphasis = any('ÊNFASE' in str(emotions) for emotions in emotions)
        has_voice_control = any(marker in str(emotions) for marker in ['VOZ_ALTA', 'VOZ_BAIXA'] for emotions in [emotions])
        
        if has_emphasis or has_voice_control:
            quality_score += 15
            feedback.append("✅ Marcadores TTS presentes")
        else:
            feedback.append("⚠️ Faltam marcadores TTS específicos")
        
        return {
            "quality_score": min(quality_score, 100),
            "pause_density": round(pause_density, 1),
            "emotion_variety": emotion_variety,
            "feedback": feedback,
            "recommendation": "Excelente" if quality_score >= 80 else "Bom" if quality_score >= 60 else "Needs Improvement"
        }
    
    def _estimate_duration(self, script: str) -> float:
        """Estima duração baseada em palavras e pausas"""
        words = len(script.split())
        
        # Contar pausas
        short_pauses = script.count('...')
        medium_pauses = script.count('......') - script.count('.........')  # Evitar overlap
        long_pauses = script.count('.........')
        
        # Cálculo: ~2.5 palavras/segundo + tempo de pausas
        base_duration = words / 2.5
        pause_time = (short_pauses * 0.5) + (medium_pauses * 1.0) + (long_pauses * 1.5)
        
        return round(base_duration + pause_time, 1)
    
    def _count_markers(self, script: str) -> Dict[str, int]:
        """Conta diferentes tipos de marcadores"""
        markers = {
            "emphasis": script.count('[ÊNFASE]'),
            "emotions": len(re.findall(r'\[(EMPOLGADO|MISTERIOSO|DRAMÁTICO|CALMO)\]', script)),
            "voice_controls": len(re.findall(r'\[(VOZ_ALTA|VOZ_BAIXA)\]', script)),
            "breathing": script.count('[RESPIRAÇÃO]'),
            "short_pauses": script.count('...'),
            "medium_pauses": script.count('......'),
            "long_pauses": script.count('.........')
        }
        
        return markers
    
    def convert_to_ssml(self, script: str) -> str:
        """Converte roteiro humanizado para SSML válido"""
        ssml_script = script
        
        # Converter pausas
        ssml_script = re.sub(r'\.{9}', self.ssml_templates["pause_long"], ssml_script)
        ssml_script = re.sub(r'\.{6}', self.ssml_templates["pause_medium"], ssml_script)  
        ssml_script = re.sub(r'\.{3}', self.ssml_templates["pause_short"], ssml_script)
        
        # Converter ênfases
        ssml_script = re.sub(r'\[ÊNFASE\](.*?)\[/ÊNFASE\]', 
                           lambda m: self.ssml_templates["emphasis_strong"].format(text=m.group(1)), 
                           ssml_script)
        
        # Converter prosódia por emoção
        emotion_mappings = {
            r'\[EMPOLGADO\](.*?)(?=\[|$)': "prosody_fast",
            r'\[MISTERIOSO\](.*?)(?=\[|$)': "prosody_slow", 
            r'\[DRAMÁTICO\](.*?)(?=\[|$)': "prosody_low",
            r'\[CALMO\](.*?)(?=\[|$)': "prosody_slow"
        }
        
        for pattern, template_key in emotion_mappings.items():
            ssml_script = re.sub(pattern, 
                               lambda m: self.ssml_templates[template_key].format(text=m.group(1).strip()), 
                               ssml_script)
        
        # Converter volume
        ssml_script = re.sub(r'\[VOZ_ALTA\](.*?)\[/VOZ_ALTA\]',
                           lambda m: self.ssml_templates["volume_loud"].format(text=m.group(1)),
                           ssml_script)
        ssml_script = re.sub(r'\[VOZ_BAIXA\](.*?)\[/VOZ_BAIXA\]',
                           lambda m: self.ssml_templates["volume_soft"].format(text=m.group(1)),
                           ssml_script)
        
        # Remover marcadores restantes
        ssml_script = re.sub(r'\[RESPIRAÇÃO\]', self.ssml_templates["pause_medium"], ssml_script)
        
        # Envolver em tags SSML
        ssml_output = f"<speak>{ssml_script}</speak>"
        
        return ssml_output