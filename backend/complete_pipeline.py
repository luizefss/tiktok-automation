#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Orquestrador completo do pipeline de vídeo automatizado.

Sequência otimizada:
1) Storyboard JSON (entrada)
2) Geração de imagens (OpenAI/Leonardo/Google)
3) Geração de áudio TTS (ElevenLabs) 
4) Geração de animação (Leonardo Motion) usando duração do áudio
5) Montagem final (MoviePy)

Uso:
  python complete_pipeline.py \
    --storyboard /path/storyboard.json \
    --work-dir /path/work \
    --out /path/final.mp4 \
    --image-provider openai \
    --voice-id "Rachel" \
    --music /path/music.mp3

Dependências:
  pip install moviepy requests python-dotenv
"""

import os
import sys
import json
import argparse
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Carregar .env
load_dotenv()

def ensure_dir(path: str):
    """Cria diretório se não existir."""
    os.makedirs(path, exist_ok=True)

def load_storyboard(path: str) -> Dict[str, Any]:
    """Carrega storyboard JSON."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_storyboard(data: Dict[str, Any], path: str):
    """Salva storyboard JSON."""
    ensure_dir(os.path.dirname(path) or ".")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def run_command(cmd: list, description: str):
    """Executa comando e verifica sucesso."""
    print(f"\n🚀 {description}")
    print(f"   Comando: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"✅ {description} - Sucesso")
        if result.stdout:
            print(f"   Output: {result.stdout}")
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - Falhou")
        print(f"   Erro: {e.stderr}")
        print(f"   Exit code: {e.returncode}")
        raise

class CompletePipeline:
    def __init__(self, args):
        self.args = args
        self.work_dir = Path(args.work_dir)
        self.images_dir = self.work_dir / "images"
        self.assets_dir = self.work_dir / "assets"
        self.temp_storyboard = self.work_dir / "storyboard_updated.json"
        
        # Garantir que diretórios existem
        ensure_dir(str(self.work_dir))
        ensure_dir(str(self.images_dir))
        ensure_dir(str(self.assets_dir))
        
        # APIs Keys
        self.openai_key = args.openai_key or os.getenv("OPENAI_API_KEY")
        self.google_key = args.google_key or os.getenv("GOOGLE_API_KEY")
        self.leonardo_key = args.leonardo_key or os.getenv("LEONARDO_API_KEY")
        self.eleven_key = args.eleven_key or os.getenv("ELEVENLABS_API_KEY")
        
        # Verificar keys necessárias
        if args.image_provider == "openai" and not self.openai_key:
            raise ValueError("OpenAI API key necessária para provider 'openai'")
        elif args.image_provider == "google" and not self.google_key:
            raise ValueError("Google API key necessária para provider 'google'")
        elif args.image_provider == "leonardo" and not self.leonardo_key:
            raise ValueError("Leonardo API key necessária para provider 'leonardo'")
            
        if not self.eleven_key:
            raise ValueError("ElevenLabs API key necessária")
            
        if not self.leonardo_key:
            raise ValueError("Leonardo API key necessária para motion")

    def step_1_generate_images(self):
        """Gera imagens usando image_fetcher.py"""
        cmd = [
            sys.executable, "image_fetcher.py",
            "--storyboard", self.args.storyboard,
            "--outdir", str(self.images_dir),
            "--provider", self.args.image_provider,
            "--size", "1024x1792",
            "--ar", "9:16"
        ]
        
        # Adicionar API key baseado no provider
        if self.args.image_provider == "openai":
            cmd.extend(["--openai-key", self.openai_key])
        elif self.args.image_provider == "google":
            cmd.extend(["--google-key", self.google_key])
        elif self.args.image_provider == "leonardo":
            cmd.extend(["--leonardo-key", self.leonardo_key])
            
        run_command(cmd, "Gerando imagens")

    def step_2_generate_audio_and_motion(self):
        """Gera áudio e motion usando render_pipeline_audio_driven.py"""
        cmd = [
            sys.executable, "render_pipeline_audio_driven.py",
            "--storyboard", self.args.storyboard,
            "--assets-dir", str(self.assets_dir),
            "--images-dir", str(self.images_dir),
            "--out", self.args.out,
            "--voice-id", self.args.voice_id,
            "--eleven-key", self.eleven_key,
            "--leonardo-key", self.leonardo_key
        ]
        
        if self.args.music:
            cmd.extend(["--music", self.args.music])
            
        run_command(cmd, "Gerando áudio e motion, montagem final")

    def run(self):
        """Executa pipeline completo."""
        print("🎬 Iniciando Pipeline Completo de Automação")
        print(f"   Storyboard: {self.args.storyboard}")
        print(f"   Diretório de trabalho: {self.work_dir}")
        print(f"   Saída: {self.args.out}")
        print(f"   Provider de imagem: {self.args.image_provider}")
        print(f"   Voz: {self.args.voice_id}")
        
        try:
            # Verificar se storyboard existe
            if not os.path.exists(self.args.storyboard):
                raise FileNotFoundError(f"Storyboard não encontrado: {self.args.storyboard}")
            
            # Step 1: Gerar imagens
            self.step_1_generate_images()
            
            # Step 2: Gerar áudio, motion e montagem final
            self.step_2_generate_audio_and_motion()
            
            print(f"\n🎉 Pipeline concluído com sucesso!")
            print(f"   Vídeo final: {self.args.out}")
            
            # Relatório de arquivos gerados
            images_count = len(list(self.images_dir.glob("scene_*.png")))
            audio_count = len(list(self.assets_dir.glob("scene_*.mp3")))
            video_count = len(list(self.assets_dir.glob("scene_*.mp4")))
            
            print(f"\n📊 Relatório:")
            print(f"   Imagens geradas: {images_count}")
            print(f"   Áudios gerados: {audio_count}")
            print(f"   Vídeos motion gerados: {video_count}")
            print(f"   Vídeo final: {os.path.exists(self.args.out)}")
            
        except Exception as e:
            print(f"\n❌ Pipeline falhou: {e}")
            raise

def main():
    parser = argparse.ArgumentParser(description="Pipeline completo de automação de vídeo")
    
    # Argumentos obrigatórios
    parser.add_argument("--storyboard", required=True, help="Caminho para o storyboard JSON")
    parser.add_argument("--work-dir", required=True, help="Diretório de trabalho")
    parser.add_argument("--out", required=True, help="Caminho do vídeo final")
    
    # Configurações de geração
    parser.add_argument("--image-provider", choices=["openai", "google", "leonardo"], 
                       default="openai", help="Provider de geração de imagens")
    parser.add_argument("--voice-id", default="Rachel", help="ID da voz ElevenLabs")
    
    # Arquivos opcionais
    parser.add_argument("--music", help="Caminho para música de fundo")
    
    # API Keys (também podem vir do .env)
    parser.add_argument("--openai-key", help="OpenAI API Key")
    parser.add_argument("--google-key", help="Google API Key")
    parser.add_argument("--leonardo-key", help="Leonardo API Key")
    parser.add_argument("--eleven-key", help="ElevenLabs API Key")
    
    args = parser.parse_args()
    
    pipeline = CompletePipeline(args)
    pipeline.run()

if __name__ == "__main__":
    main()
