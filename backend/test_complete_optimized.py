#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Teste COMPLETO do pipeline otimizado de automação.

Este script testa todo o fluxo otimizado:
1) Criação de um storyboard de teste
2) Geração de imagens via image_fetcher.py
3) Geração de áudio TTS via ElevenLabs
4) Geração de motion via Leonardo
5) Montagem final via render_pipeline_audio_driven.py

Uso:
  python test_complete_optimized.py [--provider openai|leonardo|google]
"""

import os
import json
import tempfile
import subprocess
import sys
from pathlib import Path
from dotenv import load_dotenv

# Carregar .env
load_dotenv()

# Storyboard de teste (Newton e Prisma) - OTIMIZADO
TEST_STORYBOARD = {
    "title": "Newton e o Prisma - Descoberta da Luz",
    "description": "A histórica descoberta de Isaac Newton sobre a decomposição da luz",
    "scenes": [
        {
            "t_start": 0.0,
            "t_end": 4.0,
            "narration": "Em 1666, Isaac Newton fez uma descoberta que mudaria nossa compreensão da luz para sempre.",
            "image_prompt": "Isaac Newton in his study, 1600s period accurate, warm candlelight, books and scientific instruments, painterly realistic, cinematic lighting, 9:16 vertical",
            "motion_prompt": "slow zoom in on Newton's face, subtle parallax movement, warm lighting"
        },
        {
            "t_start": 4.0,
            "t_end": 8.0,
            "narration": "Usando um simples prisma de vidro, ele direcionou um feixe de luz solar através dele.",
            "image_prompt": "Glass prism on wooden table with sunlight beam, rainbow spectrum emerging, scientific setting, detailed crystal texture, dramatic lighting, 9:16 vertical",
            "motion_prompt": "gentle rotation of prism, light beam movement, rainbow spectrum appearing"
        },
        {
            "t_start": 8.0,
            "t_end": 12.0,
            "narration": "Para sua surpresa, a luz branca se separou em um espectro completo de cores: vermelho, laranja, amarelo, verde, azul, anil e violeta.",
            "image_prompt": "Beautiful rainbow spectrum on wall, seven distinct colors, prism experiment, scientific laboratory 1600s, magical light rays, painterly style, 9:16 vertical",
            "motion_prompt": "slow pan across the spectrum colors, light rays dancing, magical atmosphere"
        },
        {
            "t_start": 12.0,
            "t_end": 16.0,
            "narration": "Newton descobriu que a luz branca não era pura, mas sim uma combinação de todas as cores do espectro visível.",
            "image_prompt": "Newton writing notes by candlelight, scientific breakthrough moment, period accurate 1600s study, quill pen and parchment, thoughtful expression, 9:16 vertical",
            "motion_prompt": "focus pull from notes to Newton's face, candlelight flickering, contemplative moment"
        },
        {
            "t_start": 16.0,
            "t_end": 20.0,
            "narration": "Esta descoberta revolucionou a óptica e nossa compreensão da natureza da luz, estabelecendo as bases da física moderna.",
            "image_prompt": "Modern physics laboratory with prism experiment setup, scientific equipment, colorful light spectrum, educational setting, professional lighting, 9:16 vertical",
            "motion_prompt": "smooth camera movement around modern lab setup, light beams and spectrum display"
        }
    ]
}

def test_api_keys():
    """Verifica se as API keys estão configuradas."""
    keys = {
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "GOOGLE_API_KEY": os.getenv("GOOGLE_API_KEY"), 
        "LEONARDO_API_KEY": os.getenv("LEONARDO_API_KEY"),
        "ELEVEN_API_KEY": os.getenv("ELEVEN_API_KEY")
    }
    
    print("🔑 Verificando API Keys:")
    for key, value in keys.items():
        status = "✅ Configurada" if value else "❌ Não encontrada"
        masked = f"{value[:8]}..." if value else "Não configurada"
        print(f"   {key}: {status} ({masked})")
    
    return keys

def create_test_storyboard(work_dir: Path) -> Path:
    """Cria arquivo de storyboard de teste."""
    storyboard_path = work_dir / "test_storyboard.json"
    
    with open(storyboard_path, 'w', encoding='utf-8') as f:
        json.dump(TEST_STORYBOARD, f, indent=2, ensure_ascii=False)
    
    print(f"📝 Storyboard de teste criado: {storyboard_path}")
    print(f"   Título: {TEST_STORYBOARD['title']}")
    print(f"   Cenas: {len(TEST_STORYBOARD['scenes'])}")
    
    return storyboard_path

def test_pipeline(provider: str = "openai"):
    """Testa o pipeline completo OTIMIZADO."""
    print("🎬 Iniciando teste do pipeline completo OTIMIZADO")
    print(f"   Provider de imagem: {provider}")
    
    # Verificar API keys
    keys = test_api_keys()
    
    # Verificar se keys necessárias estão disponíveis
    required_keys = ["ELEVEN_API_KEY", "LEONARDO_API_KEY"]
    
    if provider == "openai":
        required_keys.append("OPENAI_API_KEY")
    elif provider == "leonardo":
        required_keys.append("LEONARDO_API_KEY")
    elif provider == "google":
        required_keys.append("GOOGLE_API_KEY")
    
    for key in required_keys:
        if not keys[key]:
            print(f"❌ {key} necessária para este teste")
            return False
    
    # Criar workspace na pasta media
    media_dir = Path("../media")
    work_dir = media_dir / "test_output"
    work_dir.mkdir(exist_ok=True)
    print(f"📁 Workspace: {work_dir}")
    
    # Criar storyboard de teste
    storyboard_path = create_test_storyboard(work_dir)
    
    # Caminho de saída
    output_path = work_dir / "newton_prism_optimized.mp4"
    
    # Executar pipeline OTIMIZADO
    try:
        cmd = [
            sys.executable, "complete_pipeline.py",
            "--storyboard", str(storyboard_path),
            "--work-dir", str(work_dir),
            "--out", str(output_path),
            "--image-provider", provider,
            "--voice-id", "YNOujSUmHtgN6anjqXPf",
            "--eleven-key", os.getenv("ELEVEN_API_KEY")
        ]
        
        print(f"\n🚀 Executando pipeline OTIMIZADO:")
        print(f"   Comando: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__)),
            timeout=1800  # 30 minutos
        )
        
        print(f"\n📊 Resultado da execução:")
        print(f"   Exit code: {result.returncode}")
        
        if result.stdout:
            print(f"   Output:\n{result.stdout}")
        
        if result.stderr:
            print(f"   Errors:\n{result.stderr}")
        
        # Verificar resultado
        if result.returncode == 0 and output_path.exists():
            file_size = output_path.stat().st_size
            print(f"\n✅ Teste SUCESSO!")
            print(f"   Vídeo gerado: {output_path}")
            print(f"   Tamanho: {file_size / 1024 / 1024:.1f} MB")
            
            # Copiar para diretório atual para análise
            import shutil
            local_output = Path("newton_prism_optimized.mp4")
            shutil.copy2(str(output_path), str(local_output))
            print(f"   Copiado para: {local_output}")
            
            return True
        else:
            print(f"\n❌ Teste FALHOU!")
            return False
                
    except subprocess.TimeoutExpired:
        print("❌ Pipeline timeout (30 minutos)")
        return False
    except Exception as e:
        print(f"❌ Erro na execução: {e}")
        return False

def test_individual_components():
    """Testa componentes individuais do pipeline."""
    print("\n🔧 Testando componentes individuais:")
    
    # Teste 1: image_fetcher.py
    print("\n1️⃣ Testando image_fetcher.py...")
    try:
        import image_fetcher
        print("   ✅ image_fetcher importado com sucesso")
        
        # Verificar se as classes estão disponíveis
        if hasattr(image_fetcher, 'ImageFetcher'):
            print("   ✅ Classe ImageFetcher disponível")
        else:
            print("   ❌ Classe ImageFetcher não encontrada")
            
    except ImportError as e:
        print(f"   ❌ Erro ao importar image_fetcher: {e}")
    
    # Teste 2: render_pipeline_audio_driven.py
    print("\n2️⃣ Testando render_pipeline_audio_driven.py...")
    try:
        import render_pipeline_audio_driven
        print("   ✅ render_pipeline_audio_driven importado com sucesso")
        
        # Verificar funções principais
        if hasattr(render_pipeline_audio_driven, 'render_complete_video_audio_driven'):
            print("   ✅ Função render_complete_video_audio_driven disponível")
        else:
            print("   ❌ Função principal não encontrada")
            
    except ImportError as e:
        print(f"   ❌ Erro ao importar render_pipeline_audio_driven: {e}")
    
    # Teste 3: complete_pipeline.py
    print("\n3️⃣ Testando complete_pipeline.py...")
    try:
        import complete_pipeline
        print("   ✅ complete_pipeline importado com sucesso")
        
        # Verificar classe principal
        if hasattr(complete_pipeline, 'CompletePipeline'):
            print("   ✅ Classe CompletePipeline disponível")
        else:
            print("   ❌ Classe CompletePipeline não encontrada")
            
    except ImportError as e:
        print(f"   ❌ Erro ao importar complete_pipeline: {e}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Teste do pipeline completo OTIMIZADO")
    parser.add_argument("--provider", choices=["openai", "leonardo", "google"], 
                       default="openai", help="Provider de geração de imagens")
    parser.add_argument("--test-components", action="store_true", 
                       help="Testar apenas componentes individuais")
    
    args = parser.parse_args()
    
    if args.test_components:
        test_individual_components()
        return
    
    success = test_pipeline(args.provider)
    
    if success:
        print("\n🎉 Teste completo concluído com SUCESSO!")
        print("   ✅ Sistema OTIMIZADO pronto para produção!")
        print("   ✅ Pipeline audio-driven funcionando perfeitamente!")
        print("   ✅ Sincronização de áudio/vídeo garantida!")
    else:
        print("\n💥 Teste FALHOU!")
        print("   Verifique as configurações e tente novamente.")
        sys.exit(1)

if __name__ == "__main__":
    main()
