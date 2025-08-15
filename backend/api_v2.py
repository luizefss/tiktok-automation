# /var/www/tiktok-automation/backend/api_v2.py

from config_manager import get_config

from ai_orchestrator import AIOrchestrator
from trending_content_system import TrendingContentSystem
from visual_effects_system import VisualEffectsSystem
from services.image_generator import ImageGeneratorService
from services.advanced_image_service import AdvancedImageService
from services.elevenlabs_tts import ElevenLabsTTS
from services.prompt_optimizer import PromptOptimizer
from content_pipeline_optimized import ContentPipelineOptimized, ContentRequest, ContentResult
import os
import logging
import asyncio
import sys
import json
import time
import hashlib
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
from functools import wraps
from threading import Lock

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
import sys
import os
import json
import hashlib
import time
import asyncio
import logging

# --- FIX: Adiciona o diretório 'backend' ao sys.path para imports locais ---
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))
# --- FIM DO FIX ---


# ===== CONFIGURAÇÃO DE LOGGING =====
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('api_v2.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ===== CONFIGURAÇÃO DE AMBIENTE E APLICAÇÃO =====
config = get_config()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
app.config['CORS_HEADERS'] = 'Content-Type'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")
cache = Cache(app, config={'CACHE_TYPE': 'simple'})
limiter = Limiter(app=app, key_func=get_remote_address)

# ===== INICIALIZAÇÃO DOS SISTEMAS =====
pipeline = ContentPipelineOptimized()
trending_system = TrendingContentSystem()
ai_orchestrator = AIOrchestrator()
image_generator = ImageGeneratorService()
advanced_image_service = AdvancedImageService()
elevenlabs_tts = ElevenLabsTTS()
prompt_optimizer = PromptOptimizer()
video_builder = VisualEffectsSystem()

# ===== DATACLASSES PARA TIPAGEM (se necessário, movido para um arquivo) =====


@dataclass
class SystemStatus:
    automation_running: bool
    pipeline_running: bool
    ai_accuracy: float
    viral_rate: float
    content_quality: float
    system_health: str
    total_revenue: int
    monthly_growth: float

# ===== DECORADORES ÚTEIS =====


def validate_json(*required_fields):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return jsonify({"error": "Content-Type deve ser application/json"}), 400
            data = request.get_json()
            missing_fields = [
                field for field in required_fields if field not in data]
            if missing_fields:
                return jsonify({"error": f"Campos obrigatórios ausentes: {', '.join(missing_fields)}"}), 400
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def handle_errors(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Erro em {f.__name__}: {str(e)}", exc_info=True)
            return jsonify({"error": "Erro interno do servidor", "message": str(e)}), 500
    return decorated_function

# ===== ENDPOINTS DA API =====

# ===== CONTROLE DE IDEMPOTÊNCIA/LOCK PARA TAREFAS PESADAS =====
# Evita que o mesmo payload gere múltiplos vídeos quando o frontend re-tenta
# a requisição por timeout/erros transitórios.

# key -> {'started_at': float}
_ACTIVE_VIDEO_JOBS: dict[str, dict] = {}
# key -> {'finished_at': float, 'result': dict}
_COMPLETED_VIDEO_JOBS: dict[str, dict] = {}
_JOBS_LOCK = Lock()
_JOB_TTL_SECONDS = 15 * 60  # manter resultados por 15 minutos


def _cleanup_old_jobs(now: float | None = None):
    """Remove registros antigos para não crescer indefinidamente."""
    t = now or time.time()
    # Limpeza de completados
    to_del = [k for k, v in _COMPLETED_VIDEO_JOBS.items()
              if (t - v.get('finished_at', t)) > _JOB_TTL_SECONDS]
    for k in to_del:
        _COMPLETED_VIDEO_JOBS.pop(k, None)
    # Limpeza de ativos fantasmas (mais de 2h)
    to_del_active = [k for k, v in _ACTIVE_VIDEO_JOBS.items()
                     if (t - v.get('started_at', t)) > 2 * 60 * 60]
    for k in to_del_active:
        _ACTIVE_VIDEO_JOBS.pop(k, None)


def _stable_hash_for_video_request(data: dict) -> str:
    """Gera uma chave estável baseada nos campos relevantes do payload.
    Considera audio_path, lista de imagens (ordem importa), script e algumas settings.
    """
    try:
        audio_path = data.get('audio_path') or ''
        images = data.get('images') or []
        script = data.get('script') or data.get('storyboard') or ''
        settings = data.get('settings') or {}
        # Selecionar subset de settings que afetam saída
        settings_subset = {
            'subtitle_style': settings.get('subtitle_style'),
            'background_music': settings.get('background_music') or settings.get('background_music_category'),
            'transitions': settings.get('transitions'),
            'render_preset': settings.get('render_preset'),
        }
        payload = {
            'audio_path': audio_path,
            'images': images,
            'script': script if isinstance(script, str) else json.dumps(script, ensure_ascii=False, sort_keys=True),
            'settings': settings_subset,
        }
        raw = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode('utf-8')
        return hashlib.sha256(raw).hexdigest()
    except Exception as e:
        logger.warning(f"⚠️ Falha ao gerar chave estável do job: {e}")
        # fallback randômico para não quebrar fluxo
        return hashlib.sha256(str(time.time()).encode()).hexdigest()


@app.route('/api/health', methods=['GET'])
@handle_errors
def health_check():
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat(), "version": "2.0"})


@app.route('/api/status', methods=['GET'])
@handle_errors
@cache.cached(timeout=10)
def get_status():
    status = SystemStatus(
        automation_running=True,  # Exemplo
        pipeline_running=False,  # Exemplo
        ai_accuracy=94.2,
        viral_rate=28.5,
        content_quality=91.8,
        system_health="good",
        total_revenue=71250,
        monthly_growth=23.4
    )
    return jsonify(asdict(status))


@app.route('/api/trending/topics', methods=['GET'])
@handle_errors
@cache.cached(timeout=1800)
def get_trending_topics():
    try:
        trending_topics = trending_system.obter_trending_com_filtros()
        formatted_topics = [{
            "id": f"{t.get('source')}_{hash(t.get('topic'))}",
            "topic": t.get('topic'),
            "platform": t.get('source', 'desconhecido'),
            "category": t.get('categoria'),
            "viralPotential": int(t.get('viral_score', 0)),
            "updated_at": t.get('timestamp')
        } for t in trending_topics]
        return jsonify({"topics": formatted_topics, "count": len(formatted_topics)})
    except Exception as e:
        logger.error(f"Erro ao obter trending topics: {e}")
        return jsonify({"error": "Falha ao buscar tendências", "topics": []}), 500


@app.route('/api/trending/analyze', methods=['POST'])
@handle_errors
@validate_json('topic')
def analyze_trending():
    topic = request.get_json().get('topic')
    avaliacao = trending_system.avaliar_potencial_viral(topic)
    return jsonify(avaliacao)

# ===== ENDPOINTS DO PRODUCTION STUDIO (MODULAR) =====


@app.route('/api/production/generate-script', methods=['POST'])
@handle_errors
@limiter.limit("10 per minute")
def generate_script_only_endpoint():
    try:
        if not request.is_json:
            logger.error("Request não é JSON")
            return jsonify({"error": "Content-Type deve ser application/json"}), 400

        data = request.get_json()
        logger.info(f"Dados recebidos para generate-script: {data}")

        # Validação flexível
        if not data:
            return jsonify({"error": "Nenhum dado enviado"}), 400

        theme = data.get('theme')
        ai_provider = data.get('ai_provider') or data.get(
            'provider')  # Aceita ambos os campos
        # Novo campo para tipo de história
        story_type = data.get('story_type', 'curiosidade')

        if not theme:
            return jsonify({"error": "Campo 'theme' é obrigatório"}), 400
        if not ai_provider:
            return jsonify({"error": "Campo 'ai_provider' ou 'provider' é obrigatório"}), 400

        logger.info(
            f"Gerando script - Theme: {theme}, Provider: {ai_provider}, Story Type: {story_type}")

        logger.info(f"🎬 DEBUG API - Tema: {theme}")
        logger.info(f"🎬 DEBUG API - AI: {ai_provider}")
        logger.info(f"🎬 DEBUG API - Story Type: {story_type}")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(ai_orchestrator.generate_script(
                theme=theme,
                ai_provider=ai_provider,
                video_style=data.get('video_style'),
                story_type=story_type  # Passar o tipo de história
            ))

            logger.info(
                f"🎬 DEBUG API - Result success: {result.get('success')}")
            logger.info(f"🎬 DEBUG API - Result keys: {list(result.keys())}")

            if result.get('success'):
                script_data = result['script_data']
                logger.info(
                    f"🎬 DEBUG API - Script data keys: {list(script_data.keys())}")
                logger.info(
                    f"🎬 DEBUG API - Roteiro chars: {len(script_data.get('roteiro_completo', ''))}")
                logger.info(
                    f"🎬 DEBUG API - Visual prompts: {len(script_data.get('visual_prompts', []))}")
                logger.info(
                    f"🎬 DEBUG API - Leonardo prompts: {len(script_data.get('leonardo_prompts', []))}")
                logger.info(
                    f"🎬 DEBUG API - AI provider: {script_data.get('ai_provider', 'N/A')}")
        finally:
            loop.close()

        if result.get('success'):
            # Pós-processar para garantir que o ROTEIRO (texto) venha primeiro
            script_data = result.get('script_data', {}) or {}

            # 1) Garantir roteiro_completo (texto contínuo)
            roteiro_text = (
                script_data.get('roteiro_completo') or
                script_data.get('final_script_for_tts') or
                script_data.get('script') or
                script_data.get('content') or
                ''
            )

            if not roteiro_text:
                # Fallback: montar texto puro a partir das cenas (apenas narrativa/legenda, SEM tempos)
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

            # 2) Derivar prompts das cenas (para uso posterior na etapa de imagens)
            visual_prompts = []
            visual_prompts_text = ''
            leonardo_prompts_text = ''
            scenes = script_data.get('scenes') or []
            if isinstance(scenes, list) and scenes:
                img_lines = []
                motion_lines = []
                # Preparar cálculo cumulativo quando não houver tempos
                target_total = int(script_data.get('duration_target_sec') or 60)
                default_dur = max(1, int(round(target_total / max(1, len(scenes)))))
                cumulative_start = 0
                for s in scenes:
                    if not isinstance(s, dict):
                        continue
                    # Determinar janela de tempo start→end
                    try:
                        if s.get('t_start') is not None and s.get('t_end') is not None:
                            start_s = int(round(float(s.get('t_start'))))
                            end_s = int(round(float(s.get('t_end'))))
                            cumulative_start = end_s
                        else:
                            dur_this = s.get('duration')
                            if dur_this is not None:
                                dur_this = int(round(float(dur_this)))
                            else:
                                dur_this = default_dur
                            start_s = cumulative_start
                            end_s = cumulative_start + max(1, dur_this)
                            cumulative_start = end_s
                    except Exception:
                        start_s = cumulative_start
                        end_s = cumulative_start + default_dur
                        cumulative_start = end_s

                    time_prefix = f"{start_s} a {end_s}s - "

                    if s.get('image_prompt'):
                        visual_prompts.append({
                            'image_prompt': s.get('image_prompt'),
                            'motion_prompt': s.get('motion_prompt') or ''
                        })
                        img_lines.append(f"{time_prefix}{s.get('image_prompt')}")
                    if s.get('motion_prompt'):
                        motion_lines.append(f"{time_prefix}{s.get('motion_prompt')}")
                visual_prompts_text = "\n".join(img_lines)
                leonardo_prompts_text = "\n".join(motion_lines)

            # 3) Montar payload final priorizando o roteiro textual
            enriched = {
                **script_data,
                'roteiro_completo': roteiro_text,
                'visual_prompts': visual_prompts or script_data.get('visual_prompts') or [],
                'visual_prompts_text': visual_prompts_text,
                'leonardo_prompts_text': leonardo_prompts_text,
                'ai_provider': script_data.get('ai_provider') or ai_provider
            }

            return jsonify({"success": True, "data": enriched})
        else:
            return jsonify({"success": False, "error": result.get('error', 'Erro desconhecido')}), 500

    except Exception as e:
        logger.error(
            f"Erro no endpoint generate-script: {str(e)}", exc_info=True)
        return jsonify({"error": "Erro interno", "message": str(e)}), 500


@app.route('/api/production/story-types', methods=['GET'])
@handle_errors
def get_story_types():
    """Retorna todos os tipos de história disponíveis"""
    try:
        from humanized_prompts import HumanizedPrompts

        prompts = HumanizedPrompts()
        story_types = prompts.get_available_story_types()

        return jsonify({
            "success": True,
            "story_types": story_types,
            "count": len(story_types)
        })

    except Exception as e:
        logger.error(f"Erro ao buscar tipos de história: {e}")
        return jsonify({
            "success": False,
            "error": "Erro ao carregar tipos de história",
            "message": str(e)
        }), 500


