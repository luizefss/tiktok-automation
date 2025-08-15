import requests
import base64
import re
from datetime import datetime
import os

# Sua API Key (recomendo regenerar depois)
API_KEY = "sk-vmr0W2JIkYT8kUf5569bE596Ae854fF5B82c3dCcE7Ac5eE6"

# Endpoint correto
url = "https://api.laozhang.ai/v1/chat/completions"

# Prompt de teste
prompt = "17th-century study room, wooden desk by a window, sunlight beam entering, Isaac Newton holding a glass prism, dust motes in the air, cinematic lighting, moody shadows, painterly realistic, rich textures, vertical 9:16, no text, highly detailed, 8K resolution"

# Payload seguindo formato do Lao Zhang
payload = {
    "model": "sora-image",
    "stream": False,
    "messages": [
        {"role": "user", "content": prompt}
    ]
}

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# Fazendo requisição
response = requests.post(url, headers=headers, json=payload)

# Pasta de saída com data
output_dir = datetime.now().strftime("imagens_sora/%Y-%m-%d")
os.makedirs(output_dir, exist_ok=True)

if response.status_code == 200:
    data = response.json()
    content = data["choices"][0]["message"]["content"]

    # Se vier link no retorno
    match = re.search(r'(https?://\S+)', content)
    if match:
        img_url = match.group(1)
        img_data = requests.get(img_url).content
        file_path = os.path.join(output_dir, "teste_sora.png")
        with open(file_path, "wb") as f:
            f.write(img_data)
        print(f"✅ Imagem salva como {file_path} (via URL)")
    else:
        # Se vier em base64
        try:
            img_bytes = base64.b64decode(content)
            file_path = os.path.join(output_dir, "teste_sora.png")
            with open(file_path, "wb") as f:
                f.write(img_bytes)
            print(f"✅ Imagem salva como {file_path} (via base64)")
        except Exception as e:
            print("⚠ Conteúdo retornado não é imagem:", content)
else:
    print("❌ Erro:", response.status_code, response.text)
