# /var/www/tiktok-automation/backend/enhanced_content_generator.py

import json
import random
from typing import Dict, List, Any, Optional, Tuple
import re
from dataclasses import dataclass
from enum import Enum
import os
import logging
from datetime import datetime

# Importa as classes de serviço
from gemini_client import GeminiClient
from gemini_prompts import GeminiPrompts
# from viral_analyzer import ViralAnalyzer  # Migrado para ai_orchestrator.py
# from vertex_client import VertexClient  # Nova classe para TTS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mantém as classes Enum e dataclass para a tipagem


class ContentQuality(Enum):
    ELITE = "elite"
    PREMIUM = "premium"
    STANDARD = "standard"
    BASIC = "basic"


@dataclass
class ViralElements:
    emotional_triggers: List[str]
    curiosity_gaps: List[str]
    pattern_interrupts: List[str]
    social_proof_elements: List[str]
    urgency_factors: List[str]
    relatability_score: float
    shareability_score: float


class EnhancedContentGenerator:
    """
    Orquestrador de Geração de Conteúdo.
    Responsável por chamar as APIs de IA para gerar roteiro e áudio.
    """

    def __init__(self):
        # O GeminiClient já lida com o modelo correto e as credenciais
        self.gemini_client = GeminiClient()
        # self.vertex_client = VertexClient()  # Instancia o cliente da Vertex AI
        self.prompts = GeminiPrompts()
        # self.analyzer = ViralAnalyzer()  # Migrado para ai_orchestrator.py

    def gerar_conteudo_completo(self, settings: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Gera o roteiro, o áudio e a análise de forma otimizada.
        """
        logger.info(
            "🎬 Iniciando geração de conteúdo completo (roteiro + áudio)...")

        # 1. Análise Viral para definir a melhor estratégia
        viral_analysis = self.analyzer._analyze_viral_potential(settings)
        strategy = self.analyzer._select_viral_strategy(
            settings.get('theme', 'geral'))

        # 2. Geração do Roteiro
        content = self._generate_content_candidate(settings, strategy)

        if not content:
            logger.warning("❌ Nenhuma IA conseguiu gerar um roteiro válido.")
            return None

        # 3. Análise e Aprimoramento do Roteiro
        viral_score = self.analyzer._calculate_viral_score(content)
        enhanced_content = self._apply_viral_enhancements(content)

        enhanced_content.update({
            'viral_score': viral_score,
            'viral_strategy': strategy,
            'quality_tier': self.analyzer._determine_quality_tier(viral_score).value,
            'viral_elements': self.analyzer._extract_viral_elements(enhanced_content)
        })

        # 4. Preparação do Roteiro para TTS e Geração do Áudio
        final_content = self.preparar_e_gerar_audio(enhanced_content)

        logger.info(
            f"✅ Geração completa concluída com sucesso. Score: {enhanced_content.get('viral_score', 0):.2f}")
        return final_content

    def _generate_content_candidate(self, settings: Dict[str, Any], strategy: str) -> Optional[Dict[str, Any]]:
        """
        Gera um único candidato de conteúdo, com o prompt aprimorado.
        """
        # Itera para ter múltiplas tentativas se a primeira falhar
        for i in range(3):
            prompt = self.prompts.build_viral_prompt(settings, strategy, i)

            try:
                response_text = self.gemini_client.generate_content(prompt)
                if response_text:
                    content_data = self.gemini_client.process_response(
                        response_text)
                    if content_data and 'roteiro_completo' in content_data:
                        content_data['strategy'] = strategy
                        content_data['iteration'] = i
                        return content_data
            except Exception as e:
                logger.error(
                    f"❌ Erro na tentativa {i+1} de gerar roteiro com Gemini: {e}")

        return None

    def _apply_viral_enhancements(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Aplica melhorias no roteiro gerado, como otimização de hashtags e elementos."""
        content['hashtags'] = self.analyzer._optimize_hashtags(
            content.get('hashtags', []))
        content['storytelling_elements'] = self.analyzer._extract_story_elements(
            content)

        # Extrai sugestões visuais do próprio roteiro, se não existirem
        if 'visual_cues' not in content or not content['visual_cues']:
            content['visual_cues'] = self.analyzer._generate_visual_cues(
                content)

        content['share_triggers'] = self.analyzer._identify_share_triggers(
            content)
        return content

    def preparar_e_gerar_audio(self, content_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Prepara o roteiro para TTS (convertendo para SSML) e gera o áudio.
        """
        roteiro_completo = content_data.get('roteiro_completo', '')

        if not roteiro_completo:
            logger.error("❌ Roteiro vazio, não é possível gerar áudio.")
            return None

        try:
            # 1. Processa o texto com as marcações [VOZ], [PAUSA], etc., para criar o SSML.
            ssml_text = self._process_to_ssml(roteiro_completo)

            # 2. Extrai os parâmetros globais de TTS, como emoção e sotaque.
            tts_params = self._extract_tts_params(roteiro_completo)

            # 3. Gera o arquivo de áudio com a Vertex AI.
            output_dir = 'media/audio'  # O diretório onde o arquivo será salvo
            os.makedirs(output_dir, exist_ok=True)
            filename = f'audio_{datetime.now().strftime("%Y%m%d%H%M%S")}.mp3'
            output_path = os.path.join(output_dir, filename)

            audio_path = self.vertex_client.generate_audio(
                ssml_text=ssml_text,
                tts_params=tts_params,
                output_path=output_path
            )

            if audio_path:
                content_data['audio_path'] = audio_path
                return content_data
            else:
                logger.error("❌ Falha na geração do áudio com a Vertex AI.")
                return None

        except Exception as e:
            logger.error(f"❌ Erro ao preparar e gerar áudio: {e}")
            return None

    def _process_to_ssml(self, roteiro_completo: str) -> str:
        """
        Converte as marcações personalizadas do roteiro em SSML.
        """
        pattern = r"\[VOZ:\s*(.*?)\]|\[PAUSA:\s*(.*?)\]|\[Ênfase:\s*(.*?)\]"
        ssml_content = []
        last_end = 0

        for match in re.finditer(pattern, roteiro_completo):
            text_before = roteiro_completo[last_end:match.start()].strip()
            if text_before:
                ssml_content.append(text_before)

            voz_match, pausa_match, enfase_match = match.groups()

            if voz_match:
                attrs = {p.split(':')[0].strip(): p.split(
                    ':')[1].strip() for p in voz_match.split(',')}
                # Simplificação: A Vertex AI não suporta emoções dinâmicas em todas as vozes via SSML.
                # A forma mais segura é extrair e usar na requisição.
                ssml_content.append(f"<break time=\"0.5s\"/>")
            elif pausa_match:
                ssml_content.append(f"<break time=\"{pausa_match}\"/>")
            elif enfase_match:
                ssml_content.append(f"<emphasis>{enfase_match}</emphasis>")

            last_end = match.end()

        text_after = roteiro_completo[last_end:].strip()
        if text_after:
            ssml_content.append(text_after)

        final_ssml = " ".join(ssml_content)
        return f"<speak>{final_ssml}</speak>"

    def _extract_tts_params(self, roteiro_completo: str) -> Dict[str, Any]:
        """
        Extrai parâmetros globais de TTS, como sotaque e emoção principal,
        para serem usados na requisição à Vertex AI.
        """
        params = {
            'voice_emotion': 'neutral',
            'voice_accent': 'pt-BR',
            'voice_gender': 'MALE',
            'voice_name': 'pt-BR-Wavenet-B'
        }

        match = re.search(r"\[VOZ:\s*(.*?)\]", roteiro_completo)
        if match:
            attrs = {p.split(':')[0].strip(): p.split(':')[1].strip()
                     for p in match.group(1).split(',')}
            if 'Emoção' in attrs:
                params['voice_emotion'] = attrs['Emoção'].lower()
            if 'Sotaque' in attrs:
                params['voice_accent'] = self.analyzer._map_accent_to_locale(
                    attrs['Sotaque'])

        return params

    def _map_accent_to_locale(self, accent: str) -> str:
        """Mapeia sotaque de texto para código de localidade da Vertex AI."""
        mapping = {
            'brasileiro': 'pt-BR',
            'português': 'pt-PT',
            'americano': 'en-US',
            'britânico': 'en-GB'
        }
        return mapping.get(accent.lower(), 'pt-BR')

    # Métodos de compatibilidade (mantidos para não quebrar a lógica antiga)
    def gerar_conteudo_viral_otimizado(self, settings: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        # Redireciona para o novo método principal
        return self.gerar_conteudo_completo(settings)

    def gerar_conteudo_personalizado(self, settings: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        # Redireciona para o novo método principal
        return self.gerar_conteudo_completo(settings)

    # O `criar_variacao_conteudo` pode ser mantido ou refatorado para uma classe específica de otimização


# --- NORMALIZADOR E FUNCÕES HÍBRIDAS ---

# Constantes compartilhadas para prompts históricos/científicos
HISTORY_VISUAL_PACK_EN = (
    "ultra realistic or painterly realistic, renaissance/early-modern vibes, "
    "cinematic lighting, moody shadows, volumetric light, rich textures, "
    "dark teal/orange palette, highly detailed, vertical 9:16, no text, 8K resolution"
)
HISTORY_IMAGE_SUFFIX_EN = "vertical 9:16, no text, highly detailed, 8K resolution"

MOTION_PRESET_HIGH_EN = "slow cinematic zoom in, subtle parallax, gentle camera drift, 9:16 vertical"
MOTION_PRESET_MED_EN = "gentle pan left/right, slow zoom out, subtle parallax, 9:16 vertical"

HISTORY_VISUAL_SUFFIX = "vertical 9:16, no text, highly detailed, 8K resolution"


def _ensure_hybrid_prompt_tail(prompt_text: str) -> str:
    """Garante que o prompt tenha o sufixo híbrido (serve para DALL·E-3 e Imagen 3)."""
    if prompt_text is None:
        prompt_text = ""
    tail = HISTORY_VISUAL_SUFFIX
    # Evita duplicar
    if tail.lower() not in prompt_text.lower():
        if not prompt_text.endswith(","):
            prompt_text = prompt_text.strip().rstrip(".")
            prompt_text += ", "
        prompt_text += tail
    return prompt_text


def _fallback_scenes_from_script(script: str, total_sec: int = 60):
    """Divide o texto em 6 cenas ~10s como fallback simples."""
    safe = [l.strip() for l in (script or "").split("\n") if l.strip()]
    if not safe:
        safe = [script] if script else ["Sem conteúdo"]
    chunks = 6
    step = max(1, len(safe)//chunks)
    scenes, t = [], 0
    for i in range(0, len(safe), step):
        if len(scenes) >= chunks:
            break
        part = " ".join(safe[i:i+step])[:280]
        dur = total_sec // chunks
        scenes.append({
            "t_start": t,
            "t_end": min(total_sec, t+dur),
            "narration": part,
            "on_screen_text": "",
            "image_prompt": _ensure_hybrid_prompt_tail("cinematic historic illustration, renaissance vibes, dramatic lighting"),
            "motion_prompt": "gentle pan left/right, slow zoom out, subtle parallax, 9:16 vertical",
            "intensity": "MEDIA",
            "sfx": [],
            "music_cue": "transicao" if t > 0 else "intro_suave"
        })
        t += dur
    # Ajuste do último t_end se sobrar segundos
    if scenes and scenes[-1]["t_end"] < total_sec:
        scenes[-1]["t_end"] = total_sec
    return scenes


def normalize_storyboard_payload(content_data: dict, duration_target_sec: int = 60) -> dict:
    """
    Normaliza a resposta de qualquer IA para o formato storyboard.
    - Se vier 'scenes', valida e completa.
    - Se vier só 'roteiro_completo', cria cenas fallback.
    """
    data = dict(content_data or {})
    # Texto bruto, caso precise criar cenas de fallback
    roteiro = data.get("roteiro_completo") or data.get("script") or data.get("text") or ""

    scenes = data.get("scenes")

    # Se não há cenas válidas, gera fallback a partir do texto
    if not isinstance(scenes, list) or not scenes:
        data["scenes"] = _fallback_scenes_from_script(
            roteiro, total_sec=duration_target_sec)
    else:
        # Normaliza cenas existentes e garante campos essenciais
        normalized = []
        total = int(duration_target_sec or 60)
        n = max(1, len(scenes))
        default_dur = max(3, total // n)
        current_t = 0
        for raw in scenes:
            s = dict(raw or {})
            # Timing seguro
            t_start = s.get("t_start")
            t_end = s.get("t_end")
            if not isinstance(t_start, (int, float)):
                t_start = current_t
            if not isinstance(t_end, (int, float)) or t_end <= t_start:
                t_end = min(total, (t_start or 0) + default_dur)
            s["t_start"] = int(t_start)
            s["t_end"] = int(t_end)
            current_t = int(t_end)

            # Texto/narração
            s["narration"] = s.get("narration") or ""
            s["on_screen_text"] = s.get("on_screen_text") or ""

            # Prompt de imagem com sufixo padronizado
            img = s.get("image_prompt") or ""
            s["image_prompt"] = ensure_image_suffix_en(img)

            # Defaults de movimento/efeitos
            s.setdefault("motion_prompt", MOTION_PRESET_MED_EN)
            s.setdefault("intensity", "MEDIA")
            s.setdefault("sfx", [])
            s.setdefault("music_cue", "transicao")

            normalized.append(s)

        # Garante fechamento exato no total
        if normalized and normalized[-1]["t_end"] < total:
            normalized[-1]["t_end"] = total
        data["scenes"] = normalized

    # Defaults globais
    data["audience"] = data.get("audience") or "history"
    data["visual_pack"] = data.get("visual_pack") or "HistoryDark"
    data["voice_style"] = data.get("voice_style") or "documentary_grave"
    data["music_style"] = data.get("music_style") or "tensa_cinematica"
    data["duration_target_sec"] = int(duration_target_sec or 60)
    data.setdefault("title", data.get("title") or data.get("titulo") or "História em 60s")
    data.setdefault("thumbnail", {
        "text": data["title"],
        "image_prompt": _ensure_hybrid_prompt_tail("historic cinematic thumbnail, powerful focal subject, dramatic rim light")
    })
    data.setdefault("hashtags", data.get("hashtags") or ["#historia", "#shorts", "#curiosidades"])
    return data


# Visual packs por categoria
VISUAL_PACKS = {
    "HistoryDark": "ultra realistic or painterly realistic, cinematic lighting, moody shadows, volumetric light, rich textures, dark teal/orange palette, vertical 9:16, no text, highly detailed, 8K resolution",
    "KidsCartoon": "cartoon style, friendly characters, big expressive eyes, rounded shapes, vibrant colors, soft lighting, clean outlines, vertical 9:16, no text, highly detailed"
}

# ---------- Prompt Builder para IMAGEM (EN) ----------
IMAGE_SUFFIX_EN = "vertical 9:16, no text, highly detailed, 8K resolution"


def image_pack(style_key: str = "HistoryDark") -> str:
    return VISUAL_PACKS.get(style_key, VISUAL_PACKS["HistoryDark"])


def format_image_prompt_en(
    subject: str,
    environment: str = "",
    time_of_day: str = "",
    lighting: str = "dramatic cinematic lighting, volumetric light",
    mood: str = "mysterious, tense",
    camera: str = "cinematic perspective, 50mm lens, shallow depth of field",
    composition: str = "rule of thirds, strong focal subject, balanced negative space",
    style_key: str = "HistoryDark",
) -> str:
    """
    Monta um prompt de imagem “anatomizado” e consistente para DALL·E/Imagen.
    Tudo em inglês (melhor para os modelos de imagem).
    """
    parts = [
        subject.strip(),
        environment.strip(),
        time_of_day.strip(),
        lighting.strip(),
        mood.strip(),
        camera.strip(),
        composition.strip(),
        image_pack(style_key),
        IMAGE_SUFFIX_EN,
    ]
    # limpa entradas vazias e vírgulas/espacos duplicados
    txt = ", ".join([p for p in parts if p]).replace(
        ",,", ",").strip().strip(",")
    return txt


def ensure_image_suffix_en(prompt_text: str) -> str:
    """Garante o sufixo e remove duplicatas do sufixo/pacote."""
    if not prompt_text:
        prompt_text = ""
    base = prompt_text.strip().rstrip(",. ")
    # remove duplicatas simples
    for dup in [IMAGE_SUFFIX_EN.lower(), "no text", "vertical 9:16"]:
        if base.lower().endswith(dup):
            base = base[:-(len(dup))].rstrip(",. ")
    # recoloca sufixo padronizado
    return f"{base}, {IMAGE_SUFFIX_EN}"


def build_storyboard_prompt_historia_gpt(theme: str, duration_target_sec: int = 60) -> str:
    """
    Prompt mestre para GPT (OpenAI) retornar APENAS JSON no schema storyboard histórico/científico.
    Use este texto como 'user' ou 'system', e (se disponível) configure response_format JSON.
    """
    HISTORY_VISUAL_PACK = (
        "ultra realistic or painterly realistic, renaissance/early-modern vibes, "
        "cinematic lighting, moody shadows, volumetric light, rich textures, "
        "dark teal/orange palette, highly detailed, vertical 9:16, no text, 8K resolution"
    )
    MOTION_HIGH = "slow cinematic zoom in, subtle parallax, gentle camera drift, 9:16 vertical"
    MOTION_MED = "gentle pan left/right, slow zoom out, subtle parallax, 9:16 vertical"

    return f"""
Respond ONLY with a single VALID JSON object (no markdown, no extra text).
You are creating a historical/scientific storyboard for a vertical short (~{duration_target_sec}s).
Theme: "{theme}"

{{
  "title": "Título chamativo (<=70)",
  "audience": "history",
  "visual_pack": "HistoryDark",
  "duration_target_sec": {duration_target_sec},
  "voice_style": "documentary_grave",
  "music_style": "tensa_cinematica",
  "scenes": [
    {{
      "t_start": 0,
      "t_end": 6,
    "narration": "2–3 frases naturais em pt-BR, TTS-friendly, com detalhes específicos (sem SSML).",
      "on_screen_text": "Opcional",
      "image_prompt": "Descrição objetiva da cena. Inclua: {HISTORY_VISUAL_PACK}",
      "motion_prompt": "{MOTION_HIGH}",
      "intensity": "ALTA|MEDIA",
      "sfx": ["efeitos sutis"],
      "music_cue": "intro_suave|transicao|climax|final"
    }}
  ],
  "thumbnail": {{
    "text": "Frase de capa",
    "image_prompt": "Capa coerente. Inclua: {HISTORY_VISUAL_PACK}"
  }},
  "hashtags": ["#historia","#shorts","#curiosidades"]
}}

Rules:
- 8–10 scenes of 3–12s each; total ~{duration_target_sec}s (preferably 85–100s).
- In every 'image_prompt', end with: "vertical 9:16, no text, highly detailed, 8K resolution".
- Use {MOTION_HIGH} for intensity ALTA and {MOTION_MED} for MEDIA.
- Output must be valid JSON only.
""".strip()
