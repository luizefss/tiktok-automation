#!/usr/bin/env python3
# Teste do Sistema de Áudio Humanizado
import asyncio
import logging
import sys
import os
import json

# Adicionar path do backend
sys.path.append('/var/www/tiktok-automation/backend')

from services.gemini_tts_service import GeminiTTSService
from services.tts_service_enhanced import EnhancedTTSService

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_gemini_tts():
    """Testar Gemini TTS humanizado"""
    print("🔥 TESTANDO GEMINI TTS HUMANIZADO")
    print("=" * 50)
    
    gemini_tts = GeminiTTSService()
    
    test_text = "Olá pessoal, este é um teste da nossa nova voz humanizada. Cara, vocês não vão acreditar como ficou natural agora!"
    
    try:
        result = await gemini_tts.generate_humanized_audio(
            text=test_text,
            voice_profile="male-professional",
            emotion="enthusiastic",
            pitch=0.0,
            speed=1.0,
            volume_gain=0.0,
            accent="pt-BR"
        )
        
        print(f"✅ Resultado: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        if result.get('success'):
            audio_path = result.get('audio_path')
            if audio_path and os.path.exists(audio_path):
                file_size = os.path.getsize(audio_path)
                print(f"📁 Arquivo criado: {audio_path}")
                print(f"📏 Tamanho: {file_size} bytes")
                
                if file_size > 0:
                    print("✅ SUCESSO: Áudio gerado com conteúdo!")
                    return True
                else:
                    print("❌ ERRO: Arquivo vazio (0kb)")
                    return False
            else:
                print("❌ ERRO: Arquivo não foi criado")
                return False
        else:
            print(f"❌ ERRO: {result.get('error', 'Erro desconhecido')}")
            return False
            
    except Exception as e:
        print(f"❌ EXCEÇÃO: {str(e)}")
        return False

async def test_google_tts():
    """Testar Google Cloud TTS humanizado"""
    print("\n🎤 TESTANDO GOOGLE CLOUD TTS HUMANIZADO")
    print("=" * 50)
    
    google_tts = EnhancedTTSService()
    
    test_text = "Esta é uma demonstração do Google Cloud TTS humanizado. A voz deve soar natural e com emoção."
    
    try:
        result = await google_tts.generate_audio(
            text=test_text,
            voice_profile="male-professional",
            emotion="dramatic",
            pitch=0.0,
            speed=1.0,
            volume_gain=0.0,
            accent="pt-BR"
        )
        
        print(f"✅ Resultado: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        if result.get('success'):
            audio_path = result.get('audio_path')
            if audio_path and os.path.exists(audio_path):
                file_size = os.path.getsize(audio_path)
                print(f"📁 Arquivo criado: {audio_path}")
                print(f"📏 Tamanho: {file_size} bytes")
                
                if file_size > 0:
                    print("✅ SUCESSO: Áudio Google TTS gerado com conteúdo!")
                    return True
                else:
                    print("❌ ERRO: Arquivo Google TTS vazio (0kb)")
                    return False
            else:
                print("❌ ERRO: Arquivo Google TTS não foi criado")
                return False
        else:
            print(f"❌ ERRO Google TTS: {result.get('error', 'Erro desconhecido')}")
            return False
            
    except Exception as e:
        print(f"❌ EXCEÇÃO Google TTS: {str(e)}")
        return False

async def main():
    print("🚀 INICIANDO TESTES DE ÁUDIO HUMANIZADO")
    print("=" * 60)
    
    # Testar Gemini TTS
    gemini_success = await test_gemini_tts()
    
    # Testar Google TTS
    google_success = await test_google_tts()
    
    # Resumo
    print("\n📊 RESUMO DOS TESTES")
    print("=" * 30)
    print(f"Gemini TTS: {'✅ PASSOU' if gemini_success else '❌ FALHOU'}")
    print(f"Google TTS: {'✅ PASSOU' if google_success else '❌ FALHOU'}")
    
    if gemini_success or google_success:
        print("\n🎉 PELO MENOS UM SISTEMA DE TTS FUNCIONANDO!")
        print("✅ Sistema de áudio humanizado está operacional")
    else:
        print("\n⚠️ NENHUM SISTEMA DE TTS FUNCIONANDO CORRETAMENTE")
        print("❌ Necessário investigar problemas de configuração")

if __name__ == "__main__":
    asyncio.run(main())