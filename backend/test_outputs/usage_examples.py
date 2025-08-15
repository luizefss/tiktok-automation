"""
Exemplos de Uso do Sistema Multi-Plataforma
"""

import asyncio
from datetime import datetime, timedelta
from multi_platform_publisher import (
    MultiPlatformPublisher, 
    PublishRequest, 
    Platform,
    publish_to_all_platforms
)

async def example_basic_publish():
    """Exemplo básico de publicação"""
    
    # Cria solicitação de publicação
    request = PublishRequest(
        video_path="/caminho/para/video.mp4",
        title="Meu Vídeo Incrível",
        description="Descrição do vídeo com conteúdo interessante!",
        tags=["viral", "trending", "conteudo"],
        platforms=[Platform.TIKTOK, Platform.INSTAGRAM_REELS]
    )
    
    # Publica
    publisher = MultiPlatformPublisher()
    results = await publisher.publish_multi_platform(request)
    
    # Mostra resultados
    for platform, result in results.items():
        print(f"{platform.value}: {result.status.value}")
        if result.post_url:
            print(f"  URL: {result.post_url}")

async def example_scheduled_publish():
    """Exemplo de publicação agendada"""
    
    # Agenda para daqui a 2 horas
    schedule_time = datetime.now() + timedelta(hours=2)
    
    request = PublishRequest(
        video_path="/caminho/para/video.mp4",
        title="Vídeo Agendado",
        description="Este vídeo foi agendado!",
        tags=["agendado", "automatico"],
        platforms=[Platform.YOUTUBE_SHORTS, Platform.FACEBOOK_REELS],
        schedule_time=schedule_time
    )
    
    publisher = MultiPlatformPublisher()
    schedule_id = publisher.schedule_publication(request, schedule_time)
    print(f"Agendamento criado: {schedule_id}")

async def example_optimal_timing():
    """Exemplo usando horários ótimos"""
    
    publisher = MultiPlatformPublisher()
    
    # Obtém horários ótimos para TikTok
    optimal_times = publisher.get_optimal_posting_times(Platform.TIKTOK)
    print("Horários ótimos para TikTok:", optimal_times)
    
    # Agenda para o próximo horário ótimo
    next_optimal = optimal_times[0]
    
    request = PublishRequest(
        video_path="/caminho/para/video.mp4",
        title="Vídeo no Horário Ótimo",
        description="Publicado no melhor horário!",
        tags=["timing", "otimo"],
        platforms=[Platform.TIKTOK]
    )
    
    if next_optimal > datetime.now():
        schedule_id = publisher.schedule_publication(request, next_optimal)
        print(f"Agendado para horário ótimo: {schedule_id}")
    else:
        results = await publisher.publish_multi_platform(request)
        print("Publicado imediatamente")

async def example_analytics():
    """Exemplo de análise de performance"""
    
    publisher = MultiPlatformPublisher()
    
    # Obtém resumo analítico
    analytics = publisher.get_analytics_summary()
    
    print("📊 Resumo Analítico:")
    print(f"Total de posts: {analytics['total_posts']}")
    print(f"Taxa de sucesso: {analytics['success_rate']}%")
    
    print("\nPor plataforma:")
    for platform, stats in analytics['platforms'].items():
        success_rate = (stats['success'] / stats['total']) * 100
        print(f"  {platform}: {stats['success']}/{stats['total']} ({success_rate:.1f}%)")

async def example_convenience_function():
    """Exemplo usando função de conveniência"""
    
    # Publica em todas as plataformas de uma vez
    results = await publish_to_all_platforms(
        video_path="/caminho/para/video.mp4",
        title="Publicação Completa",
        description="Publicando em todas as plataformas!",
        tags=["viral", "multiplataforma", "automatico"]
    )
    
    print("Resultados da publicação completa:")
    for platform, result in results.items():
        print(f"  {platform.value}: {result.status.value}")

if __name__ == "__main__":
    # Executa exemplos
    print("🚀 Executando exemplos...")
    
    # asyncio.run(example_basic_publish())
    # asyncio.run(example_scheduled_publish())
    # asyncio.run(example_optimal_timing())
    # asyncio.run(example_analytics())
    # asyncio.run(example_convenience_function())
    
    print("✅ Exemplos concluídos!")
