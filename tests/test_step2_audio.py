#!/usr/bin/env python3
"""
test_step2_audio.py - Teste SIMPLES do sistema de TTS
Teste direto sem dependências complexas
"""

import os
import sys
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

print("\n" + "="*60)
print("🎙️ TESTE PASSO 2: GERAÇÃO DE ÁUDIO")
print("="*60 + "\n")

# Criar pasta para outputs
os.makedirs("./test_outputs", exist_ok=True)

# Texto simples para teste
test_text = """
Você já se perguntou sobre os mistérios do oceano?

Nas profundezas inexploradas, existem segredos que desafiam nossa compreensão...

Prepare-se para uma jornada fascinante.
"""

print("📜 Texto para narração:")
print("-"*40)
print(test_text)
print("-"*40 + "\n")

# Tentar importar e usar o TTS
try:
    from advanced_tts import AdvancedTTS

    # Inicializar TTS
    print("🎙️ Inicializando TTS...")
    tts = AdvancedTTS()

    # Testar geração básica
    print("\n📍 Teste 1: Geração básica (tom misterioso)")
    output1 = "./test_outputs/teste_misterioso.mp3"

    result1 = tts.generate_speech(
        text=test_text,
        output_path=output1,
        emotion="mysterious"
    )

    if result1:
        size = os.path.getsize(output1) / 1024
        print(f"✅ Áudio gerado: {output1} ({size:.1f} KB)")
    else:
        print("❌ Falha ao gerar áudio misterioso")

    # Teste 2: Tom conversacional
    print("\n📍 Teste 2: Tom conversacional (mais natural)")
    output2 = "./test_outputs/teste_conversacional.mp3"

    result2 = tts.generate_speech(
        text=test_text,
        output_path=output2,
        emotion="conversational"
    )

    if result2:
        size = os.path.getsize(output2) / 1024
        print(f"✅ Áudio gerado: {output2} ({size:.1f} KB)")
    else:
        print("❌ Falha ao gerar áudio conversacional")

    # Teste 3: Texto curto com velocidade normal
    print("\n📍 Teste 3: Texto curto")
    test_short = "Este é um teste rápido de áudio. A voz deve soar natural e fluida."
    output3 = "./test_outputs/teste_curto.mp3"

    result3 = tts.generate_speech(
        text=test_short,
        output_path=output3,
        emotion="serious"  # Tom neutro/sério
    )

    if result3:
        size = os.path.getsize(output3) / 1024
        print(f"✅ Áudio gerado: {output3} ({size:.1f} KB)")
    else:
        print("❌ Falha ao gerar áudio curto")

    # Resumo
    print("\n" + "="*60)
    print("📊 RESUMO DOS TESTES:")
    print("="*60)

    success_count = sum([bool(result1), bool(result2), bool(result3)])
    print(f"\nÁudios gerados: {success_count}/3")

    if success_count > 0:
        print("\n✅ TESTE CONCLUÍDO COM SUCESSO!")
        print("\n📁 Arquivos gerados em ./test_outputs/:")
        print("   - teste_misterioso.mp3 (tom grave e pausado)")
        print("   - teste_conversacional.mp3 (tom natural)")
        print("   - teste_curto.mp3 (tom neutro)")
        print("\n🎧 Ouça os áudios para verificar:")
        print("   1. Se a velocidade está boa")
        print("   2. Se o tom está adequado")
        print("   3. Se as pausas estão naturais")
    else:
        print("\n❌ Nenhum áudio foi gerado")

except ImportError as e:
    print(f"❌ Erro ao importar: {e}")
    print("\n🔧 Soluções:")
    print("1. Verifique se advanced_tts.py existe")
    print("2. Instale as dependências:")
    print("   pip install google-cloud-texttospeech")
    print("   pip install librosa soundfile scipy")

except Exception as e:
    print(f"❌ Erro inesperado: {e}")
    import traceback
    print("\n🔍 Detalhes do erro:")
    traceback.print_exc()

print("\n")
