# /var/www/tiktok-automation/backend/services/visual_effects_system.py

import os
import cv2
import numpy as np
import logging
from typing import Dict, List, Optional, Tuple, Any
import random
import math
from dataclasses import dataclass
from enum import Enum
import json
from datetime import datetime
from config_manager import get_config
import asyncio
import requests
import moviepy.config as mpy_config

# Importações para processamento visual
try:
    from moviepy import VideoFileClip, AudioFileClip, ImageClip, TextClip, CompositeVideoClip, CompositeAudioClip
    from moviepy.video.tools.subtitles import SubtitlesClip
    # from moviepy import effects as vfx  # Removido temporariamente
except ImportError as e:
    print(f"❌ Erro ao importar MoviePy: {e}")
    raise
from PIL import Image, ImageEnhance, ImageFilter

logger = logging.getLogger(__name__)
config = get_config()

logger.info("✅ MoviePy importado com sucesso")

# Configurar ImageMagick para MoviePy (removido para MoviePy 2.x)
# try:
#     mpy_config.change_settings({'IMAGEMAGICK_BINARY': '/usr/bin/convert'})
# except Exception as e:
#     logger.warning(f"Não foi possível configurar ImageMagick: {e}")


class Platform(Enum):
    """Plataformas de destino"""
    TIKTOK = "tiktok"
    YOUTUBE_SHORTS = "youtube_shorts"
    INSTAGRAM_REELS = "instagram_reels"
    FACEBOOK_REELS = "facebook_reels"


@dataclass
class PlatformSpecs:
    """Especificações técnicas por plataforma"""
    resolution: Tuple[int, int]
    aspect_ratio: str
    max_duration: int
    framerate: int
    bitrate: str
    audio_format: str


@dataclass
class VisualStyle:
    """Configuração de estilo visual"""
    name: str
    colors: List[str]
    fonts: List[str]
    effects: List[str]
    mood: str
    target_audience: str


