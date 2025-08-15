#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# render_pipeline.py
# -*- coding: utf-8 -*-

"""
Pipeline áudio-dirigido:
1) Storyboard JSON
2) ElevenLabs TTS por cena -> pega duração real do áudio
3) Leonardo Motion (image->video) usando a duração do áudio
4) Montagem MoviePy (9:16, 30fps), sem speedx

Requisitos:
  pip install moviepy requests

Obs: troque os endpoints do Leonardo no cliente (ver comentário no código do cliente).
"""

import os
import sys
import json
import argparse
import time
import hashlib
from typing import Dict, List, Any, Optional
from pathlib import Path

# MoviePy imports with compatibility
try:
    from moviepy.editor import (
        VideoFileClip, AudioFileClip, CompositeVideoClip, CompositeAudioClip,
        concatenate_videoclips, ColorClip, TextClip, vfx
    )
    MOVIEPY_VERSION = 2  # Assume version 2.x
except ImportError:
    from moviepy.editor import (
        VideoFileClip, AudioFileClip, CompositeVideoClip, CompositeAudioClip,
        concatenate_videoclips, ColorClip, TextClip
    )
    from moviepy.video import fx as vfx
    MOVIEPY_VERSION = 1

# Leonardo Motion Client
try:
    from leonardo_motion_client import LeonardoMotionClient
    LEONARDO_AVAILABLE = True
except ImportError:
    LEONARDO_AVAILABLE = False
    print("[WARN] Leonardo Motion Client não disponível")

# =========================
# CONFIGS DE VÍDEO/ÁUDIO
# =========================
TARGET_W, TARGET_H, FPS = 1080, 1920, 30
CROSSFADE_S = 0.20           # crossfade leve entre cenas (0 = corte seco)
DEFAULT_MUSIC_VOL = 0.25     # volume de música de fundo
ALLOW_SPEED_ADJUST = True    # ajustar levemente a velocidade do vídeo para casar a duração

EXPORT_OPTS = dict(
    fps=FPS,
    codec="libx264",
    audio_codec="aac",
    audio_bitrate="192k",
    preset="medium",
    bitrate="8000k",
    threads=4,
    temp_audiofile="temp-audio.m4a",
    remove_temp=True
)

# =========================
# ELEVENLABS (TTS)
# =========================
import requests

ELEVEN_TTS_URL_FMT = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
ELEVEN_MODEL_ID = "eleven_multilingual_v2"  # geralmente funciona muito bem em PT-BR

def _hash_text(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:10]

def elevenlabs_tts(
    text: str,
    voice_id: str,
    api_key: str,
    out_path: str,
    audio_format: str = "mp3",
    stability: float = 0.35,
    similarity_boost: float = 0.85,
    style: float = 0.0,
    use_speaker_boost: bool = True,
    model_id: str = ELEVEN_MODEL_ID,
    timeout: int = 60,
    retries: int = 2,
    backoff_sec: float = 2.0
) -> str:
    """
    Gera TTS (mp3/wav) no ElevenLabs para texto em PT-BR.
    Salva o arquivo em out_path e retorna o caminho.
    """
    if not text or not text.strip():
        raise ValueError("Texto TTS vazio.")

    url = ELEVEN_TTS_URL_FMT.format(voice_id=voice_id)
    headers = {
        "xi-api-key": api_key,
        "accept": f"audio/{'mpeg' if audio_format=='mp3' else 'wav'}",
        "Content-Type": "application/json",
    }
    payload = {
        "text": text,
        "model_id": model_id,
        "voice_settings": {
            "stability": stability,
            "similarity_boost": similarity_boost,
            "style": style,
            "use_speaker_boost": use_speaker_boost
        }
    }

    last_err = None
    for attempt in range(retries + 1):
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=timeout)
            if r.status_code != 200:
                raise RuntimeError(f"ElevenLabs TTS falhou ({r.status_code}): {r.text[:300]}")
            os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
            with open(out_path, "wb") as f:
                f.write(r.content)
            return out_path
        except Exception as e:
            last_err = e
            if attempt < retries:
                time.sleep(backoff_sec * (2 ** attempt))
            else:
                raise last_err

