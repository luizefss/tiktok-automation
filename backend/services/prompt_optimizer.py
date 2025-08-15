# /var/www/tiktok-automation/backend/services/prompt_optimizer.py

import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class VisualStyle:
    """Estilo visual com assinatura consistente"""
    name: str
    image_base: str
    motion_base: str
    description: str


@dataclass
class SceneConfig:
    """Configuração de cena otimizada"""
    start_time: float
    end_time: float
    text: str
    intensity: str  # ALTA, MÉDIA, BAIXA
    image_prompt: str
    motion_prompt: str
    sfx_cue: str


class PromptOptimizer:
    def __init__(self):
        logger.info("🎯 Inicializando Prompt Optimizer...")

        # Estilos visuais híbridos (DALL-E 3 + Imagen 3 compatível)
        self.visual_styles = {
            "historia_documentario": VisualStyle(
                name="História/Documentário",
                image_base="interior de oficina renascentista vibrante, bancada de madeira com engrenagens douradas e molas brilhantes, luz dourada quente criando atmosfera acolhedora, iluminação cinematográfica radiante, realismo pictórico colorido, texturas ricas e vibrantes, paleta dourado/âmbar/laranja vivo, cores vivas e saturadas, formato vertical 9:16, sem texto, altamente detalhado, resolução 8K",
                motion_base="zoom cinematográfico lento para dentro, zoom lento para fora, panorâmica suave esquerda/direita, inclinação suave para cima/baixo, paralaxe sutil, transições luminosas",
                description="Estilo histórico vibrante com cores quentes e vivas"
            ),
            "tecnologia_moderna": VisualStyle(
                name="Tecnologia Moderna", 
                image_base="ambiente de laboratório futurista brilhante, displays holográficos coloridos e painéis LED vibrantes, superfícies metálicas com reflexos cromáticos, iluminação LED multicolorida, acentos neon vívidos, design moderno fotorrealista cheio de vida, paleta azul elétrico/ciano/magenta, cores tecnológicas vibrantes, formato vertical 9:16, sem texto, altamente detalhado, resolução 8K",
                motion_base="transições de zoom suaves, efeitos de paralaxe digital coloridos, movimentos de câmera eletrônicos luminosos, transições tech vibrantes",
                description="Estilo tecnológico futurista com cores vivas e energia"
            ),
            "misterio_suspense": VisualStyle(
                name="Mistério/Suspense",
                image_base="cena atmosférica intrigante, ambiente misterioso com iluminação dramática colorida, efeitos de neblina dourada e silhuetas interessantes, iluminação cinematográfica vibrante, fonte de luz colorida, estilo cinematográfico moderno, paleta roxo profundo/azul royal/vermelho rico, cores intensas e envolventes, formato vertical 9:16, sem texto, altamente detalhado, resolução 8K",
                motion_base="movimentos de revelação dramática, transições coloridas suaves, ritmo de câmera envolvente, efeitos de zoom cinematográficos",
                description="Estilo misterioso com atmosfera colorida e vibrante"
            )
        }

        # Movimentos por intensidade
        self.motion_by_intensity = {
            "ALTA": [
                "zoom cinematográfico lento para dentro, paralaxe sutil, ênfase dramática",
                "revelação dinâmica inclinando para cima, movimento poderoso", 
                "aproximação em close-up, foco intenso"
            ],
            "MÉDIA": [
                "panorâmica suave da esquerda para direita, transição fluida",
                "revelação com zoom lento para fora, movimento contextual",
                "mudança de paralaxe sutil, movimento equilibrado"
            ],
            "BAIXA": [
                "transição fade, efeito atmosférico",
                "deriva suave, movimento mínimo",
                "mudança de foco suave, movimento calmo"
            ]
        }

        # Palavras e tags negativas para todos os provedores  
        self.negative_common = (
            "sem texto, sem legendas, sem marcas d'água, sem logos, sem marcas, "
            "sem interface, sem diagramas, sem gráficos, sem bordas, sem molduras, sem adesivos"
        )

        # Qualidade negativa adicional (evitar problemas comuns) + EVITAR CORES ESCURAS
        self.negative_quality = (
            "borrado, baixa resolução, pixelizado, artefatos jpeg, granulado, fora do quadro, cortado, "
            "desfigurado, deformado, dedos extras, membros extras, assunto duplicado, anatomia ruim, "
            "preto, escuro, sombrio, gótico, tenebroso, tons escuros, muito escuro, predominantemente preto"
        )

        # Diretrizes de composição e qualidade (em português, foco em cores vivas)
        self.composition_common = (
            "regra dos terços, composição cinematográfica, profundidade de campo rasa, bokeh natural, "
            "foco nítido no assunto, materiais realistas, iluminação coerente, cores vibrantes e saturadas, "
            "paleta de cores rica, tonalidade viva, contraste colorido, brilho natural"
        )

        # Configurações específicas ultra-avançadas por plataforma de IA
        self.ai_platform_configs = {
            "dalle": {
                "name": "DALL-E 3",
                "quality_tags": ["alto detalhamento", "fotorrealista", "grading cinematográfico", "obra-prima da arte digital", "qualidade de arte conceitual"],
                "technical_specs": "1024x1792, vertical 9:16, ultra-detalhado, arte digital profissional",
                "style_modifiers": ["trending no ArtStation", "arte digital premiada", "ilustração profissional"],
                "limit": 1000,  # DALL-E tem limite menor
                "strengths": ["interpretação criativa", "estilo artístico", "imagens conceituais"],
                "optimal_structure": "[assunto principal] + [estilo artístico] + [humor/iluminação] + [especificações técnicas]"
            },
            "imagen3": {
                "name": "Google Imagen 3",
                "quality_tags": ["fotorrealista", "resolução 8K", "fotografia profissional", "ultra-detalhado", "iluminação cinematográfica"],
                "technical_specs": "1280x2048, proporção vertical, qualidade fotográfica, texturas realistas",
                "style_modifiers": ["fotografado com câmera profissional", "fotografia premiada", "qualidade National Geographic"],
                "limit": 1600,
                "strengths": ["fotorrealismo", "iluminação natural", "detalhe arquitetônico"],
                "optimal_structure": "[descrição fotográfica] + [detalhes câmera/lente] + [iluminação] + [composição]"
            },
            "imagen4": {
                "name": "Google Imagen 4",
                "quality_tags": ["hiper-realista", "resolução 16K", "qualidade de museu", "perfeição fotográfica", "composição obra-prima"],
                "technical_specs": "1536x2048, resolução ultra-alta, detalhe máximo, nível profissional",
                "style_modifiers": ["digno de galeria", "qualidade de exposição", "perfeição técnica", "maestria artística"],
                "limit": 1800,
                "strengths": ["realismo extremo", "detalhe perfeito", "composição artística"],
                "optimal_structure": "[cena detalhada] + [maestria artística] + [perfeição técnica] + [impacto emocional]"
            }
        }
        
        # Configurações para animação de vídeo (3 segundos por imagem)
        self.video_animation_configs = {
            "leonardo": {
                "name": "Leonardo AI",
                "animation_styles": [
                    "panorâmica cinematográfica lenta", "zoom dramático", "rotação suave",
                    "flutuação suave", "revelação épica", "movimento atmosférico",
                    "efeito paralaxe", "dolly de câmera", "movimento orbital"
                ],
                "duration_per_image": 3,  # 3 segundos fixos por imagem
                "duration_range": "3 segundos por cena, timing cinematográfico",
                "technical_specs": "movimento suave, loop contínuo, renderização alta qualidade, timing cinematográfico",
                "movement_qualities": ["orgânico", "natural", "cinematográfico", "profissional"],
                "strengths": ["transições suaves", "movimento artístico", "qualidade cinematográfica"],
                "optimal_structure": "[tipo movimento] + [comportamento câmera] + [duração 3 segundos] + [especificações qualidade]"
            },
            "veo2": {
                "name": "Google Veo 2",
                "animation_styles": [
                    "movimentos complexos de câmera", "transições dinâmicas de cena", "física realista",
                    "movimento natural", "narrativa cinematográfica", "perspectiva imersiva",
                    "animação multicamadas", "dinâmica ambiental", "interação de personagens"
                ],
                "duration_per_image": 3,  # 3 segundos fixos por imagem
                "duration_range": "3 segundos por cena, timing narrativo estendido",
                "technical_specs": "qualidade 4K, desfoque de movimento natural, mudanças realistas de iluminação, qualidade broadcast",
                "movement_qualities": ["realista", "complexo", "natural", "imersivo"],
                "strengths": ["física realista", "cenas complexas", "timing otimizado"],
                "optimal_structure": "[dinâmica da cena] + [movimento realista] + [detalhes ambientais] + [duração 3 segundos]"
            }
        }
        
        # Configuração padrão do sistema: 3 segundos por imagem
        self.SECONDS_PER_IMAGE = 3

        # Ajustes por provedor (mantido para compatibilidade)
        self.provider_tweaks = {
            "openai": self.ai_platform_configs["dalle"],
            "dalle": self.ai_platform_configs["dalle"],
            "imagen": self.ai_platform_configs["imagen3"],
            "imagen3": self.ai_platform_configs["imagen3"],
            "imagen4": self.ai_platform_configs["imagen4"],
            "leonardo": {
                "quality": "highly detailed, sharp focus, intricate textures, cinematic grade",
                "limit": 1600
            },
            "hybrid": {
                "quality": "ultra detailed, photorealistic, cinematic lighting",
                "limit": 1500
            }
        }

        logger.info("✅ Prompt Optimizer inicializado - 3 segundos por imagem configurado")

    def calculate_number_of_prompts(self, target_duration_seconds: int) -> int:
        """Calcula automaticamente quantos prompts são necessários baseado na duração desejada"""
        # Para vídeos de 1 minuto (60s), sempre gerar 20 prompts
        if target_duration_seconds >= 60:
            num_prompts = 20
        else:
            num_prompts = max(1, target_duration_seconds // self.SECONDS_PER_IMAGE)
        
        logger.info(f"📊 Para {target_duration_seconds}s de vídeo: {num_prompts} prompts (3s cada)")
        return num_prompts

    def calculate_video_duration(self, number_of_prompts: int) -> int:
        """Calcula a duração total do vídeo baseado no número de prompts"""
        total_duration = number_of_prompts * self.SECONDS_PER_IMAGE
        logger.info(f"📊 Com {number_of_prompts} prompts: {total_duration}s de vídeo total")
        return total_duration

    def generate_20_prompts_for_60s_video(self, theme: str, style: str = "historia_documentario") -> List[str]:
        """Gera exatamente 20 prompts otimizados para vídeo de 60 segundos (3s cada)"""
        logger.info(f"🎯 Gerando 20 prompts para vídeo de 60s sobre: {theme}")
        
        style_config = self.visual_styles.get(style, self.visual_styles["historia_documentario"])
        prompts = []
        
        # Prompts base variados para criar diversidade visual
        base_variations = [
            "cena de abertura cinematográfica",
            "foco em detalhes importantes", 
            "panorâmica do ambiente",
            "close-up dramático",
            "perspectiva ampla",
            "momento de tensão",
            "revelação visual",
            "transição suave",
            "ângulo único",
            "destaque principal",
            "atmosfera envolvente",
            "movimento dinâmico",
            "foco narrativo",
            "elemento surpresa",
            "culminação visual",
            "contraste dramático",
            "profundidade de campo",
            "iluminação especial",
            "momento climático",
            "finalização épica"
        ]
        
        for i in range(20):
            # Usar variação base ciclicamente
            variation = base_variations[i % len(base_variations)]
            
            # Criar prompt específico combinando tema, variação e estilo
            prompt_description = f"{theme}, {variation}, {style_config.image_base}"
            
            # Otimizar o prompt
            optimized_prompt = self.optimize_image_prompt(
                prompt_description, 
                style=style, 
                provider="hybrid",
                context={"sequence": i+1, "total": 20}
            )
            
            prompts.append(optimized_prompt)
            logger.debug(f"📝 Prompt {i+1}/20: {optimized_prompt[:100]}...")
        
        logger.info(f"✅ Gerados 20 prompts para vídeo de 60s - Total: {len(prompts)} prompts")
        return prompts

    def create_hybrid_prompt(self, description: str, visual_details: str = "", lighting: str = "", style: str = "historia_documentario") -> str:
        """Cria prompt híbrido seguindo estrutura: [descrição] + [detalhes] + [iluminação] + [tags técnicas]"""
        try:
            style_config = self.visual_styles.get(
                style, self.visual_styles["historia_documentario"])

            # Componentes do prompt híbrido
            components = []

            # 1. Descrição principal (limpa)
            if description.strip():
                cleaned_desc = self.clean_prompt_noise(description)
                components.append(cleaned_desc)

            # 2. Detalhes visuais específicos
            if visual_details.strip():
                components.append(visual_details)

            # 3. Condições de iluminação
            if lighting.strip():
                components.append(lighting)
            else:
                # Usar iluminação padrão do estilo
                if style == "historia_documentario":
                    components.append(
                        "warm candlelight casting dramatic shadows, cinematic lighting")
                elif style == "tecnologia_moderna":
                    components.append(
                        "cool blue LED lighting, neon accents, digital glow effects")
                elif style == "misterio_suspense":
                    components.append(
                        "dim moody lighting, single light source, dramatic contrasts")

            # 4. Estilo artístico e tags técnicas (sempre incluir)
            artistic_style = ""
            if style == "historia_documentario":
                artistic_style = "painterly realistic, ultra realistic, rich textures, dark teal/orange palette"
            elif style == "tecnologia_moderna":
                artistic_style = "photorealistic, ultra modern, sleek design, blue/cyan palette"
            elif style == "misterio_suspense":
                artistic_style = "cinematic noir, atmospheric realism, high contrast, monochromatic with red accents"

            components.append(artistic_style)
            components.append(
                "vertical 9:16, no text, highly detailed, 8K resolution")

            # Unir componentes
            hybrid_prompt = ", ".join(filter(None, components))

            logger.info(f"🎯 Prompt híbrido criado: {hybrid_prompt[:100]}...")
            return hybrid_prompt

        except Exception as e:
            logger.error(f"❌ Erro ao criar prompt híbrido: {e}")
            return description

    def optimize_image_prompt(self, raw_prompt: str, style: str = "historia_documentario", provider: str = "hybrid", context: Optional[Dict[str, Any]] = None) -> str:
        """Otimiza prompt de imagem para compatibilidade DALL-E 3 + Imagen 3 + Leonardo.
        Mantém compatibilidade com a assinatura antiga. Usa provider para pequenos ajustes.
        """
        try:
            # Limpar ruído do prompt
            cleaned = self.clean_prompt_noise(raw_prompt)

            # Aplicar estilo visual híbrido
            style_config = self.visual_styles.get(
                style, self.visual_styles["historia_documentario"])

            # Estrutura híbrida: [descrição principal] + [base style completa]
            if cleaned.strip():
                # Se há conteúdo específico, combinar com estilo
                optimized = f"{cleaned}, {style_config.image_base}"
            else:
                # Se não há conteúdo específico, usar apenas o estilo base
                optimized = style_config.image_base

            # Composição e negativos
            if self.negative_common not in optimized:
                optimized += f", {self.negative_common}"
            if self.negative_quality not in optimized:
                optimized += f", {self.negative_quality}"
            if self.composition_common not in optimized:
                optimized += f", {self.composition_common}"

            # Assegurar 9:16
            if "9:16" not in optimized:
                optimized += ", vertical 9:16"

            # Ajustes por provedor
            prov = (provider or "hybrid").lower()
            if prov == 'dalle':
                prov = 'openai'
            tweaks = self.provider_tweaks.get(
                prov, self.provider_tweaks["hybrid"])
            if tweaks["quality"] not in optimized:
                optimized += f", {tweaks['quality']}"

            # Consistência opcional por contexto (personagens/objetos)
            if context and isinstance(context, dict):
                entity = context.get("entity") or context.get("character")
                if entity:
                    optimized += f", consistent depiction of {entity} across scenes"
                era = context.get("era") or context.get("period")
                if era:
                    optimized += f", set in {era}"
                framing = context.get("framing")
                if framing and framing not in optimized:
                    optimized += f", {framing}"
                lens = context.get("lens")
                if lens and lens not in optimized:
                    optimized += f", shot on {lens} lens"

            # Limitar comprimento se necessário (DALL·E tende a aceitar prompts menores)
            max_len = int(tweaks.get("limit", 1500))
            if len(optimized) > max_len:
                optimized = optimized[:max_len]

            logger.info(f"🎨 Prompt híbrido gerado: {optimized[:100]}...")
            return optimized

        except Exception as e:
            logger.error(f"❌ Erro ao otimizar prompt de imagem: {e}")
            return raw_prompt

    def optimize_motion_prompt(self, scene_content: str, intensity: str = "MÉDIA", style: str = "historia_documentario", duration_seconds: Optional[float] = None) -> str:
        """Otimiza prompt de movimento baseado na intensidade e contexto"""
        try:
            # Selecionar movimento apropriado
            motion_options = self.motion_by_intensity.get(
                intensity, self.motion_by_intensity["MÉDIA"])

            # Para simplicidade, usa o primeiro movimento da intensidade
            # Em uma versão mais avançada, poderia analisar o contexto da cena
            base_motion = motion_options[0]

            # Aplicar estilo de movimento
            style_config = self.visual_styles.get(
                style, self.visual_styles["historia_documentario"])

            # Incluir movimento de câmera e duração típica do clipe animado
            dur_txt = f"{int(duration_seconds)} seconds" if duration_seconds and duration_seconds > 0 else "4-8 seconds"
            camera = "cinematic camera move, parallax layers"
            optimized = f"{base_motion}, {style_config.motion_base}, {camera}, {dur_txt}, 9:16 vertical"

            logger.info(f"🎬 Movimento otimizado: {optimized}")
            return optimized

        except Exception as e:
            logger.error(f"❌ Erro ao otimizar prompt de movimento: {e}")
            return "slow cinematic movement, 6 seconds, 9:16 vertical"

    def clean_prompt_noise(self, prompt: str) -> str:
        """Remove ruído e fragmentos desnecessários do prompt"""
        try:
            # Remover pontuação problemática
            cleaned = re.sub(r'[?!,]{2,}', '', prompt)

            # Remover palavras fragmentadas (muito curtas isoladas)
            words = prompt.split()
            filtered_words = []

            for i, word in enumerate(words):
                # Manter palavra se:
                # - Tem mais de 2 caracteres OU
                # - É uma preposição comum OU
                # - Está no contexto correto
                word_clean = re.sub(r'[^\w]', '', word)

                if (len(word_clean) > 2 or
                    word_clean.lower() in ['da', 'de', 'do', 'na', 'no', 'em', 'um', 'uma'] or
                        (i > 0 and i < len(words)-1)):  # palavra no meio da frase
                    filtered_words.append(word)

            cleaned = ' '.join(filtered_words)

            # Limpar espaços múltiplos
            cleaned = re.sub(r'\s+', ' ', cleaned).strip()

            logger.debug(f"🧹 Prompt limpo: '{prompt}' → '{cleaned}'")
            return cleaned

        except Exception as e:
            logger.error(f"❌ Erro ao limpar prompt: {e}")
            return prompt

    def analyze_script_intensity(self, text: str) -> str:
        """Analisa o texto para determinar intensidade dramática"""
        try:
            # Palavras que indicam alta intensidade
            high_intensity_words = [
                'imagine', 'incrível', 'surpreendente', 'impacto', 'revolução',
                'dramático', 'impressionante', 'extraordinário', 'fascinante'
            ]

            # Palavras que indicam média intensidade
            medium_intensity_words = [
                'durante', 'contexto', 'história', 'desenvolvimento', 'evolução',
                'processo', 'método', 'técnica', 'sistema'
            ]

            text_lower = text.lower()

            high_count = sum(
                1 for word in high_intensity_words if word in text_lower)
            medium_count = sum(
                1 for word in medium_intensity_words if word in text_lower)

            if high_count >= 2:
                return "ALTA"
            elif medium_count >= 2:
                return "MÉDIA"
            else:
                return "BAIXA"

        except Exception as e:
            logger.error(f"❌ Erro ao analisar intensidade: {e}")
            return "MÉDIA"

    def create_optimized_scenes(self, script: str, image_prompts: List[str],
                                duration: float = 60.0, style: str = "historia_documentario", provider: str = "hybrid") -> List[SceneConfig]:
        """Cria cenas otimizadas com base no script e prompts"""
        try:
            # Dividir script em frases
            sentences = [s.strip() for s in script.split('.') if s.strip()]

            # Calcular duração por cena
            num_scenes = min(len(sentences), len(image_prompts))
            if num_scenes == 0:
                logger.warning(
                    "⚠️ Nenhuma cena para otimizar: script ou prompts vazios")
                return []
            duration_per_scene = duration / num_scenes

            scenes = []

            # Variações determinísticas por cena para evitar prompts idênticos
            angle_variants = [
                "low-angle shot",
                "high-angle shot",
                "over-the-shoulder",
                "top-down view",
                "dutch angle",
                "wide establishing shot",
                "medium shot",
                "close-up shot"
            ]
            time_of_day_variants = [
                "golden hour",
                "blue hour",
                "night scene with practical lights",
                "midday sunlight",
                "overcast soft light"
            ]
            lens_variants = [
                "24mm wide lens",
                "35mm lens",
                "50mm lens",
                "85mm portrait lens"
            ]

            for i in range(num_scenes):
                # Calcular timing
                start_time = i * duration_per_scene
                end_time = (i + 1) * duration_per_scene

                # Analisar intensidade da frase
                sentence = sentences[i] if i < len(sentences) else ""
                intensity = self.analyze_script_intensity(sentence)

                # Otimizar prompts usando estrutura híbrida
                raw_image_prompt = image_prompts[i] if i < len(image_prompts) else "historical scene"

                # Se o prompt for muito genérico (ex.: "scene", "scene 1"), use trecho da frase para diversificar
                generic_pattern = re.compile(r"^\s*scene(\s+\d+)?\s*$", re.IGNORECASE)
                if (not raw_image_prompt) or len(raw_image_prompt.strip()) < 6 or generic_pattern.match(raw_image_prompt.strip()):
                    # usar até 12 palavras significativas da sentença como base
                    words = [w for w in re.split(r"\s+", sentence) if w]
                    base_desc = " ".join(words[:12]) if words else "cinematic historical scene"
                    raw_image_prompt = base_desc

                # Contexto simples para consistência entre cenas (entidade principal)
                context = {"entity": None}
                words = [w.strip(',;:') for w in sentence.split()]
                for w in words:
                    if len(w) > 3:
                        context["entity"] = w
                        break

                # Framing por intensidade
                framing_map = {
                    "ALTA": "dramatic close-up, subject fills the frame",
                    "MÉDIA": "medium shot, subject waist-up",
                    "BAIXA": "wide shot, establishing view"
                }
                framing = framing_map.get(intensity, "medium shot")
                context["framing"] = framing

                # Usar otimizador ciente de provedor
                optimized_image = self.optimize_image_prompt(
                    raw_prompt=raw_image_prompt,
                    style=style,
                    provider=provider,
                    context=context
                )

                # Injetar variações determinísticas por cena para evitar repetição
                angle = angle_variants[i % len(angle_variants)]
                tod = time_of_day_variants[i % len(time_of_day_variants)]
                lens = lens_variants[i % len(lens_variants)]

                for variant in (angle, tod, lens):
                    if variant not in optimized_image:
                        optimized_image += f", {variant}"

                optimized_motion = self.optimize_motion_prompt(
                    sentence, intensity, style)

                # Criar configuração da cena
                scene = SceneConfig(
                    start_time=start_time,
                    end_time=end_time,
                    text=sentence,
                    intensity=intensity,
                    image_prompt=optimized_image,
                    motion_prompt=optimized_motion,
                    sfx_cue=self.suggest_sfx(sentence, intensity)
                )

                scenes.append(scene)

            logger.info(f"✅ {len(scenes)} cenas otimizadas criadas")
            return scenes

        except Exception as e:
            logger.error(f"❌ Erro ao criar cenas otimizadas: {e}")
            return []

    def suggest_sfx(self, text: str, intensity: str) -> str:
        """Sugere efeitos sonoros baseados no texto e intensidade"""
        text_lower = text.lower()

        if any(word in text_lower for word in ['papel', 'esboço', 'desenho']):
            return "paper rustling, quill writing"
        elif any(word in text_lower for word in ['máquina', 'engrenagem', 'mecânico']):
            return "mechanical clicks, gear sounds"
        elif any(word in text_lower for word in ['batalha', 'guerra', 'lançar']):
            return "tension sounds, wood creaking"
        elif intensity == "ALTA":
            return "dramatic crescendo, emphasis sound"
        else:
            return "ambient atmosphere, subtle background"

    def create_leonardo_style_prompt(self, scene_description: str, scene_type: str = "workshop", style: str = "historia_documentario") -> str:
        """Cria prompts no estilo do exemplo da catapulta de Leonardo"""
        try:
            # Templates baseados no seu exemplo
            leonardo_templates = {
                "workshop": "renaissance workshop interior, wooden bench with gears and springs, candlelight casting dramatic shadows, cinematic lighting, painterly realistic, subtle dust in air, vertical 9:16, no text, highly detailed, 8K resolution",
                "sketch": "cutaway illustration of renaissance mechanical concept with torsion springs and gear train, parchment paper, sepia ink, cinematic rim light, painterly realistic, vertical 9:16, no text, highly detailed, 8K resolution",
                "demonstration": "dramatic side view of reconstructed da Vinci mechanism in courtyard, wooden frame, coiled springs visible, evening light with long shadows, cinematic, painterly realistic, vertical 9:16, no text, highly detailed, 8K resolution",
                "comparison": "split composition: medieval mechanisms vs da Vinci elastic-spring design foreground, moody sky, cinematic lighting, painterly realistic, vertical 9:16, no text, highly detailed, 8K resolution",
                "vision": "montage: renaissance sketches morphing into modern engineering lab, gears becoming CAD blueprints on light table, cool cinematic glow, painterly-realistic blend, vertical 9:16, no text, highly detailed, 8K resolution",
                "portrait": "portrait-like scene of Leonardo observing his mechanical models, warm candlelight, reflective eyes, depth of field on wooden mechanisms, painterly realistic, vertical 9:16, no text, highly detailed, 8K resolution",
                "hero": "hero shot of da Vinci sketch overlaying dark background with subtle rainbow oil sheen, elegant composition, cinematic rim light, painterly realistic, vertical 9:16, no text, highly detailed, 8K resolution"
            }

            # Selecionar template mais apropriado
            template = leonardo_templates.get(
                scene_type, leonardo_templates["workshop"])

            # Se há descrição específica, integrar com template
            if scene_description.strip():
                # Extrair conceito principal da descrição
                cleaned_desc = self.clean_prompt_noise(scene_description)

                # Combinar descrição com estrutura técnica
                if "workshop" in cleaned_desc.lower() or "bancada" in cleaned_desc.lower():
                    return leonardo_templates["workshop"]
                elif "esboço" in cleaned_desc.lower() or "desenho" in cleaned_desc.lower():
                    return leonardo_templates["sketch"]
                elif "demonstra" in cleaned_desc.lower() or "ação" in cleaned_desc.lower():
                    return leonardo_templates["demonstration"]
                elif "compara" in cleaned_desc.lower() or "versus" in cleaned_desc.lower():
                    return leonardo_templates["comparison"]
                elif "futuro" in cleaned_desc.lower() or "moderno" in cleaned_desc.lower():
                    return leonardo_templates["vision"]
                elif "leonardo" in cleaned_desc.lower() or "retrato" in cleaned_desc.lower():
                    return leonardo_templates["portrait"]
                else:
                    return template

            return template

        except Exception as e:
            logger.error(f"❌ Erro ao criar prompt estilo Leonardo: {e}")
            return self.create_hybrid_prompt(scene_description, style=style)

    def generate_ultra_detailed_image_prompts(self, theme: str, script_data: Dict[str, Any]) -> Dict[str, str]:
        """Gera prompts ultra-detalhados e específicos para cada plataforma de IA"""
        try:
            # Detectar categoria do tema
            category = self._detect_content_category(theme, script_data)
            
            # Extrair elementos visuais do script
            visual_elements = self._extract_visual_keywords(script_data, theme)
            
            # Gerar prompts específicos para cada plataforma
            prompts = {}
            
            # DALL-E 3 - Foco em arte conceitual e criatividade
            prompts["dalle"] = self._create_dalle3_prompt(theme, category, visual_elements)
            
            # Imagen 3 - Foco em fotorealismo
            prompts["imagen3"] = self._create_imagen3_prompt(theme, category, visual_elements)
            
            # Imagen 4 - Máxima qualidade e detalhamento
            prompts["imagen4"] = self._create_imagen4_prompt(theme, category, visual_elements)
            
            logger.info(f"✅ Prompts ultra-detalhados gerados para tema: {theme}")
            return prompts
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar prompts ultra-detalhados: {e}")
            return {}

    def generate_video_animation_prompts(self, theme: str, script_data: Dict[str, Any], image_prompts: Dict[str, str] = None) -> Dict[str, str]:
        """Gera prompts ultra-detalhados para animação de vídeo"""
        try:
            category = self._detect_content_category(theme, script_data)
            narrative_flow = self._analyze_narrative_flow(script_data)
            
            prompts = {}
            
            # Leonardo AI - Movimento artístico e cinematográfico
            prompts["leonardo"] = self._create_leonardo_animation_prompt(theme, category, narrative_flow)
            
            # Veo 2 - Realismo e complexidade máxima
            prompts["veo2"] = self._create_veo2_animation_prompt(theme, category, narrative_flow)
            
            logger.info(f"✅ Prompts de animação gerados para tema: {theme}")
            return prompts
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar prompts de animação: {e}")
            return {}

    def _detect_content_category(self, theme: str, script_data: Dict[str, Any]) -> str:
        """Detecta categoria do conteúdo para otimização de prompts"""
        theme_lower = theme.lower()
        script_text = str(script_data.get("roteiro_completo", "")).lower()
        combined_text = f"{theme_lower} {script_text}"
        
        category_keywords = {
            "historia": ["história", "historia", "antigo", "medieval", "guerra", "civilização", "descoberta", "inventor"],
            "ciencia": ["ciência", "científico", "pesquisa", "experimento", "dna", "tecnologia", "descoberta"],
            "misterio": ["mistério", "enigma", "segredo", "paranormal", "inexplicável", "conspiração"],
            "tecnologia": ["tecnologia", "digital", "futuro", "inteligência artificial", "inovação", "robô"],
            "motivacional": ["motivação", "sucesso", "superação", "conquista", "inspiração", "crescimento"],
            "curiosidade": ["curiosidade", "fato", "incrível", "surpreendente", "descoberta", "interessante"]
        }
        
        category_scores = {}
        for category, keywords in category_keywords.items():
            score = sum(1 for keyword in keywords if keyword in combined_text)
            category_scores[category] = score
        
        if category_scores:
            best_category = max(category_scores, key=category_scores.get)
            if category_scores[best_category] > 0:
                return best_category
                
        return "curiosidade"

    def _extract_visual_keywords(self, script_data: Dict[str, Any], theme: str) -> List[str]:
        """Extrai palavras-chave visuais para incorporar nos prompts"""
        elements = []
        
        # Do script
        script_text = script_data.get("roteiro_completo", "")
        
        # Buscar elementos visuais específicos
        visual_patterns = [
            r'\b([A-Z][a-záêçõã]+(?:\s+[A-Z][a-záêçõã]+)*)\b',  # Nomes próprios
            r'\b(castelo|palácio|laboratório|floresta|oceano|montanha|cidade|igreja|prédio)\b',
            r'\b(dourado|prateado|vermelho|azul|verde|negro|branco|colorido)\b',
            r'\b(antigo|moderno|futurista|medieval|clássico|contemporâneo)\b',
            r'\b(máquina|ferramenta|instrumento|aparelho|dispositivo)\b'
        ]
        
        for pattern in visual_patterns:
            matches = re.findall(pattern, script_text.lower())
            elements.extend([match for match in matches if len(match) > 2])
        
        # Do tema
        theme_words = [word for word in theme.split() if len(word) > 3]
        elements.extend(theme_words)
        
        return list(set(elements))[:15]

    def _create_dalle3_prompt(self, theme: str, category: str, elements: List[str]) -> str:
        """Cria prompt específico otimizado para DALL-E 3"""
        config = self.ai_platform_configs["dalle"]
        
        # Estrutura base do tema
        base_description = f"Create a stunning vertical digital artwork about {theme}"
        
        # Adicionar elementos visuais específicos
        if elements:
            visual_desc = f", featuring {', '.join(elements[:5])}"
            base_description += visual_desc
        
        # Estilo artístico por categoria
        artistic_styles = {
            "historia": "renaissance painting style, historical accuracy, warm golden tones",
            "ciencia": "scientific illustration, technical precision, clean modern aesthetic",  
            "misterio": "dark atmospheric art, mysterious shadows, dramatic lighting",
            "tecnologia": "futuristic concept art, digital aesthetic, neon highlights",
            "motivacional": "inspirational poster art, bright uplifting colors, heroic composition",
            "curiosidade": "educational illustration, engaging visuals, clear presentation"
        }
        
        artistic_style = artistic_styles.get(category, artistic_styles["curiosidade"])
        
        # Composição e qualidade
        composition = "vertical 9:16 composition, perfect for mobile viewing, eye-catching design"
        quality_tags = ", ".join(config["quality_tags"][:3])
        style_modifiers = ", ".join(config["style_modifiers"][:2])
        
        prompt = f"""{base_description}

ARTISTIC STYLE: {artistic_style}, concept art masterpiece
COMPOSITION: {composition}, rule of thirds, dramatic focal point
TECHNICAL: {config["technical_specs"]}, {quality_tags}
QUALITY: {style_modifiers}, scroll-stopping imagery
MOOD: Engaging and captivating, perfect for YouTube Shorts"""

        return self._optimize_prompt_length(prompt, config["limit"])

    def _create_imagen3_prompt(self, theme: str, category: str, elements: List[str]) -> str:
        """Cria prompt fotorealista otimizado para Imagen 3"""
        config = self.ai_platform_configs["imagen3"]
        
        # Descrição fotográfica
        base_description = f"Professional vertical photograph showcasing {theme}"
        
        if elements:
            visual_desc = f", capturing {', '.join(elements[:4])} with photographic precision"
            base_description += visual_desc
        
        # Especificações fotográficas por categoria
        photo_specs = {
            "historia": "shot with vintage large format camera, warm natural lighting, documentary photography style",
            "ciencia": "macro photography, clinical lighting, high-resolution scientific documentation",
            "misterio": "atmospheric photography, dramatic shadows, film noir aesthetic",
            "tecnologia": "modern digital photography, LED lighting, futuristic composition",
            "motivacional": "portrait photography, golden hour lighting, inspiring composition",
            "curiosidade": "detailed close-up photography, perfect lighting, educational clarity"
        }
        
        photo_style = photo_specs.get(category, photo_specs["curiosidade"])
        
        # Especificações técnicas
        camera_settings = "shot with professional DSLR, 85mm lens, perfect exposure and focus"
        quality_tags = ", ".join(config["quality_tags"][:3])
        
        prompt = f"""{base_description}

PHOTOGRAPHY: {photo_style}, {camera_settings}
COMPOSITION: {config["technical_specs"]}, professional framing
QUALITY: {quality_tags}, museum-quality photography
LIGHTING: Natural photographic lighting, professionally lit
PURPOSE: Optimized for YouTube Shorts, maximum visual impact"""

        return self._optimize_prompt_length(prompt, config["limit"])

    def _create_imagen4_prompt(self, theme: str, category: str, elements: List[str]) -> str:
        """Cria prompt de máxima qualidade para Imagen 4"""
        config = self.ai_platform_configs["imagen4"]
        
        # Descrição de obra-prima
        base_description = f"Hyperrealistic masterpiece depicting {theme} with unprecedented detail"
        
        if elements:
            visual_desc = f", showcasing {', '.join(elements[:6])} in perfect artistic harmony"
            base_description += visual_desc
        
        # Especificações artísticas supremas por categoria
        masterpiece_specs = {
            "historia": "museum-quality historical recreation, period-perfect accuracy, masterful craftsmanship",
            "ciencia": "scientific visualization perfection, technical accuracy, educational excellence",
            "misterio": "atmospheric masterpiece, psychological depth, cinematic perfection",
            "tecnologia": "futuristic visualization excellence, cutting-edge aesthetics, innovative composition",
            "motivacional": "inspirational art mastery, emotional resonance, uplifting perfection",
            "curiosidade": "educational art excellence, perfect clarity, engaging presentation"
        }
        
        artistic_mastery = masterpiece_specs.get(category, masterpiece_specs["curiosidade"])
        
        # Qualidade suprema
        technical_perfection = config["technical_specs"]
        quality_tags = ", ".join(config["quality_tags"])
        style_modifiers = ", ".join(config["style_modifiers"][:3])
        
        prompt = f"""{base_description}

ARTISTIC MASTERY: {artistic_mastery}, {style_modifiers}
TECHNICAL SUPREMACY: {technical_perfection}, flawless execution
VISUAL IMPACT: {quality_tags}, breathtaking composition
EMOTIONAL DEPTH: Profound visual storytelling, memorable imagery
PLATFORM OPTIMIZATION: Perfect for YouTube Shorts, viral potential"""

        return self._optimize_prompt_length(prompt, config["limit"])

    def _create_leonardo_animation_prompt(self, theme: str, category: str, narrative_flow: str) -> str:
        """Cria prompt cinematográfico para Leonardo AI"""
        config = self.video_animation_configs["leonardo"]
        
        # Movimento base por categoria
        movement_styles = {
            "historia": "slow cinematic pan revealing historical details, atmospheric movement",
            "ciencia": "smooth zoom into scientific details, methodical camera movement", 
            "misterio": "suspenseful reveal with dramatic camera work, mysterious movement",
            "tecnologia": "futuristic camera transitions, sleek digital movement",
            "motivacional": "uplifting camera movements, inspiring reveal sequences",
            "curiosidade": "engaging exploratory movement, discovery-focused camera work"
        }
        
        base_movement = movement_styles.get(category, movement_styles["curiosidade"])
        
        # Fluxo narrativo específico
        narrative_movements = {
            "revelation": "dramatic reveal sequence with building tension",
            "action": "dynamic movement with energy and momentum",
            "mystery": "slow atmospheric movement with subtle reveals",
            "transformation": "smooth morphing transitions",
            "exploration": "curious exploratory camera movement"
        }
        
        specific_movement = narrative_movements.get(narrative_flow, "smooth cinematic movement")
        
        prompt = f"""Create cinematic animation for {theme}:

MOVEMENT STYLE: {base_movement}, {specific_movement}
CAMERA WORK: {config["technical_specs"]}, professional cinematography
DURATION: {config["duration_range"]}, perfectly timed for YouTube Shorts
VISUAL QUALITY: Cinematic excellence, {", ".join(config["movement_qualities"])}
COMPOSITION: Vertical 9:16 format, mobile-optimized framing
STORYTELLING: Visual narrative enhancement, engaging animation
TECHNICAL: Seamless loop capability, broadcast quality output"""

        return prompt.strip()

    def _create_veo2_animation_prompt(self, theme: str, category: str, narrative_flow: str) -> str:
        """Cria prompt realista complexo para Veo 2"""
        config = self.video_animation_configs["veo2"]
        
        # Dinâmica de cena por categoria
        scene_dynamics = {
            "historia": "detalhes ambientais historicamente precisos, física e iluminação adequadas ao período",
            "ciencia": "movimento cientificamente preciso, comportamento realista de materiais, dinâmicas de laboratório",
            "misterio": "mudanças ambientais atmosféricas, mudanças sutis de iluminação, ambiente misterioso",
            "tecnologia": "interação ambiental futurística, efeitos visuais high-tech, elementos digitais",
            "motivacional": "dinâmica ambiental inspiradora, atmosfera elevadora, energia motivacional",
            "curiosidade": "narrativa ambiental detalhada, progressão visual educativa"
        }
        
        scene_detail = scene_dynamics.get(category, scene_dynamics["curiosidade"])
        
        # Complexidade por fluxo narrativo
        narrative_complexity = {
            "revelation": "revelação multicamadas com narrativa ambiental complexa",
            "action": "dinâmica de alta energia com simulação de física realista",
            "mystery": "progressão atmosférica com mudanças de humor ambiental",
            "transformation": "morfismo sofisticado com física de transformação natural",
            "exploration": "descoberta ambiental imersiva com interação natural"
        }
        
        complexity_level = narrative_complexity.get(narrative_flow, "progressão ambiental natural")
        
        prompt = f"""Gere animação de vídeo premium realista para {theme}:

DINÂMICA DA CENA: {complexity_level}, {scene_detail}
REALISMO: {config["technical_specs"]}, simulação de física natural
DURAÇÃO: {config["duration_range"]}, capacidade narrativa estendida
COMPLEXIDADE: {", ".join(config["movement_qualities"])}, animação sofisticada
CINEMATOGRAFIA: trabalho de câmera de qualidade cinematográfica profissional, padrões broadcast
PROPORÇÃO: formato vertical 9:16, especificação YouTube Shorts
AMBIENTAL: mudanças realistas de iluminação, profundidade atmosférica, movimento natural
ENGAJAMENTO: retenção máxima do visualizador, qualidade otimizada para redes sociais"""

        return prompt.strip()

    def _analyze_narrative_flow(self, script_data: Dict[str, Any]) -> str:
        """Analisa o fluxo narrativo para determinar tipo de animação"""
        script = script_data.get("roteiro_completo", "").lower()
        
        if any(word in script for word in ["revelação", "descoberta", "surpreendente", "incrível", "revelar"]):
            return "revelation"
        elif any(word in script for word in ["batalha", "guerra", "conflito", "luta", "ação"]):
            return "action"
        elif any(word in script for word in ["mistério", "enigma", "segredo", "oculto", "misterioso"]):
            return "mystery"
        elif any(word in script for word in ["transformação", "evolução", "mudança", "desenvolvimento"]):
            return "transformation"
        else:
            return "exploration"

    def _optimize_prompt_length(self, prompt: str, max_length: int) -> str:
        """Otimiza o comprimento do prompt mantendo qualidade"""
        if len(prompt) <= max_length:
            return prompt
        
        # Remover seções menos críticas se necessário
        sections = prompt.split('\n\n')
        optimized_sections = []
        current_length = 0
        
        # Priorizar seções por importância
        priority_order = ["ARTISTIC", "TECHNICAL", "COMPOSITION", "QUALITY", "PHOTOGRAPHY", "MOVEMENT"]
        
        for section in sections:
            if current_length + len(section) <= max_length:
                optimized_sections.append(section)
                current_length += len(section)
            else:
                # Tentar encurtar a seção
                if any(priority in section for priority in priority_order[:3]):
                    # Manter seções importantes mas encurtadas
                    shortened = section[:max_length - current_length - 10] + "..."
                    optimized_sections.append(shortened)
                    break
        
        return '\n\n'.join(optimized_sections)

    def get_platform_capabilities(self) -> Dict[str, Dict[str, Any]]:
        """Retorna informações sobre as capacidades de cada plataforma"""
        return {
            "image_platforms": self.ai_platform_configs,
            "video_platforms": self.video_animation_configs
        }

    def get_available_styles(self) -> List[Dict[str, str]]:
        """Retorna estilos visuais disponíveis"""
        return [
            {
                "id": key,
                "name": style.name,
                "description": style.description
            }
            for key, style in self.visual_styles.items()
        ]

    def optimize_prompts_for_youtube_shorts(self, theme: str, script_data: Dict[str, Any]) -> Dict[str, Any]:
        """Gera todos os prompts otimizados especificamente para YouTube Shorts"""
        try:
            # Gerar prompts de imagem ultra-detalhados
            image_prompts = self.generate_ultra_detailed_image_prompts(theme, script_data)
            
            # Gerar prompts de animação baseados no script
            animation_prompts = self.generate_video_animation_prompts(theme, script_data, image_prompts)
            
            # Informações adicionais
            category = self._detect_content_category(theme, script_data)
            visual_elements = self._extract_visual_keywords(script_data, theme)
            
            return {
                "theme": theme,
                "category": category,
                "visual_elements": visual_elements,
                "image_prompts": image_prompts,
                "animation_prompts": animation_prompts,
                "optimization_tips": self._generate_youtube_shorts_tips(category),
                "technical_specs": {
                    "aspect_ratio": "9:16",
                    "target_duration": "15-60 seconds",
                    "quality": "Mobile-optimized, high engagement potential"
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao otimizar prompts para YouTube Shorts: {e}")
            return {}

    def _generate_youtube_shorts_tips(self, category: str) -> List[str]:
        """Gera dicas específicas de otimização para YouTube Shorts"""
        base_tips = [
            "Use cores vibrantes e contrastantes para chamar atenção",
            "Mantenha elementos importantes no centro da composição vertical",
            "Garanta que o texto seja legível em telas pequenas",
            "Use movimento para manter engajamento visual constante"
        ]
        
        category_tips = {
            "historia": [
                "Use paleta de cores épica e cinematográfica",
                "Inclua elementos arquitetônicos reconhecíveis da época",
                "Mantenha autenticidade histórica com drama visual"
            ],
            "ciencia": [
                "Use visualizações claras e educativas", 
                "Mantenha paleta de cores limpa e profissional",
                "Inclua elementos gráficos que facilitem compreensão"
            ],
            "misterio": [
                "Use contraste dramático entre luz e sombra",
                "Inclua elementos que criem tensão visual",
                "Mantenha atmosfera envolvente e suspenseful"
            ],
            "tecnologia": [
                "Use cores neon e elementos futuristas",
                "Inclua interfaces e elementos digitais reconhecíveis",
                "Mantenha estética moderna e clean"
            ],
            "motivacional": [
                "Use cores inspiradoras e energéticas",
                "Inclua elementos que transmitam sucesso e conquista",
                "Mantenha composição ascendente e positiva"
            ],
            "curiosidade": [
                "Use elementos visuais intrigantes e educativos",
                "Mantenha clareza visual para fácil compreensão",
                "Inclua detalhes que despertem curiosidade"
            ]
        }
        
        return base_tips + category_tips.get(category, [])

    def generate_textarea_prompts(self, theme: str, target_duration_seconds: int, script_data: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
        """Gera prompts formatados para textarea baseado na duração do vídeo e configuração de 3 segundos por imagem"""
        try:
            # Calcular número de prompts necessários
            num_prompts = self.calculate_number_of_prompts(target_duration_seconds)
            
            # Detectar categoria se script disponível
            category = "curiosidade"
            visual_elements = []
            if script_data:
                category = self._detect_content_category(theme, script_data)
                visual_elements = self._extract_visual_keywords(script_data, theme)
            
            # Gerar prompts base
            image_prompts = self.generate_ultra_detailed_image_prompts(theme, script_data or {})
            animation_prompts = self.generate_video_animation_prompts(theme, script_data or {})
            
            # Formatar para textarea - IMAGENS
            image_textarea = self._format_image_prompts_for_textarea(
                theme, num_prompts, image_prompts, category, visual_elements
            )
            
            # Formatar para textarea - ANIMAÇÕES
            animation_textarea = self._format_animation_prompts_for_textarea(
                theme, num_prompts, animation_prompts, category
            )
            
            logger.info(f"✅ Textarea prompts gerados: {num_prompts} prompts para {target_duration_seconds}s de vídeo")
            
            return {
                "image_prompts": image_textarea,
                "animation_prompts": animation_textarea,
                "video_info": {
                    "target_duration": target_duration_seconds,
                    "num_prompts": num_prompts,
                    "seconds_per_image": self.SECONDS_PER_IMAGE,
                    "category": category
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar prompts para textarea: {e}")
            return {
                "image_prompts": f"Erro ao gerar prompts de imagem: {e}",
                "animation_prompts": f"Erro ao gerar prompts de animação: {e}",
                "video_info": {}
            }

    def _format_image_prompts_for_textarea(self, theme: str, num_prompts: int, 
                                         image_prompts: Dict[str, str], category: str, 
                                         visual_elements: List[str]) -> str:
        """Formata prompts de imagem para exibição em textarea"""
        lines = []
        lines.append(f"🎯 TEMA: {theme}")
        lines.append(f"📊 {num_prompts} IMAGENS × {self.SECONDS_PER_IMAGE}s = {num_prompts * self.SECONDS_PER_IMAGE}s total")
        lines.append(f"📁 CATEGORIA: {category.upper()}")
        lines.append("")
        
        # Para cada plataforma
        for platform, prompt in image_prompts.items():
            platform_name = self.ai_platform_configs.get(platform, {}).get("name", platform.upper())
            lines.append(f"🖼️ ═══ {platform_name} ═══")
            lines.append("")
            
            # Gerar prompts numerados para cada imagem necessária
            for i in range(num_prompts):
                scene_time_start = i * self.SECONDS_PER_IMAGE
                scene_time_end = (i + 1) * self.SECONDS_PER_IMAGE
                
                # Personalizar cada prompt com elementos únicos
                customized_prompt = self._customize_prompt_for_scene(
                    prompt, i, num_prompts, visual_elements, theme
                )
                
                lines.append(f"⏱️ CENA {i+1}: {scene_time_start}s-{scene_time_end}s")
                lines.append(f"📸 {customized_prompt}")
                lines.append("")
            
            lines.append("─" * 50)
            lines.append("")
        
        return "\n".join(lines)

    def _format_animation_prompts_for_textarea(self, theme: str, num_prompts: int, 
                                             animation_prompts: Dict[str, str], category: str) -> str:
        """Formata prompts de animação para exibição em textarea"""
        lines = []
        lines.append(f"🎬 ANIMAÇÃO: {theme}")
        lines.append(f"📊 {num_prompts} CENAS × {self.SECONDS_PER_IMAGE}s = {num_prompts * self.SECONDS_PER_IMAGE}s total")
        lines.append(f"📁 CATEGORIA: {category.upper()}")
        lines.append("")
        
        # Para cada plataforma de vídeo
        for platform, prompt in animation_prompts.items():
            platform_name = self.video_animation_configs.get(platform, {}).get("name", platform.upper())
            lines.append(f"🎥 ═══ {platform_name} ═══")
            lines.append("")
            
            # Gerar animações numeradas para cada cena
            for i in range(num_prompts):
                scene_time_start = i * self.SECONDS_PER_IMAGE
                scene_time_end = (i + 1) * self.SECONDS_PER_IMAGE
                
                # Personalizar animação para a cena
                animation_style = self._get_animation_style_for_scene(platform, i, num_prompts)
                
                lines.append(f"⏱️ CENA {i+1}: {scene_time_start}s-{scene_time_end}s")
                lines.append(f"🎬 {animation_style}")
                lines.append(f"💫 DURAÇÃO: {self.SECONDS_PER_IMAGE} segundos")
                lines.append("")
            
            lines.append("─" * 50)
            lines.append("")
        
        return "\n".join(lines)

    def _customize_prompt_for_scene(self, base_prompt: str, scene_index: int, 
                                  total_scenes: int, visual_elements: List[str], theme: str) -> str:
        """Customiza prompt base para cada cena específica"""
        try:
            # Variações por posição na narrativa
            narrative_position = "opening" if scene_index == 0 else "middle" if scene_index < total_scenes - 1 else "closing"
            
            # Variações de enquadramento
            framing_options = [
                "wide establishing shot", "medium shot", "close-up detail", 
                "dramatic angle", "overhead view", "side perspective"
            ]
            framing = framing_options[scene_index % len(framing_options)]
            
            # Elementos visuais únicos por cena
            if visual_elements and len(visual_elements) > scene_index:
                focus_element = visual_elements[scene_index % len(visual_elements)]
                element_detail = f", focusing on {focus_element}"
            else:
                element_detail = ""
            
            # Variações de mood por posição
            mood_variations = {
                "opening": "intriguing introduction, hook visual",
                "middle": "developing narrative, building tension", 
                "closing": "powerful conclusion, memorable finale"
            }
            mood = mood_variations.get(narrative_position, "engaging visual storytelling")
            
            # Personalizar o prompt
            customized = f"{base_prompt}{element_detail}, {framing}, {mood}"
            
            return customized
            
        except Exception as e:
            logger.error(f"❌ Erro ao customizar prompt para cena {scene_index}: {e}")
            return base_prompt

    def _get_animation_style_for_scene(self, platform: str, scene_index: int, total_scenes: int) -> str:
        """Retorna estilo de animação específico para a cena"""
        try:
            config = self.video_animation_configs.get(platform, self.video_animation_configs["leonardo"])
            animation_styles = config["animation_styles"]
            
            # Selecionar estilo baseado na posição na narrativa
            if scene_index == 0:
                # Cena de abertura - movimento de introdução
                style_options = ["slow cinematic zoom in", "dramatic reveal", "epic opening pan"]
            elif scene_index == total_scenes - 1:
                # Cena final - movimento de conclusão  
                style_options = ["powerful finale zoom", "concluding pan out", "memorable closing movement"]
            else:
                # Cenas intermediárias - movimento de desenvolvimento
                style_options = animation_styles[1:-1] if len(animation_styles) > 2 else animation_styles
            
            selected_style = style_options[scene_index % len(style_options)]
            
            # Adicionar especificações técnicas
            technical_specs = config["technical_specs"]
            duration_note = f"{self.SECONDS_PER_IMAGE} seconds duration"
            
            return f"{selected_style}, {technical_specs}, {duration_note}, vertical 9:16 format"
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter estilo de animação para cena {scene_index}: {e}")
            return f"smooth cinematic movement, {self.SECONDS_PER_IMAGE} seconds, vertical format"
