# render_pipeline_audio_driven.py
# -*- coding: utf-8 -*-

"""
Pipeline áudio-dirigido (MoviePy 2.1.1):
1) Lê storyboard.json (cenas com narration, image_prompt, motion_prompt)
2) Gera TTS (ElevenLabs) por cena -> mede duração real do áudio
3) Gera vídeo por cena no Leonardo (image->video). Tenta "duration"; se o endpoint não aceitar,
   faz fallback e depois repete o clipe até cobrir a duração do áudio.
4) Monta tudo (9:16, 30fps), mixa música e exporta MP4 final

Requisitos:
  pip install moviepy requests

Ambiente (exemplos):
  export ELEVEN_API_KEY=...
  export LEONARDO_API_KEY=...

Execução:
  python render_pipeline_audio_driven.py \
    --storyboard ./storyboard.json \
    --assets-dir ./assets \
    --images-dir ./images \
    --out ./final.mp4 \
    --voice-id <ELEVEN_VOICE_ID> \
    --eleven-key $ELEVEN_API_KEY \
    --leonardo-key $LEONARDO_API_KEY \
    --music ./music/bg.mp3
"""

import os
import json
import argparse
import time
import requests
from typing import Dict, Any, Optional
from math import ceil

# ====== IMPORTS MoviePy (versão 2.x) ======
from moviepy import VideoFileClip, AudioFileClip, CompositeAudioClip, ImageClip, concatenate_videoclips, vfx, TextClip, CompositeVideoClip

# ====== CONFIG ======
TARGET_W, TARGET_H, FPS = 1080, 1920, 30
CROSSFADE_S = 0.18
DEFAULT_MUSIC_VOL = 0.22

# ====== LEGENDAS CONFIG ======
SUBTITLE_FONT = 'Arial'
SUBTITLE_FONTSIZE = 80
SUBTITLE_COLOR = 'white'
SUBTITLE_STROKE_COLOR = 'black'
SUBTITLE_STROKE_WIDTH = 3
SUBTITLE_POSITION = ('center', 'bottom')
SUBTITLE_MARGIN_BOTTOM = 200  # pixels do fundo
SUBTITLE_MAX_CHARS_PER_LINE = 35
SUBTITLE_WORDS_PER_SECOND = 2.5

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

ELEVEN_TTS_URL_FMT = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
ELEVEN_MODEL_ID = "eleven_multilingual_v2"


def ensure_dir(p: str):
    os.makedirs(p, exist_ok=True)


