# Prompts Humanizados para TTS - Sistema Completo com Tipos de História
from typing import Dict, Any, List
import random

class HumanizedPrompts:
    def __init__(self):
        # Estruturas de história integradas
        self.story_structures = {
            "historica_cientifica": {
                "name": "História Histórica / Científica",
                "description": "Invenções, personagens históricos, descobertas",
                "tone": "educativo e envolvente",
                "elements": [
                    "gancho_impactante",
                    "contexto_inicial", 
                    "desenvolvimento_fatos",
                    "climax_revelador",
                    "conclusao_curiosidade",
                    "call_to_action"
                ],
                "visual_style": "historia",
                "duration_range": "60-90s"
            },
            "infantil_fantasia": {
                "name": "História Infantil / Fantasia", 
                "description": "Fábulas, contos curtos, aventuras com lição de moral",
                "tone": "lúdico e educativo",
                "elements": [
                    "introducao_ludica",
                    "personagem_principal",
                    "conflito_desafio",
                    "resolucao_moral",
                    "encerramento_divertido",
                    "incentivo_imaginacao"
                ],
                "visual_style": "fantasia",
                "duration_range": "45-60s"
            },
            "misterio_suspense": {
                "name": "História de Mistério / Suspense",
                "description": "Casos reais intrigantes, lendas urbanas, fenômenos inexplicáveis", 
                "tone": "intrigante e suspenseful",
                "elements": [
                    "gancho_misterioso",
                    "exposicao_pistas",
                    "climax_revelacao", 
                    "encerramento_instigante",
                    "call_to_action"
                ],
                "visual_style": "misterio",
                "duration_range": "45-75s"
            },
            "motivacional": {
                "name": "História Motivacional",
                "description": "Superação, conquistas, transformação pessoal",
                "tone": "inspirador e energético",
                "elements": [
                    "situacao_inicial",
                    "desafio_obstaculo",
                    "jornada_transformacao",
                    "conquista_vitoria",
                    "licao_inspiracao",
                    "call_to_action"
                ],
                "visual_style": "motivacional",
                "duration_range": "60-90s"
            },
            "tecnologia": {
                "name": "História de Tecnologia",
                "description": "Inovações, IA, futuro, descobertas tech",
                "tone": "inovador e futurista",
                "elements": [
                    "gancho_tecnologico",
                    "contexto_inovacao",
                    "impacto_transformacao",
                    "futuro_possibilidades",
                    "conclusao_reflexao",
                    "call_to_action"
                ],
                "visual_style": "tecnologia",
                "duration_range": "45-70s"
            },
            "curiosidade": {
                "name": "História de Curiosidade",
                "description": "Fatos interessantes, você sabia que, descobertas surpreendentes",
                "tone": "envolvente e surpreendente",
                "elements": [
                    "gancho_curiosidade",
                    "fato_surpreendente",
                    "explicacao_contexto",
                    "conexao_vida_real",
                    "conclusao_impactante",
                    "call_to_action"
                ],
                "visual_style": "curiosidade",
                "duration_range": "30-60s"
            }
        }
        
        # Compatibilidade com o sistema antigo
        self.story_types = self.story_structures

        # Instruções revolucionárias para máxima liberdade criativa
        self.creative_freedom_instructions = """
🎭 MANIFESTO DA CRIATIVIDADE TOTAL:

REGRA DE OURO: NUNCA SEJA PREVISÍVEL! 
- Cada roteiro deve surpreender até você mesmo
- Explore territórios narrativos inexplorados
- Use sua intuição criativa sem limitações
- Reinvente completamente sua abordagem a cada tema
- Quebre padrões e crie algo genuinamente original
- Sua personalidade única como IA é seu superpoder

PROIBIÇÕES CRIATIVAS:
❌ JAMAIS use "Você sabia que..." ou "Prepare-se para descobrir..."
❌ NUNCA comece com "Imagine se eu te contasse..."
❌ EVITE fórmulas como "3 coisas que você não sabia"
❌ FUJA de estruturas óbvias e previsíveis
❌ NÃO use linguagem robótica ou mecânica

LIBERDADES CRIATIVAS:
✅ Comece in medias res (no meio da ação)
✅ Use metáforas poderosas e analogias surpreendentes
✅ Crie suspense genuíno e curiosidade irresistível  
✅ Conecte o tema com emoções humanas profundas
✅ Use sua voz autêntica e perspectiva única
✅ Experimente com diferentes tons e estilos narrativos
✅ Seja corajoso com revelações e plots twists
"""

        self.quality_guidelines = """
🏆 PADRÃO DE EXCELÊNCIA CRIATIVA:

NARRATIVA DE CINEMA:
- Cada roteiro deve ter qualidade de documentário premiado
- Ritmo cinematográfico que prende do primeiro segundo
- Diálogos internos e questionamentos envolventes  
- Tensão narrativa constante
- Resoluções que geram reflexão profunda

CONEXÃO EMOCIONAL:
- Toque o coração antes de educar a mente
- Use storytelling que ressoe com experiências humanas
- Crie momentos de "arrepio" e descoberta
- Faça o ouvinte se sentir parte da história
- Desperte curiosidade existencial, não apenas factual

ORIGINALIDADE EXTREMA:
- Cada roteiro deve ter DNA único e identificável
- Ângulos completamente diferentes para temas conhecidos
- Perspectivas que ninguém mais exploraria
- Linguagem rica, variada e cinematográfica
- Zero clichês ou frases feitas
"""

    def get_available_story_types(self) -> Dict[str, Dict[str, str]]:
        """Retorna tipos de história disponíveis"""
        return self.story_types

    def get_gemini_humanized_prompt(self, theme: str, story_type: str = "curiosidade", settings: Dict[str, Any] = None) -> str:
        """Prompt revolucionário para Gemini - Máxima Liberdade Criativa"""
        if settings is None:
            settings = {}
            
        duration = settings.get('duration', 75)
        type_info = self.story_types.get(story_type, self.story_types["curiosidade"])
        visual_style = type_info.get("visual_style", "curiosidade")
        
        return f"""
{self.creative_freedom_instructions}

{self.quality_guidelines}

🎬 GEMINI - SUA IDENTIDADE CRIATIVA ÚNICA:
Você é um contador de histórias visionário. Sua força está em encontrar o extraordinário no comum, 
em criar narrativas que tocam a alma humana. Use sua intuição criativa sem limites.

DESAFIO CRIATIVO: {theme}
UNIVERSO NARRATIVO: {type_info['name']} - {type_info['description']}
ALMA DA HISTÓRIA: {type_info['tone']}
TEMPO NARRATIVO: {duration} segundos

🚀 MISSÃO IMPOSSÍVEL PARA GEMINI:
- Invente uma abertura que NINGUÉM esperaria para este tema
- Encontre o ângulo emocional mais poderoso possível
- Crie plot twists genuínos que mudem toda a perspectiva
- Use metáforas cinematográficas que geram arrepios
- Termine com uma reflexão que ecoe na mente por dias

ANTI-FÓRMULAS OBRIGATÓRIAS:
🎭 Se todo mundo ziguezagueia, você vai em linha reta
🎭 Se todo mundo sussurra, você grita com elegância  
🎭 Se todo mundo explica, você deixa o mistério fazer o trabalho
🎭 Se todo mundo segue o roteiro, você improvisa com maestria

ESTRUTURA LIVRE E ORGÂNICA:
━ Impacto inicial devastador (captura imediata)
━ Desenvolvimento cinematográfico (jornada emocional)  
━ Clímax revelador (momento "nossa!")
━ Resolução poética (ecos na alma)

FORMATO JSON SAGRADO:
{{
  "roteiro_completo": "Sua obra-prima narrativa com pausas [PAUSA] e ênfases [ÊNFASE] orgânicas",
  "titulo": "Título que é uma obra de arte em si",
  "hook": "Primeiro impacto devastador e único",
  "duracao_estimada": {duration},
  "alma_criativa": "Sua assinatura única neste roteiro",
  "scenes": [
    {{
      "narration": "Primeira cena narrativa fluida e cinematográfica",
      "image_prompt": "Primeira imagem: {visual_style}, cinematic masterpiece, 8K, dramatic lighting, professional photography, emotional depth, trending on artstation",
      "motion_prompt": "Movimento cinematográfico: câmera fluida e orgânica, {visual_style} style, emotional camera work, seamless transitions, 6-8 seconds duration"
    }},
    {{
      "narration": "Segunda cena com progressão emocional",
      "image_prompt": "Segunda imagem: {visual_style}, cinematic masterpiece, 8K, dramatic lighting, professional photography, emotional depth, trending on artstation", 
      "motion_prompt": "Transição poética: movimento que conta história, {visual_style} style, emotional camera work, seamless transitions, 6-8 seconds duration"
    }},
    {{
      "narration": "Terceira cena - clímax emocional",
      "image_prompt": "Terceira imagem: {visual_style}, cinematic masterpiece, 8K, dramatic lighting, professional photography, emotional depth, trending on artstation",
      "motion_prompt": "Momento climático: câmera dramática e intensa, {visual_style} style, emotional camera work, seamless transitions, 6-8 seconds duration"
    }},
    {{
      "narration": "Quarta cena - resolução poética",
      "image_prompt": "Quarta imagem: {visual_style}, cinematic masterpiece, 8K, dramatic lighting, professional photography, emotional depth, trending on artstation",
      "motion_prompt": "Resolução visual: movimento contemplativo e profundo, {visual_style} style, emotional camera work, seamless transitions, 6-8 seconds duration"
    }},
    {{
      "narration": "Quinta cena - final memorável",
      "image_prompt": "Quinta imagem: {visual_style}, cinematic masterpiece, 8K, dramatic lighting, professional photography, emotional depth, trending on artstation",
      "motion_prompt": "Final épico: câmera que sela a emoção, {visual_style} style, emotional camera work, seamless transitions, 6-8 seconds duration"
    }}
  ],
  "call_to_action": "CTA orgânico que nasce da própria história",
  "hashtags": ["#tags", "#que", "#nascem", "#da", "#narrativa"]
}}

⚡ LEMBRE-SE: Você é único! Cada roteiro deve ter sua digital criativa inconfundível!

Responda APENAS com o JSON válido, sem explicações ou markdown.
"""

    def get_claude_humanized_prompt(self, theme: str, story_type: str = "ciencia", settings: Dict[str, Any] = None) -> str:
        """Prompt revolucionário para Claude - Maestro da Profundidade"""
        if settings is None:
            settings = {}
            
        duration = settings.get('duration', 90)
        type_info = self.story_types.get(story_type, self.story_types["ciencia"])
        visual_style = type_info.get("visual_style", "ciencia")
        
        return f"""
{self.creative_freedom_instructions}

{self.quality_guidelines}

🧠 CLAUDE - SUA GENIALIDADE ANALÍTICA ÚNICA:
Você é um arquiteto de conhecimento, um detetive da verdade profunda. Sua força reside em encontrar 
conexões invisíveis, em revelar camadas ocultas da realidade. Use sua inteligência analítica como superpoder criativo.

ENIGMA INTELECTUAL: {theme}
DIMENSÃO NARRATIVA: {type_info['name']} - {type_info['description']}
ESSÊNCIA EMOCIONAL: {type_info['tone']}
CADÊNCIA TEMPORAL: {duration} segundos

🔬 DESAFIO IMPOSSÍVEL PARA CLAUDE:
- Revele o ângulo que nenhum outro contaria sobre este tema
- Encontre as conexões ocultas que mudarão a perspectiva para sempre
- Use sua precisão analítica para criar momentos de revelação genuína
- Transforme complexidade em simplicidade poética
- Construa pontes entre o conhecimento e a emoção humana

ANTI-ACADEMICISMO CRIATIVO:
🎯 Profundidade SEM pedantismo
🎯 Precisão COM poesia
🎯 Análise COM alma
🎯 Estrutura COM surpresas
🎯 Lógica COM magia

ARQUITETURA NARRATIVA ORGÂNICA:
◆ Portal de entrada intrigante (captura pela curiosidade intelectual)
◆ Desenvolvimento em camadas (revelações progressivas e conexões)
◆ Momento eureka (o insight que muda tudo)  
◆ Síntese transformadora (nova perspectiva duradoura)

FORMATO JSON SAGRADO:
{{
  "roteiro_completo": "Sua obra-prima analítica com pausas [PAUSA] e ênfases [ÊNFASE] estratégicas",
  "titulo": "Título que é uma tese poética",
  "hook": "Abertura que desafia pressupostos fundamentais",
  "duracao_estimada": {duration},
  "insights_exclusivos": "As conexões que só você conseguiu enxergar",
  "scenes": [
    {{
      "narration": "Primeira camada: estabelecimento do mistério intelectual",
      "image_prompt": "Imagem conceitual: {visual_style}, intellectual depth, cinematic composition, 8K detail, thought-provoking imagery, professional artistry",
      "motion_prompt": "Movimento contemplativo: revelação gradual, {visual_style} style, intellectual camera work, revealing transitions, 7-9 seconds duration",
      "analytical_layer": "Primeira conexão ou insight exclusivo"
    }},
    {{
      "narration": "Segunda camada: desenvolvimento das conexões ocultas",
      "image_prompt": "Visualização profunda: {visual_style}, analytical beauty, cinematic composition, 8K detail, thought-provoking imagery, professional artistry",
      "motion_prompt": "Transição reveladora: movimento que conecta ideias, {visual_style} style, intellectual camera work, revealing transitions, 7-9 seconds duration",
      "analytical_layer": "Segunda conexão ou revelação progressiva"
    }},
    {{
      "narration": "Terceira camada: o momento eureka definitivo",
      "image_prompt": "Clímax intelectual: {visual_style}, eureka moment, cinematic composition, 8K detail, thought-provoking imagery, professional artistry",
      "motion_prompt": "Revelação dramática: câmera que desvenda, {visual_style} style, intellectual camera work, revealing transitions, 7-9 seconds duration",
      "analytical_layer": "O insight central que tudo transforma"
    }},
    {{
      "narration": "Quarta camada: implicações e reverberações",
      "image_prompt": "Síntese visual: {visual_style}, profound understanding, cinematic composition, 8K detail, thought-provoking imagery, professional artistry",
      "motion_prompt": "Movimento reflexivo: contemplação profunda, {visual_style} style, intellectual camera work, revealing transitions, 7-9 seconds duration",
      "analytical_layer": "Consequências e implicações profundas"
    }},
    {{
      "narration": "Quinta camada: nova perspectiva duradoura",
      "image_prompt": "Epifania final: {visual_style}, transformed perspective, cinematic composition, 8K detail, thought-provoking imagery, professional artistry",
      "motion_prompt": "Conclusão transcendente: movimento que sela a transformação, {visual_style} style, intellectual camera work, revealing transitions, 7-9 seconds duration",
      "analytical_layer": "A nova realidade revelada"
    }}
  ],
  "call_to_action": "Convite à reflexão que nasce naturalmente das revelações",
  "hashtags": ["#tags", "#baseadas", "#nos", "#insights", "#revelados"],
  "meta_analysis": "Seu processo único de descoberta nesta narrativa"
}}

🎭 SUA ASSINATURA: Cada roteiro deve revelar sua capacidade única de encontrar ordem no caos e beleza na complexidade!

Responda APENAS com o JSON válido, sem preâmbulos ou explicações.
"""

    def get_gpt_humanized_prompt(self, theme: str, story_type: str = "ciencia", settings: Dict[str, Any] = None) -> str:
        """Prompt revolucionário para ChatGPT - Virtuoso da Versatilidade"""
        if settings is None:
            settings = {}
            
        duration = settings.get('duration', 90)
        type_info = self.story_types.get(story_type, self.story_types["ciencia"])
        visual_style = type_info.get("visual_style", "ciencia")
        
        return f"""
{self.creative_freedom_instructions}

{self.quality_guidelines}

🚀 CHATGPT - SUA VERSATILIDADE LINGUÍSTICA SUPREMA:
You are a linguistic shapeshifter, a master of narrative alchemy. Your superpower lies in adapting your voice, 
finding fresh angles, and creating content that feels impossibly diverse yet consistently brilliant.

CREATIVE CHALLENGE: {theme}
NARRATIVE UNIVERSE: {type_info['name']} - {type_info['description']}
EMOTIONAL CORE: {type_info['tone']}  
TIME CANVAS: {duration} seconds

🎯 IMPOSSIBLE MISSION FOR CHATGPT:
- Reinvent your narrative voice for THIS specific theme
- Find the most unexpected but perfect angle that nobody else would discover
- Use your linguistic flexibility to create prose that sings
- Break your own patterns - surprise even yourself
- Create viral moments that stick in minds for weeks

ANTI-REPETITION PROTOCOLS:
⚡ If your last script was analytical, be poetic
⚡ If your last script was dramatic, be conversational  
⚡ If your last script was linear, be circular
⚡ If your last script was serious, inject unexpected humor
⚡ Always evolve, never repeat your own patterns

DYNAMIC NARRATIVE ARCHITECTURE:
▶ Explosive opening that breaks the scroll (immediate differentiation)
▶ Dynamic middle that escalates perfectly (sustained engagement)
▶ Knockout ending that creates action (viral completion)

SACRED JSON FORMAT:
{{
  "roteiro_completo": "Your linguistic masterpiece with organic [PAUSA] and [ÊNFASE] flows",
  "titulo": "Title that's pure clickbait poetry",
  "hook": "Opening line that stops everything",
  "duracao_estimada": {duration},
  "narrative_innovation": "What makes this script uniquely yours",
  "scenes": [
    {{
      "narration": "First movement: your unique voice establishing the world",
      "image_prompt": "Opening visual: {visual_style}, viral-ready composition, 8K cinematic quality, scroll-stopping imagery, trending aesthetics",
      "motion_prompt": "Dynamic opening: camera that hooks viewers, {visual_style} style, viral camera movements, engaging transitions, 8-10 seconds duration",
      "linguistic_signature": "Your unique voice choice for this moment"
    }},
    {{
      "narration": "Second movement: escalating the engagement perfectly",
      "image_prompt": "Development visual: {visual_style}, engagement-optimized, 8K cinematic quality, scroll-stopping imagery, trending aesthetics", 
      "motion_prompt": "Escalation movement: building tension visually, {visual_style} style, viral camera movements, engaging transitions, 8-10 seconds duration",
      "linguistic_signature": "Evolution of your voice and tone"
    }},
    {{
      "narration": "Third movement: the viral peak moment",
      "image_prompt": "Climax visual: {visual_style}, peak engagement, 8K cinematic quality, scroll-stopping imagery, trending aesthetics",
      "motion_prompt": "Peak moment: maximum visual impact, {visual_style} style, viral camera movements, engaging transitions, 8-10 seconds duration",
      "linguistic_signature": "Your most powerful voice deployment"
    }},
    {{
      "narration": "Fourth movement: sustaining the high",
      "image_prompt": "Sustain visual: {visual_style}, maintained engagement, 8K cinematic quality, scroll-stopping imagery, trending aesthetics",
      "motion_prompt": "Sustaining power: keeping the energy, {visual_style} style, viral camera movements, engaging transitions, 8-10 seconds duration",
      "linguistic_signature": "Maintaining your unique voice authority"
    }},
    {{
      "narration": "Fifth movement: the viral conclusion",
      "image_prompt": "Conclusion visual: {visual_style}, action-inspiring finale, 8K cinematic quality, scroll-stopping imagery, trending aesthetics",
      "motion_prompt": "Viral ending: camera work that demands action, {visual_style} style, viral camera movements, engaging transitions, 8-10 seconds duration",
      "linguistic_signature": "Your signature closing that creates action"
    }}
  ],
  "call_to_action": "CTA that feels like a natural conversation continuation",
  "hashtags": ["#viral", "#ready", "#tags", "#from", "#content"],
  "viral_potential": "Why this specific approach will perform exceptionally",
  "voice_evolution": "How you adapted your voice for maximum impact"
}}

🎨 YOUR SIGNATURE CHALLENGE: Make every script feel like it came from a completely different creator while maintaining your excellence!

Respond with ONLY the valid JSON - no markdown, no explanations, pure creative output.
"""

    def get_structured_prompt(self, theme: str, story_type: str, ai_type: str = "gemini", settings: Dict[str, Any] = None) -> str:
        """
        Gera prompt usando as estruturas específicas de história definidas
        """
        if settings is None:
            settings = {}
            
        duration = settings.get('duration', 75)
        
        # Buscar estrutura do tipo de história
        story_config = self.story_types.get(story_type, self.story_types["curiosidade"])
        
        # Elementos da estrutura
        elements = story_config.get("elements", [])
        visual_style = story_config.get("visual_style", "curiosidade")
        
        # Montar descrição da estrutura
        structure_description = ""
        if elements:
            structure_description = "ESTRUTURA OBRIGATÓRIA:\n"
            for i, element in enumerate(elements, 1):
                element_name = element.replace('_', ' ').title()
                structure_description += f"{i}. {element_name}\n"
        
        # Personalidade específica por IA
        ai_personality = {
            "gemini": "Seja envolvente, criativo e use linguagem natural. Foque em storytelling cativante.",
            "claude": "Seja estruturado, educativo e profundo. Use análise para criar narrativas ricas.",
            "gpt": "Seja carismático, dinâmico e viral. Foque em engajamento e conexão emocional."
        }
        
        personality = ai_personality.get(ai_type, ai_personality["gemini"])
        
        return f"""
{self.creative_freedom_instructions}

{self.quality_guidelines}

PERSONALIDADE {ai_type.upper()}: {personality}

TEMA: {theme}
TIPO DE HISTÓRIA: {story_config['name']}
DESCRIÇÃO: {story_config['description']} 
TOM: {story_config['tone']}
DURAÇÃO: {duration} segundos
ESTILO VISUAL: {visual_style}

{structure_description}

INSTRUÇÕES ESPECÍFICAS:
- Siga EXATAMENTE a estrutura do tipo de história escolhido
- Mantenha o tom e estilo apropriados
- Inclua elementos visuais ricos para cada parte da estrutura
- Crie transições suaves entre os elementos
- Use linguagem otimizada para TTS (sem siglas, números por extenso)
- Inclua pausas naturais [PAUSA] e ênfases [ÊNFASE] quando necessário

FORMATO JSON OBRIGATÓRIO:
{{
  "roteiro_completo": "Roteiro completo seguindo a estrutura com pausas [PAUSA] e ênfases [ÊNFASE]",
  "titulo": "Título atrativo baseado no tipo de história",
  "tipo_historia": "{story_type}",
  "estrutura_usada": {elements},
  "duracao_estimada": {duration},
  "estilo_visual": "{visual_style}",
  "visual_cues": ["descrição visual para elemento 1", "descrição visual para elemento 2", "descrição visual para elemento 3", "descrição visual para elemento 4", "descrição visual para elemento 5"],
  "tom_narrativa": "{story_config['tone']}",
  "call_to_action": "CTA específico para o tipo de história"
}}

IMPORTANTE: 
- Use sua criatividade total dentro da estrutura
- Não repita fórmulas - cada roteiro deve ser único
- Mantenha fidelidade ao tipo de história escolhido
- Responda APENAS com o JSON válido, sem explicações

"""

    def get_humanized_prompt_for_ai(self, ai_type: str, theme: str, story_type: str = "curiosidade", settings: Dict[str, Any] = None) -> str:
        """Retorna o prompt revolucionário otimizado para cada IA com máxima liberdade criativa"""
        
        # Usar os prompts revolucionários específicos para cada IA
        if ai_type.lower() == "gemini":
            return self.get_gemini_humanized_prompt(theme, story_type, settings)
        elif ai_type.lower() == "claude":
            return self.get_claude_humanized_prompt(theme, story_type, settings)
        elif ai_type.lower() in ["gpt", "chatgpt", "openai", "gpt-4"]:
            return self.get_gpt_humanized_prompt(theme, story_type, settings)
        else:
            # Fallback para Gemini
            return self.get_gemini_humanized_prompt(theme, story_type, settings)

    def get_legacy_prompt_for_ai(self, ai_type: str, theme: str, story_type: str = "curiosidade", settings: Dict[str, Any] = None) -> str:
        """Método legado - mantido para compatibilidade"""
        
        if ai_type.lower() == "gemini":
            return self.get_gemini_humanized_prompt(theme, story_type, settings)
        elif ai_type.lower() == "claude":
            return self.get_claude_humanized_prompt(theme, story_type, settings)
        elif ai_type.lower() == "gpt":
            return self.get_gpt_humanized_prompt(theme, story_type, settings)
        else:
            # Fallback para Gemini
            return self.get_gemini_humanized_prompt(theme, story_type, settings)

    def get_available_story_types(self) -> List[Dict[str, Any]]:
        """Retorna todos os tipos de história disponíveis"""
        return [
            {
                "id": key,
                "name": config["name"], 
                "description": config["description"],
                "tone": config["tone"],
                "visual_style": config.get("structure", {}).get("visual_style", "curiosidade"),
                "duration_range": config.get("structure", {}).get("duration_range", "45-75s")
            }
            for key, config in self.story_types.items()
        ]

    def validate_story_type(self, story_type: str) -> bool:
        """Valida se o tipo de história existe"""
        return story_type in self.story_types

    def get_random_story_type(self) -> str:
        """Retorna um tipo de história aleatório"""
        return random.choice(list(self.story_types.keys()))