# =========================
# MOVIEPY (MONTAGEM)
# =========================

def _fit_vertical(clip: VideoFileClip) -> VideoFileClip:
    """Garante 1080x1920 (9:16)."""
    c = clip.set_fps(FPS)
    if c.h != TARGET_H:
        c = c.resize(height=TARGET_H)
    if c.w != TARGET_W:
        c = c.resize(width=TARGET_W)
    return c

def _scene_duration(scene: Dict[str, Any]) -> float:
    t0, t1 = float(scene["t_start"]), float(scene["t_end"])
    return max(0.1, round(t1 - t0, 3))

def build_scene_clip(scene_idx: int, scene_meta: Dict[str, Any], assets_dir: str) -> VideoFileClip:
    """
    Carrega scene_{i:02d}.mp4 e scene_{i:02d}.mp3/wav (se existir),
    ajusta ao tempo da cena e retorna o VideoFileClip com áudio sincronizado.
    """
    dur = _scene_duration(scene_meta)
    base = f"scene_{scene_idx:02d}"

    vpath = os.path.join(assets_dir, f"{base}.mp4")
    if not os.path.exists(vpath):
        raise FileNotFoundError(f"Vídeo da cena {scene_idx} não encontrado: {vpath}")

    v = _fit_vertical(VideoFileClip(vpath))

    # Ajuste de duração do vídeo
    if v.duration > dur:
        v = v.subclip(0, dur)
    elif v.duration < dur and ALLOW_SPEED_ADJUST:
        factor = max(0.1, v.duration / dur)  # <1 = slow motion
        if MOVIEPY_VERSION >= 2:
            v = v.with_fps(v.fps).with_duration(dur)
        else:
            v = v.fx(vfx.speedx, factor=factor)
        if v.duration > dur:  # aparar sobra mínima
            v = v.subclip(0, dur)

    # Procura áudio (prefere .mp3; senão .wav)
    apath_mp3 = os.path.join(assets_dir, f"{base}.mp3")
    apath_wav = os.path.join(assets_dir, f"{base}.wav")
    apath = apath_mp3 if os.path.exists(apath_mp3) else (apath_wav if os.path.exists(apath_wav) else None)

    if apath:
        a = AudioFileClip(apath)
        if a.duration > dur:
            a = a.subclip(0, dur)
        if MOVIEPY_VERSION >= 2:
            v = v.with_audio(a)
        else:
            v = v.set_audio(a)

    return v

# =========================
# LEONARDO MOTION INTEGRATION
# =========================

def ensure_motion_clips(
    storyboard: Dict[str, Any],
    assets_dir: str,
    images_dir: str,
    leonardo_key: str
):
    """
    Para cada cena, se não existir scene_XX.mp4:
      - procura scene_XX.(png|jpg|jpeg) em images_dir
      - upload -> create job -> poll -> download scene_XX.mp4
      - duração = t_end - t_start
      - motion_prompt = scene["motion_prompt"] ou padrão
    """
    if not LEONARDO_AVAILABLE:
        raise RuntimeError("Leonardo Motion Client não está disponível")
        
    client = LeonardoMotionClient(api_key=leonardo_key)

    scenes = storyboard.get("scenes") or storyboard.get("storyboard") or []
    if not scenes:
        raise ValueError("Storyboard sem scenes.")

    os.makedirs(assets_dir, exist_ok=True)

    for i, s in enumerate(scenes, start=1):
        vpath = os.path.join(assets_dir, f"scene_{i:02d}.mp4")
        if os.path.exists(vpath):
            print(f"[MOTION] Cena {i}: vídeo já existe, pulando")
            continue

        # Procurar imagem base
        img = None
        for ext in ("png", "jpg", "jpeg", "webp"):
            cand = os.path.join(images_dir, f"scene_{i:02d}.{ext}")
            if os.path.exists(cand):
                img = cand
                break
        if not img:
            # Tentar scene_1, scene_2 (sem zero padding)
            for ext in ("png", "jpg", "jpeg", "webp"):
                cand = os.path.join(images_dir, f"scene_{i}.{ext}")
                if os.path.exists(cand):
                    img = cand
                    break
        
        if not img:
            raise FileNotFoundError(
                f"Imagem da cena {i} não encontrada em {images_dir}/scene_{i:02d}.(png|jpg|jpeg|webp)"
            )

        print(f"[MOTION] Cena {i}: processando {os.path.basename(img)}")
        
        motion_prompt = s.get("motion_prompt") or "slow cinematic zoom in, 9:16 vertical"
        duration = _scene_duration(s)
        
        try:
            client.image_to_motion(
                image_path=img,
                out_path=vpath,
                prompt=motion_prompt,
                duration_sec=duration
            )
            print(f"[MOTION] Cena {i}: ✅ salvo em {vpath}")
        except Exception as e:
            print(f"[MOTION] Cena {i}: ❌ erro: {e}")
            raise

