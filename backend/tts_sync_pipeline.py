# tts_sync_pipeline.py
# -*- coding: utf-8 -*-

"""
Pipeline: Storyboard -> ElevenLabs TTS por cena -> Montagem MoviePy (9:16) -> MP4 final.

Requisitos:
  pip install moviepy requests

Entrada esperada:
- JSON de storyboard com "scenes": [{ "t_start": 0, "t_end": 7, "narration": "...", ... }, ...]
- Para cada cena, um MP4 animado existente em assets_dir: scene_01.mp4, scene_02.mp4, ...
  (Esses clipes vêm do Leonardo Motion ou equivalente.)

Saída:
- final.mp4 sincronizado, com narração por cena (e música opcional).

Observações:
- Gera TTS somente se o arquivo de áudio da cena não existir (cache).
- Mantém 1080x1920 (vertical) e 30fps.
- Ajusta duração do clipe para caber no intervalo da cena.
"""

import os
import json
import time
import math
import hashlib
import requests
from typing import Optional, Dict, Any, List

# Compatibilidade MoviePy 1.x e 2.x
try:
    from moviepy.editor import (
        VideoFileClip,
        AudioFileClip,
        CompositeAudioClip,
        concatenate_videoclips,
        vfx
    )
    # MoviePy 2.x compatibility
    def apply_fx(clip, fx_func, **kwargs):
        if hasattr(clip, 'with_fps'):  # MoviePy 2.x
            return fx_func(clip, **kwargs)
        else:  # MoviePy 1.x
            return clip.fx(fx_func, **kwargs)
            
    def set_fps_compat(clip, fps):
        if hasattr(clip, 'with_fps'):  # MoviePy 2.x
            return clip.with_fps(fps)
        else:  # MoviePy 1.x
            return clip.set_fps(fps)
            
except ImportError as e:
    print(f"Erro ao importar MoviePy: {e}")
    print("Execute: pip install moviepy")
    raise

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
ELEVEN_TTS_URL_FMT = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
ELEVEN_MODEL_ID = "eleven_multilingual_v2"  # geralmente funciona muito bem em PT-BR

# Vozes recomendadas para narrativa (PT-BR)
RECOMMENDED_VOICES = {
    "Rachel": "21m00Tcm4TlvDq8ikWAM",  # feminina clara e envolvente
    "Liam": "TX3LPaxmHKxFdv7VOQHJ",   # masculina, tom narrativo calmo
    "Antoni": "ErXwobaYiN019PkySvjV",  # masculina, mais grave, boa para documentários
    "Charlotte": "XB0fDUnXU5powFXDhCwa", # feminina suave, ótima para infantil
    "Clyde": "2EiwWnXFnvU5JabPnv8n",   # masculina com entonação "rádio/TV"
    "Drew": "29vD33N1CtxCmqQRPOHJ",    # masculina profissional
    "Bella": "EXAVITQu4vr4xnSDxMaL",   # feminina suave
    "Elli": "MF3mGyEYCl7XYWbV9V6O",    # feminina jovem
    "Josh": "TxGEqnHWrfWFTfGW9XjX",    # masculina energética
    "Arnold": "VR6AewLTigWG4xSOukaG",  # masculina narrativa
    "Adam": "pNInz6obpgDQGcFmaJgB",     # masculina profunda
    "Sam": "yoZ06aMxZJJ28mfd3POQ"      # masculina jovem
}

