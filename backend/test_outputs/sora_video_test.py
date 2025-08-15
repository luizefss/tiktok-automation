import requests
import re
import os
from datetime import datetime

# Sua API Key
API_KEY = "sk-vmr0W2JIkYT8kUf5569bE596Ae854fF5B82c3dCcE7Ac5eE6"

# Endpoint
url = "https://api.laozhang.ai/v1/chat/completions"

# Prompt detalhado
prompt = (
    "A funny animated 10-second video of a cartoon dog wearing sunglasses, "
    "dancing and wagging its tail in a park, bright sunny day, smooth animation, "
    "vibrant colors, high quality"
)

# Payload
payload = {
    "model": "sora-video",
    "duration": 0.2,
    "stream": False,
    "messages": [
        {"role": "user", "content": prompt}
    ]
}

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# Requisição
response = requests.post(url, headers=headers, json=payload)

# Pasta de saída
output_dir = datetime.now().strftime("videos_sora/%Y-%m-%d")
os.makedirs(output_dir, exist_ok=True)

if response.status_code == 200:
    data = response.json()
    content = data["choices"][0]["message"]["content"]

    # Extrair URL
    match = re.search(r'(https?://\S+)', content)
    if match:
        video_url = match.group(1)
        video_data = requests.get(video_url).content
        file_path = os.path.join(output_dir, "cachorro_engracado.mp4")
        with open(file_path, "wb") as f:
            f.write(video_data)
        print(f"✅ Vídeo salvo como {file_path}")
        print(f"🔗 URL do vídeo: {video_url}")
    else:
        print("⚠ Nenhum link de vídeo encontrado no retorno:", content)
else:
    print("❌ Erro:", response.status_code, response.text)
