import google.generativeai as genai
import json

# Configurar Gemini
genai.configure(api_key="AIzaSyBOiQG_SO216ZRAvucekyMNhz6WNDK-qNo")

def test_roteiro_viral():
    """Teste 2: Gerar roteiro viral para TikTok"""
    
    model = genai.GenerativeModel('gemini-1.5-pro')
    
    prompt = """
    Crie um roteiro viral para TikTok sobre uma curiosidade interessante do mundo.
    
    REQUISITOS:
    - Deve ter um HOOK impactante nos primeiros 3 segundos
    - Duração: máximo 60 segundos
    - Tom: entusiástico e envolvente
    - Público: brasileiro, jovem
    
    RESPONDA APENAS EM JSON VÁLIDO:
    {
        "hook": "Frase de abertura impactante",
        "roteiro_completo": "Roteiro completo em português",
        "hashtags": ["#viral", "#curiosidade", "#fyp"],
        "titulo": "Título chamativo",
        "categoria": "curiosidades"
    }
    """
    
    try:
        print("🔄 Gerando roteiro viral...")
        response = model.generate_content(prompt)
        
        print("✅ RESPOSTA RECEBIDA:")
        print("-" * 50)
        print(response.text)
        print("-" * 50)
        
        # Tentar parsear JSON
        texto = response.text.strip()
        if texto.startswith('```json'):
            texto = texto[7:-3]
        elif texto.startswith('```'):
            texto = texto[3:-3]
        
        dados = json.loads(texto)
        
        print("\n🎯 ROTEIRO GERADO:")
        print(f"📢 Hook: {dados['hook']}")
        print(f"📝 Título: {dados['titulo']}")
        print(f"🏷️ Hashtags: {dados['hashtags']}")
        print(f"📂 Categoria: {dados['categoria']}")
        
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ ERRO JSON: {e}")
        print("📋 Resposta bruta para debug:")
        print(response.text)
        return False
        
    except Exception as e:
        print(f"❌ ERRO GERAL: {e}")
        return False

if __name__ == "__main__":
    print("🧪 TESTE 2: Geração de Roteiros Virais")
    print("=" * 50)
    
    if test_roteiro_viral():
        print("\n🎉 TESTE 2 PASSOU! Gemini gera roteiros virais!")
        print("👉 Próximo: testar geração de múltiplos roteiros")
    else:
        print("\n💥 TESTE 2 FALHOU! Verificar prompt")
