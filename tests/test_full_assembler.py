# /var/www/tiktok-automation/backend/test_full_assembler.py

# Para acessar as configurações e diretórios
from config_manager import get_config
from video_assembler import VideoAssemblerImproved
from audio_generator import AudioGenerator
from image_generator import ImageGenerator
from enhanced_content_generator import EnhancedContentGenerator
import os
import sys
import json
import time

# Adiciona o diretório atual ao PATH para que as importações funcionem
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importa os módulos necessários


def run_full_assembler_test():
    print("🧪 TESTE COMPLETO DO VIDEO ASSEMBLER (Gerando todos os inputs)...")
    print("=" * 70)

    config = get_config()

    # --- 1. Geração de Roteiro (simulando EnhancedContentGenerator) ---
    print("\n📝 Etapa 1: Gerando roteiro de exemplo com EnhancedContentGenerator...")
    content_gen = EnhancedContentGenerator()

    # Usar configurações que forcem uma geração personalizada
    settings_content = {
        'content_type': 'custom_message',
        'custom_topics': ['Produtividade no Trabalho'],
        'message_categories': ['Conhecimento'],
        'tone': 'educational',
        # Mapeia para Rémy na TopMediaAI ou Puck na Google TTS
        'voice_emotion': 'enthusiastic'
    }

    roteiro_data = content_gen.gerar_conteudo_personalizado(settings_content)

    if not roteiro_data:
        print("❌ FALHA: Geração de roteiro. Não é possível continuar o teste.")
        return

    print("✅ Roteiro gerado com sucesso!")
    print(f"Título: {roteiro_data.get('titulo', 'N/A')}")
    print(
        f"Roteiro completo (trecho): {roteiro_data.get('roteiro_completo', '')[:100]}...")

    # --- 2. Geração de Áudio (simulando AudioGenerator) ---
    print("\n🎵 Etapa 2: Gerando áudio de exemplo com AudioGenerator...")
    audio_gen = AudioGenerator()

    # Decida qual API de áudio usar para o teste (True para TopMediaAI, False para Google TTS)
    # Recomendo True se você quer testar Rémy, mas False se a TopMediaAI estiver com erro 500
    # <<<<<<<<<<< AJUSTE AQUI SE QUISER USAR TOPMEDIAAI >>>>>>>>>
    USE_TOPMEDIA_AI_FOR_TEST = False

    audio_file_path = audio_gen.roteiro_para_audio(
        roteiro_data,
        voice_settings={'voice_emotion': settings_content['voice_emotion'],
                        'speaking_rate': settings_content.get('speaking_speed', 1.05)},
        use_topmedia_ai=USE_TOPMEDIA_AI_FOR_TEST
    )

    if not audio_file_path:
        print("❌ FALHA: Geração de áudio. Não é possível continuar o teste.")
        return

    print(f"✅ Áudio gerado com sucesso: {audio_file_path}")

    # --- 3. Geração de Imagens (simulando ImageGenerator) ---
    print("\n🖼️ Etapa 3: Gerando imagens de exemplo com ImageGenerator...")
    image_gen = ImageGenerator()

    style_settings_images = {
        # Usar estilo do settings do frontend
        'image_style': settings_content.get('image_style', 'cinematic'),
        # Usar paleta do settings do frontend
        'color_palette': settings_content.get('color_palette', 'vibrant')
    }

    images_data_list = image_gen.gerar_imagens_para_roteiro(
        roteiro_data, style_settings=style_settings_images
    )

    if not images_data_list or len(images_data_list) < 1:
        print("❌ FALHA: Geração de imagens. Nenhuma imagem válida para continuar o teste.")
        return

    print(f"✅ {len(images_data_list)} imagens geradas com sucesso.")
    for img_info in images_data_list:
        print(f"  - {img_info.get('file', 'N/A')}")

    # --- 4. Montagem do Vídeo (VideoAssemblerImproved) ---
    print("\n🎬 Etapa 4: Montando o vídeo com VideoAssemblerImproved...")
    assembler = VideoAssemblerImproved()

    # A função criar_video_completo espera o roteiro_data (para metadados), o audio_file e images_list
    video_result = assembler.criar_video_completo(
        roteiro_data,  # Dicionário completo do roteiro
        audio_file_path,  # Caminho do arquivo de áudio
        images_data_list  # Lista de dicionários de imagem
    )

    if video_result and video_result.get('success'):
        print("\n🎉 SUCESSO: Vídeo gerado e montado!")
        print(f"Caminho do Vídeo: {video_result['video_file']}")
        print(f"Tamanho: {video_result['size_mb']:.2f} MB")
        print(f"Duração: {video_result['duration']:.2f} segundos")
        # Você pode abrir o arquivo de vídeo para verificar
    else:
        print("\n❌ FALHA: O Vídeo NÃO foi montado.")
        print(
            f"Detalhes: {video_result.get('error', 'N/A') if video_result else 'Resultado vazio ou sem sucesso'}")
        print("Verifique os logs do FFmpeg (video_assembler.log) para mais detalhes sobre a falha na montagem.")


if __name__ == "__main__":
    run_full_assembler_test()
