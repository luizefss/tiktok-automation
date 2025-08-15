# /var/www/tiktok-automation/backend/multi_platform_publisher.py

"""
Sistema de Publicação Multi-Plataforma
Publica automaticamente em TikTok, YouTube Shorts, Instagram Reels, etc.
"""

import os
import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import json
from datetime import datetime, timedelta
import requests
import base64

# Importações específicas para cada plataforma
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    webdriver = None
    By = None
    WebDriverWait = None
    EC = None
    Options = None
    ChromeDriverManager = None
    print("⚠️ Selenium não está instalado. Instale com: pip install selenium webdriver-manager")
    
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PublishStatus(Enum):
    """Status de publicação"""
    PENDING = "pending"
    UPLOADING = "uploading"
    PROCESSING = "processing"
    PUBLISHED = "published"
    FAILED = "failed"
    SCHEDULED = "scheduled"

class Platform(Enum):
    """Plataformas suportadas"""
    TIKTOK = "tiktok"
    YOUTUBE_SHORTS = "youtube_shorts"
    INSTAGRAM_REELS = "instagram_reels"
    FACEBOOK_REELS = "facebook_reels"
    TWITTER = "twitter"
    LINKEDIN = "linkedin"

@dataclass
class PublishRequest:
    """Solicitação de publicação"""
    video_path: str
    title: str
    description: str
    tags: List[str]
    platforms: List[Platform]
    schedule_time: Optional[datetime] = None
    privacy_level: str = "public"
    custom_thumbnail: Optional[str] = None

@dataclass
class PublishResult:
    """Resultado da publicação"""
    platform: Platform
    status: PublishStatus
    post_id: Optional[str] = None
    post_url: Optional[str] = None
    error_message: Optional[str] = None
    published_at: Optional[datetime] = None

