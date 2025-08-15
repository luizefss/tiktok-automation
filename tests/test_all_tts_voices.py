#!/usr/bin/env python3
# Teste Completo de Todas as Vozes TTS
import asyncio
import logging
import sys
import os
from datetime import datetime

sys.path.append('/var/www/tiktok-automation/backend')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Texto de teste otimizado para português brasileiro
TEST_TEXT = "Olá pessoal! Este é um teste da nossa nova voz para TikTok. Vocês não vão acreditar como ficou natural e humanizada. A tecnologia evoluiu muito e agora temos vozes que soam completamente brasileiras!"

async def test_google_cloud_tts_neural2():
    """Testar todas as vozes Neural2 brasileiras do Google Cloud TTS"""
    print("\n🇧🇷 TESTANDO GOOGLE CLOUD TTS - VOZES NEURAL2 BRASILEIRAS")
    print("=" * 70)
    
    try:
        from services.tts_service_enhanced import EnhancedTTSService
        from google.cloud import texttospeech
        
        tts = EnhancedTTSService()
        if not tts.client:
            print("❌ Google Cloud TTS não configurado")
            return []
        
        # Vozes Neural2 brasileiras disponíveis
        brazilian_voices = [
            {"name": "pt-BR-Neural2-A", "gender": "FEMALE", "desc": "Feminina Neural2 A"},
            {"name": "pt-BR-Neural2-B", "gender": "MALE", "desc": "Masculina Neural2 B"}, 
            {"name": "pt-BR-Neural2-C", "gender": "FEMALE", "desc": "Feminina Neural2 C"},
            {"name": "pt-BR-Wavenet-A", "gender": "FEMALE", "desc": "Feminina Wavenet A"},
            {"name": "pt-BR-Wavenet-B", "gender": "MALE", "desc": "Masculina Wavenet B"},
            {"name": "pt-BR-Standard-A", "gender": "FEMALE", "desc": "Feminina Standard A"},
            {"name": "pt-BR-Standard-B", "gender": "MALE", "desc": "Masculina Standard B"},
        ]
        
        results = []
        
        for voice in brazilian_voices:
            try:
                print(f"\n🎤 Testando: {voice['desc']} ({voice['name']})")
                
                # Configurar SSML otimizado
                ssml_text = f"""<speak>
<prosody rate="1.1" pitch="+1st">
{TEST_TEXT}
</prosody>
</speak>"""
                
                synthesis_input = texttospeech.SynthesisInput(ssml=ssml_text)
                
                voice_params = texttospeech.VoiceSelectionParams(
                    language_code="pt-BR",
                    name=voice["name"],
                    ssml_gender=getattr(texttospeech.SsmlVoiceGender, voice["gender"])
                )
                
                audio_config = texttospeech.AudioConfig(
                    audio_encoding=texttospeech.AudioEncoding.MP3,
                    speaking_rate=1.1,
                    pitch=1.0,
                    volume_gain_db=2.0
                )
                
                response = await asyncio.to_thread(
                    tts.client.synthesize_speech,
                    input=synthesis_input,
                    voice=voice_params,
                    audio_config=audio_config
                )
                
                # Salvar arquivo
                timestamp = datetime.now().strftime("%H%M%S")
                filename = f"google_{voice['name'].replace('-', '_')}_{timestamp}.mp3"
                filepath = f"/var/www/tiktok-automation/media/audio/{filename}"
                
                with open(filepath, "wb") as f:
                    f.write(response.audio_content)
                
                file_size = os.path.getsize(filepath)
                
                result = {
                    "service": "Google Cloud TTS",
                    "voice": voice["name"],
                    "description": voice["desc"],
                    "file": filepath,
                    "size": file_size,
                    "quality": "Neural2" if "Neural2" in voice["name"] else "Wavenet" if "Wavenet" in voice["name"] else "Standard"
                }
                
                results.append(result)
                print(f"✅ Gerado: {filename} ({file_size} bytes)")
                
            except Exception as e:
                print(f"❌ Erro: {voice['desc']} - {e}")
        
        return results
        
    except Exception as e:
        print(f"❌ Erro no Google Cloud TTS: {e}")
        return []