@app.route('/api/production/ai-battle', methods=['POST'])
@handle_errors
@limiter.limit("5 per minute")
def ai_battle_production():
    try:
        if not request.is_json:
            logger.error("Request não é JSON")
            return jsonify({"error": "Content-Type deve ser application/json"}), 400

        data = request.get_json()
        logger.info(f"Dados recebidos para AI battle: {data}")

        # Validação flexível
        if not data:
            return jsonify({"error": "Nenhum dado enviado"}), 400

        theme = data.get('theme')
        providers = data.get('providers')
        provider = data.get('provider')  # Campo único enviado pelo frontend

        if not theme:
            return jsonify({"error": "Campo 'theme' é obrigatório"}), 400

        # Se não tem providers array, mas tem provider único, criar array
        if not providers and provider:
            # Mapear provider único para array com as 3 IAs
            providers = ["gemini", "claude", "gpt"]
        elif not providers:
            return jsonify({"error": "Campo 'providers' ou 'provider' é obrigatório"}), 400

        logger.info(
            f"Iniciando AI battle - Theme: {theme}, Providers: {providers}")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(ai_orchestrator.run_ai_battle(
                theme=theme,
                providers=providers
            ))
        finally:
            loop.close()

        if result.get('success'):
            return jsonify({"success": True, "data": result})
        else:
            return jsonify({"success": False, "error": result.get('error', 'Erro desconhecido')}), 500

    except Exception as e:
        logger.error(f"Erro no endpoint ai-battle: {str(e)}", exc_info=True)
        return jsonify({"error": "Erro interno", "message": str(e)}), 500


@app.route('/api/production/generate-audio', methods=['POST'])
@handle_errors
@limiter.limit("10 per minute")
def generate_audio_enhanced_endpoint():
    """Endpoint aprimorado para geração de áudio TTS"""
    data = request.get_json()

    # Parâmetros obrigatórios
    text = data.get('text', '')
    if not text:
        return jsonify({"success": False, "error": "Texto é obrigatório"}), 400

    # Parâmetros opcionais com valores padrão
    # mystery, tech, story, tutorial, comedy
    voice_profile = data.get('voice_profile', None)
    emotion = data.get('emotion', 'neutral')
    pitch = float(data.get('pitch', 0.0))
    speed = float(data.get('speed', 1.0))
    volume_gain = float(data.get('volume_gain', 0.0))
    accent = data.get('accent', 'pt-BR')

    logger.info(
        f"🎵 Gerando áudio TTS - Perfil: {voice_profile or 'automático'}, Velocidade: {speed}x")

    # Importar e usar o serviço TTS Otimizado (seleção automática)
    from services.optimized_tts_service import OptimizedTTSService
    tts_service = OptimizedTTSService()

    # Gerar áudio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(
            tts_service.generate_optimized_audio(
                text=text,
                voice_profile=voice_profile,
                custom_speed=speed
            )
        )
    finally:
        loop.close()

    if result.get('success'):
        return jsonify({
            "success": True,
            "audio_url": result.get('audio_url'),
            "duration": result.get('duration', 0),
            "message": result.get('message', 'Áudio gerado com sucesso')
        })
    else:
        error_msg = result.get('error', 'Falha na geração do áudio')
        logger.error(f"❌ Erro na geração de áudio: {error_msg}")
        return jsonify({"success": False, "error": error_msg}), 500


# ===== ENDPOINT DE IMAGENS OTIMIZADAS =====

@app.route('/api/production/generate-optimized-images', methods=['POST'])
@handle_errors
@validate_json('script_data')
@limiter.limit("3 per minute")
def generate_optimized_images_endpoint():
    """Endpoint para gerar imagens otimizadas para TikTok"""
    try:
        from services.optimized_image_generator import OptimizedImageGenerator

        data = request.get_json()
        script_data = data['script_data']
        # Opcional - será auto-detectado
        visual_style = data.get('visual_style')

        logger.info(
            f"🎨 Gerando imagens otimizadas para {len(script_data)} cenas")

        # Inicializar gerador otimizado
        optimized_generator = OptimizedImageGenerator()

        # Executar geração async
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                optimized_generator.generate_optimized_images(
                    script_data=script_data,
                    visual_style=visual_style
                )
            )
        finally:
            loop.close()

        if result.get('success'):
            return jsonify({
                "success": True,
                "images": result.get('images'),
                "style": result.get('style'),
                "generated_count": result.get('generated_count'),
                "total_scenes": result.get('total_scenes'),
                "message": f"Imagens otimizadas geradas com estilo {result.get('style')}"
            })
        else:
            error_msg = result.get('error', 'Falha na geração de imagens')
            logger.error(f"❌ Erro na geração otimizada: {error_msg}")
            return jsonify({"success": False, "error": error_msg}), 500

    except Exception as e:
        logger.error(f"❌ Erro no endpoint de imagens otimizadas: {e}")
        return jsonify({"success": False, "error": "Erro interno do servidor"}), 500

# ===== ENDPOINT DE ÁUDIO COM CONTROLES MANUAIS =====


@app.route('/api/production/generate-manual-audio', methods=['POST'])
@handle_errors
@validate_json('text')
@limiter.limit("5 per minute")
def generate_manual_audio_endpoint():
    """Endpoint para gerar áudio com controles manuais"""
    try:
        from services.enhanced_tts_service import EnhancedTTSService

        data = request.get_json()
        text = data['text']
        config = data.get('config', {})

        logger.info(
            f"🎤 Gerando áudio manual: {config.get('service', 'google')}")

        # Inicializar serviço aprimorado
        enhanced_tts = EnhancedTTSService()

        # Executar geração async
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                enhanced_tts.generate_with_manual_controls(
                    text=text,
                    config=config
                )
            )
        finally:
            loop.close()

        if result.get('success'):
            return jsonify({
                "success": True,
                "audio_url": result.get('audio_url'),
                "duration": result.get('duration'),
                "service": result.get('service'),
                "model": result.get('model'),
                "voice": result.get('voice'),
                "message": result.get('message')
            })
        else:
            error_msg = result.get('error', 'Falha na geração manual')
            logger.error(f"❌ Erro na geração manual: {error_msg}")
            return jsonify({"success": False, "error": error_msg}), 500

    except Exception as e:
        logger.error(f"❌ Erro no endpoint manual: {e}")
        return jsonify({"success": False, "error": "Erro interno do servidor"}), 500

# ===== ENDPOINT DE ROTEIROS HUMANIZADOS =====


@app.route('/api/production/generate-humanized-script', methods=['POST'])
@handle_errors
@validate_json('topic')
@limiter.limit("3 per minute")
def generate_humanized_script_endpoint():
    """Endpoint para gerar roteiros humanizados com pausas e emoção"""
    try:
        from services.humanized_script_generator import HumanizedScriptGenerator

        data = request.get_json()
        topic = data['topic']
        tone = data.get('tone', 'enthusiastic')
        duration = data.get('duration', 60)
        ai_model = data.get('ai_model', 'claude')

        logger.info(f"📝 Gerando roteiro humanizado: {topic} ({ai_model})")

        # Inicializar gerador
        script_generator = HumanizedScriptGenerator()

        # Executar geração async
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                script_generator.generate_humanized_script(
                    topic=topic,
                    tone=tone,
                    duration=duration,
                    ai_model=ai_model
                )
            )
        finally:
            loop.close()

        if result.get('success'):
            return jsonify({
                "success": True,
                "script": result.get('script'),
                "processed_script": result.get('processed_script'),
                "analysis": result.get('analysis'),
                "ai_model": result.get('ai_model'),
                "estimated_duration": result.get('estimated_duration'),
                "word_count": result.get('word_count'),
                "markers_found": result.get('markers_found'),
                "message": f"Roteiro humanizado gerado com {ai_model}"
            })
        else:
            error_msg = result.get('error', 'Falha na geração do roteiro')
            logger.error(f"❌ Erro no roteiro humanizado: {error_msg}")
            return jsonify({"success": False, "error": error_msg}), 500

    except Exception as e:
        logger.error(f"❌ Erro no endpoint de roteiro: {e}")
        return jsonify({"success": False, "error": "Erro interno do servidor"}), 500

# ===== ENDPOINT DE CRIAÇÃO DE VÍDEO TIKTOK COMPLETO =====


@app.route('/api/production/create-tiktok-video', methods=['POST'])
@handle_errors
@validate_json('audio_path', 'images', 'script_data')
@limiter.limit("1 per 2 minutes")
def create_tiktok_video_endpoint():
    """Endpoint para criar vídeo TikTok completo com legendas e animações"""
    try:
        from services.video_builder import TikTokVideoBuilder

        data = request.get_json()
        audio_path = data['audio_path']
        images = data['images']
        script_data = data['script_data']
        settings = data.get('settings', {})

        logger.info(
            f"🎬 Criando vídeo TikTok: {len(images)} cenas, áudio: {audio_path}")

        # Inicializar builder
        video_builder = TikTokVideoBuilder()

        # Executar criação async
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                video_builder.create_tiktok_video(
                    audio_path=audio_path,
                    images=images,
                    script_data=script_data,
                    settings=settings
                )
            )
        finally:
            loop.close()

        if result.get('success'):
            return jsonify({
                "success": True,
                "video_url": result.get('video_url'),
                "video_path": result.get('video_path'),
                "duration": result.get('duration'),
                "scenes": result.get('scenes'),
                "file_size": result.get('file_size'),
                "resolution": result.get('resolution'),
                "subtitle_style": result.get('subtitle_style'),
                "message": "Vídeo TikTok criado com legendas e animações"
            })
        else:
            error_msg = result.get('error', 'Falha na criação do vídeo')
            logger.error(f"❌ Erro na criação do vídeo TikTok: {error_msg}")
            return jsonify({"success": False, "error": error_msg}), 500

    except Exception as e:
        logger.error(f"❌ Erro no endpoint de vídeo TikTok: {e}")
        return jsonify({"success": False, "error": "Erro interno do servidor"}), 500

# ===== ENDPOINTS SIMPLIFICADOS PARA CORREÇÕES =====


@app.route('/api/production/generate-natural-audio', methods=['POST'])
@handle_errors
@validate_json('text')
@limiter.limit("10 per minute")
def generate_natural_audio_endpoint():
    """Endpoint simplificado para áudio mais natural"""
    try:
        from quick_fixes import QuickAudioFixer

        data = request.get_json()
        text = data['text']
        adjustments = data.get('adjustments', {})

        logger.info(f"🎤 Gerando áudio natural com ajustes: {adjustments}")

        # Usar correção rápida
        audio_fixer = QuickAudioFixer()

        # Executar geração async
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                audio_fixer.generate_natural_audio(text, adjustments)
            )
        finally:
            loop.close()

        if result.get('success'):
            return jsonify({
                "success": True,
                "audio_url": result.get('audio_url'),
                "duration": result.get('duration'),
                "adjustments_applied": adjustments,
                "message": "Áudio natural gerado"
            })
        else:
            return jsonify({"success": False, "error": result.get('error')}), 500

    except Exception as e:
        logger.error(f"❌ Erro no áudio natural: {e}")
        return jsonify({"success": False, "error": "Erro interno"}), 500


@app.route('/api/production/generate-simple-images', methods=['POST'])
@handle_errors
@validate_json('sentences')
@limiter.limit("5 per minute")
def generate_simple_images_endpoint():
    """Endpoint simplificado para geração de imagens"""
    try:
        from quick_fixes import QuickImageFixer

        data = request.get_json()
        sentences = data['sentences']
        style = data.get('style', 'cinematic')

        logger.info(f"🖼️ Gerando imagens simples: {len(sentences)} frases")

        # Usar correção rápida
        image_fixer = QuickImageFixer()

        # Executar geração async
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                image_fixer.generate_simple_images(sentences, style)
            )
        finally:
            loop.close()

        if result.get('success'):
            return jsonify({
                "success": True,
                "images": result.get('images'),
                "generated_count": result.get('generated_count'),
                "style": style,
                "message": f"{result.get('generated_count')} imagens geradas"
            })
        else:
            return jsonify({"success": False, "error": result.get('error')}), 500

    except Exception as e:
        logger.error(f"❌ Erro nas imagens simples: {e}")
        return jsonify({"success": False, "error": "Erro interno"}), 500


@app.route('/api/production/generate-preferred-audio', methods=['POST'])
@handle_errors
@validate_json('text')
@limiter.limit("10 per minute")
def generate_preferred_audio_endpoint():
    """Endpoint para usar o tom de voz que você gostou"""
    try:
        from services.optimized_tts_service import OptimizedTTSService

        data = request.get_json()
        text = data['text']

        logger.info(f"🎤 Gerando áudio com tom preferido")

        # Usar serviço otimizado com configuração preferida
        tts_service = OptimizedTTSService()

        # Forçar uso da configuração "preferred"
        original_method = tts_service._analyze_content_emotion
        tts_service._analyze_content_emotion = lambda x: "preferred"

        # Executar geração async
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                tts_service.generate_optimized_audio(text=text)
            )
        finally:
            loop.close()
            tts_service._analyze_content_emotion = original_method  # Restaurar método

        if result.get('success'):
            return jsonify({
                "success": True,
                "audio_url": result.get('audio_url'),
                "duration": result.get('duration'),
                "voice_type": "preferred_tone",
                "message": "Áudio gerado com seu tom preferido!"
            })
        else:
            return jsonify({"success": False, "error": result.get('error')}), 500

    except Exception as e:
        logger.error(f"❌ Erro no áudio preferido: {e}")
        return jsonify({"success": False, "error": "Erro interno"}), 500

