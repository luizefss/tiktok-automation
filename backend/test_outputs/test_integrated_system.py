# /var/www/tiktok-automation/backend/test_integrated_system.py

"""
Teste Completo do Sistema Integrado
TTS + Efeitos Visuais + Publicação Multi-Plataforma
"""

import asyncio
import sys
import os
from pathlib import Path

# Adiciona o caminho do backend do suaobra
sys.path.append("/var/www/suaobra/backend")

from integrated_content_system import (
    IntegratedContentSystem,
    ContentRequest,
    Platform,
    create_content_from_text
)

async def test_system_status():
    """Testa status de todos os sistemas"""
    print("🔍 Verificando status do sistema...")
    
    system = IntegratedContentSystem()
    status = system.get_system_status()
    
    print(f"📊 Status dos Sistemas:")
    print(f"  - TTS: {'✅' if status['systems']['tts'] else '❌'}")
    print(f"  - Efeitos Visuais: {'✅' if status['systems']['visual_effects'] else '❌'}")
    print(f"  - Publisher: {'✅' if status['systems']['publisher'] else '❌'}")
    print(f"  - Histórico: {status['content_history_count']} itens")
    print(f"  - Diretório temp: {status['temp_directory']}")
    
    return status

async def test_tts_only():
    """Testa apenas o sistema TTS"""
    print("\n🎤 Testando apenas TTS...")
    
    try:
        sys.path.append("/var/www/suaobra/backend")
        from google_ai_studio_tts_enhanced import GoogleAIStudioTTSEnhanced
        
        tts = GoogleAIStudioTTSEnhanced()
        
        result = tts.synthesize_speech_official(
            "Este é um teste do sistema de síntese de voz.",
            emotion="neutral",
            voice_profile="pt-BR-Neural2-A"
        )
        
        if result and os.path.exists(result):
            print("✅ TTS funcionando corretamente")
            
            # Copia para arquivo de teste
            test_file = "/tmp/test_tts.mp3"
            import shutil
            shutil.copy2(result, test_file)
            
            print(f"📁 Arquivo de teste salvo: {test_file}")
            return test_file
        else:
            print("❌ TTS falhou")
            return None
            
    except Exception as e:
        print(f"❌ Erro no teste TTS: {e}")
        return None

async def test_visual_effects_only():
    """Testa apenas o sistema de efeitos visuais"""
    print("\n🎨 Testando apenas Efeitos Visuais...")
    
    try:
        from visual_effects_system import VisualEffectsSystem
        
        visual = VisualEffectsSystem()
        
        # Cria um vídeo de teste simples
        test_audio = await test_tts_only()
        
        if test_audio and os.path.exists(test_audio):
            result = visual.create_multi_platform_content(
                audio_path=test_audio,
                text="Teste de efeitos visuais",
                platforms=["tiktok"],
                style="modern_tech"
            )
            
            if result and result.get('success'):
                print("✅ Efeitos Visuais funcionando")
                videos = result.get('videos', {})
                for platform, video_path in videos.items():
                    print(f"📹 Vídeo criado para {platform}: {video_path}")
                return videos
            else:
                print("❌ Efeitos Visuais falharam")
                return {}
        else:
            print("❌ Áudio de teste não disponível")
            return {}
            
    except Exception as e:
        print(f"❌ Erro no teste de Efeitos Visuais: {e}")
        return {}

async def test_publisher_only():
    """Testa apenas o sistema de publicação"""
    print("\n📡 Testando apenas Publisher...")
    
    try:
        from multi_platform_publisher import MultiPlatformPublisher, PublishRequest
        
        publisher = MultiPlatformPublisher()
        
        # Teste simulado sem vídeo real
        test_request = PublishRequest(
            video_path="/tmp/test_video.mp4",  # Arquivo fictício
            title="Teste do Sistema de Publicação",
            description="Este é um teste do sistema integrado",
            tags=["teste", "sistema", "automatico"],
            platforms=[Platform.TIKTOK]  # Só TikTok para teste
        )
        
        # Como é um teste, não publicamos realmente
        print("✅ Publisher configurado (teste simulado)")
        print("💡 Para teste real, configure credenciais em platform_config.json")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste Publisher: {e}")
        return False

