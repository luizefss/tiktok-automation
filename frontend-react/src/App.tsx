//var/www/tiktok-automation/frontend-react/src/App.tsx

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Video, Globe, Brain, DollarSign, Target, Rocket, BarChart3 } from 'lucide-react';
import { apiService, Stats, Video as VideoType } from './services/api';

// Componentes
import { StatCard } from './components/StatCard';
import VideoModal from './components/VideoModal';
import GlobalCommandCenter from './components/GlobalCommandCenter';
import AIBattleArena from './components/AIBattleArena';
import ProductionStudio from './components/ProductionStudio';
import EmpireAnalytics from './components/EmpireAnalytics';
import TrendingPanel from './components/TrendingPanel';
import QuickActions from './components/QuickActions';

// Estilos e Tipos
import { globalStyles as styles } from './global-styles';
import { ContentSettings, TrendingItem } from './types';

type TabType = 'command' | 'ai-battle' | 'studio' | 'analytics';
interface TabConfig { id: TabType; name: string; icon: React.ReactNode; description: string; }

const App: React.FC = () =>
{
  // Estados principais
  const [ status, setStatus ] = useState<Partial<Stats>>( {} );
  const [ videos, setVideos ] = useState<VideoType[]>( [] );
  const [ isLoading, setIsLoading ] = useState( true );
  const [ selectedVideo, setSelectedVideo ] = useState<VideoType | null>( null );
  const [ activeTab, setActiveTab ] = useState<TabType>( 'command' ); // Iniciar em Command Center
  const [ isSystemActive, setIsSystemActive ] = useState( false );
  const [ globalSettings, setGlobalSettings ] = useState( {
    autoMode: true,
    multiPlatform: true,
    multiLanguage: false,
    aiCompetition: true,
    revenueTracking: true
  } );
  const [ trendingTopics, setTrendingTopics ] = useState<TrendingItem[]>( [] );
  const [ contentSettings, setContentSettings ] = useState<ContentSettings>( {
    topic: '',
    script: '',
    audio_duration: 60,
    content_ai_model: 'chatgpt',
    content_type: 'custom_message',
    custom_topics: [ 'Mistérios' ],
    message_categories: [ '' ],
    tone: 'mysterious',
    image_style: 'realistic',
    color_palette: 'vibrant',
    animation_type: 'parallax',
    voice_emotion: 'neutral',
    speaking_speed: 1.08,
    use_topmedia_ai: false,
    background_music: '',
    background_music_volume: 0.15,
    video_duration: 60,
    transitions: 'dynamic',
    text_overlay: true,
    custom_prompt_roteiro: '',
    custom_prompt_imagem: '',
    custom_prompt_audio: '',
    target_platforms: [ 'short' ],
    target_languages: [ 'pt-BR' ],
    ai_competition_mode: true,
    auto_research_trending: true,
    generate_micro_videos: true,
    video_effects_enabled: true,
    subtitle_style: 'neon_glow',
    revenue_optimization: true,
    
    // Configurações de áudio TTS
    voice_style: 'default',
    emotion_style: 'neutro',
    audio_file: undefined
  } );

  const tabs: TabConfig[] = [
    { id: 'command', name: 'Command Center', icon: <Globe size={ 20 } />, description: 'Visão geral' },
    { id: 'ai-battle', name: 'AI Battle', icon: <Brain size={ 20 } />, description: 'Arena de IAs' },
    { id: 'studio', name: 'Production', icon: <Video size={ 20 } />, description: 'Estúdio de produção' },
    { id: 'analytics', name: 'Empire Analytics', icon: <BarChart3 size={ 20 } />, description: 'Análise de performance' }
  ];

  // Carregar dados do sistema
  // Controle de rate limiting para trending topics
  const [ lastTrendingUpdate, setLastTrendingUpdate ] = useState<Date>( new Date() );
  const TRENDING_CACHE_DURATION = useMemo( () => 10 * 60 * 1000, [] ); // 10 minutos

  const loadData = useCallback( async ( showLoading = false ) =>
  {
    if ( showLoading ) setIsLoading( true );

    try
    {
      // Carregar status do sistema
      const statusData = await apiService.getStatus();
      setStatus( statusData );
      setIsSystemActive( statusData.automation_running || false );

      // Carregar vídeos
      const videosData = await apiService.getVideos();
      setVideos( videosData );

      // Carregar trending topics apenas se necessário (rate limiting)
      const now = new Date();
      const timeSinceLastUpdate = now.getTime() - lastTrendingUpdate.getTime();
      
      if ( timeSinceLastUpdate > TRENDING_CACHE_DURATION || trendingTopics.length === 0 )
      {
        console.log( '🔄 Atualizando trending topics...' );
        const trending = await apiService.getTrendingTopics();
        setTrendingTopics( trending.topics || [] );
        setLastTrendingUpdate( now );
      } else
      {
        console.log( `⏳ Trending cache válido por mais ${ Math.round( ( TRENDING_CACHE_DURATION - timeSinceLastUpdate ) / 1000 / 60 ) } minutos` );
      }

      console.log( '✅ Dados carregados:', { status: statusData, videos: videosData.length, trending: trendingTopics.length } );
    } catch ( error )
    {
      console.error( '❌ Erro ao carregar dados:', error );
    } finally
    {
      setIsLoading( false );
    }
  }, [ lastTrendingUpdate, trendingTopics.length, TRENDING_CACHE_DURATION ] );

  // Carregar dados ao iniciar
  useEffect( () =>
  {
    loadData( true );

    // Atualizar a cada 2 minutos (aumentado de 30s)
    const interval = setInterval( () => loadData( false ), 120000 );
    return () => clearInterval( interval );
  }, [ loadData ] );

  // Handler para ações assíncronas
  const handleAction = async ( action: Promise<any> ) =>
  {
    try
    {
      const result = await action;
      await loadData(); // Recarregar dados após ação
      return result;
    } catch ( error )
    {
      console.error( 'Erro na ação:', error );
      throw error;
    }
  };

  // Gerar vídeo viral com trending automático
  const handleGenerateViral = async () =>
  {
    console.log( '🚀 Gerando vídeo viral...' );
    try
    {
      // Pegar o trending topic mais quente
      const hotTopic = trendingTopics[ 0 ]?.topic || 'Trending do momento';

      const result = await handleAction( apiService.generateViral() );
      console.log( '✅ Vídeo viral iniciado:', result );
      alert( `Gerando vídeo viral: "${ hotTopic }"\n${ result.message }` );
    } catch ( error )
    {
      console.error( '❌ Erro ao gerar viral:', error );
      alert( 'Erro ao gerar vídeo viral' );
    }
  };

  // Alternar modo do sistema com feedback visual
  const handleToggleSystemMode = async () =>
  {
    console.log( '🔄 Alternando sistema...' );
    try
    {
      const result = await apiService.toggleAutomation();
      console.log( '✅ Sistema alternado:', result );
      
      // Toggle the current state since API doesn't return the new state
      const newState = !isSystemActive;
      setIsSystemActive( newState );

      // Feedback visual
      if ( newState )
      {
        alert( '🟢 Sistema ATIVADO!\nGeração automática de vídeos iniciada.' );
        // Iniciar geração automática
        setTimeout( () => handleGenerateViral(), 5000 );
      } else
      {
        alert( '🔴 Sistema PAUSADO\nGeração automática interrompida.' );
      }

      await loadData();
    } catch ( error )
    {
      console.error( '❌ Erro ao alternar sistema:', error );
      alert( 'Erro ao alternar sistema' );
    }
  };

  // Gerar conteúdo customizado
  const handleGenerateCustom = async () =>
  {
    console.log( '🎬 Gerando customizado...', contentSettings );
    try
    {
      const result = await apiService.generateCustomContent( { settings: contentSettings } );
      console.log( '✅ Geração customizada iniciada:', result );
      alert( result.message || 'Geração customizada iniciada!' );
      await loadData();
    } catch ( error )
    {
      console.error( '❌ Erro ao gerar customizado:', error );
      alert( 'Erro ao gerar conteúdo customizado' );
    }
  };

  // Iniciar batalha
  const handleStartBattle = async ( settings: ContentSettings ) =>
  {
    console.log( '⚔️ Iniciando batalha...', settings );
    try
    {
      const result = await apiService.startBattleVideo( { settings } );
      console.log( '✅ Batalha iniciada:', result );
      alert( result.message || 'Batalha iniciada!' );
    } catch ( error )
    {
      console.error( '❌ Erro ao iniciar batalha:', error );
      alert( 'Erro ao iniciar batalha' );
    }
  };

  const renderActiveTab = () =>
  {
    switch ( activeTab )
    {
      case 'command':
        return (
          <GlobalCommandCenter
            status={ status }
            isSystemActive={ isSystemActive }
            globalSettings={ globalSettings }
            trendingTopics={ trendingTopics }
            onToggleSystem={ handleToggleSystemMode }
            onGenerateViral={ handleGenerateViral }
            onSettingsChange={ async ( settings ) =>
            {
              setGlobalSettings( settings );
              // Salvar no backend
              try
              {
                await apiService.updateGlobalSettings( settings );
                console.log( '✅ Configurações salvas:', settings );
              } catch ( error )
              {
                console.error( '❌ Erro ao salvar configurações:', error );
              }
            } }
          />
        );
      case 'ai-battle':
        return <AIBattleArena contentSettings={ contentSettings } />;
      case 'studio':
        return (
          <ProductionStudio
            contentSettings={ contentSettings }
            onSettingsChange={ setContentSettings }
            onGenerateCustom={ handleGenerateCustom }
          />
        );
      case 'analytics':
        return <EmpireAnalytics videos={ videos } status={ status } contentSettings={ contentSettings } />;
      default:
        return null;
    }
  };

  if ( isLoading )
  {
    return (
      <div style={ {
        ...styles.page,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh'
      } }>
        <div style={ { textAlign: 'center' } }>
          <div style={ { fontSize: '2rem', marginBottom: '16px' } }>🚀</div>
          <div style={ { color: '#9ca3af' } }>Carregando sistema...</div>
        </div>
      </div>
    );
  }

  return (
    <div style={ styles.page }>
      { selectedVideo && <VideoModal video={ selectedVideo } onClose={ () => setSelectedVideo( null ) } /> }
      <div style={ styles.container }>
        <div style={ { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', padding: '16px 0' } }>
          <div>
            <h1 style={ {
              ...styles.headerTitle,
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              marginBottom: '4px'
            } }>
              🌍 Viral Empire Dashboard
            </h1>
            <div style={ { color: '#9ca3af', fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: '16px' } }>
              <span>🤖 Sistema: { isSystemActive ? '🟢 Ativo' : '🔴 Pausado' }</span>
              <span>📱 Plataformas: { contentSettings.target_platforms?.length || 1 }</span>
              <span>🌐 Idiomas: { contentSettings.target_languages?.length || 1 }</span>
            </div>
          </div>
          <QuickActions
            onEmergencyGenerate={ handleGenerateViral }
            isSystemActive={ isSystemActive }
            onToggleSystem={ handleToggleSystemMode }
          />
        </div>

        <div style={ styles.statsGrid }>
          <StatCard
            icon={ <Rocket size={ 28 } /> }
            title="Viral Engine"
            value={ isSystemActive ? 'ATIVO' : 'PAUSADO' }
            color={ isSystemActive ? '#10b981' : '#f59e0b' }
          />
          <StatCard
            icon={ <Target size={ 28 } /> }
            title="Fila Global"
            value={ videos.filter( v => v.metadata?.status !== 'Postado' ).length }
          />
          <StatCard
            icon={ <DollarSign size={ 28 } /> }
            title="Revenue Est."
            value={ `$${ ( ( videos.length * 50 ) + 1000 ).toLocaleString() }` }
          />
          <StatCard
            icon={ <Globe size={ 28 } /> }
            title="Alcance Global"
            value={ status.total_views ?? '0' }
          />
        </div>

        <div style={ { marginBottom: '24px' } }>
          <div style={ styles.tabContainer }>
            { tabs.map( ( tab ) => (
              <button
                key={ tab.id }
                onClick={ () => setActiveTab( tab.id ) }
                style={ {
                  ...styles.tab,
                  ...( activeTab === tab.id ? styles.activeTab : {} )
                } }
              >
                { tab.icon } <span>{ tab.name }</span>
              </button>
            ) ) }
          </div>
        </div>

        <div style={ { minHeight: '600px' } }>
          { renderActiveTab() }
        </div>

        <TrendingPanel trendingTopics={ trendingTopics } />
      </div>
    </div>
  );
};

export default App;