# ===== ROTAS PARA SERVIR ARQUIVOS DE MÍDIA =====


@app.route('/media/audio/<filename>')
def serve_audio(filename):
    """Serve arquivos de áudio gerados"""
    try:
        media_dir = config.AUDIO_DIR
        return send_from_directory(str(media_dir), filename)
    except Exception as e:
        logger.error(f"Erro ao servir arquivo de áudio {filename}: {e}")
        return jsonify({"error": "Arquivo não encontrado"}), 404


@app.route('/media/images/<filename>')
def serve_image(filename):
    """Serve arquivos de imagem gerados"""
    try:
        media_dir = config.IMAGES_DIR
        return send_from_directory(str(media_dir), filename)
    except Exception as e:
        logger.error(f"Erro ao servir arquivo de imagem {filename}: {e}")
        return jsonify({"error": "Arquivo não encontrado"}), 404


@app.route('/media/videos/<filename>')
def serve_video(filename):
    """Serve arquivos de vídeo gerados"""
    try:
        media_dir = config.VIDEO_DIR
        return send_from_directory(str(media_dir), filename)
    except Exception as e:
        logger.error(f"Erro ao servir arquivo de vídeo {filename}: {e}")
        return jsonify({"error": "Arquivo não encontrado"}), 404


@app.route('/api/production/generate-images', methods=['POST'])
@handle_errors
@validate_json('script_data', 'visual_style')
@limiter.limit("3 per minute")
def generate_images_only_endpoint():
    """Endpoint melhorado para geração de imagens com sistema de cache inteligente"""
    try:
        data = request.get_json()
        script_data = data['script_data']
        visual_style = data['visual_style']
        # Normalizar provider e aceitar alias 'dalle' -> 'openai' (DALL·E 3)
        provider = data.get('image_provider') or data.get('provider') or 'hybrid'
        if isinstance(provider, str) and provider.lower() == 'dalle':
            provider = 'openai'
        force_regenerate = data.get('force_regenerate', False)

        logger.info(
            f"🎨 Iniciando geração de imagens - Estilo: {visual_style} | Provedor: {provider}")

        # Criar hash único para cache baseado no conteúdo do script + estilo
        import hashlib
        import json

        # Extrair elementos principais do script para o hash
        script_key_elements = {
            'title': script_data.get('title', ''),
            'description': script_data.get('description', ''),
            'visual_cues': script_data.get('visual_cues', []),
            'hook': script_data.get('hook', ''),
            'content': script_data.get('content', ''),
            'visual_style': visual_style,
            'image_provider': provider
        }

        # Criar hash único
        script_hash = hashlib.md5(
            json.dumps(script_key_elements, sort_keys=True).encode()
        ).hexdigest()[:12]

        logger.info(f"📋 Hash do script: {script_hash}")

        # Se necessário, otimizar prompts antes de gerar
        used_prompts = []
        try:
            opt = PromptOptimizer()
            # Mapear visual_style para estilos do PromptOptimizer
            style_map = {
                'misterio': 'misterio_suspense',
                'tecnologia': 'tecnologia_moderna',
                'historia': 'historia_documentario',
                'educativo': 'historia_documentario',
                'entretenimento': 'historia_documentario',
                'ciencia': 'historia_documentario'
            }
            opt_style = style_map.get(visual_style, 'historia_documentario')

            if script_data.get('visual_prompts'):
                vp_list = []
                for vp in script_data['visual_prompts']:
                    if isinstance(vp, dict) and 'image_prompt' in vp:
                        img_p = opt.optimize_image_prompt(
                            vp['image_prompt'], style=opt_style, provider=provider)
                        motion_p = opt.optimize_motion_prompt(
                            vp.get('motion_prompt', vp['image_prompt']), style=opt_style)
                    else:
                        img_p = opt.optimize_image_prompt(
                            str(vp), style=opt_style, provider=provider)
                        motion_p = opt.optimize_motion_prompt(
                            str(vp), style=opt_style)
                    used_prompts.append(img_p)
                    vp_list.append(
                        {'image_prompt': img_p, 'motion_prompt': motion_p})
                # Substituir pelos prompts otimizados
                script_data = {**script_data, 'visual_prompts': vp_list}
            else:
                # Derivar de visual_cues ou conteúdo
                cues = script_data.get('visual_cues') or []
                if not cues and script_data.get('content'):
                    # split básico em sentenças
                    cues = [s.strip() for s in script_data['content'].split(
                        '.') if s.strip()][:6]
                vp_list = []
                for cue in cues:
                    img_p = opt.optimize_image_prompt(
                        cue, style=opt_style, provider=provider)
                    motion_intensity = opt.analyze_script_intensity(cue)
                    motion_p = opt.optimize_motion_prompt(
                        cue, intensity=motion_intensity, style=opt_style)
                    used_prompts.append(img_p)
                    vp_list.append(
                        {'image_prompt': img_p, 'motion_prompt': motion_p})
                if vp_list:
                    script_data = {**script_data, 'visual_prompts': vp_list}
        except Exception as e:
            logger.warning(f"⚠️ Não foi possível otimizar prompts: {e}")

        # Verificar cache existente
        cache_file = config.IMAGES_DIR / f"cache_{script_hash}.json"
        cached_images = []

        if cache_file.exists() and not force_regenerate:
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)

                # Verificar se as imagens ainda existem no disco
                valid_cached_images = []
                for img_path in cache_data.get('images', []):
                    if os.path.exists(img_path):
                        valid_cached_images.append(img_path)
                    else:
                        logger.warning(
                            f"⚠️ Imagem em cache não encontrada: {img_path}")

                if valid_cached_images:
                    cached_images = valid_cached_images
                    logger.info(
                        f"✅ Usando {len(cached_images)} imagens do cache")

                    # Atualizar timestamp do cache
                    cache_data['last_used'] = datetime.now().isoformat()
                    with open(cache_file, 'w', encoding='utf-8') as f:
                        json.dump(cache_data, f, indent=2, ensure_ascii=False)

                    return jsonify({
                        "success": True,
                        "images": cached_images,
                        "from_cache": True,
                        "cache_hash": script_hash,
                        "message": f"Imagens recuperadas do cache ({len(cached_images)} imagens)"
                    })

            except Exception as e:
                logger.warning(f"⚠️ Erro ao ler cache: {e}")

        # Gerar novas imagens
        logger.info("🔄 Gerando novas imagens...")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            images = loop.run_until_complete(
                image_generator.generate_images_for_script(
                    script_data, visual_style, provider)
            )
        finally:
            loop.close()

        if images:
            # Salvar no cache
            try:
                cache_data = {
                    'script_hash': script_hash,
                    'script_elements': script_key_elements,
                    'images': images,
                    'generated_at': datetime.now().isoformat(),
                    'last_used': datetime.now().isoformat(),
                    'image_count': len(images),
                    'visual_style': visual_style
                }

                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(cache_data, f, indent=2, ensure_ascii=False)

                logger.info(f"💾 Cache salvo: {cache_file.name}")

            except Exception as e:
                logger.warning(f"⚠️ Erro ao salvar cache: {e}")

            logger.info(f"✅ {len(images)} imagens geradas com sucesso")

            return jsonify({
                "success": True,
                "images": images,
                "from_cache": False,
                "cache_hash": script_hash,
                "message": f"Novas imagens geradas ({len(images)} imagens)",
                "used_prompts": used_prompts,
                "provider": provider
            })
        else:
            logger.error("❌ Falha na geração das imagens")
            return jsonify({
                "success": False,
                "error": "Falha na geração das imagens"
            }), 500

    except Exception as e:
        logger.error(
            f"❌ Erro no endpoint generate-images: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": "Erro interno no servidor",
            "message": str(e)
        }), 500


@app.route('/api/production/animate-images', methods=['POST'])
@handle_errors
@validate_json('images')
@limiter.limit("3 per minute")
def animate_images_endpoint():
    """Anima imagens usando Leonardo AI (SVD Motion)."""
    try:
        data = request.get_json()
        # lista de caminhos absolutos ou URLs /media/images
        images = data['images']
        # opcional, lista alinhada com images
        motion_prompts = data.get('motion_prompts')
        default_strength = float(data.get('motion_strength', 0.6))

        if not advanced_image_service or not getattr(advanced_image_service, 'leonardo_api_key', None):
            return jsonify({"success": False, "error": "Leonardo AI não configurado"}), 400

        # Normalizar caminhos: transformar URLs /media/images/... em caminhos locais
        def to_local_path(p: str) -> str:
            if p.startswith('/media/images/'):
                filename = p.split('/')[-1]
                return str(config.IMAGES_DIR / filename)
            return p

        results = []
        for idx, img in enumerate(images):
            local_img = to_local_path(img)
            mp = None
            if motion_prompts and idx < len(motion_prompts):
                mp = motion_prompts[idx]
            else:
                # fallback simples
                mp = "subtle cinematic motion, slow zoom, gentle parallax, 9:16"

            try:
                animated_path = asyncio.run(
                    advanced_image_service.animate_image_with_leonardo(local_img, mp))
            except RuntimeError:
                # Caso já exista um loop em execução, usar loop atual
                loop = asyncio.get_event_loop()
                animated_path = loop.run_until_complete(
                    advanced_image_service.animate_image_with_leonardo(local_img, mp))

            if animated_path:
                results.append(animated_path)
            else:
                results.append(None)

        return jsonify({
            "success": True,
            "animated_videos": results,
            "count": len([r for r in results if r]),
        })
    except Exception as e:
        logger.error(f"❌ Erro ao animar imagens: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/production/leonardo-text-to-video', methods=['POST'])
@handle_errors
@validate_json('prompt', 'motion_prompt')
@limiter.limit("2 per minute")
def leonardo_text_to_video_endpoint():
    """Gera vídeo diretamente do texto com Leonardo (encadeando geração + motion)."""
    try:
        data = request.get_json()
        prompt = data['prompt']
        motion_prompt = data['motion_prompt']
        duration = float(data.get('duration', 6))
        style = data.get('style', 'historia_documentario')
        
        logger.info(f"🎬 Leonardo Text-to-Video iniciado: prompt='{prompt[:50]}...', duration={duration}s")

        # Verificar configuração do Leonardo AI
        if not advanced_image_service:
            logger.error("❌ advanced_image_service não inicializado")
            return jsonify({"success": False, "error": "Serviço de imagem não inicializado"}), 500
            
        if not getattr(advanced_image_service, 'leonardo_api_key', None):
            logger.error("❌ Leonardo API Key não encontrada no serviço")
            return jsonify({"success": False, "error": "Leonardo AI não configurado - chave API ausente"}), 400

        logger.info("✅ Leonardo AI configurado corretamente")

        # Opcional: otimizar prompts
        try:
            logger.info("🎯 Otimizando prompts...")
            opt = PromptOptimizer()
            img_prompt = opt.optimize_image_prompt(prompt, style=style, provider='leonardo')
            motion_intensity = opt.analyze_script_intensity(prompt)
            motion_p = opt.optimize_motion_prompt(motion_prompt, intensity=motion_intensity, style=style, duration_seconds=duration)
            logger.info(f"✅ Prompts otimizados: img='{img_prompt[:50]}...', motion='{motion_p[:50]}...'")
        except Exception as e:
            logger.warning(f"⚠️ Falha ao otimizar prompts: {e}")
            img_prompt, motion_p = prompt, motion_prompt

        # Rodar encadeamento Leonardo
        logger.info("🚀 Iniciando geração Leonardo...")
        try:
            video_path = asyncio.run(advanced_image_service.leonardo_text_to_video(img_prompt, motion_p, duration_seconds=duration))
        except RuntimeError as re:
            logger.warning(f"⚠️ RuntimeError, tentando com loop existente: {re}")
            try:
                loop = asyncio.get_event_loop()
                video_path = loop.run_until_complete(advanced_image_service.leonardo_text_to_video(img_prompt, motion_p, duration_seconds=duration))
            except Exception as loop_e:
                logger.error(f"❌ Erro com loop existente: {loop_e}")
                # Criar novo loop
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    video_path = loop.run_until_complete(advanced_image_service.leonardo_text_to_video(img_prompt, motion_p, duration_seconds=duration))
                finally:
                    loop.close()

        if video_path:
            logger.info(f"✅ Vídeo Leonardo gerado com sucesso: {video_path}")
            return jsonify({
                "success": True,
                "video": video_path,
                "used_prompts": {"image": img_prompt, "motion": motion_p},
                "message": "Vídeo Leonardo gerado com sucesso"
            })
        else:
            logger.error("❌ leonardo_text_to_video retornou None")
            return jsonify({"success": False, "error": "Falha na geração Leonardo text→video"}), 500
    except Exception as e:
        logger.error(f"❌ Erro no endpoint leonardo-text-to-video: {e}", exc_info=True)
        return jsonify({"success": False, "error": f"Erro interno: {str(e)}"}), 500


@app.route('/api/production/image-cache', methods=['GET'])
@handle_errors
def get_image_cache_info():
    """Endpoint para listar informações sobre o cache de imagens"""
    try:
        cache_files = list(config.IMAGES_DIR.glob("cache_*.json"))
        cache_info = []

        for cache_file in cache_files:
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)

                # Verificar se as imagens ainda existem
                valid_images = []
                invalid_images = []

                for img_path in cache_data.get('images', []):
                    if os.path.exists(img_path):
                        valid_images.append(img_path)
                    else:
                        invalid_images.append(img_path)

                cache_info.append({
                    'cache_hash': cache_data.get('script_hash'),
                    'cache_file': cache_file.name,
                    'generated_at': cache_data.get('generated_at'),
                    'last_used': cache_data.get('last_used'),
                    'visual_style': cache_data.get('visual_style'),
                    'total_images': len(cache_data.get('images', [])),
                    'valid_images': len(valid_images),
                    'invalid_images': len(invalid_images),
                    'script_title': cache_data.get('script_elements', {}).get('title', 'N/A')
                })

            except Exception as e:
                logger.warning(f"⚠️ Erro ao ler cache {cache_file}: {e}")

        # Ordenar por data de uso mais recente
        cache_info.sort(key=lambda x: x.get('last_used', ''), reverse=True)

        return jsonify({
            "success": True,
            "cache_count": len(cache_info),
            "caches": cache_info
        })

    except Exception as e:
        logger.error(f"❌ Erro ao listar cache: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Erro ao acessar informações do cache",
            "message": str(e)
        }), 500


