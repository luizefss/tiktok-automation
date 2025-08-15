"""
Configurações e estruturas para diferentes tipos de histórias
"""

from typing import Dict, List, Any
from enum import Enum


class StoryType(Enum):
    HISTORICA_CIENTIFICA = "historica_cientifica"
    INFANTIL_FANTASIA = "infantil_fantasia"
    MISTERIO_SUSPENSE = "misterio_suspense"
    MOTIVACIONAL = "motivacional"
    TECNOLOGIA = "tecnologia"
    CURIOSIDADE = "curiosidade"


class StoryStructures:
    """Estruturas base para cada tipo de história"""
    
    STRUCTURES = {
        "historica_cientifica": {
            "name": "História Histórica / Científica",
            "description": "Invenções, personagens históricos, descobertas",
            "elements": [
                "gancho_impactante",
                "contexto_inicial",
                "desenvolvimento_fatos",
                "climax_revelador", 
                "conclusao_curiosidade",
                "call_to_action"
            ],
            "example_prompts": [
                "A invenção que mudou o mundo mas você nunca ouviu falar",
                "O cientista que foi chamado de louco mas estava certo",
                "A descoberta que aconteceu por acaso e revolucionou tudo"
            ],
            "visual_style": "historia",
            "duration_range": "60-90s",
            "tone": "educativo e envolvente"
        },
        
        "infantil_fantasia": {
            "name": "História Infantil / Fantasia", 
            "description": "Fábulas, contos curtos, aventuras com lição de moral",
            "elements": [
                "introducao_ludica",
                "personagem_principal",
                "conflito_desafio",
                "resolucao_moral",
                "encerramento_divertido",
                "incentivo_imaginacao"
            ],
            "example_prompts": [
                "A aventura do gatinho que queria voar",
                "O dragão que tinha medo de fogo",
                "A princesa que salvava os príncipes"
            ],
            "visual_style": "fantasia",
            "duration_range": "45-60s",
            "tone": "lúdico e educativo"
        },
        
        "misterio_suspense": {
            "name": "História de Mistério / Suspense",
            "description": "Casos reais intrigantes, lendas urbanas, fenômenos inexplicáveis",
            "elements": [
                "gancho_misterioso",
                "exposicao_pistas",
                "climax_revelacao",
                "encerramento_instigante",
                "call_to_action"
            ],
            "example_prompts": [
                "O caso que a polícia nunca conseguiu resolver",
                "A lenda urbana que pode ser real",
                "O fenômeno que a ciência não explica"
            ],
            "visual_style": "misterio",
            "duration_range": "45-75s",
            "tone": "intrigante e suspenseful"
        },
        
        "motivacional": {
            "name": "História Motivacional",
            "description": "Superação, conquistas, transformação pessoal",
            "elements": [
                "situacao_inicial",
                "desafio_obstáculo",
                "jornada_transformacao",
                "conquista_vitoria",
                "licao_inspiracao",
                "call_to_action"
            ],
            "example_prompts": [
                "De zero a herói em 30 dias",
                "Como superar o impossível",
                "A transformação que ninguém acreditava"
            ],
            "visual_style": "motivacional",
            "duration_range": "60-90s",
            "tone": "inspirador e energético"
        },
        
        "tecnologia": {
            "name": "História de Tecnologia",
            "description": "Inovações, IA, futuro, descobertas tech",
            "elements": [
                "gancho_tecnologico",
                "contexto_inovacao",
                "impacto_transformacao",
                "futuro_possibilidades",
                "conclusao_reflexao",
                "call_to_action"
            ],
            "example_prompts": [
                "A IA que está mudando tudo",
                "A tecnologia que vai revolucionar sua vida",
                "O futuro chegou e você não percebeu"
            ],
            "visual_style": "tecnologia",
            "duration_range": "45-70s",
            "tone": "inovador e futurista"
        },
        
        "curiosidade": {
            "name": "História de Curiosidade",
            "description": "Fatos interessantes, você sabia que, descobertas surpreendentes",
            "elements": [
                "gancho_curiosidade",
                "fato_surpreendente",
                "explicacao_contexto",
                "conexao_vida_real",
                "conclusao_impactante",
                "call_to_action"
            ],
            "example_prompts": [
                "Você sabia que isso existe?",
                "O fato mais bizarro que você vai ouvir hoje",
                "A verdade por trás do que você sempre acreditou"
            ],
            "visual_style": "curiosidade",
            "duration_range": "30-60s",
            "tone": "envolvente e surpreendente"
        }
    }
    
    @classmethod
    def get_structure(cls, story_type: str) -> Dict[str, Any]:
        """Retorna a estrutura para um tipo de história"""
        return cls.STRUCTURES.get(story_type, cls.STRUCTURES["curiosidade"])
    
    @classmethod
    def get_all_types(cls) -> List[Dict[str, Any]]:
        """Retorna todos os tipos de história disponíveis"""
        return [
            {
                "id": key,
                "name": value["name"],
                "description": value["description"],
                "visual_style": value["visual_style"],
                "duration_range": value["duration_range"],
                "tone": value["tone"]
            }
            for key, value in cls.STRUCTURES.items()
        ]
    
    @classmethod
    def get_structure_prompt(cls, story_type: str) -> str:
        """Gera um prompt estruturado para o tipo de história"""
        structure = cls.get_structure(story_type)
        
        elements_text = "\n".join([f"- {element.replace('_', ' ').title()}" for element in structure["elements"]])
        
        return f"""
TIPO DE HISTÓRIA: {structure["name"]}
DESCRIÇÃO: {structure["description"]}
TOM: {structure["tone"]}
DURAÇÃO: {structure["duration_range"]}

ESTRUTURA OBRIGATÓRIA:
{elements_text}

ESTILO VISUAL: {structure["visual_style"]}
        """.strip()


