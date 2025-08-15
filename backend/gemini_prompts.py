# /var/www/tiktok-automation/backend/gemini_prompts.py
import json
import random
from typing import Dict, List, Any, Optional
import re
from datetime import datetime


class GeminiPrompts:
    def __init__(self):
        # Mantenha todas as suas definições de viral_formulas e message_templates
        # Elas são a base do seu prompt e estão ótimas.
        self.viral_formulas = {
            'pattern_interrupt': {
                'structure': "Declaração chocante → Explicação → Transformação → CTA",
                'examples': [
                    "Eu estava errado sobre [X] por [Y] anos...",
                    "Pare de [ação comum]. Aqui está o porquê...",
                    "A verdade que [autoridade] não quer que você saiba..."
                ]
            },
            'story_arc': {
                'structure': "Conflito → Jornada → Descoberta → Resolução",
                'examples': [
                    "Perdi tudo aos [idade], mas descobri que...",
                    "Tentei [X] por [tempo] até que [momento pivotal]...",
                    "Todos diziam que era impossível, então eu..."
                ]
            },
            'curiosity_loop': {
                'structure': "Pergunta intrigante → Construção → Revelação parcial → Hook final",
                'examples': [
                    "O que acontece quando você [ação incomum]?",
                    "Existe um segredo que [grupo] usa para...",
                    "Por que [fenômeno comum] é na verdade [revelação]?"
                ]
            }
        }
        self.message_templates = {
            'motivational': {
                'hooks': [
                    "95% das pessoas desistem quando estão a 5% do sucesso...",
                    "A diferença entre o impossível e o possível está na sua mente",
                    "Você não precisa ser perfeito, precisa ser consistente",
                    "O que você faria se soubesse que não pode falhar?",
                    "Seu maior inimigo não é o fracasso, é o conforto",
                    "A dor de hoje é a força de amanhã",
                    "Ninguém lembra do segundo lugar, seja excepcional"
                ],
                'themes': [
                    'superação de obstáculos', 'mentalidade de crescimento', 'persistência',
                    'autoconfiança', 'transformação pessoal', 'propósito de vida',
                    'disciplina radical', 'mentalidade de campeão', 'resiliência mental'
                ],
                'viral_triggers': ['transformação', 'superação', 'antes/depois', 'desafio']
            },
            'educational': {
                'hooks': [
                    "Esta informação pode mudar completamente sua perspectiva sobre...",
                    "99% das pessoas não sabem sobre este fato científico...",
                    "A verdade por trás de... que ninguém te conta",
                    "Como isso que você faz todo dia está afetando seu cérebro",
                    "O erro #1 que está destruindo seu [objetivo]",
                    "Cientistas descobriram que [hábito comum] na verdade...",
                    "A técnica secreta que [grupo de elite] usa para..."
                ],
                'themes': [
                    'neurociência aplicada', 'hábitos e comportamento', 'psicologia cognitiva',
                    'ciência da produtividade', 'saúde mental', 'aprendizado eficaz',
                    'biohacking', 'otimização mental', 'inteligência emocional'
                ],
                'viral_triggers': ['revelação', 'ciência', 'hack', 'segredo']
            },
            'inspirational': {
                'hooks': [
                    "Se você pudesse voltar no tempo, o que diria para seu eu de 5 anos atrás?",
                    "A vida não acontece para você, acontece através de você",
                    "Todo grande sonho começou com alguém que ousou acreditar",
                    "Sua próxima versão está esperando você decidir mudá-la",
                    "O universo conspira a favor de quem age",
                    "Você é mais poderoso do que imagina",
                    "Cada escolha é uma chance de recomeçar"
                ],
                'themes': [
                    'propósito e significado', 'gratidão e mindfulness', 'conexão humana',
                    'legado pessoal', 'impacto positivo', 'evolução espiritual',
                    'manifestação', 'abundância', 'transformação quântica'
                ],
                'viral_triggers': ['emoção', 'reflexão', 'espiritualidade', 'conexão']
            },
            'controversial': {
                'hooks': [
                    "Vou dizer o que ninguém tem coragem de falar sobre...",
                    "A mentira que todo mundo acredita sobre [tema]",
                    "Por que [crença popular] está completamente errada",
                    "A verdade inconveniente sobre [assunto polêmico]"
                ],
                'themes': [
                    'verdades inconvenientes', 'mitos desmascarados', 'opiniões impopulares',
                    'realidade vs expectativa', 'tabus sociais', 'crítica construtiva'
                ],
                'viral_triggers': ['polêmica', 'debate', 'verdade', 'revelação']
            }
        }

    def _map_category_to_key(self, category: str) -> str:
        # Mantém esta função
        mapping = {
            'Motivação': 'motivational',
            'Conhecimento': 'educational',
            'Reflexão': 'inspirational',
            'Empreendedorismo': 'motivational',
            'Mindset': 'motivational',
            'Produtividade': 'educational',
            'Controvérsia': 'controversial'
        }
        return mapping.get(category, 'motivational')

    def _get_strategy_instructions(self, strategy: str) -> str:
        # Mantém esta função
        strategies = {
            'emotional_rollercoaster': """
            ESTRATÉGIA: Montanha-russa emocional
            - Comece com vulnerabilidade extrema
            - Alterne entre esperança e desespero
            - Termine com transformação épica
            - Use palavras que evocam emoções viscerais
            """,
            'pattern_interrupt': """
            ESTRATÉGIA: Interrupção de padrão
            - Abra com afirmação CHOCANTE mas verdadeira
            - Destrua uma crença comum
            - Apresente perspectiva radicalmente nova
            - Use contrastes extremos
            """,
            'curiosity_loop': """
            ESTRATÉGIA: Loop de curiosidade
            - Faça pergunta impossível de ignorar
            - Dê pistas sem revelar tudo
            - Construa tensão crescente
            - Revele de forma inesperada
            """,
            'trend_hijack': """
            ESTRATÉGIA: Sequestro de tendência
            - Conecte com trend atual
            - Adicione twist único
            - Subverta expectativas
            - Crie novo ângulo viral
            """
        }
        return strategies.get(strategy, strategies['pattern_interrupt'])

    def build_viral_prompt(self, settings: Dict[str, Any], strategy: str, iteration: int) -> str:
        topics = settings.get('custom_topics', [])
        categories = settings.get('message_categories', ['Motivação'])
        tone = settings.get('tone', 'inspirational')
        voice_emotion = settings.get('voice_emotion', 'enthusiastic')
        accent = settings.get('accent', 'brazilian')  # Adicionando sotaque

        main_category = random.choice(
            categories) if categories else 'Motivação'
        category_key = self._map_category_to_key(main_category)
        template_data = self.message_templates.get(
            category_key, self.message_templates['motivational'])

        hook_variation = iteration % len(template_data['hooks'])
        selected_hook = template_data['hooks'][hook_variation]

        viral_instructions = self._get_strategy_instructions(strategy)

        # Determinar se deve criar história em capítulos ou única
        duration_minutes = settings.get('duration', 60) / 60
        create_chapters = duration_minutes > 1.5 or settings.get('multi_chapter', False)
        
        if create_chapters:
            chapter_structure = """
        **MODO HISTÓRIA EM CAPÍTULOS ATIVADO**
        
        ESTRUTURA NARRATIVA DE CAPÍTULOS (Otimizada para plataformas):
        1. **CAPÍTULO 1 - INTRODUÇÃO:** Apresenta personagens, cenário e conflito inicial (75-90s)
        2. **CAPÍTULO 2 - DESENVOLVIMENTO:** Aprofunda o conflito, adiciona complexidade (75-90s)
        3. **CAPÍTULO 3 - CLÍMAX/RESOLUÇÃO:** Ponto alto da história e conclusão satisfatória (75-90s)
        
        CADA CAPÍTULO DEVE TER:
        - **DURAÇÃO:** 75-90 segundos cada (máximo 2 minutos para compatibilidade)
        - **HOOK PRÓPRIO:** Começo impactante que funciona independente
        - **CLIFFHANGER FORTE:** Final que gera ansiedade para próximo episódio
        - **IMAGENS ESPECÍFICAS:** 4-6 cenas visuais detalhadas por capítulo
        - **CONTINUIDADE:** Conectar naturalmente com próximo capítulo
        - **AUTONOMIA:** Cada capítulo deve fazer sentido sozinho também
            """
        else:
            chapter_structure = "**MODO HISTÓRIA ÚNICA** - Conteúdo completo em um vídeo (60-120s)"

        prompt = f"""
        Você é um roteirista especialista em STORYTELLING ENVOLVENTE e criação de conteúdo viral. Sua missão é criar histórias humanas e autênticas que conectem emocionalmente.

        {chapter_structure}

        INSTRUÇÕES ESSENCIAIS:
        1.  **STORYTELLING PESSOAL:** Crie uma história como se fosse uma experiência real, vivida por alguém. Use linguagem íntima: "Deixa eu contar uma coisa que aconteceu...", "Vocês não vão acreditar no que passei..."
        
        2.  **ESTRUTURA NARRATIVA CLÁSSICA:**
           - **SITUAÇÃO INICIAL:** Contexto pessoal/momento da vida
           - **CONFLITO/PROBLEMA:** Desafio ou descoberta surpreendente  
           - **DESENVOLVIMENTO:** Como a situação evoluiu
           - **CLÍMAX:** Momento de virada/revelação impactante
           - **RESOLUÇÃO:** Como mudou a perspectiva/vida
        
        3.  **TIMING E IMAGENS DETALHADAS:**
           Para cada momento da história, especifique:
           - **[TIMING: 0-5s]** - Momento exato da história
           - **[IMAGEM: descrição detalhada]** - Prompt específico para geração de imagem
           - **[ANIMAÇÃO LEONARDO: movimento/efeito]** - Como animar a imagem
           
        EXEMPLO DE FORMATAÇÃO:
        [TIMING: 0-5s] [VOZ: Íntimo] Deixa eu contar uma coisa que mudou minha vida completamente...
        [IMAGEM: Pessoa jovem sentada sozinha em um quarto escuro, luz azul do celular iluminando rosto pensativo, ambiente melancólico]
        [ANIMAÇÃO LEONARDO: Luz pulsando suavemente, sombras se movendo pela parede]
        
        ---

        ESTRATÉGIA VIRAL: {strategy}
        {viral_instructions}

        CONFIGURAÇÕES:
        -   **Tema da História:** {', '.join(topics) if topics else 'Crie uma história pessoal impactante na categoria ' + main_category}
        -   **Categoria:** {category_key}
        -   **Tom:** {tone}
        -   **Emoção Principal:** {voice_emotion}
        -   **Sotaque:** {accent}
        -   **Duração:** {settings.get('duration', 60)} segundos
        
        FÓRMULA DE STORYTELLING:
        1.  **HOOK PESSOAL (0-5s):** "Deixa eu contar...", "Aconteceu uma coisa..."
        2.  **CONTEXTO (5-15s):** Situação inicial, quem são os personagens
        3.  **CONFLITO (15-30s):** O problema, descoberta ou desafio
        4.  **CLÍMAX (30-45s):** Momento de virada, revelação impactante
        5.  **RESOLUÇÃO (45-60s):** Como a história terminou, lição aprendida
        
        ---

        REQUISITOS VISUAIS OBRIGATÓRIOS:
        -   **MÍNIMO 4 IMAGENS** com timing específico por história/capítulo
        -   **PROMPTS DETALHADOS** para Leonardo AI (cenário, iluminação, mood, estilo)
        -   **INSTRUÇÕES DE ANIMAÇÃO** para cada imagem (movimento de câmera, efeitos, transições)
        -   **CONTINUIDADE VISUAL** entre as cenas
        
        ---
        
        Responda APENAS com um objeto JSON válido, seguindo estritamente a seguinte estrutura. NÃO inclua qualquer texto extra fora do JSON.
        
        {{
            "tipo_conteudo": "{['capitulos', 'historia_unica'][int(create_chapters)]}",
            "titulo_geral": "Título HIPNÓTICO da história completa (max 60 chars)",
            "total_capitulos": {3 if create_chapters else 1},
            "duracao_total_estimada": {(85 * 3) if create_chapters else settings.get('duration', 90)},
            
            "capitulos": [
                {{
                    "numero": 1,
                    "titulo_capitulo": "Título específico do capítulo",
                    "hook": "Primeira frase que PARALISA o scroll",
                    "roteiro_completo": "Script detalhado com marcações [TIMING], [IMAGEM] e [ANIMAÇÃO LEONARDO] para cada momento",
                    "duracao_estimada": {85 if create_chapters else settings.get('duration', 90)},
                    "cliffhanger": "Final FORTE que gera ansiedade para próximo (só para capítulos 1-2)",
                    "compatibilidade_plataforma": "{['YouTube Shorts (60s)', 'TikTok (3min)', 'Kwai (7min)'][1] if create_chapters else 'Todas as plataformas'}",
                    
                    "cenas_visuais": [
                        {{
                            "timing": "0-8s",
                            "descricao_cena": "Hook visual impactante",
                            "prompt_imagem": "Prompt DETALHADO para Leonardo AI: cenário, personagens, iluminação, mood, estilo fotográfico, composição",
                            "animacao_leonardo": "Movimento inicial dramático: zoom in rápido, movimento de câmera específico",
                            "mood_visual": "Atmosfera de abertura intrigante"
                        }},
                        {{
                            "timing": "15-25s", 
                            "descricao_cena": "Desenvolvimento da tensão",
                            "prompt_imagem": "Segundo ambiente visual com mudança de mood",
                            "animacao_leonardo": "Transição suave, pan horizontal, foco em detalhes",
                            "mood_visual": "Construção de suspense"
                        }},
                        {{
                            "timing": "35-45s",
                            "descricao_cena": "Primeiro ponto de virada", 
                            "prompt_imagem": "Momento de revelação ou conflito",
                            "animacao_leonardo": "Movimento dramático, zoom out, efeito de surprise",
                            "mood_visual": "Intensidade crescente"
                        }},
                        {{
                            "timing": "55-65s",
                            "descricao_cena": "Desenvolvimento do conflito",
                            "prompt_imagem": "Cena de ação ou emoção forte",
                            "animacao_leonardo": "Movimento dinâmico, câmera tremula, efeitos visuais",
                            "mood_visual": "Pico emocional"
                        }},
                        {{
                            "timing": "70-80s",
                            "descricao_cena": "Cliffhanger ou resolução",
                            "prompt_imagem": "Cena final impactante",
                            "animacao_leonardo": "Movimento de suspense ou alívio, fade específico",
                            "mood_visual": "Tensão máxima ou catarse"
                        }}
                    ]
                }}
            ],
            
            "elementos_narrativos": {{
                "personagens_principais": ["Personagem 1", "Personagem 2"],
                "cenario_principal": "Local onde se passa a história",
                "conflito_central": "Problema/desafio principal",
                "tema_emocional": "Emoção dominante da história",
                "mensagem_final": "Lição ou reflexão que fica",
                "arco_evolutivo": "Como a história/personagem evolui"
            }},
            
            "viral_elements": {{
                "emotional_triggers": ["gatilho1", "gatilho2", "gatilho3"],
                "curiosity_gaps": ["gap1", "gap2"],
                "pattern_interrupts": ["interrupt1", "interrupt2"],
                "story_hooks": ["hook narrativo 1", "hook narrativo 2"],
                "cliffhanger_strength": "forte/médio/leve"
            }},
            
            "continuidade_visual": {{
                "paleta_cores": "Cores dominantes da história",
                "estilo_visual": "Fotográfico/Artístico/Cinematográfico",
                "iluminacao_geral": "Mood de luz (dramática/suave/contrastada)",
                "transicoes_entre_cenas": "Como conectar visualmente as cenas",
                "elementos_visuais_recorrentes": "Objetos/símbolos que aparecem em vários capítulos"
            }},
            
            "otimizacao_plataformas": {{
                "youtube_shorts": "Adaptações específicas para 60s",
                "tiktok": "Aproveitamento dos 3 minutos disponíveis", 
                "kwai": "Uso inteligente dos 7 minutos permitidos",
                "formato_principal": "TikTok (melhor duração para storytelling)"
            }},
            
            "hashtags": ["#storytelling", "#historia", "#viral", "#emocional", "#fyp", "#serie"],
            "call_to_action": "CTA específico para histórias em série",
            "estimated_total_duration": {(85 * 3) if create_chapters else settings.get('duration', 90)},
            "engagement_prediction": {{
                "watch_time": 95,
                "replay_rate": 80,
                "share_likelihood": 90,
                "comment_trigger": "Elemento que gera identificação/debate/teoria sobre próximo capítulo"
            }}
        }}

        IMPORTANTE: Crie histórias AUTÊNTICAS que soem como experiências reais. Use linguagem brasileira natural, emoções genuínas e situações que as pessoas possam se identificar. Para capítulos, cada um deve ter força suficiente para viralizar sozinho.
        """
        return prompt