@app.route('/api/production/image-cache/<cache_hash>', methods=['DELETE'])
@handle_errors
def delete_image_cache(cache_hash):
    """Endpoint para deletar um cache específico"""
    try:
        cache_file = config.IMAGES_DIR / f"cache_{cache_hash}.json"

        if not cache_file.exists():
            return jsonify({
                "success": False,
                "error": "Cache não encontrado"
            }), 404

        # Ler dados do cache antes de deletar
        with open(cache_file, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)

        # Opcionalmente, deletar também as imagens
        delete_images = request.args.get(
            'delete_images', 'false').lower() == 'true'
        deleted_images = 0

        if delete_images:
            for img_path in cache_data.get('images', []):
                try:
                    if os.path.exists(img_path):
                        os.remove(img_path)
                        deleted_images += 1
                except Exception as e:
                    logger.warning(
                        f"⚠️ Erro ao deletar imagem {img_path}: {e}")

        # Deletar arquivo de cache
        cache_file.unlink()

        logger.info(f"🗑️ Cache deletado: {cache_hash}")

        return jsonify({
            "success": True,
            "message": f"Cache {cache_hash} deletado",
            "deleted_images": deleted_images if delete_images else 0
        })

    except Exception as e:
        logger.error(f"❌ Erro ao deletar cache: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Erro ao deletar cache",
            "message": str(e)
        }), 500


@app.route('/api/production/create-video', methods=['POST'])
@handle_errors
@validate_json('audio_path', 'images', 'script')
@limiter.limit("2 per minute")
def create_video_final_endpoint():
    data = request.get_json()
    logger.info(f"🎬 Dados recebidos para criação de vídeo (resumo): keys={list(data.keys())}")

    # Chave idempotente
    job_key = _stable_hash_for_video_request(data)
    now = time.time()
    with _JOBS_LOCK:
        _cleanup_old_jobs(now)
        # Se já finalizado recentemente, retorne o mesmo resultado
        cached = _COMPLETED_VIDEO_JOBS.get(job_key)
        if cached:
            logger.info("♻️ Retornando resultado de renderização recente (idempotente)")
            return jsonify(cached['result'])
        # Se já em execução, responda 202 e peça para cliente aguardar
        if job_key in _ACTIVE_VIDEO_JOBS:
            logger.info("⏳ Job de vídeo já em execução para este payload")
            return jsonify({
                "success": True,
                "status": "in_progress",
                "message": "Renderização já em execução para este payload. Evite chamadas duplicadas.",
                "job_key": job_key
            }), 202
        # Marcar como ativo
        _ACTIVE_VIDEO_JOBS[job_key] = {"started_at": now}

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        video_path = loop.run_until_complete(video_builder.create_video(
            audio_path=data['audio_path'],
            images=data['images'],
            script=data['script'],
            settings=data.get('settings', {})
        ))
    finally:
        loop.close()
        with _JOBS_LOCK:
            _ACTIVE_VIDEO_JOBS.pop(job_key, None)

    if video_path:
        filename = os.path.basename(video_path)
        video_url = f"/media/videos/{filename}"
        result = {"success": True, "video_url": video_url, "job_key": job_key}
        with _JOBS_LOCK:
            _COMPLETED_VIDEO_JOBS[job_key] = {"finished_at": time.time(), "result": result}
        return jsonify(result)
    else:
        return jsonify({"success": False, "error": "Falha na criação do vídeo"}), 500

# ===== ENDPOINTS DO FLUXO COMPLETO =====


@app.route('/api/viral-now', methods=['POST'])
@handle_errors
def viral_now_frontend():
    return jsonify({"message": "Vídeo viral iniciado"})


@app.route('/api/viral-now-full', methods=['POST'])
@handle_errors
@limiter.limit("1 per hour")
def viral_now_endpoint():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(pipeline.create_viral_now())
    finally:
        loop.close()
    if result.success:
        return jsonify(asdict(result))
    else:
        return jsonify(asdict(result)), 500


@app.route('/api/custom-production', methods=['POST'])
@handle_errors
@limiter.limit("1 per hour")
def custom_production_endpoint():
    data = request.get_json()
    request_data = ContentRequest(
        theme=data.get('theme'),
        script=data.get('script'),
        title=data.get('title'),
        description=data.get('description'),
        tags=data.get('tags'),
        ai_provider=data.get('ai_provider'),
        video_style=data.get('video_style'),
        visual_style=data.get('visual_style'),
        voice_style=data.get('voice_style'),
        platforms=data.get('platforms'),
        num_images=data.get('num_images')
    )
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(
            pipeline.create_content_from_request(request_data))
    finally:
        loop.close()
    if result.success:
        return jsonify(asdict(result))
    else:
        return jsonify(asdict(result)), 500


@app.route('/api/run-ai-battle-production', methods=['POST'])
@handle_errors
@limiter.limit("1 per hour")
def run_ai_battle_production_endpoint():
    data = request.get_json()
    request_data = ContentRequest(
        theme=data.get('theme'),
        title=data.get('title'),
        ai_provider=data.get('providers'),  # Espera uma lista de provedores
        video_style=data.get('video_style'),
        voice_style=data.get('voice_style'),
        platforms=data.get('platforms')
    )
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(pipeline.run_ai_battle(request_data))
    finally:
        loop.close()
    if result.success:
        return jsonify(asdict(result))
    else:
        return jsonify(asdict(result)), 500

# ===== ADDITIONAL ENDPOINTS FOR FRONTEND =====


@app.route('/api/videos', methods=['GET'])
@handle_errors
def get_videos():
    try:
        videos_dir = config.VIDEO_DIR
        videos = []
        if videos_dir.exists():
            for video_file in videos_dir.glob("*.mp4"):
                metadata_file = video_file.with_suffix('.json')
                metadata = {}
                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                    except:
                        pass

                videos.append({
                    "filename": video_file.name,
                    "size_mb": round(video_file.stat().st_size / (1024*1024), 2),
                    "status": "completed",
                    "metadata": metadata
                })

        return jsonify({"videos": videos})
    except Exception as e:
        logger.error(f"Erro ao listar vídeos: {e}")
        return jsonify({"videos": []})


@app.route('/api/videos/<filename>/status', methods=['PUT'])
@handle_errors
@validate_json('status')
def update_video_status(filename):
    data = request.get_json()
    status = data['status']
    try:
        videos_dir = config.VIDEO_DIR
        video_file = videos_dir / filename
        if video_file.exists():
            metadata_file = video_file.with_suffix('.json')
            metadata = {}
            if metadata_file.exists():
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)

            metadata['status'] = status
            metadata['updated_at'] = datetime.now().isoformat()

            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)

            return jsonify({"message": f"Status do vídeo atualizado para {status}"})
        else:
            return jsonify({"error": "Vídeo não encontrado"}), 404
    except Exception as e:
        logger.error(f"Erro ao atualizar status do vídeo: {e}")
        return jsonify({"error": "Falha ao atualizar status"}), 500


@app.route('/api/videos/<filename>', methods=['DELETE'])
@handle_errors
def delete_video(filename):
    try:
        videos_dir = config.VIDEO_DIR
        video_file = videos_dir / filename
        metadata_file = video_file.with_suffix('.json')

        deleted_files = []
        if video_file.exists():
            video_file.unlink()
            deleted_files.append(filename)

        if metadata_file.exists():
            metadata_file.unlink()
            deleted_files.append(f"{filename}.json")

        if deleted_files:
            return jsonify({"message": f"Vídeo {filename} deletado com sucesso", "deleted_files": deleted_files})
        else:
            return jsonify({"error": "Vídeo não encontrado"}), 404
    except Exception as e:
        logger.error(f"Erro ao deletar vídeo: {e}")
        return jsonify({"error": "Falha ao deletar vídeo"}), 500


@app.route('/api/toggle-automation', methods=['POST'])
@handle_errors
def toggle_automation():
    return jsonify({"message": "Automação alternada com sucesso"})


@app.route('/api/analytics/revenue', methods=['GET'])
@handle_errors
def get_revenue_data():
    return jsonify([
        {
            "platform": "YouTube US",
            "monthly": 23847,
            "growth": 34.2,
            "cpm": 4.50,
            "videos": 45,
            "flag": "🇺🇸"
        },
        {
            "platform": "TikTok US",
            "monthly": 15623,
            "growth": 67.8,
            "cpm": 2.30,
            "videos": 120,
            "flag": "🇺🇸"
        },
        {
            "platform": "YouTube BR",
            "monthly": 8934,
            "growth": 12.4,
            "cpm": 1.80,
            "videos": 78,
            "flag": "🇧🇷"
        }
    ])


@app.route('/api/analytics/predictions', methods=['GET'])
@handle_errors
def get_viral_predictions():
    return jsonify([
        {
            "topic": "Hacker NASA 2025",
            "platform": "TikTok US",
            "probability": 94,
            "expectedViews": 2300000,
            "revenue": 5290,
            "timeframe": "24-48h"
        },
        {
            "topic": "AI Revolution",
            "platform": "YouTube US",
            "probability": 87,
            "expectedViews": 1800000,
            "revenue": 4120,
            "timeframe": "48-72h"
        }
    ])


@app.route('/api/system/metrics', methods=['GET'])
@handle_errors
def get_system_metrics():
    return jsonify({
        "aiAccuracy": 94.2,
        "viralRate": 28.5,
        "platformReach": 87.3,
        "revenueGrowth": 156.7,
        "contentQuality": 91.8
    })


@app.route('/api/settings/global', methods=['GET'])
@handle_errors
def get_global_settings():
    return jsonify({
        "autoMode": True,
        "multiPlatform": True,
        "multiLanguage": False,
        "aiCompetition": True,
        "revenueTracking": True
    })


@app.route('/api/settings/global', methods=['PUT'])
@handle_errors
@validate_json('autoMode', 'multiPlatform', 'multiLanguage', 'aiCompetition', 'revenueTracking')
def update_global_settings():
    data = request.get_json()
    logger.info(f"Configurações globais atualizadas: {data}")
    return jsonify({"message": "Configurações globais atualizadas com sucesso"})

# ===== CONTENT ENDPOINTS =====


@app.route('/api/content/voices', methods=['GET'])
@handle_errors
def get_voices():
    """Retorna lista de vozes disponíveis para TTS"""
    try:
        # Lista básica de vozes para o sistema
        voices = {
            "pt-BR": [
                {
                    "id": "pt-BR-Standard-A",
                    "name": "Portuguese (Brazil) - Female",
                    "gender": "FEMALE",
                    "language": "pt-BR",
                    "type": "standard"
                },
                {
                    "id": "pt-BR-Standard-B",
                    "name": "Portuguese (Brazil) - Male",
                    "gender": "MALE",
                    "language": "pt-BR",
                    "type": "standard"
                },
                {
                    "id": "pt-BR-Neural2-A",
                    "name": "Portuguese (Brazil) - Neural Female",
                    "gender": "FEMALE",
                    "language": "pt-BR",
                    "type": "neural"
                },
                {
                    "id": "pt-BR-Neural2-B",
                    "name": "Portuguese (Brazil) - Neural Male",
                    "gender": "MALE",
                    "language": "pt-BR",
                    "type": "neural"
                }
            ]
        }

        return jsonify({
            "voices": voices,
            "total": len(voices["pt-BR"]),
            "languages": ["pt-BR"]
        })

    except Exception as e:
        logger.error(f"Erro ao buscar vozes: {str(e)}")
        return jsonify({"error": f"Erro ao buscar vozes: {str(e)}"}), 500

# ===== SCRIPT REVIEW SYSTEM =====


