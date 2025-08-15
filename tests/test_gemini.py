#/var/www/tiktok-automation/tests/test_gemini.py

import google.generativeai as genai

# Sua API key
genai.configure(api_key="AIzaSyBOiQG_SO216ZRAvucekyMNhz6WNDK-qNo")

def test_gemini_connection():
    """Teste 1: Verificar se API key funciona"""
    try:
        model = genai.GenerativeModel('gemini-1.5-pro')
        response = model.generate_content("Responda apenas: API funcionando!")
        print("✅ GEMINI CONECTADO:")
        print(response.text)
        return True
    except Exception as e:
        print(f"❌ ERRO CONEXÃO: {e}")
        return False

if __name__ == "__main__":
    print("🧪 TESTE 1: Conexão Gemini")
    print("=" * 40)
    
    if test_gemini_connection():
        print("\n🎉 TESTE PASSOU! Próximo: roteiros")
    else:
        print("\n💥 TESTE FALHOU! Verificar API key")
