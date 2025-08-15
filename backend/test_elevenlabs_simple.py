#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Teste Simples d        
        if result:
            # O método generate_audio do ElevenLabs já salva o arquivo automaticamente
            if os.path.exists(result):
                file_size = os.path.getsize(result)
                print(f"✅ Áudio gerado com sucesso!")
                print(f"📁 Arquivo: {result}")
                print(f"💽 Tamanho: {file_size} bytes")
                return True
            else:
                print(f"❌ Arquivo não foi criado: {result}")
                return False
        else:
            print("❌ Falha na geração do áudio")
            return Falsebs TTS
===============================
Teste rápido para validar que o ElevenLabs está funcionando corretamente.
"""

import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Adicionar o diretório backend ao path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

async def test_elevenlabs_simple():
    """Teste simples do ElevenLabs TTS"""
    print("🎙️ TESTE SIMPLES ELEVENLABS TTS")
    print("=" * 50)
    
    # Carregar variáveis de ambiente
    load_dotenv()
    
    elevenlabs_key = os.getenv('ELEVEN_API_KEY')
    if not elevenlabs_key:
        print("❌ ELEVEN_API_KEY não encontrada no .env")
        return False
    
    print(f"🔑 ElevenLabs API Key: {elevenlabs_key[:10]}...")
    
    try:
        from services.elevenlabs_tts import ElevenLabsTTS
        
        # Inicializar o serviço (sem api_key, ele lê do config)
        tts = ElevenLabsTTS()
        print("✅ Serviço ElevenLabs inicializado")
        
        # Listar vozes disponíveis
        print("\n📋 Listando vozes disponíveis...")
        voices = await tts.get_available_voices()
        print(f"✅ Encontradas {len(voices)} vozes:")
        for i, voice in enumerate(voices[:5]):  # Mostrar apenas as primeiras 5
            print(f"   {i+1}. {voice['name']} ({voice['voice_id'][:8]}...)")
        
        # Gerar um áudio de teste
        test_text = "Olá! Este é um teste do sistema ElevenLabs integrado ao pipeline de automação TikTok."
        output_path = "../media/audio/test_elevenlabs_audio.mp3"
        
        print(f"\n🎵 Gerando áudio de teste...")
        print(f"📝 Texto: {test_text}")
        print(f"💾 Saída: {output_path}")
        
        # Criar diretório se não existir
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Usar perfil de voz profissional masculino
        voice_profile = "male-professional"
        print(f"🎤 Usando perfil de voz: {voice_profile}")
        
        result = await tts.generate_audio(
            text=test_text,
            voice_profile=voice_profile
        )
        
        if result and os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            print(f"✅ Áudio gerado com sucesso!")
            print(f"📁 Arquivo: {output_path}")
            print(f"📏 Tamanho: {file_size} bytes")
            return True
        else:
            print(f"❌ Falha ao gerar áudio: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Erro no teste ElevenLabs: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Função principal"""
    success = asyncio.run(test_elevenlabs_simple())
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 TESTE ELEVENLABS PASSOU!")
        print("\n💡 Próximos passos:")
        print("   1. Integrar com pipeline de vídeo")
        print("   2. Testar diferentes vozes")
        print("   3. Ajustar configurações de qualidade")
    else:
        print("❌ TESTE ELEVENLABS FALHOU")
        print("\n🔧 Verificar:")
        print("   1. Chave de API no .env")
        print("   2. Conectividade com internet")
        print("   3. Saldo da conta ElevenLabs")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