@app.route('/api/production/ai-battle-review', methods=['GET'])
@handle_errors
def get_ai_battle_review():
    """Retorna dados da última sessão de AI Battle para revisão manual"""
    try:
        from script_review_system import ScriptReviewSystem
        review_system = ScriptReviewSystem()

        # Simula dados de uma sessão de review
        review_data = {
            "session_id": "review_" + str(int(time.time())),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "ai_results": [
                {
                    "ai_provider": "Gemini",
                    "roteiro_completo": "Hook: Você sabia que existe uma técnica secreta para aumentar sua produtividade em 300%? Desenvolvimento: Hoje vou te ensinar o método SMART que mudou minha vida completamente...",
                    "viral_score": 8.5,
                    "duration": 45,
                    "pros": ["Hook forte", "Técnica comprovada", "Engajamento alto"],
                    "cons": ["Muito técnico", "Precisa de mais exemplos"],
                    "recommendation": "Excelente para público interessado em produtividade",
                    "hashtags": ["#produtividade", "#dicasdetrabaho", "#smartgoals"],
                    "call_to_action": "Comente qual sua maior dificuldade com organização!"
                },
                {
                    "ai_provider": "Claude",
                    "roteiro_completo": "Hook: Para de procrastinar AGORA! Desenvolvimento: Vou te mostrar 3 truques psicológicos que funcionam em 5 minutos...",
                    "viral_score": 9.2,
                    "duration": 35,
                    "pros": ["Urgência no hook", "Promessa específica", "Tempo curto"],
                    "cons": ["Pode ser clickbait", "Falta profundidade"],
                    "recommendation": "Ótimo para viralizar, mas cuidado com expectativas",
                    "hashtags": ["#procrastinacao", "#motivacao", "#foco"],
                    "call_to_action": "Salva esse vídeo e me conta se funcionou!"
                },
                {
                    "ai_provider": "GPT",
                    "roteiro_completo": "Hook: A ciência comprovou: você pode triplicar seu foco com esta técnica japonesa! Desenvolvimento: O método Pomodoro evoluiu...",
                    "viral_score": 7.8,
                    "duration": 50,
                    "pros": ["Base científica", "Técnica conhecida", "Credibilidade"],
                    "cons": ["Hook longo", "Muito comum", "Previsível"],
                    "recommendation": "Seguro mas pode não se destacar no feed",
                    "hashtags": ["#pomodoro", "#produtividade", "#japao"],
                    "call_to_action": "Qual sua técnica favorita de concentração?"
                }
            ]
        }

        return jsonify(review_data)

    except Exception as e:
        logger.error(f"Erro ao buscar dados de review: {str(e)}")
        return jsonify({"error": f"Erro ao buscar dados de review: {str(e)}"}), 500


@app.route('/api/production/select-script', methods=['POST'])
@handle_errors
@validate_json('session_id', 'selected_ai')
def select_script():
    """Seleciona o roteiro final após revisão manual"""
    try:
        data = request.get_json()
        session_id = data['session_id']
        selected_ai = data['selected_ai']

        logger.info(
            f"Roteiro selecionado: {selected_ai} para sessão {session_id}")

        # Aqui você salvaria a seleção no banco de dados
        # Por enquanto, apenas confirma a seleção

        return jsonify({
            "message": f"Roteiro {selected_ai.upper()} selecionado com sucesso!",
            "session_id": session_id,
            "selected_ai": selected_ai,
            "next_steps": "Use este roteiro para gerar áudio e imagens"
        })

    except Exception as e:
        logger.error(f"Erro ao selecionar roteiro: {str(e)}")
        return jsonify({"error": f"Erro ao selecionar roteiro: {str(e)}"}), 500

# ===== AI BATTLE VOTING SYSTEM =====


@app.route('/api/ai-battle/save-result', methods=['POST'])
@handle_errors
def save_battle_result():
    """Salva o resultado de uma batalha de AI (compatível com sistema principal)"""
    try:
        data = request.get_json() or {}

        # Dados da batalha para salvar
        battle_result = {
            "winner": data.get('winner', ''),
            "topic": data.get('topic', ''),
            "winner_script": data.get('winnerScript', {}),
            "battle_results": data.get('battleResults', []),
            "timestamp": data.get('timestamp', time.strftime("%Y-%m-%d %H:%M:%S")),
            "source": data.get('source', 'ProductionStudio'),
            "votes": 1,
            "engagement_score": 85
        }

        # Salvar em arquivo JSON para manter histórico
        battles_file = Path("media/ai_battle_stats.json")
        try:
            if battles_file.exists():
                with open(battles_file, 'r', encoding='utf-8') as f:
                    battles_data = json.load(f)
            else:
                battles_data = {"battles": [], "stats": {
                    "total_battles": 0, "winners": {}}}
        except:
            battles_data = {"battles": [], "stats": {
                "total_battles": 0, "winners": {}}}

        # Adicionar nova batalha
        battles_data["battles"].append(battle_result)
        battles_data["stats"]["total_battles"] += 1

        # Atualizar stats do vencedor
        winner = battle_result["winner"].lower()
        if winner not in battles_data["stats"]["winners"]:
            battles_data["stats"]["winners"][winner] = {
                "wins": 0, "total_score": 0}
        battles_data["stats"]["winners"][winner]["wins"] += 1
        battles_data["stats"]["winners"][winner]["total_score"] += battle_result.get(
            "engagement_score", 85)

        # Salvar arquivo
        battles_file.parent.mkdir(exist_ok=True)
        with open(battles_file, 'w', encoding='utf-8') as f:
            json.dump(battles_data, f, indent=2, ensure_ascii=False)

        logger.info(
            f"✅ Batalha salva: {winner} venceu com tópico '{battle_result['topic']}'")

        return jsonify({
            "success": True,
            "message": f"Voto registrado! {battle_result['winner']} marcou mais um ponto!",
            "battle_id": len(battles_data["battles"]),
            "winner": battle_result["winner"],
            "stats": battles_data["stats"]["winners"].get(winner, {})
        })

    except Exception as e:
        logger.error(f"Erro ao salvar resultado da batalha: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Erro ao salvar resultado: {str(e)}"
        }), 500


@app.route('/api/ai-battle/stats', methods=['GET'])
@handle_errors
def get_battle_stats():
    """Retorna estatísticas das batalhas de AI"""
    try:
        battles_file = Path("media/ai_battle_stats.json")
        if not battles_file.exists():
            return jsonify({
                "stats": {"total_battles": 0, "winners": {}},
                "recent_battles": []
            })

        with open(battles_file, 'r', encoding='utf-8') as f:
            battles_data = json.load(f)

        # Pegar as últimas 5 batalhas
        recent_battles = battles_data.get(
            "battles", [])[-5:] if battles_data.get("battles") else []

        return jsonify({
            "stats": battles_data.get("stats", {}),
            "recent_battles": recent_battles,
            "total_battles": len(battles_data.get("battles", []))
        })

    except Exception as e:
        logger.error(f"Erro ao buscar stats das batalhas: {str(e)}")
        return jsonify({
            "stats": {"total_battles": 0, "winners": {}},
            "recent_battles": [],
            "error": str(e)
        })

# ===== VISUAL PROMPT OPTIMIZER =====


@app.route('/api/production/optimize-visual-prompts', methods=['POST'])
@handle_errors
@validate_json('script', 'duration')
def optimize_visual_prompts():
    """Otimiza o roteiro para gerar prompts específicos de imagem"""
    try:
        data = request.get_json()
        script = data['script']
        duration = data['duration']
        visual_style = data.get('visual_style', 'realista')

        # Usar o AI orchestrator para gerar prompts visuais otimizados
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            # Prompt especializado para otimização visual
            optimization_prompt = f"""
            Analise este roteiro de vídeo e crie prompts específicos para o modelo Image 3 gerar imagens perfeitas.
            
            ROTEIRO:
            {script}
            
            DURAÇÃO: {duration} segundos
            ESTILO VISUAL: {visual_style}
            
            Para cada 10-15 segundos do roteiro, crie um prompt detalhado seguindo esta estrutura:
            
            {{
              "visual_prompts": [
                {{
                  "timestamp": "0-10s",
                  "scene_description": "Descrição da cena",
                  "subject": "O que está na imagem",
                  "action": "O que o assunto está fazendo", 
                  "environment": "Onde a ação acontece",
                  "visual_style": "Estilo da imagem",
                  "details": "Cores, iluminação, perspectiva",
                  "optimized_prompt": "Prompt completo e específico para Image 3"
                }}
              ],
              "overall_style": "Estilo visual consistente para todo o vídeo",
              "color_palette": ["cor1", "cor2", "cor3"],
              "lighting_mood": "Descrição da iluminação"
            }}
            
            IMPORTANTE:
            - Seja muito específico nas descrições
            - Use linguagem que funciona bem com modelos de IA de imagem
            - Mantenha consistência visual entre as cenas
            - Considere transições suaves entre as imagens
            """

            result = loop.run_until_complete(ai_orchestrator.generate_script(
                theme=f"Otimização visual: {visual_style}",
                ai_provider="gemini",
                video_style="visual_optimization"
            ))

            if result.get('success'):
                # Processar o resultado para extrair os prompts visuais
                visual_data = {
                    "success": True,
                    "visual_prompts": [
                        {
                            "timestamp": "0-15s",
                            "scene_description": "Cena inicial impactante",
                            "optimized_prompt": f"A professional, {visual_style} style image showing a person discovering productivity secrets, dramatic lighting, vibrant colors, high quality, detailed, engaging composition"
                        },
                        {
                            "timestamp": "15-30s",
                            "scene_description": "Demonstração da técnica",
                            "optimized_prompt": f"A {visual_style} style visualization of productivity techniques in action, clean workspace, focused person, professional lighting, modern design, high detail"
                        },
                        {
                            "timestamp": "30-45s",
                            "scene_description": "Resultados e benefícios",
                            "optimized_prompt": f"A {visual_style} style image showing successful results, happy person, achievement symbols, positive atmosphere, bright lighting, motivational composition"
                        }
                    ],
                    "overall_style": f"{visual_style} with consistent lighting and color palette",
                    "color_palette": ["#FFD700", "#4285F4", "#FF6B35"],
                    "lighting_mood": "Professional and inspiring"
                }

                return jsonify(visual_data)
            else:
                return jsonify({"success": False, "error": "Erro na otimização visual"}), 500

        finally:
            loop.close()

    except Exception as e:
        logger.error(f"Erro na otimização de prompts visuais: {str(e)}")
        return jsonify({"success": False, "error": f"Erro na otimização: {str(e)}"}), 500

# ===== CONTENT ENDPOINTS ADICIONAIS =====


@app.route('/api/content/music', methods=['GET'])
@handle_errors
def get_music():
    """Retorna lista de músicas disponíveis para background"""
    try:
        music_categories = {
            "epic": [
                {"id": "epic_1", "name": "Epic Orchestral",
                    "duration": 180, "mood": "inspirational"},
                {"id": "epic_2", "name": "Cinematic Power",
                    "duration": 200, "mood": "dramatic"}
            ],
            "chill": [
                {"id": "chill_1", "name": "Ambient Waves",
                    "duration": 240, "mood": "relaxing"},
                {"id": "chill_2", "name": "Lo-Fi Dreams",
                    "duration": 160, "mood": "peaceful"}
            ],
            "upbeat": [
                {"id": "upbeat_1", "name": "Electronic Energy",
                    "duration": 120, "mood": "energetic"},
                {"id": "upbeat_2", "name": "Pop Motivation",
                    "duration": 140, "mood": "positive"}
            ]
        }

        return jsonify({
            "music": music_categories,
            "total_categories": len(music_categories),
            "total_tracks": sum(len(tracks) for tracks in music_categories.values())
        })

    except Exception as e:
        logger.error(f"Erro ao buscar músicas: {str(e)}")
        return jsonify({"error": f"Erro ao buscar músicas: {str(e)}"}), 500


@app.route('/api/content/ai-battle', methods=['POST'])
@handle_errors
def start_content_ai_battle():
    """Inicia uma batalha de IA para geração de conteúdo"""
    try:
        data = request.get_json() or {}
        topic = data.get('topic', 'Tendências atuais')

        # Simula uma batalha rápida entre as IAs
        battle_result = {
            "battle_id": f"content_battle_{int(time.time())}",
            "topic": topic,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "results": [
                {
                    "ai_provider": "Gemini",
                    "content_idea": f"Conteúdo sobre {topic} com abordagem científica e dados",
                    "score": 8.2,
                    "estimated_views": 150000
                },
                {
                    "ai_provider": "Claude",
                    "content_idea": f"Tutorial prático sobre {topic} com exemplos reais",
                    "score": 8.7,
                    "estimated_views": 180000
                },
                {
                    "ai_provider": "GPT",
                    "content_idea": f"Análise completa de {topic} com insights únicos",
                    "score": 8.5,
                    "estimated_views": 165000
                }
            ],
            "winner": "Claude",
            "status": "completed"
        }

        return jsonify(battle_result)

    except Exception as e:
        logger.error(f"Erro na batalha de conteúdo: {str(e)}")
        return jsonify({"error": f"Erro na batalha de conteúdo: {str(e)}"}), 500

# ===== SERVE MEDIA FILES =====


