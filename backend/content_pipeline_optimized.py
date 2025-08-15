# /var/www/tiktok-automation/backend/content_pipeline_optimized.py

"""
Pipeline Otimizado de Criação de Conteúdo (Versão Unificada)
Orquestra o fluxo completo:
Tema → Roteiro c/ IA → Áudio c/ TTS → Imagens c/ AI → Vídeo → Publicação
"""

import asyncio
import logging
import os
import sys
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import json

# Importações dos sistemas de serviço
from services.image_generator import ImageGeneratorService  # Corrigido
from visual_effects_system import VisualEffectsSystem, Platform  # Corrigido
from ai_orchestrator import AIOrchestrator  # Corrigido
from trending_content_system import TrendingContentSystem  # Corrigido
from multi_platform_publisher import MultiPlatformPublisher, PublishRequest, PublishStatus
from enhanced_content_generator import EnhancedContentGenerator

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class ContentRequest:
    """Solicitação completa de criação de conteúdo"""
    # Tema ou roteiro personalizado
    theme: Optional[str] = None
    script: Optional[str] = None

    # Metadados do vídeo
    title: str = ""
    description: str = ""
    tags: List[str] = field(default_factory=list)

    # Configurações de IA e Mídia
    ai_provider: str = "gemini"  # gemini, claude, gpt, ou 'auto' para batalha
    video_style: str = "misterio"
    visual_style: str = "tecnologia"
    image_style: str = "realistic"
    num_images: int = 5

    # Configurações de áudio
    voice_style: str = "neutral"
    voice_accent: str = "brasileiro"

    # Publicação
    platforms: List[str] = field(default_factory=lambda: [
                                 "tiktok", "instagram_reels", "youtube_shorts"])
    schedule_time: Optional[datetime] = None


@dataclass
class ContentResult:
    """Resultado da criação de conteúdo"""
    success: bool
    script_data: Optional[Dict[str, Any]] = None
    audio_file: str = ""
    image_files: List[str] = field(default_factory=list)
    video_files: Dict[str, str] = field(default_factory=dict)
    publish_results: Dict[str, Any] = field(default_factory=dict)
    processing_time: float = 0.0
    error_message: str = ""