def assemble_video(
    storyboard: Dict[str, Any],
    assets_dir: str,
    out_path: str,
    music_path: Optional[str] = None,
    crossfade_s: float = CROSSFADE_S
) -> str:
    """
    Monta o vídeo final a partir das cenas em assets_dir
    """
    scenes = storyboard.get("scenes") or storyboard.get("storyboard")
    if not scenes:
        raise ValueError("Storyboard sem 'scenes' (ou 'storyboard').")

    clips = []
    for i, s in enumerate(scenes, start=1):
        clip = build_scene_clip(i, s, assets_dir)
        if clips and crossfade_s > 0:
            if MOVIEPY_VERSION >= 2:
                clip = clip.with_start(clips[-1].end - crossfade_s).crossfadein(crossfade_s)
            else:
                clip = clip.crossfadein(crossfade_s)
        clips.append(clip)

    if MOVIEPY_VERSION >= 2:
        final = concatenate_videoclips(clips, method="compose").with_fps(FPS)
    else:
        final = concatenate_videoclips(
            clips,
            method="compose",
            padding=(-crossfade_s if crossfade_s > 0 else 0)
        ).set_fps(FPS)

    # Música de fundo opcional
    if music_path and os.path.exists(music_path):
        try:
            music = AudioFileClip(music_path)
            if MOVIEPY_VERSION >= 2:
                music = music.with_volume_multiplied(DEFAULT_MUSIC_VOL).with_start(0).with_duration(final.duration)
            else:
                music = music.volumex(DEFAULT_MUSIC_VOL).set_start(0).set_duration(final.duration)
                
            final_audio = final.audio
            if final_audio:
                mixed = CompositeAudioClip([final_audio, music])
            else:
                mixed = CompositeAudioClip([music])
            
            if MOVIEPY_VERSION >= 2:
                final = final.with_audio(mixed)
            else:
                final = final.set_audio(mixed)
        except Exception as e:
            print(f"[WARN] Falha ao mixar música: {e}")

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    print(f"[EXPORT] Exportando para {out_path}")
    final.write_videofile(out_path, **EXPORT_OPTS)
    return out_path

# =========================
# TTS GENERATION
# =========================

def generate_tts_per_scene_if_needed(
    storyboard: Dict[str, Any],
    assets_dir: str,
    voice_id: str,
    elevenlabs_api_key: str,
    audio_format: str = "mp3"
):
    """
    Para cada cena, gera TTS da 'narration' se o arquivo de áudio não existir.
    """
    scenes = storyboard.get("scenes") or storyboard.get("storyboard")
    if not scenes:
        raise ValueError("Storyboard sem 'scenes' (ou 'storyboard').")

    os.makedirs(assets_dir, exist_ok=True)

    for i, s in enumerate(scenes, start=1):
        base = f"scene_{i:02d}"
        out_path = os.path.join(assets_dir, f"{base}.{audio_format}")
        if os.path.exists(out_path):
            print(f"[TTS] Cena {i}: áudio já existe, pulando")
            continue
            
        text = (s.get("narration") or "").strip()
        if not text:
            print(f"[TTS] Cena {i}: sem narração, pulando")
            continue
            
        print(f"[TTS] Cena {i}: gerando ({len(text)} chars)")
        elevenlabs_tts(
            text=text,
            voice_id=voice_id,
            api_key=elevenlabs_api_key,
            out_path=out_path,
            audio_format=audio_format
        )

