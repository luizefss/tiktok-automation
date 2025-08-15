#!/usr/bin/env python3
"""
Teste rápido para verificar se o MoviePy está funcionando após ajustes no ImageMagick
"""

import os
import tempfile
from moviepy.editor import ColorClip, TextClip, CompositeVideoClip

def test_moviepy():
    """Teste básico do MoviePy com texto"""
    print("🧪 Testando MoviePy após ajustes no ImageMagick...")
    
    try:
        # Criar um clip colorido básico
        color_clip = ColorClip(size=(640, 480), color=(0, 0, 0), duration=2)
        print("✅ ColorClip criado com sucesso")
        
        # Tentar criar um TextClip (isso é o que estava falhando)
        text_clip = TextClip("Teste MoviePy", 
                           fontsize=30, 
                           color='white',
                           font='Arial')
        print("✅ TextClip criado com sucesso")
        
        # Posicionar o texto
        text_clip = text_clip.set_position('center').set_duration(2)
        print("✅ TextClip posicionado com sucesso")
        
        # Compor o vídeo
        final_clip = CompositeVideoClip([color_clip, text_clip])
        print("✅ CompositeVideoClip criado com sucesso")
        
        # Salvar temporariamente
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp_file:
            temp_path = tmp_file.name
        
        final_clip.write_videofile(temp_path, fps=30, verbose=False, logger=None)
        print(f"✅ Vídeo salvo em: {temp_path}")
        
        # Verificar se o arquivo foi criado
        if os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
            print("✅ Arquivo de vídeo válido criado!")
            file_size = os.path.getsize(temp_path) / 1024  # KB
            print(f"📊 Tamanho do arquivo: {file_size:.2f} KB")
            
            # Limpar arquivo temporário
            os.unlink(temp_path)
            print("🧹 Arquivo temporário removido")
            
            return True
        else:
            print("❌ Arquivo de vídeo não foi criado corretamente")
            return False
            
    except Exception as e:
        print(f"❌ Erro no teste do MoviePy: {e}")
        return False

if __name__ == "__main__":
    print("="*60)
    print("🎬 TESTE DE FUNCIONAMENTO DO MOVIEPY")
    print("="*60)
    
    success = test_moviepy()
    
    print("\n" + "="*60)
    if success:
        print("🎉 MOVIEPY FUNCIONANDO CORRETAMENTE!")
        print("✅ Os ajustes no ImageMagick resolveram o problema")
    else:
        print("❌ MOVIEPY AINDA COM PROBLEMAS")
        print("⚠️  Pode ser necessário ajustes adicionais")
    print("="*60)