class StoryTemplates:
    """Templates específicos para cada estrutura"""
    
    TEMPLATES = {
        "historica_cientifica": {
            "gancho_impactante": "Uma descoberta/invenção revolucionária que mudou tudo",
            "contexto_inicial": "Época, local, personagem principal da história",
            "desenvolvimento_fatos": "Sequência de eventos e descobertas importantes",
            "climax_revelador": "O momento da grande descoberta ou revelação",
            "conclusao_curiosidade": "Impacto atual e curiosidade final",
            "call_to_action": "Engajamento sobre ciência/história"
        },
        
        "infantil_fantasia": {
            "introducao_ludica": "Era uma vez... de forma divertida e cativante",
            "personagem_principal": "Apresentação do herói/protagonista carismático", 
            "conflito_desafio": "O problema ou aventura que precisa ser resolvida",
            "resolucao_moral": "Como o problema foi resolvido com uma lição",
            "encerramento_divertido": "Final feliz e memorable",
            "incentivo_imaginacao": "Estimular criatividade das crianças"
        },
        
        "misterio_suspense": {
            "gancho_misterioso": "Um mistério intrigante que desperta curiosidade",
            "exposicao_pistas": "Fatos, evidências e detalhes misteriosos",
            "climax_revelacao": "A revelação chocante ou reviravolta",
            "encerramento_instigante": "Final que deixa o público pensando",
            "call_to_action": "Engajamento sobre o mistério"
        }
    }
    
    @classmethod
    def get_template(cls, story_type: str) -> Dict[str, str]:
        """Retorna o template para um tipo de história"""
        return cls.TEMPLATES.get(story_type, {})


# Configurações de integração com o sistema existente
STORY_TO_VISUAL_STYLE_MAP = {
    "historica_cientifica": "historia",
    "infantil_fantasia": "fantasia", 
    "misterio_suspense": "misterio",
    "motivacional": "motivacional",
    "tecnologia": "tecnologia",
    "curiosidade": "curiosidade"
}

STORY_TO_THEME_MAP = {
    "historica_cientifica": ["história", "ciência", "descoberta", "invenção"],
    "infantil_fantasia": ["fantasia", "aventura", "fábula", "moral"],
    "misterio_suspense": ["mistério", "suspense", "enigma", "inexplicável"],
    "motivacional": ["motivação", "superação", "sucesso", "transformação"],
    "tecnologia": ["tecnologia", "inovação", "futuro", "IA"],
    "curiosidade": ["curiosidade", "fato", "descoberta", "você sabia"]
}