# =========================
# FUNÇÃO PRINCIPAL
# =========================

def load_storyboard(storyboard_path_or_dict) -> Dict[str, Any]:
    if isinstance(storyboard_path_or_dict, dict):
        return storyboard_path_or_dict
    with open(storyboard_path_or_dict, "r", encoding="utf-8") as f:
        return json.load(f)

def render_from_storyboard(
    storyboard_path_or_dict,
    assets_dir: str,
    out_path: str,
    eleven_voice_id: Optional[str] = None,
    eleven_api_key: Optional[str] = None,
    audio_format: str = "mp3",
    music_path: Optional[str] = None,
    leonardo_key: Optional[str] = None,
    images_dir: Optional[str] = None,
    gen_motion: bool = False
) -> str:
    """
    Função única: carrega storyboard -> gera TTS por cena -> gera motion -> monta vídeo -> exporta MP4.
    """
    storyboard = load_storyboard(storyboard_path_or_dict)

    # (1) Gerar TTS por cena (se informado)
    if eleven_voice_id and eleven_api_key:
        print("[PIPELINE] Gerando TTS...")
        generate_tts_per_scene_if_needed(
            storyboard=storyboard,
            assets_dir=assets_dir,
            voice_id=eleven_voice_id,
            elevenlabs_api_key=eleven_api_key,
            audio_format=audio_format
        )

    # (2) Gerar Motion (se habilitado)
    if gen_motion and leonardo_key and images_dir:
        print("[PIPELINE] Gerando motion clips...")
        ensure_motion_clips(
            storyboard=storyboard,
            assets_dir=assets_dir,
            images_dir=images_dir,
            leonardo_key=leonardo_key
        )

    # (3) Montar vídeo final
    print("[PIPELINE] Montando vídeo final...")
    return assemble_video(
        storyboard=storyboard,
        assets_dir=assets_dir,
        out_path=out_path,
        music_path=music_path
    )

# =========================
# CLI
# =========================

def main():
    parser = argparse.ArgumentParser(description="Pipeline completo de renderização de vídeo")
    parser.add_argument("--storyboard", required=True, help="Caminho para o arquivo JSON do storyboard")
    parser.add_argument("--assets-dir", default="./assets", help="Diretório para assets temporários")
    parser.add_argument("--out", default="./final_video.mp4", help="Caminho do vídeo final")
    parser.add_argument("--music", help="Caminho para música de fundo (opcional)")
    
    # ElevenLabs TTS
    parser.add_argument("--voice-id", help="ID da voz ElevenLabs")
    parser.add_argument("--elevenlabs-key", help="API Key ElevenLabs")
    
    # Leonardo Motion
    parser.add_argument("--gen-motion", action="store_true", help="Gerar clipes motion se faltarem")
    parser.add_argument("--images-dir", help="Pasta com imagens scene_XX.png/jpg")
    parser.add_argument("--leonardo-key", help="API Key Leonardo AI")
    
    args = parser.parse_args()

    print(f"[PIPELINE] Iniciando renderização...")
    print(f"[PIPELINE] Storyboard: {args.storyboard}")
    print(f"[PIPELINE] Assets: {args.assets_dir}")
    print(f"[PIPELINE] Saída: {args.out}")
    
    if args.gen_motion:
        print(f"[PIPELINE] Motion: Habilitado (imagens: {args.images_dir})")
    
    if args.voice_id:
        print(f"[PIPELINE] TTS: Habilitado (voz: {args.voice_id})")

    try:
        result = render_from_storyboard(
            storyboard_path_or_dict=args.storyboard,
            assets_dir=args.assets_dir,
            out_path=args.out,
            eleven_voice_id=args.voice_id,
            eleven_api_key=args.elevenlabs_key,
            music_path=args.music,
            leonardo_key=args.leonardo_key,
            images_dir=args.images_dir,
            gen_motion=args.gen_motion
        )
        
        print(f"[PIPELINE] ✅ Vídeo renderizado: {result}")
    except Exception as e:
        print(f"[PIPELINE] ❌ Erro: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
