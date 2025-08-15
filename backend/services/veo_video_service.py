import os
import io
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from config_manager import get_config

logger = logging.getLogger(__name__)
config = get_config()


class VeoVideoService:
    """Serviço para geração de vídeo a partir de imagem usando Vertex AI Veo 2.

    Estratégia:
    - Tenta usar o SDK do Vertex AI (google-cloud-aiplatform / vertexai.preview.vision_models.VideoGenerationModel).
    - Caso falhe (SDK indisponível), tenta REST Google AI Studio se API key existir.
    - Salva sempre em MEDIA_DIR/videos e retorna URL /media/videos/<arquivo>.

    Observação: O modelo é configurável via env VEO_MODEL (padrão: "veo-2.0").
    """

    def __init__(self) -> None:
        self.vertex_available = False
        self.api_key_available = bool(getattr(config, 'VERTEX_AI_API_KEY', None))
        # Vertex SDK model name (commonly "veo-2.0"). For Google AI Studio, use 'veo-2.0-generate-001'.
        self.model_name = os.getenv('VEO_MODEL', 'veo-2.0')

        # Garante diretório de vídeos
        try:
            Path(config.VIDEO_DIR).mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

        self._setup_vertex_ai()

    def _setup_vertex_ai(self) -> None:
        try:
            import vertexai  # type: ignore
            project = getattr(config, 'GOOGLE_PROJECT_ID', None)
            location = getattr(config, 'GOOGLE_LOCATION', 'us-central1')
            if project:
                vertexai.init(project=project, location=location)
                self.vertex_available = True
                logger.info("✅ Vertex AI inicializado para Veo 2")
            else:
                logger.warning("⚠️ GOOGLE_PROJECT_ID ausente; Veo 2 via SDK desativado")
        except Exception as e:
            logger.warning(f"⚠️ SDK Vertex AI indisponível para Veo 2: {e}")
            self.vertex_available = False

    def _normalize_media_path(self, image_path: str) -> str:
        # Converte /media/... para caminho local
        if image_path.startswith('/media/'):
            rel = image_path[len('/media/'):]
            return str(Path(config.MEDIA_DIR) / rel)
        return image_path

    def _save_video_bytes(self, data: bytes, prefix: str = "veo2") -> str:
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{prefix}_{ts}.mp4"
        out_path = Path(config.VIDEO_DIR) / filename
        with open(out_path, 'wb') as f:
            f.write(data)
        return f"/media/videos/{filename}"

    def image_to_video(self, image_path: str, prompt: str, duration_seconds: int = 3, aspect_ratio: str = "16:9") -> str:
        local_image = self._normalize_media_path(image_path)
        logger.info(f"Veo 2 ▶️ image_to_video(img={local_image}, dur={duration_seconds}, ar={aspect_ratio})")

        # 1) Tentativa via SDK Vertex
        if self.vertex_available:
            try:
                from vertexai.preview.vision_models import VideoGenerationModel  # type: ignore
                # Tentar múltiplos namespaces para Image
                v_image = None
                try:
                    from vertexai.preview.vision_models import Image as VertexImage  # type: ignore
                    if hasattr(VertexImage, 'load_from_file'):
                        v_image = VertexImage.load_from_file(local_image)
                    elif hasattr(VertexImage, 'from_file'):
                        v_image = VertexImage.from_file(local_image)
                except Exception as e:
                    logger.warning(f"Veo 2: Image helper preview falhou: {e}")
                    try:
                        from vertexai.vision_models import Image as VertexImage2  # type: ignore
                        if hasattr(VertexImage2, 'load_from_file'):
                            v_image = VertexImage2.load_from_file(local_image)
                        elif hasattr(VertexImage2, 'from_file'):
                            v_image = VertexImage2.from_file(local_image)
                    except Exception as e2:
                        logger.warning(f"Veo 2: Image helper alt falhou: {e2}")

                model = VideoGenerationModel.from_pretrained(self.model_name)

                # A assinatura pode variar. Tentamos parâmetros comuns.
                try:
                    response = model.generate_video(
                        prompt=prompt,
                        images=[v_image] if v_image is not None else None,
                        duration=duration_seconds,
                        aspect_ratio=aspect_ratio,
                    )
                except TypeError:
                    # Fallback alternativo de nomes de parâmetros
                    response = model.generate_video(
                        prompt=prompt,
                        input_images=[v_image] if v_image is not None else None,
                        duration_seconds=duration_seconds,
                        aspect_ratio=aspect_ratio,
                    )

                # Extrair bytes do vídeo
                video_bytes = None
                if hasattr(response, 'video_bytes') and response.video_bytes:
                    video_bytes = response.video_bytes
                elif hasattr(response, 'video') and isinstance(response.video, (bytes, bytearray)):
                    video_bytes = bytes(response.video)
                elif hasattr(response, 'videos') and response.videos:
                    # alguns retornos podem trazer lista de vídeos
                    first = response.videos[0]
                    if isinstance(first, (bytes, bytearray)):
                        video_bytes = bytes(first)
                    elif hasattr(first, 'bytes'):
                        video_bytes = first.bytes

                if video_bytes:
                    return self._save_video_bytes(video_bytes, prefix="veo2")

                # Alguns SDKs oferecem método save diretamente
                if hasattr(response, 'save'):
                    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"veo2_{ts}.mp4"
                    out_path = Path(config.VIDEO_DIR) / filename
                    response.save(str(out_path))
                    return f"/media/videos/{filename}"

                logger.warning("⚠️ Resposta do Veo 2 sem bytes ou método save detectável")
            except Exception as e:
                logger.warning(f"⚠️ Falha na geração Veo 2 via SDK: {e}")

        # 2) Fallback Google AI Studio via biblioteca google.genai com operações assíncronas
        if self.api_key_available:
            try:
                import time
                from google import genai  # type: ignore
                from google.genai import types as genai_types  # type: ignore
                
                client = genai.Client(api_key=config.VERTEX_AI_API_KEY)
                
                # Preparar imagem como objeto File
                with open(local_image, 'rb') as f:
                    img_data = f.read()
                
                # Usar Veo 3 (mais recente) como primeira tentativa, depois Veo 2
                for model_id in ['veo-3.0-generate-preview', 'veo-2.0-generate-001']:
                    try:
                        logger.info(f"Tentando {model_id}...")
                        
                        # Para Veo 3: suporte a imagem como parâmetro image
                        if model_id.startswith('veo-3'):
                            # Veo 3 usa image= e config=
                            imagen_file = genai_types.Part.from_bytes(data=img_data, mime_type="image/png")
                            config_obj = genai_types.GenerateVideosConfig(aspect_ratio=aspect_ratio)
                            
                            operation = client.models.generate_videos(
                                model=model_id,
                                prompt=prompt,
                                image=imagen_file,
                                config=config_obj,
                            )
                        else:
                            # Veo 2 pode usar diferentes parâmetros
                            imagen_file = genai_types.Part.from_bytes(data=img_data, mime_type="image/png")
                            operation = client.models.generate_videos(
                                model=model_id,
                                prompt=prompt,
                                image=imagen_file,
                            )
                        
                        # Aguardar operação assíncrona (polling)
                        max_wait = 300  # 5 minutos
                        start_time = time.time()
                        while not operation.done and (time.time() - start_time) < max_wait:
                            logger.info(f"Aguardando {model_id}... ({int(time.time() - start_time)}s)")
                            time.sleep(10)
                            operation = client.operations.get(operation)
                        
                        if operation.done and hasattr(operation, 'response'):
                            # Extrair vídeo gerado
                            generated_videos = operation.response.generated_videos
                            if generated_videos and len(generated_videos) > 0:
                                video_obj = generated_videos[0].video
                                # Baixar usando client.files.download
                                video_bytes = client.files.download(file=video_obj)
                                if video_bytes:
                                    return self._save_video_bytes(video_bytes, prefix=f"veo_{model_id.split('-')[1]}")
                        else:
                            logger.warning(f"⚠️ {model_id}: operação não finalizou ou sem resposta")
                    except Exception as model_e:
                        error_msg = str(model_e).lower()
                        if "quota" in error_msg or "rate" in error_msg or "limit" in error_msg:
                            logger.error(f"⚠️ {model_id}: Quota ou rate limit excedido - {model_e}")
                        elif "permission" in error_msg or "forbidden" in error_msg:
                            logger.error(f"⚠️ {model_id}: Permissões insuficientes - {model_e}")
                        else:
                            logger.warning(f"⚠️ Falha {model_id}: {model_e}")
                        continue  # Tentar próximo modelo
                        
            except Exception as e:
                logger.warning(f"⚠️ Falha geral na geração Veo via google.genai: {e}")

        # 3) Fallback REST Google AI Studio (modelo generate-001). A API/endpoint pode variar por versão.
        if self.api_key_available:
            try:
                import base64
                import requests
                with open(local_image, 'rb') as f:
                    img_b64 = base64.b64encode(f.read()).decode('utf-8')

                url = "https://generativelanguage.googleapis.com/v1/models/veo-2.0-generate-001:generateVideo"
                headers = {"Content-Type": "application/json", "x-goog-api-key": config.VERTEX_AI_API_KEY}
                payload = {
                    "prompt": {"text": prompt},
                    "config": {"durationSeconds": duration_seconds, "aspectRatio": aspect_ratio},
                    "inputs": [{"image": {"mimeType": "image/png", "bytes": img_b64}}]
                }
                r = requests.post(url, headers=headers, data=json.dumps(payload), timeout=180)
                if r.status_code == 200:
                    data = r.json()
                    # Heurísticas de onde o vídeo pode vir (dependente da versão da API)
                    video_b64 = (
                        data.get('video', {}).get('bytes')
                        or (data.get('videos')[0].get('bytes') if isinstance(data.get('videos'), list) and data['videos'] else None)
                        or data.get('videoBytes')
                    )
                    if video_b64:
                        return self._save_video_bytes(base64.b64decode(video_b64), prefix="veo2")
                    # Alguns retornos podem trazer URL assinada
                    video_url = data.get('video', {}).get('uri') or data.get('videoUri')
                    if video_url:
                        vr = requests.get(video_url, timeout=180)
                        if vr.status_code == 200:
                            return self._save_video_bytes(vr.content, prefix="veo2")
                else:
                    logger.warning(f"Veo REST falhou {r.status_code}: {r.text[:200]}")
                    if r.status_code == 429:
                        logger.error("⚠️ Rate limit excedido na API Veo")
                    elif r.status_code == 403:
                        logger.error("⚠️ Quota excedida ou permissões insuficientes na API Veo")
            except Exception as e:
                logger.warning(f"⚠️ Falha na geração Veo 2 via REST: {e}")

        logger.error("❌ Veo: não foi possível gerar vídeo - todas as tentativas falharam")
        logger.info("💡 Possíveis causas: quota excedida, rate limit, API em manutenção ou modelo indisponível")
        raise Exception("Veo API indisponível - quota excedida ou rate limit atingido. Tente novamente mais tarde.")