class ContentPipelineOptimized:
    """
    Pipeline Otimizado: Orquestra o fluxo de criação de conteúdo.
    """

    def __init__(self):
        logger.info("🚀 Inicializando Content Pipeline Optimized...")
        self.ai_orchestrator = AIOrchestrator()
        self.trending_system = TrendingContentSystem()
        self.image_service = ImageGeneratorService()
        self.video_service = VisualEffectsSystem()
        self.publisher = MultiPlatformPublisher()

        self.output_dir = Path(
            "/var/www/tiktok-automation/media/content_history")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info("✅ Content Pipeline inicializado")

    async def create_viral_now(self) -> ContentResult:
        """
        Modo "Viral Agora": Gera um vídeo a partir de um tema em alta.
        """
        try:
            logger.info(
                "🔥 MODO 'VIRAL AGORA' ATIVADO: Buscando tema em alta...")

            # Etapa 1: Obter tema viral
            viral_topic_data = self.trending_system.obter_topico_para_roteiro()
            if not viral_topic_data:
                raise Exception("Não foi possível obter um tópico viral.")

            theme = viral_topic_data['topic']
            video_style = viral_topic_data['categoria']

            # Cria a requisição com o tema viral
            request = ContentRequest(
                theme=theme,
                video_style=video_style,
                title=self.trending_system.gerar_titulo_viral(
                    theme, video_style),
                tags=viral_topic_data.get('keywords', [])
            )

            # Prossegue com o pipeline normal
            result = await self.create_content_from_request(request)

            if result.success:
                logger.info(f"🎉 'Viral Agora' concluído com sucesso!")
            else:
                logger.error(f"❌ Falha no modo 'Viral Agora'.")

            return result

        except Exception as e:
            logger.error(f"❌ Erro no modo 'Viral Agora': {e}")
            return ContentResult(success=False, error_message=str(e))

    async def create_content_from_request(self, request: ContentRequest) -> ContentResult:
        """
        Pipeline principal que processa a requisição completa.
        """
        start_time = datetime.now()
        logger.info(
            f"🎬 Iniciando pipeline para o tema: '{request.theme}' ou roteiro personalizado.")

        try:
            # 1. Geração de Roteiro e Áudio
            logger.info("📝🎵 Etapa 1: Gerando roteiro e áudio...")
            script_result = await self._generate_script_and_audio(request)
            if not script_result.get('success'):
                raise Exception(
                    f"Falha na geração de roteiro ou áudio: {script_result.get('error')}")

            script_data = script_result['script_data']
            audio_path = script_data.get('audio_path')

            # 2. Geração de Imagens
            logger.info("🎨 Etapa 2: Gerando imagens...")
            image_files = await self.image_service.generate_images_for_script(
                script_data=script_data,
                visual_style=request.visual_style
            )
            if not image_files:
                logger.warning(
                    "⚠️ Falha na geração de imagens, continuando com placeholders.")

            # 3. Criação de Vídeos
            logger.info("🎬 Etapa 3: Montando vídeos...")
            video_files = await self.video_service.create_video(
                audio_path=audio_path,
                images=image_files,
                script=script_data.get('roteiro_completo', ''),
                settings={"subtitle_style": "moderno",
                          "background_music_category": script_data.get('style')}
            )

            if not video_files:
                raise Exception("Falha na criação de vídeos.")

            # 4. Publicação Multi-Plataforma
            logger.info("📡 Etapa 4: Publicando em plataformas...")
            publish_results = await self._publish_content(request, video_files)

            processing_time = (datetime.now() - start_time).total_seconds()

            result = ContentResult(
                success=True,
                script_data=script_data,
                audio_file=audio_path,
                image_files=image_files,
                video_files=video_files,
                publish_results=publish_results,
                processing_time=processing_time
            )

            logger.info(f"✅ Pipeline concluído em {processing_time:.2f}s")
            self._save_result_summary(request, result)

            return result

        except Exception as e:
            logger.error(f"❌ Erro no pipeline: {e}")
            processing_time = (datetime.now() - start_time).total_seconds()
            return ContentResult(
                success=False,
                error_message=str(e),
                processing_time=processing_time
            )

    async def run_ai_battle(self, request: ContentRequest) -> ContentResult:
        """
        Executa uma batalha de IAs e usa o roteiro vencedor para gerar o vídeo.
        """
        try:
            logger.info("⚔️ MODO 'AI BATTLE' ATIVADO.")

            # Etapa 1: Batalha de roteiros
            battle_result = await self.ai_orchestrator.run_ai_battle(
                theme=request.theme,
                providers=request.ai_provider  # Espera uma lista de provedores
            )

            if not battle_result['success']:
                raise Exception(
                    f"A batalha de IAs falhou: {battle_result.get('error')}")

            # Usa o roteiro vencedor
            winner_script_data = battle_result['winner_script_data']
            winner_provider = battle_result['winner']
            logger.info(f"🏆 Roteiro vencedor da batalha: {winner_provider}")

            # Geração de áudio, imagens e vídeo com base no vencedor
            request.script = winner_script_data.get('roteiro_completo')
            request.title = winner_script_data.get('titulo')
            request.video_style = winner_script_data.get('style')

            # Passa o roteiro para o gerador de áudio
            # (Aqui pode ter um ajuste para o audio ser gerado a partir do winner_script)
            # A lógica de generate_script_and_audio já lida com isso se o script já estiver pronto
            result = await self.create_content_from_request(request)

            result.script_data['ai_battle_result'] = battle_result

            return result

        except Exception as e:
            logger.error(f"❌ Erro no modo 'AI Battle': {e}")
            return ContentResult(success=False, error_message=str(e))

    async def _generate_script_and_audio(self, request: ContentRequest) -> Dict[str, Any]:
        """
        Orquestra a geração de roteiro e áudio de forma unificada.
        """
        if request.script:
            # Caso o roteiro já venha pronto (produção manual)
            logger.info(
                "📝 Roteiro personalizado fornecido. Pulando geração de roteiro com IA.")

            # Criar um 'script_data' dummy para ser processado
            script_data = {
                'roteiro_completo': request.script,
                'titulo': request.title,
                'visual_cues': self.ai_orchestrator._extract_visual_cues(request.script),
                'style': request.video_style,
                'tone': request.voice_style
            }

            # Geração de áudio a partir do roteiro
            enhanced_content_generator = EnhancedContentGenerator()
            result = await asyncio.to_thread(enhanced_content_generator.preparar_e_gerar_audio, script_data)

            if result:
                return {"success": True, "script_data": result}
            else:
                return {"success": False, "error": "Falha ao gerar áudio do roteiro personalizado."}

        else:
            # Geração de roteiro e áudio completa (modo automático)
            enhanced_content_generator = EnhancedContentGenerator()
            result = await asyncio.to_thread(enhanced_content_generator.gerar_conteudo_completo, {
                "theme": request.theme,
                "video_style": request.video_style,
                "accent": request.voice_accent,
                "ai_provider": request.ai_provider
            })

            if result:
                return {"success": True, "script_data": result}
            else:
                return {"success": False, "error": "Falha na geração de roteiro e áudio com IA."}

    async def _publish_content(self, request: ContentRequest, video_files: Dict[str, str]) -> Dict[str, Any]:
        """
        Publica os vídeos gerados nas plataformas configuradas.
        """
        publish_results = {}
        for platform_str, video_path in video_files.items():
            try:
                platform_enum = Platform[platform_str.upper().replace(
                    '_REELS', '').replace('_SHORTS', '')]

                publish_request = PublishRequest(
                    video_path=video_path,
                    title=request.title,
                    description=request.description or request.theme,
                    tags=request.tags,
                    platforms=[platform_enum],
                    schedule_time=request.schedule_time
                )

                # A chamada real para o publicador
                result = await self.publisher.publish_multi_platform(publish_request)
                publish_results.update(
                    {platform_str: result.get(platform_enum, {}).status.value})

            except Exception as e:
                logger.error(f"❌ Erro na publicação para {platform_str}: {e}")
                publish_results[platform_str] = PublishStatus.FAILED.value

        return publish_results

    def _save_result_summary(self, request: ContentRequest, result: ContentResult):
        """Salva um resumo do resultado do pipeline."""
        try:
            summary = {
                "timestamp": datetime.now().isoformat(),
                "request": {
                    "theme": request.theme,
                    "title": request.title,
                    "platforms": request.platforms,
                    "video_style": request.video_style,
                },
                "result": {
                    "success": result.success,
                    "processing_time": result.processing_time,
                    "audio_file": result.audio_file,
                    "num_images": len(result.image_files),
                    "num_videos": len(result.video_files),
                    "publish_results": result.publish_results,
                    "error_message": result.error_message
                }
            }

            summary_file = self.output_dir / \
                f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)

            logger.info(f"✅ Resumo do pipeline salvo em: {summary_file}")

        except Exception as e:
            logger.error(f"❌ Erro ao salvar resumo: {e}")
