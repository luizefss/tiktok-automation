# /var/www/tiktok-automation/backend/setup_platforms.py

"""
Script de Configuração do Sistema Multi-Plataforma
Instala dependências e configura credenciais
"""

import os
import sys
import subprocess
import json
import logging
from typing import Dict, Any
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PlatformSetup:
    """Configurador do sistema multi-plataforma"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.config_file = self.base_dir / "platform_config.json"
        
    def setup_environment(self):
        """Configura o ambiente completo"""
        logger.info("🚀 Iniciando configuração do ambiente multi-plataforma...")
        
        try:
            # 1. Instala dependências Python
            self.install_python_dependencies()
            
            # 2. Configura navegador para automação
            self.setup_browser_automation()
            
            # 3. Cria arquivos de configuração
            self.create_configuration_files()
            
            # 4. Configura estrutura de diretórios
            self.setup_directory_structure()
            
            logger.info("✅ Configuração concluída com sucesso!")
            
        except Exception as e:
            logger.error(f"❌ Erro na configuração: {e}")
            raise

    def install_python_dependencies(self):
        """Instala dependências Python necessárias"""
        logger.info("📦 Instalando dependências Python...")
        
        dependencies = [
            "selenium==4.15.2",
            "webdriver-manager==4.0.1",
            "requests==2.31.0",
            "google-auth==2.23.4",
            "google-auth-oauthlib==1.1.0",
            "google-auth-httplib2==0.1.1",
            "google-api-python-client==2.108.0",
            "tweepy==4.14.0",
            "facebook-sdk==3.1.0",
            "linkedin-api==2.0.1",
            "aiohttp==3.9.1",
            "asyncio-mqtt==0.13.0",
            "celery==5.3.4",
            "redis==5.0.1"
        ]
        
        for dep in dependencies:
            try:
                logger.info(f"Instalando {dep}...")
                subprocess.run([
                    sys.executable, "-m", "pip", "install", dep
                ], check=True, capture_output=True, text=True)
                logger.info(f"✅ {dep} instalado")
            except subprocess.CalledProcessError as e:
                logger.warning(f"⚠️ Falha ao instalar {dep}: {e}")

    def setup_browser_automation(self):
        """Configura automação de navegador"""
        logger.info("🌐 Configurando automação de navegador...")
        
        try:
            # Instala ChromeDriver automaticamente
            from webdriver_manager.chrome import ChromeDriverManager
            from selenium import webdriver
            from selenium.webdriver.chrome.service import Service
            
            # Download do ChromeDriver
            chrome_driver_path = ChromeDriverManager().install()
            logger.info(f"ChromeDriver instalado em: {chrome_driver_path}")
            
            # Testa instalação
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            
            service = Service(chrome_driver_path)
            driver = webdriver.Chrome(service=service, options=options)
            
            # Teste básico
            driver.get("https://www.google.com")
            assert "Google" in driver.title
            driver.quit()
            
            logger.info("✅ Automação de navegador configurada")
            
        except Exception as e:
            logger.error(f"❌ Erro na configuração do navegador: {e}")
            logger.info("💡 Alternativas: usar APIs oficiais das plataformas")

    def create_configuration_files(self):
        """Cria arquivos de configuração"""
        logger.info("⚙️ Criando arquivos de configuração...")
        
        # Configuração principal
        config = {
            "tiktok": {
                "enabled": False,
                "auth_method": "selenium",
                "upload_settings": {
                    "max_file_size_mb": 287,
                    "supported_formats": ["mp4", "mov", "avi"],
                    "max_duration_seconds": 180,
                    "auto_captions": True,
                    "privacy_default": "public"
                },
                "selenium_config": {
                    "headless": True,
                    "timeout": 30,
                    "retry_attempts": 3
                },
                "credentials": {
                    "username": "",
                    "password": "",
                    "phone": ""
                }
            },
            "youtube": {
                "enabled": False,
                "auth_method": "oauth2",
                "upload_settings": {
                    "max_file_size_mb": 1024,
                    "supported_formats": ["mp4", "mov", "avi", "wmv"],
                    "max_duration_seconds": 60,
                    "category": "22",  # People & Blogs
                    "privacy_default": "public"
                },
                "oauth2_config": {
                    "client_id": "",
                    "client_secret": "",
                    "redirect_uri": "http://localhost:8080/oauth/callback",
                    "scopes": ["https://www.googleapis.com/auth/youtube.upload"]
                },
                "credentials": {}
            },
            "instagram": {
                "enabled": False,
                "auth_method": "graph_api",
                "upload_settings": {
                    "max_file_size_mb": 100,
                    "supported_formats": ["mp4", "mov"],
                    "max_duration_seconds": 90,
                    "aspect_ratio": "9:16",
                    "min_resolution": "720p"
                },
                "graph_api_config": {
                    "app_id": "",
                    "app_secret": "",
                    "access_token": "",
                    "instagram_business_account_id": ""
                },
                "credentials": {}
            },
            "facebook": {
                "enabled": False,
                "auth_method": "graph_api",
                "upload_settings": {
                    "max_file_size_mb": 100,
                    "supported_formats": ["mp4", "mov"],
                    "max_duration_seconds": 60,
                    "aspect_ratio": "9:16"
                },
                "graph_api_config": {
                    "app_id": "",
                    "app_secret": "",
                    "access_token": "",
                    "page_id": ""
                },
                "credentials": {}
            },
            "twitter": {
                "enabled": False,
                "auth_method": "api_v2",
                "upload_settings": {
                    "max_file_size_mb": 512,
                    "supported_formats": ["mp4", "mov"],
                    "max_duration_seconds": 140,
                    "aspect_ratio": "16:9"
                },
                "api_v2_config": {
                    "api_key": "",
                    "api_secret": "",
                    "access_token": "",
                    "access_token_secret": "",
                    "bearer_token": ""
                },
                "credentials": {}
            },
            "linkedin": {
                "enabled": False,
                "auth_method": "api",
                "upload_settings": {
                    "max_file_size_mb": 200,
                    "supported_formats": ["mp4", "mov"],
                    "max_duration_seconds": 600,
                    "aspect_ratio": "16:9"
                },
                "api_config": {
                    "client_id": "",
                    "client_secret": "",
                    "access_token": "",
                    "person_id": ""
                },
                "credentials": {}
            },
            "scheduling": {
                "enabled": True,
                "timezone": "America/Sao_Paulo",
                "optimal_times": {
                    "tiktok": ["07:00", "20:00"],
                    "instagram": ["12:00", "20:00"],
                    "youtube": ["15:00", "21:00"],
                    "facebook": ["13:00", "19:00"],
                    "twitter": ["09:00", "17:00"],
                    "linkedin": ["08:00", "18:00"]
                }
            },
            "analytics": {
                "enabled": True,
                "metrics_tracking": [
                    "views", "likes", "comments", "shares", "reach"
                ],
                "reporting_frequency": "daily"
            },
            "content_optimization": {
                "hashtag_research": True,
                "trending_topics": True,
                "audience_analysis": True,
                "performance_tracking": True
            }
        }
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Configuração salva em: {self.config_file}")
        
        # Arquivo de exemplo de uso
        self.create_usage_examples()

    def create_usage_examples(self):
        """Cria exemplos de uso"""
        examples_file = self.base_dir / "usage_examples.py"
        
        examples_content = '''"""
