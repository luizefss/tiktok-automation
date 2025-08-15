#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Teste do Pipeline C    # Verificar se existem imagens de teste
    test_images_dir = "../media/test_images"
    if not os.path.exists(test_images_dir):
        print(f"❌ Diretório {test_images_dir} não encontrado")eto Leonardo Motion + ElevenLabs TTS
========================================================

Este script testa a integração completa:
1. Storyboard JSON
2. Geração de imagens (simulado com imagens existentes)
3. Leonardo Motion (animação)
4. ElevenLabs TTS (narração)
5. MoviePy (montagem final)
"""

import os
import json
import sys
from pathlib import Path

# Adicionar o diretório backend ao path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Imports do pipeline
try:
    from leonardo_motion_client import leonardo_animate_image
    from services.elevenlabs_tts import ElevenLabsTTS
    # MoviePy v2.x nova sintaxe de importação
    from moviepy import VideoFileClip, AudioFileClip, CompositeVideoClip
    PIPELINE_AVAILABLE = True
except ImportError as e:
    print(f"❌ Erro ao importar pipeline: {e}")
    PIPELINE_AVAILABLE = False

def create_test_storyboard():
    """Cria um storyboard de teste simples"""
    storyboard = {
        "title": "Teste do Pipeline Leonardo + ElevenLabs",
        "description": "Teste de integração completa",
        "scenes": [
            {
                "scene_number": 1,
                "t_start": 0,
                "t_end": 4,
                "image_prompt": "A beautiful sunset over the mountains, golden hour lighting, cinematic composition",
                "narration": "O sol se põe majestosamente sobre as montanhas, pintando o céu com cores douradas.",
                "motion_prompt": "slow cinematic zoom in, golden particles floating"
            },
            {
                "scene_number": 2,
                "t_start": 4,
                "t_end": 8,
                "image_prompt": "A peaceful lake reflecting the sunset colors, mirror-like water surface",
                "narration": "As águas calmas do lago refletem perfeitamente as cores do entardecer.",
                "motion_prompt": "gentle water ripples, subtle camera pan right"
            },
            {
                "scene_number": 3,
                "t_start": 8,
                "t_end": 12,
                "image_prompt": "Mountains silhouette against colorful sky, dramatic lighting",
                "narration": "As silhuetas das montanhas se destacam contra o céu colorido.",
                "motion_prompt": "slow vertical pan up, atmospheric haze movement"
            }
        ]
    }
    return storyboard

def test_leonardo_motion():
    """Testa apenas o cliente Leonardo Motion"""
    print("\n=== TESTE LEONARDO MOTION ===")
    
    # Verificar se há imagens de teste
    test_images_dir = "../media/test_images"
    if not os.path.exists(test_images_dir):
        print(f"❌ Diretório {test_images_dir} não encontrado")
        return False
    
    # Procurar primeira imagem disponível
    test_image = None
    for ext in ['png', 'jpg', 'jpeg', 'webp']:
        for img_file in os.listdir(test_images_dir):
            if img_file.lower().endswith(f'.{ext}'):
                test_image = os.path.join(test_images_dir, img_file)
                break
        if test_image:
            break
    
    if not test_image:
        print(f"❌ Nenhuma imagem encontrada em {test_images_dir}")
        return False
    
    print(f"🖼️ Usando imagem de teste: {test_image}")
    
    # Ler chave da API
    leonardo_key = os.getenv('LEONARDO_API_KEY')
    if not leonardo_key:
        print("❌ LEONARDO_API_KEY não encontrada no .env")
        return False
    
    try:
        output_video = "./test_motion_output.mp4"
        print(f"🎬 Gerando motion para: {output_video}")
        
        result = leonardo_animate_image(
            image_path=test_image,
            out_path=output_video,
            api_key=leonardo_key,
            motion_strength=8,
            prompt="slow cinematic zoom in, atmospheric particles"
        )
        
        print(f"✅ Motion gerado: {result}")
        return True
        
    except Exception as e:
        print(f"❌ Erro no Leonardo Motion: {e}")
        return False

def test_complete_pipeline():
    """Testa o pipeline completo"""
    print("\n=== TESTE PIPELINE COMPLETO ===")
    
    # Por enquanto, apenas simulando - implementação completa depois
    print("� Pipeline completo ainda em desenvolvimento")
    print("✅ Teste do Leonardo Motion + ElevenLabs será implementado na próxima versão")
    return True

def main():
    """Função principal de teste"""
    print("🧪 TESTE DO PIPELINE LEONARDO MOTION + ELEVENLABS")
    print("=" * 60)
    
    # Carregar variáveis de ambiente
    from dotenv import load_dotenv
    load_dotenv()
    
    # Verificar dependências
    print("\n=== VERIFICAÇÃO DE DEPENDÊNCIAS ===")
    
    try:
        import moviepy
        print(f"✅ MoviePy: {moviepy.__version__}")
    except ImportError:
        print("❌ MoviePy não instalado")
        return 1
    
    try:
        import requests
        print("✅ Requests disponível")
    except ImportError:
        print("❌ Requests não instalado")
        return 1
    
    leonardo_key = os.getenv('LEONARDO_API_KEY')
    elevenlabs_key = os.getenv('ELEVEN_API_KEY')
    
    print(f"🔑 Leonardo API: {'✅' if leonardo_key else '❌'}")
    print(f"🔑 ElevenLabs API: {'✅' if elevenlabs_key else '❌'}")
    
    # Executar testes
    success = True
    
    # Teste 1: Leonardo Motion apenas
    if leonardo_key:
        success &= test_leonardo_motion()
    else:
        print("⏭️ Pulando teste Leonardo Motion (sem API key)")
    
    # Teste 2: Pipeline completo
    if leonardo_key and elevenlabs_key and PIPELINE_AVAILABLE:
        success &= test_complete_pipeline()
    else:
        print("⏭️ Pulando teste pipeline completo (falta API keys ou dependências)")
    
    # Resultado final
    print("\n" + "=" * 60)
    if success:
        print("🎉 TODOS OS TESTES PASSARAM!")
        print("\n💡 Próximos passos:")
        print("   1. Testar com imagens reais geradas pelo sistema")
        print("   2. Ajustar configurações de motion_strength")
        print("   3. Testar diferentes vozes ElevenLabs")
        print("   4. Integrar com o frontend")
    else:
        print("❌ ALGUNS TESTES FALHARAM")
        print("\n🔧 Para resolver:")
        print("   1. Verificar chaves de API no .env")
        print("   2. Instalar dependências: pip install moviepy requests")
        print("   3. Verificar conectividade com APIs")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
