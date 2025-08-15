#!/usr/bin/env python3
"""
Teste isolado para Imagen 3 - Google AI
"""

import os
import sys
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

def test_imagen3():
    """Testa a geração de imagem com Imagen 3"""
    print("🧪 Iniciando teste do Imagen 3...")
    
    # Verificar se as credenciais estão disponíveis
    google_ai_key = os.getenv('GOOGLE_AI_STUDIO_API_KEY')
    vertex_ai_project = os.getenv('VERTEX_AI_PROJECT_ID')
    
    print(f"📋 Google AI Studio API Key: {'✅ Disponível' if google_ai_key else '❌ Não encontrada'}")
    print(f"📋 Vertex AI Project ID: {'✅ Disponível' if vertex_ai_project else '❌ Não encontrado'}")
    
    if not google_ai_key and not vertex_ai_project:
        print("❌ Nenhuma credencial encontrada para Imagen 3")
        return False
    
    try:
        # Tentar importar o serviço de imagem
        from services.image_generator import ImageGeneratorService
        
        print("📦 Inicializando Image Generator Service...")
        service = ImageGeneratorService()
        
        # Prompt de teste
        test_prompt = "Um gato fofo brincando com uma bola de lã, estilo cartoon, cores vibrantes"
        
        print(f"🎨 Testando geração com prompt: '{test_prompt}'")
        
        # Gerar imagem
        result = service.generate_image(
            prompt=test_prompt,
            style="cartoon",
            aspect_ratio="1:1"
        )
        
        if result and result.get('success'):
            print("✅ Imagen 3 funcionando perfeitamente!")
            print(f"📸 Imagem gerada: {result.get('image_path', 'N/A')}")
            print(f"🔗 URL: {result.get('image_url', 'N/A')}")
            return True
        else:
            print("❌ Falha na geração da imagem")
            print(f"📄 Detalhes: {result}")
            return False
            
    except ImportError as e:
        print(f"❌ Erro de importação: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        return False

def test_vertex_ai_connection():
    """Testa especificamente a conexão com Vertex AI"""
    print("\n🔗 Testando conexão com Vertex AI...")
    
    try:
        from google.cloud import aiplatform
        
        project_id = os.getenv('VERTEX_AI_PROJECT_ID')
        location = os.getenv('VERTEX_AI_LOCATION', 'us-central1')
        
        if not project_id:
            print("❌ VERTEX_AI_PROJECT_ID não configurado")
            return False
            
        print(f"📋 Project ID: {project_id}")
        print(f"📋 Location: {location}")
        
        # Inicializar Vertex AI
        aiplatform.init(project=project_id, location=location)
        
        print("✅ Vertex AI inicializado com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro na conexão com Vertex AI: {e}")
        return False

def test_google_ai_studio():
    """Testa especificamente o Google AI Studio"""
    print("\n🔗 Testando Google AI Studio...")
    
    try:
        import google.generativeai as genai
        
        api_key = os.getenv('GOOGLE_AI_STUDIO_API_KEY')
        
        if not api_key:
            print("❌ GOOGLE_AI_STUDIO_API_KEY não configurada")
            return False
            
        # Configurar API
        genai.configure(api_key=api_key)
        
        # Listar modelos disponíveis
        models = list(genai.list_models())
        
        print(f"✅ Google AI Studio conectado!")
        print(f"📋 {len(models)} modelos disponíveis")
        
        # Procurar por modelos de imagem
        imagen_models = [m for m in models if 'imagen' in m.name.lower()]
        
        if imagen_models:
            print(f"🎨 Modelos Imagen encontrados:")
            for model in imagen_models:
                print(f"   - {model.name}")
        else:
            print("ℹ️ Nenhum modelo Imagen encontrado na lista")
            
        return True
        
    except Exception as e:
        print(f"❌ Erro na conexão com Google AI Studio: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Teste Imagen 3 - TikTok Automation")
    print("=" * 50)
    
    # Verificar environment
    print(f"📁 Diretório atual: {os.getcwd()}")
    print(f"🐍 Python: {sys.version}")
    
    # Executar testes
    vertex_ok = test_vertex_ai_connection()
    studio_ok = test_google_ai_studio()
    
    print("\n" + "=" * 50)
    
    if vertex_ok or studio_ok:
        print("✅ Pelo menos uma API está funcionando, testando geração...")
        success = test_imagen3()
        
        if success:
            print("🎉 TESTE CONCLUÍDO COM SUCESSO!")
        else:
            print("⚠️ Teste de geração falhou")
    else:
        print("❌ Nenhuma API está funcionando")
    
    print("=" * 50)