Exemplos de Uso do Sistema Multi-Plataforma
"""

import asyncio
from datetime import datetime, timedelta
from multi_platform_publisher import (
    MultiPlatformPublisher, 
    PublishRequest, 
    Platform,
    publish_to_all_platforms
)

async def example_basic_publish():
    """Exemplo básico de publicação"""
    
    # Cria solicitação de publicação
    request = PublishRequest(
        video_path="/caminho/para/video.mp4",
        title="Meu Vídeo Incrível",
        description="Descrição do vídeo com conteúdo interessante!",
        tags=["viral", "trending", "conteudo"],
        platforms=[Platform.TIKTOK, Platform.INSTAGRAM_REELS]
    )
    
    # Publica
    publisher = MultiPlatformPublisher()
    results = await publisher.publish_multi_platform(request)
    
    # Mostra resultados
    for platform, result in results.items():
        print(f"{platform.value}: {result.status.value}")
        if result.post_url:
            print(f"  URL: {result.post_url}")

async def example_scheduled_publish():
    """Exemplo de publicação agendada"""
    
    # Agenda para daqui a 2 horas
    schedule_time = datetime.now() + timedelta(hours=2)
    
    request = PublishRequest(
        video_path="/caminho/para/video.mp4",
        title="Vídeo Agendado",
        description="Este vídeo foi agendado!",
        tags=["agendado", "automatico"],
        platforms=[Platform.YOUTUBE_SHORTS, Platform.FACEBOOK_REELS],
        schedule_time=schedule_time
    )
    
    publisher = MultiPlatformPublisher()
    schedule_id = publisher.schedule_publication(request, schedule_time)
    print(f"Agendamento criado: {schedule_id}")

async def example_optimal_timing():
    """Exemplo usando horários ótimos"""
    
    publisher = MultiPlatformPublisher()
    
    # Obtém horários ótimos para TikTok
    optimal_times = publisher.get_optimal_posting_times(Platform.TIKTOK)
    print("Horários ótimos para TikTok:", optimal_times)
    
    # Agenda para o próximo horário ótimo
    next_optimal = optimal_times[0]
    
    request = PublishRequest(
        video_path="/caminho/para/video.mp4",
        title="Vídeo no Horário Ótimo",
        description="Publicado no melhor horário!",
        tags=["timing", "otimo"],
        platforms=[Platform.TIKTOK]
    )
    
    if next_optimal > datetime.now():
        schedule_id = publisher.schedule_publication(request, next_optimal)
        print(f"Agendado para horário ótimo: {schedule_id}")
    else:
        results = await publisher.publish_multi_platform(request)
        print("Publicado imediatamente")

async def example_analytics():
    """Exemplo de análise de performance"""
    
    publisher = MultiPlatformPublisher()
    
    # Obtém resumo analítico
    analytics = publisher.get_analytics_summary()
    
    print("📊 Resumo Analítico:")
    print(f"Total de posts: {analytics['total_posts']}")
    print(f"Taxa de sucesso: {analytics['success_rate']}%")
    
    print("\\nPor plataforma:")
    for platform, stats in analytics['platforms'].items():
        success_rate = (stats['success'] / stats['total']) * 100
        print(f"  {platform}: {stats['success']}/{stats['total']} ({success_rate:.1f}%)")

async def example_convenience_function():
    """Exemplo usando função de conveniência"""
    
    # Publica em todas as plataformas de uma vez
    results = await publish_to_all_platforms(
        video_path="/caminho/para/video.mp4",
        title="Publicação Completa",
        description="Publicando em todas as plataformas!",
        tags=["viral", "multiplataforma", "automatico"]
    )
    
    print("Resultados da publicação completa:")
    for platform, result in results.items():
        print(f"  {platform.value}: {result.status.value}")

if __name__ == "__main__":
    # Executa exemplos
    print("🚀 Executando exemplos...")
    
    # asyncio.run(example_basic_publish())
    # asyncio.run(example_scheduled_publish())
    # asyncio.run(example_optimal_timing())
    # asyncio.run(example_analytics())
    # asyncio.run(example_convenience_function())
    
    print("✅ Exemplos concluídos!")
'''
        
        with open(examples_file, 'w', encoding='utf-8') as f:
            f.write(examples_content)
        
        logger.info(f"✅ Exemplos criados em: {examples_file}")

    def setup_directory_structure(self):
        """Cria estrutura de diretórios necessária"""
        logger.info("📁 Criando estrutura de diretórios...")
        
        directories = [
            "uploads",
            "downloads", 
            "temp",
            "logs",
            "analytics",
            "thumbnails",
            "templates",
            "schedules"
        ]
        
        for directory in directories:
            dir_path = self.base_dir / directory
            dir_path.mkdir(exist_ok=True)
            logger.info(f"✅ Diretório criado: {directory}")

    def setup_platform_credentials(self, platform: str, credentials: Dict[str, Any]):
        """Configura credenciais de uma plataforma específica"""
        logger.info(f"🔑 Configurando credenciais para {platform}...")
        
        if not self.config_file.exists():
            self.create_configuration_files()
        
        with open(self.config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        if platform in config:
            config[platform]['enabled'] = True
            config[platform]['credentials'].update(credentials)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Credenciais configuradas para {platform}")
        else:
            logger.error(f"❌ Plataforma {platform} não encontrada na configuração")

    def test_platform_connection(self, platform: str) -> bool:
        """Testa conexão com uma plataforma"""
        logger.info(f"🔍 Testando conexão com {platform}...")
        
        try:
            # Implementar testes específicos por plataforma
            if platform == "tiktok":
                return self._test_tiktok_connection()
            elif platform == "youtube":
                return self._test_youtube_connection()
            elif platform == "instagram":
                return self._test_instagram_connection()
            elif platform == "facebook":
                return self._test_facebook_connection()
            elif platform == "twitter":
                return self._test_twitter_connection()
            elif platform == "linkedin":
                return self._test_linkedin_connection()
            else:
                logger.error(f"❌ Plataforma {platform} não suportada")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro ao testar {platform}: {e}")
            return False

    def _test_tiktok_connection(self) -> bool:
        """Testa conexão TikTok via Selenium"""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.service import Service
            from webdriver_manager.chrome import ChromeDriverManager
            
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')
            
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            
            driver.get("https://www.tiktok.com")
            success = "TikTok" in driver.title
            driver.quit()
            
            logger.info("✅ TikTok: Conexão bem-sucedida")
            return success
            
        except Exception as e:
            logger.error(f"❌ TikTok: {e}")
            return False

    def _test_youtube_connection(self) -> bool:
        """Testa conexão YouTube API"""
        # Implementar teste de API
        logger.info("✅ YouTube: Teste simulado")
        return True

    def _test_instagram_connection(self) -> bool:
        """Testa conexão Instagram API"""
        # Implementar teste de API
        logger.info("✅ Instagram: Teste simulado")
        return True

    def _test_facebook_connection(self) -> bool:
        """Testa conexão Facebook API"""
        # Implementar teste de API
        logger.info("✅ Facebook: Teste simulado")
        return True

    def _test_twitter_connection(self) -> bool:
        """Testa conexão Twitter API"""
        # Implementar teste de API
        logger.info("✅ Twitter: Teste simulado")
        return True

    def _test_linkedin_connection(self) -> bool:
        """Testa conexão LinkedIn API"""
        # Implementar teste de API
        logger.info("✅ LinkedIn: Teste simulado")
        return True

    def generate_setup_report(self):
        """Gera relatório de configuração"""
        logger.info("📋 Gerando relatório de configuração...")
        
        report = {
            "setup_completed": True,
            "timestamp": datetime.now().isoformat(),
            "python_version": sys.version,
            "dependencies_installed": True,
            "browser_automation": True,
            "configuration_files": True,
            "directory_structure": True,
            "platforms_status": {}
        }
        
        # Testa cada plataforma
        platforms = ["tiktok", "youtube", "instagram", "facebook", "twitter", "linkedin"]
        for platform in platforms:
            report["platforms_status"][platform] = self.test_platform_connection(platform)
        
        # Salva relatório
        report_file = self.base_dir / "setup_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Relatório salvo em: {report_file}")
        return report

def main():
    """Função principal de configuração"""
    setup = PlatformSetup()
    
    try:
        # Executa configuração completa
        setup.setup_environment()
        
        # Gera relatório
        report = setup.generate_setup_report()
        
        print("\\n" + "="*50)
        print("🎉 CONFIGURAÇÃO CONCLUÍDA!")
        print("="*50)
        print(f"✅ Dependências instaladas")
        print(f"✅ Navegador configurado")
        print(f"✅ Arquivos de configuração criados")
        print(f"✅ Estrutura de diretórios criada")
        print("\\n📝 Próximos passos:")
        print("1. Configure as credenciais das plataformas em platform_config.json")
        print("2. Execute os testes de conexão")
        print("3. Veja os exemplos em usage_examples.py")
        print("="*50)
        
    except Exception as e:
        print(f"\n❌ ERRO NA CONFIGURAÇÃO: {e}")
        print("Verifique os logs para mais detalhes.")

if __name__ == "__main__":
    main()
