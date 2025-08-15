#!/usr/bin/env python3
"""
Teste para verificar se os prompts visuais estão sendo gerados corretamente
"""

import asyncio
import json
from ai_orchestrator import AIOrchestrator

async def test_visual_prompts():
    """Testa se todas as IAs geram prompts visuais e Leonardo AI"""
    orchestrator = AIOrchestrator()
    
    theme = "A história fascinante dos telescópios"
    story_type = "historica"
    
    print("🧪 Testando geração de prompts visuais...")
    print(f"📖 Tema: {theme}")
    print(f"🎭 Tipo: {story_type}")
    print("=" * 60)
    
    # Testar cada IA
    providers = ["gemini", "claude", "gpt"]
    
    for provider in providers:
        print(f"\n🤖 Testando {provider.upper()}...")
        print("-" * 40)
        
        try:
            result = await orchestrator.generate_script(
                theme=theme,
                ai_provider=provider,
                story_type=story_type
            )
            
            if result.get('success'):
                script_data = result['script_data']
                
                # Verificar se tem roteiro
                roteiro = script_data.get('roteiro_completo', '')
                print(f"📝 Roteiro: {'✅ Gerado' if roteiro else '❌ Faltando'} ({len(roteiro)} chars)")
                
                # Verificar se tem prompts visuais
                visual_prompts = script_data.get('visual_prompts', [])
                print(f"🎨 Prompts Visuais: {'✅ Gerados' if visual_prompts else '❌ Faltando'} ({len(visual_prompts)} cenas)")
                
                # Verificar se tem prompts Leonardo AI
                leonardo_prompts = script_data.get('leonardo_prompts', [])
                print(f"🎬 Leonardo AI: {'✅ Gerados' if leonardo_prompts else '❌ Faltando'} ({len(leonardo_prompts)} animações)")
                
                # Verificar timing
                if visual_prompts:
                    first_scene = visual_prompts[0]
                    has_timing = 'timing' in first_scene or 'start_time' in first_scene
                    print(f"⏰ Timing: {'✅ Incluído' if has_timing else '❌ Faltando'}")
                    
                    # Mostrar exemplo de cena
                    print(f"\n📄 Exemplo da primeira cena:")
                    print(json.dumps(first_scene, indent=2, ensure_ascii=False)[:200] + "...")
                
            else:
                print(f"❌ Erro: {result.get('error', 'Desconhecido')}")
                
        except Exception as e:
            print(f"❌ Exceção: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Teste concluído!")

if __name__ == "__main__":
    asyncio.run(test_visual_prompts())