async def test_gemini_tts_models():
    """Testar os diferentes modelos do Gemini TTS"""
    print("\n🤖 TESTANDO GEMINI TTS - MODELOS FLASH E PRO")
    print("=" * 70)
    
    try:
        import google.generativeai as genai
        from google.genai import types
        from config_manager import get_config
        
        config = get_config()
        
        if not config.GEMINI_API_KEY:
            print("❌ GEMINI_API_KEY não configurada")
            return []
        
        # Configurar cliente com nova API
        client = genai.Client(api_key=config.GEMINI_API_KEY)
        
        # Modelos para testar
        models = [
            "gemini-2.5-flash-preview-tts",
            "gemini-2.5-pro-preview-tts"
        ]
        
        # Vozes disponíveis (escolher algumas principais)
        voices = ["Kore", "Charon", "Fenrir", "Aoede"]
        
        results = []
        
        for model in models:
            for voice_name in voices:
                try:
                    print(f"\n🎯 Testando: {model} com voz {voice_name}")
                    
                    # Texto otimizado para TTS
                    prompt = f"Diga com entusiasmo em português brasileiro: {TEST_TEXT}"
                    
                    response = client.models.generate_content(
                        model=model,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            response_modalities=["AUDIO"],
                            speech_config=types.SpeechConfig(
                                voice_config=types.VoiceConfig(
                                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                        voice_name=voice_name,
                                    )
                                )
                            ),
                        )
                    )
                    
                    # Extrair dados de áudio
                    audio_data = response.candidates[0].content.parts[0].inline_data.data
                    
                    if audio_data:
                        # Salvar arquivo
                        timestamp = datetime.now().strftime("%H%M%S")
                        filename = f"gemini_{model.replace('-', '_')}_{voice_name}_{timestamp}.wav"
                        filepath = f"/var/www/tiktok-automation/media/audio/{filename}"
                        
                        # Salvar como WAV usando wave
                        import wave
                        with wave.open(filepath, "wb") as wf:
                            wf.setnchannels(1)  # mono
                            wf.setsampwidth(2)  # 16-bit
                            wf.setframerate(24000)  # 24kHz
                            wf.writeframes(audio_data)
                        
                        file_size = os.path.getsize(filepath)
                        
                        result = {
                            "service": "Gemini TTS",
                            "voice": f"{model}-{voice_name}",
                            "description": f"{model} com voz {voice_name}",
                            "file": filepath,
                            "size": file_size,
                            "quality": "Pro" if "pro" in model else "Flash"
                        }
                        
                        results.append(result)
                        print(f"✅ Gerado: {filename} ({file_size} bytes)")
                    else:
                        print(f"❌ Nenhum dado de áudio retornado")
                        
                except Exception as e:
                    print(f"❌ Erro: {model}-{voice_name} - {e}")
                    
                # Pausa entre chamadas
                await asyncio.sleep(1)
        
        return results
        
    except Exception as e:
        print(f"❌ Erro no Gemini TTS: {e}")
        return []

async def main():
    print("🚀 TESTE COMPLETO DE SISTEMAS TTS PARA TIKTOK")
    print("=" * 80)
    
    all_results = []
    
    # Testar Google Cloud TTS
    google_results = await test_google_cloud_tts_neural2()
    all_results.extend(google_results)
    
    # Testar Gemini TTS
    gemini_results = await test_gemini_tts_models()
    all_results.extend(gemini_results)
    
    # Relatório final
    print("\n📊 RELATÓRIO FINAL - COMPARAÇÃO DE VOZES")
    print("=" * 80)
    
    if not all_results:
        print("❌ Nenhuma voz foi testada com sucesso")
        return
    
    # Agrupar por qualidade
    neural2_voices = [r for r in all_results if r["quality"] == "Neural2"]
    wavenet_voices = [r for r in all_results if r["quality"] == "Wavenet"]  
    gemini_voices = [r for r in all_results if "Gemini" in r["service"]]
    
    print(f"\n🥇 VOZES NEURAL2 (Melhor qualidade): {len(neural2_voices)}")
    for voice in neural2_voices:
        print(f"  ✅ {voice['description']} - {voice['size']} bytes - {voice['file']}")
    
    print(f"\n🥈 VOZES WAVENET (Boa qualidade): {len(wavenet_voices)}")
    for voice in wavenet_voices:
        print(f"  ✅ {voice['description']} - {voice['size']} bytes")
        
    print(f"\n🤖 VOZES GEMINI TTS: {len(gemini_voices)}")
    for voice in gemini_voices:
        print(f"  ✅ {voice['description']} - {voice['size']} bytes")
    
    # Recomendações
    print(f"\n💡 RECOMENDAÇÕES:")
    print(f"  🎯 Para qualidade máxima: pt-BR-Neural2-B (masculina) ou pt-BR-Neural2-A (feminina)")
    print(f"  🎯 Para fallback: pt-BR-Wavenet-B (masculina) ou pt-BR-Wavenet-A (feminina)")
    print(f"  🎯 Para Gemini: Usar o modelo flash com voz Kore para português")
    print(f"  📁 Todos os arquivos salvos em: /var/www/tiktok-automation/media/audio/")

if __name__ == "__main__":
    asyncio.run(main())