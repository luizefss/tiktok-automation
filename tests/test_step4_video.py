# /var/www/tiktok-automation/backend/test_step4_video.py
import os
import json
from dotenv import load_dotenv
from ai_orchestrator import AIOrchestrator
from advanced_tts import AdvancedTTS
from vertex_image_generator import VertexImageGenerator
# Certifique-se de ter este arquivo criado
from video_builder import VideoBuilder

# Carregar variáveis de ambiente
load_dotenv()


def test_video_builder():
    """Testa a montagem de um vídeo completo."""
    print("\n" + "="*60)
    print("🎬 TESTE PASSO 4: MONTAGEM DO VÍDEO")
    print("="*60 + "\n")

    try:
        # Gerar roteiro (FASE 1)
        ai = AIOrchestrator()
        script = ai.generate_script(
            topic="os mistérios do triângulo das bermudas", duration=30)

        # Salvar roteiro para uso posterior
        with open("./test_outputs/video_script.json", 'w', encoding='utf-8') as f:
            json.dump(script, f, ensure_ascii=False, indent=2)

        # Gerar áudio (FASE 2)
        tts = AdvancedTTS()
        audio_path = "./test_outputs/video_audio.mp3"
        tts.generate_speech(script['full_text'],
                            audio_path, emotion="mysterious")

        # Gerar imagens (FASE 3)
        image_gen = VertexImageGenerator()
        images = image_gen.generate_images(script, num_images=5)

        # Montar vídeo (FASE 4)
        video_builder = VideoBuilder()
        output_name = "teste_video_completo"
        video_path = video_builder.create_video(
            images,
            audio_path,
            script,
            output_name,
            add_subtitles=True,
            add_music=True
        )

        if video_path:
            print(f"✅ Vídeo gerado com sucesso: {video_path}")
            print("🎉 PASSO 4 CONCLUÍDO COM SUCESSO!")
        else:
            print("❌ Falha ao montar o vídeo.")

    except Exception as e:
        print(f"❌ Erro inesperado no pipeline: {e}")


if __name__ == "__main__":
    test_video_builder()
