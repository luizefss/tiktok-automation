"""
Sistema de Otimização de Prompts Visuais para TikTok Automation
Converte roteiros narrativos em prompts visuais otimizados para Image 3.
"""

import logging
import re
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from gemini_client import GeminiClient

logger = logging.getLogger(__name__)

@dataclass
class VisualSegment:
    """Representa um segmento visual com timing específico"""
    start_time: float
    end_time: float
    text: str
    duration: float
    visual_prompt: Optional[str] = None

class VisualPromptOptimizer:
    """
    Sistema principal para otimização de prompts visuais.
    """
    
    def __init__(self):
        """Inicializa o otimizador com configurações e conexões AI"""
        try:
            self.gemini_client = GeminiClient()
            logger.info("✅ Visual Prompt Optimizer inicializado com Gemini")
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar Gemini client: {e}")
            self.gemini_client = None
        
        # Configuração de categorias de conteúdo
        self.content_categories = {
            "construção": {
                "subjects": ["máquinas", "operários", "materiais", "equipamentos", "estruturas"],
                "environments": ["canteiro de obras", "edifício em construção", "fábrica", "oficina"],
                "actions": ["construindo", "soldando", "operando", "montando", "erguendo"]
            },
            "tecnologia": {
                "subjects": ["computadores", "smartphones", "robôs", "drones", "dispositivos"],
                "environments": ["laboratório", "escritório moderno", "centro de dados", "fábrica tech"],
                "actions": ["digitando", "programando", "testando", "inovando", "conectando"]
            },
            "motivacional": {
                "subjects": ["pessoas determinadas", "símbolos de sucesso", "conquistas", "crescimento"],
                "environments": ["ambiente inspirador", "cenário de conquista", "espaço motivacional"],
                "actions": ["alcançando objetivos", "superando obstáculos", "crescendo", "evoluindo"]
            },
            "educacional": {
                "subjects": ["livros", "diagramas", "experimentos", "professores", "estudantes"],
                "environments": ["sala de aula moderna", "laboratório", "biblioteca", "ambiente de aprendizado"],
                "actions": ["ensinando", "aprendendo", "descobrindo", "experimentando", "estudando"]
            }
        }
    
    def segment_script_by_time(self, script_text: str, segment_duration: int = 8) -> List[Dict[str, Any]]:
        """
        Segmenta o roteiro em partes de tempo específico para geração de imagens.
        """
        try:
            # Estimar palavras por segundo (média 2.5 palavras/segundo no português)
            words_per_second = 2.5
            words_per_segment = int(segment_duration * words_per_second)
            
            # Remover marcações de tempo e limpeza
            cleaned_script = re.sub(r'\[\d+:\d+\]', '', script_text)
            cleaned_script = re.sub(r'\s+', ' ', cleaned_script).strip()
            
            # Dividir em palavras
            words = cleaned_script.split()
            segments = []
            
            current_time = 0
            for i in range(0, len(words), words_per_segment):
                segment_words = words[i:i + words_per_segment]
                segment_text = ' '.join(segment_words)
                
                # Calcular duração baseada no número de palavras
                duration = len(segment_words) / words_per_second
                
                segments.append({
                    'text': segment_text,
                    'start_time': current_time,
                    'end_time': current_time + duration,
                    'duration': duration
                })
                
                current_time += duration
            
            logger.info(f"Script segmentado em {len(segments)} partes")
            return segments
            
        except Exception as e:
            logger.error(f"Erro na segmentação do script: {e}")
            return []

    def detect_content_category(self, script_text: str) -> str:
        """
        Detecta automaticamente a categoria do conteúdo baseado no texto.
        """
        script_lower = script_text.lower()
        
        # Palavras-chave por categoria
        keywords = {
            "construção": ["construção", "obras", "concreto", "tijolo", "engenharia", "arquitetura", "edifício", "casa", "prédio", "reforma"],
            "tecnologia": ["tecnologia", "digital", "computador", "software", "app", "internet", "robô", "automação", "inovação", "inteligência artificial"],
            "motivacional": ["sucesso", "motivação", "conquista", "sonho", "objetivo", "vitória", "superação", "crescimento"],
            "educacional": ["educação", "aprender", "ensinar", "conhecimento", "estudo", "ciência", "descoberta", "pesquisa"]
        }
        
        category_scores = {}
        for category, words in keywords.items():
            score = sum(1 for word in words if word in script_lower)
            category_scores[category] = score
        
        # Retorna a categoria com maior score, ou 'geral' se empate
        if category_scores:
            best_category = max(category_scores, key=category_scores.get)
            if category_scores[best_category] > 0:
                return best_category
        
        return "geral"

    def generate_visual_prompt(self, segment_text: str, category: str, visual_style: str = "cinematic") -> str:
        """
        Gera um prompt visual otimizado para um segmento específico do roteiro.
        """
        try:
            # Prompt para o Gemini gerar descrição visual
            optimization_prompt = f"""
TAREFA: Converter este segmento de roteiro em um prompt visual detalhado para Image 3.

SEGMENTO DO ROTEIRO: "{segment_text}"
CATEGORIA: {category}
ESTILO VISUAL: {visual_style}

INSTRUÇÕES:
1. Criar um prompt visual que represente VISUALMENTE o conteúdo do roteiro
2. Focar em elementos visuais concretos (objetos, pessoas, ambientes, ações)
3. Evitar conceitos abstratos - tudo deve ser visualmente representável
4. Incluir detalhes de estilo ({visual_style})
5. Orientação vertical (9:16) para TikTok
6. Alta qualidade e resolução profissional

ELEMENTOS PARA INCLUIR:
- Sujeitos principais (pessoas, objetos, etc.)
- Ambiente/cenário específico  
- Ações visuais claras
- Iluminação e atmosfera
- Composição e enquadramento

RESPOSTA: Forneça APENAS o prompt visual final, sem explicações adicionais.
"""

            # Usar Gemini para otimizar o prompt
            if self.gemini_client:
                response = self.gemini_client.generate_content(optimization_prompt)
                
                if response and hasattr(response, 'text') and response.text:
                    optimized_prompt = response.text.strip()
                    
                    # Adicionar modificadores de estilo específicos
                    if visual_style == "cinematic":
                        optimized_prompt += ", cinematic, dramatic lighting, professional composition"
                    elif visual_style == "realistic":
                        optimized_prompt += ", photorealistic, natural lighting, documentary style"
                    elif visual_style == "artistic":
                        optimized_prompt += ", artistic, creative composition, stylized"
                    elif visual_style == "minimalist":
                        optimized_prompt += ", minimalist, clean composition, simple"
                    
                    # Adicionar especificações técnicas
                    optimized_prompt += ", high quality, professional, 4K resolution, 9:16 vertical aspect ratio"
                    
                    return optimized_prompt
                else:
                    logger.warning("Resposta vazia do Gemini para prompt visual")
                    return self._create_fallback_prompt(segment_text, category, visual_style)
            else:
                return self._create_fallback_prompt(segment_text, category, visual_style)
                
        except Exception as e:
            logger.error(f"Erro na geração de prompt visual com Gemini: {e}")
            return self._create_fallback_prompt(segment_text, category, visual_style)

    def _create_fallback_prompt(self, segment_text: str, category: str, visual_style: str) -> str:
        """
        Cria um prompt visual básico quando a IA não está disponível.
        """
        try:
            # Obter elementos da categoria
            category_data = self.content_categories.get(category, self.content_categories.get("educacional", {}))
            
            subjects = category_data.get("subjects", ["pessoas"])
            environments = category_data.get("environments", ["ambiente moderno"])
            actions = category_data.get("actions", ["trabalhando"])
            
            # Construir prompt básico
            subject = subjects[0] if subjects else "pessoas"
            environment = environments[0] if environments else "ambiente moderno"
            action = actions[0] if actions else "em atividade"
            
            fallback_prompt = f"{subject} {action} em {environment}"
            
            # Adicionar estilo
            if visual_style == "cinematic":
                fallback_prompt += ", cinematic, dramatic lighting, professional composition"
            elif visual_style == "realistic":
                fallback_prompt += ", photorealistic, natural lighting"
            elif visual_style == "artistic":
                fallback_prompt += ", artistic, stylized"
            elif visual_style == "minimalist":
                fallback_prompt += ", minimalist, clean"
            
            # Especificações técnicas
            fallback_prompt += ", high quality, professional, 4K resolution, 9:16 vertical aspect ratio"
            
            return fallback_prompt
            
        except Exception as e:
            logger.error(f"Erro no prompt fallback: {e}")
            return f"high quality professional image, {visual_style} style, 9:16 aspect ratio"

    def optimize_script_for_visuals(
        self, 
        script_text: str = None,
        script_data: Dict[str, Any] = None, 
        visual_style: str = "cinematic",
        content_category: str = "auto_detect",
        target_duration: int = 30,
        segment_duration: int = 8
    ) -> List[Dict[str, Any]]:
        """
        Função principal que otimiza um roteiro para geração visual.
        
        Args:
            script_text: Texto do roteiro diretamente
            script_data: Dados do roteiro em formato dict (fallback)
            visual_style: Estilo visual para aplicar
            content_category: Categoria do conteúdo ou 'auto_detect'
            target_duration: Duração total do vídeo em segundos
            segment_duration: Duração de cada segmento em segundos
        """
        try:
            # Extrair texto do roteiro
            if script_text:
                text = script_text
            elif script_data:
                text = script_data.get('roteiro_completo', script_data.get('script', ''))
            else:
                logger.warning("Nenhum roteiro fornecido para otimização visual")
                return []
            
            if not text:
                logger.warning("Roteiro vazio fornecido para otimização visual")
                return []
            
            # Detectar categoria do conteúdo se necessário
            if content_category == "auto_detect":
                category = self.detect_content_category(text)
            else:
                category = content_category
                
            logger.info(f"🎯 Categoria: {category}, Estilo: {visual_style}")
            
            # Segmentar roteiro por tempo
            segments = self.segment_script_by_time(text, segment_duration)
            logger.info(f"📝 Roteiro segmentado em {len(segments)} partes")
            
            # Gerar prompts visuais para cada segmento
            visual_prompts = []
            for i, segment in enumerate(segments):
                try:
                    visual_prompt = self.generate_visual_prompt(
                        segment['text'], 
                        category, 
                        visual_style
                    )
                    
                    if visual_prompt:
                        visual_prompts.append({
                            "segment_index": i,
                            "start_time": segment.get('start_time', i * segment_duration),
                            "end_time": segment.get('end_time', (i + 1) * segment_duration),
                            "original_text": segment['text'],
                            "visual_prompt": visual_prompt,
                            "category": category,
                            "style": visual_style
                        })
                        logger.info(f"✅ Prompt visual {i+1} gerado")
                    else:
                        logger.warning(f"⚠️ Falha na geração do prompt visual {i+1}")
                        
                except Exception as e:
                    logger.error(f"Erro no segmento {i}: {e}")
                    continue
            
            logger.info(f"🎨 {len(visual_prompts)} prompts visuais gerados com sucesso")
            return visual_prompts
            
        except Exception as e:
            logger.error(f"Erro na otimização visual: {e}", exc_info=True)
            return []

# Função auxiliar para integração fácil
def optimize_script_visuals(script_data: Dict[str, Any], visual_style: str = "cinematic") -> List[Dict[str, Any]]:
    """
    Função de conveniência para otimizar roteiros para geração visual.
    """
    optimizer = VisualPromptOptimizer()
    return optimizer.optimize_script_for_visuals(script_data=script_data, visual_style=visual_style)
