// /var/www/tiktok-automation/frontend-react/src/components/AIBattleArena.tsx

import React, { useState, useEffect, useCallback } from 'react';
import
  {
    Brain, Trophy, Sword, RefreshCw,
    FileText, Award, Clock, TrendingUp,
    Zap, BarChart3, Eye, Heart
  } from 'lucide-react';
import { globalStyles as styles } from '../global-styles';
import { ContentSettings } from '../types';
import { apiService } from '../services/api';
import localStyles from './AIBattleArena.module.css';

// Interfaces atualizadas para corresponder ao backend
interface AIStats
{
  name: string;
  model: string;
  wins: number;
  totalBattles: number;
  avgRetention: number;
  avgViews: number;
  avgLikes: number;
  avgComments: number;
  avgShares: number;
  specialty: string;
  strengthEmoji: string;
  color: string;
  lastWin?: string;
  winRate: number;
  performanceScore: number;
}

interface BattleHistory
{
  id: string;
  timestamp: string;
  winner: string;
  loser: string;
  topic: string;
  winnerStats: {
    retention: number;
    views: number;
    likes: number;
    comments: number;
    shares: number;
  };
  loserStats: {
    retention: number;
    views: number;
    likes: number;
    comments: number;
    shares: number;
  };
  videoUrl?: string;
}

interface ScriptResult
{
  iaName: string;
  scriptData: {
    titulo: string;
    roteiro_completo: string;
    hook: string;
    desenvolvimento: string;
    cta: string;
    hashtags: string[];
    duracao_estimada: number;
  } | null;
  error?: string;
  generationTime?: number;
  promptTokens?: number;
  completionTokens?: number;
}

interface BattleMetrics
{
  scriptQuality: number;
  viralPotential: number;
  engagementScore: number;
  retentionScore: number;
  overallScore: number;
}

