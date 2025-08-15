#!/usr/bin/env python3
"""
Teste completo do Step 3 - Geração de imagens com cache
"""

import requests
import json
import time
from datetime import datetime

# Configurações
BASE_URL = "http://localhost:6000/api"

def test_image_generation():
    """Testa a geração de imagens com cache"""
    print("🧪 Testando geração de imagens com cache - Step 3")
    print("=" * 60)
    
    # Script de exemplo para teste
    test_script = {
        "title": "O Mistério do Gato Desaparecido",
        "script_data": {
            "organized_script": [
                {
                    "timestamp": "00:00-00:03",
                    "text": "Era uma noite escura e misteriosa na cidade...",
                    "visual_cue": "Uma cidade escura à noite com luzes amareladas",
                    "audio_note": "Som ambiente urbano noturno"
                },
                {
                    "timestamp": "00:03-00:06", 
                    "text": "Quando um gato preto desapareceu misteriosamente...",
                    "visual_cue": "Um gato preto caminhando em um beco sombrio",
                    "audio_note": "Miado distante e eco"
                },
                {
                    "timestamp": "00:06-00:09",
                    "text": "Deixando apenas pegadas misteriosas para trás...",
                    "visual_cue": "Pegadas de gato na neve ou poeira sob a luz da lua",
                    "audio_note": "Vento suave"
                }
            ],
            "visual_cues": [
                "Uma cidade escura à noite com luzes amareladas",
                "Um gato preto caminhando em um beco sombrio", 
                "Pegadas de gato na neve ou poeira sob a luz da lua"
            ]
        },
        "visual_style": "misterio"
    }
    
    print("📋 Script de teste:")
    print(f"   Título: {test_script['title']}")
    print(f"   Estilo: {test_script['visual_style']}")
    print(f"   Cenas: {len(test_script['script_data']['visual_cues'])}")
    print()
    
    # Verificar cache inicial
    print("🔍 Verificando cache inicial...")
    cache_response = requests.get(f"{BASE_URL}/production/image-cache")
    if cache_response.status_code == 200:
        cache_data = cache_response.json()
        print(f"   Cache inicial: {cache_data['cache_count']} entradas")
    else:
        print(f"   ❌ Erro ao verificar cache: {cache_response.status_code}")
    print()
    
    # Primeira geração (deve criar cache)
    print("🎨 Primeira geração de imagens (criando cache)...")
    start_time = time.time()
    
    response1 = requests.post(
        f"{BASE_URL}/production/generate-images",
        json=test_script,
        headers={"Content-Type": "application/json"}
    )
    
    generation_time_1 = time.time() - start_time
    
    if response1.status_code == 200:
        result1 = response1.json()
        print(f"   ✅ Sucesso! {len(result1.get('generated_images', []))} imagens geradas")
        print(f"   ⏱️ Tempo: {generation_time_1:.2f}s")
        print(f"   💾 Cache ID: {result1.get('cache_id', 'N/A')}")
        
        # Mostrar detalhes das imagens
        if 'generated_images' in result1:
            for i, img in enumerate(result1['generated_images']):
                print(f"      Imagem {i+1}: {img.get('filename', 'N/A')}")
    else:
        print(f"   ❌ Erro: {response1.status_code}")
        if response1.text:
            print(f"   Detalhes: {response1.text}")
        return False
    print()
    
    # Verificar cache após primeira geração
    print("🔍 Verificando cache após primeira geração...")
    cache_response = requests.get(f"{BASE_URL}/production/image-cache")
    if cache_response.status_code == 200:
        cache_data = cache_response.json()
        print(f"   Cache atual: {cache_data['cache_count']} entradas")
        
        if cache_data['caches']:
            for cache in cache_data['caches']:
                print(f"      ID: {cache['cache_id']}")
                print(f"      Script: {cache['script_title']}")
                print(f"      Imagens: {cache['image_count']}")
                print(f"      Criado: {cache['created_at']}")
    print()
    
    # Segunda geração (deve usar cache)
    print("🔄 Segunda geração de imagens (deve usar cache)...")
    start_time = time.time()
    
    response2 = requests.post(
        f"{BASE_URL}/production/generate-images",
        json=test_script,
        headers={"Content-Type": "application/json"}
    )
    
    generation_time_2 = time.time() - start_time
    
    if response2.status_code == 200:
        result2 = response2.json()
        print(f"   ✅ Sucesso! {len(result2.get('generated_images', []))} imagens retornadas")
        print(f"   ⏱️ Tempo: {generation_time_2:.2f}s")
        print(f"   💾 Cache usado: {result2.get('cache_used', False)}")
        print(f"   💾 Cache ID: {result2.get('cache_id', 'N/A')}")
        
        # Comparar tempos
        speedup = generation_time_1 / generation_time_2 if generation_time_2 > 0 else 0
        print(f"   🚀 Aceleração: {speedup:.1f}x mais rápido")
        
    else:
        print(f"   ❌ Erro: {response2.status_code}")
        if response2.text:
            print(f"   Detalhes: {response2.text}")
    print()
    
    # Teste com script diferente (deve gerar novo cache)
    print("🆕 Teste com script diferente...")
    different_script = test_script.copy()
    different_script["title"] = "A Aventura do Cachorro Corajoso"
    different_script["visual_style"] = "tecnologia"
    different_script["script_data"]["visual_cues"] = [
        "Um robô futurista em uma cidade cyber",
        "Luzes neon refletindo em superfícies metálicas",
        "Hologramas flutuando no ar"
    ]
    
    start_time = time.time()
    response3 = requests.post(
        f"{BASE_URL}/production/generate-images",
        json=different_script,
        headers={"Content-Type": "application/json"}
    )
    generation_time_3 = time.time() - start_time
    
    if response3.status_code == 200:
        result3 = response3.json()
        print(f"   ✅ Novo script processado! {len(result3.get('generated_images', []))} imagens")
        print(f"   ⏱️ Tempo: {generation_time_3:.2f}s")
        print(f"   💾 Novo Cache ID: {result3.get('cache_id', 'N/A')}")
    else:
        print(f"   ❌ Erro: {response3.status_code}")
    print()
    
    # Verificar cache final
    print("🔍 Cache final:")
    cache_response = requests.get(f"{BASE_URL}/production/image-cache")
    if cache_response.status_code == 200:
        cache_data = cache_response.json()
        print(f"   Total de caches: {cache_data['cache_count']}")
        
        for cache in cache_data['caches']:
            print(f"      📁 {cache['script_title']} ({cache['image_count']} imgs)")
    
    print("=" * 60)
    print("🎉 Teste completo do Step 3 concluído!")
    return True

if __name__ == "__main__":
    print(f"🚀 Iniciando teste Step 3 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Verificar se backend está rodando
    try:
        response = requests.get(f"{BASE_URL}/status", timeout=5)
        if response.status_code == 200:
            print("✅ Backend está rodando")
        else:
            print("❌ Backend não está respondendo corretamente")
            exit(1)
    except:
        print("❌ Backend não está acessível")
        exit(1)
    
    print()
    success = test_image_generation()
    
    if success:
        print("✅ Todos os testes passaram!")
    else:
        print("❌ Alguns testes falharam")