# --- NOVOS PATCHES PARA PROMPTS HÍBRIDOS ---

# Constantes compartilhadas para prompts históricos/científicos
HISTORY_VISUAL_PACK_EN = (
    "ultra realistic or painterly realistic, renaissance/early-modern vibes, "
    "cinematic lighting, moody shadows, volumetric light, rich textures, "
    "dark teal/orange palette, highly detailed, vertical 9:16, no text, 8K resolution"
)
HISTORY_IMAGE_SUFFIX_EN = "vertical 9:16, no text, highly detailed, 8K resolution"

MOTION_PRESET_HIGH_EN = "slow cinematic zoom in, subtle parallax, gentle camera drift, 9:16 vertical"
MOTION_PRESET_MED_EN  = "gentle pan left/right, slow zoom out, subtle parallax, 9:16 vertical"

HISTORY_VISUAL_PACK = (
    "ultra realistic or painterly realistic, renaissance/early-modern vibes, "
    "cinematic lighting, moody shadows, volumetric light, rich textures, "
    "dark teal/orange palette, highly detailed, vertical 9:16, no text, 8K resolution"
)

HISTORY_MOTION_PRESET_HIGH = "slow cinematic zoom in, subtle parallax, gentle camera drift, 9:16 vertical"
HISTORY_MOTION_PRESET_MED  = "gentle pan left/right, slow zoom out, subtle parallax, 9:16 vertical"