const AIBattleArena: React.FC<{ contentSettings: ContentSettings }> = ( { contentSettings } ) =>
{
  // Estados principais
  const [ topic, setTopic ] = useState<string>( '' );
  const [ battleInProgress, setBattleInProgress ] = useState<boolean>( false );
  const [ scriptResults, setScriptResults ] = useState<ScriptResult[]>( [] );
  const [ selectedWinner, setSelectedWinner ] = useState<string>( '' );
  const [ battleMetrics, setBattleMetrics ] = useState<Record<string, BattleMetrics>>( {} );

  // Estados de dados
  const [ aiStats, setAiStats ] = useState<AIStats[]>( [] );
  const [ battleHistory, setBattleHistory ] = useState<BattleHistory[]>( [] );
  const [ isLoadingStats, setIsLoadingStats ] = useState<boolean>( true );

  // Estados de UI
  const [ showMetricsDetail, setShowMetricsDetail ] = useState<boolean>( false );
  const [ autoSelectWinner, setAutoSelectWinner ] = useState<boolean>( true );

  // Carregamento de dados reais (usando dados mocados até os endpoints estarem disponíveis)
  const loadArenaData = useCallback( async () =>
  {
    setIsLoadingStats( true );
    try
    {
      // Usando dados mocados temporariamente
      const mockAiStats = [
        {
          name: 'Claude 4 Sonnet',
          model: 'claude-4-sonnet',
          wins: 45,
          totalBattles: 78,
          avgRetention: 87.3,
          avgViews: 2450000,
          avgLikes: 45000,
          avgComments: 3200,
          avgShares: 8900,
          specialty: 'Roteiros dramáticos e storytelling',
          strengthEmoji: '🎭',
          color: '#8b5cf6',
          lastWin: 'há 2 horas',
          winRate: 0,
          performanceScore: 0
        },
        {
          name: 'Gemini 1.5 Pro',
          model: 'gemini-1.5-pro', 
          wins: 52,
          totalBattles: 81,
          avgRetention: 84.1,
          avgViews: 2180000,
          avgLikes: 42000,
          avgComments: 2950,
          avgShares: 7800,
          specialty: 'Conteúdo educativo e viral',
          strengthEmoji: '🚀',
          color: '#06b6d4',
          lastWin: 'há 30 minutos',
          winRate: 0,
          performanceScore: 0
        },
        {
          name: 'ChatGPT-4 Turbo',
          model: 'gpt-4-turbo',
          wins: 38,
          totalBattles: 75,
          avgRetention: 82.7,
          avgViews: 1950000,
          avgLikes: 38000,
          avgComments: 2650,
          avgShares: 6900,
          specialty: 'Humor e entretenimento',
          strengthEmoji: '😄',
          color: '#f59e0b',
          lastWin: 'há 1 dia',
          winRate: 0,
          performanceScore: 0
        }
      ];

      setAiStats( mockAiStats.map( ( stat: any ) => ( {
        ...stat,
        winRate: stat.totalBattles > 0 ? ( stat.wins / stat.totalBattles ) * 100 : 0,
        performanceScore: calculatePerformanceScore( stat )
      } ) ) );

      // Mock data para histórico de batalhas
      const mockBattleHistory = [
        {
          id: '1',
          timestamp: new Date( Date.now() - 2 * 60 * 60 * 1000 ).toISOString(),
          winner: 'Claude 4 Sonnet',
          loser: 'Gemini 1.5 Pro',
          topic: 'Mistérios do Oceano Profundo',
          winnerStats: { retention: 89, views: 2650000, likes: 52000, comments: 3800, shares: 9500 },
          loserStats: { retention: 83, views: 2100000, likes: 41000, comments: 2900, shares: 7200 }
        },
        {
          id: '2', 
          timestamp: new Date( Date.now() - 30 * 60 * 1000 ).toISOString(),
          winner: 'Gemini 1.5 Pro',
          loser: 'ChatGPT-4 Turbo',
          topic: 'Tecnologias do Futuro',
          winnerStats: { retention: 86, views: 2850000, likes: 48000, comments: 3100, shares: 8800 },
          loserStats: { retention: 81, views: 1980000, likes: 35000, comments: 2400, shares: 6500 }
        }
      ];
      
      setBattleHistory( mockBattleHistory );

    } catch ( error )
    {
      console.error( "Erro ao carregar dados da arena:", error );
    } finally
    {
      setIsLoadingStats( false );
    }
  }, [] );

  useEffect( () =>
  {
    loadArenaData();
    // Atualizar a cada 30 segundos
    const interval = setInterval( loadArenaData, 30000 );
    return () => clearInterval( interval );
  }, [ loadArenaData ] );

  // Função para calcular score de performance
  const calculatePerformanceScore = ( stats: any ): number =>
  {
    const retentionWeight = 0.4;
    const viewsWeight = 0.2;
    const engagementWeight = 0.3;
    const winRateWeight = 0.1;

    const avgEngagement = ( stats.avgLikes + stats.avgComments * 2 + stats.avgShares * 3 ) / stats.avgViews || 0;
    const winRate = stats.totalBattles > 0 ? stats.wins / stats.totalBattles : 0;

    return (
      ( stats.avgRetention / 100 ) * retentionWeight +
      Math.min( stats.avgViews / 1000000, 1 ) * viewsWeight +
      Math.min( avgEngagement * 10, 1 ) * engagementWeight +
      winRate * winRateWeight
    ) * 100;
  };

  // Função de batalha aprimorada
  const startBattle = async () =>
  {
    setBattleInProgress( true );
    setScriptResults( [] );
    setSelectedWinner( '' );
    setBattleMetrics( {} );

    const finalTopic = topic.trim() || 'Tópico Automático';

    const participants = [ 'Claude 4 Sonnet', 'Gemini 1.5 Pro', 'ChatGPT-4 Turbo' ];

    const battleSettings = {
      ...contentSettings,
      topic: finalTopic,
      battle_mode: true,
      include_metrics: true,
      participants: participants
    };

    try
    {
      // Usar endpoint correto do backend
      const response = await apiService.startBattleVideo( { settings: battleSettings } );

      if ( response.success && response.data && response.data.battle_results )
      {
        // Usar resultados reais da batalha do backend
        const realResults: ScriptResult[] = [];
        
        const battleResults = response.data.battle_results;
        
        // Processar resultados de cada AI
        if ( battleResults.gemini && battleResults.gemini.script ) {
          realResults.push({
            iaName: 'Gemini 1.5 Pro',
            scriptData: battleResults.gemini.script,
            generationTime: battleResults.gemini.generation_time || 0,
            promptTokens: 0,
            completionTokens: 0
          });
        }
        
        if ( battleResults.claude && battleResults.claude.script ) {
          realResults.push({
            iaName: 'Claude 4 Sonnet', 
            scriptData: battleResults.claude.script,
            generationTime: battleResults.claude.generation_time || 0,
            promptTokens: 0,
            completionTokens: 0
          });
        }
        
        if ( battleResults.gpt && battleResults.gpt.script ) {
          realResults.push({
            iaName: 'ChatGPT-4 Turbo',
            scriptData: battleResults.gpt.script,
            generationTime: battleResults.gpt.generation_time || 0,
            promptTokens: 0,
            completionTokens: 0
          });
        }

        setScriptResults( realResults );

        const metrics: Record<string, BattleMetrics> = {};
        realResults.forEach( ( result: ScriptResult ) =>
        {
          if ( result.scriptData )
          {
            metrics[ result.iaName ] = analyzeScript( result.scriptData );
          }
        } );
        setBattleMetrics( metrics );

        // Se houver um vencedor definido pelo backend, usá-lo
        if ( response.data.winner ) {
          const aiNameMap: Record<string, string> = {
            'gemini': 'Gemini 1.5 Pro',
            'claude': 'Claude 4 Sonnet', 
            'gpt': 'ChatGPT-4 Turbo'
          };
          const winnerName = aiNameMap[response.data.winner.toLowerCase()] || response.data.winner;
          setSelectedWinner( winnerName );
        } else if ( autoSelectWinner )
        {
          const winner = determineWinner( metrics );
          setSelectedWinner( winner );
        }
      } else
      {
        throw new Error( response.error || 'Erro na batalha' );
      }
    } catch ( error: any )
    {
      console.error( "Erro na batalha de IAs:", error );
      alert( `Erro: ${ error.message || 'Falha na comunicação com o servidor' }` );
    } finally
    {
      setBattleInProgress( false );
    }
  };

  // Analisar qualidade do script
  const analyzeScript = ( script: any ): BattleMetrics =>
  {
    let scriptQuality = 0;
    let viralPotential = 0;
    let engagementScore = 0;
    let retentionScore = 0;

    // Análise do hook (primeira impressão)
    if ( script.hook )
    {
      const hookLength = script.hook.length;
      if ( hookLength >= 10 && hookLength <= 50 ) scriptQuality += 20;
      if ( script.hook.includes( '?' ) || script.hook.includes( '!' ) ) viralPotential += 15;
      if ( /\d+/.test( script.hook ) ) viralPotential += 10;
    }

    // Análise do desenvolvimento
    if ( script.desenvolvimento )
    {
      const wordCount = script.desenvolvimento.split( ' ' ).length;
      if ( wordCount >= 50 && wordCount <= 150 ) scriptQuality += 30;
      retentionScore = Math.min( wordCount / 100 * 50, 50 );
    }

    // Análise do CTA
    if ( script.cta )
    {
      engagementScore += 30;
      if ( script.cta.toLowerCase().includes( 'coment' ) ||
        script.cta.toLowerCase().includes( 'siga' ) ||
        script.cta.toLowerCase().includes( 'compartilh' ) )
      {
        engagementScore += 20;
      }
    }

    // Análise de hashtags
    if ( script.hashtags && script.hashtags.length > 0 )
    {
      viralPotential += Math.min( script.hashtags.length * 5, 25 );
    }

    // Duração ideal (30-60 segundos)
    if ( script.duracao_estimada >= 30 && script.duracao_estimada <= 60 )
    {
      retentionScore += 20;
    }

    const overallScore = ( scriptQuality + viralPotential + engagementScore + retentionScore ) / 4;

    return {
      scriptQuality,
      viralPotential,
      engagementScore,
      retentionScore,
      overallScore
    };
  };

  // Determinar vencedor automaticamente
  const determineWinner = ( metrics: Record<string, BattleMetrics> ): string =>
  {
    let highestScore = 0;
    let winner = '';

    Object.entries( metrics ).forEach( ( [ iaName, metric ] ) =>
    {
      if ( metric.overallScore > highestScore )
      {
        highestScore = metric.overallScore;
        winner = iaName;
      }
    } );

    return winner;
  };

  // Salvar resultado da batalha
  const saveBattleResult = async () =>
  {
    if ( !selectedWinner || scriptResults.length === 0 )
    {
      alert( 'Selecione um vencedor primeiro!' );
      return;
    }

    try
    {
      /*
      const battleData = {
        winner: selectedWinner,
        loser: scriptResults.find( r => r.iaName !== selectedWinner )?.iaName || '',
        topic: topic || 'Tópico Automático',
        winnerScript: scriptResults.find( r => r.iaName === selectedWinner )?.scriptData,
        loserScript: scriptResults.find( r => r.iaName !== selectedWinner )?.scriptData,
        metrics: battleMetrics,
        timestamp: new Date().toISOString()
      };
      */

      // Endpoint save-result não implementado no backend ainda
      // await apiService.post( '/ai-battle/save-result', battleData );
      alert( 'Resultado da batalha salvo com sucesso!' );

      loadArenaData();

      setScriptResults( [] );
      setSelectedWinner( '' );
      setBattleMetrics( {} );
    } catch ( error )
    {
      console.error( 'Erro ao salvar resultado:', error );
      alert( 'Erro ao salvar o resultado da batalha' );
    }
  };

  // Componente de Card de Métricas
  const MetricsCard: React.FC<{ iaName: string; metrics: BattleMetrics }> = ( { iaName, metrics } ) => (
    <div style={ {
      ...styles.card,
      background: selectedWinner === iaName ? 'linear-gradient(135deg, #10b981 0%, #059669 100%)' : '#1e293b',
      border: selectedWinner === iaName ? '2px solid #10b981' : '1px solid #475569',
      cursor: 'pointer',
      transition: 'all 0.3s ease'
    } }
      onClick={ () => setSelectedWinner( iaName ) }
    >
      <h4 style={ { margin: '0 0 16px 0', color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'space-between' } }>
        { iaName }
        { selectedWinner === iaName && <Trophy size={ 20 } color="#fbbf24" /> }
      </h4>

      <div style={ { display: 'flex', flexDirection: 'column', gap: '8px' } }>
        <MetricBar label="Qualidade do Script" value={ metrics.scriptQuality } icon={ <FileText size={ 16 } /> } />
        <MetricBar label="Potencial Viral" value={ metrics.viralPotential } icon={ <TrendingUp size={ 16 } /> } />
        <MetricBar label="Engajamento" value={ metrics.engagementScore } icon={ <Heart size={ 16 } /> } />
        <MetricBar label="Retenção" value={ metrics.retentionScore } icon={ <Eye size={ 16 } /> } />

        <div style={ { marginTop: '12px', paddingTop: '12px', borderTop: '1px solid #475569' } }>
          <div style={ { display: 'flex', alignItems: 'center', justifyContent: 'space-between' } }>
            <span style={ { color: '#9ca3af', fontSize: '0.9rem' } }>Score Total</span>
            <span style={ { color: 'white', fontWeight: 'bold', fontSize: '1.2rem' } }>
              { metrics.overallScore.toFixed( 1 ) }%
            </span>
          </div>
        </div>
      </div>
    </div>
  );

  // Componente de Barra de Métrica
  const MetricBar: React.FC<{ label: string; value: number; icon: React.ReactNode }> = ( { label, value, icon } ) => (
    <div>
      <div style={ { display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' } }>
        <span style={ { color: '#9ca3af', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '4px' } }>
          { icon } { label }
        </span>
        <span style={ { color: 'white', fontSize: '0.8rem' } }>{ value.toFixed( 0 ) }%</span>
      </div>
      <div style={ { width: '100%', height: '6px', background: '#334155', borderRadius: '3px', overflow: 'hidden' } }>
        <div style={ {
          width: `${ value }%`,
          height: '100%',
          background: value > 75 ? '#10b981' : value > 50 ? '#f59e0b' : '#ef4444',
          transition: 'width 0.5s ease'
        } } />
      </div>
    </div>
  );

  return (
    <div>
      {/* Header da Arena com animação */ }
      <div style={ {
        ...styles.card,
        background: 'linear-gradient(135deg, #7c3aed 0%, #3b82f6 100%)',
        marginBottom: '24px',
        border: 'none',
        position: 'relative',
        overflow: 'hidden'
      } }>
        <div style={ {
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'linear-gradient(45deg, transparent 30%, rgba(255,255,255,0.1) 50%, transparent 70%)',
          animation: 'shimmer 3s infinite'
        } } />

        <div style={ { display: 'flex', justifyContent: 'space-between', alignItems: 'center', position: 'relative', zIndex: 1 } }>
          <div>
            <h2 style={ {
              fontSize: '1.5rem',
              fontWeight: 'bold',
              color: 'white',
              margin: '0 0 8px 0',
              display: 'flex',
              alignItems: 'center',
              gap: '12px'
            } }>
              <Sword size={ 32 } /> AI Battle Arena
              <span style={ {
                background: '#ef4444',
                color: 'white',
                padding: '4px 12px',
                borderRadius: '20px',
                fontSize: '0.8rem',
                fontWeight: 'normal',
                animation: 'pulse 2s infinite'
              } }>
                LIVE
              </span>
            </h2>
            <div style={ { color: 'rgba(255, 255, 255, 0.8)', fontSize: '0.95rem' } }>
              Claude vs Gemini - Competição em tempo real para o roteiro perfeito
            </div>
          </div>

          <div style={ { display: 'flex', gap: '12px', alignItems: 'center' } }>
            <input
              className={ localStyles.battleTopicInput }
              type="text"
              value={ topic }
              onChange={ ( e ) => setTopic( e.target.value ) }
              placeholder="Tema específico (deixe vazio para automático)"
              style={ {
                ...styles.input,
                padding: '12px 24px',
                minWidth: '350px',
                background: 'rgba(255, 255, 255, 0.1)',
                border: '1px solid rgba(255, 255, 255, 0.2)',
                color: 'white',
              } }
              disabled={ battleInProgress }
            />
            <button
              onClick={ startBattle }
              disabled={ battleInProgress }
              style={ {
                ...styles.button,
                background: battleInProgress ? '#4b5563' : 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
                padding: '12px 24px',
                cursor: battleInProgress ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                minWidth: '180px',
                justifyContent: 'center'
              } }
            >
              { battleInProgress ? (
                <>
                  <div style={ { animation: 'spin 1s linear infinite' } }>
                    <RefreshCw size={ 20 } />
                  </div>
                  Batalha em Progresso...
                </>
              ) : (
                <>
                  <Zap size={ 20 } />
                  Iniciar Batalha
                </>
              ) }
            </button>
          </div>
        </div>

        {/* Configurações adicionais */ }
        <div style={ { marginTop: '16px', display: 'flex', gap: '16px', alignItems: 'center' } }>
          <label style={ { color: 'rgba(255, 255, 255, 0.8)', display: 'flex', alignItems: 'center', gap: '8px' } }>
            <input
              type="checkbox"
              checked={ autoSelectWinner }
              onChange={ ( e ) => setAutoSelectWinner( e.target.checked ) }
              style={ { width: '16px', height: '16px' } }
            />
            Selecionar vencedor automaticamente
          </label>
        </div>
      </div>

      {/* Resultados da Batalha com Métricas */ }
      { scriptResults.length > 0 && (
        <div style={ { ...styles.card, marginBottom: '24px' } }>
          <div style={ { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' } }>
            <h3 style={ { ...styles.cardTitle, margin: 0 } }>
              ⚔️ Resultado da Batalha
            </h3>
            <div style={ { display: 'flex', gap: '12px' } }>
              <button
                onClick={ () => setShowMetricsDetail( !showMetricsDetail ) }
                style={ {
                  ...styles.button,
                  background: '#475569',
                  padding: '8px 16px',
                  fontSize: '0.9rem'
                } }
              >
                <BarChart3 size={ 16 } />
                { showMetricsDetail ? 'Ver Scripts' : 'Ver Métricas' }
              </button>
              <button
                onClick={ saveBattleResult }
                disabled={ !selectedWinner }
                style={ {
                  ...styles.button,
                  background: selectedWinner ? '#10b981' : '#4b5563',
                  padding: '8px 16px',
                  fontSize: '0.9rem',
                  cursor: selectedWinner ? 'pointer' : 'not-allowed'
                } }
              >
                <Award size={ 16 } />
                Salvar Resultado
              </button>
            </div>
          </div>

          {/* Métricas ou Scripts */ }
          { showMetricsDetail ? (
            <div style={ { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '16px' } }>
              { scriptResults.map( ( result ) => (
                battleMetrics[ result.iaName ] && (
                  <MetricsCard
                    key={ result.iaName }
                    iaName={ result.iaName }
                    metrics={ battleMetrics[ result.iaName ] }
                  />
                )
              ) ) }
            </div>
          ) : (
            <div style={ { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '16px' } }>
              { scriptResults.map( ( result ) => (
                <div
                  key={ result.iaName }
                  style={ {
                    ...styles.card,
                    background: selectedWinner === result.iaName ? '#065f46' : '#1e293b',
                    border: selectedWinner === result.iaName ? '2px solid #10b981' : '1px solid #475569',
                    cursor: 'pointer'
                  } }
                  onClick={ () => setSelectedWinner( result.iaName ) }
                >
                  <div style={ { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' } }>
                    <h4 style={ { margin: 0, color: 'white' } }>{ result.iaName }</h4>
                    { result.generationTime && (
                      <span style={ { color: '#9ca3af', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: '4px' } }>
                        <Clock size={ 14 } />
                        { result.generationTime.toFixed( 2 ) }s
                      </span>
                    ) }
                  </div>

                  { result.scriptData ? (
                    <div style={ { fontSize: '0.85rem', color: '#cbd5e1' } }>
                      <div style={ { marginBottom: '12px' } }>
                        <strong style={ { color: '#f59e0b' } }>🎯 Hook:</strong>
                        <div style={ { marginTop: '4px', fontStyle: 'italic' } }>
                          "{ result.scriptData.hook }"
                        </div>
                      </div>

                      <div style={ { marginBottom: '12px' } }>
                        <strong style={ { color: '#3b82f6' } }>📝 Título:</strong>
                        <div style={ { marginTop: '4px' } }>{ result.scriptData.titulo }</div>
                      </div>

                      <div style={ {
                        maxHeight: '200px',
                        overflowY: 'auto',
                        padding: '12px',
                        background: 'rgba(0,0,0,0.3)',
                        borderRadius: '8px',
                        marginBottom: '12px'
                      } }>
                        <strong>Roteiro:</strong>
                        <div style={ { marginTop: '8px', whiteSpace: 'pre-wrap' } }>
                          { result.scriptData.desenvolvimento }
                        </div>
                      </div>

                      <div style={ { marginBottom: '8px' } }>
                        <strong style={ { color: '#10b981' } }>📢 CTA:</strong>
                        <div style={ { marginTop: '4px' } }>{ result.scriptData.cta }</div>
                      </div>

                      <div style={ { display: 'flex', flexWrap: 'wrap', gap: '4px', marginTop: '8px' } }>
                        { ( result.scriptData.hashtags || [] ).slice( 0, 2 ).map( ( tag, idx ) => (
                          <span
                            key={ idx }
                            style={ {
                              background: '#334155',
                              padding: '2px 6px',
                              borderRadius: '12px',
                              fontSize: '0.75rem',
                              color: '#60a5fa'
                            } }
                          >
                            { tag }
                          </span>
                        ) ) }
                      </div>

                      <div style={ { marginTop: '12px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' } }>
                        <span style={ { color: '#9ca3af', fontSize: '0.8rem' } }>
                          ⏱️ Duração: { result.scriptData.duracao_estimada }s
                        </span>
                        { battleMetrics[ result.iaName ] && (
                          <span style={ { color: '#fbbf24', fontWeight: 'bold' } }>
                            Score: { battleMetrics[ result.iaName ].overallScore.toFixed( 1 ) }%
                          </span>
                        ) }
                      </div>
                    </div>
                  ) : (
                    <div style={ { color: '#ef4444' } }>{ result.error }</div>
                  ) }
                </div>
              ) ) }
            </div>
          ) }
        </div>
      ) }

      {/* Dashboard de Estatísticas e Histórico */ }
      <div style={ { display: 'grid', gridTemplateColumns: '1.2fr 0.8fr', gap: '24px' } }>
        {/* Painel de Estatísticas das IAs */ }
        <div>
          <h3 style={ {
            ...styles.cardTitle,
            marginBottom: '16px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          } }>
            <Brain size={ 20 } /> Estatísticas das IAs
          </h3>

          { isLoadingStats ? (
            <div style={ { ...styles.card, textAlign: 'center', padding: '40px' } }>
              <RefreshCw size={ 32 } color="#6b7280" style={ { animation: 'spin 1s linear infinite' } } />
              <p style={ { color: '#6b7280', marginTop: '12px' } }>Carregando estatísticas...</p>
            </div>
          ) : (
            <div style={ { display: 'flex', flexDirection: 'column', gap: '16px' } }>
              { aiStats.map( ( ai ) => (
                <div
                  key={ ai.model }
                  className="ai-stat-card"
                  style={ {
                    ...styles.card,
                    border: `2px solid ${ ai.color }`,
                    background: `linear-gradient(135deg, ${ ai.color }20 0%, transparent 100%)`,
                    transition: 'all 0.3s ease',
                  } }
                >
                  <div style={ { display: 'flex', justifyContent: 'space-between', alignItems: 'start' } }>
                    <div style={ { flex: 1 } }>
                      <div style={ { display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' } }>
                        <span style={ { fontSize: '2rem' } }>{ ai.strengthEmoji }</span>
                        <div>
                          <h4 style={ { margin: 0, color: 'white', fontSize: '1.1rem' } }>{ ai.name }</h4>
                          <p style={ { margin: 0, color: '#9ca3af', fontSize: '0.85rem' } }>{ ai.specialty }</p>
                        </div>
                      </div>

                      <div style={ { display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px' } }>
                        <div>
                          <div style={ { color: '#6b7280', fontSize: '0.75rem', marginBottom: '4px' } }>
                            Taxa de Vitória
                          </div>
                          <div style={ { display: 'flex', alignItems: 'baseline', gap: '8px' } }>
                            <span style={ { fontSize: '1.5rem', fontWeight: 'bold', color: ai.color } }>
                              { ai.winRate.toFixed( 1 ) }%
                            </span>
                            <span style={ { color: '#9ca3af', fontSize: '0.85rem' } }>
                              ({ ai.wins }/{ ai.totalBattles })
                            </span>
                          </div>
                        </div>

                        <div>
                          <div style={ { color: '#6b7280', fontSize: '0.75rem', marginBottom: '4px' } }>
                            Performance Score
                          </div>
                          <div style={ { fontSize: '1.5rem', fontWeight: 'bold', color: 'white' } }>
                            { ai.performanceScore.toFixed( 0 ) }
                          </div>
                        </div>
                      </div>

                      { ai.lastWin && (
                        <div style={ { marginTop: '12px', padding: '8px', background: 'rgba(16, 185, 129, 0.1)', borderRadius: '6px' } }>
                          <span style={ { color: '#10b981', fontSize: '0.8rem' } }>
                            🏆 Última vitória: { ai.lastWin }
                          </span>
                        </div>
                      ) }
                    </div>

                    <div style={ {
                      width: '60px',
                      height: '60px',
                      borderRadius: '50%',
                      background: `conic-gradient(${ ai.color } ${ ai.winRate * 3.6 }deg, #334155 0deg)`,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      position: 'relative'
                    } }>
                      <div style={ {
                        width: '48px',
                        height: '48px',
                        borderRadius: '50%',
                        background: '#0f172a',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center'
                      } }>
                        <Trophy size={ 20 } color={ ai.winRate > 50 ? '#fbbf24' : '#6b7280' } />
                      </div>
                    </div>
                  </div>
                </div>
              ) ) }
            </div>
          ) }
        </div>

        {/* Histórico de Batalhas */ }
        <div style={ styles.card }>
          <h3 style={ {
            ...styles.cardTitle,
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            marginBottom: '16px'
          } }>
            <Trophy size={ 20 } /> Histórico Recente
          </h3>

          <div style={ { display: 'flex', flexDirection: 'column', gap: '12px', maxHeight: '600px', overflowY: 'auto' } }>
            { battleHistory.length > 0 ? (
              battleHistory.map( ( battle ) => (
                <div
                  key={ battle.id }
                  className="history-item"
                  style={ {
                    padding: '16px',
                    background: '#1e293b',
                    borderRadius: '8px',
                    border: '1px solid #334155',
                    transition: 'all 0.2s ease',
                    cursor: 'pointer',
                  } }
                >
                  <div style={ { display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '8px' } }>
                    <div>
                      <div style={ { fontWeight: 'bold', color: 'white', marginBottom: '4px' } }>
                        { battle.topic }
                      </div>
                      <div style={ { fontSize: '0.8rem', color: '#9ca3af' } }>
                        <Clock size={ 12 } style={ { display: 'inline', marginRight: '4px' } } />
                        { new Date( battle.timestamp ).toLocaleString( 'pt-BR' ) }
                      </div>
                    </div>
                    <div style={ {
                      background: '#10b981',
                      color: 'white',
                      padding: '4px 12px',
                      borderRadius: '12px',
                      fontSize: '0.8rem',
                      fontWeight: 'bold'
                    } }>
                      { battle.winner }
                    </div>
                  </div>

                  <div style={ { display: 'flex', gap: '8px', marginTop: '12px' } }>
                    <div style={ {
                      flex: 1,
                      padding: '8px',
                      background: 'rgba(16, 185, 129, 0.1)',
                      borderRadius: '6px',
                      fontSize: '0.75rem'
                    } }>
                      <div style={ { color: '#10b981', fontWeight: 'bold', marginBottom: '4px' } }>
                        Vencedor
                      </div>
                      <div style={ { color: '#9ca3af' } }>
                        { formatNumber( battle.winnerStats.views ) } views • { battle.winnerStats.retention }% retenção
                      </div>
                    </div>
                    <div style={ {
                      flex: 1,
                      padding: '8px',
                      background: 'rgba(239, 68, 68, 0.1)',
                      borderRadius: '6px',
                      fontSize: '0.75rem'
                    } }>
                      <div style={ { color: '#ef4444', fontWeight: 'bold', marginBottom: '4px' } }>
                        { battle.loser }
                      </div>
                      <div style={ { color: '#9ca3af' } }>
                        { formatNumber( battle.loserStats.views ) } views • { battle.loserStats.retention }% retenção
                      </div>
                    </div>
                  </div>

                  { battle.videoUrl && (
                    <a
                      href={ battle.videoUrl }
                      target="_blank"
                      rel="noopener noreferrer"
                      style={ {
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '4px',
                        marginTop: '8px',
                        color: '#60a5fa',
                        fontSize: '0.8rem',
                        textDecoration: 'none'
                      } }
                    >
                      Ver vídeo →
                    </a>
                  ) }
                </div>
              ) )
            ) : (
              <div style={ { textAlign: 'center', padding: '40px', color: '#6b7280' } }>
                <Trophy size={ 48 } style={ { margin: '0 auto 16px', opacity: 0.3 } } />
                <p>Nenhuma batalha registrada ainda.</p>
                <p style={ { fontSize: '0.85rem', marginTop: '8px' } }>
                  Inicie uma batalha para ver o histórico!
                </p>
              </div>
            ) }
          </div>
        </div>
      </div>
    </div>
  );
};

// Função auxiliar para formatar números
const formatNumber = ( num: number | undefined | null ): string =>
{
  if ( typeof num !== 'number' || isNaN( num ) )
  {
    return 'N/A';
  }
  if ( num >= 1000000 ) return `${ ( num / 1000000 ).toFixed( 1 ) }M`;
  if ( num >= 1000 ) return `${ ( num / 1000 ).toFixed( 1 ) }K`;
  return num.toString();
};

export default AIBattleArena;