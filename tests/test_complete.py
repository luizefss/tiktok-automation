# /var/www/tiktok-automation/backend/test_complete.py

"""
Script de teste do pipeline completo
"""
import os
from dotenv import load_dotenv
from complete_pipeline import CompletePipeline
import json

# Carregar variáveis de ambiente
load_dotenv()

def test_pipeline():
    """
    Testa o pipeline completo
    """
    print("\n" + "="*60)
    print("🚀 TESTE DO PIPELINE COMPLETO DE GERAÇÃO DE VÍDEO")
    print("="*60 + "\n")
    
    # Verificar APIs disponíveis
    print("📋 Verificando APIs...")
    apis_status = {
        'Gemini': bool(os.getenv('GEMINI_API_KEY')),
        'Claude': bool(os.getenv('CLAUDE_API_KEY')),
        'GPT': bool(os.getenv('OPENAI_API_KEY')),
        'Google AI Studio': bool(os.getenv('GOOGLE_AI_STUDIO_API_KEY')),
        'YouTube': bool(os.getenv('YOUTUBE_API_KEY'))
    }
    
    for api, status in apis_status.items():
        print(f"  {api}: {'✅ Configurada' if status else '❌ Não configurada'}")
    
    print("\n" + "-"*60 + "\n")
    
    # Criar pipeline
    pipeline = CompletePipeline()
    
    # Testar geração
    print("🎬 Gerando vídeo de teste...")
    print("  Tema: Os mistérios do Triângulo das Bermudas")
    print("  Duração: 60 segundos")
    print("  Tipo: Mistério")
    print("\n" + "-"*60 + "\n")
    
    result = pipeline.generate_complete_video(
        topic="os mistérios do triângulo das bermudas",
        duration=60,
        content_type="mystery",
        voice_emotion="mysterious",
        add_subtitles=True,
        add_music=True
    )
    
    # Exibir resultados
    print("\n" + "="*60)
    print("📊 RESULTADO DO TESTE")
    print("="*60 + "\n")
    
    print(f"Status: {result['status']}")
    
    if result['status'] == 'completo':
        print("\n✅ VÍDEO GERADO COM SUCESSO!")
        print(f"\n📁 Arquivos gerados:")
        for file_type, path in result.get('files', {}).items():
            print(f"  {file_type}: {path}")
        
        print(f"\n📊 Detalhes dos passos:")
        for step, details in result.get('steps', {}).items():
            print(f"\n  {step.upper()}:")
            for key, value in details.items():
                if key != 'paths':  # Não imprimir lista de paths
                    print(f"    {key}: {value}")
    else:
        print(f"\n❌ ERRO: {result.get('error', 'Erro desconhecido')}")
    
    print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    test_pipeline()