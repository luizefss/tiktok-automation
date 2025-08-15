#var/www/tiktok-automation/backend/sistema_completo_final.py
import os
import time
from datetime import datetime
from complete_pipeline import TikTokPipeline
from tiktok_poster import TikTokPosterV2

class SistemaCompletoFinal:
    def __init__(self):
        self.pipeline = TikTokPipeline()
        self.poster = TikTokPosterV2()
        
    def executar_ciclo_completo(self):
        """CICLO COMPLETO: Gerar vídeo → Postar automaticamente"""
        try:
            print("🚀 EXECUTANDO CICLO COMPLETO DE AUTOMAÇÃO TIKTOK")
            print("=" * 60)
            
            # ETAPA 1: Gerar vídeo completo
            print("🎬 ETAPA 1: Gerando vídeo com IA...")
            resultado_video = self.pipeline.gerar_video_completo()
            
            if not resultado_video:
                print("❌ Falha na geração do vídeo")
                return False
            
            video_path = resultado_video['video']['video_file']
            roteiro_data = resultado_video['roteiro']
            
            print(f"✅ Vídeo gerado: {os.path.basename(video_path)}")
            print(f"📝 Título: {roteiro_data['titulo']}")
            print(f"🔥 Baseado em trending: {roteiro_data.get('is_trending', False)}")
            
            # ETAPA 2: Preparar dados para posting
            titulo = roteiro_data['titulo']
            hashtags = roteiro_data.get('hashtags', [])
            
            # Adicionar hashtags extras para viral
            hashtags_extras = ['#fyp', '#viral', '#brasil']
            hashtags.extend(hashtags_extras)
            hashtags = list(set(hashtags))  # Remover duplicatas
            
            # ETAPA 3: Postar no TikTok
            print("\n📤 ETAPA 2: Postando no TikTok...")
            
            # Criar driver para posting
            if not self.poster.criar_driver_compativel():
                print("❌ Falha ao criar driver de posting")
                return False
            
            # Navegar para TikTok
            if not self.poster.testar_navegacao():
                print("⚠️ Problemas na navegação, mas continuando...")
            
            # implementar login real)
            sucesso_posting = self.poster.upload_real_tiktokstudio(
                video_file=video_path,
                titulo=titulo,
                hashtags=hashtags
            )
            
            if sucesso_posting:
                print("\n🎉 CICLO COMPLETO EXECUTADO COM SUCESSO!")
                print(f"📱 Vídeo '{titulo}' pronto para TikTok!")
                print(f"📁 Localização: {video_path}")
                
                # Mostrar instruções para posting manual
                print("\n" + "="*60)
                print("📱 INSTRUÇÕES PARA POSTING FINAL:")
                print("="*60)
                print("1. Baixe o vídeo do servidor para seu celular")
                print("2. Abra TikTok no celular")
                print("3. Clique em '+' para criar")
                print("4. Selecione o vídeo")
                print(f"5. Cole o título: {titulo}")
                print(f"6. Cole as hashtags: {' '.join(hashtags)}")
                print("7. Publique!")
                
                return True
            else:
                print("❌ Falha no posting")
                return False
                
        except Exception as e:
            print(f"❌ Erro no ciclo completo: {e}")
            return False
        
        finally:
            self.poster.fechar()
    
    def automacao_continua(self, intervalo_horas=8):
        """Automação contínua - gera vídeos a cada X horas"""
        try:
            print(f"🔄 INICIANDO AUTOMAÇÃO CONTÍNUA")
            print(f"⏰ Intervalo: {intervalo_horas} horas entre vídeos")
            print("🔴 Pressione Ctrl+C para parar")
            print("=" * 60)
            
            ciclo = 1
            
            while True:
                print(f"\n🔢 CICLO {ciclo}")
                print(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Executar ciclo completo
                sucesso = self.executar_ciclo_completo()
                
                if sucesso:
                    print(f"✅ Ciclo {ciclo} concluído com sucesso!")
                else:
                    print(f"❌ Ciclo {ciclo} falhou")
                
                # Aguardar próximo ciclo
                print(f"\n⏰ Aguardando {intervalo_horas} horas para próximo ciclo...")
                
                # Sleep em chunks para permitir interrupção
                total_seconds = intervalo_horas * 3600
                for i in range(0, total_seconds, 60):  # Check a cada minuto
                    time.sleep(60)
                    remaining_hours = (total_seconds - i) // 3600
                    remaining_minutes = ((total_seconds - i) % 3600) // 60
                    
                    if i % 3600 == 0:  # Log a cada hora
                        if remaining_hours > 0:
                            print(f"⏳ {remaining_hours}h{remaining_minutes:02d}m restantes...")
                
                ciclo += 1
                
        except KeyboardInterrupt:
            print("\n🛑 Automação interrompida pelo usuário")
        
        except Exception as e:
            print(f"❌ Erro na automação contínua: {e}")

# Sistema final
if __name__ == "__main__":
    print("🤖 SISTEMA COMPLETO DE AUTOMAÇÃO TIKTOK")
    print("🔥 Trending Topics + Vertex AI + Google TTS + Posting")
    print("=" * 60)
    
    sistema = SistemaCompletoFinal()
    
    try:
        print("Escolha uma opção:")
        print("1. Executar um ciclo completo (gerar + postar)")
        print("2. Iniciar automação contínua")
        print("3. Apenas gerar vídeo (sem posting)")
        
        opcao = input("\nOpção (1-3): ").strip()
        
        if opcao == "1":
            sistema.executar_ciclo_completo()
        
        elif opcao == "2":
            horas = input("Intervalo em horas (padrão 8): ").strip()
            intervalo = int(horas) if horas.isdigit() else 8
            sistema.automacao_continua(intervalo)
        
        elif opcao == "3":
            resultado = sistema.pipeline.gerar_video_completo()
            if resultado:
                print(f"✅ Vídeo gerado: {resultado['video']['video_file']}")
            else:
                print("❌ Falha na geração")
        
        else:
            print("❌ Opção inválida")
    
    except KeyboardInterrupt:
        print("\n⚠️ Interrompido pelo usuário")
    
    except Exception as e:
        print(f"❌ Erro geral: {e}")