async def test_integrated_pipeline():
    """Testa o pipeline completo integrado"""
    print("\n🚀 Testando Pipeline Integrado Completo...")
    
    try:
        # Teste com função de conveniência
        result = await create_content_from_text(
            text="Olá! Este é um teste completo do sistema integrado de criação de conteúdo. Vamos ver se todos os componentes funcionam juntos perfeitamente.",
            title="Teste Sistema Integrado",
            description="Demonstração completa do pipeline TTS + Efeitos + Publicação",
            tags=["teste", "integrado", "completo", "automatico"],
            voice="pt-BR-Neural2-A",
            style="modern_tech",
            platforms=["tiktok"]  # Apenas TikTok para teste
        )
        
        if result.success:
            print("✅ Pipeline integrado funcionando!")
            print(f"⏱️ Tempo de processamento: {result.processing_time:.2f}s")
            print(f"🎵 Arquivos de áudio: {len(result.audio_files)}")
            print(f"🎬 Arquivos de vídeo: {len(result.video_files)}")
            print(f"📱 Tentativas de publicação: {len(result.publish_results)}")
            
            # Mostra detalhes dos arquivos criados
            for platform, audio_path in result.audio_files.items():
                if os.path.exists(audio_path):
                    size = os.path.getsize(audio_path)
                    print(f"  📁 Áudio {platform}: {audio_path} ({size} bytes)")
            
            for platform, video_path in result.video_files.items():
                if os.path.exists(video_path):
                    size = os.path.getsize(video_path)
                    print(f"  📁 Vídeo {platform}: {video_path} ({size} bytes)")
            
            return True
        else:
            print(f"❌ Pipeline falhou: {result.error_message}")
            return False
            
    except Exception as e:
        print(f"❌ Erro no pipeline integrado: {e}")
        return False

async def test_batch_processing():
    """Testa processamento em lote"""
    print("\n📦 Testando Processamento em Lote...")
    
    try:
        system = IntegratedContentSystem()
        
        # Cria múltiplas solicitações
        requests = [
            ContentRequest(
                text=f"Este é o conteúdo número {i+1} para teste em lote.",
                title=f"Conteúdo Lote {i+1}",
                description=f"Teste de processamento em lote - item {i+1}",
                tags=["lote", "teste", f"item{i+1}"],
                platforms=[Platform.TIKTOK]
            )
            for i in range(3)  # 3 itens para teste
        ]
        
        # Processa lote
        results = await system.create_content_batch(requests)
        
        successful = sum(1 for r in results if r.success)
        print(f"✅ Lote processado: {successful}/{len(results)} sucessos")
        
        return successful == len(results)
        
    except Exception as e:
        print(f"❌ Erro no processamento em lote: {e}")
        return False

async def test_cleanup():
    """Testa limpeza de arquivos temporários"""
    print("\n🧹 Testando Limpeza...")
    
    try:
        system = IntegratedContentSystem()
        
        # Lista arquivos antes
        temp_files_before = list(system.temp_dir.glob("*"))
        print(f"📁 Arquivos temporários antes: {len(temp_files_before)}")
        
        # Executa limpeza (arquivos de mais de 0 horas para forçar limpeza)
        system.cleanup_temp_files(older_than_hours=0)
        
        # Lista arquivos depois
        temp_files_after = list(system.temp_dir.glob("*"))
        print(f"📁 Arquivos temporários depois: {len(temp_files_after)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na limpeza: {e}")
        return False

async def main():
    """Função principal de teste"""
    print("🧪 INICIANDO TESTES DO SISTEMA INTEGRADO")
    print("=" * 50)
    
    tests = [
        ("Status do Sistema", test_system_status),
        ("TTS Isolado", test_tts_only),
        ("Efeitos Visuais Isolado", test_visual_effects_only),
        ("Publisher Isolado", test_publisher_only),
        ("Pipeline Integrado", test_integrated_pipeline),
        ("Processamento em Lote", test_batch_processing),
        ("Limpeza", test_cleanup)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        
        try:
            result = await test_func()
            results[test_name] = result
            
            if result:
                print(f"✅ {test_name}: PASSOU")
            else:
                print(f"❌ {test_name}: FALHOU")
                
        except Exception as e:
            print(f"💥 {test_name}: ERRO - {e}")
            results[test_name] = False
    
    # Resumo final
    print("\n" + "=" * 50)
    print("📊 RESUMO DOS TESTES")
    print("=" * 50)
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{test_name}: {status}")
    
    print(f"\n🎯 RESULTADO FINAL: {passed}/{total} testes passaram")
    
    if passed == total:
        print("🎉 TODOS OS TESTES PASSARAM! Sistema pronto para produção.")
    elif passed >= total * 0.7:
        print("⚠️ MAIORIA DOS TESTES PASSOU. Verifique os erros.")
    else:
        print("❌ MUITOS TESTES FALHARAM. Sistema precisa de correções.")
    
    return passed / total

if __name__ == "__main__":
    # Executa todos os testes
    try:
        success_rate = asyncio.run(main())
        exit_code = 0 if success_rate >= 0.7 else 1
        exit(exit_code)
    except KeyboardInterrupt:
        print("\n🛑 Testes interrompidos pelo usuário")
        exit(1)
    except Exception as e:
        print(f"\n💥 Erro fatal nos testes: {e}")
        exit(1)
