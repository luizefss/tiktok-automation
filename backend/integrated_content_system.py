# /var/www/tiktok-automation/backend/integrated_content_system.py

"""
Sistema Integrado de Criação e Publicação de Conteúdo
Combina TTS + Efeitos Visuais + Publicação Multi-Plataforma
"""

import os
import sys
import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
import json

# Adiciona o diretório do suaobra ao path para importar TTS
suaobra_backend = "/var/www/tiktok-automation/backend"
if suaobra_backend not in sys.path:
    sys.path.append(suaobra_backend)

# Importações dos sistemas desenvolvidos
try:
    from google_ai_studio_tts_enhanced import GoogleAIStudioTTSEnhanced
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    logging.warning("⚠️ Sistema TTS não disponível")

try:
    from visual_effects_system import VisualEffectsSystem, create_multi_platform_video
    VISUAL_EFFECTS_AVAILABLE = True
except ImportError:
    VISUAL_EFFECTS_AVAILABLE = False
    logging.warning("⚠️ Sistema de Efeitos Visuais não disponível")

try:
    from multi_platform_publisher import MultiPlatformPublisher, PublishRequest, Platform
    PUBLISHER_AVAILABLE = True
except ImportError:
    PUBLISHER_AVAILABLE = False
    logging.warning("⚠️ Sistema de Publicação não disponível")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ContentRequest:
    """Solicitação completa de criação de conteúdo"""
    # Texto para conversão
    text: str
    
    # Configurações de áudio
    voice_name: str = "pt-BR-Neural2-A"
    emotion: str = "neutral"
    
    # Configurações visuais
    visual_style: str = "modern_tech"
    platform_specs: List[str] = None
    
    # Configurações de publicação
    title: str = ""
    description: str = ""
    tags: List[str] = None
    platforms: List[Platform] = None
    
    # Agendamento
    schedule_time: Optional[datetime] = None
    
    def __post_init__(self):
        if self.platform_specs is None:
            self.platform_specs = ["tiktok", "instagram_reels", "youtube_shorts"]
        if self.tags is None:
            self.tags = []
        if self.platforms is None:
            self.platforms = [Platform.TIKTOK, Platform.INSTAGRAM_REELS, Platform.YOUTUBE_SHORTS]

@dataclass
class ContentResult:
    """Resultado da criação de conteúdo"""
    success: bool
    audio_files: Dict[str, str] = None
    video_files: Dict[str, str] = None
    publish_results: Dict[Platform, Any] = None
    error_message: str = ""
    processing_time: float = 0.0
    
    def __post_init__(self):
        if self.audio_files is None:
            self.audio_files = {}
        if self.video_files is None:
            self.video_files = {}
        if self.publish_results is None:
            self.publish_results = {}

