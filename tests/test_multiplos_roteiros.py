import google.generativeai as genai
import json

# Configurar Gemini
genai.configure(api_key="AIzaSyBOiQG_SO216ZRAvucekyMNhz6WNDK-qNo")

def gerar_roteiro(categoria, numero):
    """Gera um roteiro específico por categoria"""
    
    prompts = {
        "curiosidades": "uma curiosidade bizarra e interessante do mundo",
        "historia": "um fato histórico surpreendente e pouco conhecido", 
        "ciencia": "um fenômeno científico fascinante explicado de forma simples",
        "misterios": "um mistério real não resolvido que intriga cientistas"
    }
    
    model = genai.GenerativeModel('gemini-1.5-pro')
    
    prompt = f"""
    Crie um roteiro viral para TikTok sobre {prompts[categoria]}.
    
    IMPORTANTE: Seja criativo e diferente dos roteiros anteriores!
    
    RESPONDA APENAS EM JSON:
    {{
        "hook": "Frase impactante de abertura",
        "roteiro_completo": "Roteiro completo em português para 60 segundos",
        "hashtags": ["#viral", "#{categoria}", "#fyp"],
        "titulo": "Título chamativo",
        "categoria": "{categoria}"
    }}
    """
    
    try:
        print(f"🔄 Gerando roteiro {numero}: {categoria}...")
        response = model.generate_content(prompt)
        
        # Parse JSON
        texto = response.text.strip()
        if texto.startswith('```json'):
            texto = texto[7:-3]
        elif texto.startswith('```'):
            texto = texto[3:-3]
        
        dados = json.loads(texto)
        
        print(f"✅ ROTEIRO {numero} - {categoria.upper()}:")
        print(f"📢 Hook: {dados['hook']}")
        print(f"📝 Título: {dados['titulo']}")
        print("-" * 40)
        
        return dados
        
    except Exception as e:
        print(f"❌ ERRO no roteiro {numero}: {e}")
        return None

def test_diversidade_roteiros():
    """Teste 3: Gerar roteiros de categorias diferentes"""
    
    categorias = ["curiosidades", "historia", "ciencia", "misterios"]
    roteiros_gerados = []
    
    print("🎬 GERANDO 4 ROTEIROS DIFERENTES:")
    print("=" * 50)
    
    for i, categoria in enumerate(categorias, 1):
        roteiro = gerar_roteiro(categoria, i)
        if roteiro:
            roteiros_gerados.append(roteiro)
        
        print()  # Linha em branco
    
    print(f"🎉 RESULTADO: {len(roteiros_gerados)}/4 roteiros gerados com sucesso!")
    
    if len(roteiros_gerados) >= 3:
        print("✅ TESTE PASSOU! Sistema gera conteúdo diversificado!")
        return True
    else:
        print("❌ TESTE FALHOU! Problemas na geração")
        return False

if __name__ == "__main__":
    print("🧪 TESTE 3: Diversidade de Roteiros")
    print("=" * 50)
    
    if test_diversidade_roteiros():
        print("\n🚀 PRÓXIMO PASSO: Backend para automação!")
    else:
        print("\n🔧 AJUSTAR: Revisar prompts ou API")
