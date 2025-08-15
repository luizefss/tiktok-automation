# /var/www/tiktok-automation/backend/hybrid_ai.py

import random
import requests
import json
from datetime import datetime
import os
from dotenv import load_dotenv
from typing import Dict, Any, Optional  # Adicionado para anotações de tipo


class HybridAI:
    def __init__(self):
        load_dotenv()  # Carrega variáveis de ambiente

        self.claude_api_key = os.getenv("CLAUDE_API_KEY")
        # A proporção de uso pode não ser relevante aqui se o orquestrador que decide,
        # mas pode ser mantida se o HybridAI for usado em outro contexto
        self.use_claude_ratio = 0.3

        if not self.claude_api_key:
            print(
                "⚠️ CLAUDE_API_KEY não encontrada no .env. Claude AI pode não funcionar.")

    def gerar_roteiro_claude(self, settings: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Gera roteiro usando Claude AI com base nas configurações fornecidas.
        O Claude espera uma 'categoria' para o prompt, que será mapeada dos settings.
        """
        if not self.claude_api_key:
            print("❌ Claude API Key não configurada. Geração com Claude desabilitada.")
            return None

        try:
            # Claude espera uma categoria ou tópicos para construir o prompt.
            # Mapeia as settings para o que Claude precisa para o prompt.
            # Usando 'message_categories' do settings, pegando a primeira.
            categoria = settings.get('message_categories', ['curiosidades'])[0]
            prompt = self.criar_prompt_roteiro(categoria, settings)

            response = requests.post(
                'https://api.anthropic.com/v1/messages',
                headers={
                    'x-api-key': self.claude_api_key,
                    'anthropic-version': '2023-06-01',
                    'content-type': 'application/json'
                },
                json={
                    # Verifique se este modelo está disponível no seu plano
                    'model': 'claude-3-5-sonnet-20241022',
                    'max_tokens': 1000,
                    'messages': [
                        {'role': 'user', 'content': prompt}
                    ]
                }
            )

            if response.status_code == 200:
                data = response.json()
                texto_resposta = data['content'][0]['text']

                # Claude pode retornar texto solto ou JSON dentro de markdown
                try:
                    import re
                    if texto_resposta.strip().startswith('```json'):
                        # Extrai JSON de bloco de código markdown
                        match = re.search(r'```json\n(.*?)```',
                                          texto_resposta, re.DOTALL)
                        if match:
                            json_text = match.group(1).strip()
                            roteiro = json.loads(json_text)
                        else:
                            print(
                                "⚠️ Claude respondeu com bloco JSON, mas formato inesperado. Não foi possível extrair JSON.")
                            print(
                                f"Resposta Claude (trecho): {texto_resposta[:200]}...")
                            return None
                    else:  # Tenta parsear diretamente se não houver markdown
                        roteiro = json.loads(texto_resposta.strip())
                except json.JSONDecodeError as json_e:
                    print(
                        f"❌ Erro ao decodificar JSON da resposta do Claude: {json_e}")
                    print(
                        f"Resposta Claude (trecho): {texto_resposta[:200]}...")
                    return None

                roteiro['ia_used'] = 'claude'
                roteiro['timestamp'] = datetime.now().isoformat()

                return roteiro

            else:
                print(
                    f"❌ Erro Claude API (Status: {response.status_code}): {response.text}")
                return None

        except Exception as e:
            print(f"❌ Erro na geração Claude: {e}")
            return None

    def criar_prompt_roteiro(self, categoria: str, settings: Dict[str, Any] = None) -> str:
        """Cria prompt otimizado para Claude com storytelling em capítulos"""
        if settings is None:
            settings = {}
            
        # Mapear categorias para temas de storytelling
        storytelling_themes = {
            "curiosidades": "uma descoberta pessoal surpreendente que mudou sua perspectiva",
            "historia": "uma experiência pessoal marcante com lições de vida",
            "ciencia": "como uma descoberta científica impactou pessoalmente sua vida",
            "misterios": "um mistério real que você vivenciou ou investigou pessoalmente",
            "tecnologia": "como uma tecnologia mudou radicalmente seu cotidiano",
            "motivacao": "uma história de superação pessoal autêntica",
            "reflexao": "um momento de mudança profunda em sua vida"
        }

        tema = storytelling_themes.get(categoria, "uma experiência pessoal transformadora")
        duration_minutes = settings.get('duration', 90) / 60
        create_chapters = duration_minutes > 1.5 or settings.get('multi_chapter', False)
        
        if create_chapters:
            chapter_instruction = """
        **MODO CAPÍTULOS ATIVADO**: Crie uma história dividida em 3 capítulos:
        - Capítulo 1: Situação inicial e conflito (75-90s)
        - Capítulo 2: Desenvolvimento e complicações (75-90s)  
        - Capítulo 3: Clímax e resolução (75-90s)
        
        Duração total: aprox. 255s (4min 15s) - Compatível com TikTok (3min) e Kwai (7min)
        Cada capítulo individualmente compatível com YouTube Shorts (60s quando editado)
        
        Cada capítulo deve ter seu próprio hook e cliffhanger (exceto o último).
            """
        else:
            chapter_instruction = "**MODO HISTÓRIA ÚNICA**: Conte toda a experiência em um vídeo de 90 segundos."

        return f"""
        Você é um especialista em STORYTELLING PESSOAL e criação de narrativas envolventes para redes sociais.
        
        {chapter_instruction}
        
        Crie uma história AUTÊNTICA sobre {tema}, como se fosse uma experiência real vivida por alguém.
        
        ESTRUTURA NARRATIVA OBRIGATÓRIA:
        1. **SITUAÇÃO INICIAL**: Contexto pessoal, quem você era antes
        2. **EVENTO GATILHO**: O que aconteceu que mudou tudo
        3. **DESENVOLVIMENTO**: Como você lidou com a situação
        4. **CLÍMAX**: O momento de virada ou revelação
        5. **TRANSFORMAÇÃO**: Como você mudou após a experiência
        
        LINGUAGEM STORYTELLING:
        - Use primeira pessoa: "Deixa eu contar o que aconteceu comigo..."
        - Tom íntimo e conversacional: "Vocês não vão acreditar no que passei..."
        - Emoções genuínas: "Eu estava completamente perdido..."
        - Detalhes específicos que tornam a história crível
        
        ELEMENTOS VISUAIS OBRIGATÓRIOS:
        Para cada momento da história, inclua:
        - **[TIMING: X-Ys]** momento exato
        - **[IMAGEM: descrição detalhada]** prompt para Leonardo AI
        - **[ANIMAÇÃO: movimento específico]** como animar a cena
        
        EXEMPLO DE FORMATAÇÃO:
        [TIMING: 0-5s] [ÍNTIMO] Deixa eu contar uma coisa que mudou minha vida...
        [IMAGEM: Pessoa jovem em quarto escuro, apenas luz do celular, expressão pensativa]
        [ANIMAÇÃO: Zoom lento no rosto, luz pulsando suavemente]
        
        RESPONDA APENAS EM JSON VÁLIDO:
        ```json
        {{
            "tipo_conteudo": "{['capitulos', 'historia_unica'][int(not create_chapters)]}",
            "titulo_geral": "Título da história completa",
            "total_capitulos": {3 if create_chapters else 1},
            
            "capitulos": [
                {{
                    "numero": 1,
                    "titulo_capitulo": "Título específico",
                    "hook": "Frase de abertura impactante",
                    "roteiro_completo": "História com marcações [TIMING], [IMAGEM] e [ANIMAÇÃO]",
                    "duracao_estimada": {85 if create_chapters else settings.get('duration', 90)},
                    "cliffhanger": "Final que deixa em suspense",
                    
                    "cenas_visuais": [
                        {{
                            "timing": "0-5s",
                            "descricao_cena": "Momento da história", 
                            "prompt_imagem": "Prompt detalhado: cenário, pessoas, iluminação, mood",
                            "animacao_leonardo": "Movimento específico da câmera/personagens",
                            "mood_visual": "Atmosfera emocional"
                        }}
                    ]
                }}
            ],
            
            "elementos_narrativos": {{
                "personagem_principal": "Quem conta a história",
                "cenario_principal": "Onde acontece",
                "conflito_central": "Problema enfrentado", 
                "transformacao": "Como a pessoa mudou",
                "licao_aprendida": "Mensagem principal"
            }},
            
            "hashtags": ["#storytelling", "#{categoria}", "#fyp", "#historia", "#viral"]
        }}
        ```
        
        IMPORTANTE: Crie uma história que soe REAL e HUMANA. As pessoas devem se identificar e pensar "isso poderia ter acontecido comigo". Use emoções autênticas e detalhes específicos.
        """

    def build_storyboard_prompt_historia_claude(self, theme: str, duration_target_sec: int = 60) -> str:
        """
        Prompt mestre p/ CLAUDE retornar APENAS um JSON válido no schema de storyboard histórico/científico.
        Narração pt-BR; prompts visuais/motion em inglês.
        """
        HISTORY_VISUAL_PACK_EN = (
            "ultra realistic or painterly realistic, renaissance/early-modern vibes, "
            "cinematic lighting, moody shadows, volumetric light, rich textures, "
            "dark teal/orange palette, highly detailed, vertical 9:16, no text, 8K resolution"
        )
        HISTORY_IMAGE_SUFFIX_EN = "vertical 9:16, no text, highly detailed, 8K resolution"
        MOTION_PRESET_HIGH_EN = "slow cinematic zoom in, subtle parallax, gentle camera drift, 9:16 vertical"
        MOTION_PRESET_MED_EN  = "gentle pan left/right, slow zoom out, subtle parallax, 9:16 vertical"
        
        return f"""
Return ONLY a single VALID JSON object (no markdown, no backticks).
Theme: "{theme}"
Format: vertical short (~{duration_target_sec}s), historical/scientific tone.

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
    "narration": "2–3 frases naturais em português do Brasil (sem SSML), TTS-friendly, com detalhes concretos.",
    "on_screen_text": "Opcional, até 6 palavras",
      "image_prompt": "English visual description. Include: {HISTORY_VISUAL_PACK_EN}. End with: {HISTORY_IMAGE_SUFFIX_EN}",
      "motion_prompt": "{MOTION_PRESET_HIGH_EN}",
      "intensity": "ALTA|MEDIA",
      "sfx": ["efeitos sutis"],
      "music_cue": "intro_suave"
    }}
  ],
  "thumbnail": {{
    "text": "Frase de capa",
    "image_prompt": "English prompt for cover. Include: {HISTORY_VISUAL_PACK_EN}"
  }},
  "hashtags": ["#historia","#shorts","#ciencia"]
}}