class IntegratedContentSystem:
    """
    Sistema Integrado Completo
    TTS → Efeitos Visuais → Publicação Multi-Plataforma
    """
    
    def __init__(self):
        logger.info("🚀 Inicializando Sistema Integrado de Conteúdo...")
        
        # Inicializa subsistemas
        self.tts_system = None
        self.visual_system = None
        self.publisher = None
        
        self._initialize_subsystems()
        
        # Configurações
        self.temp_dir = Path("/tmp/content_creation")
        self.temp_dir.mkdir(exist_ok=True)
        
        # Cache e histórico
        self.content_history = []
        
        logger.info("✅ Sistema Integrado inicializado")

    def _initialize_subsystems(self):
        """Inicializa todos os subsistemas"""
        
        # Sistema TTS
        if TTS_AVAILABLE:
            try:
                self.tts_system = GoogleAIStudioTTSEnhanced()
                logger.info("✅ Sistema TTS carregado")
            except Exception as e:
                logger.error(f"❌ Erro ao carregar TTS: {e}")
        
        # Sistema de Efeitos Visuais
        if VISUAL_EFFECTS_AVAILABLE:
            try:
                self.visual_system = VisualEffectsSystem()
                logger.info("✅ Sistema de Efeitos Visuais carregado")
            except Exception as e:
                logger.error(f"❌ Erro ao carregar Efeitos Visuais: {e}")
        
        # Sistema de Publicação
        if PUBLISHER_AVAILABLE:
            try:
                self.publisher = MultiPlatformPublisher()
                logger.info("✅ Sistema de Publicação carregado")
            except Exception as e:
                logger.error(f"❌ Erro ao carregar Publisher: {e}")

    async def create_and_publish_content(self, request: ContentRequest) -> ContentResult:
        """
        Pipeline completo de criação e publicação de conteúdo
        """
        start_time = datetime.now()
        logger.info(f"🎬 Iniciando criação de conteúdo: '{request.text[:50]}...'")
        
        try:
            result = ContentResult(success=False)
            
            # 1. Geração de Áudio (TTS)
            logger.info("🎵 Etapa 1: Gerando áudio...")
            audio_files = await self._generate_audio(request)
            if not audio_files:
                return ContentResult(
                    success=False, 
                    error_message="Falha na geração de áudio"
                )
            result.audio_files = audio_files
            
            # 2. Criação de Vídeos com Efeitos
            logger.info("🎨 Etapa 2: Criando vídeos com efeitos...")
            video_files = await self._create_videos(request, audio_files)
            if not video_files:
                return ContentResult(
                    success=False,
                    error_message="Falha na criação de vídeos",
                    audio_files=audio_files
                )
            result.video_files = video_files
            
            # 3. Publicação Multi-Plataforma
            logger.info("📡 Etapa 3: Publicando em plataformas...")
            publish_results = await self._publish_content(request, video_files)
            result.publish_results = publish_results
            
            # 4. Finalização
            processing_time = (datetime.now() - start_time).total_seconds()
            result.processing_time = processing_time
            result.success = True
            
            # Salva no histórico
            self._save_to_history(request, result)
            
            logger.info(f"✅ Conteúdo criado e publicado em {processing_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"❌ Erro no pipeline: {e}")
            processing_time = (datetime.now() - start_time).total_seconds()
            return ContentResult(
                success=False,
                error_message=str(e),
                processing_time=processing_time
            )

    async def _generate_audio(self, request: ContentRequest) -> Dict[str, str]:
        """Gera arquivos de áudio usando TTS"""
        if not self.tts_system:
            logger.error("❌ Sistema TTS não disponível")
            return {}
        
        try:
            audio_files = {}
            
            # Gera áudio principal
            logger.info(f"🎤 Gerando áudio com voz {request.voice_name}")
            
            # Usa a API do TTS Enhanced
            audio_path = await asyncio.to_thread(
                self.tts_system.synthesize_speech_official,
                request.text,
                emotion=request.emotion,
                voice_profile=request.voice_name
            )
            
            if audio_path and os.path.exists(audio_path):
                # Salva arquivo principal
                main_audio_path = self.temp_dir / f"audio_main_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
                
                # Copia o arquivo gerado
                import shutil
                shutil.copy2(audio_path, main_audio_path)
                
                audio_files['main'] = str(main_audio_path)
                logger.info(f"✅ Áudio principal gerado: {main_audio_path}")
                
                # Gera variações se necessário
                for i, platform in enumerate(request.platform_specs):
                    if platform != 'main':
                        # Copia o áudio principal para cada plataforma
                        platform_audio_path = self.temp_dir / f"audio_{platform}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
                        
                        shutil.copy2(main_audio_path, platform_audio_path)
                        audio_files[platform] = str(platform_audio_path)
                
                return audio_files
            else:
                logger.error("❌ Falha na síntese de áudio")
                return {}
                
        except Exception as e:
            logger.error(f"❌ Erro na geração de áudio: {e}")
            return {}

    async def _create_videos(self, request: ContentRequest, audio_files: Dict[str, str]) -> Dict[str, str]:
        """Cria vídeos com efeitos visuais"""
        if not self.visual_system:
            logger.error("❌ Sistema de Efeitos Visuais não disponível")
            return {}
        
        try:
            video_files = {}
            
            for platform, audio_path in audio_files.items():
                if platform == 'main':
                    continue
                    
                logger.info(f"🎬 Criando vídeo para {platform}")
                
                # Configurações específicas da plataforma
                platform_config = self._get_platform_video_config(platform)
                
                # Gera vídeo usando o sistema de efeitos visuais
                video_result = await asyncio.to_thread(
                    create_multi_platform_video,
                    audio_path,
                    {
                        "text": request.text,
                        "platforms": [platform],
                        "style": request.visual_style
                    }
                )
                
                if video_result and video_result.get('success'):
                    platform_videos = video_result.get('videos', {})
                    if platform in platform_videos:
                        video_files[platform] = platform_videos[platform]
                        logger.info(f"✅ Vídeo criado para {platform}: {platform_videos[platform]}")
                    else:
                        logger.warning(f"⚠️ Vídeo não gerado para {platform}")
                else:
                    logger.error(f"❌ Falha na criação de vídeo para {platform}")
            
            return video_files
            
        except Exception as e:
            logger.error(f"❌ Erro na criação de vídeos: {e}")
            return {}

    def _get_platform_video_config(self, platform: str) -> Dict[str, Any]:
        """Retorna configurações específicas de vídeo por plataforma"""
        configs = {
            "tiktok": {
                "resolution": (1080, 1920),
                "fps": 30,
                "duration_max": 180,
                "aspect_ratio": "9:16"
            },
            "instagram_reels": {
                "resolution": (1080, 1920),
                "fps": 30,
                "duration_max": 90,
                "aspect_ratio": "9:16"
            },
            "youtube_shorts": {
                "resolution": (1080, 1920),
                "fps": 30,
                "duration_max": 60,
                "aspect_ratio": "9:16"
            },
            "facebook_reels": {
                "resolution": (1080, 1920),
                "fps": 30,
                "duration_max": 60,
                "aspect_ratio": "9:16"
            },
            "twitter": {
                "resolution": (1920, 1080),
                "fps": 30,
                "duration_max": 140,
                "aspect_ratio": "16:9"
            }
        }
        
        return configs.get(platform, configs["tiktok"])

    async def _publish_content(self, request: ContentRequest, video_files: Dict[str, str]) -> Dict[Platform, Any]:
        """Publica conteúdo nas plataformas"""
        if not self.publisher:
            logger.error("❌ Sistema de Publicação não disponível")
            return {}
        
        try:
            publish_results = {}
            
            for platform in request.platforms:
                platform_key = platform.value.lower()
                
                if platform_key in video_files:
                    video_path = video_files[platform_key]
                    
                    # Cria solicitação de publicação
                    publish_request = PublishRequest(
                        video_path=video_path,
                        title=request.title or f"Conteúdo Automático - {datetime.now().strftime('%d/%m/%Y')}",
                        description=request.description or request.text[:100],
                        tags=request.tags,
                        platforms=[platform],
                        schedule_time=request.schedule_time
                    )
                    
                    # Publica
                    result = await self.publisher.publish_multi_platform(publish_request)
                    publish_results.update(result)
                    
                    logger.info(f"📱 Publicação em {platform.value}: {result[platform].status.value}")
                else:
                    logger.warning(f"⚠️ Vídeo não disponível para {platform.value}")
            
            return publish_results
            
        except Exception as e:
            logger.error(f"❌ Erro na publicação: {e}")
            return {}

    def _save_to_history(self, request: ContentRequest, result: ContentResult):
        """Salva no histórico de conteúdo"""
        history_entry = {
            "timestamp": datetime.now().isoformat(),
            "request": {
                "text": request.text[:100] + "..." if len(request.text) > 100 else request.text,
                "voice_name": request.voice_name,
                "emotion": request.emotion,
                "visual_style": request.visual_style,
                "platforms": [p.value for p in request.platforms],
                "title": request.title
            },
            "result": {
                "success": result.success,
                "processing_time": result.processing_time,
                "audio_files_count": len(result.audio_files),
                "video_files_count": len(result.video_files),
                "published_platforms": len(result.publish_results),
                "error_message": result.error_message
            }
        }
        
        self.content_history.append(history_entry)
        
        # Salva em arquivo
        history_file = self.temp_dir / "content_history.json"
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(self.content_history, f, indent=2, ensure_ascii=False)

    async def create_content_batch(self, requests: List[ContentRequest]) -> List[ContentResult]:
        """Cria múltiplos conteúdos em lote"""
        logger.info(f"📦 Processando lote de {len(requests)} conteúdos...")
        
        results = []
        
        for i, request in enumerate(requests, 1):
            logger.info(f"🔄 Processando conteúdo {i}/{len(requests)}")
            
            result = await self.create_and_publish_content(request)
            results.append(result)
            
            # Delay entre processamentos para evitar rate limiting
            if i < len(requests):
                await asyncio.sleep(2)
        
        successful = sum(1 for r in results if r.success)
        logger.info(f"✅ Lote concluído: {successful}/{len(requests)} sucessos")
        
        return results

    def get_system_status(self) -> Dict[str, Any]:
        """Retorna status dos sistemas"""
        return {
            "systems": {
                "tts": TTS_AVAILABLE and self.tts_system is not None,
                "visual_effects": VISUAL_EFFECTS_AVAILABLE and self.visual_system is not None,
                "publisher": PUBLISHER_AVAILABLE and self.publisher is not None
            },
            "content_history_count": len(self.content_history),
            "temp_directory": str(self.temp_dir),
            "last_update": datetime.now().isoformat()
        }

    def cleanup_temp_files(self, older_than_hours: int = 24):
        """Remove arquivos temporários antigos"""
        logger.info(f"🧹 Limpando arquivos temporários...")
        
        cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
        removed_count = 0
        
        for file_path in self.temp_dir.glob("*"):
            if file_path.is_file():
                file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_time < cutoff_time:
                    try:
                        file_path.unlink()
                        removed_count += 1
                    except Exception as e:
                        logger.warning(f"⚠️ Erro ao remover {file_path}: {e}")
        
        logger.info(f"✅ {removed_count} arquivos temporários removidos")

# Instância global
integrated_system = IntegratedContentSystem()

# Funções de conveniência
async def create_content_from_text(
    text: str,
    title: str = "",
    description: str = "",
    tags: List[str] = None,
    voice: str = "pt-BR-Neural2-A",
    style: str = "modern_tech",
    platforms: List[str] = None
) -> ContentResult:
    """Função de conveniência para criação rápida de conteúdo"""
    
    if platforms is None:
        platforms = ["tiktok", "instagram_reels", "youtube_shorts"]
    
    if tags is None:
        tags = ["automatico", "ai", "conteudo"]
    
    # Converte strings de plataforma para enum
    platform_enums = []
    for platform in platforms:
        if platform.lower() == "tiktok":
            platform_enums.append(Platform.TIKTOK)
        elif platform.lower() in ["instagram_reels", "instagram"]:
            platform_enums.append(Platform.INSTAGRAM_REELS)
        elif platform.lower() in ["youtube_shorts", "youtube"]:
            platform_enums.append(Platform.YOUTUBE_SHORTS)
        elif platform.lower() in ["facebook_reels", "facebook"]:
            platform_enums.append(Platform.FACEBOOK_REELS)
        elif platform.lower() == "twitter":
            platform_enums.append(Platform.TWITTER)
        elif platform.lower() == "linkedin":
            platform_enums.append(Platform.LINKEDIN)
    
    request = ContentRequest(
        text=text,
        title=title,
        description=description,
        tags=tags,
        voice_name=voice,
        visual_style=style,
        platform_specs=platforms,
        platforms=platform_enums
    )
    
    return await integrated_system.create_and_publish_content(request)

async def create_scheduled_content(
    text: str,
    schedule_time: datetime,
    **kwargs
) -> ContentResult:
    """Cria conteúdo agendado"""
    request = ContentRequest(
        text=text,
        schedule_time=schedule_time,
        **kwargs
    )
    
    return await integrated_system.create_and_publish_content(request)

if __name__ == "__main__":
    # Exemplo de uso
    async def main():
        print("🚀 Testando Sistema Integrado...")
        
        # Status do sistema
        status = integrated_system.get_system_status()
        print(f"Status: {status}")
        
        # Teste básico
        if status['systems']['tts']:
            result = await create_content_from_text(
                text="Olá! Este é um teste do sistema integrado de criação de conteúdo.",
                title="Teste do Sistema",
                description="Demonstração do pipeline completo",
                tags=["teste", "demo", "automatico"]
            )
            
            print(f"Resultado: {result.success}")
            print(f"Tempo: {result.processing_time:.2f}s")
            if result.error_message:
                print(f"Erro: {result.error_message}")
        else:
            print("⚠️ Sistema TTS não disponível para teste")
    
    # asyncio.run(main())
