# /var/www/tiktok-automation/backend/ai_orchestrator.py

import json
import random
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from unidecode import unidecode
import asyncio

# Importa as classes de serviço
from gemini_client import GeminiClient
from services.claude_service import ClaudeService
from services.gpt_service import GPTService
from gemini_prompts import GeminiPrompts

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ContentQuality(Enum):
    ELITE = "elite"
    PREMIUM = "premium"
    STANDARD = "standard"
    BASIC = "basic"


class ViralElements(Enum):
    EMOTIONAL = "emotional_triggers"
    CURIOSITY = "curiosity_gaps"
    PATTERN = "pattern_interrupts"
    SOCIAL_PROOF = "social_proof"
    URGENCY = "urgency_factors"


class VideoTheme(Enum):
    MISTERIO = "misterio"
    CURIOSIDADE = "curiosidade"
    HISTORIA = "historia"
    CIENCIA = "ciencia"
    TERROR = "terror"
    MOTIVACIONAL = "motivacional"
    COMEDIA = "comedia"
    ROMANCE = "romance"


class RegionalAccent(Enum):
    NEUTRO = "neutro"
    CARIOCA = "carioca"
    PAULISTA = "paulista"
    MINEIRO = "mineiro"
    NORDESTINO = "nordestino"
    GAUCHO = "gaúcho"
    BAIANO = "baiano"


