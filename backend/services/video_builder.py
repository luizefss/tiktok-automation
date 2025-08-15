# /var/www/tiktok-automation/backend/services/video_builder.py

import os
import logging
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
from moviepy import (
    AudioFileClip, ImageClip, TextClip, CompositeVideoClip, 
    CompositeAudioClip, concatenate_videoclips
)
from moviepy.video.tools.subtitles import SubtitlesClip
import pysrt
import numpy as np
import requests
import moviepy.config as mpy_config

logger = logging.getLogger(__name__)

# Configurar ImageMagick para MoviePy
try:
    mpy_config.change_settings({'IMAGEMAGICK_BINARY': '/usr/bin/convert'})
except Exception as e:
    logger.warning(f"Não foi possível configurar ImageMagick: {e}")

class VideoBuilderService:
    def __init__(self):
        # Diretórios
        self.videos_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "..", "media", "videos"
        )
        self.audio_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "..", "media", "audio"
        )
        os.makedirs(self.videos_dir, exist_ok=True)
        
        # Biblioteca de músicas por categoria
        self.music_library = {
            'tecnologia': {
                'urls': [
                    'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3',
                ],
                'volume': 0.3
            },
            'mistério': {
                'urls': [
                    'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3',
                ],
                'volume': 0.25
            },
            'inspiracional': {
                'urls': [
                    'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3',
                ],
                'volume': 0.35
            },
            'educativo': {
                'urls': [
                    'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-4.mp3',
                ],
                'volume': 0.3
            }
        }
        
        # Configurações de legendas
        self.subtitle_styles = {
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
            'elegante': {
                'fontsize': 55,
                'color': '#FFD700',
                'stroke_color': '#8B4513',
                'stroke_width': 2,
                'font': 'Times-Bold'
            }
        }
        
        # Configurações de transições
        self.transition_effects = {
            'corte': {'duration': 0.1},
            'fade': {'duration': 0.5},
            'slide': {'duration': 0.8},
            'zoom': {'duration': 0.6}
        }
        
        logger.info("✅ Video Builder Service inicializado")

    async def create_video(self, 
                         audio_path: str,
                         images: List[str], 
                         script: str,
                         settings: Dict[str, any]) -> Optional[str]:
        """
        Cria vídeo completo com áudio, imagens, legendas e música de fundo
        
        Args:
            audio_path: Caminho do arquivo de áudio da narração
            images: Lista de caminhos das imagens
            script: Roteiro original para gerar legendas
            settings: Configurações do vídeo (estilo, transições, etc.)
            
        Returns:
            Caminho do vídeo final gerado
        """
        try:
            logger.info("🎬 Iniciando criação do vídeo...")
            
            # Carregar áudio principal
            audio_clip = AudioFileClip(audio_path)
            video_duration = audio_clip.duration
            
            # Criar clipes de imagem com duração sincronizada
            image_clips = self._create_image_clips(images, video_duration)
            
            # Gerar legendas automáticas
            subtitle_clip = self._create_subtitles(script, video_duration, settings.get('subtitle_style', 'moderno'))
            
            # Adicionar música de fundo se especificada
            final_audio = await self._add_background_music(audio_clip, settings.get('background_music_category'))
            
            # Combinar todos os elementos visuais
            video_clips = image_clips + [subtitle_clip] if subtitle_clip else image_clips
            final_video = CompositeVideoClip(video_clips, size=(1080, 1920))  # Formato vertical
            
            # Adicionar áudio final
            final_video = final_video.set_audio(final_audio)
            final_video = final_video.set_duration(video_duration)
            
            # Salvar vídeo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"video_final_{timestamp}.mp4"
            output_path = os.path.join(self.videos_dir, output_filename)
            
            # Renderizar com configurações otimizadas
            final_video.write_videofile(
                output_path,
                fps=30,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True,
                verbose=False,
                logger=None
            )
            
            # Limpar recursos
            audio_clip.close()
            final_audio.close()
            final_video.close()
            for clip in image_clips:
                clip.close()
            if subtitle_clip:
                subtitle_clip.close()
            
            logger.info(f"✅ Vídeo criado com sucesso: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar vídeo: {e}")
            return None

    def _create_image_clips(self, images: List[str], total_duration: float) -> List[ImageClip]:
        """Cria clipes de imagem com duração e transições"""
        if not images:
            logger.warning("⚠️ Nenhuma imagem fornecida")
            return []
        
        clips = []
        duration_per_image = total_duration / len(images)
        
        for i, image_path in enumerate(images):
            try:
                if not os.path.exists(image_path):
                    logger.warning(f"⚠️ Imagem não encontrada: {image_path}")
                    continue
                
                # Criar clipe da imagem
                clip = ImageClip(image_path)
                
                # Redimensionar para formato vertical (9:16)
                clip = clip.resize(height=1920).resize(lambda t: 1 if t < 1080 else 1080/clip.w)
                clip = clip.set_position('center')
                
                # Definir tempo de início e duração
                start_time = i * duration_per_image
                clip = clip.set_start(start_time).set_duration(duration_per_image)
                
                # Adicionar efeito de zoom sutil
                def zoom_effect(get_frame, t):
                    frame = get_frame(t)
                    zoom_factor = 1 + (t / duration_per_image) * 0.1  # Zoom de 10%
                    return frame
                
                clip = clip.fl(zoom_effect)
                
                clips.append(clip)
                
            except Exception as e:
                logger.error(f"❌ Erro ao processar imagem {image_path}: {e}")
                continue
        
        return clips

    def _create_subtitles(self, script: str, duration: float, style: str = 'moderno') -> Optional[TextClip]:
        """Cria legendas automáticas baseadas no roteiro"""
        try:
            # Configuração do estilo
            style_config = self.subtitle_styles.get(style, self.subtitle_styles['moderno'])
            
            # Dividir roteiro em frases para sincronização
            sentences = [s.strip() for s in script.split('.') if s.strip()]
            if not sentences:
                return None
            
            # Calcular timing para cada frase
            time_per_sentence = duration / len(sentences)
            subtitle_clips = []
            
            for i, sentence in enumerate(sentences):
                if len(sentence) < 5:  # Ignorar frases muito curtas
                    continue
                
                start_time = i * time_per_sentence
                end_time = min((i + 1) * time_per_sentence, duration)
                
                # Criar clipe de texto
                txt_clip = TextClip(
                    sentence,
                    fontsize=style_config['fontsize'],
                    color=style_config['color'],
                    stroke_color=style_config['stroke_color'],
                    stroke_width=style_config['stroke_width'],
                    font=style_config['font'],
                    method='caption',
                    size=(1000, None),  # Largura fixa, altura automática
                    align='center'
                )
                
                txt_clip = txt_clip.set_position(('center', 'bottom')).set_start(start_time).set_duration(end_time - start_time)
                subtitle_clips.append(txt_clip)
            
            # Combinar todos os clipes de legenda
            if subtitle_clips:
                return CompositeVideoClip(subtitle_clips, size=(1080, 1920))
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar legendas: {e}")
            
        return None

    async def _add_background_music(self, main_audio: AudioFileClip, music_category: Optional[str] = None) -> AudioFileClip:
        """Adiciona música de fundo ao áudio principal"""
        if not music_category or music_category not in self.music_library:
            return main_audio
        
        try:
            music_config = self.music_library[music_category]
            music_url = music_config['urls'][0]  # Usar primeira música da categoria
            
            # Download da música (em produção, usar cache local)
            music_path = await self._download_background_music(music_url, music_category)
            
            if music_path and os.path.exists(music_path):
                # Carregar música de fundo
                bg_music = AudioFileClip(music_path)
                
                # Ajustar duração da música para corresponder ao áudio principal
                if bg_music.duration < main_audio.duration:
                    # Repetir música se for mais curta
                    loops_needed = int(main_audio.duration / bg_music.duration) + 1
                    bg_music = concatenate_videoclips([bg_music] * loops_needed)
                
                bg_music = bg_music.subclip(0, main_audio.duration)
                
                # Reduzir volume da música de fundo
                bg_music = bg_music.volumex(music_config['volume'])
                
                # Combinar áudios
                final_audio = CompositeAudioClip([main_audio, bg_music])
                
                bg_music.close()
                return final_audio
            
        except Exception as e:
            logger.error(f"❌ Erro ao adicionar música de fundo: {e}")
        
        return main_audio

    async def _download_background_music(self, url: str, category: str) -> Optional[str]:
        """Download e cache de música de fundo"""
        try:
            music_filename = f"bg_music_{category}.mp3"
            music_path = os.path.join(self.audio_dir, music_filename)
            
            # Verificar se já existe
            if os.path.exists(music_path):
                return music_path
            
            # Download da música
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            with open(music_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"✅ Música de fundo baixada: {music_path}")
            return music_path
            
        except Exception as e:
            logger.error(f"❌ Erro ao baixar música de fundo: {e}")
            return None

    def get_available_subtitle_styles(self) -> List[Dict[str, any]]:
        """Retorna estilos de legenda disponíveis"""
        styles = []
        for style_id, config in self.subtitle_styles.items():
            styles.append({
                "id": style_id,
                "name": style_id.title(),
                "preview": {
                    "color": config['color'],
                    "fontsize": config['fontsize']
                }
            })
        return styles

    def get_available_music_categories(self) -> List[Dict[str, any]]:
        """Retorna categorias de música disponíveis"""
        categories = []
        for category_id, config in self.music_library.items():
            categories.append({
                "id": category_id,
                "name": category_id.title(),
                "volume": config['volume']
            })
        return categories

# Instância global do serviço
video_builder = VideoBuilderService()
