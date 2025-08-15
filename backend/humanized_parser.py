# Parser Atualizado para Formato Estruturado
import re
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class HumanizedParser:
    def __init__(self):
        self.default_values = {
            "estimated_duration": 60,
            "viral_score": 85,
            "hashtags": ["#viral", "#tiktok", "#brasil", "#historia", "#incrivel"],
            "speech_optimized": True
        }

    def extract_humanized_script(self, response_text: str, ai_provider: str = "unknown") -> Dict[str, Any]:
        """Extrai roteiro do novo formato estruturado"""
        
        try:
            logger.info(f"Extraindo roteiro humanizado de {ai_provider}")
            
            # Primeiro tentar JSON (formato principal)
            json_result = self._try_standard_json(response_text)
            if json_result:
                # Processar JSON e criar prompts visuais
                processed = self._process_json_format(json_result, ai_provider)
                return processed
            
            # Fallback: Extrair do formato estruturado texto
            extracted = self._extract_structured_format(response_text)
            
            # Garantir estrutura completa
            return self._ensure_complete_structure(extracted, ai_provider)
            
        except Exception as e:
            logger.error(f"Erro ao extrair roteiro: {e}")
            return self._create_emergency_fallback(response_text, ai_provider)

    def _process_json_format(self, json_data: Dict[str, Any], ai_provider: str) -> Dict[str, Any]:
        """Processa formato JSON e cria prompts visuais e Leonardo AI"""
        
        # Dados básicos do JSON
        result = {
            "titulo": json_data.get("titulo", "Conteúdo Viral"),
            "roteiro_completo": self._clean_script_for_narration(json_data.get("roteiro_completo", "")),
            "roteiro_original": json_data.get("roteiro_completo", ""),  # Manter original com tags
            "hook": self._extract_hook_from_script(json_data.get("roteiro_completo", "")),
            "tipo_historia": json_data.get("tipo_historia", ""),
            "estrutura_usada": json_data.get("estrutura_usada", []),
            "duracao_estimada": json_data.get("duracao_estimada", 60),
            "estilo_visual": json_data.get("estilo_visual", "curiosidade"),
            "call_to_action": json_data.get("call_to_action", ""),
            "tom_narrativa": json_data.get("tom_narrativa", ""),
            "ai_provider": ai_provider
        }
        
        # Extrair visual_cues e criar prompts detalhados
        visual_cues = json_data.get("visual_cues", [])
        
        # Determinar duração ideal (até 60s, se maior criar partes)
        target_duration = min(result["duracao_estimada"], 60)
        words_per_second = 2.5  # Velocidade média de fala
        max_words = int(target_duration * words_per_second)
        
        # Verificar se precisa dividir em partes
        script_words = len(result["roteiro_completo"].split())
        needs_parts = script_words > max_words
        
        if needs_parts:
            result["needs_parts"] = True
            result["estimated_parts"] = max(2, script_words // max_words)
            result["roteiro_completo"] = self._truncate_for_part_1(result["roteiro_completo"], max_words)
            result["parte_atual"] = 1
        
        # Determinar número de imagens baseado na duração - CONFIGURAÇÃO 3 SEGUNDOS POR IMAGEM
        duration_seconds = len(result["roteiro_completo"].split()) / words_per_second
        # Para vídeos de 1 minuto (60s), sempre 20 prompts
        if duration_seconds >= 60:
            num_images = 20
        else:
            num_images = max(3, int(duration_seconds / 3))  # 1 imagem a cada 3s, mínimo 3 imagens
        
        if visual_cues:
            # Expandir visual_cues para o número de imagens necessário (3s por imagem)
            if len(visual_cues) < num_images:
                # Se temos 8 prompts e precisamos de 20 imagens, reutilizar prompts ciclicamente
                expanded_cues = []
                for i in range(num_images):
                    # Cicla pelos prompts existentes: 0,1,2,3,4,5,6,7,0,1,2,3,4,5,6,7,0,1,2,3...
                    cue_index = i % len(visual_cues)
                    expanded_cues.append(visual_cues[cue_index])
                visual_cues = expanded_cues
            elif len(visual_cues) > num_images:
                # Se temos mais prompts que imagens necessárias, usar apenas os primeiros
                visual_cues = visual_cues[:num_images]
            
            # Dividir roteiro em segmentos baseado no número de imagens
            script_segments = self._split_script_by_cues(result["roteiro_completo"], num_images)
            
            # Criar prompts visuais e Leonardo AI
            visual_prompts = []
            leonardo_prompts = []
            
            for i, (cue, segment) in enumerate(zip(visual_cues, script_segments)):
                # Tempo de cada cena: FIXO 3 SEGUNDOS
                scene_duration = 3  # 3 segundos por imagem
                start_time = i * scene_duration
                end_time = (i + 1) * scene_duration
                
                # Prompt de imagem baseado no visual_cue
                image_prompt = self._create_image_prompt(cue, result["estilo_visual"], segment)
                
                # Prompt Leonardo AI
                leonardo_prompt = self._create_leonardo_prompt(i)
                
                visual_prompts.append({
                    "timing": f"{start_time:.0f}-{end_time:.0f}s",
                    "narration": segment.strip(),
                    "image_prompt": image_prompt,
                    "scene_number": i + 1
                })
                
                leonardo_prompts.append({
                    "timing": f"{start_time:.0f}-{end_time:.0f}s", 
                    "animation": leonardo_prompt,
                    "duration": f"{scene_duration:.0f} seconds",
                    "scene_number": i + 1
                })
        
            result["visual_prompts"] = visual_prompts
            result["leonardo_prompts"] = leonardo_prompts
            
            # Criar strings separadas para os text areas
            result["visual_prompts_text"] = self._format_visual_prompts_for_textarea(visual_prompts)
            result["leonardo_prompts_text"] = self._format_leonardo_prompts_for_textarea(leonardo_prompts)
        else:
            # Fallback se não houver visual_cues
            result["visual_prompts"] = []
            result["leonardo_prompts"] = []
            result["visual_prompts_text"] = ""
            result["leonardo_prompts_text"] = ""
        
        # Adicionar campos compatíveis com o sistema antigo
        result["estimated_duration"] = int(duration_seconds)
        result["viral_score"] = 87
        result["hashtags"] = self._generate_hashtags(result["tipo_historia"])
        result["speech_optimized"] = True
        
        # Log para debug do sistema de 3 segundos
        logger.info(f"✅ SISTEMA 3s: {num_images} imagens para {duration_seconds:.0f}s de vídeo")
        logger.info(f"📊 Visual cues: {len(visual_cues)} → Prompts expandidos: {len(result.get('visual_prompts', []))}")
        
        return result

    def _clean_script_for_narration(self, script: str) -> str:
        """Remove tags e limpa o texto para narração pura"""
        if not script:
            return ""
        
        # Remover tags específicas
        cleaned = script
        cleaned = cleaned.replace("[PAUSA]", "")
        cleaned = cleaned.replace("[ÊNFASE]", "")
        cleaned = cleaned.replace("[GANCHO]", "")
        cleaned = cleaned.replace("[HOOK]", "")
        cleaned = cleaned.replace("[CTA]", "")
        cleaned = cleaned.replace("[CLÍMAX]", "")
        
        # Limpar espaços extras
        cleaned = " ".join(cleaned.split())
        
        return cleaned.strip()

    def _truncate_for_part_1(self, script: str, max_words: int) -> str:
        """Trunca o script para a Parte 1 e adiciona continuação"""
        words = script.split()
        if len(words) <= max_words:
            return script
        
        # Truncar e adicionar indicação de continuidade
        truncated = " ".join(words[:max_words])
        
        # Tentar terminar em uma frase completa
        last_punct = max(truncated.rfind('.'), truncated.rfind('!'), truncated.rfind('?'))
        if last_punct > len(truncated) * 0.8:  # Se a pontuação está nos últimos 20%
            truncated = truncated[:last_punct + 1]
        
        truncated += " Continue assistindo a Parte 2 para descobrir o resto da história!"
        
        return truncated

    def _format_visual_prompts_for_textarea(self, visual_prompts: list) -> str:
        """Formata prompts visuais para exibição em textarea"""
        if not visual_prompts:
            return ""
        
        formatted = []
        for prompt in visual_prompts:
            scene_text = f"⏰ Cena {prompt['scene_number']}: {prompt['timing']}\n"
            scene_text += f"📸 PROMPT IMAGEN 3:\n{prompt['image_prompt']}\n"
            formatted.append(scene_text)
        
        return "\n".join(formatted)

    def _format_leonardo_prompts_for_textarea(self, leonardo_prompts: list) -> str:
        """Formata prompts Leonardo AI para exibição em textarea"""
        if not leonardo_prompts:
            return ""
        
        formatted = []
        for prompt in leonardo_prompts:
            scene_text = f"⏰ Cena {prompt['scene_number']}: {prompt['timing']}\n"
            scene_text += f"🎬 PROMPT LEONARDO AI:\n{prompt['animation']}\n"
            formatted.append(scene_text)
        
        return "\n".join(formatted)

    def _extract_hook_from_script(self, script: str) -> str:
        """Extrai o hook (primeiras palavras) do roteiro"""
        if not script:
            return "Você não vai acreditar nisso..."
        
        # Pegar primeiras 50-80 caracteres
        words = script.split()
        hook_words = []
        char_count = 0
        
        for word in words:
            if char_count + len(word) > 80:
                break
            hook_words.append(word)
            char_count += len(word) + 1
        
        return " ".join(hook_words)

    def _split_script_by_cues(self, script: str, num_cues: int) -> list:
        """Divide o roteiro em segmentos baseado no número de visual_cues"""
        if not script:
            return ["Conteúdo gerado"] * num_cues
        
        # Remove pausas e ênfases para análise
        clean_script = script.replace("[PAUSA]", "").replace("[ÊNFASE]", "")
        words = clean_script.split()
        
        if len(words) < num_cues:
            # Se há poucas palavras, repetir o script
            return [script] * num_cues
        
        # Dividir em segmentos aproximadamente iguais
        words_per_segment = len(words) // num_cues
        segments = []
        
        for i in range(num_cues):
            start_idx = i * words_per_segment
            if i == num_cues - 1:  # Último segmento pega o resto
                segment_words = words[start_idx:]
            else:
                end_idx = (i + 1) * words_per_segment
                segment_words = words[start_idx:end_idx]
            
            segments.append(" ".join(segment_words))
        
        return segments

    def _create_image_prompt(self, visual_cue: str, estilo_visual: str, segment: str) -> str:
        """Cria prompt detalhado para Imagen 3"""
        
        # Mapear estilos visuais para descritores
        style_descriptors = {
            "curiosidade": "vibrant colors, engaging composition, educational style, modern design",
            "misterio": "dark atmosphere, mysterious lighting, dramatic shadows, vintage style", 
            "historia": "historical accuracy, period details, cinematic lighting, documentary style",
            "ciencia": "scientific visualization, clean design, modern graphics, professional style",
            "tecnologia": "futuristic design, tech aesthetic, sleek visuals, digital style"
        }
        
        style_desc = style_descriptors.get(estilo_visual, "engaging visual style")
        
        # Extrair palavras-chave do segmento de narração
        key_words = self._extract_keywords_from_segment(segment)
        
        prompt = f"{visual_cue}, {key_words}, {style_desc}, ultra detailed, 8K resolution, professional photography, vertical format 9:16, no text, trending on artstation"
        
        return prompt

    def _create_leonardo_prompt(self, scene_index: int) -> str:
        """Cria prompt de animação para Leonardo AI"""
        
        # Variados tipos de movimento cinematográfico
        animations = [
            "pan left to right, slow dramatic camera movement",
            "zoom in slowly, smooth cinematic transition", 
            "rotate 360 degrees, elegant camera rotation",
            "fade transition, atmospheric depth effect",
            "slide up reveal, dynamic vertical movement",
            "zoom out reveal, expansive perspective change",
            "tilt shift effect, professional depth focus",
            "parallax scrolling, layered depth movement"
        ]
        
        animation = animations[scene_index % len(animations)]
        
        return f"{animation}, cinematic style, smooth transitions, professional quality, 4-8 seconds duration, loop seamlessly"

    def _extract_keywords_from_segment(self, segment: str) -> str:
        """Extrai palavras-chave visuais do segmento de narração"""
        
        # Lista de stopwords para remover
        stopwords = {"o", "a", "os", "as", "de", "da", "do", "das", "dos", "em", "na", "no", "e", "que", "para", "com", "por", "se", "é", "foi", "são", "foram"}
        
        # Limpar e filtrar palavras
        words = segment.lower().replace("[PAUSA]", "").replace("[ÊNFASE]", "").split()
        keywords = [word for word in words if len(word) > 3 and word not in stopwords]
        
        # Pegar até 3 palavras-chave mais relevantes
        return " ".join(keywords[:3])

    def _generate_hashtags(self, tipo_historia: str) -> list:
        """Gera hashtags baseadas no tipo de história"""
        
        base_hashtags = ["#viral", "#tiktok", "#brasil"]
        
        historia_hashtags = {
            "Historia Historica": ["#historia", "#fatos", "#educativo", "#conhecimento"],
            "Historia Infantil": ["#infantil", "#criancas", "#educacao", "#diversao"],
            "Historia de Misterio": ["#misterio", "#suspense", "#enigma", "#intrigante"],
            "Historia de Curiosidade": ["#curiosidade", "#sabiaquedesvele", "#incrivel", "#descoberta"]
        }
        
        specific_tags = historia_hashtags.get(tipo_historia, ["#interessante", "#conteudo"])
        
        return base_hashtags + specific_tags[:2]

    def _extract_structured_format(self, text: str) -> Dict[str, Any]:
        """Extrai dados do novo formato estruturado TÍTULO/RESUMO/ROTEIRO"""
        
        result = {}
        
        # Extrair TÍTULO
        title_match = re.search(r'TÍTULO:\s*(.+?)(?=\n|RESUMO:|$)', text, re.IGNORECASE)
        if title_match:
            result["titulo"] = title_match.group(1).strip()
        
        # Extrair RESUMO
        resumo_match = re.search(r'RESUMO:\s*(.+?)(?=\n\n|ROTEIRO:|$)', text, re.IGNORECASE)
        if resumo_match:
            result["resumo"] = resumo_match.group(1).strip()
        
        # Extrair ROTEIRO completo (todo o conteúdo cronometrado)
        roteiro_match = re.search(r'ROTEIRO:\s*(.*?)(?=MÚSICA:|NOTAS DE PRODUÇÃO:|CAPÍTULOS:|$)', text, re.IGNORECASE | re.DOTALL)
        if roteiro_match:
            roteiro_text = roteiro_match.group(1).strip()
            result["roteiro_completo"] = self._process_timed_script(roteiro_text)
            
            # Extrair hook (primeira parte do roteiro)
            first_part = re.search(r'\[0s-\d+s\]\s*—\s*(.+?)(?=\n|\[)', roteiro_text)
            if first_part:
                result["hook"] = first_part.group(1).strip().strip('"')
        
        # Extrair MÚSICA
        musica_match = re.search(r'MÚSICA:\s*(.+?)(?=\n|NOTAS DE PRODUÇÃO:|$)', text, re.IGNORECASE)
        if musica_match:
            result["musica"] = musica_match.group(1).strip()
        
        # Extrair NOTAS DE PRODUÇÃO
        notas_match = re.search(r'NOTAS DE PRODUÇÃO:\s*(.+?)(?=\n|CAPÍTULOS:|$)', text, re.IGNORECASE)
        if notas_match:
            result["notas_producao"] = notas_match.group(1).strip()
        
        # Extrair prompts de imagem
        result["visual_prompts"] = self._extract_image_prompts(text)
        
        # Extrair prompts de animação
        result["animation_prompts"] = self._extract_animation_prompts(text)
        
        return result

    def _process_timed_script(self, roteiro_text: str) -> str:
        """Processa roteiro cronometrado e extrai apenas o texto narrativo"""
        
        # Extrair todas as partes narradas (texto após —)
        narrative_parts = re.findall(r'\[\d+s-\d+s\]\s*—\s*"?([^"\n]+)"?', roteiro_text)
        
        if narrative_parts:
            # Juntar todas as partes narrativas
            full_script = " ".join(part.strip() for part in narrative_parts)
            return full_script
        
        # Fallback: limpar o texto e usar tudo
        cleaned = re.sub(r'PROMPT_IMAGE3:.*?(?=\n|\[|$)', '', roteiro_text, flags=re.IGNORECASE)
        cleaned = re.sub(r'PROMPT_LEONARDO:.*?(?=\n|\[|$)', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\[.*?\]', '', cleaned)
        
        return cleaned.strip()

    def _extract_image_prompts(self, text: str) -> list:
        """Extrai todos os prompts de imagem"""
        
        prompts = re.findall(r'PROMPT_IMAGE3:\s*(.+?)(?=\n|PROMPT_LEONARDO:|$)', text, re.IGNORECASE)
        return [prompt.strip().strip('"') for prompt in prompts]

    def _extract_animation_prompts(self, text: str) -> list:
        """Extrai todos os prompts de animação"""
        
        prompts = re.findall(r'PROMPT_LEONARDO:\s*(.+?)(?=\n|\[|$)', text, re.IGNORECASE)
        return [prompt.strip().strip('"') for prompt in prompts]

    def _try_standard_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Tenta extrair JSON padrão se ainda vier no formato antigo"""
        
        try:
            # Procurar JSON entre ```json e ```
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL | re.IGNORECASE)
            if json_match:
                return json.loads(json_match.group(1))
            
            # Procurar JSON entre primeira { e última }
            start = text.find('{')
            end = text.rfind('}')
            if start != -1 and end != -1 and end > start:
                json_text = text[start:end+1]
                return json.loads(json_text)
                
        except (json.JSONDecodeError, Exception):
            pass
            
        return None

    def _ensure_complete_structure(self, extracted: Dict[str, Any], ai_provider: str) -> Dict[str, Any]:
        """Garante que todos os campos necessários existem"""
        
        result = {
            "titulo": extracted.get("titulo", "Conteúdo Viral Gerado"),
            "resumo": extracted.get("resumo", "História interessante e envolvente"),
            "roteiro_completo": extracted.get("roteiro_completo", "Conteúdo gerado pela IA"),
            "hook": extracted.get("hook", "Você não vai acreditar nessa história"),
            "musica": extracted.get("musica", "trilha inspiradora"),
            "notas_producao": extracted.get("notas_producao", "cores vibrantes, transições suaves"),
            "visual_prompts": extracted.get("visual_prompts", []),
            "animation_prompts": extracted.get("animation_prompts", []),
            "estimated_duration": self.default_values["estimated_duration"],
            "viral_score": self.default_values["viral_score"],
            "hashtags": self.default_values["hashtags"],
            "speech_optimized": True,
            "ai_provider": ai_provider,
            "cenas_visuais": self._create_visual_scenes(extracted)
        }
        
        return result

    def _create_visual_scenes(self, extracted: Dict[str, Any]) -> list:
        """Cria estrutura de cenas visuais a partir dos prompts extraídos"""
        
        image_prompts = extracted.get("visual_prompts", [])
        animation_prompts = extracted.get("animation_prompts", [])
        
        scenes = []
        for i, (img_prompt, anim_prompt) in enumerate(zip(image_prompts, animation_prompts)):
            scene = {
                "timing": f"{i*5}s-{(i+1)*5}s",
                "prompt_imagem": img_prompt,
                "animacao_leonardo": anim_prompt,
                "mood_visual": "envolvente e cinematográfico"
            }
            scenes.append(scene)
        
        return scenes

    def _ensure_humanized_format(self, json_data: Dict[str, Any]) -> Dict[str, Any]:
        """Converte JSON antigo para novo formato se necessário"""
        
        # Se já está no formato correto, retorna
        if "roteiro_completo" in json_data:
            return json_data
        
        # Converte formato antigo
        if "capitulos" in json_data:
            primeiro_capitulo = json_data["capitulos"][0] if json_data["capitulos"] else {}
            return {
                "titulo": json_data.get("titulo_geral", "Título Gerado"),
                "roteiro_completo": primeiro_capitulo.get("roteiro_completo", "Roteiro gerado"),
                "hook": primeiro_capitulo.get("hook", "Hook gerado"),
                **self.default_values
            }
        
        return json_data

    def _create_emergency_fallback(self, response_text: str, ai_provider: str) -> Dict[str, Any]:
        """Cria resposta de emergência se tudo falhar"""
        
        # Limpar texto
        clean_text = re.sub(r'```\w*', '', response_text)
        clean_text = re.sub(r'[{}"]', '', clean_text)
        clean_text = clean_text.strip()
        
        # Usar até 300 caracteres do texto limpo
        script_text = clean_text[:300] if len(clean_text) > 50 else "Roteiro gerado automaticamente pela IA."
        
        return {
            "titulo": "Conteúdo Viral Criado",
            "roteiro_completo": script_text,
            "hook": "Essa história vai te surpreender",
            **self.default_values,
            "ai_provider": ai_provider,
            "extraction_method": "emergency_fallback"
        }
