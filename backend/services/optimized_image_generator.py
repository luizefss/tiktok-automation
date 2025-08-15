#!/usr/bin/env python3

import os
import logging
import json
import asyncio
from typing import List, Dict, Optional, Any
from datetime import datetime
import random

from config_manager import get_config
from services.image_generator import ImageGeneratorService

logger = logging.getLogger(__name__)
config = get_config()


class OptimizedImageGenerator:
    """
    Gerador de imagens otimizado para TikTok com:
    - Prompts inteligentes baseados no conteúdo
    - Estilos visuais automáticos
    - Qualidade 9:16 (vertical)
    - Continuidade visual entre cenas
    """
    
    def __init__(self):
        self.base_generator = ImageGeneratorService()
        self.tiktok_styles = self._setup_tiktok_styles()
        logger.info("✅ Optimized Image Generator inicializado")
    
    def _setup_tiktok_styles(self) -> Dict[str, Dict]:
        """Estilos otimizados para TikTok"""
        return {
            "viral_modern": {
                "style": "cinematic, modern, vibrant colors, high contrast",
                "lighting": "dramatic lighting, neon accents",
                "composition": "vertical 9:16, dynamic angle",
                "effects": "motion blur, depth of field"
            },
            "storytelling": {
                "style": "cinematic storytelling, emotional, atmospheric",
                "lighting": "warm golden hour, soft shadows",
                "composition": "vertical composition, rule of thirds",
                "effects": "film grain, color grading"
            },
            "educational": {
                "style": "clean, professional, informative",
                "lighting": "bright, even lighting",
                "composition": "centered, clear focus",
                "effects": "sharp details, high clarity"
            },
            "mystery_dark": {
                "style": "dark, mysterious, noir aesthetic",
                "lighting": "low key lighting, dramatic shadows",
                "composition": "vertical framing, tension",
                "effects": "vignette, desaturated colors"
            },
            "energetic": {
                "style": "vibrant, energetic, pop art",
                "lighting": "bright colorful lighting",
                "composition": "dynamic vertical composition",
                "effects": "saturated colors, high energy"
            }
        }
    
    def _analyze_content_style(self, script_text: str) -> str:
        """Detecta automaticamente o melhor estilo visual baseado no conteúdo"""
        text_lower = script_text.lower()
        
        # Detectar palavras-chave por categoria
        keywords = {
            "mystery_dark": ["mistério", "segredo", "oculto", "sombra", "noite", "escuro", "sussurro"],
            "energetic": ["energia", "festa", "alegria", "diversão", "animado", "explosive", "incrível"],
            "educational": ["aprenda", "descubra", "tutorial", "como fazer", "explicação", "ensinar"],
            "storytelling": ["história", "era uma vez", "aconteceu", "relato", "narrativa"]
        }
        
        # Calcular scores para cada estilo
        scores = {}
        for style, words in keywords.items():
            score = sum(1 for word in words if word in text_lower)
            scores[style] = score
        
        # Retornar estilo com maior score, ou viral_modern como padrão
        best_style = max(scores, key=scores.get) if max(scores.values()) > 0 else "viral_modern"
        
        logger.info(f"🎨 Estilo detectado: {best_style} (scores: {scores})")
        return best_style
    
    def _create_scene_prompts(self, script_data: List[Dict], visual_style: str) -> List[Dict]:
        """Cria prompts otimizados para cada cena com continuidade visual"""
        scene_prompts = []
        style_config = self.tiktok_styles[visual_style]
        
        # Cores dominantes para manter consistência
        color_palette = self._get_color_palette(visual_style)
        
        for i, scene in enumerate(script_data):
            scene_text = scene.get('text', '')
            
            # Prompt base otimizado
            base_prompt = f"""
            {scene_text}
            
            Visual Style: {style_config['style']}
            Lighting: {style_config['lighting']}
            Composition: {style_config['composition']}
            Effects: {style_config['effects']}
            Color Palette: {color_palette}
            
            TikTok optimized: vertical 9:16 aspect ratio, mobile-first design,
            eye-catching visuals, high contrast for small screens,
            clear focal point, professional quality
            """
            
            # Adicionar variações por posição na sequência
            if i == 0:
                base_prompt += "\nOpening scene: compelling hook, attention-grabbing"
            elif i == len(script_data) - 1:
                base_prompt += "\nClosing scene: satisfying conclusion, memorable"
            else:
                base_prompt += f"\nMiddle scene {i+1}: maintain visual continuity"
            
            scene_prompts.append({
                "text": scene_text,
                "prompt": base_prompt.strip(),
                "scene_number": i + 1,
                "style": visual_style
            })
        
        return scene_prompts
    
    def _get_color_palette(self, visual_style: str) -> str:
        """Retorna paleta de cores para o estilo"""
        palettes = {
            "viral_modern": "vibrant blues, electric purples, neon accents",
            "storytelling": "warm golden tones, cinematic orange and teal",
            "educational": "clean blues, professional whites, accent colors",
            "mystery_dark": "deep blacks, moody blues, silver highlights",
            "energetic": "bright yellows, electric pinks, vibrant greens"
        }
        return palettes.get(visual_style, "balanced color palette")
    
    def _map_legacy_style(self, style: str) -> str:
        """Mapeia estilos antigos para novos estilos otimizados"""
        style_mapping = {
            "realista": "storytelling",
            "cinematico": "viral_modern", 
            "dramatico": "mystery_dark",
            "futurista": "energetic",
            "artistico": "storytelling"
        }
        return style_mapping.get(style.lower(), "viral_modern")
    
    async def generate_optimized_images(self, script_data: List[Dict], visual_style: Optional[str] = None) -> Dict[str, Any]:
        """
        Gera imagens otimizadas para TikTok
        
        Args:
            script_data: Lista de cenas com texto
            visual_style: Estilo visual (auto-detectado se None)
        
        Returns:
            Dict com imagens geradas e metadados
        """
        try:
            # Auto-detectar estilo se não fornecido ou mapear estilo antigo
            if not visual_style:
                full_script = " ".join([scene.get('text', '') for scene in script_data])
                visual_style = self._analyze_content_style(full_script)
            else:
                # Mapear estilos antigos para novos
                visual_style = self._map_legacy_style(visual_style)
            
            logger.info(f"🎬 Gerando imagens otimizadas - Estilo: {visual_style}")
            
            # Criar prompts otimizados
            scene_prompts = self._create_scene_prompts(script_data, visual_style)
            
            # Gerar imagens usando o serviço base
            generated_images = []
            
            for i, scene_prompt in enumerate(scene_prompts):
                logger.info(f"🖼️ Gerando imagem {i+1}/{len(scene_prompts)}")
                
                # Criar dados corretos para o gerador base
                scene_data = {
                    "text": scene_prompt["text"],
                    "prompt": scene_prompt["prompt"],
                    "scene": scene_prompt["scene_number"]
                }
                
                # Usar o gerador base com dados corretos
                result = await self.base_generator.generate_images_for_script(
                    [scene_data], 
                    visual_style
                )
                
                if result and len(result) > 0:
                    image_data = result[0]
                    image_data.update({
                        "scene_number": i + 1,
                        "style": visual_style,
                        "optimized": True
                    })
                    generated_images.append(image_data)
                else:
                    logger.warning(f"⚠️ Falha na geração da imagem {i+1}")
            
            if generated_images:
                logger.info(f"✅ {len(generated_images)} imagens otimizadas geradas")
                return {
                    "success": True,
                    "images": generated_images,
                    "style": visual_style,
                    "total_scenes": len(script_data),
                    "generated_count": len(generated_images),
                    "optimized": True
                }
            else:
                logger.error("❌ Falha na geração de imagens otimizadas")
                return {
                    "success": False,
                    "error": "Não foi possível gerar imagens otimizadas",
                    "style": visual_style
                }
                
        except Exception as e:
            logger.error(f"❌ Erro no gerador otimizado: {e}")
            return {
                "success": False,
                "error": f"Erro interno: {str(e)}"
            }
    
    async def generate_single_optimized_image(self, text: str, style: Optional[str] = None) -> Dict[str, Any]:
        """Gera uma única imagem otimizada"""
        if not style:
            style = self._analyze_content_style(text)
        
        scene_data = [{"text": text}]
        result = await self.generate_optimized_images(scene_data, style)
        
        if result.get("success") and result.get("images"):
            return {
                "success": True,
                "image": result["images"][0],
                "style": style
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "Falha na geração")
            }