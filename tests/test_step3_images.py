# /var/www/tiktok-automation/backend/test_step3_images.py
import json
import os
from dotenv import load_dotenv
from vertex_image_generator import VertexImageGenerator

# Carregar variáveis de ambiente
load_dotenv()


def test_image_generator():
    """Testa a geração de imagens a partir de um roteiro JSON."""
    print("\n" + "="*60)
    print("🎨 TESTE PASSO 3: GERAÇÃO DE IMAGENS")
    print("="*60 + "\n")

    script_path = "./test_outputs/test_script.json"

    try:
        # Carregar roteiro do arquivo JSON
        with open(script_path, 'r', encoding='utf-8') as f:
            script_data = json.load(f)

        # Inicializar o gerador de imagens
        image_gen = VertexImageGenerator()

        # Gerar imagens
        images = image_gen.generate_images(script_data, num_images=5)

        if images:
            print(f"✅ {len(images)} imagens geradas com sucesso!")
            print("🎉 PASSO 3 CONCLUÍDO COM SUCESSO!")
            print(f"Verifique as imagens em: {os.path.dirname(images[0])}")
        else:
            print("❌ Falha ao gerar as imagens.")

    except FileNotFoundError:
        print(
            f"❌ Erro: O arquivo de roteiro '{script_path}' não foi encontrado.")
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")


if __name__ == "__main__":
    test_image_generator()
