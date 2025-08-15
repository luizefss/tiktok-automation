#!/usr/bin/env python3
"""
Teste que replica exatamente a lógica da API
"""

import asyncio
import json
from ai_orchestrator import AIOrchestrator

def test_api_logic():
    """Testa exatamente como a API"""
    
    # Simular dados da API
    data = {
        'theme': 'A descoberta revolucionária dos telescópios',
        'ai_provider': 'gemini', 
        'story_type': 'historica'
    }
    
    theme = data.get('theme')
    ai_provider = data.get('ai_provider')
    story_type = data.get('story_type', 'curiosidade')
    
    print(f"🔍 API Logic - Theme: {theme}")
    print(f"🔍 API Logic - AI: {ai_provider}")
    print(f"🔍 API Logic - Story Type: {story_type}")
    print("=" * 60)
    
    # Instanciar como na API (global)
    ai_orchestrator = AIOrchestrator()
    
    # Loop como na API
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(ai_orchestrator.generate_script(
            theme=theme,
            ai_provider=ai_provider,
            video_style=data.get('video_style'),
            story_type=story_type
        ))
        
        print(f"🔍 API Logic - Result success: {result.get('success')}")
        print(f"🔍 API Logic - Result keys: {list(result.keys())}")
        
        if result.get('success'):
            script_data = result['script_data']
            print(f"🔍 API Logic - Script data keys: {list(script_data.keys())}")
            print(f"🔍 API Logic - Roteiro chars: {len(script_data.get('roteiro_completo', ''))}")
            print(f"🔍 API Logic - Visual prompts: {len(script_data.get('visual_prompts', []))}")
            print(f"🔍 API Logic - Leonardo prompts: {len(script_data.get('leonardo_prompts', []))}")
            print(f"🔍 API Logic - AI provider: {script_data.get('ai_provider', 'N/A')}")
            
            # Mostrar conteúdo
            print("\n📝 Roteiro:")
            print(script_data.get('roteiro_completo', 'VAZIO')[:200] + "...")
            
            print("\n🎨 Visual Prompts:")
            visual_prompts = script_data.get('visual_prompts', [])
            if visual_prompts:
                print(json.dumps(visual_prompts[0], indent=2, ensure_ascii=False))
            else:
                print("VAZIO")
                
        else:
            print(f"❌ Error: {result.get('error')}")
            
    finally:
        loop.close()

if __name__ == "__main__":
    test_api_logic()