Rules:
- 8–10 scenes, 3–12s each; total ~{duration_target_sec}s (preferably 85–100s).
- Every 'image_prompt' must end with: "{HISTORY_IMAGE_SUFFIX_EN}".
- 'motion_prompt' in English. Use "{MOTION_PRESET_HIGH_EN}" for ALTA, "{MOTION_PRESET_MED_EN}" for MEDIA.
- Output MUST be JSON only.
""".strip()

    def criar_prompt_roteiro_historia(self, tema: str, duration_target_sec: int = 60) -> str:
        """
        Prompt para CLAUDE retornar APENAS JSON no schema storyboard histórico/científico.
        """
        HISTORY_VISUAL_PACK = (
            "ultra realistic or painterly realistic, renaissance/early-modern vibes, "
            "cinematic lighting, moody shadows, volumetric light, rich textures, "
            "dark teal/orange palette, highly detailed, vertical 9:16, no text, 8K resolution"
        )
        HISTORY_MOTION_HIGH = "slow cinematic zoom in, subtle parallax, gentle camera drift, 9:16 vertical"
        HISTORY_MOTION_MED  = "gentle pan left/right, slow zoom out, subtle parallax, 9:16 vertical"
        
        return f"""
Gere APENAS um JSON VÁLIDO (sem markdown, sem ```), com storyboard histórico/científico para Shorts/TikTok/Kwai (~{duration_target_sec}s).
Tema: "{tema}"

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
      "narration": "Frase curta, pt-BR.",
      "on_screen_text": "Opcional",
      "image_prompt": "Descrição objetiva + estilo. Inclua: {HISTORY_VISUAL_PACK}",
      "motion_prompt": "{HISTORY_MOTION_HIGH}",
      "intensity": "ALTA|MEDIA",
      "sfx": ["vento leve"],
      "music_cue": "intro_suave"
    }}
  ],
  "thumbnail": {{
    "text": "Frase de capa",
    "image_prompt": "Coerente com o tema. Inclua: {HISTORY_VISUAL_PACK}"
  }},
  "hashtags": ["#historia","#shorts","#ciencia"]
}}

REGRAS:
- 6–8 cenas; 3–10s cada; total ~{duration_target_sec}s.
- Em "image_prompt", terminar com: "vertical 9:16, no text, highly detailed, 8K resolution".
- Nada fora do JSON.
""".strip()

    # O método 'gerar_roteiro_hibrido' foi removido desta classe,
    # pois a lógica de orquestração é agora no AIContentOrchestrator.
    # Se ele for necessário em outro lugar, deve ser repensado ou movido.


# Teste para a classe HybridAI isoladamente (focando no Claude)
if __name__ == "__main__":
    print("🧪 TESTANDO CLAUDE AI ISOLADAMENTE COM HYBRIDAI")
    print("=" * 60)

    # Certifique-se que CLAUDE_API_KEY="SUA_CHAVE_AQUI" está no seu arquivo .env
    # A chave fornecida: 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

    claude_test_instance = HybridAI()

    test_settings_for_claude = {
        # Será usado como categoria para o prompt do Claude
        'message_categories': ['Tecnologia'],
        # Apenas para contexto, não usado no prompt do Claude aqui
        'custom_topics': ['Inteligência Artificial', 'Robótica']
    }

    print("\n--- Testando geração de roteiro com Claude ---")
    roteiro_claude_result = claude_test_instance.gerar_roteiro_claude(
        test_settings_for_claude)

    if roteiro_claude_result:
        print(f"✅ Claude Título: {roteiro_claude_result.get('titulo', 'N/A')}")
        print(
            f"   IA Usada: {roteiro_claude_result.get('ia_used', 'claude (padrão)')}")
        print(
            f"   Roteiro Completo (trecho): {roteiro_claude_result.get('roteiro_completo', '')[:100]}...")
    else:
        print("❌ Falha na geração com Claude.")
