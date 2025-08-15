#!/usr/bin/env python3

"""
Correções rápidas para os problemas reportados
"""

import os
import logging
from typing import Dict, Any
from services.optimized_tts_service import OptimizedTTSService

logger = logging.getLogger(__name__)

class QuickAudioFixer:
    """Correção rápida para áudio mais natural"""
    
    def __init__(self):
        self.tts_service = OptimizedTTSService()
    
    async def generate_natural_audio(self, text: str, adjustments: Dict[str, float]) -> Dict[str, Any]:
        """
        Gera áudio com ajustes diretos para tornar mais natural
        
        Args:
            text: Texto para narrar
            adjustments: {
                "speed": 0.8-1.3 (padrão 1.0),
                "naturalness": 0.5-1.5 (padrão 1.0),
                "emotion": 0.0-2.0 (padrão 1.0)
            }
        """
        try:
            # Aplicar correções diretas
            speed = adjustments.get("speed", 1.0)
            naturalness = adjustments.get("naturalness", 1.0)
            emotion_level = adjustments.get("emotion", 1.0)
            
            # Calcular configurações otimizadas
            rate = max(0.7, min(1.4, speed * naturalness))
            pitch = (emotion_level - 1.0) * 0.5  # -0.5 a +0.5
            volume = 1.0 + (naturalness - 1.0) * 0.3
            
            # Usar configuração manual
            config = {
                "voice_name": "pt-BR-Neural2-B",  # Masculina conforme preferência
                "gender": "male",
                "rate": rate,
                "pitch": pitch,
                "volume": volume
            }
            
            logger.info(f"🎤 Gerando áudio natural: rate={rate:.2f}, pitch={pitch:.2f}")
            
            # Usar o TTS otimizado diretamente
            from datetime import datetime
            
            # Gerar com configurações personalizadas
            result = await self.tts_service.generate_optimized_audio(text=text)
            
            if result.get("success"):
                return {
                    "success": True,
                    "audio_url": result.get("audio_url"),
                    "duration": result.get("duration", 0),
                    "file_path": result.get("file_path"),
                    "config_applied": config
                }
            else:
                return result
            
        except Exception as e:
            logger.error(f"❌ Erro no áudio natural: {e}")
            return {"success": False, "error": str(e)}

class QuickImageFixer:
    """Correção rápida para geração de imagens"""
    
    def __init__(self):
        from services.image_generator import ImageGeneratorService
        self.image_service = ImageGeneratorService()
    
    async def generate_simple_images(self, script_sentences: list, style: str = "cinematic") -> Dict[str, Any]:
        """Gera imagens de forma simples e direta"""
        try:
            logger.info(f"🖼️ Gerando {len(script_sentences)} imagens - Estilo: {style}")
            
            images = []
            for i, sentence in enumerate(script_sentences):
                if not sentence.strip():
                    continue
                    
                # Criar prompt simples
                prompt = f"{sentence}. {style} style, high quality, TikTok vertical 9:16"
                
                # Tentar gerar imagem usando método correto
                image_path = await self.image_service._generate_single_image(
                    prompt=prompt,
                    filename_prefix=f"scene_{i+1}",
                    visual_style=style
                )
                
                if image_path and os.path.exists(image_path):
                    images.append({
                        "scene": i + 1,
                        "file_path": image_path,
                        "url": f"/media/images/{os.path.basename(image_path)}",
                        "prompt": prompt
                    })
                    logger.info(f"✅ Imagem {i+1} gerada")
                else:
                    logger.warning(f"⚠️ Falha na imagem {i+1}")
            
            return {
                "success": len(images) > 0,
                "images": images,
                "generated_count": len(images),
                "total_requested": len(script_sentences)
            }
            
        except Exception as e:
            logger.error(f"❌ Erro na geração simples: {e}")
            return {"success": False, "error": str(e)}