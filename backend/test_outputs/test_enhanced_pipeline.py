# /var/www/tiktok-automation/backend/test_enhanced_pipeline.py

"""
Teste do Pipeline Avançado
Roteiro → Imagens → Áudio → Vídeo → Publicação
"""

import asyncio
from content_pipeline_enhanced import (
    ContentPipelineEnhanced,
    ContentPipelineRequest,
    Platform,
    create_content_from_script
)

async def test_script_analysis():
    """Testa análise de roteiro"""
    print("📝 Testando Análise de Roteiro...")
    
    script = """
    Transformação incrível de uma cozinha pequena! Começamos com um espaço apertado e escuro,
    mas com o projeto certo conseguimos criar uma cozinha moderna, funcional e aconchegante.
    Usamos cores claras, móveis planejados e uma iluminação especial que fez toda a diferença.
    O resultado ficou simplesmente perfeito para essa família!
    """
    
    pipeline = ContentPipelineEnhanced()
    analysis = await pipeline._analyze_script(script)
    
    if analysis:
        print("✅ Análise concluída:")
        print(f"  Tópico Principal: {analysis.main_topic}")
        print(f"  Palavras-chave Visuais: {analysis.visual_keywords}")
        print(f"  Emoções: {analysis.emotions}")
        print(f"  Audiência: {analysis.target_audience}")
        print(f"  Tom: {analysis.tone}")
        print(f"  Duração Estimada: {analysis.duration_estimate:.1f} min")
        print(f"  Pontos Principais: {len(analysis.key_points)} itens")
        return True
    else:
        print("❌ Falha na análise")
        return False

async def test_image_generation():
    """Testa geração de imagens"""
    print("\n🎨 Testando Geração de Imagens...")
    
    script = """
    Vamos construir uma casa moderna com design sustentável. 
    O projeto inclui painéis solares, jardim vertical e materiais ecológicos.
    """
    
    pipeline = ContentPipelineEnhanced()
    analysis = await pipeline._analyze_script(script)
    
    if analysis:
        request = ContentPipelineRequest(
            script=script,
            title="Casa Sustentável",
            description="Projeto moderno e ecológico",
            tags=["sustentável", "moderno"],
            platforms=[Platform.TIKTOK],
            generate_images=True
        )
        
        images = await pipeline._generate_images(analysis, request)
        
        if images:
            print("✅ Imagens geradas:")
            for platform, image_list in images.items():
                print(f"  {platform}: {len(image_list)} imagens")
                for img in image_list:
                    print(f"    - {img}")
            return True
        else:
            print("❌ Falha na geração de imagens")
            return False
    else:
        print("❌ Falha na análise prévia")
        return False

async def test_complete_pipeline():
    """Testa pipeline completo"""
    print("\n🚀 Testando Pipeline Completo...")
    
    script = """
    Olá pessoal! Hoje vou mostrar uma reforma incrível que fizemos em um apartamento pequeno.
    O cliente queria mais espaço e funcionalidade, então criamos um projeto integrado que 
    aproveita cada centímetro. Demolimos uma parede, criamos uma cozinha americana moderna
    e instalamos móveis planejados que fazem toda a diferença. O resultado ficou espetacular!
    """
    
    result = await create_content_from_script(
        script=script,
        title="Reforma Completa de Apartamento Pequeno",
        description="Transformação total com cozinha americana e móveis planejados",
        tags=["reforma", "apartamento", "cozinha americana", "móveis planejados"],
        platforms=["tiktok", "instagram_reels"],
        generate_images=True,
        visual_style="modern_tech",
        voice_style="inspired"
    )
    
    if result.success:
        print("✅ Pipeline completo executado com sucesso!")
        print(f"⏱️ Tempo total: {result.processing_time:.2f}s")
        
        if result.script_analysis:
            print(f"📝 Análise: {result.script_analysis.main_topic}")
            print(f"🎭 Emoções: {', '.join(result.script_analysis.emotions)}")
            print(f"👥 Audiência: {result.script_analysis.target_audience}")
        
        print(f"🖼️ Imagens geradas: {sum(len(imgs) for imgs in result.generated_images.values())}")
        for platform, images in result.generated_images.items():
            print(f"  {platform}: {len(images)} imagens")
        
        print(f"🎵 Arquivos de áudio: {len(result.audio_files)}")
        for platform, audio in result.audio_files.items():
            print(f"  {platform}: {audio}")
        
        print(f"🎬 Vídeos criados: {len(result.video_files)}")
        for platform, video in result.video_files.items():
            print(f"  {platform}: {video}")
        
        print(f"📱 Publicações: {len(result.publish_results)} tentativas")
        
        return True
    else:
        print(f"❌ Pipeline falhou: {result.error_message}")
        return False

async def test_flow_comparison():
    """Compara os dois fluxos"""
    print("\n⚖️ Comparando Fluxos...")
    
    print("📊 FLUXO ANTERIOR:")
    print("1. TTS (Áudio) → 2. Efeitos Visuais → 3. Publicação")
    print("   - Mais rápido")
    print("   - Efeitos visuais genéricos")
    print("   - Sem imagens relacionadas ao conteúdo")
    
    print("\n📊 FLUXO NOVO (ENHANCED):")
    print("1. Análise do Roteiro → 2. Geração de Imagens → 3. TTS (Áudio) → 4. Composição de Vídeo → 5. Publicação")
    print("   - Mais personalizado")
    print("   - Imagens específicas do conteúdo")
    print("   - Análise inteligente do roteiro")
    print("   - Voz adaptada ao contexto")
    print("   - Vídeos mais envolventes")
    
    print("\n💡 RECOMENDAÇÃO:")
    print("Use o FLUXO ENHANCED para conteúdo premium e personalizado")
    print("Use o FLUXO ANTERIOR para produção rápida em massa")

async def main():
    """Executa todos os testes"""
    print("🧪 TESTANDO PIPELINE AVANÇADO DE CONTEÚDO")
    print("=" * 60)
    
    tests = [
        ("Análise de Roteiro", test_script_analysis),
        ("Geração de Imagens", test_image_generation),
        ("Pipeline Completo", test_complete_pipeline),
        ("Comparação de Fluxos", test_flow_comparison)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        
        try:
            result = await test_func()
            results[test_name] = result
            
            if result if result is not None else True:
                print(f"✅ {test_name}: PASSOU")
            else:
                print(f"❌ {test_name}: FALHOU")
                
        except Exception as e:
            print(f"💥 {test_name}: ERRO - {e}")
            results[test_name] = False
    
    # Resumo
    print("\n" + "=" * 60)
    print("📊 RESUMO DOS TESTES")
    print("=" * 60)
    
    passed = sum(1 for r in results.values() if r)
    total = len([r for r in results.values() if r is not None])
    
    for test_name, result in results.items():
        if result is not None:
            status = "✅ PASSOU" if result else "❌ FALHOU"
            print(f"{test_name}: {status}")
    
    print(f"\n🎯 RESULTADO: {passed}/{total} testes passaram")
    
    print("\n💡 PRÓXIMOS PASSOS:")
    print("1. Configurar APIs de geração de imagens (DALL-E, Stable Diffusion)")
    print("2. Implementar composição real de vídeos com MoviePy")
    print("3. Integrar com sistema de templates visuais")
    print("4. Adicionar análise de sentimentos mais avançada")
    print("5. Implementar cache de imagens e otimizações")

if __name__ == "__main__":
    asyncio.run(main())