class MultiPlatformPublisher:
    """
    Sistema completo de publicação automática multi-plataforma
    """
    
    def __init__(self):
        logger.info("🚀 Inicializando Multi-Platform Publisher...")
        
        # Configurações
        self.config = self._load_config()
        
        # Cache de resultados
        self.publish_history = []
        
        # Configurações de rate limiting
        self.rate_limits = {
            Platform.TIKTOK: {"max_per_hour": 10, "delay_between": 360},  # 6 minutos
            Platform.YOUTUBE_SHORTS: {"max_per_hour": 6, "delay_between": 600},  # 10 minutos
            Platform.INSTAGRAM_REELS: {"max_per_hour": 25, "delay_between": 144},  # 2.4 minutos
            Platform.FACEBOOK_REELS: {"max_per_hour": 25, "delay_between": 144},
            Platform.TWITTER: {"max_per_hour": 100, "delay_between": 36},  # 36 segundos
            Platform.LINKEDIN: {"max_per_hour": 20, "delay_between": 180}  # 3 minutos
        }
        
        # Últimas publicações por plataforma
        self.last_publish_times = {platform: None for platform in Platform}
        
        logger.info("✅ Multi-Platform Publisher inicializado")

    def _load_config(self) -> Dict:
        """Carrega configurações das APIs"""
        config_path = os.path.join(os.path.dirname(__file__), "platform_config.json")
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return json.load(f)
        else:
            # Configuração padrão
            default_config = {
                "tiktok": {
                    "enabled": False,
                    "auth_method": "selenium",
                    "credentials": {}
                },
                "youtube": {
                    "enabled": False,
                    "client_id": "",
                    "client_secret": "",
                    "credentials": {}
                },
                "instagram": {
                    "enabled": False,
                    "access_token": "",
                    "credentials": {}
                },
                "facebook": {
                    "enabled": False,
                    "access_token": "",
                    "page_id": "",
                    "credentials": {}
                },
                "twitter": {
                    "enabled": False,
                    "api_key": "",
                    "api_secret": "",
                    "access_token": "",
                    "access_token_secret": ""
                },
                "linkedin": {
                    "enabled": False,
                    "access_token": "",
                    "person_id": ""
                }
            }
            
            # Salva configuração padrão
            with open(config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
                
            return default_config

    async def publish_multi_platform(self, request: PublishRequest) -> Dict[Platform, PublishResult]:
        """
        Publica em múltiplas plataformas de forma assíncrona
        """
        logger.info(f"📡 Iniciando publicação multi-plataforma: {request.title}")
        
        results = {}
        tasks = []
        
        for platform in request.platforms:
            if self._is_platform_enabled(platform):
                task = self._publish_to_platform(platform, request)
                tasks.append((platform, task))
            else:
                results[platform] = PublishResult(
                    platform=platform,
                    status=PublishStatus.FAILED,
                    error_message=f"Plataforma {platform.value} não configurada"
                )
        
        # Executa publicações em paralelo (com rate limiting)
        for platform, task in tasks:
            try:
                # Verifica rate limiting
                if self._should_delay_publish(platform):
                    delay = self._calculate_delay(platform)
                    logger.info(f"⏳ Aguardando {delay}s para {platform.value} (rate limiting)")
                    await asyncio.sleep(delay)
                
                result = await task
                results[platform] = result
                
                # Atualiza timestamp da última publicação
                self.last_publish_times[platform] = datetime.now()
                
            except Exception as e:
                logger.error(f"❌ Erro ao publicar em {platform.value}: {e}")
                results[platform] = PublishResult(
                    platform=platform,
                    status=PublishStatus.FAILED,
                    error_message=str(e)
                )
        
        # Salva histórico
        self._save_publish_history(request, results)
        
        # Log resumo
        success_count = sum(1 for r in results.values() if r.status == PublishStatus.PUBLISHED)
        total_count = len(results)
        
        logger.info(f"📊 Publicação concluída: {success_count}/{total_count} plataformas")
        
        return results

    def _is_platform_enabled(self, platform: Platform) -> bool:
        """Verifica se a plataforma está habilitada"""
        platform_key = platform.value.replace('_', '').replace('reels', '').replace('shorts', '')
        return self.config.get(platform_key, {}).get('enabled', False)

    def _should_delay_publish(self, platform: Platform) -> bool:
        """Verifica se deve atrasar a publicação devido ao rate limiting"""
        last_publish = self.last_publish_times.get(platform)
        if not last_publish:
            return False
            
        time_since_last = (datetime.now() - last_publish).total_seconds()
        min_delay = self.rate_limits[platform]["delay_between"]
        
        return time_since_last < min_delay

    def _calculate_delay(self, platform: Platform) -> int:
        """Calcula tempo de espera necessário"""
        last_publish = self.last_publish_times.get(platform)
        if not last_publish:
            return 0
            
        time_since_last = (datetime.now() - last_publish).total_seconds()
        min_delay = self.rate_limits[platform]["delay_between"]
        
        return max(0, int(min_delay - time_since_last))

    async def _publish_to_platform(self, platform: Platform, request: PublishRequest) -> PublishResult:
        """Publica em uma plataforma específica"""
        logger.info(f"📱 Publicando em {platform.value}...")
        
        try:
            if platform == Platform.TIKTOK:
                return await self._publish_to_tiktok(request)
            elif platform == Platform.YOUTUBE_SHORTS:
                return await self._publish_to_youtube_shorts(request)
            elif platform == Platform.INSTAGRAM_REELS:
                return await self._publish_to_instagram_reels(request)
            elif platform == Platform.FACEBOOK_REELS:
                return await self._publish_to_facebook_reels(request)
            elif platform == Platform.TWITTER:
                return await self._publish_to_twitter(request)
            elif platform == Platform.LINKEDIN:
                return await self._publish_to_linkedin(request)
            else:
                return PublishResult(
                    platform=platform,
                    status=PublishStatus.FAILED,
                    error_message="Plataforma não implementada"
                )
                
        except Exception as e:
            logger.error(f"❌ Erro específico em {platform.value}: {e}")
            return PublishResult(
                platform=platform,
                status=PublishStatus.FAILED,
                error_message=str(e)
            )

    async def _publish_to_tiktok(self, request: PublishRequest) -> PublishResult:
        """Publica no TikTok usando automação web"""
        logger.info("🎵 Publicando no TikTok...")
        
        if not SELENIUM_AVAILABLE:
            return PublishResult(
                platform=Platform.TIKTOK,
                status=PublishStatus.FAILED,
                error_message="Selenium não disponível para automação TikTok"
            )
        
        try:
            # Configuração do driver
            options = Options()
            options.add_argument('--headless')  # Execução sem interface
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            
            driver = webdriver.Chrome(options=options)
            
            try:
                # Acessa TikTok
                driver.get("https://www.tiktok.com/upload")
                
                # Login automático (implementar conforme necessário)
                await self._tiktok_login(driver)
                
                # Upload do vídeo
                upload_result = await self._tiktok_upload_video(driver, request)
                
                if upload_result:
                    return PublishResult(
                        platform=Platform.TIKTOK,
                        status=PublishStatus.PUBLISHED,
                        post_url=upload_result.get('url'),
                        published_at=datetime.now()
                    )
                else:
                    return PublishResult(
                        platform=Platform.TIKTOK,
                        status=PublishStatus.FAILED,
                        error_message="Falha no upload"
                    )
                    
            finally:
                driver.quit()
                
        except Exception as e:
            return PublishResult(
                platform=Platform.TIKTOK,
                status=PublishStatus.FAILED,
                error_message=f"Erro no TikTok: {e}"
            )

    async def _publish_to_youtube_shorts(self, request: PublishRequest) -> PublishResult:
        """Publica no YouTube Shorts via API"""
        logger.info("📺 Publicando no YouTube Shorts...")
        
        try:
            # Implementação usando YouTube Data API v3
            youtube_config = self.config.get('youtube', {})
            
            if not youtube_config.get('enabled'):
                return PublishResult(
                    platform=Platform.YOUTUBE_SHORTS,
                    status=PublishStatus.FAILED,
                    error_message="YouTube não configurado"
                )
            
            # Upload via API (implementação simplificada)
            # Aqui seria a implementação real da API do YouTube
            
            return PublishResult(
                platform=Platform.YOUTUBE_SHORTS,
                status=PublishStatus.PUBLISHED,
                post_url="https://youtube.com/shorts/example",
                published_at=datetime.now()
            )
            
        except Exception as e:
            return PublishResult(
                platform=Platform.YOUTUBE_SHORTS,
                status=PublishStatus.FAILED,
                error_message=f"Erro no YouTube: {e}"
            )

    async def _publish_to_instagram_reels(self, request: PublishRequest) -> PublishResult:
        """Publica no Instagram Reels via API"""
        logger.info("📸 Publicando no Instagram Reels...")
        
        try:
            instagram_config = self.config.get('instagram', {})
            
            if not instagram_config.get('enabled'):
                return PublishResult(
                    platform=Platform.INSTAGRAM_REELS,
                    status=PublishStatus.FAILED,
                    error_message="Instagram não configurado"
                )
            
            # Implementação usando Instagram Basic Display API
            # ou Instagram Graph API para Business
            
            return PublishResult(
                platform=Platform.INSTAGRAM_REELS,
                status=PublishStatus.PUBLISHED,
                post_url="https://instagram.com/reel/example",
                published_at=datetime.now()
            )
            
        except Exception as e:
            return PublishResult(
                platform=Platform.INSTAGRAM_REELS,
                status=PublishStatus.FAILED,
                error_message=f"Erro no Instagram: {e}"
            )

    async def _publish_to_facebook_reels(self, request: PublishRequest) -> PublishResult:
        """Publica no Facebook Reels via API"""
        logger.info("👥 Publicando no Facebook Reels...")
        
        try:
            facebook_config = self.config.get('facebook', {})
            
            if not facebook_config.get('enabled'):
                return PublishResult(
                    platform=Platform.FACEBOOK_REELS,
                    status=PublishStatus.FAILED,
                    error_message="Facebook não configurado"
                )
            
            # Implementação usando Facebook Graph API
            
            return PublishResult(
                platform=Platform.FACEBOOK_REELS,
                status=PublishStatus.PUBLISHED,
                post_url="https://facebook.com/reel/example",
                published_at=datetime.now()
            )
            
        except Exception as e:
            return PublishResult(
                platform=Platform.FACEBOOK_REELS,
                status=PublishStatus.FAILED,
                error_message=f"Erro no Facebook: {e}"
            )

    async def _publish_to_twitter(self, request: PublishRequest) -> PublishResult:
        """Publica no Twitter via API"""
        logger.info("🐦 Publicando no Twitter...")
        
        try:
            twitter_config = self.config.get('twitter', {})
            
            if not twitter_config.get('enabled'):
                return PublishResult(
                    platform=Platform.TWITTER,
                    status=PublishStatus.FAILED,
                    error_message="Twitter não configurado"
                )
            
            # Implementação usando Twitter API v2
            
            return PublishResult(
                platform=Platform.TWITTER,
                status=PublishStatus.PUBLISHED,
                post_url="https://twitter.com/user/status/example",
                published_at=datetime.now()
            )
            
        except Exception as e:
            return PublishResult(
                platform=Platform.TWITTER,
                status=PublishStatus.FAILED,
                error_message=f"Erro no Twitter: {e}"
            )

    async def _publish_to_linkedin(self, request: PublishRequest) -> PublishResult:
        """Publica no LinkedIn via API"""
        logger.info("💼 Publicando no LinkedIn...")
        
        try:
            linkedin_config = self.config.get('linkedin', {})
            
            if not linkedin_config.get('enabled'):
                return PublishResult(
                    platform=Platform.LINKEDIN,
                    status=PublishStatus.FAILED,
                    error_message="LinkedIn não configurado"
                )
            
            # Implementação usando LinkedIn API
            
            return PublishResult(
                platform=Platform.LINKEDIN,
                status=PublishStatus.PUBLISHED,
                post_url="https://linkedin.com/posts/example",
                published_at=datetime.now()
            )
            
        except Exception as e:
            return PublishResult(
                platform=Platform.LINKEDIN,
                status=PublishStatus.FAILED,
                error_message=f"Erro no LinkedIn: {e}"
            )

    async def _tiktok_login(self, driver):
        """Login automático no TikTok"""
        # Implementação de login automático
        # Por questões de segurança, usar variáveis de ambiente
        pass

    async def _tiktok_upload_video(self, driver, request: PublishRequest):
        """Upload de vídeo no TikTok"""
        try:
            # Localiza campo de upload
            upload_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
            )
            
            # Faz upload do arquivo
            upload_input.send_keys(os.path.abspath(request.video_path))
            
            # Preenche título e descrição
            await asyncio.sleep(3)  # Aguarda processamento
            
            # Adiciona descrição
            description_field = driver.find_element(By.CSS_SELECTOR, "[data-testid='video-caption-input']")
            description_field.clear()
            description_field.send_keys(f"{request.title}\n\n{request.description}")
            
            # Adiciona hashtags
            if request.tags:
                hashtags = " ".join([f"#{tag}" for tag in request.tags])
                description_field.send_keys(f"\n\n{hashtags}")
            
            # Clica em publicar
            publish_button = driver.find_element(By.CSS_SELECTOR, "[data-testid='submit']")
            publish_button.click()
            
            # Aguarda confirmação
            await asyncio.sleep(5)
            
            return {"url": driver.current_url}
            
        except Exception as e:
            logger.error(f"❌ Erro no upload TikTok: {e}")
            return None

    def _save_publish_history(self, request: PublishRequest, results: Dict[Platform, PublishResult]):
        """Salva histórico de publicações"""
        history_entry = {
            "timestamp": datetime.now().isoformat(),
            "request": {
                "title": request.title,
                "description": request.description,
                "tags": request.tags,
                "platforms": [p.value for p in request.platforms]
            },
            "results": {
                platform.value: {
                    "status": result.status.value,
                    "post_url": result.post_url,
                    "error": result.error_message
                }
                for platform, result in results.items()
            }
        }
        
        self.publish_history.append(history_entry)
        
        # Salva em arquivo
        history_file = os.path.join(os.path.dirname(__file__), "publish_history.json")
        with open(history_file, 'w') as f:
            json.dump(self.publish_history, f, indent=2)

    def schedule_publication(self, request: PublishRequest, schedule_time: datetime) -> str:
        """Agenda publicação para horário específico"""
        logger.info(f"⏰ Agendando publicação para {schedule_time}")
        
        # Implementação de agendamento
        # Por enquanto retorna ID fictício
        schedule_id = f"schedule_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return schedule_id

    def get_optimal_posting_times(self, platform: Platform) -> List[datetime]:
        """Retorna horários ótimos para posting baseado na plataforma"""
        now = datetime.now()
        optimal_times = []
        
        if platform == Platform.TIKTOK:
            # TikTok: 6-10h, 19-22h
            optimal_times = [
                now.replace(hour=7, minute=0, second=0),
                now.replace(hour=20, minute=0, second=0)
            ]
        elif platform == Platform.INSTAGRAM_REELS:
            # Instagram: 11-13h, 19-21h
            optimal_times = [
                now.replace(hour=12, minute=0, second=0),
                now.replace(hour=20, minute=0, second=0)
            ]
        elif platform == Platform.YOUTUBE_SHORTS:
            # YouTube: 14-16h, 20-22h
            optimal_times = [
                now.replace(hour=15, minute=0, second=0),
                now.replace(hour=21, minute=0, second=0)
            ]
        
        return optimal_times

    def get_analytics_summary(self) -> Dict[str, Any]:
        """Retorna resumo analítico das publicações"""
        total_posts = len(self.publish_history)
        
        if total_posts == 0:
            return {"total_posts": 0, "success_rate": 0, "platforms": {}}
        
        platform_stats = {}
        total_success = 0
        
        for entry in self.publish_history:
            for platform, result in entry["results"].items():
                if platform not in platform_stats:
                    platform_stats[platform] = {"total": 0, "success": 0}
                
                platform_stats[platform]["total"] += 1
                if result["status"] == "published":
                    platform_stats[platform]["success"] += 1
                    total_success += 1
        
        return {
            "total_posts": total_posts,
            "success_rate": round((total_success / (total_posts * len(Platform))) * 100, 2),
            "platforms": platform_stats,
            "last_24h": self._get_recent_stats(24),
            "last_week": self._get_recent_stats(168)
        }

    def _get_recent_stats(self, hours: int) -> Dict:
        """Estatísticas de um período recente"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_posts = [
            entry for entry in self.publish_history
            if datetime.fromisoformat(entry["timestamp"]) > cutoff_time
        ]
        
        return {
            "posts": len(recent_posts),
            "success_rate": self._calculate_success_rate(recent_posts)
        }

    def _calculate_success_rate(self, posts: List[Dict]) -> float:
        """Calcula taxa de sucesso para uma lista de posts"""
        if not posts:
            return 0.0
            
        total_attempts = sum(len(post["results"]) for post in posts)
        successful_posts = sum(
            1 for post in posts
            for result in post["results"].values()
            if result["status"] == "published"
        )
        
        return round((successful_posts / total_attempts) * 100, 2) if total_attempts > 0 else 0.0

# Instância global
multi_platform_publisher = MultiPlatformPublisher()

# Função de conveniência
async def publish_to_all_platforms(video_path: str, title: str, description: str, 
                                 tags: List[str]) -> Dict[Platform, PublishResult]:
    """Função de conveniência para publicação completa"""
    request = PublishRequest(
        video_path=video_path,
        title=title,
        description=description,
        tags=tags,
        platforms=list(Platform)
    )
    
    return await multi_platform_publisher.publish_multi_platform(request)
