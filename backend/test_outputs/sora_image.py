import requests
import base64

# 🔹 Coloque aqui sua API KEY do Lao Zhang
API_KEY = "02f7602530ec4035be7f1c8c7231b762"

# 🔹 Prompt para gerar a imagem
prompt = "17th-century study room, wooden desk by a window, sunlight beam entering, Isaac Newton holding a glass prism, dust motes in the air, cinematic lighting, moody shadows, painterly realistic, rich textures, vertical 9:16, no text, highly detailed, 8K resolution"

# Endpoint da API
url = "https://api.laozhang.ai/v1/images/generations"

payload = {
    "model": "sora_image",  # Modelo escolhido
    "prompt": prompt,
    "size": "1024x1024",
    "n": 1  # Quantidade de imagens
}

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# Fazendo a requisição
response = requests.post(url, json=payload, headers=headers)

# Verificando resultado
if response.status_code == 200:
    data = response.json()
    image_base64 = data["data"][0]["b64_json"]
    image_bytes = base64.b64decode(image_base64)

    # Salvando no VPS
    with open("teste_sora.png", "wb") as f:
        f.write(image_bytes)

    print("✅ Imagem salva como teste_sora.png")
else:
    print("❌ Erro:", response.status_code, response.text)
