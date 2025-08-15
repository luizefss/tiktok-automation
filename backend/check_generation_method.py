#!/usr/bin/env python3
"""
Teste para verificar qual método de geração está sendo usado
"""

import os
import sys
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

def check_image_generation_method():
    """Verifica qual método de geração está ativo"""
    print("🔍 Verificando métodos de geração disponíveis...")
    
    # Verificar Vertex AI
    vertex_available = False
    try:
        from google.cloud import aiplatform
        project_id = os.getenv('VERTEX_AI_PROJECT_ID')
        if project_id:
            aiplatform.init(project=project_id, location='us-central1')
            vertex_available = True
            print("✅ Vertex AI: Disponível")
        else:
            print("❌ Vertex AI: PROJECT_ID não configurado")
    except Exception as e:
        print(f"❌ Vertex AI: Erro - {e}")
    
    # Verificar Google AI Studio
    studio_available = False
    try:
        import google.generativeai as genai
        api_key = os.getenv('GOOGLE_AI_STUDIO_API_KEY')
        if api_key:
            genai.configure(api_key=api_key)
            studio_available = True
            print("✅ Google AI Studio: Disponível")
        else:
            print("❌ Google AI Studio: API_KEY não configurada")
    except Exception as e:
        print(f"❌ Google AI Studio: Erro - {e}")
    
    # Verificar qual será usado
    print("\n🎯 Método que será usado:")
    if vertex_available:
        print("🚀 VERTEX AI (Imagen 3) - Método principal")
    elif studio_available:
        print("🔄 GOOGLE AI STUDIO (Fallback API)")
    else:
        print("⚠️ GERAÇÃO PROCEDURAL (Último recurso)")
    
    return vertex_available, studio_available

if __name__ == "__main__":
    print("🔬 Análise de Métodos de Geração - TikTok Automation")
    print("=" * 60)
    
    vertex, studio = check_image_generation_method()
    
    print("\n" + "=" * 60)
    print("📋 RESUMO:")
    print(f"   Vertex AI: {'✅ Ativo' if vertex else '❌ Inativo'}")
    print(f"   Google AI Studio: {'✅ Ativo' if studio else '❌ Inativo'}")
    
    if vertex:
        print("\n🎉 USANDO IMAGEN 3 VIA VERTEX AI (melhor qualidade)")
    elif studio:
        print("\n⚠️ USANDO FALLBACK API (boa qualidade)")
    else:
        print("\n🔧 USANDO GERAÇÃO PROCEDURAL (básica)")
