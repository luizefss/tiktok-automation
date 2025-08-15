#!/usr/bin/env python3
"""
Teste rápido dos novos prompts simplificados
"""

import sys
import os
sys.path.append('/var/www/tiktok-automation/backend')

from humanized_prompts import HumanizedPrompts

def test_prompts():
    """Testa os novos prompts"""
    prompts = HumanizedPrompts()
    theme = "telescópios espaciais"
    
    print("🧪 Testando novos prompts simplificados...")
    print("=" * 60)
    
    # Teste Gemini
    print("\n🔹 GEMINI PROMPT:")
    gemini_prompt = prompts.get_gemini_humanized_prompt(theme)
    print(gemini_prompt[:300] + "...")
    
    print("\n" + "-" * 40)
    
    # Teste Claude  
    print("\n🔹 CLAUDE PROMPT:")
    claude_prompt = prompts.get_claude_humanized_prompt(theme)
    print(claude_prompt[:300] + "...")
    
    print("\n" + "-" * 40)
    
    # Teste GPT
    print("\n🔹 GPT PROMPT:")
    gpt_prompt = prompts.get_gpt_humanized_prompt(theme)
    print(gpt_prompt[:300] + "...")
    
    print("\n" + "=" * 60)
    print("✅ Prompts simplificados testados!")
    print("🎯 Agora devem gerar conteúdo mais sério e educativo")

if __name__ == "__main__":
    test_prompts()
