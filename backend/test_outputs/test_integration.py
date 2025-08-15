#!/usr/bin/env python3
# /var/www/tiktok-automation/backend/test_integration.py

"""
Teste de integração do sistema TTS aprimorado
Verifica compatibilidade e funcionalidades avançadas
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.tts_service_enhanced import TTSServiceEnhanced
import json

def test_compatibility():
    """Testa compatibilidade com a interface antiga"""
    print("🔄 Testando compatibilidade com interface atual...")
    
    tts = TTSServiceEnhanced()
    
    # Testa método antigo
    test_script = "Olá! Este é um teste de compatibilidade do nosso sistema."
    audio_file = tts.generate_audio_sync(test_script, "mulher_nova_carioca")
    
    if audio_file:
        print(f"   ✅ Compatibilidade OK - Arquivo: {audio_file}")
        return True
    else:
        print("   ❌ Falha na compatibilidade")
        return False

def test_enhanced_features():
    """Testa recursos aprimorados"""
    print("\n🚀 Testando recursos aprimorados...")
    
    tts = TTSServiceEnhanced()
    
    # Teste 1: Áudio com emoção específica
    test_script = "Que descoberta incrível e emocionante!"
    audio_file = tts.generate_audio_with_emotion(test_script, "enthusiastic", "mulher_nova_carioca")
    
    success_1 = audio_file is not None
    print(f"   Teste emoção específica: {'✅' if success_1 else '❌'}")
    
    # Teste 2: Áudio premium com recomendação automática
    test_script = "Bem-vindos ao nosso canal educativo sobre ciência!"
    audio_file = tts.generate_audio_premium(test_script, target_audience="estudantes")
    
    success_2 = audio_file is not None
    print(f"   Teste áudio premium: {'✅' if success_2 else '❌'}")
    
    # Teste 3: Análise de emoções
    test_script = "Que história incrível! Mas algo misterioso aconteceu... Estou muito feliz!"
    analysis = tts.analyze_script_emotions(test_script)
    
    success_3 = len(analysis.get("segments", [])) > 0
    print(f"   Teste análise emoções: {'✅' if success_3 else '❌'}")
    print(f"     - Emoção dominante: {analysis.get('dominant_emotion', 'N/A')}")
    print(f"     - Segmentos encontrados: {analysis.get('total_segments', 0)}")
    
    return success_1 and success_2 and success_3

def test_voice_listing():
    """Testa listagem de vozes"""
    print("\n🎤 Testando listagem de vozes...")
    
    tts = TTSServiceEnhanced()
    voices = tts.get_available_voices()
    
    legacy_count = len(voices.get("legacy_voices", {}))
    premium_count = len(voices.get("premium_voices", {}))
    total_count = voices.get("total_count", 0)
    
    print(f"   Vozes legadas: {legacy_count}")
    print(f"   Vozes premium: {premium_count}")
    print(f"   Total: {total_count}")
    
    # Lista algumas vozes
    if legacy_count > 0:
        print("   Vozes legadas disponíveis:")
        for voice_id, voice_info in list(voices["legacy_voices"].items())[:3]:
            print(f"     - {voice_id}: {voice_info['name']}")
    
    return total_count > 0

def test_voice_quality():
    """Testa qualidade de voz"""
    print("\n🎵 Testando qualidade de voz...")
    
    tts = TTSServiceEnhanced()
    
    # Testa diferentes perfis
    test_profiles = ["default-female", "premium-male-professional", "neural-female-natural"]
    results = []
    
    for profile in test_profiles:
        result = tts.test_voice_quality(profile)
        results.append(result)
        
        if result["success"]:
            print(f"   ✅ {profile}: {result['file_size_kb']} KB")
        else:
            print(f"   ❌ {profile}: {result.get('error', 'Erro desconhecido')}")
    
    return any(r["success"] for r in results)

def test_emotion_configs():
    """Testa configurações de emoção"""
    print("\n🎭 Testando configurações de emoção...")
    
    tts = TTSServiceEnhanced()
    
    emotions = ["neutral", "dramatic", "enthusiastic", "mysterious", "calm"]
    configs_found = []
    
    for emotion in emotions:
        config = tts.get_emotion_config(emotion)
        configs_found.append(config)
        
        speaking_rate = config.get("speaking_rate", "N/A")
        pitch = config.get("pitch", "N/A")
        print(f"   {emotion}: velocidade={speaking_rate}, tom={pitch}")
    
    return all(c for c in configs_found)

def run_integration_tests():
    """Executa todos os testes de integração"""
    print("🧪 INICIANDO TESTES DE INTEGRAÇÃO")
    print("=" * 60)
    
    tests = [
        ("Compatibilidade", test_compatibility),
        ("Recursos Aprimorados", test_enhanced_features),
        ("Listagem de Vozes", test_voice_listing),
        ("Qualidade de Voz", test_voice_quality),
        ("Configurações de Emoção", test_emotion_configs)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ Erro em {test_name}: {e}")
            results[test_name] = False
    
    # Relatório final
    print("\n" + "=" * 60)
    print("📊 RELATÓRIO DE INTEGRAÇÃO")
    print("=" * 60)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, success in results.items():
        status = "✅ PASSOU" if success else "❌ FALHOU"
        print(f"{test_name:.<35} {status}")
    
    print(f"\n🎯 RESULTADO: {passed}/{total} testes passaram ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 INTEGRAÇÃO COMPLETA! Todos os recursos funcionam perfeitamente!")
        print("💡 O sistema está pronto para uso em produção.")
    elif passed >= total * 0.8:
        print("✅ INTEGRAÇÃO BOA! Maioria dos recursos funciona.")
        print("⚠️ Alguns recursos podem precisar de ajustes.")
    else:
        print("⚠️ INTEGRAÇÃO PARCIAL! Muitos recursos falharam.")
        print("🔧 Verifique configurações e dependências.")
    
    return passed, total

if __name__ == "__main__":
    run_integration_tests()
