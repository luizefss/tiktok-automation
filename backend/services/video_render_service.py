"""
Serviço de renderização de vídeo final integrando:
- Storyboard JSON (com scenes[])
- Advanced Image Service (DALL-E 3 + Imagen 3)
- Leonardo Motion (animação)
- ElevenLabs TTS (narração)
- MoviePy (montagem final)
"""

import os
import json
import asyncio
import tempfile
import shutil
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

# Importa o pipeline TTS/MoviePy
try:
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from tts_sync_pipeline import render_from_storyboard, get_voice_id, RECOMMENDED_VOICES
    TTS_AVAILABLE = True
    print("✅ TTS Pipeline importado com sucesso")
except ImportError as e:
    print(f"⚠️ TTS Pipeline não disponível: {e}")
    TTS_AVAILABLE = False

logger = logging.getLogger(__name__)

class VideoRenderService:
    def __init__(self):
        self.base_output_dir = os.path.join(os.getcwd(), "render_output")
        os.makedirs(self.base_output_dir, exist_ok=True)
        
        # Serviços necessários
        self.advanced_image_service = None
        self.leonardo_motion_service = None
        self.elevenlabs_service = None
        
        logger.info("🎬 Video Render Service inicializado")

    async def render_complete_video(
        self,
        storyboard_data: Dict[str, Any],
        voice_id: Optional[str] = None,
        elevenlabs_key: Optional[str] = None,
        music_path: Optional[str] = None,
        use_leonardo_motion: bool = True,
        use_elevenlabs_tts: bool = True
    ) -> Dict[str, Any]:
        """
        Pipeline completo: Storyboard -> Imagens -> Animação -> TTS -> Vídeo Final
        """
        try:
            logger.info("🎬 Iniciando renderização completa de vídeo")
            
            # 1. Criar workspace temporário
            workspace = self._create_workspace(storyboard_data)
            
            # 2. Gerar imagens para cada cena
            await self._generate_scene_images(storyboard_data, workspace)
            
            # 3. Animar imagens com Leonardo Motion (se habilitado)
            if use_leonardo_motion:
                await self._animate_scene_images(storyboard_data, workspace)
            
            # 4. Gerar narração com ElevenLabs (se habilitado)
            if use_elevenlabs_tts and voice_id and elevenlabs_key:
                await self._generate_scene_audio(storyboard_data, workspace, voice_id, elevenlabs_key)
            
            # 5. Montar vídeo final com MoviePy
            final_video_path = await self._assemble_final_video(
                storyboard_data, workspace, music_path
            )
            
            # 6. Limpar workspace temporário (opcional)
            # shutil.rmtree(workspace["temp_dir"])
            
            return {
                "success": True,
                "video_path": final_video_path,
                "workspace": workspace,
                "duration": storyboard_data.get("duration_target_sec", 60),
                "scenes_count": len(storyboard_data.get("scenes", []))
            }
            
        except Exception as e:
            logger.error(f"❌ Erro na renderização de vídeo: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }

    def _create_workspace(self, storyboard_data: Dict[str, Any]) -> Dict[str, str]:
        """Cria workspace temporário para renderização"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        title_safe = "".join(c for c in storyboard_data.get("title", "video")[:20] if c.isalnum() or c in "_-")
        
        temp_dir = os.path.join(self.base_output_dir, f"render_{title_safe}_{timestamp}")
        os.makedirs(temp_dir, exist_ok=True)
        
        workspace = {
            "temp_dir": temp_dir,
            "storyboard_path": os.path.join(temp_dir, "storyboard.json"),
            "assets_dir": os.path.join(temp_dir, "assets"),
            "images_dir": os.path.join(temp_dir, "images"),
            "videos_dir": os.path.join(temp_dir, "videos"),
            "audio_dir": os.path.join(temp_dir, "audio"),
            "final_video": os.path.join(temp_dir, "final.mp4")
        }
        
        # Criar subdiretórios
        for path in [workspace["assets_dir"], workspace["images_dir"], 
                    workspace["videos_dir"], workspace["audio_dir"]]:
            os.makedirs(path, exist_ok=True)
        
        # Salvar storyboard
        with open(workspace["storyboard_path"], "w", encoding="utf-8") as f:
            json.dump(storyboard_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"📁 Workspace criado: {temp_dir}")
        return workspace

    async def _generate_scene_images(self, storyboard_data: Dict[str, Any], workspace: Dict[str, str]):
        """Gera imagens para cada cena usando Advanced Image Service"""
        scenes = storyboard_data.get("scenes", [])
        logger.info(f"🎨 Gerando {len(scenes)} imagens de cena")
        
        for i, scene in enumerate(scenes, 1):
            image_prompt = scene.get("image_prompt", "")
            if not image_prompt:
                logger.warning(f"Cena {i} sem image_prompt - pulando")
                continue
            
            try:
                # Usar Advanced Image Service (DALL-E 3 como fallback do Imagen 3)
                if self.advanced_image_service:
                    result = await self.advanced_image_service.generate_image_with_fallback(
                        prompt=image_prompt,
                        scene_number=i,
                        output_dir=workspace["images_dir"]
                    )
                    if result.get("success"):
                        logger.info(f"✅ Imagem {i} gerada: {result.get('image_path')}")
                    else:
                        logger.error(f"❌ Falha na geração da imagem {i}: {result.get('error')}")
                else:
                    logger.warning(f"Advanced Image Service não disponível - criando placeholder para cena {i}")
                    # Criar arquivo placeholder
                    placeholder_path = os.path.join(workspace["images_dir"], f"scene_{i:02d}.jpg")
                    with open(placeholder_path, "w") as f:
                        f.write("placeholder")
                    
            except Exception as e:
                logger.error(f"❌ Erro ao gerar imagem da cena {i}: {e}")

    async def _animate_scene_images(self, storyboard_data: Dict[str, Any], workspace: Dict[str, str]):
        """Anima imagens usando Leonardo Motion"""
        scenes = storyboard_data.get("scenes", [])
        logger.info(f"🎬 Animando {len(scenes)} imagens com Leonardo Motion")
        
        for i, scene in enumerate(scenes, 1):
            image_path = os.path.join(workspace["images_dir"], f"scene_{i:02d}.jpg")
            video_path = os.path.join(workspace["videos_dir"], f"scene_{i:02d}.mp4")
            
            if not os.path.exists(image_path):
                logger.warning(f"Imagem da cena {i} não encontrada: {image_path}")
                continue
            
            motion_prompt = scene.get("motion_prompt", "slow cinematic zoom in, 9:16 vertical")
            duration = scene.get("t_end", 10) - scene.get("t_start", 0)
            
            try:
                # Usar Leonardo Motion Service
                if self.leonardo_motion_service:
                    result = await self.leonardo_motion_service.animate_image(
                        image_path=image_path,
                        motion_prompt=motion_prompt,
                        duration=duration,
                        output_path=video_path
                    )
                    if result.get("success"):
                        logger.info(f"✅ Animação {i} criada: {video_path}")
                    else:
                        logger.error(f"❌ Falha na animação {i}: {result.get('error')}")
                else:
                    logger.warning(f"Leonardo Motion Service não disponível - criando placeholder para cena {i}")
                    # Criar arquivo placeholder
                    with open(video_path, "w") as f:
                        f.write("placeholder video")
                        
            except Exception as e:
                logger.error(f"❌ Erro ao animar cena {i}: {e}")

    async def _generate_scene_audio(
        self, 
        storyboard_data: Dict[str, Any], 
        workspace: Dict[str, str],
        voice_id: str,
        elevenlabs_key: str
    ):
        """Gera narração para cada cena usando ElevenLabs"""
        scenes = storyboard_data.get("scenes", [])
        logger.info(f"🎤 Gerando narração para {len(scenes)} cenas com ElevenLabs")
        
        # Converte nome de voz para ID se necessário
        if TTS_AVAILABLE:
            actual_voice_id = get_voice_id(voice_id)
        else:
            actual_voice_id = voice_id
        
        for i, scene in enumerate(scenes, 1):
            narration = scene.get("narration", "").strip()
            if not narration:
                logger.warning(f"Cena {i} sem narração - pulando")
                continue
            
            audio_path = os.path.join(workspace["audio_dir"], f"scene_{i:02d}.wav")
            
            try:
                if TTS_AVAILABLE:
                    # Usar módulo TTS direto
                    from tts_sync_pipeline import elevenlabs_tts
                    elevenlabs_tts(
                        text=narration,
                        voice_id=actual_voice_id,
                        api_key=elevenlabs_key,
                        out_path=audio_path,
                        audio_format="wav",
                        stability=0.5,
                        similarity_boost=0.8
                    )
                    logger.info(f"✅ Áudio {i} gerado: {audio_path}")
                else:
                    logger.warning(f"TTS não disponível - criando placeholder para cena {i}")
                    # Criar arquivo placeholder
                    with open(audio_path, "w") as f:
                        f.write("placeholder audio")
                        
            except Exception as e:
                logger.error(f"❌ Erro ao gerar áudio da cena {i}: {e}")

    async def _assemble_final_video(
        self, 
        storyboard_data: Dict[str, Any], 
        workspace: Dict[str, str],
        music_path: Optional[str] = None
    ) -> str:
        """Monta vídeo final usando MoviePy através do render_pipeline.py"""
        logger.info("🎬 Montando vídeo final com MoviePy")
        
        try:
            # Preparar assets no formato esperado pelo render_pipeline
            assets_dir = workspace["assets_dir"]
            scenes = storyboard_data.get("scenes", [])
            
            for i, scene in enumerate(scenes, 1):
                # Copiar vídeos para assets (formato scene_XX.mp4)
                src_video = os.path.join(workspace["videos_dir"], f"scene_{i:02d}.mp4")
                dst_video = os.path.join(assets_dir, f"scene_{i:02d}.mp4")
                if os.path.exists(src_video) and os.path.getsize(src_video) > 0:
                    shutil.copy2(src_video, dst_video)
                
                # Copiar áudios para assets (formato scene_XX.wav)
                src_audio = os.path.join(workspace["audio_dir"], f"scene_{i:02d}.wav")
                dst_audio = os.path.join(assets_dir, f"scene_{i:02d}.wav")
                if os.path.exists(src_audio) and os.path.getsize(src_audio) > 0:
                    shutil.copy2(src_audio, dst_audio)
            
            # Usar TTS pipeline para montagem final
            if TTS_AVAILABLE:
                final_video_path = render_from_storyboard(
                    storyboard_path_or_dict=workspace["storyboard_path"],
                    assets_dir=assets_dir,
                    out_path=workspace["final_video"],
                    eleven_voice_id=None,  # Não gerar TTS aqui (já foi gerado)
                    eleven_api_key=None,
                    audio_format="wav",
                    music_path=music_path
                )
            else:
                # Fallback: montagem simples sem TTS
                from render_pipeline import assemble_video_from_storyboard
                final_video_path = assemble_video_from_storyboard(
                    storyboard_json_path=workspace["storyboard_path"],
                    assets_dir=assets_dir,
                    out_path=workspace["final_video"],
                    music_path=music_path,
                    crossfade_s=0.2
                )
            
            logger.info(f"✅ Vídeo final renderizado: {final_video_path}")
            return final_video_path
            
        except Exception as e:
            logger.error(f"❌ Erro na montagem final: {e}")
            raise

    def set_services(self, advanced_image_service=None, leonardo_motion_service=None, elevenlabs_service=None):
        """Define os serviços externos necessários"""
        self.advanced_image_service = advanced_image_service
        self.leonardo_motion_service = leonardo_motion_service  
        self.elevenlabs_service = elevenlabs_service
        logger.info("🔧 Serviços externos configurados para Video Render Service")

# Instância global
video_render_service = VideoRenderService()