def load_storyboard(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# ====== TTS (ElevenLabs) ======


def elevenlabs_tts_to_file(text: str, voice_id: str, api_key: str, out_path: str,
                           stability=0.35, similarity=0.85, style=0.0, timeout=60):
    if not text or not text.strip():
        return None
    url = ELEVEN_TTS_URL_FMT.format(voice_id=voice_id)
    headers = {"xi-api-key": api_key, "accept": "audio/mpeg",
               "Content-Type": "application/json"}
    payload = {
        "text": text,
        "model_id": ELEVEN_MODEL_ID,
        "voice_settings": {
            "stability": stability,
            "similarity_boost": similarity,
            "style": style,
            "use_speaker_boost": True
        }
    }
    r = requests.post(url, headers=headers, json=payload, timeout=timeout)
    if r.status_code != 200:
        raise RuntimeError(
            f"ElevenLabs TTS error {r.status_code}: {r.text[:300]}")
    ensure_dir(os.path.dirname(out_path) or ".")
    with open(out_path, "wb") as f:
        f.write(r.content)
    return out_path


def get_audio_duration(path: str) -> float:
    clip = AudioFileClip(path)
    d = float(clip.duration)
    clip.close()
    return max(0.5, round(d, 3))

# ====== Leonardo Motion Client (init-image + image-to-video) ======


class LeonardoMotionClient:
    """
    Fluxo:
      1) init-image (pega presigned URL) -> upload S3 -> retorna image_id
      2) create_image_to_video(image_id, duration_sec, prompt, aspect_ratio) -> job_id
         - tenta 'duration'
         - se vier 400 "Unexpected variable duration", reenvia sem 'duration'
      3) poll(job_id) -> video_url
    """

    def __init__(self, api_key: str, base_url="https://cloud.leonardo.ai/api"):
        self.api_key = api_key
        self.s = requests.Session()
        self.s.headers.update(
            {"Authorization": f"Bearer {api_key}", "Accept": "application/json"})
        self.base = base_url.rstrip("/")

    def upload_image(self, image_path: str) -> str:
        # 1) init-image: retorna URL/fields para upload multipart
        ext = os.path.splitext(image_path)[1][1:].lower()  # png/jpg/jpeg/webp
        url = f"{self.base}/rest/v1/init-image"
        r = self.s.post(url, json={"extension": ext}, headers={
                        "Content-Type": "application/json"}, timeout=30)
        r.raise_for_status()
        data = r.json()
        # Alguns tenants retornam direto
        up = data.get("uploadInitImage") or data
        image_id = up.get("id")
        upload_url = up.get("url")
        fields = up.get("fields")
        if isinstance(fields, str):
            try:
                fields = json.loads(fields)
            except Exception:
                pass
        if not (image_id and upload_url and isinstance(fields, dict)):
            raise RuntimeError(f"init-image response inesperado: {data}")

        # 2) upload multipart para o S3
        ctype = "image/" + ("jpeg" if ext == "jpg" else ext)
        with open(image_path, "rb") as f:
            files = {"file": (os.path.basename(image_path), f, ctype)}
            r2 = requests.post(upload_url, data=fields,
                               files=files, timeout=180)
            r2.raise_for_status()
        return image_id

    def create_image_to_video(self, image_path: str, duration_sec: float) -> str:
        """
        1) Upload image using existing upload_image method
        2) Create motion job
        3) Return job_id
        """
        # 1) Upload using existing method
        image_id = self.upload_image(image_path)

        # 2) Create SVD motion job
        payload = {
            "imageId": image_id,
            "motionStrength": 8,
            "duration": 6
        }
        print("[DEBUG] Payload enviado para Leonardo AI (motion):", payload)
        r = requests.post(f"{self.base}/rest/v1/generations-motion-svd",
                         headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                         json=payload, timeout=60)
        print("[DEBUG] Status code:", r.status_code)
        if r.status_code != 200:
            print("[DEBUG] Response text:", r.text)
        r.raise_for_status()
        job_data = r.json()
        print("[DEBUG] Resposta job_data:", job_data)
        job_id = job_data.get("generationId") or job_data.get("id")
        if not job_id:
            raise RuntimeError(f"Job creation failed: {job_data}")
        return job_id

    def poll_motion(self, job_id: str, timeout=900, interval=3) -> str:
        url = f"{self.base}/rest/v1/generations/{job_id}"
        t0 = time.time()
        while True:
            r = self.s.get(url, timeout=30)
            r.raise_for_status()
            data = r.json()

            status = (data.get("status") or data.get(
                "generations_by_pk", {}).get("status") or "").lower()
            if status in ("succeeded", "completed", "complete"):
                video_url = (
                    data.get("video_url")
                    or data.get("data", {}).get("video_url")
                    or data.get("result", {}).get("video_url")
                )
                if not video_url:
                    outs = (
                        data.get("generated_images")
                        or data.get("generations_by_pk", {}).get("generated_images")
                        or data.get("outputs") or []
                    )
                    if outs and isinstance(outs, list):
                        video_url = outs[0].get(
                            "url") or outs[0].get("video_url")
                if not video_url:
                    raise RuntimeError(
                        f"Job {job_id} finalizado sem video_url: {data}")
                return video_url

            if status in ("failed", "error"):
                raise RuntimeError(f"Job {job_id} falhou: {data}")

            if time.time() - t0 > timeout:
                raise TimeoutError(f"Timeout no job {job_id}")

            time.sleep(interval)

    def download(self, url: str, out_path: str):
        r = self.s.get(url, stream=True, timeout=300)
        r.raise_for_status()
        ensure_dir(os.path.dirname(out_path) or ".")
        with open(out_path, "wb") as f:
            for chunk in r.iter_content(8192):
                if chunk:
                    f.write(chunk)
        return out_path

# ====== Helpers de vídeo ======

def create_local_motion_from_image(image_path: str, duration_sec: float, out_path: str) -> str:
    """Gera um vídeo com efeito Ken Burns (zoom/pan leve) localmente, sem API externa."""
    ensure_dir(os.path.dirname(out_path) or ".")
    img = ImageClip(image_path).with_duration(max(0.5, float(duration_sec)))
    # Ajusta para 9:16 mantendo proporção e aplica zoom suave
    if img.h != TARGET_H:
        img = img.resized(height=TARGET_H)
    if img.w < TARGET_W:
        # se sobrar borda, faz um leve zoom para cobrir
        scale = TARGET_W / float(img.w)
        img = img.resized(scale)
    # zoom progressivo de ~5%
    dur = img.duration
    img = img.resized(lambda t: 1.0 + 0.05 * (t / max(0.001, dur)))
    # recorta exatamente 1080x1920, centralizado
    x_center = img.w / 2
    y_center = img.h / 2
    x1 = int(x_center - TARGET_W / 2)
    y1 = int(y_center - TARGET_H / 2)
    img = img.cropped(x1=max(0, x1), y1=max(0, y1), width=TARGET_W, height=TARGET_H)

    # Exporta clipe mudo
    img.with_fps(FPS).write_videofile(out_path, codec="libx264", audio=False, fps=FPS, preset="medium", bitrate="6000k")
    return out_path


def fit_vertical(clip: VideoFileClip) -> VideoFileClip:
    c = clip.with_fps(FPS)
    if c.h != TARGET_H:
        c = c.resized(height=TARGET_H)
    if c.w != TARGET_W:
        c = c.resized(width=TARGET_W)
    return c


def ensure_min_duration_loop(videopath: str, min_dur: float) -> VideoFileClip:
    """
    Abre videopath e retorna um clip com pelo menos min_dur,
    repetindo o original quantas vezes for preciso e cortando no final.
    Útil quando o endpoint entrega vídeo curto (~5s).
    """
    base = VideoFileClip(videopath)
    if base.duration >= min_dur:
        return base.subclipped(0, min_dur)

    reps = ceil(min_dur / max(0.1, base.duration))
    # concat de cópias do mesmo arquivo para cobrir a duração
    clips = [VideoFileClip(videopath) for _ in range(reps)]
    concat = concatenate_videoclips(clips, method="compose")
    return concat.subclipped(0, min_dur)


def build_scene_clip(i: int, s: Dict[str, Any], assets_dir: str, enable_subtitles: bool = False) -> VideoFileClip:
    dur_target = max(0.5, float(s["t_end"]) - float(s["t_start"]))
    base = f"scene_{i:02d}"
    vpath = os.path.join(assets_dir, f"{base}.mp4")
    if not os.path.exists(vpath):
        raise FileNotFoundError(f"Falta vídeo da cena {i}: {vpath}")

    # Caso o vídeo seja curto, estende com loop para cobrir a narração
    clip = ensure_min_duration_loop(vpath, dur_target)
    clip = fit_vertical(clip)

    # Áudio: prioriza MP3 > WAV
    apath_mp3 = os.path.join(assets_dir, f"{base}.mp3")
    apath_wav = os.path.join(assets_dir, f"{base}.wav")
    a = None
    if os.path.exists(apath_mp3):
        a = AudioFileClip(apath_mp3)
    elif os.path.exists(apath_wav):
        a = AudioFileClip(apath_wav)

    if a:
        # Se o áudio exceder por milissegundos, corta a cauda
        if a.duration > clip.duration + 0.05:
            a = a.subclip(0, clip.duration)
    clip = clip.with_audio(a)
    
    # ADICIONAR LEGENDAS se habilitadas e há narração
    if enable_subtitles:
        narration_text = s.get("narration", "").strip()
        if narration_text:
            print(f"[SUBTITLE] Adicionando legendas à cena {i}")
            clip = add_subtitles_to_scene(clip, narration_text)

    return clip


def assemble_video(storyboard: Dict[str, Any], assets_dir: str, out_path: str,
                   music_path: Optional[str] = None, enable_subtitles: bool = False) -> str:
    scenes = storyboard.get("scenes") or storyboard.get("storyboard") or []
    if not scenes:
        raise ValueError("Storyboard sem 'scenes'.")

    clips = []
    for i, s in enumerate(scenes, start=1):
        c = build_scene_clip(i, s, assets_dir, enable_subtitles)
        if clips and CROSSFADE_S > 0:
            c = c.crossfadein(CROSSFADE_S)
        clips.append(c)

    final = concatenate_videoclips(
        clips, method="compose",
        padding=(-CROSSFADE_S if CROSSFADE_S > 0 else 0)
    ).with_fps(FPS)

    # Música opcional
    if music_path and os.path.exists(music_path):
        try:
            bg = AudioFileClip(music_path).volumex(
                DEFAULT_MUSIC_VOL).set_start(0).set_duration(final.duration)
            final = final.set_audio(CompositeAudioClip(
                [final.audio, bg]) if final.audio else bg)
        except Exception as e:
            print(f"[WARN] Música: {e}")

    ensure_dir(os.path.dirname(out_path) or ".")
    print(f"[EXPORT] {out_path}")
    final.write_videofile(out_path, **EXPORT_OPTS)
    return out_path

# ====== SISTEMA DE LEGENDAS ======

def split_text_into_lines(text: str, max_chars: int = SUBTITLE_MAX_CHARS_PER_LINE) -> list:
    """Divide texto em linhas para legendas, respeitando palavras"""
    words = text.split()
    lines = []
    current_line = ""
    
    for word in words:
        if len(current_line + " " + word) <= max_chars:
            current_line = (current_line + " " + word).strip()
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    
    if current_line:
        lines.append(current_line)
    
    return lines

def create_subtitle_segments(text: str, duration: float) -> list:
    """Cria segmentos de legenda com timing baseado na duração do áudio"""
    words = text.split()
    if not words:
        return []
    
    # Calcular quantas palavras por segmento baseado na velocidade
    words_per_segment = max(3, int(SUBTITLE_WORDS_PER_SECOND * 2))  # 2 segundos por segmento
    segment_duration = min(3.0, duration / max(1, len(words) / words_per_segment))
    
    segments = []
    current_time = 0.0
    
    for i in range(0, len(words), words_per_segment):
        segment_words = words[i:i + words_per_segment]
        segment_text = " ".join(segment_words)
        
        # Dividir em linhas se necessário
        lines = split_text_into_lines(segment_text)
        display_text = "\n".join(lines)
        
        end_time = min(current_time + segment_duration, duration)
        
        segments.append({
            'text': display_text,
            'start': current_time,
            'end': end_time,
            'duration': end_time - current_time
        })
        
        current_time = end_time
        
        if current_time >= duration:
            break
    
    return segments

def create_subtitle_clip(text: str, start_time: float, duration: float, 
                         font: str = SUBTITLE_FONT, fontsize: int = SUBTITLE_FONTSIZE, 
                         color: str = SUBTITLE_COLOR, position_type: str = "bottom") -> TextClip:
    """Cria um clip de legenda individual"""
    try:
        # Configurar posição baseada no parâmetro
        if position_type == "top":
            position = ('center', 100)
        elif position_type == "middle":
            position = ('center', 'center')
        else:  # bottom
            position = ('center', TARGET_H - SUBTITLE_MARGIN_BOTTOM)
        
        subtitle_clip = TextClip(
            text,
            font=font,
            fontsize=fontsize,
            color=color,
            stroke_color=SUBTITLE_STROKE_COLOR,
            stroke_width=SUBTITLE_STROKE_WIDTH,
            method='caption',
            size=(TARGET_W - 100, None),  # Margem lateral
            align='center'
        ).set_start(start_time).set_duration(duration).set_position(position)
        
        return subtitle_clip
        
    except Exception as e:
        print(f"[WARN] Erro criando legenda '{text[:30]}...': {e}")
        # Fallback simples sem stroke
        if position_type == "top":
            fallback_pos = ('center', 100)
        elif position_type == "middle":
            fallback_pos = ('center', 'center')
        else:  # bottom
            fallback_pos = ('center', TARGET_H - SUBTITLE_MARGIN_BOTTOM)
            
        return TextClip(
            text,
            font=font,
            fontsize=fontsize,
            color=color,
            method='caption',
            size=(TARGET_W - 100, None),
            align='center'
        ).set_start(start_time).set_duration(duration).set_position(fallback_pos)

def add_subtitles_to_scene(video_clip, narration_text: str, scene_start: float = 0.0,
                           font: str = SUBTITLE_FONT, fontsize: int = SUBTITLE_FONTSIZE, 
                           color: str = SUBTITLE_COLOR, position: str = "bottom") -> CompositeVideoClip:
    """Adiciona legendas a um clip de vídeo de uma cena"""
    if not narration_text or not narration_text.strip():
        return video_clip
    
    duration = video_clip.duration
    segments = create_subtitle_segments(narration_text.strip(), duration)
    
    if not segments:
        return video_clip
    
    subtitle_clips = []
    for segment in segments:
        subtitle_clip = create_subtitle_clip(
            segment['text'], 
            segment['start'], 
            segment['duration']
        )
        subtitle_clips.append(subtitle_clip)
    
    # Compor vídeo com legendas
    return CompositeVideoClip([video_clip] + subtitle_clips)

# ====== Orquestração ======


def main():
    ap = argparse.ArgumentParser(
        description="Áudio-dirigido: TTS -> Image2Video -> Montagem (MoviePy 2.1.1)")
    ap.add_argument("--storyboard", required=True)
    ap.add_argument("--assets-dir", required=True)
    ap.add_argument("--images-dir", required=True,
                    help="scene_XX.png/jpg/webp")
    ap.add_argument("--out", required=True)
    ap.add_argument("--music", default=None)
    ap.add_argument("--subtitles", action="store_true", help="Ativar legendas automáticas")
    ap.add_argument("--subtitle-font", default="Arial", help="Fonte das legendas")
    ap.add_argument("--subtitle-size", type=int, default=80, help="Tamanho da fonte das legendas")
    ap.add_argument("--subtitle-color", default="white", help="Cor das legendas")
    ap.add_argument("--subtitle-position", default="bottom", choices=["top", "middle", "bottom"], help="Posição das legendas")

    # ElevenLabs
    ap.add_argument("--voice-id", required=True)
    ap.add_argument("--eleven-key", required=True)

    # Leonardo
    ap.add_argument("--leonardo-key", required=True)

    args = ap.parse_args()

    storyboard = load_storyboard(args.storyboard)
    scenes = storyboard.get("scenes") or storyboard.get("storyboard")
    if not scenes:
        raise ValueError("Storyboard sem scenes.")

    ensure_dir(args.assets_dir)

    # (1) TTS por cena -> reancora t_start/t_end pela duração real do áudio
    for i, s in enumerate(scenes, start=1):
        base = os.path.join(args.assets_dir, f"scene_{i:02d}")
        apath = base + ".mp3"
        if not os.path.exists(apath):
            text = (s.get("narration") or "").strip()
            if text:
                print(f"[TTS] Cena {i}")
                elevenlabs_tts_to_file(
                    text, args.voice_id, args.eleven_key, apath)
        # Recalcula tempos encadeados
        if os.path.exists(apath):
            dur = get_audio_duration(apath)
            if i == 1:
                s["t_start"] = 0.0
            else:
                prev_end = float(scenes[i-2]["t_end"])
                s["t_start"] = round(prev_end, 3)
            s["t_end"] = round(float(s["t_start"]) + dur, 3)

    # (2) Image->Video por cena (tenta duração; se o endpoint não aceitar, segue sem)
    client = LeonardoMotionClient(args.leonardo_key)
    for i, s in enumerate(scenes, start=1):
        vpath = os.path.join(args.assets_dir, f"scene_{i:02d}.mp4")
        if os.path.exists(vpath):
            continue  # cache

        # encontra imagem base
        img = None
        for ext in ("png", "jpg", "jpeg", "webp"):
            cand = os.path.join(args.images_dir, f"scene_{i:02d}.{ext}")
            if os.path.exists(cand):
                img = cand
                break
        if not img:
            raise FileNotFoundError(
                f"[MOTION] Sem imagem scene_{i:02d} em {args.images_dir}")

        dur = max(0.5, float(s["t_end"]) - float(s["t_start"]))
        motion_prompt = s.get(
            "motion_prompt") or "slow cinematic zoom in, subtle parallax, 9:16 vertical"

        print(f"[MOTION] Cena {i}: upload -> job (target {dur:.2f}s)")
        try:
            job_id = client.create_image_to_video(img, dur)
            video_url = client.poll_motion(job_id)
            client.download(video_url, vpath)
        except Exception as e:
            print(f"[MOTION-LOCAL] Falha Leonardo ({e}). Gerando motion local...")
            create_local_motion_from_image(img, dur, vpath)

    # (3) Montagem final
    assemble_video(storyboard, args.assets_dir,
                   args.out, music_path=args.music, enable_subtitles=args.subtitles)


if __name__ == "__main__":
    main()
