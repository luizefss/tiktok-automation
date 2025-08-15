"""
Sistema de Revisão e Seleção de Roteiros para Produção
Permite avaliar e escolher o melhor roteiro entre múltiplas IAs
"""

import logging
import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ScriptComparison:
    """Estrutura para comparação de roteiros"""
    script_id: str
    ai_provider: str
    score: float
    title: str
    hook: str
    viral_score: float
    duration: int
    pros: List[str]
    cons: List[str]
    recommendation: str

class ScriptReviewSystem:
    """
    Sistema para revisar e comparar roteiros de múltiplas IAs
    """
    
    def __init__(self):
        self.reviews_dir = "/var/www/tiktok-automation/media/script_reviews"
        os.makedirs(self.reviews_dir, exist_ok=True)
        logger.info("✅ Script Review System inicializado")
    
    def analyze_scripts_for_review(self, battle_results: Dict[str, Any]) -> List[ScriptComparison]:
        """
        Analisa roteiros da batalha para facilitar a revisão manual
        """
        try:
            comparisons = []
            
            for ai_provider, result in battle_results.items():
                script_data = result.get('script_data', {})
                analysis = result.get('analysis', {})
                
                # Extrair informações principais
                comparison = ScriptComparison(
                    script_id=f"{ai_provider}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    ai_provider=ai_provider.upper(),
                    score=result.get('score', 0),
                    title=script_data.get('titulo', 'Sem título'),
                    hook=script_data.get('hook', 'Sem hook'),
                    viral_score=analysis.get('viral_score', 0),
                    duration=script_data.get('estimated_duration', 0),
                    pros=self._extract_pros(script_data, analysis),
                    cons=self._extract_cons(script_data, analysis),
                    recommendation=self._generate_recommendation(analysis)
                )
                
                comparisons.append(comparison)
            
            # Ordenar por score para facilitar comparação
            comparisons.sort(key=lambda x: x.score, reverse=True)
            
            logger.info(f"✅ {len(comparisons)} roteiros analisados para revisão")
            return comparisons
            
        except Exception as e:
            logger.error(f"Erro na análise de roteiros: {e}")
            return []
    
    def _extract_pros(self, script_data: Dict, analysis: Dict) -> List[str]:
        """Extrai pontos positivos do roteiro"""
        pros = []
        
        # Analisar hook
        hook_score = analysis.get('hook_score', 0)
        if hook_score > 0.8:
            pros.append("🎯 Hook muito impactante")
        elif hook_score > 0.6:
            pros.append("✅ Hook bem construído")
        
        # Analisar viral score
        viral_score = analysis.get('viral_score', 0)
        if viral_score > 85:
            pros.append("🔥 Alto potencial viral")
        elif viral_score > 70:
            pros.append("📈 Bom potencial viral")
        
        # Analisar CTA
        cta_score = analysis.get('cta_score', 0)
        if cta_score > 0.7:
            pros.append("💬 Call-to-action efetivo")
        
        # Analisar elementos virais
        viral_elements = script_data.get('viral_elements', {})
        if viral_elements.get('curiosity_gaps'):
            pros.append("🤔 Gera curiosidade")
        if viral_elements.get('pattern_interrupts'):
            pros.append("⚡ Quebra padrões de atenção")
        if viral_elements.get('social_proof'):
            pros.append("👥 Inclui prova social")
        
        # Analisar estrutura
        if script_data.get('structure'):
            pros.append("📝 Estrutura bem definida")
        
        # Se não encontrou pros específicos, adicionar algo genérico
        if not pros:
            pros.append("✅ Roteiro tecnicamente correto")
        
        return pros[:4]  # Máximo 4 pros
    
    def _extract_cons(self, script_data: Dict, analysis: Dict) -> List[str]:
        """Extrai pontos de melhoria do roteiro"""
        cons = []
        
        # Analisar hook
        hook_score = analysis.get('hook_score', 0)
        if hook_score < 0.5:
            cons.append("⚠️ Hook pode ser mais impactante")
        
        # Analisar viral score
        viral_score = analysis.get('viral_score', 0)
        if viral_score < 60:
            cons.append("📉 Potencial viral baixo")
        
        # Analisar duração
        duration = script_data.get('estimated_duration', 0)
        if duration > 70:
            cons.append("⏱️ Pode ser muito longo")
        elif duration < 30:
            cons.append("⏱️ Pode ser muito curto")
        
        # Analisar CTA
        cta_score = analysis.get('cta_score', 0)
        if cta_score < 0.4:
            cons.append("💬 CTA precisa ser mais forte")
        
        # Analisar tips de otimização
        optimization_tips = analysis.get('optimization_tips', [])
        if optimization_tips:
            cons.extend(optimization_tips[:2])  # Máximo 2 tips
        
        # Se não encontrou cons específicos
        if not cons:
            cons.append("✨ Poucos pontos de melhoria")
        
        return cons[:3]  # Máximo 3 cons
    
    def _generate_recommendation(self, analysis: Dict) -> str:
        """Gera recomendação baseada na análise"""
        viral_score = analysis.get('viral_score', 0)
        hook_score = analysis.get('hook_score', 0)
        
        if viral_score > 85 and hook_score > 0.8:
            return "🔥 RECOMENDADO - Excelente para publicação imediata"
        elif viral_score > 70 and hook_score > 0.6:
            return "👍 BOM - Recomendado com pequenos ajustes"
        elif viral_score > 60:
            return "⚠️ REGULAR - Considere melhorias antes da publicação"
        else:
            return "❌ REVISAR - Precisa de ajustes significativos"
    
    def save_review_session(self, theme: str, comparisons: List[ScriptComparison], battle_results: Dict) -> str:
        """Salva sessão de revisão para análise posterior"""
        try:
            session_id = f"review_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            review_data = {
                "session_id": session_id,
                "theme": theme,
                "timestamp": datetime.now().isoformat(),
                "comparisons": [
                    {
                        "script_id": comp.script_id,
                        "ai_provider": comp.ai_provider,
                        "score": comp.score,
                        "title": comp.title,
                        "hook": comp.hook,
                        "viral_score": comp.viral_score,
                        "duration": comp.duration,
                        "pros": comp.pros,
                        "cons": comp.cons,
                        "recommendation": comp.recommendation
                    }
                    for comp in comparisons
                ],
                "full_battle_results": battle_results
            }
            
            file_path = os.path.join(self.reviews_dir, f"{session_id}.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(review_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ Sessão de revisão salva: {session_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"Erro ao salvar sessão de revisão: {e}")
            return ""
    
    def get_script_by_choice(self, battle_results: Dict, chosen_ai: str) -> Optional[Dict]:
        """Retorna o roteiro da IA escolhida"""
        try:
            chosen_ai_lower = chosen_ai.lower()
            
            if chosen_ai_lower in battle_results:
                return battle_results[chosen_ai_lower].get('script_data')
            
            logger.warning(f"IA '{chosen_ai}' não encontrada nos resultados")
            return None
            
        except Exception as e:
            logger.error(f"Erro ao buscar roteiro escolhido: {e}")
            return None
    
    def generate_comparison_summary(self, comparisons: List[ScriptComparison]) -> Dict[str, Any]:
        """Gera resumo comparativo para facilitar decisão"""
        if not comparisons:
            return {}
        
        # Encontrar o melhor em cada categoria
        best_viral = max(comparisons, key=lambda x: x.viral_score)
        best_hook = max(comparisons, key=lambda x: x.score)  # Score geral inclui hook
        shortest = min(comparisons, key=lambda x: x.duration)
        longest = max(comparisons, key=lambda x: x.duration)
        
        summary = {
            "total_scripts": len(comparisons),
            "best_viral_score": {
                "ai": best_viral.ai_provider,
                "score": best_viral.viral_score
            },
            "best_overall": {
                "ai": best_hook.ai_provider,
                "score": best_hook.score
            },
            "duration_range": {
                "shortest": {"ai": shortest.ai_provider, "duration": shortest.duration},
                "longest": {"ai": longest.ai_provider, "duration": longest.duration}
            },
            "recommendations": [comp.recommendation for comp in comparisons],
            "quick_decision_tip": self._get_quick_decision_tip(comparisons)
        }
        
        return summary
    
    def _get_quick_decision_tip(self, comparisons: List[ScriptComparison]) -> str:
        """Dá uma dica rápida para decisão"""
        if not comparisons:
            return "Nenhum roteiro disponível"
        
        best = comparisons[0]  # Já ordenado por score
        
        if best.viral_score > 85:
            return f"💡 Dica: {best.ai_provider} tem o melhor equilíbrio geral (Score: {best.score})"
        elif len(comparisons) > 1:
            second = comparisons[1]
            return f"💡 Dica: Compare {best.ai_provider} (Score: {best.score}) vs {second.ai_provider} (Score: {second.score})"
        else:
            return f"💡 Dica: Único roteiro disponível - {best.ai_provider}"

# Instância global do sistema
script_review_system = ScriptReviewSystem()
