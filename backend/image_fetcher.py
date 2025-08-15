# image_fetcher.py
# -*- coding: utf-8 -*-

"""
Gera images/scene_XX.png     payload = {
        "model": "dall-e-3",
        "prompt": prompt,
        "size": size,  # "1024x1024", "1024x1792" (vertical), "1792x1024" (horizontal)
        "response_format": "b64_json"
    }r de um storyboard JSON com "scenes[*].image_prompt".

Suporta 3 providers (via --provider):
  - openai      -> GPT-Image-1 (Images API)  [Docs: https://platform.openai.com/docs/guides/image-generation ]
  - google      -> Imagen (Gemini/Vertex AI) [Docs: https://ai.google.dev/gemini-api/docs/imagen , https://cloud.google.com/vertex-ai/generative-ai/docs/image/generate-images ]
  - leonardo    -> Leonardo Generations      [Docs: https://docs.leonardo.ai/reference/creategeneration ]

Uso:
  python image_fetcher.py \
    --storyboard /path/storyboard.json \
    --outdir /path/images \
    --provider openai \
    --ar 9:16 \
    --size 1024x1792 \
    --openai-key sk-... \
    [--google-key AI... ou GOOGLE_APPLICATION_CREDENTIALS=/path/key.json] \
    [--leonardo-key <token>]

Observações:
- 9:16 preferido para Shorts; mapeio tamanhos válidos automaticamente por provider.
- Cache: não rebaixa se images/scene_XX.png já existir.
"""

import os, io, json, base64, time, argparse
from typing import Dict, Any, List, Optional

import requests
from dotenv import load_dotenv

# Carregar variáveis de ambiente do .env
load_dotenv()

# =========================
# Helpers
# =========================

def ensure_dir(p: str):
    os.makedirs(p, exist_ok=True)

def read_storyboard(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def pick_scene_prompts(data: Dict[str, Any]) -> List[str]:
    scenes = data.get("scenes") or data.get("storyboard") or []
    prompts = []
    for s in scenes:
        p = (s.get("image_prompt") or "").strip()
        prompts.append(p)
    return prompts

def save_png_bytes(out_path: str, b: bytes):
    ensure_dir(os.path.dirname(out_path) or ".")
    with open(out_path, "wb") as f:
        f.write(b)
    return out_path

# =========================
# Provider: OpenAI (GPT-Image-1 / DALL·E)
# Docs: https://platform.openai.com/docs/guides/image-generation
# Models/sizes: gpt-image-1 aceita 1024x1024, 1024x1792, 1792x1024 (vertical/horizontal) [docs]
# =========================

def openai_generate_image(prompt: str, api_key: str, size: str = "1024x1792") -> bytes:
    """
    OpenAI Images API (dall-e-3).
    Retorna bytes PNG.
    """
    print(f"DEBUG: API Key recebida: {api_key[:20]}..." if api_key else "DEBUG: API Key é None")
    
    url = "https://api.openai.com/v1/images/generations"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": "dall-e-3",
        "prompt": prompt,
        "size": size,  # "1024x1024", "1024x1792" (vertical), "1792x1024" (horizontal)
        "response_format": "b64_json"
    }
    r = requests.post(url, headers=headers, json=payload, timeout=180)
    r.raise_for_status()
    data = r.json()
    b64 = data["data"][0]["b64_json"]
    return base64.b64decode(b64)

# =========================
# Provider: Google Imagen (Gemini/Vertex)
# Docs (Gemini API Imagen): https://ai.google.dev/gemini-api/docs/imagen
# Docs (Vertex Imagen):     https://cloud.google.com/vertex-ai/generative-ai/docs/image/generate-images
# Aqui, deixo uma implementação REST simples usando Gemini API Key (ai.google.dev).
# Se você usa Vertex, troque o endpoint por REST Vertex AI.
# =========================

def google_imagen_generate_image(prompt: str, api_key: str, size: str = "1024x1792") -> bytes:
    """
    Usa Gemini Imagen endpoint (ai.google.dev) para gerar imagem e retorna PNG bytes.
    NOTA: o endpoint/forma pode variar por região/conta. Ajuste se necessário.
    """
    # Endpoint de exemplo (Gemini Imagen). Em algumas contas, pode ser diferente/precisar OAuth.
    url = f"https://generativelanguage.googleapis.com/v1beta/images:generate?key={api_key}"
    # Alguns endpoints aceitam "mimeType" e "width/height". Se não aceitar "size", ajusta manual.
    # Fallback: pedir portrait 9:16 por texto.
    body = {
        "prompt": {
            "text": f"{prompt} -- aspect ratio 9:16, portrait vertical"
        },
        "cfgScale": 7  # leve guia
    }
    r = requests.post(url, json=body, timeout=180)
    r.raise_for_status()
    data = r.json()
    # A resposta costuma vir como base64 PNG/JPEG em "images[0].data"
    # Ajustar caso seu payload venha diferente (consulte sua conta).
    images = data.get("images") or data.get("candidates") or []
    if not images:
        raise RuntimeError(f"Imagen response sem 'images': {data}")
    # tentativa comum:
    b64 = images[0].get("data") or images[0].get("image", {}).get("data")
    if not b64:
        raise RuntimeError(f"Imagen sem 'data' base64: {images[0]}")
    return base64.b64decode(b64)

