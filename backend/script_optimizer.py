# Script Optimizer - Otimiza roteiros para narração humanizada
import re
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class ScriptOptimizer:
    def __init__(self):
        self.emotion_patterns = {
            "dramatic": ["incrível", "impressionante", "chocante", "revelação", "segredo"],
            "mysterious": ["mistério", "oculto", "secreto", "enigma", "desconhecido"],
            "enthusiastic": ["fantástico", "incrível", "maravilhoso", "espetacular"],
            "suspenseful": ["cuidado", "atenção", "perigo", "surpresa", "inesperado"]
        }
        
    def optimize_for_speech(self, script_data: Dict[str, Any]) -> Dict[str, Any]:
        """Otimiza roteiro completo para narração humanizada"""
        
        try:
            # Extrair roteiro principal
            original_text = script_data.get('roteiro_completo', '')
            if not original_text:
                return script_data
            
            logger.info("Otimizando roteiro para narração humanizada...")
            
            # Aplicar otimizações sequenciais
            optimized_text = self._clean_formatting(original_text)
            optimized_text = self._add_natural_pauses(optimized_text)
            optimized_text = self._improve_pronunciation(optimized_text)
            optimized_text = self._add_emotion_markers(optimized_text)
            optimized_text = self._fix_numbers_and_symbols(optimized_text)
            optimized_text = self._add_breath_marks(optimized_text)
            
            # Atualizar script_data
            script_data['roteiro_completo'] = optimized_text
            script_data['speech_optimized'] = True
            
            logger.info("Roteiro otimizado para narração humanizada")
            return script_data
            
        except Exception as e:
            logger.error(f"Erro ao otimizar roteiro: {e}")
            return script_data

    def _clean_formatting(self, text: str) -> str:
        """Remove formatação que atrapalha a leitura natural"""
        
        # Remover marcações de tempo antigas
        text = re.sub(r'\[VOZ:.*?\]', '', text)
        text = re.sub(r'\[PAUSA:.*?\]', '', text)
        text = re.sub(r'\[Ênfase:.*?\]', '', text)
        text = re.sub(r'\[Tom:.*?\]', '', text)
        
        # Remover bullets e símbolos desnecessários
        text = text.replace('→', '').replace('■', '').replace('●', '')
        text = text.replace('▶', '').replace('✓', '').replace('📌', '')
        
        # Limpar espaços múltiplos
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()

    def _add_natural_pauses(self, text: str) -> str:
        """Adiciona pausas naturais para melhor respiração"""
        
        # Pausas após pontos
        text = re.sub(r'\.(\s*)([A-ZÁÉÍÓÚÇÂÊÔÀÈ])', r'. <break time="0.8s"/>\1\2', text)
        
        # Pausas após vírgulas
        text = re.sub(r',(\s*)', r', <break time="0.4s"/>\1', text)
        
        # Pausas após exclamações
        text = re.sub(r'!(\s*)([A-ZÁÉÍÓÚÇÂÊÔÀÈ])', r'! <break time="0.6s"/>\1\2', text)
        
        # Pausas após interrogações
        text = re.sub(r'\?(\s*)([A-ZÁÉÍÓÚÇÂÊÔÀÈ])', r'? <break time="0.7s"/>\1\2', text)
        
        # Pausas dramáticas para reticências
        text = re.sub(r'\.\.\.', '... <break time="1.2s"/>', text)
        
        return text

    def _improve_pronunciation(self, text: str) -> str:
        """Melhora pronúncia de palavras problemáticas"""
        
        # Dicionário de substituições para melhor pronúncia
        pronunciation_fixes = {
            # Números
            'TikTok': 'Tik Tok',
            'YouTube': 'You Tube',
            'WhatsApp': 'Whats App',
            'Instagram': 'Insta gram',
            
            # Palavras técnicas
            'app': 'aplicativo',
            'apps': 'aplicativos',
            'site': 'site',
            'website': 'web site',
            'online': 'on-line',
            
            # Abreviações
            'etc': 'et cetera',
            'ex': 'exemplo',
            'Dr.': 'Doutor',
            'Sr.': 'Senhor',
            'Sra.': 'Senhora',
            
            # Melhor fluidez
            'né?': ', não é?',
            'pq': 'porque',
            'vc': 'você',
            'tb': 'também'
        }
        
        for original, replacement in pronunciation_fixes.items():
            text = re.sub(r'\b' + re.escape(original) + r'\b', replacement, text, flags=re.IGNORECASE)
            
        return text

    def _add_emotion_markers(self, text: str) -> str:
        """Adiciona marcadores de emoção baseado no conteúdo"""
        
        # Palavras que merecem ênfase
        emphasis_words = [
            'incrível', 'fantástico', 'impressionante', 'espetacular',
            'revolucionário', 'exclusivo', 'segredo', 'revelação',
            'nunca', 'jamais', 'sempre', 'todos', 'ninguém'
        ]
        
        for word in emphasis_words:
            pattern = r'\b(' + re.escape(word) + r')\b'
            replacement = r'<emphasis level="strong">\1</emphasis>'
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        # Números importantes merecem ênfase
        text = re.sub(r'\b(\d+%)\b', r'<emphasis level="moderate">\1</emphasis>', text)
        text = re.sub(r'\b(\d+\s*mil)\b', r'<emphasis level="moderate">\1</emphasis>', text, flags=re.IGNORECASE)
        text = re.sub(r'\b(\d+\s*milhão|milhões)\b', r'<emphasis level="strong">\1</emphasis>', text, flags=re.IGNORECASE)
        
        return text

    def _fix_numbers_and_symbols(self, text: str) -> str:
        """Converte números e símbolos para forma falada"""
        
        # Percentuais
        text = re.sub(r'(\d+)%', r'\1 por cento', text)
        
        # Valores monetários
        text = re.sub(r'R\$\s*(\d+)', r'\1 reais', text)
        text = re.sub(r'\$(\d+)', r'\1 dólares', text)
        
        # Números ordinais comuns
        ordinals = {
            '1º': 'primeiro', '2º': 'segundo', '3º': 'terceiro',
            '4º': 'quarto', '5º': 'quinto', '1ª': 'primeira',
            '2ª': 'segunda', '3ª': 'terceira', '4ª': 'quarta', '5ª': 'quinta'
        }
        
        for symbol, word in ordinals.items():
            text = text.replace(symbol, word)
        
        # Símbolos especiais
        text = text.replace('&', ' e ')
        text = text.replace('+', ' mais ')
        text = text.replace('=', ' igual a ')
        text = text.replace('x', ' vezes ')
        
        return text

    def _add_breath_marks(self, text: str) -> str:
        """Adiciona marcas de respiração em textos longos"""
        
        # Dividir em sentenças
        sentences = re.split(r'[.!?]+', text)
        
        processed_sentences = []
        for i, sentence in enumerate(sentences):
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # Adicionar respiração a cada 3-4 sentenças
            if i > 0 and i % 3 == 0:
                sentence = '<break time="1s"/>' + sentence
            
            # Para sentenças muito longas (mais de 20 palavras)
            words = sentence.split()
            if len(words) > 20:
                # Inserir pausa no meio
                mid_point = len(words) // 2
                words.insert(mid_point, '<break time="0.6s"/>')
                sentence = ' '.join(words)
            
            processed_sentences.append(sentence)
        
        return '. '.join(processed_sentences)

    def analyze_emotion_from_content(self, text: str) -> str:
        """Analisa o texto e sugere a emoção mais adequada"""
        
        text_lower = text.lower()
        emotion_scores = {}
        
        for emotion, patterns in self.emotion_patterns.items():
            score = 0
            for pattern in patterns:
                score += len(re.findall(r'\b' + pattern + r'\b', text_lower))
            emotion_scores[emotion] = score
        
        # Análise adicional por contexto
        if '?' in text and 'você sabia' in text_lower:
            emotion_scores['mysterious'] = emotion_scores.get('mysterious', 0) + 2
            
        if re.search(r'[!]{2,}', text):
            emotion_scores['enthusiastic'] = emotion_scores.get('enthusiastic', 0) + 3
            
        if '...' in text:
            emotion_scores['suspenseful'] = emotion_scores.get('suspenseful', 0) + 2
        
        # Retornar emoção com maior pontuação
        if emotion_scores:
            best_emotion = max(emotion_scores.items(), key=lambda x: x[1])
            if best_emotion[1] > 0:
                return best_emotion[0]
        
        return "neutral"

    def get_optimized_preview_text(self, full_text: str, max_sentences: int = 2) -> str:
        """Extrai e otimiza texto para preview"""
        
        # Pegar primeiras sentenças
        sentences = re.split(r'[.!?]+', full_text)
        preview_sentences = sentences[:max_sentences]
        preview_text = '. '.join(preview_sentences).strip()
        
        # Se não termina com pontuação, adicionar
        if preview_text and not preview_text[-1] in '.!?':
            preview_text += '.'
        
        # Aplicar otimizações básicas
        preview_text = self._clean_formatting(preview_text)
        preview_text = self._improve_pronunciation(preview_text)
        preview_text = self._fix_numbers_and_symbols(preview_text)
        
        return preview_text