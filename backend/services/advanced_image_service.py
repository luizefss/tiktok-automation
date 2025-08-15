# /var/www/tiktok-automation/backend/services/advanced_image_service.py

import os
import logging
import asyncio
import aiohttp
import openai
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from config_manager import get_config
import json
import base64
from PIL import Image
import requests
from pathlib import Path

logger = logging.getLogger(__name__)
config = get_config()

class AdvancedImageService:
    def __init__(self):
        logger.info("🎨 Inicializando Advanced Image Service...")
        
        # Configurar OpenAI DALL-E 3
        self.openai_client = None
        if hasattr(config, 'OPENAI_API_KEY') and config.OPENAI_API_KEY:
            openai.api_key = config.OPENAI_API_KEY
            self.openai_client = openai
            logger.info("✅ OpenAI DALL-E 3 configurado")
        else:
            logger.warning("⚠️ OpenAI API Key não encontrada")
        
        # Configurar Leonardo AI
        self.leonardo_api_key = getattr(config, 'LEONARDO_API_KEY', None)
        self.leonardo_base_url = "https://cloud.leonardo.ai/api/rest/v1"
        
        if self.leonardo_api_key:
            logger.info(f"✅ Leonardo AI configurado: {self.leonardo_api_key[:10]}...")
        else:
            logger.warning("⚠️ Leonardo AI API Key não encontrada")
        
        logger.info("✅ Advanced Image Service inicializado")

    async def generate_image_with_fallback(self, prompt: str, style: str = "realistic") -> Optional[str]:
        """Gera imagem com DALL-E 3 primeiro, fallback para Imagen 4"""
        # Primeiro tenta com DALL-E 3
        logger.info(f"🎨 Tentando gerar imagem com DALL-E 3: {prompt[:50]}...")
        dalle_result = await self.generate_with_dalle3(prompt, style)
        
        if dalle_result:
            logger.info("✅ Imagem gerada com sucesso via DALL-E 3")
            return dalle_result
        
        # Fallback para Imagen 4
        try:
            from services.image_generator import ImageGeneratorService
            imagen_service = ImageGeneratorService()
            
            logger.info(f"🔄 Fallback: Tentando gerar imagem com Imagen 4: {prompt[:50]}...")
            imagen_result = await imagen_service.generate_images_imagen4(prompt, 1)
            
            if imagen_result and len(imagen_result) > 0:
                logger.info("✅ Imagem gerada com sucesso via Imagen 4")
                return imagen_result[0]
                
        except Exception as e:
            logger.warning(f"⚠️ Imagen 4 falhou: {e}")
            
        logger.error("❌ Falha em todas as tentativas de geração de imagem")
        return None

    async def generate_with_dalle3(self, prompt: str, style: str = "realistic") -> Optional[str]:
        """Gera imagem com DALL-E 3"""
        if not self.openai_client:
            logger.error("❌ OpenAI client não configurado")
            return None
            
        try:
            logger.info(f"🎨 Gerando imagem com DALL-E 3: {prompt[:50]}...")
            
            # Adaptar o prompt para DALL-E 3
            dalle_prompt = self._adapt_prompt_for_dalle(prompt, style)
            
            response = await asyncio.to_thread(
                self.openai_client.images.generate,
                model="dall-e-3",
                prompt=dalle_prompt,
                size="1024x1792",  # Formato vertical para TikTok
                quality="hd",
                n=1
            )
            
            if response.data and len(response.data) > 0:
                image_url = response.data[0].url
                
                # Baixar e salvar a imagem
                local_path = await self._download_and_save_image(image_url, "dalle3")
                
                if local_path:
                    logger.info(f"✅ Imagem DALL-E 3 salva: {local_path}")
                    return local_path
                    
        except Exception as e:
            logger.error(f"❌ Erro ao gerar imagem com DALL-E 3: {e}")
            
        return None

    async def generate_with_leonardo_static(self, prompt: str, style: str = "realistic", size: str = "1024x1792") -> Optional[str]:
        """Gera imagem estática com Leonardo AI e salva em IMAGES_DIR.

        Observações importantes:
        - Leonardo limita width/height entre 32 e 1536.
        - Muitos modelos gerativos funcionam melhor com dimensões múltiplas de 32.
        - Esta função normaliza o parâmetro "size" para respeitar esses limites e manter o aspecto.
        """
        if not self.leonardo_api_key:
            logger.error("❌ Leonardo AI não configurado")
            return None

        try:
            # Normalizar tamanho respeitando limites da API
            width, height = self._normalize_size_for_leonardo(size)
            logger.info(f"🔧 Dimensões Leonardo normalizadas: {width}x{height}")

            headers = {
                'Authorization': f'Bearer {self.leonardo_api_key}',
                'Content-Type': 'application/json'
            }

            payload = {
                "height": height,
                "width": width,
                "modelId": "1e60896f-3c26-4296-8ecc-53e2afecc132",  # Leonardo Phoenix
                "prompt": prompt,
                "num_images": 1,
                "alchemy": True,  # Melhor qualidade
                "presetStyle": "DYNAMIC"
            }
            
            logger.info(f"📡 Enviando payload para Leonardo: {payload}")

            # 1) Criar geração
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.leonardo_base_url}/generations", headers=headers, json=payload) as r:
                    logger.info(f"📡 Leonardo API status: {r.status}")
                    if r.status != 200:
                        txt = await r.text()
                        logger.error(f"❌ Leonardo erro: {r.status} - {txt}")
                        raise RuntimeError(f"Leonardo create failed {r.status}: {txt}")
                    job = await r.json()
                    logger.info(f"✅ Leonardo job: {job}")
                    gen_id = job.get("sdGenerationJob", {}).get("generationId") or job.get("generationId") or job.get("id")
                    if not gen_id:
                        logger.error(f"❌ Sem generationId: {job}")
                        raise RuntimeError(f"Geração sem generationId: {job}")
                    logger.info(f"🔍 ID gerado: {gen_id}")

            # 2) Poll resultado
            for _ in range(120):
                await asyncio.sleep(2)
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{self.leonardo_base_url}/generations/{gen_id}", headers=headers) as rs:
                        if rs.status != 200:
                            continue
                        info = await rs.json()
                        outs = (info.get("generations_by_pk", {}).get("generated_images")
                                or info.get("data", {}).get("images")
                                or info.get("images")
                                or [])
                        if outs:
                            image_data = outs[0]
                            url = image_data.get("url") or image_data.get("imageUrl")
                            image_id = image_data.get("id")  # Capturar o image_id
                            if not url:
                                break
                            # Baixar e salvar
                            async with aiohttp.ClientSession() as s2:
                                async with s2.get(url) as img_resp:
                                    if img_resp.status == 200:
                                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                        filename = f"leonardo_{timestamp}.png"
                                        local_path = config.IMAGES_DIR / filename
                                        with open(local_path, 'wb') as f:
                                            f.write(await img_resp.read())
                                        
                                        # Armazenar image_id para uso posterior
                                        if image_id:
                                            await self._store_image_metadata(str(local_path), image_id)
                                        
                                        return str(local_path)
            return None
        except Exception as e:
            logger.error(f"❌ Erro ao gerar imagem com Leonardo: {e}")
            return None

    async def animate_image_with_leonardo(self, image_path: str, motion_prompt: str) -> Optional[str]:
        """Anima imagem usando Leonardo AI"""
        if not self.leonardo_api_key:
            logger.error("❌ Leonardo AI não configurado")
            return None
            
        try:
            logger.info(f"🎬 Animando imagem com Leonardo AI: {image_path}")
            
            # 1. Fazer upload da imagem para Leonardo AI
            upload_response = await self._upload_image_to_leonardo(image_path)
            if not upload_response:
                return None
                
            # 2. Criar animação
            animation_response = await self._create_leonardo_animation(
                upload_response['id'], 
                motion_prompt
            )
            
            if animation_response:
                # 3. Aguardar processamento e baixar resultado
                animated_video_path = await self._wait_and_download_animation(
                    animation_response['id']
                )
                
                if animated_video_path:
                    logger.info(f"✅ Imagem animada com sucesso: {animated_video_path}")
                    return animated_video_path
                    
        except Exception as e:
            logger.error(f"❌ Erro ao animar imagem com Leonardo AI: {e}")
            
        return None

    async def leonardo_text_to_video(self, prompt: str, motion_prompt: str, duration_seconds: Optional[float] = None, size: str = "1024x1792") -> Optional[str]:
        """Gera imagem e anima em uma sequência única usando Leonardo AI.
        Observação: a API do Leonardo separa geração e motion; aqui encadeamos automaticamente.
        """
        if not self.leonardo_api_key:
            logger.error("❌ Leonardo AI não configurado")
            return None
        try:
            # 1) Gerar imagem estática primeiro
            # Normaliza para evitar erros de dimensão (ex.: 1024x1792 -> 864x1536)
            image_path = await self.generate_with_leonardo_static(prompt, size=size)
            if not image_path:
                logger.error("❌ Falha na etapa de imagem do Leonardo")
                return None
            # 2) Enriquecer motion_prompt com duração se fornecida
            if duration_seconds and duration_seconds > 0:
                motion_prompt = f"{motion_prompt}, duration {int(duration_seconds)} seconds, 9:16"
            # 3) Animar a imagem usando o novo endpoint mais moderno
            # Primeiro obter o image_id da imagem gerada
            image_id = await self._extract_image_id_from_path(image_path)
            if image_id:
                video_path = await self.create_leonardo_image_to_video(image_id, motion_prompt, is_generated=True)
            else:
                # Fallback para método tradicional se não conseguir extrair ID
                video_path = await self.animate_image_with_leonardo(image_path, motion_prompt)
            
            return video_path
        except Exception as e:
            logger.error(f"❌ Erro no fluxo texto→vídeo Leonardo: {e}")
            return None

    def _normalize_size_for_leonardo(self, size: str) -> Tuple[int, int]:
        """Normaliza dimensões para os limites da API Leonardo (32..1536) mantendo aspecto.

        - Aceita formatos como "1024x1792" ou "W x H" (com espaços).
        - Ajusta por escala para que nenhum lado ultrapasse 1536.
        - Arredonda para múltiplos de 32, mínimos 32.
        - Se parsing falhar, usa 864x1536 (vertical 9:16 dentro do limite).
        """
        try:
            # Extrair números do parâmetro size
            cleaned = size.lower().replace(' ', '')
            if 'x' in cleaned:
                w_str, h_str = cleaned.split('x')
                w, h = int(float(w_str)), int(float(h_str))
            else:
                raise ValueError("Formato de size inválido")

            MAX_DIM, MIN_DIM = 1536, 32

            # Escala para não exceder o máximo em nenhum eixo
            scale = min(MAX_DIM / float(w), MAX_DIM / float(h), 1.0)
            w_scaled = max(MIN_DIM, int(round(w * scale)))
            h_scaled = max(MIN_DIM, int(round(h * scale)))

            # Arredondar para múltiplos de 32 (prática comum para modelos SD)
            def round32(v: int) -> int:
                return max(MIN_DIM, min(MAX_DIM, int(round(v / 32.0) * 32)))

            w_32, h_32 = round32(w_scaled), round32(h_scaled)

            # Garantir novamente limites após arredondamento
            w_32 = min(w_32, MAX_DIM)
            h_32 = min(h_32, MAX_DIM)

            # Evitar zero
            w_32 = max(w_32, MIN_DIM)
            h_32 = max(h_32, MIN_DIM)

            # Log auxiliar quando houver mudança
            if (w_32, h_32) != (w, h):
                logger.debug(f"🔧 Normalizado tamanho Leonardo: {w}x{h} -> {w_32}x{h_32}")

            return w_32, h_32
        except Exception:
            # Vertical seguro por padrão
            return 864, 1536

    async def _upload_image_to_leonardo(self, image_path: str) -> Optional[Dict]:
        """Faz upload da imagem para Leonardo AI usando presigned URL"""
        try:
            headers = {
                'Authorization': f'Bearer {self.leonardo_api_key}',
                'Content-Type': 'application/json'
            }
            
            # 1. Solicitar presigned URL para upload
            upload_data = {
                'extension': 'png'
            }
            
            async with aiohttp.ClientSession() as session:
                # Solicitar URL de upload
                async with session.post(
                    f"{self.leonardo_base_url}/init-image",
                    headers=headers,
                    json=upload_data
                ) as response:
                    if response.status == 200:
                        upload_info = await response.json()
                        
                        # 2. Fazer upload da imagem usando presigned URL
                        presigned = upload_info.get('uploadInitImage', {})
                        presigned_url = presigned.get('url')
                        fields = presigned.get('fields', {})
                        init_image_id = presigned.get('id')

                        # Preparar dados para upload (S3 Presigned POST)
                        form_data = aiohttp.FormData()
                        # Campos podem vir como dict, lista de pares ou string JSON
                        try:
                            if isinstance(fields, dict):
                                for key, value in fields.items():
                                    form_data.add_field(str(key), str(value))
                            elif isinstance(fields, list):
                                for item in fields:
                                    if isinstance(item, dict) and 'name' in item and 'value' in item:
                                        form_data.add_field(str(item['name']), str(item['value']))
                                    elif isinstance(item, (list, tuple)) and len(item) == 2:
                                        k, v = item
                                        form_data.add_field(str(k), str(v))
                            elif isinstance(fields, str):
                                import json as _json
                                try:
                                    parsed = _json.loads(fields)
                                    if isinstance(parsed, dict):
                                        for k, v in parsed.items():
                                            form_data.add_field(str(k), str(v))
                                except Exception:
                                    logger.warning("⚠️ Campos presigned (fields) retornaram como string não parseável")
                        except Exception as e:
                            logger.warning(f"⚠️ Erro preparando campos presigned: {e}")
                        
                        # Ler arquivo antes do upload
                        with open(image_path, 'rb') as f:
                            img_data = f.read()
                        
                        # Adicionar arquivo aos dados do formulário
                        form_data.add_field('file', img_data, filename='image.png', content_type='image/png')
                        
                        # Upload para S3
                        async with session.post(presigned_url, data=form_data) as upload_response:
                            if upload_response.status == 204:  # S3 retorna 204 para sucesso
                                return {
                                    'id': init_image_id,
                                    'url': presigned_url
                                }
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Erro ao solicitar presigned URL: {response.status} - {error_text}")
                                
        except Exception as e:
            logger.error(f"❌ Erro no upload para Leonardo AI: {e}")
            
        return None

    async def _create_leonardo_animation(self, image_id: str, motion_prompt: str) -> Optional[Dict]:
        """Cria animação usando Leonardo Image-to-Video (endpoint mais avançado)"""
        try:
            headers = {
                'Authorization': f'Bearer {self.leonardo_api_key}',
                'Content-Type': 'application/json'
            }
            
            # Primeiro tenta Image-to-Video (endpoint mais moderno)
            animation_data = {
                "imageType": "UPLOADED",  # Para imagens de upload
                "isPublic": False,
                "imageId": image_id,
                "prompt": motion_prompt or "Cinematic motion, smooth camera movement, realistic animation",
                "frameInterpolation": True,  # Melhor qualidade
                "promptEnhance": True       # Otimização automática do prompt
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.leonardo_base_url}/generations-image-to-video",
                    headers=headers,
                    json=animation_data
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        generation_id = (
                            result.get('imageToVideoGenerationJob', {}).get('generationId') or
                            result.get('generationId') or
                            result.get('id')
                        )
                        logger.info("✅ Leonardo Image-to-Video criado com sucesso")
                        return {
                            'id': generation_id,
                            'jobId': generation_id
                        }
                    else:
                        error_text = await response.text()
                        logger.warning(f"⚠️ Image-to-Video falhou: {response.status} - {error_text}")
                        
                        # Fallback para SVD Motion se Image-to-Video não funcionar
                        logger.info("🔄 Tentando fallback para SVD Motion...")
                        return await self._create_leonardo_svd_motion(image_id, motion_prompt)
                        
        except Exception as e:
            logger.warning(f"⚠️ Erro Image-to-Video, tentando SVD: {e}")
            return await self._create_leonardo_svd_motion(image_id, motion_prompt)
            
        return None

    async def _create_leonardo_svd_motion(self, image_id: str, motion_prompt: str) -> Optional[Dict]:
        """Fallback: Cria animação SVD (método original)"""
        try:
            headers = {
                'Authorization': f'Bearer {self.leonardo_api_key}',
                'Content-Type': 'application/json'
            }
            
            # Payload para SVD Motion (método original)
            animation_data = {
                "imageId": image_id,
                "isInitImage": True,
                "isPublic": False,
                "motionStrength": 180,
                "isVariation": False
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.leonardo_base_url}/generations-motion-svd",
                    headers=headers,
                    json=animation_data
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info("✅ Leonardo SVD Motion criado com sucesso")
                        return {
                            'id': result.get('motionSvdGenerationJob', {}).get('generationId'),
                            'jobId': result.get('motionSvdGenerationJob', {}).get('generationId')
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Erro SVD Motion: {response.status} - {error_text}")
                        
        except Exception as e:
            logger.error(f"❌ Erro SVD Motion: {e}")
            
        return None

    async def _wait_and_download_animation(self, generation_id: str) -> Optional[str]:
        """Aguarda processamento e baixa a animação SVD"""
        try:
            headers = {
                'Authorization': f'Bearer {self.leonardo_api_key}'
            }
            
            # Aguardar até 120 segundos pelo processamento
            for i in range(24):  # 24 tentativas x 5 segundos = 120 segundos
                await asyncio.sleep(5)
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{self.leonardo_base_url}/generations/{generation_id}",
                        headers=headers
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            generations = result.get('generations_by_pk', {}).get('generated_images', [])
                            
                            if generations and len(generations) > 0:
                                generation = generations[0]
                                if generation.get('url'):
                                    # Baixar o vídeo gerado
                                    video_url = generation['url']
                                    return await self._download_and_save_video(video_url, "leonardo_animation")
                                    
                logger.info(f"🔄 Aguardando processamento Leonardo AI... ({i+1}/24)")
                
            logger.error("❌ Timeout aguardando animação Leonardo AI")
                
        except Exception as e:
            logger.error(f"❌ Erro ao aguardar animação Leonardo AI: {e}")
            
        return None

    async def _download_and_save_image(self, url: str, prefix: str) -> Optional[str]:
        """Baixa e salva imagem e retorna caminho absoluto salvo no disco"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{prefix}_{timestamp}.png"
            local_path = config.IMAGES_DIR / filename

            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        with open(local_path, 'wb') as f:
                            f.write(await response.read())

                        # Retornar caminho absoluto (mantém consistência com outros geradores)
                        return str(local_path)

        except Exception as e:
            logger.error(f"❌ Erro ao baixar imagem: {e}")

        return None

    async def _download_and_save_video(self, url: str, prefix: str) -> Optional[str]:
        """Baixa e salva vídeo"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{prefix}_{timestamp}.mp4"
            local_path = config.VIDEO_DIR / filename
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        with open(local_path, 'wb') as f:
                            f.write(await response.read())
                        
                        # Retornar caminho relativo para API
                        return f"/media/videos/{filename}"
                        
        except Exception as e:
            logger.error(f"❌ Erro ao baixar vídeo: {e}")
            
        return None

    def _adapt_prompt_for_dalle(self, prompt: str, style: str) -> str:
        """Adapta prompt para DALL-E 3"""
        style_prefixes = {
            "realistic": "Photorealistic, high quality, detailed",
            "cinematic": "Cinematic, dramatic lighting, film photography",
            "artistic": "Digital art, stylized, vibrant colors",
            "minimalist": "Clean, minimalist design, simple composition"
        }
        
        prefix = style_prefixes.get(style, style_prefixes["realistic"])
        
        # Garantir formato vertical para TikTok
        adapted_prompt = f"{prefix}, vertical format 9:16 aspect ratio, {prompt}"
        
        # Limitar tamanho do prompt para DALL-E 3
        if len(adapted_prompt) > 4000:
            adapted_prompt = adapted_prompt[:4000]
            
        return adapted_prompt

    async def create_leonardo_image_to_video(self, image_id: str, motion_prompt: str, is_generated: bool = True) -> Optional[str]:
        """Cria vídeo a partir de imagem usando o novo endpoint image-to-video do Leonardo AI"""
        if not self.leonardo_api_key:
            logger.error("❌ Leonardo AI não configurado")
            return None
            
        try:
            headers = {
                'accept': 'application/json',
                'authorization': f'Bearer {self.leonardo_api_key}',
                'content-type': 'application/json'
            }
            
            # Payload para o novo endpoint image-to-video
            payload = {
                "imageType": "GENERATED" if is_generated else "UPLOADED",
                "isPublic": False,
                "imageId": image_id,
                "prompt": motion_prompt,
                "frameInterpolation": True,  # Melhor qualidade de movimento
                "promptEnhance": True  # Melhora automática do prompt
            }
            
            logger.info(f"🎬 Criando vídeo Leonardo AI com novo endpoint: {motion_prompt[:50]}...")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.leonardo_base_url}/generations-image-to-video",
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        generation_id = result.get('motionSvdGenerationJob', {}).get('generationId')
                        
                        if generation_id:
                            logger.info(f"✅ Leonardo image-to-video iniciado: {generation_id}")
                            
                            # Aguardar processamento e baixar resultado
                            return await self._wait_and_download_animation(generation_id)
                            
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Erro no image-to-video Leonardo: {response.status} - {error_text}")
                        
        except Exception as e:
            logger.error(f"❌ Erro no Leonardo image-to-video: {e}")
            
        return None

    async def _store_image_metadata(self, image_path: str, image_id: str) -> None:
        """Armazena metadados da imagem Leonardo em arquivo JSON"""
        try:
            metadata_path = f"{image_path}.meta"
            metadata = {
                "image_id": image_id,
                "generated_at": datetime.now().isoformat(),
                "service": "leonardo_ai"
            }
            
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f)
                
            logger.debug(f"📝 Metadados Leonardo salvos: {image_id}")
            
        except Exception as e:
            logger.warning(f"⚠️ Erro ao salvar metadados Leonardo: {e}")

    async def _extract_image_id_from_path(self, image_path: str) -> Optional[str]:
        """Extrai o ID da imagem Leonardo baseado em metadados armazenados"""
        try:
            metadata_path = f"{image_path}.meta"
            
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                
                image_id = metadata.get("image_id")
                if image_id:
                    logger.debug(f"🔍 Image ID recuperado: {image_id}")
                    return image_id
                    
        except Exception as e:
            logger.debug(f"⚠️ Não foi possível recuperar image_id: {e}")
            
        return None

    def get_leonardo_motion_prompts(self) -> List[Dict[str, str]]:
        """Retorna prompts de movimento pré-definidos para Leonardo AI"""
        return [
            {
                "id": "subtle_movement",
                "name": "Movimento Sutil",
                "prompt": "movimento natural sutil, respiração suave, efeitos de vento leve, cores vibrantes"
            },
            {
                "id": "dynamic_zoom",
                "name": "Zoom Dinâmico",
                "prompt": "zoom dinâmico da câmera, movimento cinematográfico, mudança de foco em profundidade, cores intensas"
            },
            {
                "id": "floating_elements",
                "name": "Elementos Flutuantes",
                "prompt": "partículas flutuantes, atmosfera mágica, movimento etéreo, cores brilhantes e vibrantes"
            },
            {
                "id": "perspective_shift",
                "name": "Mudança de Perspectiva",
                "prompt": "transformação de perspectiva, rotação 3D, movimento espacial, cores vivas e coloridas"
            },
            {
                "id": "energy_pulse",
                "name": "Pulso de Energia",
                "prompt": "ondas de energia, luz pulsante, movimento rítmico, cores radiantes e vibrantes"
            }
        ]
