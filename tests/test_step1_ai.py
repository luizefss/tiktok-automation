#!/usr/bin/env python3
"""
test_step1_ai.py - Teste isolado do AI Orchestrator
Execute este arquivo PRIMEIRO para verificar se a geração de roteiro funciona
"""

import os
import sys
from dotenv import load_dotenv

# Carregar variáveis de ambiente do .env
load_dotenv()

print("\n" + "="*70)
print("🧪 TESTE PASSO 1: GERAÇÃO DE ROTEIRO")
print("="*70 + "\n")

# Verificar se o .env está configurado
print("📋 Verificando configuração do .env...")
print("-"*40)

gemini_key = os.getenv('GEMINI_API_KEY')
claude_key = os.getenv('CLAUDE_API_KEY')
openai_key = os.getenv('OPENAI_API_KEY')

print(
    f"GEMINI_API_KEY: {'✅ Configurada' if gemini_key else '❌ Não encontrada'}")
print(
    f"CLAUDE_API_KEY: {'✅ Configurada' if claude_key else '❌ Não encontrada'}")
print(
    f"OPENAI_API_KEY: {'✅ Configurada' if openai_key else '❌ Não encontrada'}")

if not any([gemini_key, claude_key, openai_key]):
    print("\n⚠️ ATENÇÃO: Nenhuma API key encontrada!")
    print("Verifique se o arquivo .env existe e contém as chaves.")
    print("O sistema usará o modo fallback (roteiro básico).")

print("\n" + "-"*40 + "\n")

# Tentar importar o AI Orchestrator
try:
    from ai_orchestrator import AIOrchestrator
    print("✅ Módulo ai_orchestrator.py importado com sucesso!")
except ImportError as e:
    print(f"❌ Erro ao importar ai_orchestrator.py: {e}")
    print("Certifique-se de que o arquivo ai_orchestrator.py existe no mesmo diretório.")
    sys.exit(1)

print("\n" + "-"*40 + "\n")

# Criar instância e testar
print("🤖 Inicializando AI Orchestrator...")
try:
    ai = AIOrchestrator()
    print("✅ AI Orchestrator inicializado!\n")
except Exception as e:
    print(f"❌ Erro ao inicializar: {e}")
    sys.exit(1)

# Testar geração de roteiro
print("📝 Gerando roteiro de teste...")
print("-"*40)
print("Tema: Os mistérios do oceano profundo")
print("Duração: 30 segundos")
print("Tipo: mystery")
print("-"*40 + "\n")

try:
    result = ai.generate_script(
        topic="os mistérios do oceano profundo",
        duration=30,
        content_type="mystery"
    )

    print("✅ ROTEIRO GERADO COM SUCESSO!")
    print("\n" + "="*70)
    print("📊 RESULTADO:")
    print("="*70)
    print(f"\n🤖 IA utilizada: {result['ai_used']}")
    print(f"📌 Título: {result['title']}")
    print(f"⏱️ Duração: {result['duration']} segundos")
    print(f"📅 Timestamp: {result['timestamp']}")

    print("\n📜 TEXTO DO ROTEIRO (primeiros 500 caracteres):")
    print("-"*40)
    print(result['full_text'][:500])
    if len(result['full_text']) > 500:
        print("...")

    print("\n🏷️ ESTRUTURA DO ROTEIRO:")
    print("-"*40)
    structured = result.get('structured', {})
    if structured:
        print(f"Hook: {structured.get('hook', 'N/A')[:100]}...")
        print(f"Palavras-chave: {structured.get('keywords', [])}")
        print(f"CTA: {structured.get('cta', 'N/A')}")
        sections = structured.get('sections', [])
        print(f"Número de seções: {len(sections)}")
        # Mostrar apenas 3 primeiras
        for i, section in enumerate(sections[:3]):
            if isinstance(section, dict):
                print(
                    f"  Seção {i+1}: {section.get('type', 'N/A')} - {section.get('emotion', 'N/A')}")

    print("\n" + "="*70)
    print("✅ TESTE CONCLUÍDO COM SUCESSO!")
    print("="*70)

    # Salvar roteiro de teste
    print("\n💾 Salvando roteiro de teste...")
    os.makedirs("./test_outputs", exist_ok=True)

    import json
    with open("./test_outputs/test_script.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    with open("./test_outputs/test_script.txt", "w", encoding="utf-8") as f:
        f.write(f"TÍTULO: {result['title']}\n")
        f.write("="*50 + "\n\n")
        f.write(result['full_text'])

    print("✅ Arquivos salvos em ./test_outputs/")
    print("  - test_script.json (estrutura completa)")
    print("  - test_script.txt (texto do roteiro)")

except Exception as e:
    print(f"\n❌ ERRO ao gerar roteiro: {e}")
    import traceback
    print("\nDetalhes do erro:")
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*70)
print("🎉 PASSO 1 COMPLETO! Agora você pode prosseguir para o Passo 2 (TTS)")
print("="*70 + "\n")