def get_voice_id(voice_name: str) -> str:
    """Converte nome da voz para ID da ElevenLabs"""
    return RECOMMENDED_VOICES.get(voice_name, voice_name)

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

    audio_format: "mp3" (padrão) ou "wav"
    """
    if not text or not text.strip():
        raise ValueError("Texto TTS vazio.")

    # Converte nome de voz para ID se necessário
    if voice_id in RECOMMENDED_VOICES:
        voice_id = RECOMMENDED_VOICES[voice_id]

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

    print(f"🎙️ Gerando TTS ElevenLabs: {len(text)} chars com voz {voice_id}")
    
    last_err = None
    for attempt in range(retries + 1):
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=timeout)
            if r.status_code != 200:
                raise RuntimeError(f"ElevenLabs TTS falhou ({r.status_code}): {r.text[:300]}")
            os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
            with open(out_path, "wb") as f:
                f.write(r.content)
            print(f"✅ TTS salvo: {out_path}")
            return out_path
        except Exception as e:
            last_err = e
            if attempt < retries:
                print(f"⚠️ TTS tentativa {attempt + 1} falhou, tentando novamente em {backoff_sec}s...")
                time.sleep(backoff_sec * (2 ** attempt))
            else:
                print(f"❌ TTS falhou após {retries + 1} tentativas: {e}")
                raise last_err

# =========================
# MOVIEPY (MONTAGEM)
# =========================

def _fit_vertical(clip: VideoFileClip) -> VideoFileClip:
    """Garante 1080x1920 (9:16)."""
    c = set_fps_compat(clip, FPS)
    if c.h != TARGET_H:
        c = c.resize(height=TARGET_H)
    if c.w != TARGET_W:
        c = c.resize(width=TARGET_W)
    return c

def _scene_duration(scene: Dict[str, Any]) -> float:
    t0, t1 = float(scene.get("t_start", 0)), float(scene.get("t_end", 4))
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

    print(f"🎬 Processando cena {scene_idx}: {vpath} (duração: {dur}s)")
    v = _fit_vertical(VideoFileClip(vpath))

    # Ajuste de duração do vídeo
    if v.duration > dur:
        v = v.subclip(0, dur)
    elif v.duration < dur and ALLOW_SPEED_ADJUST:
        factor = max(0.1, v.duration / dur)  # <1 = slow motion
        v = apply_fx(v, vfx.speedx, factor=factor)
        if v.duration > dur:  # aparar sobra mínima
            v = v.subclip(0, dur)

    # Procura áudio (prefere .mp3; senão .wav)
    apath_mp3 = os.path.join(assets_dir, f"{base}.mp3")
    apath_wav = os.path.join(assets_dir, f"{base}.wav")
    apath = apath_mp3 if os.path.exists(apath_mp3) else (apath_wav if os.path.exists(apath_wav) else None)

    if apath:
        print(f"🎵 Adicionando áudio: {apath}")
        a = AudioFileClip(apath)
        if a.duration > dur:
            a = a.subclip(0, dur)
        v = v.set_audio(a)
    else:
        print(f"⚠️ Sem áudio para cena {scene_idx}")

    return v

def assemble_video(
    storyboard: Dict[str, Any],
    assets_dir: str,
    out_path: str,
    music_path: Optional[str] = None,
    crossfade_s: float = CROSSFADE_S
) -> str:
    """Monta o vídeo final a partir das cenas e storyboard"""
    scenes = storyboard.get("scenes") or storyboard.get("storyboard") or storyboard.get("cenas", [])
    if not scenes:
        raise ValueError("Storyboard sem 'scenes' (ou 'storyboard' ou 'cenas').")

    print(f"🎬 Montando vídeo com {len(scenes)} cenas...")
    
    clips = []
    for i, s in enumerate(scenes, start=1):
        clip = build_scene_clip(i, s, assets_dir)
        if clips and crossfade_s > 0:
            clip = clip.crossfadein(crossfade_s)
        clips.append(clip)

    print("🔗 Concatenando cenas...")
    final = concatenate_videoclips(
        clips,
        method="compose",
        padding=(-crossfade_s if crossfade_s > 0 else 0)
    )
    final = set_fps_compat(final, FPS)

    # Música de fundo opcional
    if music_path and os.path.exists(music_path):
        try:
            print(f"🎵 Adicionando música de fundo: {music_path}")
            music = AudioFileClip(music_path).volumex(DEFAULT_MUSIC_VOL).set_start(0).set_duration(final.duration)
            final_audio = final.audio
            if final_audio:
                mixed = CompositeAudioClip([final_audio, music])
            else:
                mixed = CompositeAudioClip([music])
            final = final.set_audio(mixed)
        except Exception as e:
            print(f"[WARN] Falha ao mixar música: {e}")

    print(f"💾 Exportando vídeo final: {out_path}")
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    final.write_videofile(out_path, **EXPORT_OPTS)
    
    # Cleanup
    for clip in clips:
        clip.close()
    final.close()
    
    print(f"✅ Vídeo exportado com sucesso: {out_path}")
    return out_path

# =========================
# ORQUESTRAÇÃO
# =========================

def generate_tts_per_scene_if_needed(
    storyboard: Dict[str, Any],
    assets_dir: str,
    voice_id: str,
    elevenlabs_api_key: str,
    audio_format: str = "mp3",
    voice_settings: Optional[Dict] = None
):
    """
    Para cada cena, gera TTS da 'narration' se o arquivo de áudio não existir.
    - Salva como scene_{i:02d}.mp3 ou .wav
    """
    scenes = storyboard.get("scenes") or storyboard.get("storyboard") or storyboard.get("cenas", [])
    if not scenes:
        raise ValueError("Storyboard sem 'scenes' (ou 'storyboard' ou 'cenas').")

    os.makedirs(assets_dir, exist_ok=True)
    
    # Configurações de voz padrão + customizadas
    tts_settings = {
        "stability": 0.35,
        "similarity_boost": 0.85,
        "style": 0.0,
        "use_speaker_boost": True
    }
    if voice_settings:
        tts_settings.update(voice_settings)

    print(f"🎙️ Gerando TTS para {len(scenes)} cenas com voz {voice_id}")

    for i, s in enumerate(scenes, start=1):
        base = f"scene_{i:02d}"
        out_path = os.path.join(assets_dir, f"{base}.{audio_format}")
        if os.path.exists(out_path):
            print(f"✅ TTS cena {i} já existe: {out_path}")
            continue  # cache
        
        text = (s.get("narration") or s.get("narracao") or "").strip()
        if not text:
            print(f"⚠️ Cena {i} sem narração — ignorando.")
            continue
            
        try:
            elevenlabs_tts(
                text=text,
                voice_id=voice_id,
                api_key=elevenlabs_api_key,
                out_path=out_path,
                audio_format=audio_format,
                **tts_settings
            )
        except Exception as e:
            print(f"❌ Erro ao gerar TTS para cena {i}: {e}")
            # Continua com as outras cenas

def load_storyboard(storyboard_path_or_dict) -> Dict[str, Any]:
    """Carrega storyboard de arquivo JSON ou dict"""
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
    voice_settings: Optional[Dict] = None
) -> str:
    """
    Função única: carrega storyboard -> gera TTS por cena (se voice_id + api_key) -> monta vídeo -> exporta MP4.
    """
    print("🚀 Iniciando pipeline de renderização completa...")
    
    storyboard = load_storyboard(storyboard_path_or_dict)
    
    print(f"📄 Storyboard carregado: {len(storyboard.get('scenes', storyboard.get('storyboard', storyboard.get('cenas', []))))} cenas")

    if eleven_voice_id and eleven_api_key:
        generate_tts_per_scene_if_needed(
            storyboard=storyboard,
            assets_dir=assets_dir,
            voice_id=eleven_voice_id,
            elevenlabs_api_key=eleven_api_key,
            audio_format=audio_format,
            voice_settings=voice_settings
        )
    else:
        print("⚠️ Sem credenciais ElevenLabs - usando áudios existentes apenas")
        
    return assemble_video(
        storyboard=storyboard,
        assets_dir=assets_dir,
        out_path=out_path,
        music_path=music_path
    )

# =========================
# EXEMPLO DE USO
# =========================
if __name__ == "__main__":
    """
    Exemplo rápido (ajuste caminhos antes de rodar):

    python tts_sync_pipeline.py

    Requer:
      - storyboard.json com 'scenes' (cada cena deve ter t_start, t_end, narration)
      - assets_dir com scene_01.mp4, scene_02.mp4, ...
      - ElevenLabs voice_id + api_key (se quiser gerar TTS automaticamente)
    """
    # ---- edite estes caminhos:
    STORYBOARD_JSON = "./storyboard.json"
    ASSETS_DIR = "./assets"
    OUTPUT_MP4 = "./final.mp4"

    # (opcional) música
    MUSIC_PATH = None  # ex: "./music/bg_track.mp3"

    # (opcional) TTS ElevenLabs
    ELEVEN_VOICE_ID = "Rachel"  # ou use o ID diretamente: "21m00Tcm4TlvDq8ikWAM"
    ELEVEN_API_KEY = os.getenv("ELEVEN_API_KEY")  # configure sua API key

    if not ELEVEN_API_KEY:
        print("⚠️ ELEVEN_API_KEY não configurada. Configure: export ELEVEN_API_KEY=sua_key")
        ELEVEN_VOICE_ID = None  # Desabilita TTS

    # Render
    try:
        result = render_from_storyboard(
            storyboard_path_or_dict=STORYBOARD_JSON,
            assets_dir=ASSETS_DIR,
            out_path=OUTPUT_MP4,
            eleven_voice_id=ELEVEN_VOICE_ID,
            eleven_api_key=ELEVEN_API_KEY,
            audio_format="mp3",
            music_path=MUSIC_PATH,
            voice_settings={
                "stability": 0.5,      # mais estável
                "similarity_boost": 0.8,
                "style": 0.2           # um pouco mais expressivo
            }
        )
        print(f"🎉 Vídeo gerado com sucesso: {result}")
    except Exception as e:
        print(f"❌ Erro na renderização: {e}")
        import traceback
        traceback.print_exc()