def build_storyboard_prompt_historia_gemini(theme: str, duration_target_sec: int = 60) -> str:
    """
    Prompt mestre p/ GEMINI gerar APENAS um JSON com storyboard histórico/científico (~duration_target_sec s).
    Narração pt-BR; prompts de imagem e movimento em inglês.
    """
    return f"""
Gere APENAS um ÚNICO objeto JSON VÁLIDO (sem markdown, sem texto fora do JSON).
Tema: "{theme}"
Formato: vertical short (~{duration_target_sec}s). Estilo: histórico/científico.

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
            "narration": "2–3 frases naturais em português do Brasil (sem SSML), TTS-friendly, ricas em detalhes concretos.",
      "on_screen_text": "Opcional, até 6 palavras.",
      "image_prompt": "Clear scene description in English. Include: {HISTORY_VISUAL_PACK_EN}. Ensure it ends with: {HISTORY_IMAGE_SUFFIX_EN}",
      "motion_prompt": "{MOTION_PRESET_HIGH_EN}",
      "intensity": "ALTA|MEDIA",
      "sfx": ["efeitos sutis"],
      "music_cue": "intro_suave|transicao|climax|final"
    }}
  ],
  "thumbnail": {{
    "text": "Frase curta de capa",
    "image_prompt": "English prompt coherent with theme. Include: {HISTORY_VISUAL_PACK_EN}"
  }},
  "hashtags": ["#historia","#shorts","#curiosidades"]
}}

REGRAS:
- Gere 8–10 cenas, 3–12s cada; total ~{duration_target_sec}s (preferencialmente 85–100s).
- Cada "narration" deve ter 2–3 frases com conteúdo específico (evite generalidades). Use linguagem natural brasileira.
- Toda 'image_prompt' deve terminar com: "{HISTORY_IMAGE_SUFFIX_EN}".
- 'motion_prompt' em inglês. Use "{MOTION_PRESET_HIGH_EN}" p/ intensidade ALTA e "{MOTION_PRESET_MED_EN}" p/ MÉDIA.
- Narração SEM SSML. Sem texto fora do JSON.
""".strip()

