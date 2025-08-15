#!/usr/bin/env python3
# Teste Específico do Gemini TTS com Nova API
import asyncio
import logging
import sys
import os
from datetime import datetime
import wave

sys.path.append('/var/www/tiktok-automation/backend')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

TEST_TEXT = "Olá pessoal! Este é um teste da nossa nova voz para TikTok. Vocês não vão acreditar como ficou natural e humanizada!"

async def test_gemini_tts_v2():
    """Testar Gemini TTS com a API mais simples"""
    print("\n🤖 TESTANDO GEMINI TTS - API ALTERNATIVA")
    print("=" * 50)
    
    try:
        import google.generativeai as genai
        from config_manager import get_config
        
        config = get_config()
        
        if not config.GEMINI_API_KEY:
            print("❌ GEMINI_API_KEY não configurada")
            return []
        
        genai.configure(api_key=config.GEMINI_API_KEY)
        
        # Testar modelos TTS disponíveis
        models = [
            "gemini-2.5-flash-preview-tts",
            "gemini-2.5-pro-preview-tts"
        ]
        
        results = []
        
        for model_name in models:
            try:
                print(f"\n🎯 Testando: {model_name}")
                
                model = genai.GenerativeModel(model_name)
                
                # Prompt otimizado para TTS em português
                prompt = f"Diga de forma natural e entusiasmada: {TEST_TEXT}"
                
                # Configuração específica para áudio
                generation_config = genai.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=1000,
                )
                
                response = model.generate_content(
                    prompt,
                    generation_config=generation_config
                )
                
                # Verificar se há conteúdo de áudio
                print(f"Resposta: {response.text if hasattr(response, 'text') else 'Sem texto'}")
                
                if hasattr(response, 'candidates') and response.candidates:
                    candidate = response.candidates[0]
                    print(f"Candidate parts: {len(candidate.content.parts) if hasattr(candidate.content, 'parts') else 0}")
                    
                    # Procurar por dados de áudio
                    for part in candidate.content.parts:
                        if hasattr(part, 'inline_data') and part.inline_data:
                            print(f"✅ Encontrado dados inline: {len(part.inline_data.data)} bytes")
                            
                            # Salvar áudio
                            timestamp = datetime.now().strftime("%H%M%S")
                            filename = f"gemini_v2_{model_name.replace('-', '_')}_{timestamp}.wav"
                            filepath = f"/var/www/tiktok-automation/media/audio/{filename}"
                            
                            with wave.open(filepath, "wb") as wf:
                                wf.setnchannels(1)
                                wf.setsampwidth(2)
                                wf.setframerate(24000)
                                wf.writeframes(part.inline_data.data)
                            
                            file_size = os.path.getsize(filepath)
                            print(f"✅ Gerado: {filename} ({file_size} bytes)")
                            
                            results.append({
                                "model": model_name,
                                "file": filepath,
                                "size": file_size
                            })
                            break
                    else:
                        print("❌ Nenhum dado de áudio encontrado")
                else:
                    print("❌ Nenhum candidate encontrado")
                
            except Exception as e:
                print(f"❌ Erro com {model_name}: {e}")
        
        return results
        
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        return []

async def test_simple_gemini_call():
    """Teste mais simples possível"""
    print("\n🔍 TESTE BÁSICO GEMINI")
    print("=" * 30)
    
    try:
        import google.generativeai as genai
        from config_manager import get_config
        
        config = get_config()
        genai.configure(api_key=config.GEMINI_API_KEY)
        
        # Listar modelos disponíveis
        print("Modelos disponíveis:")
        for model in genai.list_models():
            if 'tts' in model.name.lower():
                print(f"  📍 {model.name}")
        
        # Tentar usar o modelo normal primeiro
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content("Diga olá em português brasileiro")
        print(f"Resposta texto: {response.text}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro básico: {e}")
        return False

async def main():
    print("🧪 TESTE ESPECÍFICO GEMINI TTS")
    print("=" * 40)
    
    # Teste básico primeiro
    basic_ok = await test_simple_gemini_call()
    
    if basic_ok:
        # Teste TTS específico
        results = await test_gemini_tts_v2()
        
        if results:
            print(f"\n✅ SUCESSO: {len(results)} arquivos de áudio gerados")
            for result in results:
                print(f"  🎵 {result['model']}: {result['size']} bytes")
        else:
            print("\n❌ Nenhum arquivo de áudio foi gerado")
    else:
        print("\n❌ Falha no teste básico - verifique configuração")

if __name__ == "__main__":
    asyncio.run(main())