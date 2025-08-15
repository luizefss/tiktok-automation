# /var/www/tiktok-automation/backend/services/image_generator.py

import os
import logging
import base64
import json
import hashlib
from typing import List, Dict, Optional, Tuple, Any
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import numpy as np
import requests
from datetime import datetime
from config_manager import get_config
import asyncio  
import random 
from services.advanced_image_service import AdvancedImageService

logger = logging.getLogger(__name__)
config = get_config()


class ImageGeneratorService:
    def __init__(self):
        """Inicializa o gerador de imagens com Vertex AI Imagen 4 e fallback"""
        self.images_dir = config.IMAGES_DIR
        os.makedirs(self.images_dir, exist_ok=True)

        self.vertex_available = False
        self.api_key_available = False
        self._setup_vertex_ai()
        self._setup_api_key()

        self.visual_styles = self._setup_visual_styles()

        # Serviço avançado para DALL·E 3 e Leonardo (para fallback/alternativa)
        try:
            self.advanced_service = AdvancedImageService()
        except Exception as e:
            logger.warning(f"⚠️ Não foi possível inicializar AdvancedImageService: {e}")
            self.advanced_service = None

        logger.info("✅ Image Generator Service inicializado")

    def _setup_vertex_ai(self):
        """Configura o cliente da Vertex AI"""
        try:
            from google.cloud import aiplatform
            if config.SERVICE_ACCOUNT_PATH.exists():
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = str(
                    config.SERVICE_ACCOUNT_PATH)
            aiplatform.init(project=config.GOOGLE_PROJECT_ID,
                            location=config.GOOGLE_LOCATION)
            self.vertex_available = True
            logger.info("✅ Vertex AI configurado para Imagen 4")
        except Exception as e:
            logger.warning(
                f"⚠️ Vertex AI não disponível, usando fallback: {e}")

    def _setup_api_key(self):
        """Verifica se a API Key do Google AI Studio está disponível"""
        if config.VERTEX_AI_API_KEY:
            self.api_key_available = True
            logger.info("✅ Google AI Studio API Key disponível")

    def _setup_visual_styles(self) -> Dict[str, Dict[str, Any]]:
        """Configuração de estilos visuais para diferentes tipos de conteúdo"""
        return {
            "tecnologia": {
                "style": "futuristic, high-tech, digital, neon lights, cyberpunk",
                "colors": "blue, cyan, purple, electric",
                "mood": "innovative, cutting-edge, modern"
            },
            "educativo": {
                "style": "clean, minimalist, educational, infographic style",
                "colors": "blue, green, white, professional",
                "mood": "clear, informative, trustworthy"
            },
            "entretenimento": {
                "style": "vibrant, colorful, dynamic, pop art, energetic",
                "colors": "bright colors, rainbow, vivid",
                "mood": "fun, exciting, engaging"
            },
            "misterio": {
                "style": "dark, mysterious, noir, shadows, dramatic lighting",
                "colors": "dark purple, black, gold, crimson",
                "mood": "suspenseful, intriguing, enigmatic"
            },
            "lifestyle": {
                "style": "modern, trendy, aesthetic, instagram-worthy",
                "colors": "pastel, warm tones, natural",
                "mood": "aspirational, stylish, contemporary"
            },
            "ciencia": {
                "style": "scientific, laboratory, research, molecular, space",
                "colors": "blue, white, green, scientific",
                "mood": "precise, analytical, discovery"
            }
        }

    async def generate_images_for_script(self, script_data: Dict, visual_style: str = "misterio", provider: str = "hybrid") -> List[str]:
        """
        Gera imagens inteligentes baseadas no contexto do roteiro.
        
        Args:
            script_data: Dicionário contendo o roteiro e metadados.
            visual_style: Estilo visual escolhido.
            provider: Provedor desejado ("imagen" | "openai" | "hybrid")
            
        Returns:
            Lista de caminhos dos arquivos de imagem gerados.
        """
        try:
            # Verificar se temos visual_prompts estruturados
            visual_prompts = script_data.get('visual_prompts', [])
            visual_cues = script_data.get('visual_cues', [])
            
            if visual_prompts:
                # Usar visual_prompts estruturados (novo formato)
                logger.info(f"✅ Usando {len(visual_prompts)} visual_prompts estruturados")
                num_images = len(visual_prompts)

                # Extrair os prompts das imagens já formatados
                image_prompts: List[str] = []
                for vp in visual_prompts:
                    if isinstance(vp, dict) and 'image_prompt' in vp:
                        image_prompts.append(vp['image_prompt'])
                    else:
                        # Fallback se não estiver no formato esperado
                        image_prompts.append(str(vp))
                # 1) Deduplicar prompts idênticos
                seen = set()
                deduped: List[str] = []
                for p in image_prompts:
                    key = ' '.join(p.lower().split())
                    if key not in seen:
                        seen.add(key)
                        deduped.append(p)
                image_prompts = deduped

                # 2) Garantir no mínimo 20 imagens, gerando variações ricas
                min_count = 20
                if len(image_prompts) < min_count:
                    base = list(image_prompts)
                    if not base:
                        base = [f"generic scene, {visual_style}"]
                    # Função interna para criar variações robustas
                    def _make_variations(src: str, need: int, start_idx: int = 0) -> List[str]:
                        presets = [
                            "overhead view, wide establishing shot, 24mm lens, morning soft light",
                            "low angle hero shot, 35mm lens, dramatic rim lighting, contrasty shadows",
                            "close-up macro details, 85mm lens, shallow depth of field, bokeh background",
                            "medium shot, rule of thirds composition, golden hour warm light",
                            "silhouette backlit, sun flare, atmospheric haze, cinematic look",
                            "POV perspective, slight motion blur, handheld feel",
                            "from behind the subject, leading lines, dynamic perspective",
                            "bird's-eye view, symmetrical framing, minimalist background",
                            "night scene, practical neon lights, reflections, moody colors",
                            "rainy weather, wet surfaces, specular highlights, dramatic clouds",
                            "foggy morning, volumetric light beams, soft palette",
                            "high contrast chiaroscuro, painterly texture, film grain",
                        ]
                        out: List[str] = []
                        i = start_idx
                        while len(out) < need:
                            preset = presets[i % len(presets)]
                            i += 1
                            out.append(f"{src}, {preset}")
                        return out
                    idx = 0
                    while len(image_prompts) < min_count:
                        for b in base:
                            need = min_count - len(image_prompts)
                            if need <= 0:
                                break
                            vars_batch = _make_variations(b, min(3, need), start_idx=idx)
                            idx += 3
                            image_prompts.extend(vars_batch)
                            if len(image_prompts) >= min_count:
                                break
                # Ajustar num_images ao total final de prompts
                num_images = len(image_prompts)
                        
            elif visual_cues:
                # Usar visual_cues (formato antigo)
                logger.info(f"⚠️ Usando {len(visual_cues)} visual_cues (formato antigo)")
                num_images = max(len(visual_cues), 20)
                image_prompts = self._create_image_prompts(visual_cues, visual_style, num_images)
            else:
                # Fallback padrão
                logger.warning("❌ Nenhum visual_prompts ou visual_cues encontrado, usando fallback")
                num_images = 20
                image_prompts = self._create_image_prompts([], visual_style, num_images)

            logger.info(f"🎨 Gerando {num_images} imagens para o roteiro...")

            # Preparar diversidade de provedores quando 'hybrid'
            per_image_providers: List[str]
            # Normalizar alias 'dalle' -> 'openai'
            normalized_provider = (provider or "hybrid").lower()
            if normalized_provider == 'dalle':
                normalized_provider = 'openai'
            if normalized_provider == "hybrid":
                cycle: List[str] = []
                if self.vertex_available or self.api_key_available:
                    cycle.append("imagen")
                if self.advanced_service:
                    cycle.append("leonardo")
                cycle.append("openai")  # manter DALL·E como opção adicional
                if not cycle:
                    cycle = ["hybrid"]
                per_image_providers = [cycle[i % len(cycle)] for i in range(num_images)]
            else:
                per_image_providers = [normalized_provider] * num_images

            # Gera imagens em paralelo com provedores variados (se aplicável)
            tasks = [self._generate_single_image(
                prompt, f"scene_{i+1}", visual_style, per_image_providers[i]) for i, prompt in enumerate(image_prompts)]
            generated_images = await asyncio.gather(*tasks)

            valid_images = [path for path in generated_images if path]

            logger.info(
                f"✅ {len(valid_images)} imagens geradas para o roteiro")
            return valid_images

        except Exception as e:
            logger.error(f"❌ Erro ao gerar imagens para roteiro: {e}")
            return []

    def _create_image_prompts(self, concepts: List[str], visual_style: str, num_images: int) -> List[str]:
        """Cria prompts otimizados para Imagen 3, com base nos conceitos."""
        style_config = self.visual_styles.get(
            visual_style, self.visual_styles["misterio"])
        prompts = []

        base_style = f"{style_config['style']}, {style_config['colors']}, {style_config['mood']}"

        for i, concept in enumerate(concepts[:num_images]):
            # Prompt customizado para o conceito
            prompt = f"""
            {concept}, {base_style}, 
            ultra detailed, high quality, cinematic lighting, 
            vertical format 9:16, social media ready,
            no text, no words, visual storytelling
            """
            prompts.append(' '.join(prompt.split()))

        # Se não houver conceitos, gera imagens genéricas
        while len(prompts) < num_images:
            base_concept = concepts[0] if concepts else "cena misteriosa"
            variation_prompt = f"{base_concept} variation, {base_style}, different angle, creative composition, vertical format 9:16, high quality"
            prompts.append(variation_prompt.strip())

        return prompts[:num_images]

    async def _generate_single_image(self, prompt: str, filename_prefix: str, visual_style: str, provider: str = "hybrid") -> Optional[str]:
        """Gera uma única imagem usando o provedor selecionado e fallbacks."""
        # Normalizar alias 'dalle' -> 'openai'
        provider = (provider or "hybrid").lower()
        if provider == 'dalle':
            provider = 'openai'
        image_path: Optional[str] = None

        # Mapear estilo textual para DALL·E, se necessário
        dalle_style_map = {
            "misterio": "cinematic",
            "tecnologia": "realistic",
            "ciencia": "realistic",
            "entretenimento": "artistic",
            "educativo": "minimalist",
            "lifestyle": "realistic",
        }
        dalle_style = dalle_style_map.get(visual_style, "realistic")

        async def try_imagen_chain() -> Optional[str]:
            path = None
            if self.vertex_available:
                path = self._generate_with_imagen4(prompt, filename_prefix)
            if not path and self.api_key_available:
                path = self._generate_with_api(prompt, filename_prefix)
            return path

        async def try_dalle3() -> Optional[str]:
            if not self.advanced_service:
                return None
            try:
                return await self.advanced_service.generate_with_dalle3(prompt, style=dalle_style)
            except Exception as e:
                logger.warning(f"⚠️ Falha no DALL·E 3: {e}")
                return None

        # Roteamento por provedor
        if provider == "imagen":
            image_path = await try_imagen_chain()
        elif provider == "openai":
            image_path = await try_dalle3()
        elif provider == "leonardo":
            if self.advanced_service:
                try:
                    image_path = await self.advanced_service.generate_with_leonardo_static(prompt)
                except Exception as e:
                    logger.warning(f"⚠️ Falha no Leonardo estático: {e}")
        else:  # hybrid
            image_path = await try_imagen_chain()
            # Priorizar Leonardo antes de DALL·E se disponível
            if not image_path and self.advanced_service:
                try:
                    image_path = await self.advanced_service.generate_with_leonardo_static(prompt)
                except Exception as e:
                    logger.warning(f"⚠️ Falha no Leonardo estático: {e}")
            if not image_path:
                image_path = await try_dalle3()

        # Fallback procedural
        if not image_path:
            logger.info(f"   Usando fallback procedural para {filename_prefix}")
            image_path = self._create_procedural_image(
                prompt=prompt,
                content_type=visual_style,
                index=filename_prefix
            )

        if not image_path:
            logger.error(f"❌ Falha em todos os métodos para {filename_prefix}")
            return None

        logger.info(f"✅ Imagem gerada: {os.path.basename(image_path)}")
        return image_path

    async def generate_images_imagen4(self, prompt: str, count: int = 1) -> List[str]:
        """Método público para gerar imagens especificamente com Imagen 4"""
        logger.info(f"🎨 Gerando {count} imagens com Imagen 4: {prompt[:50]}...")
        
        results = []
        for i in range(count):
            filename_prefix = f"imagen4_{i+1}"
            
            # Tentar Vertex AI primeiro
            if self.vertex_available:
                path = self._generate_with_imagen4(prompt, filename_prefix)
                if path:
                    results.append(path)
                    continue
                    
            # Fallback para API REST
            if self.api_key_available:
                path = self._generate_with_api(prompt, filename_prefix)
                if path:
                    results.append(path)
                    continue
                    
            logger.warning(f"⚠️ Falha ao gerar imagem {i+1}/{count} com Imagen 4")
        
        logger.info(f"✅ Imagen 4: {len(results)}/{count} imagens geradas")
        return results

    def _generate_with_imagen4(self, prompt: str, filename_prefix: str) -> Optional[str]:
        """Gera imagem usando Vertex AI Imagen 4."""
        if not self.vertex_available:
            return None
        try:
            from vertexai.preview.vision_models import ImageGenerationModel
            model = ImageGenerationModel.from_pretrained(
                "imagen-4.0-ultra-generate-preview-06-06")
            response = model.generate_images(
                prompt=prompt,
                number_of_images=1,
                aspect_ratio="9:16",
                safety_filter_level="block_some",
                person_generation="allow_all",
                add_watermark=False
            )
            output_path = self.images_dir / \
                f"{filename_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            response.images[0].save(location=str(output_path))
            return str(output_path)
        except Exception as e:
            logger.warning(f"⚠️ Imagen 4 falhou: {e}")
            return None

    def _generate_with_api(self, prompt: str, filename_prefix: str) -> Optional[str]:
        """Gera imagem usando API REST do Google AI Studio (Imagen 4) como alternativa."""
        if not self.api_key_available:
            return None
        try:
            url = "https://generativelanguage.googleapis.com/v1beta/models/imagen-4.0-ultra-generate-preview-06-06:generateImage"
            headers = {"Content-Type": "application/json",
                       "x-goog-api-key": config.VERTEX_AI_API_KEY}
            data = {"prompt": prompt, "number_of_images": 1,
                    "aspect_ratio": "9:16"}
            response = requests.post(
                url, headers=headers, json=data, timeout=15)
            if response.status_code == 200:
                result = response.json()
                if 'images' in result and result['images']:
                    image_data = base64.b64decode(result['images'][0]['image'])
                    output_path = self.images_dir / \
                        f"{filename_prefix}_api_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    with open(output_path, 'wb') as f:
                        f.write(image_data)
                    return str(output_path)
            return None
        except Exception as e:
            logger.warning(f"⚠️ API de imagem (Imagen 4) falhou: {e}")
            return None

    def _create_procedural_image(self, prompt: str, content_type: str, index: int) -> str:
        """Cria imagem procedural de alta qualidade como fallback."""
        width, height = config.VIDEO_WIDTH, config.VIDEO_HEIGHT

        # Esquemas de cores melhorados por tipo
        color_schemes = {
            'misterio': {'gradient': [(5, 5, 15), (25, 20, 45), (40, 30, 60)], 'accent': (100, 80, 140), 'glow': (150, 130, 200)},
            'tecnologia': {'gradient': [(0, 0, 10), (10, 5, 30), (20, 10, 50)], 'accent': (0, 255, 255), 'glow': (50, 200, 255)},
            'ciencia': {'gradient': [(2, 10, 2), (10, 40, 10), (30, 80, 30)], 'accent': (100, 255, 100), 'glow': (150, 255, 150)},
            'historia': {'gradient': [(20, 15, 5), (50, 40, 15), (80, 60, 20)], 'accent': (255, 200, 50), 'glow': (255, 230, 150)},
            'curiosidade': {'gradient': [(15, 15, 30), (30, 30, 60), (45, 45, 90)], 'accent': (255, 150, 50), 'glow': (255, 200, 100)},
            'default': {'gradient': [(30, 30, 30), (60, 60, 60), (90, 90, 90)], 'accent': (180, 180, 180), 'glow': (220, 220, 220)}
        }

        colors = color_schemes.get(content_type, color_schemes['default'])
        img = Image.new('RGB', (width, height), colors['gradient'][0])
        img_array = np.zeros((height, width, 3), dtype=np.uint8)
        center_x, center_y = width // 2, height // 2
        for y in range(height):
            for x in range(width):
                dist = np.sqrt((x - center_x)**2 + (y - center_y)**2)
                max_dist = np.sqrt(center_x**2 + center_y**2)
                ratio = dist / max_dist
                t = min(1.0, max(0.0, (ratio - 0.3) / 0.7))
                color = tuple(
                    int(colors['gradient'][0][i] * (1 - t) +
                        colors['gradient'][1][i] * t)
                    for i in range(3)
                )
                img_array[y, x] = color
        img = Image.fromarray(img_array)
        draw = ImageDraw.Draw(img, 'RGBA')
        for _ in range(50):
            x = random.randint(0, width)
            y = random.randint(0, height)
            size = random.randint(1, 4)
            opacity = random.randint(30, 100)
            glow_color = (*colors['glow'], opacity)
            draw.ellipse([(x-size, y-size), (x+size, y+size)], fill=glow_color)
        img = img.filter(ImageFilter.GaussianBlur(radius=1))

        output_path = self.images_dir / \
            f"procedural_{index}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        img.save(output_path, quality=95)

        return str(output_path)

    def _apply_cinematic_filter(self, image_path: str):
        """Aplica filtro cinematográfico na imagem (pode ser usado no futuro)"""
        pass

    def generate_image(self, prompt: str, style: str = "misterio", aspect_ratio: str = "9:16") -> Dict[str, Any]:
        """
        Método público para gerar uma única imagem.
        
        Args:
            prompt: Descrição da imagem a ser gerada
            style: Estilo visual (misterio, tecnologia, ciencia, etc.)
            aspect_ratio: Proporção da imagem (9:16, 16:9, 1:1)
        
        Returns:
            Dict com success, image_path, image_url e message
        """
        try:
            logger.info(f"🎨 Gerando imagem com prompt: '{prompt}' | Estilo: {style}")
            
            # Preparar prompt com estilo
            style_config = self.visual_styles.get(style, self.visual_styles["misterio"])
            enhanced_prompt = f"{prompt}, {style_config['style']}, {style_config['colors']}, {style_config['mood']}, ultra detailed, high quality, cinematic lighting"
            
            if aspect_ratio == "9:16":
                enhanced_prompt += ", vertical format 9:16, social media ready"
            elif aspect_ratio == "16:9":
                enhanced_prompt += ", horizontal format 16:9, cinematic"
            elif aspect_ratio == "1:1":
                enhanced_prompt += ", square format 1:1, instagram ready"
            
            enhanced_prompt += ", no text, no words, visual storytelling"
            
            # Tentar gerar com Vertex AI primeiro
            image_path = None
            if self.vertex_available:
                image_path = self._generate_with_imagen3(enhanced_prompt, "single_gen")
                
            # Fallback para API se Vertex AI falhar
            if not image_path and self.api_key_available:
                image_path = self._generate_with_api(enhanced_prompt, "single_gen")
                
            # Fallback procedural se ambos falharem
            if not image_path:
                logger.info("🔄 Usando geração procedural como fallback")
                image_path = self._create_procedural_image(
                    prompt=enhanced_prompt,
                    content_type=style,
                    index="single_gen"
                )
            
            if image_path:
                # Construir URL (assumindo que as imagens são servidas estaticamente)
                image_filename = os.path.basename(image_path)
                image_url = f"/static/images/{image_filename}"
                
                logger.info(f"✅ Imagem gerada com sucesso: {image_filename}")
                return {
                    "success": True,
                    "image_path": image_path,
                    "image_url": image_url,
                    "message": "Imagem gerada com sucesso",
                    "style_used": style,
                    "method_used": "vertex_ai" if self.vertex_available else ("api" if self.api_key_available else "procedural")
                }
            else:
                logger.error("❌ Falha em todos os métodos de geração")
                return {
                    "success": False,
                    "image_path": None,
                    "image_url": None,
                    "message": "Falha em todos os métodos de geração de imagem",
                    "error": "Não foi possível gerar a imagem com nenhum método disponível"
                }
                
        except Exception as e:
            logger.error(f"❌ Erro durante geração de imagem: {e}")
            return {
                "success": False,
                "image_path": None,
                "image_url": None,
                "message": f"Erro durante geração: {str(e)}",
                "error": str(e)
            }

    def get_available_styles(self) -> List[Dict[str, Any]]:
        """Retorna estilos visuais disponíveis"""
        styles = []
        for style_id, config in self.visual_styles.items():
            styles.append({
                "id": style_id,
                "name": style_id.title(),
                "description": config["mood"],
                "preview_colors": config["colors"]
            })
        return styles