def build_storyboard_prompt_historia(theme: str, duration_target_sec: int = 60) -> str:
    """
    Prompt mestre para GEMINI gerar storyboard histórico/científico no formato JSON único.
    Saída: APENAS JSON válido (sem markdown), com cenas, prompts híbridos (Image3/DALL·E-3) e Leonardo Motion.
    """
    return f"""
Você é um roteirista/diretor para vídeos curtos (Shorts/TikTok/Kwai) de HISTÓRIA/CIÊNCIA (~{duration_target_sec}s).
Gere APENAS UM objeto JSON VÁLIDO (sem markdown, sem texto fora do JSON) seguindo o schema abaixo.
O tema é: "{theme}".

{{ 
  "title": "Título chamativo (<= 70 chars)",
  "audience": "history",
  "visual_pack": "HistoryDark",
  "duration_target_sec": {duration_target_sec},
  "voice_style": "documentary_grave",
  "music_style": "tensa_cinematica",
  "scenes": [
    {{
      "t_start": 0,
      "t_end": 6,
      "narration": "Frase curta e clara, pt-BR, TTS-friendly.",
      "on_screen_text": "Opcional, <= 6 palavras.",
      "image_prompt": "Descrição clara da cena + detalhes técnicos (híbrido DALL·E-3/Imagen 3). SEMPRE incluir: {HISTORY_VISUAL_PACK}",
      "motion_prompt": "{HISTORY_MOTION_PRESET_HIGH}",
      "intensity": "ALTA|MEDIA",
      "sfx": ["efeitos curtos e sutis"],
      "music_cue": "intro_suave|transicao|climax|final"
    }}
  ],
  "thumbnail": {{
    "text": "Frase curta de capa",
    "image_prompt": "Capa coerente com o tema. Incluir: {HISTORY_VISUAL_PACK}"
  }},
  "hashtags": ["#historia","#shorts","#curiosidades"]
}}

REGRAS:
- 6 a 8 cenas; cada cena 3–10s; total ~{duration_target_sec}s.
- "image_prompt": SEMPRE terminar com: "vertical 9:16, no text, highly detailed, 8K resolution" (se já estiver incluso, mantenha).
- Use {HISTORY_MOTION_PRESET_HIGH} para intensidade ALTA e {HISTORY_MOTION_PRESET_MED} para intensidade MÉDIA.
- Linguagem natural, pt-BR, sem SSML.
- Nada fora do JSON.
""".strip()
