# leonardo_motion_client.py
# -*- coding: utf-8 -*-

"""
Cliente genérico para Leonardo Motion (image->video).

Fluxo:
  1) upload_image(image_path) -> retorna asset_id (ou url)
  2) create_motion_job(asset_id, prompt, duration, aspect_ratio) -> job_id
  3) poll_job(job_id) -> { status, video_url? }
  4) download_video(video_url, out_path)

Config:
  - LEONARDO_API_KEY via env var ou parâmetro
  - Endpoints podem mudar. Substitua os PLACEHOLDER_* pelos endpoints da sua conta.

Dependências:
  pip install requests
"""

import os
import time
import requests
from typing import Optional

class LeonardoMotionClient:
    def __init__(self, api_key: str, base_url: str = "https://cloud.leonardo.ai/api"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        })

    # ---------- 1) UPLOAD DE IMAGEM ----------
    def upload_image(self, image_path: str) -> str:
        """
        Sobe a image e retorna um 'asset_id' (ou URL) para usar no job.
        Substitua a rota abaixo pelo endpoint oficial de upload do Leonardo.
        """
        url = f"{self.base_url}/rest/v1/init-image"  # Endpoint atualizado
        files = {"file": open(image_path, "rb")}
        r = self.session.post(url, files=files, timeout=120)
        r.raise_for_status()
        data = r.json()
        # Ajuste conforme payload real:
        # Ex.: asset_id = data["data"]["id"]  ou  data["id"]  ou  data["url"]
        asset_id = data.get("id") or data.get("data", {}).get("id") or data.get("url")
        if not asset_id:
            raise RuntimeError(f"Upload sem id/url: {data}")
        return asset_id

    # ---------- 2) CRIAR JOB DE MOTION ----------
    def create_motion_job(
        self,
        asset_id_or_url: str,
        prompt: str,
        duration_sec: float,
        aspect_ratio: str = "9:16",
        model: Optional[str] = None
    ) -> str:
        """
        Cria o job de animação (image->video).
        Substitua a rota/payload pelo esquema oficial do Leonardo Motion.
        """
        url = f"{self.base_url}/rest/v1/generations-motion-svd"  # Endpoint atualizado para Motion SVD
        payload = {
            "imageId": asset_id_or_url,      # pode ser id ou url
            "motionStrength": 8,             # valor padrão para motion strength
            "isInitImagePublic": False
        }
        if model:
            payload["model"] = model

        r = self.session.post(url, json=payload, timeout=60)
        r.raise_for_status()
        data = r.json()
        job_id = data.get("generationId") or data.get("id") or data.get("job_id")
        if not job_id:
            raise RuntimeError(f"Create job sem id: {data}")
        return job_id

    # ---------- 3) POLL ----------
    def poll_job(self, job_id: str, poll_interval: float = 3.0, timeout: int = 600) -> dict:
        """
        Faz polling até concluir. Retorna o payload final (espera conter a URL do vídeo).
        Substitua a rota/campos abaixo conforme a API oficial.
        """
        url = f"{self.base_url}/rest/v1/generations/{job_id}"  # Endpoint atualizado
        t0 = time.time()
        while True:
            r = self.session.get(url, timeout=30)
            r.raise_for_status()
            data = r.json()

            # Para Leonardo AI, o status está na estrutura de generations
            generation = data.get("generations_by_pk", data)
            status = (generation.get("status") or "").upper()
            
            # Status do Leonardo: PENDING, PROCESSING, COMPLETE, FAILED
            if status in ("COMPLETE", "COMPLETED"):
                return data
            if status in ("FAILED", "ERROR"):
                raise RuntimeError(f"Job falhou: {data}")

            if time.time() - t0 > timeout:
                raise TimeoutError(f"Timeout polling job {job_id}")

            time.sleep(poll_interval)

    # ---------- 4) DOWNLOAD ----------
    def download_video(self, video_url: str, out_path: str) -> str:
        r = self.session.get(video_url, stream=True, timeout=300)
        r.raise_for_status()
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        with open(out_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        return out_path

    # ---------- 5) MÉTODO DE CONVENIÊNCIA ----------
    def image_to_motion(
        self,
        image_path: str,
        out_path: str,
        prompt: str = "slow cinematic zoom in, 9:16 vertical",
        duration_sec: float = 4.0,
        motion_strength: int = 8
    ) -> str:
        """
        Método completo: upload -> job -> poll -> download
        Retorna o caminho do vídeo salvo.
        """
        print(f"[Leonardo] Upload: {os.path.basename(image_path)}")
        asset_id = self.upload_image(image_path)
        
        print(f"[Leonardo] Creating motion job (strength: {motion_strength})")
        job_id = self.create_motion_job(
            asset_id_or_url=asset_id,
            prompt=prompt,
            duration_sec=duration_sec
        )
        
        print(f"[Leonardo] Polling job: {job_id}")
        result = self.poll_job(job_id)
        
        # Extrair URL do vídeo do resultado
        generation = result.get("generations_by_pk", result)
        generated_videos = generation.get("generated_videos", [])
        
        if not generated_videos:
            raise RuntimeError(f"No video generated: {result}")
            
        video_url = generated_videos[0].get("url")
        if not video_url:
            raise RuntimeError(f"No video URL in result: {result}")
        
        print(f"[Leonardo] Downloading: {out_path}")
        return self.download_video(video_url, out_path)


# ---------- FUNÇÃO DE CONVENIÊNCIA ----------
def leonardo_animate_image(
    image_path: str,
    out_path: str,
    api_key: str,
    motion_strength: int = 8,
    prompt: str = "slow cinematic zoom in"
) -> str:
    """
    Função simples para animar uma imagem.
    """
    client = LeonardoMotionClient(api_key)
    return client.image_to_motion(
        image_path=image_path,
        out_path=out_path,
        prompt=prompt,
        motion_strength=motion_strength
    )


if __name__ == "__main__":
    # Teste rápido
    import sys
    if len(sys.argv) < 4:
        print("Uso: python leonardo_motion_client.py <image_path> <out_path> <api_key>")
        sys.exit(1)
    
    image_path, out_path, api_key = sys.argv[1:4]
    result = leonardo_animate_image(image_path, out_path, api_key)
    print(f"✅ Vídeo gerado: {result}")