# =========================
# Provider: Leonardo (Generations)
# Docs: https://docs.leonardo.ai/reference/creategeneration
# =========================

def leonardo_generate_image(prompt: str, api_key: str, size: str = "1024x1792") -> bytes:
    """
    Cria uma geração no Leonardo e baixa a primeira saída como PNG.
    size: Leonardo geralmente recebe guidance de aspecto via prompt e/ou params próprios (width/height).
    """
    # 1) criar geração
    gen_url = "https://cloud.leonardo.ai/api/rest/v1/generations"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    # Mapeamento de tamanho simples (ajuste conforme plano/modelo)
    if size == "1024x1792":
        width, height = 1024, 1792
    elif size == "1792x1024":
        width, height = 1792, 1024
    else:
        width, height = 1024, 1024

    payload = {
        "height": height,
        "width": width,
        "prompt": prompt,
        # "modelId": "...",  # opcional: Phoenix/Kino XL etc (se quiser travar um modelo)
        "num_images": 1,
        "presetStyle": "DYNAMIC"  # opcional
    }
    r = requests.post(gen_url, headers=headers, json=payload, timeout=60)
    r.raise_for_status()
    job = r.json()
    gen_id = job.get("sdGenerationJob", {}).get("generationId") or job.get("generationId") or job.get("id")
    if not gen_id:
        raise RuntimeError(f"Geração sem generationId: {job}")

    # 2) poll
    status_url = f"https://cloud.leonardo.ai/api/rest/v1/generations/{gen_id}"
    for _ in range(120):
        rs = requests.get(status_url, headers=headers, timeout=30)
        rs.raise_for_status()
        info = rs.json()
        # Os campos variam; normalmente vem em "generations_by_pk" ou "data"
        outs = (info.get("generations_by_pk", {}).get("generated_images")
                or info.get("data", {}).get("images")
                or info.get("images")
                or [])
        if outs:
            # 3) baixa a URL da primeira imagem (normalmente .png)
            url = outs[0].get("url") or outs[0].get("imageUrl")
            if not url:
                raise RuntimeError(f"Saída sem URL: {outs[0]}")
            img = requests.get(url, timeout=180)
            img.raise_for_status()
            return img.content
        time.sleep(2)

    raise TimeoutError(f"Leonardo geração {gen_id} não concluiu a tempo.")

# =========================
# Orquestrador
# =========================

def fetch_images_for_storyboard(
    storyboard_path: str,
    outdir: str,
    provider: str,
    size: str = "1024x1792",
    ar_hint: str = "9:16",
    openai_key: Optional[str] = None,
    google_key: Optional[str] = None,
    leonardo_key: Optional[str] = None,
    overwrite: bool = False
):
    data = read_storyboard(storyboard_path)
    prompts = pick_scene_prompts(data)

    ensure_dir(outdir)
    total = len(prompts)

    for i, prompt in enumerate(prompts, start=1):
        out_path = os.path.join(outdir, f"scene_{i:02d}.png")
        if os.path.exists(out_path) and not overwrite:
            print(f"[CACHE] {out_path}")
            continue

        if not prompt:
            print(f"[SKIP] Cena {i} sem image_prompt.")
            continue

        # reforço leve de AR se o provider ignorar size
        prompt_eff = prompt
        if ar_hint and "9:16" in ar_hint and "vertical 9:16" not in prompt.lower():
            prompt_eff += ", vertical 9:16"

        print(f"[GEN] Cena {i}/{total} via {provider} size={size}")
        if provider == "openai":
            if not openai_key:
                raise ValueError("--openai-key requerido")
            png = openai_generate_image(prompt_eff, api_key=openai_key, size=size)
        elif provider == "google":
            if not google_key:
                raise ValueError("--google-key requerido")
            png = google_imagen_generate_image(prompt_eff, api_key=google_key, size=size)
        elif provider == "leonardo":
            if not leonardo_key:
                raise ValueError("--leonardo-key requerido")
            png = leonardo_generate_image(prompt_eff, api_key=leonardo_key, size=size)
        else:
            raise ValueError("provider inválido. Use: openai | google | leonardo")

        save_png_bytes(out_path, png)
        print(f"[OK] {out_path}")

# =========================
# CLI
# =========================

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Gerador de imagens por cena (OpenAI / Google Imagen / Leonardo)")
    ap.add_argument("--storyboard", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--provider", required=True, choices=["openai", "google", "leonardo"])
    ap.add_argument("--size", default="1024x1792", help="1024x1792 (vertical), 1792x1024 (horizontal) ou 1024x1024")
    ap.add_argument("--ar", default="9:16")
    ap.add_argument("--openai-key", default=os.getenv("OPENAI_API_KEY"))
    ap.add_argument("--google-key", default=os.getenv("GOOGLE_API_KEY"))   # Gemini (ai.google.dev)
    ap.add_argument("--leonardo-key", default=os.getenv("LEONARDO_API_KEY"))
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    fetch_images_for_storyboard(
        storyboard_path=args.storyboard,
        outdir=args.outdir,
        provider=args.provider,
        size=args.size,
        ar_hint=args.ar,
        openai_key=args.openai_key,
        google_key=args.google_key,
        leonardo_key=args.leonardo_key,
        overwrite=args.overwrite
    )