class VisualEffectsSystem:
    def __init__(self):
        logger.info("🎨 Inicializando Sistema de Efeitos Visuais...")

        self.videos_dir = config.VIDEO_DIR
        self.audio_dir = config.AUDIO_DIR
        os.makedirs(self.videos_dir, exist_ok=True)

        # Garantir diretórios auxiliares
        try:
            os.makedirs(self.audio_dir, exist_ok=True)
        except Exception:
            pass
        try:
            os.makedirs(getattr(config, 'MUSIC_DIR', self.audio_dir), exist_ok=True)
        except Exception:
            pass

        # Configurações e presets
        self.platform_specs = self._setup_platform_specs()
        self.visual_styles = self._setup_visual_styles()
        self.music_library = self._setup_music_library()
        self.subtitle_styles = self._setup_subtitle_styles()

        # Importar serviço de transcrição de forma lazy para evitar problemas de path
        self.transcriber = None
        try:
            import importlib
            for mod_name in (
                'services.transcription_service',
                'backend.services.transcription_service',
            ):
                try:
                    mod = importlib.import_module(mod_name)
                    if hasattr(mod, 'TranscriptionService'):
                        self.transcriber = getattr(mod, 'TranscriptionService')()
                        break
                except Exception:
                    continue
            if self.transcriber is None:
                # Fallback: importação dinâmica por caminho do arquivo
                import importlib.util
                base_dir = os.path.dirname(os.path.abspath(__file__))
                svc_path = os.path.join(base_dir, 'services', 'transcription_service.py')
                if os.path.exists(svc_path):
                    spec = importlib.util.spec_from_file_location('transcription_service', svc_path)
                    mod = importlib.util.module_from_spec(spec)
                    assert spec and spec.loader
                    spec.loader.exec_module(mod)  # type: ignore[attr-defined]
                    if hasattr(mod, 'TranscriptionService'):
                        self.transcriber = getattr(mod, 'TranscriptionService')()
        except Exception as e:
            logger.warning(f"⚠️ TranscriptionService indisponível: {e}")

        logger.info("✅ Visual Effects System inicializado")

    def _setup_platform_specs(self) -> Dict[Platform, PlatformSpecs]:
        return {
            Platform.TIKTOK: PlatformSpecs(resolution=(1080, 1920), aspect_ratio="9:16", max_duration=180, framerate=30, bitrate="2M", audio_format="aac"),
            Platform.YOUTUBE_SHORTS: PlatformSpecs(resolution=(1080, 1920), aspect_ratio="9:16", max_duration=60, framerate=30, bitrate="2.5M", audio_format="aac"),
            Platform.INSTAGRAM_REELS: PlatformSpecs(resolution=(1080, 1920), aspect_ratio="9:16", max_duration=90, framerate=30, bitrate="2M", audio_format="aac"),
            Platform.FACEBOOK_REELS: PlatformSpecs(resolution=(
                1080, 1920), aspect_ratio="9:16", max_duration=60, framerate=30, bitrate="2M", audio_format="aac")
        }

    def _setup_visual_styles(self) -> Dict[str, VisualStyle]:
        return {
            "modern_tech": VisualStyle(name="Tecnologia Moderna", colors=["#00ff41", "#0080ff"], fonts=["Roboto"], effects=["neon_glow"], mood="futuristic", target_audience="tech_enthusiasts"),
            "misterio": VisualStyle(name="Mistério", colors=["#2c3e50", "#7f00ff"], fonts=["Times New Roman"], effects=["shadows"], mood="suspenseful", target_audience="all"),
            "bold_energetic": VisualStyle(name="Energia Vibrante", colors=["#ff0040", "#ff8c00"], fonts=["Impact"], effects=["pulse"], mood="energetic", target_audience="young_adults"),
            "minimal_elegant": VisualStyle(name="Elegância Minimalista", colors=["#2c3e50", "#ecf0f1"], fonts=["Helvetica"], effects=["fade_elegant"], mood="sophisticated", target_audience="professionals"),
        }

    def _setup_music_library(self) -> Dict[str, Dict]:
        # Em produção, este dicionário seria populado dinamicamente ou lido de um arquivo
        return {
            'misterio': {'urls': ['https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3'], 'volume': 0.25},
            'inspiracional': {'urls': ['https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3'], 'volume': 0.35},
            'educativo': {'urls': ['https://www.soundhelix.com/examples/mp3/SoundHelix-Song-4.mp3'], 'volume': 0.3},
        }

    def _setup_subtitle_styles(self) -> Dict[str, Dict]:
        return {
            'moderno': {
                'fontsize': 60,
                'color': 'white',
                'stroke_color': 'black',
                'stroke_width': 2,
                'font': 'Arial-Bold'
            },
            'neon': {
                'fontsize': 65,
                'color': '#00FFFF',
                'stroke_color': '#0080FF',
                'stroke_width': 3,
                'font': 'Arial-Bold'
            },
            'neon_yellow': {
                'fontsize': 62,
                'color': '#FFD700',  # amarelo
                'stroke_color': 'black',
                'stroke_width': 3,
                'font': 'Arial-Bold'
            },
            'elegante': {
                'fontsize': 55,
                'color': '#FFD700',
                'stroke_color': '#8B4513',
                'stroke_width': 2,
                'font': 'Times-Bold'
            }
        }

    async def create_video(self, audio_path: str, images: List[str], script: str, settings: Dict[str, Any]) -> Optional[str]:
        """Cria vídeo completo com áudio, imagens, legendas e música de fundo."""
        try:
            logger.info("🎬 Iniciando criação do vídeo...")

            # Verificar e converter audio_path se for URL
            logger.info(f"🔍 Audio path original: '{audio_path}'")
            logger.info(f"🔍 MEDIA_DIR: '{config.MEDIA_DIR}'")
            
            if audio_path.startswith('/media/'):
                # Converter URL relativa para caminho absoluto
                relative_path = audio_path[len('/media/'):]
                logger.info(f"🔍 Relative path extraído: '{relative_path}'")
                audio_path = str(config.MEDIA_DIR / relative_path)
                logger.info(f"🔄 Convertido audio_path para: {audio_path}")
                
                # Verificar se arquivo existe
                if not os.path.exists(audio_path):
                    logger.error(f"❌ Arquivo de áudio não encontrado: {audio_path}")
                    return None
                else:
                    logger.info(f"✅ Arquivo de áudio encontrado: {audio_path}")
                    
            elif audio_path.startswith('http'):
                # Baixar áudio se for URL completa
                logger.warning(f"⚠️ Áudio é URL completa, tentando converter: {audio_path}")
                filename = audio_path.split('/')[-1]
                local_audio_path = str(config.MEDIA_DIR / 'audio' / filename)
                if os.path.exists(local_audio_path):
                    audio_path = local_audio_path
                else:
                    logger.error(f"❌ Arquivo de áudio não encontrado: {local_audio_path}")
                    return None

            # Carregar áudio principal
            try:
                audio_clip = AudioFileClip(audio_path)
                
                # Verificar se o clip foi carregado corretamente
                if not hasattr(audio_clip, 'duration') or audio_clip.duration is None:
                    logger.error(f"❌ Áudio carregado mas sem duração válida: {audio_path}")
                    if audio_clip:
                        audio_clip.close()
                    return None
                    
                video_duration = audio_clip.duration
                logger.info(f"🎵 Áudio carregado com duração: {video_duration}s")
                
            except Exception as e:
                logger.error(f"❌ Erro ao carregar arquivo de áudio {audio_path}: {str(e)}")
                return None

            # Criar clipes de imagem com duração sincronizada e efeitos
            logger.info(f"🎬 Processando {len(images)} imagens para duração de {video_duration}s")
            image_clips = self._create_image_clips(images, video_duration, settings)
            
            if not image_clips:
                logger.error(f"❌ Nenhum clip de imagem foi criado a partir de {len(images)} imagens")
                return None
                
            logger.info(f"✅ {len(image_clips)} clips de imagem criados com sucesso")

            # Gerar legendas com transcrição (se habilitado e disponível)
            subtitle_mode = settings.get('subtitle_mode')  # 'script' | 'transcribe'
            if subtitle_mode == 'transcribe' and self.transcriber and getattr(self.transcriber, 'transcribe', None):
                try:
                    segments = self.transcriber.transcribe(audio_path)
                except Exception as trans_err:
                    logger.warning(f"⚠️ Falha na transcrição, caindo para legendas por script: {trans_err}")
                    segments = None
                subtitle_clip = await self._create_subtitles(script, video_duration, settings.get('subtitle_style', 'moderno'), segments)
            else:
                subtitle_clip = await self._create_subtitles(script, video_duration, settings.get('subtitle_style', 'moderno'))

            # Adicionar música de fundo
            final_audio = await self._process_audio(audio_clip, video_duration, settings)

            # Combinar todos os elementos visuais
            video_clips = image_clips
            if subtitle_clip:
                video_clips.append(subtitle_clip)

            final_video = CompositeVideoClip(video_clips, size=(
                config.VIDEO_WIDTH, config.VIDEO_HEIGHT))

            # Adicionar áudio final
            logger.info(f"🎵 Adicionando áudio ao vídeo - Duração: {final_audio.duration}s")
            final_video = final_video.with_audio(final_audio)
            final_video = final_video.with_duration(video_duration)

            # Salvar vídeo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"video_final_{timestamp}.mp4"
            output_path = self.videos_dir / output_filename

            final_video.write_videofile(
                str(output_path), fps=config.VIDEO_FPS, codec='libx264', audio_codec='aac')

            logger.info(f"✅ Vídeo criado com sucesso: {output_path}")
            return str(output_path)

        except Exception as e:
            logger.error(f"❌ Erro ao criar vídeo: {str(e)}")
            logger.error(f"❌ Tipo do erro: {type(e).__name__}")
            import traceback
            logger.error(f"❌ Traceback completo: {traceback.format_exc()}")
            return None

    def _create_image_clips(self, images: List[str], total_duration: float, settings: Optional[Dict[str, Any]] = None) -> List[ImageClip]:
        """Cria clipes de imagem com duração e transições.
        Regras:
        - Entre 1.5s e 3.0s por imagem (Regra dos 3s), mantendo dinamismo.
        - Repete o conjunto de imagens para preencher todo o áudio, se necessário.
        """
        if not images:
            return []
        clips = []

        # Parâmetros de pacing
        mincut = float(settings.get('min_cut', 1.5)) if settings else 1.5
        maxcut = float(settings.get('max_cut', 3.0)) if settings else 3.0
        if mincut > maxcut:
            mincut, maxcut = maxcut, mincut

        # Número alvo de clipes para cobrir todo o áudio
        target_num = max(1, int(math.ceil(total_duration / maxcut)))

        # Se temos menos imagens que o necessário, repetir/ciclar
        base_images = list(images)
        if len(base_images) == 0:
            return []
        if len(base_images) < target_num:
            images_sequence = [base_images[i % len(base_images)] for i in range(target_num)]
        else:
            images_sequence = base_images[:target_num]

        # Gerar durações aleatórias dentro do intervalo e ajustar para fechar exatamente a duração total
        durations = []
        remaining = total_duration
        for idx in range(len(images_sequence)):
            if idx == len(images_sequence) - 1:
                dur = max(0.2, remaining)
            else:
                dur = random.uniform(mincut, maxcut)
                # Não ultrapassar o restante menos um mínimo para os próximos
                max_allowed = max(0.2, remaining - (mincut * (len(images_sequence) - idx - 1)))
                dur = min(dur, max_allowed)
            durations.append(dur)
            remaining = max(0.0, remaining - dur)
        # Correção numérica para fechar total
        if durations:
            diff = total_duration - sum(durations)
            durations[-1] = max(0.2, durations[-1] + diff)

        for i, (original_image_path, duration_per_image) in enumerate(zip(images_sequence, durations)):
            try:
                logger.info(f"🖼️ Processando imagem {i+1}/{len(images)}: {original_image_path}")
                
                image_path = original_image_path  # Variável para armazenar o caminho final
                
                # Converter URL para caminho local se necessário
                if original_image_path.startswith('/media/'):
                    # Converter URL relativa para caminho absoluto
                    relative_path = original_image_path[len('/media/'):]
                    local_path = str(config.MEDIA_DIR / relative_path)
                    logger.info(f"🔄 Convertendo para caminho local: {local_path}")
                    
                    if os.path.exists(local_path):
                        image_path = local_path
                        logger.info(f"✅ Arquivo encontrado: {image_path}")
                    else:
                        logger.error(f"❌ Arquivo de imagem não encontrado: {local_path}")
                        continue
                        
                elif original_image_path.startswith('http'):
                    # Extrair nome do arquivo da URL
                    filename = original_image_path.split('/')[-1]
                    local_path = str(config.IMAGES_DIR / filename)
                    
                    # Verificar se o arquivo já existe localmente
                    if os.path.exists(local_path):
                        image_path = local_path
                        logger.info(f"✅ Usando arquivo local existente: {local_path}")
                    else:
                        logger.warning(f"⚠️ Arquivo de imagem não encontrado localmente: {local_path}")
                        # Tentar baixar a imagem
                        try:
                            import requests
                            response = requests.get(original_image_path, timeout=10)
                            if response.status_code == 200:
                                with open(local_path, 'wb') as f:
                                    f.write(response.content)
                                image_path = local_path
                                logger.info(f"📥 Imagem baixada: {local_path}")
                            else:
                                logger.error(f"❌ Erro ao baixar imagem: {response.status_code}")
                                continue
                        except Exception as download_error:
                            logger.error(f"❌ Erro ao baixar imagem {original_image_path}: {download_error}")
                            continue
                
                # Criar clip da imagem
                logger.info(f"🎬 Criando ImageClip para CAMINHO FINAL: {image_path}")
                logger.info(f"🔍 Verificando se arquivo existe: {os.path.exists(image_path)}")
                
                if not os.path.exists(image_path):
                    logger.error(f"❌ ERRO CRÍTICO: Arquivo não existe no caminho final: {image_path}")
                    continue
                
                clip = ImageClip(image_path, duration=duration_per_image)
                clip = clip.resized(height=getattr(config, 'VIDEO_HEIGHT', 1920)).with_position('center')
                # Leve movimento para reduzir monotonia (ken-burns leve)
                try:
                    start_scale = 1.0
                    end_scale = 1.05
                    def zoom_effect(get_frame, t, s0=start_scale, s1=end_scale, dur=duration_per_image):
                        alpha = min(1.0, max(0.0, t / max(0.001, dur)))
                        scale = s0 + (s1 - s0) * alpha
                        frame = get_frame(t)
                        h, w = frame.shape[0], frame.shape[1]
                        nh, nw = int(h * scale), int(w * scale)
                        # padding crop
                        dy = max(0, (nh - h) // 2)
                        dx = max(0, (nw - w) // 2)
                        # Safe crop
                        zoomed = cv2.resize(frame, (nw, nh))
                        zoomed = zoomed[dy:dy+h, dx:dx+w]
                        return zoomed
                    clip = clip.fl(lambda gf, t: zoom_effect(gf, t))
                except Exception:
                    pass
                clip = clip.with_start(i * duration_per_image)
                clips.append(clip)
                logger.info(f"✅ Clip {i+1} criado com sucesso - duração: {duration_per_image}s")
            except Exception as e:
                logger.error(f"❌ Erro ao processar imagem {original_image_path}: {e}")
                continue

        return clips

    async def _create_subtitles(self, script: str, duration: float, style: str = 'moderno', segments: Optional[List[Dict[str, Any]]] = None) -> Optional[CompositeVideoClip]:
        """Cria legendas.
        - Se segments for fornecido, usa {start, end, text} (em segundos) para sincronização precisa.
        - Caso contrário, divide o script uniformemente pelo tempo total.
        """
        # Esta é uma implementação simplificada. Em um sistema real,
        # você usaria uma transcrição com timestamps para sincronizar.
        try:
            # Compat: mapear estilo 'tiktok' para 'moderno'
            if style == 'tiktok':
                style = 'moderno'
            style_config = self.subtitle_styles.get(style, self.subtitle_styles['moderno'])

            subtitle_clips = []
            style_config = self.subtitle_styles.get(style, self.subtitle_styles['moderno'])

            if segments:
                base_segments = [seg for seg in segments if seg.get('text')]
                for seg in base_segments:
                    start_time = max(0.0, float(seg.get('start', 0.0)))
                    end_time = min(duration, float(seg.get('end', duration)))
                    if end_time <= start_time:
                        continue
                    text = str(seg.get('text', '')).strip()
                    if not text:
                        continue
                    try:
                        txt_clip = TextClip(
                            text=text,
                            font_size=int(style_config.get('fontsize', 56)),
                            color=str(style_config.get('color', 'white')),
                            stroke_color=str(style_config.get('stroke_color', 'black')),
                            stroke_width=int(style_config.get('stroke_width', 2)),
                            size=(int(config.VIDEO_WIDTH*0.9), None),
                            font=str(style_config.get('font', 'Arial-Bold')),
                            method='caption'
                        )
                        txt_clip = txt_clip.with_position(('center', 'bottom')).with_start(start_time).with_duration(end_time - start_time)
                        subtitle_clips.append(txt_clip)
                    except Exception as subtitle_error:
                        logger.warning(f"⚠️ Erro ao criar legenda (transcribe) '{text[:30]}...': {subtitle_error}")
                        continue
            else:
                sentences = [s.strip() for s in script.split('.') if s.strip()]
                if not sentences:
                    return None
                time_per_sentence = duration / len(sentences)
                for i, sentence in enumerate(sentences):
                    start_time = i * time_per_sentence
                    end_time = min((i + 1) * time_per_sentence, duration)
                    try:
                        txt_clip = TextClip(
                            text=sentence,
                            font_size=int(style_config.get('fontsize', 56)),
                            color=str(style_config.get('color', 'white')),
                            stroke_color=str(style_config.get('stroke_color', 'black')),
                            stroke_width=int(style_config.get('stroke_width', 2)),
                            size=(int(config.VIDEO_WIDTH*0.9), None),
                            font=str(style_config.get('font', 'Arial-Bold')),
                            method='caption'
                        )
                        txt_clip = txt_clip.with_position(('center', 'bottom')).with_start(start_time).with_duration(end_time - start_time)
                        subtitle_clips.append(txt_clip)
                    except Exception as subtitle_error:
                        logger.warning(f"⚠️ Erro ao criar legenda para frase '{sentence[:30]}...': {subtitle_error}")
                        continue

            if subtitle_clips:
                logger.info(f"✅ {len(subtitle_clips)} legendas criadas com sucesso")
                return CompositeVideoClip(subtitle_clips, size=(getattr(config, 'VIDEO_WIDTH', 1080), getattr(config, 'VIDEO_HEIGHT', 1920)))
            else:
                logger.warning("⚠️ Nenhuma legenda foi criada com sucesso")

        except Exception as e:
            logger.error(f"❌ Erro ao criar legendas: {e}")

        return None

    async def _process_audio(self, audio_clip: AudioFileClip, video_duration: float, settings: Optional[Dict[str, Any]] = None) -> AudioFileClip:
        """Processa o áudio principal e adiciona música de fundo se necessário."""
        try:
            background_music = None
            music_volume = 0.3
            if settings:
                background_music = settings.get('background_music', settings.get('background_music_category'))
                music_volume = float(settings.get('music_volume', 0.3) or 0.3)
            logger.info(f"🎵 Processando áudio - Categoria música: {background_music}")
            logger.info(f"🎵 Duração do áudio principal: {audio_clip.duration}s")

            if not background_music or background_music == 'none':
                logger.info("🎵 Sem música de fundo, retornando áudio principal")
                return audio_clip.with_duration(video_duration)

            # URLs de música de fundo gratuita
            music_urls = {
                'upbeat': 'https://www.soundjay.com/misc/sounds/gaming_music_loop.wav',
                'chill': 'https://www.soundjay.com/misc/sounds/chill_background.wav',
                'energetic': 'https://www.soundjay.com/misc/sounds/upbeat_loop.wav',
                'ambient': 'https://www.soundjay.com/misc/sounds/ambient_music.wav'
            }
            
            # Usar uma música padrão se a categoria não existir
            music_url = music_urls.get(background_music, music_urls['upbeat'])
            
            try:
                # Baixar música de fundo
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                # Definir extensão por Content-Type ou pela URL
                def _choose_ext(resp, url):
                    ct = resp.headers.get('Content-Type', '').lower()
                    if 'mpeg' in ct or 'mp3' in ct:
                        return 'mp3'
                    if 'wav' in ct or url.lower().endswith('.wav'):
                        return 'wav'
                    if url.lower().endswith('.mp3'):
                        return 'mp3'
                    return 'mp3'
                
                import requests
                response = requests.get(music_url, timeout=30)
                if response.status_code == 200:
                    ext = _choose_ext(response, music_url)
                    music_filename = f"bg_music_{background_music}_{timestamp}.{ext}"
                    music_path = config.MUSIC_DIR / music_filename
                
                    logger.info(f"🎵 Baixando música de fundo de: {music_url}")
                    with open(music_path, 'wb') as f:
                        f.write(response.content)
                    logger.info(f"🎵 Música baixada: {music_path}")
                    
                    # Carregar música de fundo com fallback
                    try:
                        bg_music = AudioFileClip(str(music_path))
                    except Exception as load_err:
                        logger.warning(f"⚠️ Falha ao carregar música {music_path}: {load_err}. Continuando sem música de fundo.")
                        return audio_clip.with_duration(video_duration)
                    
                    try:
                        # Ajustar volume da música (mais baixo que a voz)
                        bg_music = bg_music.with_duration(video_duration)
                        bg_music = bg_music.multiply_volume(music_volume)
                        
                        # Misturar áudio principal com música de fundo
                        final_audio = CompositeAudioClip([
                            audio_clip.with_duration(video_duration),
                            bg_music
                        ])
                        
                        logger.info(f"✅ Música de fundo adicionada com sucesso")
                        return final_audio
                    except Exception as mix_err:
                        logger.warning(f"⚠️ Erro ao mixar música de fundo: {mix_err}. Continuando sem música.")
                        return audio_clip.with_duration(video_duration)
                    
                else:
                    logger.warning(f"⚠️ Erro ao baixar música: {response.status_code}")
                    return audio_clip.with_duration(video_duration)
                    
            except Exception as music_error:
                logger.warning(f"⚠️ Erro ao processar música de fundo: {music_error}")
                return audio_clip.with_duration(video_duration)
                
        except Exception as e:
            logger.error(f"❌ Erro no processamento de áudio: {e}")
            return audio_clip.with_duration(video_duration)

    async def _download_background_music(self, url: str, category: str) -> Optional[str]:
        """Download e cache de música de fundo."""
        try:
            music_filename = f"bg_music_{category}.mp3"
            music_path = self.audio_dir / music_filename

            if music_path.exists():
                return str(music_path)

            response = requests.get(url, timeout=10)
            response.raise_for_status()

            with open(music_path, 'wb') as f:
                f.write(response.content)

            logger.info(f"✅ Música de fundo baixada: {music_path}")
            return str(music_path)

        except Exception as e:
            logger.error(f"❌ Erro ao baixar música de fundo: {e}")
            return None

    def get_available_subtitle_styles(self) -> List[Dict[str, Any]]:
        """Retorna estilos de legenda disponíveis."""
        return [{"id": k, "name": k.title(), "preview": {"color": v['color'], "fontsize": v['fontsize']}} for k, v in self.subtitle_styles.items()]

    def get_available_music_categories(self) -> List[Dict[str, Any]]:
        """Retorna categorias de música disponíveis."""
        return [{"id": k, "name": k.title(), "volume": v['volume']} for k, v in self.music_library.items()]