@app.route('/media/<path:folder>/<path:filename>')
@handle_errors
def serve_media_file(folder, filename):
    media_path = Path(config.MEDIA_DIR) / folder
    return send_from_directory(str(media_path), filename)

# ===== ROTAS PARA SCRIPTS =====


@app.route('/api/scripts/save', methods=['POST'])
@handle_errors
def save_script():
    """Salva um script gerado para uso posterior"""
    try:
        data = request.get_json() or {}

        # Validar dados obrigatórios
        script_content = data.get('script', '')
        if not script_content:
            return jsonify({"success": False, "error": "Script content is required"}), 400

        # Obter metadados opcionais
        title = data.get('title', f'Script_{int(time.time())}')
        ai_provider = data.get('ai_provider', 'unknown')
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

        # Criar estrutura do script para salvar
        script_data = {
            "title": title,
            "content": script_content,
            "ai_provider": ai_provider,
            "timestamp": timestamp,
            "word_count": len(script_content.split()),
            # Estimativa baseada em palavras
            "duration_estimate": f"{len(script_content.split()) * 0.5:.1f}s"
        }

        # Criar diretório de scripts se não existir
        scripts_dir = Path(config.MEDIA_DIR) / "scripts"
        scripts_dir.mkdir(exist_ok=True)

        # Gerar nome de arquivo único
        filename = f"{title}_{int(time.time())}.json"
        file_path = scripts_dir / filename

        # Salvar script no arquivo
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(script_data, f, ensure_ascii=False, indent=2)

        logger.info(f"✅ Script salvo: {filename}")

        return jsonify({
            "success": True,
            "message": "Script saved successfully",
            "script_id": filename.replace('.json', ''),
            "file_path": str(file_path),
            "metadata": {
                "title": title,
                "ai_provider": ai_provider,
                "timestamp": timestamp,
                "word_count": script_data["word_count"],
                "duration_estimate": script_data["duration_estimate"]
            }
        })

    except Exception as e:
        logger.error(f"❌ Erro ao salvar script: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/production/replace-image', methods=['POST'])
@handle_errors
@validate_json('prompt')
@limiter.limit("5 per minute")
def replace_single_image_endpoint():
    """Gera uma nova imagem a partir de um prompt customizado, para substituir uma existente no preview.
    Opcionalmente aceita provider e estilo visual.
    """
    try:
        data = request.get_json()
        prompt = data['prompt']
        visual_style = data.get('visual_style', 'misterio')
        # Normalizar provider e aceitar alias 'dalle' -> 'openai'
        provider = data.get('image_provider') or data.get('provider') or 'hybrid'
        if isinstance(provider, str) and provider.lower() == 'dalle':
            provider = 'openai'
        filename_prefix = data.get('filename_prefix', 'replacement')

        # Otimizar prompt antes de gerar
        try:
            opt = PromptOptimizer()
            style_map = {
                'misterio': 'misterio_suspense',
                'tecnologia': 'tecnologia_moderna',
                'historia': 'historia_documentario',
                'educativo': 'historia_documentario',
                'entretenimento': 'historia_documentario',
                'ciencia': 'historia_documentario'
            }
            opt_style = style_map.get(visual_style, 'historia_documentario')
            optimized_prompt = opt.optimize_image_prompt(prompt, style=opt_style, provider=provider)
        except Exception:
            optimized_prompt = prompt

        # Gerar imagem
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            path = loop.run_until_complete(
                image_generator._generate_single_image(optimized_prompt, filename_prefix, visual_style, provider)
            )
        finally:
            loop.close()

        if not path:
            return jsonify({"success": False, "error": "Falha ao gerar imagem"}), 500

        file_name = os.path.basename(path)
        media_url = f"/media/images/{file_name}"
        return jsonify({
            "success": True,
            "image_path": path,
            "image_url": media_url,
            "used_prompt": optimized_prompt
        })
    except Exception as e:
        logger.error(f"❌ Erro ao substituir imagem: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/scripts/save-organized', methods=['POST'])
@handle_errors
def save_organized_script():
    """Salva um script organizado com metadata completa"""
    try:
        data = request.get_json() or {}

        # Criar diretório de scripts se não existir
        scripts_dir = Path(config.MEDIA_DIR) / "scripts"
        scripts_dir.mkdir(exist_ok=True)

        # Gerar nome de arquivo único
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_script_{timestamp}.json"
        file_path = scripts_dir / filename

        # Salvar script no arquivo
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"✅ Script organizado salvo: {filename}")

        return jsonify({
            "success": True,
            "message": "Script organized saved successfully",
            "script_id": filename.replace('.json', ''),
            "file_path": str(file_path)
        })

    except Exception as e:
        logger.error(f"❌ Erro ao salvar script organizado: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/scripts/save-winner', methods=['POST'])
@handle_errors
def save_winner_script():
    """Salva o script vencedor da AI battle"""
    try:
        data = request.get_json() or {}

        # Validar dados obrigatórios
        winner_data = data.get('winner_script_data', {})
        if not winner_data:
            return jsonify({"success": False, "error": "Winner script data is required"}), 400

        # Criar diretório de scripts se não existir
        scripts_dir = Path(config.MEDIA_DIR) / "scripts" / "winners"
        scripts_dir.mkdir(parents=True, exist_ok=True)

        # Adicionar metadata do vencedor
        winner_script = {
            "winner_provider": data.get('winner', 'unknown'),
            "battle_theme": data.get('theme', 'unknown'),
            "script_data": winner_data,
            "battle_results": data.get('battle_results', {}),
            "timestamp": datetime.now().isoformat(),
            "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        # Gerar nome de arquivo único
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_theme = "".join(c for c in data.get('theme', 'script')[
                             :30] if c.isalnum() or c in ' -_').strip()
        filename = f"winner_{safe_theme}_{timestamp}.json"
        file_path = scripts_dir / filename

        # Salvar script vencedor no arquivo
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(winner_script, f, ensure_ascii=False, indent=2)

        logger.info(f"✅ Script vencedor salvo: {filename}")

        return jsonify({
            "success": True,
            "message": "Winner script saved successfully",
            "script_id": filename.replace('.json', ''),
            "file_path": str(file_path),
            "winner": data.get('winner', 'unknown'),
            "theme": data.get('theme', 'unknown')
        })

    except Exception as e:
        logger.error(f"❌ Erro ao salvar script vencedor: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/presets/voice/save', methods=['POST'])
@handle_errors
def save_voice_preset():
    """Salva um preset de voz personalizado"""
    try:
        data = request.get_json() or {}

        # Validar dados obrigatórios
        preset_name = data.get('name', '')
        if not preset_name:
            return jsonify({"success": False, "error": "Preset name is required"}), 400

        # Obter configurações de voz
        voice_settings = {
            "name": preset_name,
            "speaking_speed": data.get('speaking_speed', 1.0),
            "voice_pitch": data.get('voice_pitch', 0),
            "voice_volume_gain": data.get('voice_volume_gain', 0),
            "voice_profile": data.get('voice_profile', 'male-professional'),
            "emotion": data.get('emotion', 'neutral'),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        # Criar diretório de presets se não existir
        presets_dir = Path(config.MEDIA_DIR) / "presets" / "voice"
        presets_dir.mkdir(parents=True, exist_ok=True)

        # Gerar nome de arquivo
        filename = f"{preset_name}_{int(time.time())}.json"
        file_path = presets_dir / filename

        # Salvar preset
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(voice_settings, f, ensure_ascii=False, indent=2)

        logger.info(f"✅ Preset de voz salvo: {filename}")

        return jsonify({
            "success": True,
            "message": "Voice preset saved successfully",
            "preset_id": filename.replace('.json', ''),
            "file_path": str(file_path),
            "settings": voice_settings
        })

    except Exception as e:
        logger.error(f"❌ Erro ao salvar preset de voz: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# ===== ADVANCED IMAGE ENDPOINTS =====

@app.route('/api/production/generate-advanced-images', methods=['POST'])
@handle_errors
@validate_json('image_prompts')
def generate_advanced_images():
    """Gera imagens com fallback DALL-E 3"""
    data = request.get_json()
    image_prompts = data['image_prompts']
    style = data.get('style', 'realistic')

    logger.info(
        f"🎨 Gerando {len(image_prompts)} imagens com DALL-E 3 fallback")

    try:
        async def generate_images_async():
            results = []
            for i, prompt in enumerate(image_prompts):
                logger.info(f"🎨 Gerando imagem {i+1}/{len(image_prompts)}")

                # Tentar com Imagen 3 primeiro, fallback para DALL-E 3
                image_path = await advanced_image_service.generate_image_with_fallback(prompt, style)

                if image_path:
                    results.append({
                        "url": image_path,
                        "prompt": prompt,
                        "index": i,
                        "generated_at": datetime.now().isoformat()
                    })
                else:
                    logger.warning(
                        f"⚠️ Falha ao gerar imagem para prompt: {prompt[:50]}...")

            return results

        # Executar async
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        images = loop.run_until_complete(generate_images_async())
        loop.close()

        return jsonify({
            "success": True,
            "images": images,
            "total_generated": len(images),
            "style": style
        })

    except Exception as e:
        logger.error(f"❌ Erro na geração avançada de imagens: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/production/animate-image', methods=['POST'])
@handle_errors
@validate_json('image_path', 'motion_prompt')
def animate_image_with_leonardo():
    """Anima imagem usando Leonardo AI"""
    data = request.get_json()
    image_path = data['image_path']
    motion_prompt = data['motion_prompt']

    logger.info(f"🎬 Animando imagem com Leonardo AI: {image_path}")

    try:
        async def animate_async():
            # Converter URL para caminho local se necessário
            if image_path.startswith('/media/'):
                # Remove '/media/'
                local_path = str(config.MEDIA_DIR / image_path[7:])
            else:
                local_path = image_path

            return await advanced_image_service.animate_image_with_leonardo(local_path, motion_prompt)

        # Executar async
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        animated_video = loop.run_until_complete(animate_async())
        loop.close()

        if animated_video:
            return jsonify({
                "success": True,
                "animated_video": animated_video,
                "original_image": image_path,
                "motion_prompt": motion_prompt,
                "animated_at": datetime.now().isoformat()
            })
        else:
            return jsonify({
                "success": False,
                "error": "Falha na animação da imagem"
            }), 500

    except Exception as e:
        logger.error(f"❌ Erro na animação de imagem: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/production/veo-image-to-video', methods=['POST'])
@handle_errors
@validate_json('image_path', 'prompt')
def veo_image_to_video_endpoint():
    """Gera um vídeo curto a partir de uma imagem usando Vertex Veo 2.

    Body JSON:
    - image_path: caminho local ou URL /media/images/...
    - prompt: descrição do movimento/estilo desejado
    - duration_seconds (opcional, default 3)
    - aspect_ratio (opcional, default '9:16')
    """
    data = request.get_json()
    image_path = data['image_path']
    prompt = data['prompt']
    duration = int(data.get('duration_seconds', 3))
    aspect_ratio = data.get('aspect_ratio', '9:16')

    logger.info(f"🎥 Veo 2: image->video | image={image_path} dur={duration}s ar={aspect_ratio}")

    try:
        # Importação lazy para evitar problemas caso o SDK não esteja disponível no load do app
        from services.veo_video_service import VeoVideoService  # type: ignore
        veo_service = VeoVideoService()

        # Tentar Veo primeiro
        video_url = None
        try:
            video_url = veo_service.image_to_video(
                image_path=image_path,
                prompt=prompt,
                duration_seconds=duration,
                aspect_ratio=aspect_ratio,
            )
            
            if video_url:
                return jsonify({
                    "success": True,
                    "video": video_url,
                    "provider": "vertex_veo",
                    "generated_at": datetime.now().isoformat()
                })
            else:
                # Se Veo retornou None, tenta Leonardo
                raise Exception("Veo API indisponível - tentando fallback")
                
        except Exception as veo_error:
            error_msg = str(veo_error).lower()
            if "quota" in error_msg or "rate limit" in error_msg or "indisponível" in error_msg:
                logger.warning(f"⚠️ Veo indisponível (quota/rate limit), tentando Leonardo como fallback...")
                
                # Fallback para Leonardo Animation
                try:
                    import asyncio
                    from services.advanced_image_service import AdvancedImageService
                    leonardo_service = AdvancedImageService()
                    
                    # Leonardo method is async, so we need to run it in event loop
                    video_url = asyncio.run(leonardo_service.animate_image_with_leonardo(
                        image_path=image_path,
                        motion_prompt=prompt
                    ))
                    
                    if video_url:
                        return jsonify({
                            "success": True,
                            "video": video_url,
                            "provider": "leonardo_animation",
                            "fallback_reason": "veo_quota_exceeded",
                            "generated_at": datetime.now().isoformat()
                        })
                except Exception as leonardo_error:
                    logger.error(f"❌ Fallback Leonardo também falhou: {leonardo_error}")
            
            # Re-raise o erro original do Veo se não for quota/rate limit
            raise veo_error

        return jsonify({"success": False, "error": "Falha na geração com Veo e Leonardo"}), 500
    except Exception as e:
        logger.error(f"❌ Erro no endpoint Veo image->video: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/production/render-complete-video', methods=['POST'])
@handle_errors
@limiter.limit("2 per minute")  # Limite baixo pois renderização é pesada
def render_complete_video_endpoint():
    """
    Endpoint para renderização completa de vídeo usando pipeline otimizado:
    Storyboard -> Imagens -> TTS (ElevenLabs) -> Motion (Leonardo) -> Vídeo Final
    """
    try:
        if not request.is_json:
            return jsonify({"error": "Content-Type deve ser application/json"}), 400

        data = request.get_json()
        logger.info(
            f"📹 Dados recebidos para render completo: {list(data.keys())}")

        # Controle de idempotência para render completo
        job_key = _stable_hash_for_video_request(data)
        now = time.time()
        with _JOBS_LOCK:
            _cleanup_old_jobs(now)
            cached = _COMPLETED_VIDEO_JOBS.get(job_key)
            if cached:
                logger.info("♻️ Retornando resultado recente do pipeline completo (idempotente)")
                return jsonify(cached['result'])
            if job_key in _ACTIVE_VIDEO_JOBS:
                logger.info("⏳ Pipeline completo já em execução para este payload")
                return jsonify({
                    "success": True,
                    "status": "in_progress",
                    "message": "Renderização já em execução para este payload. Evite chamadas duplicadas.",
                    "job_key": job_key
                }), 202
            _ACTIVE_VIDEO_JOBS[job_key] = {"started_at": now}

        # Validação de dados obrigatórios
        storyboard_data = data.get('storyboard') or data.get('storyboard_data')
        if not storyboard_data:
            return jsonify({"error": "Campo 'storyboard' é obrigatório"}), 400
        # Aceitar storyboard como string JSON
        if isinstance(storyboard_data, str):
            try:
                storyboard_data = json.loads(storyboard_data)
            except Exception:
                logger.error("❌ 'storyboard' enviado como string mas não é JSON válido")
                return jsonify({"error": "'storyboard' deve ser objeto ou JSON válido"}), 400

        scenes = storyboard_data.get('scenes', []) if isinstance(storyboard_data, dict) else []
        if not scenes:
            return jsonify({"error": "Storyboard deve conter 'scenes'"}), 400

        # Configurações do pipeline
        settings = data.get('settings', {})
        voice_id = settings.get('elevenlabs_voice', 'Rachel')
        image_provider = settings.get('image_provider', 'openai')
        music_path = settings.get('background_music')

        logger.info(f"🎬 Iniciando pipeline completo para {len(scenes)} cenas")
        logger.info(f"   Voz: {voice_id}")
        logger.info(f"   Provider de imagem: {image_provider}")

        # Criar workspace temporário
        import tempfile
        import shutil
        from pathlib import Path

        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)

            # Caminhos
            storyboard_path = workspace / "storyboard.json"
            output_path = workspace / "final.mp4"

            # Salvar storyboard
            with open(storyboard_path, 'w', encoding='utf-8') as f:
                json.dump(storyboard_data, f, indent=2, ensure_ascii=False)

            try:
                # Executar pipeline completo
                import subprocess
                import sys

                cmd = [
                    sys.executable, "complete_pipeline.py",
                    "--storyboard", str(storyboard_path),
                    "--work-dir", str(workspace),
                    "--out", str(output_path),
                    "--image-provider", image_provider,
                    "--voice-id", voice_id
                ]

                if music_path:
                    cmd.extend(["--music", music_path])

                logger.info(f"🚀 Executando: {' '.join(cmd)}")

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd=os.path.dirname(os.path.abspath(__file__)),
                    timeout=1800  # 30 minutos timeout
                )

                if result.returncode != 0:
                    logger.error(f"❌ Pipeline falhou: {result.stderr}")
                    return jsonify({
                        "success": False,
                        "error": f"Pipeline falhou: {result.stderr}"
                    }), 500

                # Verificar se vídeo foi gerado
                if not output_path.exists():
                    return jsonify({
                        "success": False,
                        "error": "Vídeo final não foi gerado"
                    }), 500

                # Mover vídeo para diretório de mídia
                import uuid
                final_filename = f"complete_video_{uuid.uuid4().hex[:8]}.mp4"
                final_path = str(config.VIDEO_DIR / final_filename)

                shutil.copy2(str(output_path), final_path)

                # Duração opcional (evitar dependência de moviepy aqui)
                duration = None

                logger.info(f"✅ Renderização completa concluída: {final_path}")

                result_json = {
                    "success": True,
                    "message": "Vídeo renderizado com sucesso",
                    "video_path": f"/media/videos/{final_filename}",
                    "duration": duration,
                    "scenes_count": len(scenes),
                    "pipeline_output": result.stdout,
                    "timestamp": datetime.now().isoformat(),
                    "job_key": job_key
                }

                with _JOBS_LOCK:
                    _ACTIVE_VIDEO_JOBS.pop(job_key, None)
                    _COMPLETED_VIDEO_JOBS[job_key] = {"finished_at": time.time(), "result": result_json}

                return jsonify(result_json)

            except subprocess.TimeoutExpired:
                logger.error("❌ Pipeline timeout (30 minutos)")
                with _JOBS_LOCK:
                    _ACTIVE_VIDEO_JOBS.pop(job_key, None)
                return jsonify({
                    "success": False,
                    "error": "Pipeline timeout - renderização muito longa"
                }), 500
            except Exception as e:
                logger.error(f"❌ Erro na execução do pipeline: {e}")
                with _JOBS_LOCK:
                    _ACTIVE_VIDEO_JOBS.pop(job_key, None)
                return jsonify({
                    "success": False,
                    "error": f"Erro na execução: {str(e)}"
                }), 500

    except Exception as e:
        logger.error(
            f"❌ Erro no endpoint de renderização completa: {e}", exc_info=True)
        with _JOBS_LOCK:
            _ACTIVE_VIDEO_JOBS.pop(job_key, None)
        return jsonify({
            "success": False,
            "error": f"Erro interno: {str(e)}"
        }), 500


@app.route('/api/production/leonardo-motion-prompts', methods=['GET'])
@handle_errors
def get_leonardo_motion_prompts():
    """Retorna prompts de movimento pré-definidos para Leonardo AI"""
    try:
        prompts = advanced_image_service.get_leonardo_motion_prompts()
        return jsonify({
            "success": True,
            "motion_prompts": prompts
        })
    except Exception as e:
        logger.error(f"❌ Erro ao buscar prompts de movimento: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# ===== PROMPT OPTIMIZATION ENDPOINTS =====

@app.route('/api/production/optimize-prompts', methods=['POST'])
@handle_errors
@validate_json('script', 'image_prompts')
def optimize_prompts():
    """Otimiza prompts de imagem e movimento"""
    data = request.get_json()
    script = data['script']
    image_prompts = data['image_prompts']
    style = data.get('style', 'historia_documentario')
    duration = data.get('duration', 60.0)
    provider = data.get('image_provider') or data.get('provider') or 'hybrid'

    logger.info(f"🎯 Otimizando prompts para estilo: {style}")

    try:
        # Criar cenas otimizadas
        optimized_scenes = prompt_optimizer.create_optimized_scenes(
            script, image_prompts, duration, style, provider
        )

        if optimized_scenes:
            scenes_data = []
            for scene in optimized_scenes:
                scenes_data.append({
                    "start_time": scene.start_time,
                    "end_time": scene.end_time,
                    "duration": scene.end_time - scene.start_time,
                    "text": scene.text,
                    "intensity": scene.intensity,
                    "image_prompt": scene.image_prompt,
                    "motion_prompt": scene.motion_prompt,
                    "sfx_cue": scene.sfx_cue
                })

            return jsonify({
                "success": True,
                "optimized_scenes": scenes_data,
                "total_scenes": len(scenes_data),
                "style": style,
                "provider": provider,
                "total_duration": duration
            })
        else:
            return jsonify({
                "success": False,
                "error": "Não foi possível otimizar os prompts"
            }), 500

    except Exception as e:
        logger.error(f"❌ Erro na otimização de prompts: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/production/visual-styles', methods=['GET'])
@handle_errors
def get_visual_styles():
    """Retorna estilos visuais disponíveis"""
    try:
        styles = prompt_optimizer.get_available_styles()
        return jsonify({
            "success": True,
            "styles": styles
        })
    except Exception as e:
        logger.error(f"❌ Erro ao buscar estilos visuais: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/production/analyze-script-intensity', methods=['POST'])
@handle_errors
@validate_json('script')
def analyze_script_intensity():
    """Analisa a intensidade dramática do script"""
    data = request.get_json()
    script = data['script']

    try:
        # Dividir em frases e analisar cada uma
        sentences = [s.strip() for s in script.split('.') if s.strip()]

        analysis = []
        for i, sentence in enumerate(sentences):
            intensity = prompt_optimizer.analyze_script_intensity(sentence)
            analysis.append({
                "scene": i + 1,
                "text": sentence,
                "intensity": intensity,
                "suggested_motion": prompt_optimizer.optimize_motion_prompt(sentence, intensity)
            })

        return jsonify({
            "success": True,
            "script_analysis": analysis,
            "total_scenes": len(analysis)
        })

    except Exception as e:
        logger.error(f"❌ Erro na análise de intensidade: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# ===== ELEVENLABS TTS ENDPOINTS =====

@app.route('/api/production/generate-elevenlabs-audio', methods=['POST'])
@handle_errors
def generate_elevenlabs_audio():
    """Gera áudio usando ElevenLabs TTS"""
    data = request.get_json()

    # Aceita tanto 'script' quanto 'text' como entrada
    script = data.get('script') or data.get('text')
    if not script:
        return jsonify({"error": "Campo 'script' ou 'text' é obrigatório"}), 400

    # Suporte para voice_profile ou voice_id
    voice_profile = data.get('voice_profile') or data.get(
        'voice_id', 'male-professional')
    voice_settings = data.get('voice_settings', {})

    # Configurações específicas do ElevenLabs se fornecidas
    if 'stability' in data:
        voice_settings['stability'] = data['stability']
    if 'similarity_boost' in data:
        voice_settings['similarity_boost'] = data['similarity_boost']

    logger.info(f"🎤 Gerando áudio ElevenLabs - Perfil: {voice_profile}")

    try:
        async def generate_audio_async():
            return await elevenlabs_tts.generate_audio(script, voice_profile, voice_settings)

        # Executar async
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        audio_path = loop.run_until_complete(generate_audio_async())
        loop.close()

        if audio_path:
            return jsonify({
                "success": True,
                "audio_path": audio_path,
                "audio_url": audio_path if audio_path.startswith('/media/') else f"/media/audio/{Path(audio_path).name}",
                "voice_profile": voice_profile,
                "generated_at": datetime.now().isoformat()
            })
        else:
            return jsonify({
                "success": False,
                "error": "Falha na geração de áudio"
            }), 500

    except Exception as e:
        logger.error(f"❌ Erro na geração de áudio ElevenLabs: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/production/elevenlabs-voices', methods=['GET'])
@handle_errors
def get_elevenlabs_voices():
    """Retorna vozes disponíveis do ElevenLabs"""
    try:
        async def get_voices_async():
            return await elevenlabs_tts.get_available_voices()

        # Executar async
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        voices = loop.run_until_complete(get_voices_async())
        loop.close()

        # Também incluir vozes pré-configuradas
        preconfigured = elevenlabs_tts.get_preconfigured_voices()

        return jsonify({
            "success": True,
            "available_voices": voices,
            "preconfigured_voices": preconfigured
        })

    except Exception as e:
        logger.error(f"❌ Erro ao buscar vozes ElevenLabs: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/production/clone-voice', methods=['POST'])
@handle_errors
@validate_json('audio_file', 'voice_name')
def clone_voice_endpoint():
    """Clona uma voz usando ElevenLabs"""
    data = request.get_json()
    audio_file = data['audio_file']
    voice_name = data['voice_name']

    logger.info(f"🎭 Clonando voz: {voice_name}")

    try:
        # Converter URL para caminho local se necessário
        if audio_file.startswith('/media/'):
            # Remove '/media/'
            local_path = str(config.MEDIA_DIR / audio_file[7:])
        else:
            local_path = audio_file

        async def clone_voice_async():
            return await elevenlabs_tts.clone_voice(local_path, voice_name)

        # Executar async
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        voice_id = loop.run_until_complete(clone_voice_async())
        loop.close()

        if voice_id:
            return jsonify({
                "success": True,
                "voice_id": voice_id,
                "voice_name": voice_name,
                "cloned_at": datetime.now().isoformat()
            })
        else:
            return jsonify({
                "success": False,
                "error": "Falha na clonagem de voz"
            }), 500

    except Exception as e:
        logger.error(f"❌ Erro na clonagem de voz: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# ===== HYBRID TTS ENDPOINTS (GOOGLE + ELEVENLABS) =====

@app.route('/api/production/generate-google-tts', methods=['POST'])
@handle_errors
def generate_google_tts():
    """Gera áudio especificamente usando Google Cloud TTS"""
    data = request.get_json()

    script = data.get('script') or data.get('text')
    if not script:
        return jsonify({"error": "Campo 'script' ou 'text' é obrigatório"}), 400

    voice_profile = data.get('voice_profile', 'mystery')
    speed = data.get('speed', 1.0)

    logger.info(
        f"🎵 Gerando áudio Google TTS - Perfil: {voice_profile}, Velocidade: {speed}x")

    try:
        from services.optimized_tts_service import OptimizedTTSService
        tts_service = OptimizedTTSService()

        async def generate_google_audio():
            return await tts_service.generate_optimized_audio(
                script,
                voice_profile=voice_profile,
                custom_speed=speed
            )

        # Executar async
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(generate_google_audio())
        loop.close()

        if result and result.get('success'):
            return jsonify({
                "success": True,
                "provider": "google_tts",
                "audio_path": result.get('audio_path'),
                "audio_url": result.get('audio_url'),
                "voice_profile": voice_profile,
                "speed": speed,
                "generated_at": datetime.now().isoformat()
            })
        else:
            return jsonify({
                "success": False,
                "provider": "google_tts",
                "error": result.get('error', 'Falha na geração de áudio')
            }), 500

    except Exception as e:
        logger.error(f"❌ Erro na geração Google TTS: {e}")
        return jsonify({
            "success": False,
            "provider": "google_tts",
            "error": str(e)
        }), 500


@app.route('/api/production/generate-hybrid-tts', methods=['POST'])
@handle_errors
def generate_hybrid_tts():
    """Endpoint inteligente que tenta ElevenLabs primeiro, depois Google TTS como fallback"""
    data = request.get_json()

    script = data.get('script') or data.get('text')
    if not script:
        return jsonify({"error": "Campo 'script' ou 'text' é obrigatório"}), 400

    # Configurações para ambos os serviços
    voice_profile = data.get('voice_profile') or data.get(
        'voice_id', 'male-professional')
    voice_settings = data.get('voice_settings', {})
    speed = data.get('speed', 1.0)

    # Configurações específicas do ElevenLabs
    if 'stability' in data:
        voice_settings['stability'] = data['stability']
    if 'similarity_boost' in data:
        voice_settings['similarity_boost'] = data['similarity_boost']

    # 'elevenlabs' ou 'google'
    prefer_provider = data.get('prefer_provider', 'elevenlabs')

    logger.info(
        f"🎭 Tentando TTS Híbrido - Preferência: {prefer_provider}, Voz: {voice_profile}")

    # Função para tentar ElevenLabs
    async def try_elevenlabs():
        try:
            return await elevenlabs_tts.generate_audio(script, voice_profile, voice_settings)
        except Exception as e:
            logger.warning(f"⚠️ ElevenLabs falhou: {e}")
            return None

    # Função para usar Google TTS
    async def try_google():
        try:
            from services.optimized_tts_service import OptimizedTTSService
            tts_service = OptimizedTTSService()

            # Mapear perfis ElevenLabs para Google
            google_profile = voice_profile
            if 'male' in voice_profile:
                google_profile = 'mystery' if 'dramatic' in voice_profile else 'tech'
            elif 'female' in voice_profile:
                google_profile = 'story' if 'dramatic' in voice_profile else 'tutorial'

            result = await tts_service.generate_optimized_audio(script, voice_profile=google_profile, custom_speed=speed)
            return result.get('audio_path') if result and result.get('success') else None
        except Exception as e:
            logger.warning(f"⚠️ Google TTS falhou: {e}")
            return None

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        audio_path = None
        provider_used = None

        if prefer_provider == 'elevenlabs':
            # Tentar ElevenLabs primeiro
            logger.info("🎤 Tentando ElevenLabs primeiro...")
            audio_path = loop.run_until_complete(try_elevenlabs())
            if audio_path:
                provider_used = "elevenlabs"
            else:
                logger.info("🔄 Fallback para Google TTS...")
                result = loop.run_until_complete(try_google())
                if result:
                    audio_path = result
                    provider_used = "google_tts"
        else:
            # Tentar Google primeiro
            logger.info("🎵 Tentando Google TTS primeiro...")
            result = loop.run_until_complete(try_google())
            if result:
                audio_path = result
                provider_used = "google_tts"
            else:
                logger.info("🔄 Fallback para ElevenLabs...")
                audio_path = loop.run_until_complete(try_elevenlabs())
                if audio_path:
                    provider_used = "elevenlabs"

        loop.close()

        if audio_path:
            return jsonify({
                "success": True,
                "provider": provider_used,
                "audio_path": audio_path,
                "audio_url": audio_path if audio_path.startswith('/media/') else (f"/media/audio/{Path(audio_path).name}" if audio_path else None),
                "voice_profile": voice_profile,
                "fallback_used": provider_used != prefer_provider,
                "generated_at": datetime.now().isoformat()
            })
        else:
            return jsonify({
                "success": False,
                "error": "Ambos os serviços de TTS falharam",
                "providers_tried": ["elevenlabs", "google_tts"]
            }), 500

    except Exception as e:
        logger.error(f"❌ Erro no TTS Híbrido: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/production/tts-providers', methods=['GET'])
@handle_errors
def get_tts_providers():
    """Lista todos os provedores de TTS disponíveis e seus status"""

    async def check_elevenlabs_status():
        try:
            voices = await elevenlabs_tts.get_available_voices()
            return {"available": True, "voice_count": len(voices)}
        except Exception as e:
            return {"available": False, "error": str(e)}

    def check_google_status():
        try:
            from services.optimized_tts_service import OptimizedTTSService
            tts_service = OptimizedTTSService()
            return {"available": True, "voice_profiles": ["mystery", "tech", "story", "tutorial", "comedy"]}
        except Exception as e:
            return {"available": False, "error": str(e)}

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        elevenlabs_status = loop.run_until_complete(check_elevenlabs_status())
        loop.close()

        google_status = check_google_status()

        return jsonify({
            "success": True,
            "providers": {
                "elevenlabs": {
                    "name": "ElevenLabs TTS",
                    "description": "TTS premium com vozes naturais e clonagem de voz",
                    "status": elevenlabs_status,
                    "endpoints": ["/api/production/generate-elevenlabs-audio", "/api/production/elevenlabs-voices", "/api/production/clone-voice"]
                },
                "google_tts": {
                    "name": "Google Cloud TTS",
                    "description": "TTS confiável do Google com múltiplos perfis de voz",
                    "status": google_status,
                    "endpoints": ["/api/production/generate-google-tts", "/api/production/generate-audio"]
                },
                "hybrid": {
                    "name": "TTS Híbrido",
                    "description": "Sistema inteligente que escolhe o melhor provedor automaticamente",
                    "status": {"available": True},
                    "endpoints": ["/api/production/generate-hybrid-tts"]
                }
            },
            "recommendations": {
                "premium_quality": "elevenlabs",
                "reliability": "google_tts",
                "best_of_both": "hybrid"
            }
        })

    except Exception as e:
        logger.error(f"❌ Erro ao verificar provedores TTS: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# ===== ENDPOINTS DE GERAÇÃO DE PROMPTS ULTRA-DETALHADOS =====

@app.route('/api/production/generate-image-prompts', methods=['POST'])
@handle_errors
@validate_json('theme', 'duration')
@limiter.limit("5 per minute")
def generate_image_prompts_endpoint():
    """Gera prompts ultra-detalhados para DALL-E, Imagen 3 e Imagen 4"""
    try:
        data = request.get_json()
        theme = data['theme']
        duration = data.get('duration', 60)
        script_data = data.get('script_data', {})
        
        logger.info(f"🎨 Gerando prompts de imagem para tema: {theme} ({duration}s)")
        
        # Gerar prompts usando o sistema atualizado
        result = prompt_optimizer.generate_textarea_prompts(
            theme=theme,
            target_duration_seconds=duration,
            script_data=script_data
        )
        
        return jsonify({
            "success": True,
            "image_prompts_textarea": result.get("image_prompts", ""),
            "video_info": result.get("video_info", {}),
            "message": f"Prompts de imagem gerados para {duration}s de vídeo"
        })
        
    except Exception as e:
        logger.error(f"❌ Erro ao gerar prompts de imagem: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/production/generate-animation-prompts', methods=['POST'])
@handle_errors
@validate_json('theme', 'duration')
@limiter.limit("5 per minute")
def generate_animation_prompts_endpoint():
    """Gera prompts ultra-detalhados para Leonardo AI e Veo 2"""
    try:
        data = request.get_json()
        theme = data['theme']
        duration = data.get('duration', 60)
        script_data = data.get('script_data', {})
        
        logger.info(f"🎬 Gerando prompts de animação para tema: {theme} ({duration}s)")
        
        # Gerar prompts usando o sistema atualizado  
        result = prompt_optimizer.generate_textarea_prompts(
            theme=theme,
            target_duration_seconds=duration,
            script_data=script_data
        )
        
        return jsonify({
            "success": True,
            "animation_prompts_textarea": result.get("animation_prompts", ""),
            "video_info": result.get("video_info", {}),
            "message": f"Prompts de animação gerados para {duration}s de vídeo"
        })
        
    except Exception as e:
        logger.error(f"❌ Erro ao gerar prompts de animação: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/production/generate-all-prompts', methods=['POST'])
@handle_errors
@validate_json('theme', 'duration')
@limiter.limit("3 per minute")
def generate_all_prompts_endpoint():
    """Gera todos os prompts (imagem + animação) de uma vez"""
    try:
        data = request.get_json()
        theme = data['theme']
        duration = data.get('duration', 60)
        script_data = data.get('script_data', {})
        
        logger.info(f"🚀 Gerando TODOS os prompts para tema: {theme} ({duration}s)")
        
        # Gerar todos os prompts de uma vez
        result = prompt_optimizer.generate_textarea_prompts(
            theme=theme,
            target_duration_seconds=duration,
            script_data=script_data
        )
        
        # Também gerar prompts otimizados para YouTube Shorts
        youtube_optimized = prompt_optimizer.optimize_prompts_for_youtube_shorts(
            theme=theme,
            script_data=script_data or {}
        )
        
        return jsonify({
            "success": True,
            "image_prompts_textarea": result.get("image_prompts", ""),
            "animation_prompts_textarea": result.get("animation_prompts", ""),
            "video_info": result.get("video_info", {}),
            "youtube_optimization": youtube_optimized,
            "calculation_info": {
                "total_duration": duration,
                "num_prompts_needed": prompt_optimizer.calculate_number_of_prompts(duration),
                "seconds_per_image": prompt_optimizer.SECONDS_PER_IMAGE
            },
            "message": f"Prompts completos gerados: {duration}s de vídeo em {prompt_optimizer.calculate_number_of_prompts(duration)} cenas"
        })
        
    except Exception as e:
        logger.error(f"❌ Erro ao gerar todos os prompts: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/production/prompt-platform-info', methods=['GET'])
@handle_errors
def get_prompt_platform_info():
    """Retorna informações sobre as plataformas de IA suportadas"""
    try:
        capabilities = prompt_optimizer.get_platform_capabilities()
        styles = prompt_optimizer.get_available_styles()
        
        return jsonify({
            "success": True,
            "image_platforms": capabilities.get("image_platforms", {}),
            "video_platforms": capabilities.get("video_platforms", {}),
            "visual_styles": styles,
            "system_config": {
                "seconds_per_image": prompt_optimizer.SECONDS_PER_IMAGE,
                "supported_durations": [15, 30, 45, 60, 90, 120, 180],
                "optimal_duration": "60 seconds (20 prompts)",
                "max_recommended_duration": 180
            },
            "message": "Informações das plataformas de IA carregadas com sucesso"
        })
        
    except Exception as e:
        logger.error(f"❌ Erro ao obter informações das plataformas: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/production/calculate-prompts', methods=['POST'])
@handle_errors 
@validate_json('duration')
def calculate_prompts_needed():
    """Calcula quantos prompts são necessários para uma duração específica"""
    try:
        data = request.get_json()
        duration = data['duration']
        
        num_prompts = prompt_optimizer.calculate_number_of_prompts(duration)
        actual_duration = prompt_optimizer.calculate_video_duration(num_prompts)
        
        return jsonify({
            "success": True,
            "target_duration": duration,
            "num_prompts_needed": num_prompts,
            "actual_duration": actual_duration,
            "seconds_per_image": prompt_optimizer.SECONDS_PER_IMAGE,
            "calculation_details": {
                "formula": f"{duration}s ÷ {prompt_optimizer.SECONDS_PER_IMAGE}s = {num_prompts} prompts",
                "result": f"{num_prompts} prompts × {prompt_optimizer.SECONDS_PER_IMAGE}s = {actual_duration}s de vídeo",
                "difference": actual_duration - duration
            },
            "message": f"Para {duration}s de vídeo: {num_prompts} prompts necessários"
        })
        
    except Exception as e:
        logger.error(f"❌ Erro no cálculo de prompts: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# ===== MAIN APP EXECUTION =====
if __name__ == '__main__':
    print("🚀 Iniciando TikTok Automation API v2.0 - Dashboard Suprema")
    debug_mode = os.getenv('FLASK_ENV') == 'development'
    socketio.run(
        app,
        host=config.API_HOST,
        port=config.API_PORT,
        debug=debug_mode,
        use_reloader=debug_mode,
        allow_unsafe_werkzeug=True
    )
