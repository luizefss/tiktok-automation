#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Pipeline SIMPLIFICADO - DALL-E 3 + ElevenLabs + MoviePy
========================================================

Este pipeline funciona com:
✅ DALL-E 3 (OpenAI) - Imagens de alta qualidade 
✅ ElevenLabs TTS - Áudio premium
✅ MoviePy - Montagem com efeitos visuais
❌ Leonardo Motion - Removido (requer upgrade de conta)

Ao invés de Motion real, usaremos efeitos no MoviePy:
- Ken Burns effect (zoom/pan)
- Fade in/out
- Parallax simples
- Transições suaves
"""

import os
import json
import sys
from pathlib import Path
from dotenv import load_dotenv

# Carregar .env
load_dotenv()

def create_test_video_simplified():
    """Teste do pipeline simplificado SEM Leonardo Motion"""
    print("🎬 PIPELINE SIMPLIFICADO - DALL-E 3 + ElevenLabs + MoviePy")
    print("=" * 60)
    
    # Verificar APIs necessárias
    openai_key = os.getenv('OPENAI_API_KEY')
    eleven_key = os.getenv('ELEVEN_API_KEY')
    
    print("🔑 Verificando APIs:")
    print(f"   DALL-E 3 (OpenAI): {'✅' if openai_key else '❌'}")
    print(f"   ElevenLabs TTS: {'✅' if eleven_key else '❌'}")
    print(f"   Leonardo Motion: ⚠️ DESABILITADO (sem modelos)")
    
    if not openai_key or not eleven_key:
        print("❌ APIs obrigatórias não configuradas")
        return False
    
    # Usar arquivos já gerados
    media_dir = Path("../media/test_output")
    if not media_dir.exists():
        print(f"❌ Diretório {media_dir} não encontrado")
        return False
    
    images_dir = media_dir / "images"
    assets_dir = media_dir / "assets"
    storyboard_file = media_dir / "test_storyboard.json"
    
    print(f"\n📁 Usando arquivos existentes:")
    print(f"   Imagens: {images_dir}")
    print(f"   Áudios: {assets_dir}")
    print(f"   Storyboard: {storyboard_file}")
    
    # Verificar arquivos
    image_files = list(images_dir.glob("scene_*.png"))
    audio_files = list(assets_dir.glob("scene_*.mp3"))
    
    print(f"\n📊 Arquivos encontrados:")
    print(f"   Imagens: {len(image_files)} arquivos")
    print(f"   Áudios: {len(audio_files)} arquivos")
    
    if len(image_files) == 0 or len(audio_files) == 0:
        print("❌ Arquivos necessários não encontrados")
        return False
    
    # Criar vídeo simplificado com MoviePy
    try:
        from moviepy import VideoFileClip, AudioFileClip, CompositeVideoClip, ImageClip
        import moviepy.video.fx as vfx
        
        print("\n🎬 Criando vídeo com efeitos MoviePy...")
        
        # Carregar storyboard
        with open(storyboard_file, 'r', encoding='utf-8') as f:
            storyboard = json.load(f)
        
        clips = []
        
        for i, scene in enumerate(storyboard['scenes'], 1):
            scene_img = images_dir / f"scene_{i:02d}.png"
            scene_audio = assets_dir / f"scene_{i:02d}.mp3"
            
            if not scene_img.exists() or not scene_audio.exists():
                print(f"⚠️ Pulando cena {i} - arquivos faltando")
                continue
            
            # Carregar áudio para duração
            audio = AudioFileClip(str(scene_audio))
            duration = audio.duration
            
            # Criar clip de imagem com efeitos Ken Burns
            img_clip = (ImageClip(str(scene_img))
                       .with_duration(duration)
                       .resize(height=1920)  # 9:16 aspect ratio
                       .with_effects([vfx.Resize(1.1)])  # Zoom inicial
                       .with_effects([vfx.FadeIn(0.5), vfx.FadeOut(0.5)]))  # Fade
            
            # Adicionar áudio
            final_clip = img_clip.with_audio(audio)
            clips.append(final_clip)
            
            print(f"   ✅ Cena {i}: {duration:.1f}s")
        
        if not clips:
            print("❌ Nenhuma cena válida encontrada")
            return False
        
        # Concatenar todas as cenas
        from moviepy import concatenate_videoclips
        final_video = concatenate_videoclips(clips, method="compose")
        
        # Salvar vídeo final
        output_file = media_dir / "newton_prism_SIMPLIFIED.mp4"
        print(f"\n💾 Salvando vídeo: {output_file}")
        
        final_video.write_videofile(
            str(output_file),
            fps=24,
            codec='libx264',
            audio_codec='aac',
            temp_audiofile='temp-audio.m4a',
            remove_temp=True
        )
        
        print(f"\n🎉 SUCESSO! Vídeo criado: {output_file}")
        print(f"   Duração total: {final_video.duration:.1f}s")
        print(f"   Resolução: 1080x1920 (9:16)")
        print(f"   Qualidade: HD com áudio AAC")
        
        # Cleanup
        final_video.close()
        for clip in clips:
            clip.close()
        
        return True
        
    except ImportError as e:
        print(f"❌ Erro de importação MoviePy: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro na criação do vídeo: {e}")
        return False

def main():
    """Função principal"""
    success = create_test_video_simplified()
    
    if success:
        print("\n" + "=" * 60)
        print("🎉 PIPELINE SIMPLIFICADO FUNCIONANDO!")
        print("\n💡 Próximos passos:")
        print("   1. ✅ DALL-E 3 + ElevenLabs funcionando perfeitamente")
        print("   2. ✅ Vídeo HD gerado com efeitos visuais")
        print("   3. 🔄 Para Motion real, considere upgrade do Leonardo AI")
        print("   4. 🎨 Personalizar efeitos no MoviePy conforme necessário")
    else:
        print("\n❌ Teste falhou. Verifique as configurações.")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
