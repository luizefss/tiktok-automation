# /var/www/tiktok-automation/backend/config_manager.py

import os
from pathlib import Path
from dataclasses import dataclass, field
from dotenv import load_dotenv
from typing import List

load_dotenv(dotenv_path=Path(__file__).parent / '.env')


@dataclass
class Config:
    # Non-default arguments first
    BASE_DIR: Path
    MEDIA_DIR: Path
    AUDIO_DIR: Path
    VIDEO_DIR: Path
    IMAGES_DIR: Path
    TEMP_DIR: Path
    MUSIC_DIR: Path
    LOGS_DIR: Path
    
    # Default arguments last
    AI_BATTLE_PARTICIPANTS: List[str] = field(
        default_factory=lambda: ["gemini", "claude", "gpt"])

    GEMINI_API_KEY: str = field(
        default_factory=lambda: os.getenv("GEMINI_API_KEY"))
    CLAUDE_API_KEY: str = field(
        default_factory=lambda: os.getenv("CLAUDE_API_KEY"))
    OPENAI_API_KEY: str = field(
        default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    VERTEX_AI_API_KEY: str = field(
        default_factory=lambda: os.getenv("VERTEX_AI_API_KEY"))
    LEONARDO_API_KEY: str = field(
        default_factory=lambda: os.getenv("LEONARDO_API_KEY"))
    ELEVEN_API_KEY: str = field(
        default_factory=lambda: os.getenv("ELEVEN_API_KEY"))
    YOUTUBE_API_KEY: str = field(
        default_factory=lambda: os.getenv("YOUTUBE_API_KEY"))
    NEWS_API_KEY: str = field(
        default_factory=lambda: os.getenv("NEWS_API_KEY"))
    # ... adicione outras chaves de API aqui

    # Google Cloud Settings
    GOOGLE_PROJECT_ID: str = field(default_factory=lambda: os.getenv(
        'VERTEX_AI_PROJECT_ID', os.getenv('GOOGLE_CLOUD_PROJECT_ID', "weighty-sled-467607-n1")))
    GOOGLE_LOCATION: str = field(default_factory=lambda: os.getenv(
        'VERTEX_AI_LOCATION', "us-central1"))
    SERVICE_ACCOUNT_PATH: Path = field(default_factory=lambda: Path(
        os.getenv('GOOGLE_APPLICATION_CREDENTIALS', './service-account-key.json')))

    # API Settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 6000
    API_DEBUG: bool = False

    # TTS Settings
    TTS_VOICE: str = "pt-BR-Chirp3-HD-Puck"
    TTS_SPEAKING_RATE: float = 1.05
    TTS_MODEL: str = "gemini-2.5-pro-preview-tts"

    # Video Settings
    VIDEO_WIDTH: int = 1080
    VIDEO_HEIGHT: int = 1920
    VIDEO_FPS: int = 30
    VIDEO_CRF: int = 23
    AUDIO_BITRATE: int = 128

    # Timeouts (seconds)
    API_TIMEOUT: int = 30
    FFMPEG_TIMEOUT: int = 300
    IMAGE_DOWNLOAD_TIMEOUT: int = 10

    # Trending System Settings
    TRENDING_MAX_CACHE_HOURS: int = 6
    TRENDING_MAX_USED_TOPICS: int = 100

    # AI Battle Settings
    AI_BATTLE_PARTICIPANTS: List[str] = field(
        default_factory=lambda: ["gemini", "claude", "gpt"])


class ConfigManager:
    _instance = None
    _config = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._config is None:
            self._config = self._create_config()

    def _create_config(self) -> Config:
        """Cria configuração baseada no ambiente atual e variáveis de ambiente"""
        current_dir = Path(__file__).parent
        base_dir = current_dir.parent if "backend" in str(
            current_dir) else current_dir
        media_dir = base_dir / "media"

        config = Config(
            BASE_DIR=base_dir,
            MEDIA_DIR=media_dir,
            AUDIO_DIR=media_dir / "audio",
            VIDEO_DIR=media_dir / "videos",
            IMAGES_DIR=media_dir / "images",
            TEMP_DIR=media_dir / "temp",
            MUSIC_DIR=media_dir / "music",
            LOGS_DIR=base_dir / "logs",
        )

        # Atualiza paths com base no .env se necessário
        service_account_path_str = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if service_account_path_str:
            config.SERVICE_ACCOUNT_PATH = Path(service_account_path_str)

        return config

    def get(self) -> Config:
        """Retorna a configuração"""
        return self._config

    def ensure_directories(self):
        """Cria diretórios necessários"""
        dirs_to_create = [
            self._config.MEDIA_DIR,
            self._config.AUDIO_DIR,
            self._config.VIDEO_DIR,
            self._config.IMAGES_DIR,
            self._config.TEMP_DIR,
            self._config.MUSIC_DIR,
            self._config.LOGS_DIR,
        ]
        for directory in dirs_to_create:
            directory.mkdir(parents=True, exist_ok=True)


# Singleton global
config_manager = ConfigManager()


def get_config() -> Config:
    """Função helper para obter config"""
    return config_manager.get()


# Auto-criar diretórios na inicialização
config_manager.ensure_directories()
