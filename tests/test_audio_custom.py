# /var/www/tiktok-automation/backend/test_audio_custom.py
import os
from dotenv import load_dotenv
from advanced_tts import AdvancedTTS

# Carregar variáveis de ambiente
load_dotenv()


def test_tts_generator():
    """Testa a geração de áudio a partir de um texto personalizado."""
    print("\n" + "="*60)
    print("🎙️ TESTE DE ÁUDIO CUSTOMIZADO")
    print("="*60 + "\n")

    audio_output_path = "./test_outputs/test_audio_custom.mp3"

    # TEXTO PERSONALIZADO PARA TESTE DE VOZ DE 15 SEGUNDOS
    texto_de_teste = "O que realmente se esconde... na escuridão do nosso universo? As estrelas... guardam segredos milenares. E se a verdade... fosse mais aterrorizante do que a gente imagina?"

    # EMOÇÃO A SER TESTADA
    emocao_teste = "mysterious"

    try:
        tts_gen = AdvancedTTS()
        output_file = tts_gen.generate_speech(
            texto_de_teste, audio_output_path, emotion=emocao_teste)

        if output_file:
            print(f"✅ Áudio gerado e salvo em: {output_file}")
            print(f"Texto utilizado: '{texto_de_teste}'")
            print("🎉 TESTE DE ÁUDIO CONCLUÍDO COM SUCESSO!")
        else:
            print("❌ Falha ao gerar o áudio.")

    except Exception as e:
        print(f"❌ Erro inesperado: {e}")


if __name__ == "__main__":
    test_tts_generator()
