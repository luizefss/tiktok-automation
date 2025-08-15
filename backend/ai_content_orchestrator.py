# /var/www/tiktok-automation/backend/ai_content_orchestrator.py

import random
import os
import json
import logging
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

# Importa os geradores de conteúdo existentes
from enhanced_content_generator import EnhancedContentGenerator  # Para Gemini
from hybrid_ai import HybridAI  # Para Claude
from trending_content_system import TrendingContentSystem
from datetime import datetime


# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AIContentOrchestrator:
    def __init__(self):
        load_dotenv()

        # Centraliza a inicialização dos geradores de IA
        self.ai_generators = {
            'Gemini 1.5 Pro': EnhancedContentGenerator(),
            'Claude 4 Sonnet': HybridAI(),
            # Adicione outras IAs aqui, como 'ChatGPT-4 Turbo'
            # 'ChatGPT-4 Turbo': OSEU_GERADOR_CHATGPT()
        }
        self.trending_system = TrendingContentSystem()

    def iniciar_batalha_de_roteiros(self, battle_settings: Dict[str, Any]) -> Dict[str, Any]:

        # Obtém a lista de participantes do frontend ou usa um padrão
        participants = battle_settings.get(
            'participants', ['Gemini 1.5 Pro', 'Claude 4 Sonnet'])

        custom_topics = battle_settings.get('custom_topics', [])

        if custom_topics:
            topic = custom_topics[0]
            logger.info(
                f"\n⚔️  INICIANDO BATALHA (MODO MANUAL) SOBRE O TEMA: '{topic}' ⚔️")
        else:
            logger.info("\n⚔️  INICIANDO BATALHA (MODO AUTOMÁTICO) ⚔️")
            logger.info("🧠 Buscando tema relevante nas tendências...")

            topic_data = self.trending_system.obter_topico_para_roteiro()
            topic = topic_data.get(
                'topic') if topic_data else "O mistério do universo"

            logger.info(f"🎯 Tema selecionado das tendências: '{topic}'")
            battle_settings['custom_topics'] = [topic]

        results = []

        for ia_name in participants:
            ia_generator = self.ai_generators.get(ia_name)
            if not ia_generator:
                results.append({"iaName": ia_name, "scriptData": None,
                               "error": f"IA '{ia_name}' não configurada."})
                continue

            try:
                logger.info(f"⚔️ IA {ia_name} iniciando...")
                # Chama o método de geração de roteiro do gerador correspondente
                if ia_name == 'Claude 4 Sonnet':
                    roteiro = ia_generator.gerar_roteiro_claude(
                        battle_settings)
                else:
                    roteiro = ia_generator.gerar_conteudo_viral_otimizado(
                        battle_settings)

                if roteiro:
                    results.append(
                        {"iaName": ia_name, "scriptData": roteiro, "error": None})
                    logger.info(f"✅ {ia_name} gerou roteiro com sucesso.")
                else:
                    results.append(
                        {"iaName": ia_name, "scriptData": None, "error": "Falha na geração."})

            except Exception as e:
                # Captura o erro da API e continua
                results.append(
                    {"iaName": ia_name, "scriptData": None, "error": str(e)})
                logger.error(f"❌ {ia_name} falhou: {e}")

        logger.info("✅ Batalha finalizada.")

        # Encontrar um vencedor, se houver
        valid_results = [res for res in results if res.get('scriptData')]
        if not valid_results:
            return {"success": False, "error": "Nenhuma IA conseguiu gerar um roteiro válido."}

        # Simplesmente escolhe um vencedor aleatoriamente entre os que funcionaram
        winner = random.choice(valid_results)

        return {
            "success": True,
            "results": results,
            "winner": winner.get('iaName')
        }

    # Resto dos métodos mantidos
    def gerar_roteiro_com_ia_selecionada(self, settings: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        content_ai_model = settings.get('content_ai_model', 'gemini').lower()
        logger.info(
            f"\n🧠 Orquestrador: Gerando roteiro com {content_ai_model.upper()}...")

        ia_generator = self.ai_generators.get(content_ai_model)
        if ia_generator:
            try:
                # Chama o método de geração de roteiro do gerador correspondente
                if content_ai_model == 'claude':
                    roteiro = ia_generator.gerar_roteiro_claude(settings)
                else:
                    roteiro = ia_generator.gerar_conteudo_viral_otimizado(
                        settings)

                if roteiro:
                    roteiro['ia_used'] = content_ai_model
                    return roteiro
                else:
                    logger.warning("Falha na geração do roteiro.")
                    return None
            except Exception as e:
                logger.error(f"Erro na geração com {content_ai_model}: {e}")
                return None
        else:
            logger.warning(
                f"Modelo de IA '{content_ai_model}' inválido. Usando Gemini como fallback.")
            return self.ai_generators.get('Gemini 1.5 Pro').gerar_conteudo_viral_otimizado(settings)

    # Os métodos _gerar_com_gemini, _gerar_com_claude e _gerar_com_chatgpt foram removidos pois não são mais necessários
    # A lógica foi consolidada em 'gerar_roteiro_com_ia_selecionada' e 'iniciar_batalha_de_roteiros'.


# Teste para AIContentOrchestrator
if __name__ == "__main__":
    print("🧪 TESTANDO AI CONTENT ORCHESTRATOR")
    print("=" * 60)

    orchestrator = AIContentOrchestrator()

    test_settings_gemini = {
        'content_ai_model': 'Gemini 1.5 Pro',
        'content_type': 'custom_message',
        'custom_topics': ['Hábitos Produtivos', 'Foco'],
        'message_categories': ['Conhecimento'],
        'tone': 'educational',
        'voice_emotion': 'enthusiastic',
        'image_style': 'vectorized',
        'color_palette': 'vibrant',
    }

    test_settings_claude = {
        'content_ai_model': 'Claude 4 Sonnet',
        'content_type': 'custom_message',
        'message_categories': ['Tecnologia'],
        'custom_topics': ['Futuro da IA'],
        'tone': 'dramatic',
        'voice_emotion': 'dramatic',
        'image_style': 'cinematic',
    }

    # <<< BLOCO DE TESTE PARA A NOVA FUNÇÃO DE BATALHA >>>
    print("\n--- ⚔️  Testando a Batalha de IAs (Modo Final) ⚔️  ---")

    battle_settings_teste = {
        "content_type": "custom_message",
        "custom_topics": ["O verdadeiro poder da disciplina"],
        "message_categories": ["Motivação"],
        "tone": "inspirational",
        "voice_emotion": "calm",
        "target_languages": ["pt-BR"],
        # Lista de participantes
        "participants": ["Gemini 1.5 Pro", "Claude 4 Sonnet"]
    }

    battle_results = orchestrator.iniciar_batalha_de_roteiros(
        battle_settings_teste)

    if battle_results and battle_results.get('success'):
        print("\n✅ Batalha concluída com sucesso!")
        for result in battle_results.get('results', []):
            ia_name = result.get('iaName')
            script_data = result.get('scriptData')
            error = result.get('error')

            if script_data and not error:
                print(f"--- Resultado para {ia_name} ---")
                print(f"  Título: {script_data.get('titulo')}")
                print(f"  Hook: {script_data.get('hook')}")
            else:
                print(f"--- Falha ou Standby para {ia_name} ---")
                print(f"  Motivo: {error or 'Não retornou roteiro.'}")

        print(f"\n🏆 Vencedor da Batalha: {battle_results.get('winner')}")

    else:
        print("\n❌ Falha na execução da batalha de IAs.")