class AIOrchestrator:
    def __init__(self):
        self.gemini_client = GeminiClient()
        self.claude_service = ClaudeService()
        self.gpt_service = GPTService()
        self.prompts = GeminiPrompts()

        self.ai_providers = {
            "gemini": {"service": self.gemini_client, "models": ["gemini-2.5-pro-preview-tts"]},
            "claude": {"service": self.claude_service, "models": self.claude_service.available_models},
            "gpt": {"service": self.gpt_service, "models": self.gpt_service.available_models}
        }
        
        # Log de inicialização dos provedores
        logger.info("🤖 Inicializando AI Orchestrator...")
        self._log_provider_status()

    def _select_viral_strategy(self, topic: str, category: str = "geral") -> Dict[str, str]:
        """Seleciona a estratégia viral com base no tópico e na categoria."""
        strategies = {
            "tecnologia": {"hook_style": "curiosidade_tech", "duration": "45-60s", "cta_type": "engagement_alto", "emotional_trigger": "discovery", "pattern_interrupt": "stat_shock"},
            "entretenimento": {"hook_style": "drama_emocional", "duration": "30-45s", "cta_type": "viral_sharing", "emotional_trigger": "excitement", "pattern_interrupt": "story_twist"},
            "educacao": {"hook_style": "problema_solucao", "duration": "60-90s", "cta_type": "save_follow", "emotional_trigger": "empowerment", "pattern_interrupt": "myth_buster"},
            "lifestyle": {"hook_style": "transformacao_pessoal", "duration": "45-75s", "cta_type": "aspirational_follow", "emotional_trigger": "inspiration", "pattern_interrupt": "before_after"},
            "negocios": {"hook_style": "segredo_financeiro", "duration": "50-70s", "cta_type": "value_driven", "emotional_trigger": "aspiration", "pattern_interrupt": "money_reveal"},
            "saude": {"hook_style": "mito_vs_verdade", "duration": "45-60s", "cta_type": "health_conscious", "emotional_trigger": "concern", "pattern_interrupt": "medical_surprise"},
            "geral": {"hook_style": "curiosidade_geral", "duration": "45-60s", "cta_type": "engagement_medio", "emotional_trigger": "curiosity", "pattern_interrupt": "unexpected_fact"}
        }
        return strategies.get(category.lower(), strategies["geral"])

    async def generate_script(
        self,
        theme: str,
        ai_provider: str = "gemini",
        video_style: Optional[str] = None,
        accent: str = "brasileiro",
        emotion_level: int = 7,
    story_type: str = "curiosidade",
    allow_cross_provider_fallback: bool = True
    ) -> Dict[str, Any]:
        """Gera um roteiro humanizado e otimizado para TTS com estruturas específicas de história."""
        try:
            if not video_style:
                video_style = self._detect_video_style(theme)

            strategy = self._select_viral_strategy(theme, video_style)
            
            # Detectar se é conteúdo histórico/científico para usar novos prompts híbridos
            is_history_science = any(keyword in theme.lower() for keyword in 
                                   ['historia', 'ciencia', 'leonardo', 'catapulta', 'renascimento', 
                                    'inventor', 'descoberta', 'experimento', 'invenção', 'cientista',
                                    'guerra', 'batalha', 'medieval', 'antigo', 'egipto', 'romano',
                                    'genio', 'maquina', 'engenharia', 'fisica', 'quimica', 'medicina',
                                    'arqueologia', 'filosofo', 'matematico', 'rei', 'imperio', 'civilizacao']) or \
                                story_type in ['historia', 'ciencia']
            
            logger.info(f"🎯 Detecção de conteúdo histórico/científico: {is_history_science} (tema: {theme}, story_type: {story_type})")
            
            if is_history_science:
                # Usar novos prompts híbridos para história/ciência
                if ai_provider.lower() == 'gemini':
                    from gemini_prompts import build_storyboard_prompt_historia_gemini
                    # Incrementa a duração alvo para enriquecer o roteiro do Gemini
                    prompt = build_storyboard_prompt_historia_gemini(theme, duration_target_sec=90)
                elif ai_provider.lower() == 'claude':
                    from hybrid_ai import HybridAI
                    hybrid_ai = HybridAI()
                    prompt = hybrid_ai.build_storyboard_prompt_historia_claude(theme, duration_target_sec=90)
                elif ai_provider.lower() in ['gpt-4', 'gpt', 'openai']:
                    from enhanced_content_generator import build_storyboard_prompt_historia_gpt
                    prompt = build_storyboard_prompt_historia_gpt(theme, duration_target_sec=90)
                else:
                    # Fallback para outros provedores
                    from humanized_prompts import HumanizedPrompts
                    humanized_prompts = HumanizedPrompts()
                    prompt = humanized_prompts.get_humanized_prompt_for_ai(
                        ai_type=ai_provider,
                        theme=theme,
                        story_type=story_type
                    )
            else:
                # Usar prompts humanizados para TTS com tipo de história
                from humanized_prompts import HumanizedPrompts
                humanized_prompts = HumanizedPrompts()
                
                # Gerar prompt humanizado específico para cada IA com estrutura de história
                prompt = humanized_prompts.get_humanized_prompt_for_ai(
                    ai_type=ai_provider,
                    theme=theme,
                    story_type=story_type  # Usar o tipo de história especificado
                )
            
            logger.info(f"Usando prompt estruturado para {ai_provider.upper()} - Tipo: {story_type}")

            # Acrescentar regras de diferenciação/relevância por provedor
            prompt = self._augment_prompt_for_provider(ai_provider, prompt, theme, video_style, story_type)

            # Definir schema esperado quando for GPT para garantir JSON estrito
            gpt_schema = {
                "type": "object",
                "properties": {
                    "roteiro_completo": {"type": "string"},
                    "hook": {"type": "string"},
                    "titulo": {"type": "string"},
                    "hashtags": {"type": "array", "items": {"type": "string"}},
                    "ia_used": {"type": "string"},
                    "accent": {"type": "string"},
                    "estimated_duration": {"type": "number"},
                    "call_to_action": {"type": "string"},
                    "style": {"type": "string"},
                    "speech_optimized": {"type": "boolean"},
                    "scenes": {"type": "array", "items": {"type": "object"}},
                    "viral_analysis": {"type": "object"}
                },
                "required": ["roteiro_completo", "hook", "titulo"],
                "additionalProperties": True
            }

            # Gerar com provedor (para GPT, passa schema) com ou sem fallback entre provedores
            # Em batalhas, desativamos fallback cruzado para garantir independência entre concorrentes
            if allow_cross_provider_fallback:
                providers_order = [ai_provider]
                for p in ["claude", "gpt", "gemini"]:
                    if p.lower() not in [prov.lower() for prov in providers_order]:
                        providers_order.append(p)
            else:
                providers_order = [ai_provider]

            script_text: Optional[str] = None
            for prov in providers_order:
                if not self._check_provider_availability(prov):
                    logger.info(f"⏭️ Provedor indisponível: {prov}")
                    continue
                logger.info(f"🤖 Gerando com provedor: {prov}")
                script_text = await self._generate_with_provider(
                    prompt,
                    prov,
                    json_schema=gpt_schema if prov.lower() in ["gpt", "openai", "gpt-4"] else None,
                )
                if script_text:
                    ai_provider = prov  # atualizar para o provedor efetivo
                    break
            if not script_text:
                raise RuntimeError("Falha em todos os provedores de IA")

            # Processar resposta baseado no tipo de conteúdo
            if is_history_science:
                # Para conteúdo histórico/científico, usar normalizador híbrido
                try:
                    import json
                    if not script_text:
                        raise json.JSONDecodeError("empty", "", 0)
                    script_data = json.loads(script_text.strip())
                except json.JSONDecodeError:
                    # Tentar processadores específicos por provedor (Claude/GPT) para extrair JSON
                    parsed: Optional[Dict[str, Any]] = None
                    try:
                        prov = ai_provider.lower()
                        if prov == 'claude' and script_text:
                            parsed = self._process_claude_response(script_text)
                        elif prov in ['gpt', 'openai', 'gpt-4'] and script_text:
                            parsed = self._process_gpt_response(script_text)
                    except Exception:
                        parsed = None
                    
                    if parsed:
                        script_data = parsed
                    else:
                        # Se não der, usar parser humanizado como último recurso
                        from humanized_parser import HumanizedParser
                        parser = HumanizedParser()
                        script_data = parser.extract_humanized_script(script_text or "", ai_provider) or {}

                # Aplicar normalizador para garantir formato correto, mesmo se vier vazio
                from enhanced_content_generator import normalize_storyboard_payload
                # Se for Gemini, manter alvo um pouco maior para incentivar mais cenas
                norm_target = 90 if ai_provider.lower() == 'gemini' else 60
                script_data = normalize_storyboard_payload(script_data, duration_target_sec=norm_target)
            else:
                # Usar parser humanizado para todas as outras IAs
                from humanized_parser import HumanizedParser
                parser = HumanizedParser()
                script_data = parser.extract_humanized_script(script_text or "", ai_provider)

            # Verificação de aderência ao tema e retry se necessário (após parsing de ambos ramos)
            try:
                topic_match, missing = self._compute_topic_match(theme, script_data or {})
                if ai_provider.lower() in ['claude', 'gpt', 'openai', 'gpt-4'] and topic_match < 0.5:
                    logger.warning(f"⚠️ {ai_provider.title()} gerou roteiro com baixa aderência ao tema ({topic_match:.2f}). Reforçando prompt e tentando novamente...")
                    reinforced_prompt = self._build_reinforced_prompt(prompt, theme, missing, ai_provider)
                    retry_text = await self._generate_with_provider(
                        reinforced_prompt,
                        ai_provider,
                        json_schema=gpt_schema if ai_provider.lower() in ["gpt", "openai", "gpt-4"] else None,
                    )
                    # Repetir parsing com mesmo caminho do ramo atual
                    try:
                        import json
                        retry_data = json.loads((retry_text or '').strip())
                    except Exception:
                        if ai_provider.lower() == 'claude':
                            retry_data = self._process_claude_response(retry_text or "") or {}
                        elif ai_provider.lower() in ['gpt', 'openai', 'gpt-4']:
                            retry_data = self._process_gpt_response(retry_text or "") or {}
                        else:
                            from humanized_parser import HumanizedParser
                            parser = HumanizedParser()
                            retry_data = parser.extract_humanized_script(retry_text or "", ai_provider)
                    # Normalizar estrutura final
                    from enhanced_content_generator import normalize_storyboard_payload
                    norm_target = 90 if ai_provider.lower() == 'gemini' else 60
                    retry_data = normalize_storyboard_payload(retry_data or {}, duration_target_sec=norm_target)

                    retry_match, _ = self._compute_topic_match(theme, retry_data or {})
                    if retry_match >= topic_match:
                        script_data = retry_data
                        logger.info(f"✅ Retry do Claude melhorou a aderência ao tema para {retry_match:.2f}")
            except Exception as guard_err:
                logger.debug(f"Guardrail de aderência ignorado por erro: {guard_err}")
            
            if not script_data or (not script_data.get('roteiro_completo') and not script_data.get('scenes')):
                # Em vez de um payload genérico, reforçar prompt e tentar outro provedor antes do fallback final
                try:
                    topic_match, missing = self._compute_topic_match(theme, script_data or {})
                except Exception:
                    topic_match, missing = 0.0, []

                # Montar uma ordem de fallback curta e tentativa de reforço
                fallback_order = ['claude', 'gpt', 'gemini'] if allow_cross_provider_fallback else []
                # Garantir que o atual não venha primeiro de novo
                fallback_order = [p for p in fallback_order if p.lower() != (ai_provider or '').lower()]
                reinforced_prompt = self._build_reinforced_prompt(prompt, theme, missing, ai_provider)
                for prov in fallback_order:
                    if not self._check_provider_availability(prov):
                        continue
                    try:
                        text_retry = await self._generate_with_provider(
                            reinforced_prompt,
                            prov,
                            json_schema=gpt_schema if prov in ["gpt", "openai", "gpt-4"] else None,
                        )
                        parsed_retry = None
                        try:
                            parsed_retry = json.loads((text_retry or '').strip())
                        except Exception:
                            if prov == 'claude':
                                parsed_retry = self._process_claude_response(text_retry or "")
                            elif prov in ['gpt', 'openai', 'gpt-4']:
                                parsed_retry = self._process_gpt_response(text_retry or "")
                        if parsed_retry and (parsed_retry.get('roteiro_completo') or parsed_retry.get('scenes')):
                            script_data = parsed_retry
                            ai_provider = prov
                            break
                    except Exception:
                        continue

                # Fallback final minimalista porém focado no tema
                if not script_data or (not script_data.get('roteiro_completo') and not script_data.get('scenes')):
                    from enhanced_content_generator import normalize_storyboard_payload
                    fallback_payload = {
                        "titulo": theme if len(theme) <= 60 else theme[:57] + '...',
                        "hook": self._build_personalized_opening(theme),
                        "roteiro_completo": f"{theme}: resumo objetivo em linguagem falada, com curiosidade inicial, 2-3 fatos marcantes e encerramento com CTA leve.",
                        "hashtags": [f"#{k}" for k in self._extract_keywords(theme)[:5]]
                    }
                    script_data = normalize_storyboard_payload(fallback_payload, duration_target_sec=(90 if (ai_provider or '').lower() == 'gemini' else 60))

            # Carimbar explicitamente o provedor real utilizado (evita confusão em batalhas)
            script_data['ia_used'] = ai_provider
            script_data['style'] = video_style
            script_data['accent'] = accent
            script_data['story_type'] = story_type  # Adicionar o tipo de história ao resultado

            script_data['viral_analysis'] = self._analyze_viral_potential(
                script_data, theme, video_style)

            # Anotar assinatura do provedor e aderência ao tema
            try:
                topic_match_score, _ = self._compute_topic_match(theme, script_data or {})
                provider_signature = {
                    "provider": ai_provider,
                    "angle": "analitico-causal-com-nuancas" if ai_provider.lower() == 'claude' else "generico",
                    "differentiation": "enfoque em causalidade/contexto" if ai_provider.lower() == 'claude' else "",
                    "topic_match": round(float(topic_match_score), 3)
                }
                script_data['provider_signature'] = provider_signature
            except Exception:
                pass

            # ===== Enriquecimento: garantir roteiro primeiro e prompts derivados =====
            try:
                # 1) Roteiro textual contínuo, sem marcações de tempo
                roteiro_text = (
                    script_data.get('roteiro_completo') or
                    script_data.get('final_script_for_tts') or
                    script_data.get('script') or
                    script_data.get('content') or
                    ''
                )

                if not roteiro_text:
                    scenes = script_data.get('scenes') or []
                    if isinstance(scenes, list) and scenes:
                        parts = []
                        for s in scenes:
                            if not isinstance(s, dict):
                                continue
                            if s.get('narration'):
                                parts.append(str(s['narration']))
                            elif s.get('on_screen_text'):
                                parts.append(str(s['on_screen_text']))
                        roteiro_text = "\n".join(parts)

                script_data['roteiro_completo'] = roteiro_text or ''

                # 2) Derivar prompts com duração por cena
                scenes = script_data.get('scenes') or []
                visual_prompts: List[Dict[str, str]] = []
                img_lines: List[str] = []
                motion_lines: List[str] = []

                if isinstance(scenes, list) and scenes:
                    # Preparar cálculo cumulativo com limite de 3s por cena (pacing visual)
                    target_total = int(script_data.get('duration_target_sec') or 60)
                    max_cut = 3  # segundos
                    # se provedor mandou tempo médio maior, reduzimos para cap de 3s nas labels
                    approx_default = max(1, int(round(target_total / max(1, len(scenes)))))
                    per_scene = min(max_cut, approx_default)
                    cumulative_start = 0
                    for s in scenes:
                        if not isinstance(s, dict):
                            continue
                        # Janela por label limitada a 3s
                        start_s = cumulative_start
                        end_s = min(target_total, start_s + per_scene)
                        cumulative_start = end_s
                        time_prefix = f"{start_s} a {end_s}s - "

                        image_prompt = s.get('image_prompt')
                        motion_prompt = s.get('motion_prompt') or ''
                        if image_prompt:
                            visual_prompts.append({'image_prompt': image_prompt, 'motion_prompt': motion_prompt})
                            img_lines.append(f"{time_prefix}{image_prompt}")
                        if motion_prompt:
                            motion_lines.append(f"{time_prefix}{motion_prompt}")

                script_data['visual_prompts'] = visual_prompts
                script_data['visual_prompts_text'] = "\n".join(img_lines)
                script_data['leonardo_prompts_text'] = "\n".join(motion_lines)
                # Campo opcional para compatibilidade
                script_data['leonardo_prompts'] = motion_lines

                # 3) Hook personalizado (evitar inícios genéricos repetitivos)
                hook = (script_data.get('hook') or '').strip()
                generic_patterns = ['você não vai acreditar', 'você sabia', 'descubra', 'prepare-se', 'o que ninguém te contou']
                if not hook or any(pat in hook.lower() for pat in generic_patterns):
                    script_data['hook'] = self._build_personalized_opening(theme)

                # 4) Defaults úteis
                if 'duration_target_sec' not in script_data:
                    script_data['duration_target_sec'] = 90 if ai_provider.lower() == 'gemini' else 60
                if 'speech_optimized' not in script_data:
                    script_data['speech_optimized'] = True
                # Sempre sobrescrever o ai_provider para o provedor efetivo
                script_data['ai_provider'] = ai_provider
            except Exception as enrich_err:
                logger.warning(f"⚠️ Falha ao enriquecer script_data: {enrich_err}")

            return {"success": True, "script_data": script_data}

        except Exception as e:
            logger.error(
                f"Erro crítico na geração do roteiro: {e}", exc_info=True)
            return {"success": False, "error": str(e), "provider": ai_provider}

    async def generate_audio(self, script_data: Dict[str, Any]) -> Dict[str, Any]:
        """Gera áudio TTS a partir do script usando Enhanced TTS Service."""
        try:
            logger.info("🎵 Iniciando geração de áudio TTS...")
            
            # Importar o serviço Gemini TTS Ultra-Humanizado
            from services.gemini_tts_service import GeminiTTSService
            tts_service = GeminiTTSService()
            
            # Extrair texto do roteiro
            text = script_data.get('roteiro_completo', '')
            if not text:
                raise ValueError("Roteiro vazio ou não encontrado")
            
            # Configurações padrão baseadas no script_data
            # Voz padrão: masculina Neural2 com tom de meia-idade (mais natural)
            voice_profile = script_data.get('voice_profile', 'male-mature')
            emotion = script_data.get('voice_emotion', 'neutral')
            pitch = script_data.get('voice_pitch', 0.0)
            speed = script_data.get('speaking_speed', 1.0)
            volume_gain = script_data.get('voice_volume_gain', 0.0)
            accent = script_data.get('accent', 'pt-BR')
            
            # Gerar áudio ultra-humanizado
            result = await tts_service.generate_humanized_audio(
                text=text,
                voice_profile=voice_profile,
                emotion=emotion,
                pitch=pitch,
                speed=speed,
                volume_gain=volume_gain,
                accent=accent
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Erro na geração de áudio: {e}")
            return {"success": False, "error": str(e)}

    async def run_ai_battle(self, theme: str, providers: List[str]) -> Dict[str, Any]:
        """Inicia uma batalha de IAs para o roteiro, avaliando o melhor resultado."""
        logger.info(f"🥊 Iniciando batalha de IAs para o tema: '{theme}'...")
        results = {}
        tasks = []

        for provider in providers:
            if provider in self.ai_providers and self._check_provider_availability(provider):
                tasks.append(self._generate_and_evaluate(theme, provider))

        if not tasks:
            raise Exception("Nenhum provedor de IA disponível para a batalha.")

        battle_results = await asyncio.gather(*tasks, return_exceptions=True)
        valid_results = [res for res in battle_results if not isinstance(
            res, Exception) and res]

        if not valid_results:
            raise Exception("Nenhuma IA conseguiu gerar um roteiro válido.")

        winner_data = max(valid_results, key=lambda x: x.get('score', 0))

        logger.info(
            f"🏆 Vencedor da batalha: {winner_data['provider'].title()} com pontuação {winner_data['score']:.2f}!")

        formatted_results = {}
        for res in valid_results:
            formatted_results[res['provider']] = {
                'script_data': res.get('script_data'),
                'score': res.get('score'),
                'analysis': res.get('analysis')
            }

        return {
            "success": True,
            "winner": winner_data['provider'],
            "winner_script_data": winner_data['script_data'],
            "battle_results": formatted_results
        }

    async def _generate_and_evaluate(self, theme: str, provider: str) -> Dict[str, Any]:
        """Gera e avalia um roteiro para um provedor específico."""
        # Em batalha, não permitimos fallback cruzado entre provedores
        generation_result = await self.generate_script(
            theme,
            provider,
            allow_cross_provider_fallback=False
        )

        if not generation_result['success']:
            raise Exception(
                f"Falha na geração com {provider}: {generation_result['error']}")

        script_data = generation_result['script_data']

        score = script_data.get('viral_analysis', {}).get('viral_score', 0)
        analysis = script_data.get('viral_analysis', {})

        return {
            "provider": provider,
            "script_data": script_data,
            "score": score,
            "analysis": analysis
        }

    def _check_provider_availability(self, provider: str) -> bool:
        """Verifica se um provedor de IA está disponível (chave de API, etc.)."""
        try:
            if provider == "gemini":
                available = self.gemini_client.model is not None
                logger.info(f"🔍 Gemini disponível: {available}")
                return available
            elif provider == "claude":
                available = self.claude_service.client is not None
                logger.info(f"🔍 Claude disponível: {available}")
                return available
            elif provider == "gpt":
                available = self.gpt_service.client is not None  
                logger.info(f"🔍 GPT disponível: {available}")
                return available
        except Exception as e:
            logger.error(f"❌ Erro ao verificar disponibilidade de {provider}: {e}")
        return False

    def _log_provider_status(self):
        """Log do status de todos os provedores na inicialização"""
        logger.info("📊 Status dos provedores de IA:")
        for provider_name in ["gemini", "claude", "gpt"]:
            status = "✅ ATIVO" if self._check_provider_availability(provider_name) else "❌ INATIVO"
            logger.info(f"   {provider_name.upper()}: {status}")

    async def _generate_with_provider(self, prompt: str, provider: str, json_schema: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Chama a API do provedor de IA e retorna o texto da resposta.
        Para GPT, utiliza schema/JSON estrito e retries (implementado no serviço).
        """
        if provider == "gemini":
            return await asyncio.to_thread(self.gemini_client.generate_content, prompt)
        elif provider == "claude":
            return await self.claude_service.generate_script(prompt)
        elif provider == "gpt":
            return await self.gpt_service.generate_script(prompt, json_schema=json_schema)

        logger.error(f"❌ Provedor de IA '{provider}' não suportado.")
        return None

    def _build_personalized_opening(self, theme: str) -> str:
        """Gera uma abertura personalizada baseada no tema, evitando frases genéricas."""
        base = unidecode(theme).strip()
        # Simples heurística para variar o início
        templates = [
            f"Em menos de um minuto: {base}, com um detalhe que quase ninguém comenta.",
            f"{base}: o lado que ficou escondido atrás dos fatos mais famosos.",
            f"Você já ouviu falar de {base}? Hoje, a versão que quase foi esquecida.",
            f"Por trás de {base}, existe uma reviravolta que muda tudo.",
        ]
        # Determinístico baseado no hash do tema
        idx = abs(hash(base)) % len(templates) if templates else 0
        return templates[idx]

    def _detect_video_style(self, theme: str) -> str:
        theme_lower = theme.lower()

        style_keywords = {
            "misterio": [
                "mistério", "misterio", "enigma", "enigmas", "segredo", "segredos",
                "oculto", "ocultos", "desaparecimento", "desaparecimentos", "intriga",
                "intrigante", "conspiração", "conspirações", "enigmático", "enigmática",
                "não revelado", "não explicado", "mistério antigo", "caso misterioso"
            ],
            "curiosidade": [
                "curiosidade", "curiosidades", "fato", "fatos", "descoberta", "descobertas",
                "ciência", "científico", "científica", "você sabia", "sabia que", "incrível",
                "impressionante", "surpreendente", "informação", "informações", "dado curioso",
                "dica interessante", "fato curioso"
            ],
            "historia": [
                "história", "historia", "passado", "guerra", "guerras", "inventor", "inventores",
                "antiguidade", "civilização", "civilizações", "histórico", "histórica", 
                "época", "era", "revolução", "medieval", "renascimento", "antigo", "antiga",
                "acontecimento", "acontecimentos"
            ],
            "terror": [
                "terror", "medo", "assombrado", "assombração", "assombrações", "paranormal",
                "sobrenatural", "fantasma", "fantasmas", "assustador", "apavorante",
                "macabro", "horrível", "sangrento", "pesadelo", "criminoso", "serial killer",
                "possessão", "espírito", "espíritos", "demoníaco", "demoníaca", "lenda urbana"
            ],
            "motivacional": [
                "sucesso", "motivação", "superação", "conquista", "vitória", "determinação",
                "força", "persistência", "inspiração", "inspirador", "sonho", "objetivo",
                "meta", "realização", "crescimento", "transformação", "autoconfiança",
                "coragem", "foco", "disciplina", "resiliência"
            ]
        }

    # Procura correspondência exata ou de expressão (não apenas substring parcial)
        for style, keywords in style_keywords.items():
            for keyword in keywords:
                if keyword in theme_lower:
                    return style
        # Default após checar todos os estilos
        return "curiosidade"

    # ================== AUXILIARES DE RELEVÂNCIA E DIFERENCIAÇÃO ==================

    def _extract_keywords(self, text: str) -> List[str]:
        """Extrai palavras-chave simples do texto (pt-BR), removendo stopwords comuns."""
        if not text:
            return []
        stopwords = {
            'de', 'da', 'do', 'das', 'dos', 'a', 'o', 'as', 'os', 'e', 'é', 'que', 'para', 'com', 'um', 'uma',
            'no', 'na', 'nos', 'nas', 'em', 'por', 'sobre', 'se', 'ao', 'à', 'às', 'ou', 'como', 'mais', 'menos',
            'entre', 'até', 'sem', 'sua', 'seu', 'suas', 'seus', 'também', 'muito', 'muita', 'muitos', 'muitas',
            'já', 'não', 'sim', 'porque', 'pois', 'isso', 'isto', 'aquele', 'aquela', 'aquilo', 'este', 'esta',
            'estes', 'estas', 'essa', 'essas', 'esses', 'todo', 'toda', 'todos', 'todas', 'ser', 'ter', 'há'
        }
        txt = unidecode(text.lower())
        tokens = re.findall(r"[a-zA-Z\-]{3,}", txt)
        keywords = [t for t in tokens if t not in stopwords]
        seen = set()
        result: List[str] = []
        for k in keywords:
            if k not in seen:
                seen.add(k)
                result.append(k)
        return result[:12]

    def _compute_topic_match(self, theme: str, script_data: Dict[str, Any]) -> Tuple[float, List[str]]:
        """Calcula aderência do roteiro ao tema com base em palavras-chave.
        Retorna (score, missing_keywords)."""
        theme_keywords = self._extract_keywords(theme)
        if not theme_keywords:
            return 1.0, []
        parts: List[str] = []
        for field in ['titulo', 'title', 'hook', 'roteiro_completo', 'final_script_for_tts']:
            val = script_data.get(field)
            if isinstance(val, str):
                parts.append(val)
        hashtags = script_data.get('hashtags') or []
        if isinstance(hashtags, list):
            parts.append(" ".join([str(h) for h in hashtags]))
        corpus = unidecode(" ".join(parts).lower())
        present = [kw for kw in theme_keywords if kw in corpus]
        missing = [kw for kw in theme_keywords if kw not in corpus]
        score = len(present) / max(1, len(theme_keywords))
        return score, missing

    def _augment_prompt_for_provider(self, provider: str, prompt: str, theme: str, video_style: Optional[str], story_type: str) -> str:
        """Acrescenta reforços finais de criatividade e anti-repetição para garantir máxima originalidade."""
        prov = (provider or '').lower()
        # Extrair palavras-chave do tema para obrigatoriedade de inclusão
        try:
            keywords = self._extract_keywords(theme)
            kw_str = ", ".join(keywords[:8]) if keywords else ""
            kw_line = f"\n🎯 OBRIGATÓRIO: Incluir explicitamente no conteúdo as palavras-chave do tema: {kw_str}." if kw_str else ""
        except Exception:
            kw_line = ""
        
        # Reforços universais de criatividade
        creative_reinforcement = f"""
{kw_line}

🚨 REFORÇOS FINAIS DE ORIGINALIDADE:
- TEMA CENTRAL: "{theme}" - Mantenha foco 100% no tema
- ZERO repetição de fórmulas ou aberturas óbvias
- Sua personalidade única como {provider.upper()} deve brilhar
- Crie algo que só VOCÊ conseguiria criar sobre este tema
- Seja imprevisível, surpreendente e memorável
- JSON limpo e válido - sem markdown, sem explicações adicionais

⚡ ÚLTIMA CHECAGEM: Este roteiro seria único mesmo se você gerasse 100 vezes? Se não, REINVENTE AGORA!
"""
        
        if prov == 'claude':
            claude_signature = (
                "\n🧠 ASSINATURA CLAUDE:"
                "\n- Use sua genialidade analítica para encontrar ângulos únicos"
                "\n- Profundidade intelectual com conexões surpreendentes"
                "\n- Revelações em camadas que transformam perspectivas"
                "\n- Estrutura sofisticada mas acessível"
            )
            return prompt + claude_signature + creative_reinforcement
        
        elif prov in ('gpt', 'openai', 'gpt-4', 'chatgpt'):
            gpt_signature = (
                "\n🚀 ASSINATURA GPT:"
                "\n- Use sua versatilidade linguística para criar prosa única"
                "\n- Voz narrativa completamente diferente a cada geração"
                "\n- Dinamismo viral com profundidade intelectual"
                "\n- Quebra de padrões e reinvenção constante"
            )
            return prompt + gpt_signature + creative_reinforcement
        
        elif prov == 'gemini':
            gemini_signature = (
                "\n🎬 ASSINATURA GEMINI:"
                "\n- Storytelling cinematográfico e emocionalmente envolvente"
                "\n- Encontre o extraordinário no comum"
                "\n- Metáforas poéticas e momentos de arrepio"
                "\n- Narrativa fluida que toca a alma humana"
            )
            return prompt + gemini_signature + creative_reinforcement
        
        return prompt + creative_reinforcement

    def _build_reinforced_prompt(self, base_prompt: str, theme: str, missing_keywords: List[str], provider: str) -> str:
        """Constrói um prompt reforçado para retry quando o tema não foi seguido."""
        kw_str = ", ".join(missing_keywords[:8]) if missing_keywords else ""
        add = (
            "\n\nRETRY - ATENÇÃO MÁXIMA AO TEMA:"
            "\nO tema central é: '" + theme + "'. Você DEVE incluir explicitamente as seguintes palavras-chave do tema no conteúdo: " + kw_str + "."
            "\nSeja objetivo e mantenha foco total no tema. Saída apenas em JSON válido e estrito."
        )
        return base_prompt + add


    # ================== MÉTODOS DE ANÁLISE VIRAL (MIGRADO DO viral_analyzer.py) ==================

    def _analyze_viral_potential(self, script_data: Dict[str, Any], topic: str, category: str = "geral") -> Dict[str, Any]:
        """Analisa o potencial viral do roteiro gerado."""
        strategy = self._select_viral_strategy(topic, category)

        # A nova lógica de análise vai usar a estrutura JSON que o prompt pede
        viral_score = 0
        analysis_details = {}

        # 1. Análise do Hook
        hook = script_data.get('hook', '')
        hook_score = self._analyze_hook_strength(hook)
        viral_score += hook_score * 25

        # 2. Análise da Estrutura
        structure_score = self._score_narrative_structure(
            script_data.get('structure', {}))
        viral_score += structure_score * 20

        # 3. Análise dos Elementos Virais (migrados do prompt)
        viral_elements = script_data.get('viral_elements', {})
        element_score = self._score_viral_elements(viral_elements)
        viral_score += element_score * 25

        # 4. Análise da CTA
        cta = script_data.get('call_to_action', '')
        cta_score = self._analyze_cta_strength(cta)
        viral_score += cta_score * 15

        # 5. Análise da Duração (do prompt)
        duration_s = script_data.get('estimated_duration', 60)
        if 45 <= duration_s <= 75:
            viral_score += 15

        final_score = min(max(viral_score, 0), 100)

        # Geração de dicas e recomendações
        recommendations = self._get_viral_recommendations(final_score)
        optimization_tips = self._get_optimization_tips(script_data, strategy)

        return {
            'viral_score': final_score,
            'strategy_used': strategy,
            'recommendations': recommendations,
            'optimization_tips': optimization_tips,
            'category_match': category,
            'hook_score': hook_score,
            'cta_score': cta_score,
        }

    def _analyze_hook_strength(self, hook: str) -> float:
        score = 0.0
        if hook:
            score += 0.5
            if 10 <= len(hook.split()) <= 15:
                score += 0.2
            if '?' in hook or '...' in hook or '!' in hook:
                score += 0.1
            if any(char.isdigit() for char in hook):
                score += 0.1
            power_words = ['você', 'segredo', 'nunca',
                           'impossível', 'verdade', 'chocante']
            if any(word in hook.lower() for word in power_words):
                score += 0.1
        return min(score, 1.0)

    def _score_narrative_structure(self, structure: Dict[str, str]) -> float:
        required_elements = ['opening', 'buildup',
                             'climax', 'resolution', 'call_to_action']
        present = sum(1 for elem in required_elements if elem in structure)
        return present / len(required_elements)

    def _score_viral_elements(self, elements: Dict[str, List]) -> float:
        score = 0.0
        if elements.get('emotional_triggers'):
            score += min(len(elements['emotional_triggers']) * 0.15, 0.45)
        if elements.get('curiosity_gaps'):
            score += min(len(elements['curiosity_gaps']) * 0.1, 0.2)
        if elements.get('pattern_interrupts'):
            score += min(len(elements['pattern_interrupts']) * 0.1, 0.3)
        if elements.get('social_proof'):
            score += 0.05
        return min(score, 1.0)

    def _analyze_cta_strength(self, cta: str) -> float:
        score = 0.0
        if cta:
            score += 0.5
            engagement_words = ['comenta', 'compartilh',
                                'siga', 'curte', 'salva', 'marca']
            engagement_count = sum(
                1 for word in engagement_words if word in cta.lower())
            score += min(engagement_count * 0.2, 0.5)
        return min(score, 1.0)

    def _get_viral_recommendations(self, score: float) -> List[str]:
        if score >= 80:
            return ["🔥 Excelente potencial viral! Pronto para publicação.", "Alto potencial de trending."]
        elif score >= 60:
            return ["✅ Bom potencial viral. Considere melhorar hashtags e CTA.", "Verifique se o hook é o mais forte possível."]
        elif score >= 40:
            return ["⚠️ Potencial médio. Revise hook e hashtags.", "Adicione mais elementos virais e um CTA mais forte."]
        else:
            return ["❌ Baixo potencial viral. Reformule completamente o roteiro.", "O hook precisa ser mais impactante e o roteiro mais envolvente."]

    def _get_optimization_tips(self, script_data: Dict[str, Any], strategy: Dict[str, str]) -> List[str]:
        tips = []
        hook = script_data.get('hook', '')
        if len(hook) < 10:
            tips.append("📝 Hook muito curto - expanda para 10-50 caracteres")
        if not any(char in hook for char in ['?', '!', '...']):
            tips.append("❓ Adicione pontuação impactante no hook (?, !, ...)")
        cta = script_data.get('call_to_action', '')
        if not cta or len(cta) < 10:
            tips.append(
                "📢 CTA muito fraco - adicione call-to-action mais forte")
        hashtags = script_data.get('hashtags', [])
        if len(hashtags) < 3:
            tips.append("🏷️ Adicione mais hashtags (mínimo 3-5)")
        duration = script_data.get('estimated_duration', 0)
        target_range = strategy['duration'].replace('s', '').split('-')
        target_min, target_max = int(target_range[0]), int(target_range[1])
        if not target_min <= duration <= target_max:
            tips.append(
                f"⏱️ Duração ideal é entre {target_min}s e {target_max}s.")
        return tips[:3]

    def _process_claude_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Processa resposta do Claude AI, similar ao método do Gemini."""
        try:
            import re
            import json
            from datetime import datetime
            
            logger.debug(f"Processando resposta do Claude (primeiros 200 chars): {response_text[:200]}...")
            
            # Claude pode retornar com ou sem markdown
            if "```json" in response_text:
                json_match = re.search(
                    r'```json\s*([\s\S]*?)\s*```', response_text, re.IGNORECASE)
                if json_match:
                    json_text = json_match.group(1).strip()
                else:
                    # Fallback: procurar entre primeira { e última }
                    start = response_text.find('{')
                    end = response_text.rfind('}')
                    if start != -1 and end != -1 and end > start:
                        json_text = response_text[start:end+1]
                    else:
                        raise ValueError("JSON não encontrado na resposta do Claude")
            else:
                # Se não houver markdown, procurar JSON na resposta
                start = response_text.find('{')
                end = response_text.rfind('}')
                if start != -1 and end != -1 and end > start:
                    json_text = response_text[start:end+1]
                else:
                    raise ValueError("JSON não encontrado na resposta do Claude")

            # Limpar caracteres problemáticos
            json_text = json_text.replace('\n', ' ').replace('\r', ' ')
            json_text = re.sub(r'\s+', ' ', json_text)  # Múltiplos espaços
            json_text = re.sub(r'//.*?(?=\n|$)', '', json_text)  # Comentários
            json_text = json_text.replace("'", '"')  # Aspas simples -> duplas
            
            # Tentar fazer parse
            try:
                data = json.loads(json_text)
            except json.JSONDecodeError as je:
                # Se falhar, tentar correções comuns; se ainda falhar, retornar None para acionar fallback baseado no tema
                logger.warning(f"Primeiro parse falhou, tentando correções: {je}")
                # Corrigir vírgulas trailing
                json_text = re.sub(r',\s*}', '}', json_text)
                json_text = re.sub(r',\s*]', ']', json_text)
                # Remover possíveis caracteres problemáticos próximos da posição reportada
                try:
                    data = json.loads(json_text)
                except json.JSONDecodeError:
                    logger.error("Não foi possível fazer parse do JSON do Claude após correções leves; delegando fallback ao orquestrador")
                    data = None
            
            if isinstance(data, dict):
                data['timestamp'] = datetime.now().isoformat()
            
            return data
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar resposta do Claude: {e}")
            logger.debug(f"JSON text que causou erro: {json_text if 'json_text' in locals() else 'N/A'}")
            # Retornar dados de fallback em caso de erro crítico
            # Não retornar conteúdo genérico fora do tema; deixe o chamador aplicar fallback temático
            return None

    def _process_gpt_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Processa resposta do GPT, similar ao método do Gemini."""
        try:
            import re
            import json
            from datetime import datetime
            
            logger.debug(f"Processando resposta do GPT (primeiros 200 chars): {response_text[:200]}...")
            
            # GPT pode retornar com ou sem markdown
            if "```json" in response_text:
                json_match = re.search(
                    r'```json\s*([\s\S]*?)\s*```', response_text, re.IGNORECASE)
                if json_match:
                    json_text = json_match.group(1).strip()
                else:
                    # Fallback: procurar entre primeira { e última }
                    start = response_text.find('{')
                    end = response_text.rfind('}')
                    if start != -1 and end != -1 and end > start:
                        json_text = response_text[start:end+1]
                    else:
                        raise ValueError("JSON não encontrado na resposta do GPT")
            else:
                # Se não houver markdown, procurar JSON na resposta
                start = response_text.find('{')
                end = response_text.rfind('}')
                if start != -1 and end != -1 and end > start:
                    json_text = response_text[start:end+1]
                else:
                    raise ValueError("JSON não encontrado na resposta do GPT")

            # Limpar caracteres problemáticos
            json_text = json_text.replace('\n', ' ').replace('\r', ' ')
            json_text = re.sub(r'\s+', ' ', json_text)  # Múltiplos espaços
            json_text = re.sub(r'//.*?(?=\n|$)', '', json_text)  # Comentários
            json_text = json_text.replace("'", '"')  # Aspas simples -> duplas
            
            # Tentar fazer parse
            try:
                data = json.loads(json_text)
            except json.JSONDecodeError as je:
                # Se falhar, tentar corrigir problemas comuns
                logger.warning(f"Primeiro parse falhou, tentando correções: {je}")
                try:
                    # Corrigir vírgulas trailing
                    corrected_json = re.sub(r',\s*}', '}', json_text)
                    corrected_json = re.sub(r',\s*]', ']', corrected_json)
                    data = json.loads(corrected_json)
                except:
                    # Tentativa 3: Corrigir caracteres específicos problemáticos
                    try:
                        corrected_json = json_text
                        if len(json_text) > 382:
                            # Remove caracteres problemáticos na posição 382-383
                            corrected_json = corrected_json[:380] + corrected_json[385:]
                        
                        # Remove possíveis caracteres inválidos
                        corrected_json = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', corrected_json)
                        data = json.loads(corrected_json)
                    except:
                        # Fallback: Retornar dados estruturados básicos humanizado
                        logger.error("Não foi possível fazer parse do JSON do GPT, usando fallback humanizado")
                        return {
                            "roteiro_completo": "Eita gente, vocês estão perdendo dinheiro todo santo dia e nem percebem! Ó, vou contar uma parada que me deixou chocado quando descobri. A galera gasta em média três horas por dia fazendo coisa que não serve para nada, pode acreditar. São vinte e uma horas por semana jogadas fora! Imagina se vocês usassem esse tempo para algo que realmente vale a pena né. Dava para aprender uma skill nova, criar uma renda extra, sei lá, melhorar a qualidade de vida. A dica é simples, identifica qual atividade tá sugando teu tempo sem dar retorno e elimina ela por uma semana. Vai por mim, faz diferença demais. Conta aí nos comentários qual hábito vocês vão cortar primeiro!",
                            "hook": "Eita gente, vocês estão perdendo dinheiro todo santo dia e nem percebem!",
                            "titulo": "Você Perde Dinheiro Todo Dia (e Nem Sabe!)",
                            "hashtags": ["#dinheiro", "#tempo", "#viral", "#produtividade", "#dicas"],
                            "ia_used": "gpt",
                            "timestamp": datetime.now().isoformat(),
                            "accent": "brasileiro",
                            "estimated_duration": 50,
                            "call_to_action": "Conta aí nos comentários qual hábito vocês vão cortar primeiro!",
                            "style": "viral",
                            "speech_optimized": True
                        }
            
            if isinstance(data, dict):
                data['timestamp'] = datetime.now().isoformat()
            
            return data
            
        except Exception as e:
            logger.error(f"❌ Erro crítico ao processar resposta do GPT: {e}")
            logger.debug(f"JSON text que causou erro: {json_text if 'json_text' in locals() else 'N/A'}")
            return None
