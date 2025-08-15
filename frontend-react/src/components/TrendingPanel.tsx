// /var/www/tiktok-automation/frontend-react/src/components/TrendingPanel.tsx

import React, { useState, useEffect } from 'react';
import
{
  TrendingUp, Clock, Youtube, Smartphone, ArrowUp, Flame, Star, AlertCircle, ChevronRight, Target
} from 'lucide-react';
import { TrendingItem } from '../types';

// Interface para a prop 'trendingTopics'
interface TrendingPanelProps
{
  trendingTopics: TrendingItem[];
}

// Interface para as estatísticas de plataformas (agora dentro do escopo)
interface PlatformStats
{
  platform: string;
  icon: React.ReactNode;
  color: string;
  trends: number;
  totalVolume: number;
}

// Função auxiliar para formatar números de forma segura
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

const TrendingPanel: React.FC<TrendingPanelProps> = ( { trendingTopics } ) =>
{
  const [ isExpanded, setIsExpanded ] = useState( false );
  const [ selectedPlatform, setSelectedPlatform ] = useState<string>( 'all' );
  const [ selectedCategory, setSelectedCategory ] = useState<string>( 'all' );
  const [ lastUpdate, setLastUpdate ] = useState( new Date() );

  // A lógica de dados simulados foi removida, a lista vem diretamente da prop.
  const platformStats: PlatformStats[] = [
    {
      platform: 'YouTube',
      icon: <Youtube size={ 16 } />,
      color: '#ff0000',
      trends: trendingTopics.filter( t => t.platform === 'YouTube' ).length,
      totalVolume: trendingTopics.filter( t => t.platform === 'YouTube' ).reduce( ( sum, t ) => sum + ( t.volume || 0 ), 0 )
    },
    {
      platform: 'Notícias',
      icon: <AlertCircle size={ 16 } />,
      color: '#10b981',
      trends: trendingTopics.filter( t => t.platform === 'Notícias' ).length,
      totalVolume: trendingTopics.filter( t => t.platform === 'Notícias' ).reduce( ( sum, t ) => sum + ( t.volume || 0 ), 0 )
    },
    {
      platform: 'Google Trends',
      icon: <TrendingUp size={ 16 } />,
      color: '#3b82f6',
      trends: trendingTopics.filter( t => t.platform === 'Google Trends' ).length,
      totalVolume: trendingTopics.filter( t => t.platform === 'Google Trends' ).reduce( ( sum, t ) => sum + ( t.volume || 0 ), 0 )
    },
    {
      platform: 'Reddit',
      icon: <Star size={ 16 } />,
      color: '#ff4500',
      trends: trendingTopics.filter( t => t.platform === 'Reddit' ).length,
      totalVolume: trendingTopics.filter( t => t.platform === 'Reddit' ).reduce( ( sum, t ) => sum + ( t.volume || 0 ), 0 )
    },
    {
      platform: 'Twitter',
      icon: <Smartphone size={ 16 } />,
      color: '#1da1f2',
      trends: trendingTopics.filter( t => t.platform === 'Twitter' ).length,
      totalVolume: trendingTopics.filter( t => t.platform === 'Twitter' ).reduce( ( sum, t ) => sum + ( t.volume || 0 ), 0 )
    }
  ];

  // Atualiza a hora da última atualização sempre que a prop `trendingTopics` muda
  useEffect( () =>
  {
    if ( trendingTopics.length > 0 )
    {
      setLastUpdate( new Date() );
    }
  }, [ trendingTopics ] );

  // Obter categorias únicas
  const categoryStats = Array.from( new Set( trendingTopics.map( t => t.category ) ) ).map( category => ( {
    category,
    trends: trendingTopics.filter( t => t.category === category ).length,
    platforms: Array.from( new Set( trendingTopics.filter( t => t.category === category ).map( t => t.platform ) ) )
  } ) );

  // Calcular estatísticas de plataforma para a barra inferior (baseado nos dados atuais)
  const getCurrentPlatformStats = () => {
    const dataToUse = trendingTopics; // Sempre usar dados completos na barra inferior
    
    return [
      {
        platform: 'YouTube',
        icon: <Youtube size={ 16 } />,
        color: '#ff0000',
        trends: dataToUse.filter( t => t.platform === 'YouTube' ).length,
        totalVolume: dataToUse.filter( t => t.platform === 'YouTube' ).reduce( ( sum, t ) => sum + ( t.volume || 0 ), 0 )
      },
      {
        platform: 'Notícias',
        icon: <AlertCircle size={ 16 } />,
        color: '#10b981',
        trends: dataToUse.filter( t => t.platform === 'Notícias' ).length,
        totalVolume: dataToUse.filter( t => t.platform === 'Notícias' ).reduce( ( sum, t ) => sum + ( t.volume || 0 ), 0 )
      },
      {
        platform: 'Google Trends',
        icon: <TrendingUp size={ 16 } />,
        color: '#3b82f6',
        trends: dataToUse.filter( t => t.platform === 'Google Trends' ).length,
        totalVolume: dataToUse.filter( t => t.platform === 'Google Trends' ).reduce( ( sum, t ) => sum + ( t.volume || 0 ), 0 )
      },
      {
        platform: 'Reddit',
        icon: <Star size={ 16 } />,
        color: '#ff4500',
        trends: dataToUse.filter( t => t.platform === 'Reddit' ).length,
        totalVolume: dataToUse.filter( t => t.platform === 'Reddit' ).reduce( ( sum, t ) => sum + ( t.volume || 0 ), 0 )
      },
      {
        platform: 'Twitter',
        icon: <Smartphone size={ 16 } />,
        color: '#1da1f2',
        trends: dataToUse.filter( t => t.platform === 'Twitter' ).length,
        totalVolume: dataToUse.filter( t => t.platform === 'Twitter' ).reduce( ( sum, t ) => sum + ( t.volume || 0 ), 0 )
      }
    ];
  };

  const currentPlatformStats = getCurrentPlatformStats();

  const getStatusColor = ( status: TrendingItem[ 'status' ] | undefined ) =>
  {
    switch ( status )
    {
      case 'hot': return '#ef4444';
      case 'rising': return '#10b981';
      case 'stable': return '#3b82f6';
      case 'declining': return '#9ca3af';
      default: return '#6b7280';
    }
  };

  const getStatusIcon = ( status: TrendingItem[ 'status' ] | undefined ) =>
  {
    switch ( status )
    {
      case 'hot': return <Flame size={ 14 } />;
      case 'rising': return <TrendingUp size={ 14 } />;
      case 'stable': return <Target size={ 14 } />;
      case 'declining': return <ArrowUp size={ 14 } style={ { transform: 'rotate(180deg)' } } />;
      default: return <AlertCircle size={ 14 } />;
    }
  };

  const getStatusLabel = ( status: TrendingItem[ 'status' ] | undefined ) =>
  {
    switch ( status )
    {
      case 'hot': return 'Viral';
      case 'rising': return 'Crescendo';
      case 'stable': return 'Estável';
      case 'declining': return 'Caindo';
      default: return 'N/A';
    }
  };

  const filteredTrends = trendingTopics.filter( item => {
    const platformMatch = selectedPlatform === 'all' || item.platform.toLowerCase().includes( selectedPlatform.toLowerCase() );
    const categoryMatch = selectedCategory === 'all' || item.category === selectedCategory;
    return platformMatch && categoryMatch;
  } );

  const TrendingCard = ( { item }: { item: TrendingItem } ) => (
    <div style={ {
      padding: '16px',
      background: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
      borderRadius: '8px',
      border: `1px solid ${ getStatusColor( item.status ) }40`,
      cursor: 'pointer',
      transition: 'all 0.3s ease',
      minWidth: '320px',
      maxWidth: '320px',
      minHeight: '180px',
      maxHeight: '180px',
      position: 'relative',
      overflow: 'hidden',
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'space-between'
    } }>
      {/* Status indicator */ }
      <div style={ {
        position: 'absolute',
        top: '8px',
        right: '8px',
        display: 'flex',
        alignItems: 'center',
        gap: '4px',
        background: `${ getStatusColor( item.status ) }20`,
        padding: '2px 6px',
        borderRadius: '10px',
        fontSize: '0.7rem',
        color: getStatusColor( item.status )
      } }>
        { getStatusIcon( item.status ) }
        { getStatusLabel( item.status ) }
      </div>

      {/* Content */ }
      <div style={ { flex: 1, paddingRight: '60px' } }>
        <div style={ {
          color: 'white',
          fontWeight: 'bold',
          fontSize: '0.9rem',
          marginBottom: '8px',
          lineHeight: '1.3',
          overflow: 'hidden',
          display: '-webkit-box',
          WebkitLineClamp: 2,
          WebkitBoxOrient: 'vertical'
        } }>
          { item.topic }
        </div>
        <div style={ {
          color: '#9ca3af',
          fontSize: '0.75rem',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          flexWrap: 'wrap'
        } }>
          <span>📱 { item.platform }</span>
          <span>🏷️ { item.category }</span>
          <span>🌍 { item.region }</span>
        </div>
      </div>

      {/* Stats */ }
      <div style={ {
        display: 'grid',
        gridTemplateColumns: '1fr 1fr 1fr',
        gap: '8px',
        marginBottom: '8px',
        fontSize: '0.75rem'
      } }>
        <div>
          <div style={ { color: '#9ca3af' } }>Crescimento</div>
          <div style={ {
            color: '#10b981',
            fontWeight: 'bold',
            display: 'flex',
            alignItems: 'center',
            gap: '2px'
          } }>
            <ArrowUp size={ 10 } />
            +{ item.growth || 0 }%
          </div>
        </div>
        <div>
          <div style={ { color: '#9ca3af' } }>Volume</div>
          <div style={ { color: '#3b82f6', fontWeight: 'bold' } }>
            { formatNumber( item.volume ) }
          </div>
        </div>
        <div>
          <div style={ { color: '#9ca3af' } }>Potencial</div>
          <div style={ { color: '#f59e0b', fontWeight: 'bold' } }>
            { item.viralPotential || 0 }%
          </div>
        </div>
      </div>

      {/* Hashtags and time */ }
      <div style={ {
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        fontSize: '0.7rem'
      } }>
        <div style={ {
          display: 'flex',
          gap: '4px',
          flexWrap: 'wrap',
          flex: 1
        } }>
          { ( item.hashtags || [] ).slice( 0, 2 ).map( ( tag ) => (
            <span
              key={ tag }
              style={ {
                background: '#3b82f620',
                color: '#3b82f6',
                padding: '2px 6px',
                borderRadius: '8px',
                fontSize: '0.65rem'
              } }
            >
              { tag }
            </span>
          ) ) }
        </div>
        <div style={ {
          color: '#9ca3af',
          display: 'flex',
          alignItems: 'center',
          gap: '2px',
          marginLeft: '8px'
        } }>
          <Clock size={ 10 } />
          { item.timeframe }
        </div>
      </div>
    </div>
  );

  return (
    <div style={ {
      position: 'fixed',
      bottom: 0,
      left: 0,
      right: 0,
      background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
      borderTop: '2px solid #3b82f6',
      zIndex: 100,
      transition: 'all 0.3s ease',
      transform: isExpanded ? 'translateY(0)' : 'translateY(calc(100% - 60px))'
    } }>
      {/* Header bar */ }
      <div
        onClick={ () => setIsExpanded( !isExpanded ) }
        style={ {
          height: '60px',
          padding: '0 24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          cursor: 'pointer',
          borderBottom: isExpanded ? '1px solid #334155' : 'none'
        } }
      >
        <div style={ {
          display: 'flex',
          alignItems: 'center',
          gap: '12px'
        } }>
          <div style={ {
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            color: 'white',
            fontWeight: 'bold'
          } }>
            <TrendingUp size={ 20 } style={ { color: '#3b82f6' } } />
            🔥 Inteligência de Tendências
            { trendingTopics.length > 0 && (
              <div style={ {
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                background: '#10b98120',
                padding: '2px 6px',
                borderRadius: '8px',
                fontSize: '0.7rem',
                color: '#10b981'
              } }>
                AO VIVO
              </div>
            ) }
          </div>

          {/* Quick stats */ }
          <div style={ {
            display: 'flex',
            gap: '16px',
            fontSize: '0.8rem',
            color: '#9ca3af'
          } }>
            <span>📊 { trendingTopics.length } tendências</span>
            <span>⚡ { trendingTopics.filter( t => t.status === 'hot' ).length } virais</span>
            <span>
              📈 Média +
              { trendingTopics.length > 0
                ? Math.round( trendingTopics.reduce( ( sum, t ) => sum + ( t.growth || 0 ), 0 ) / trendingTopics.length )
                : 0 }%
            </span>
          </div>
        </div>

        <div style={ {
          display: 'flex',
          alignItems: 'center',
          gap: '12px'
        } }>
          <div style={ {
            color: '#9ca3af',
            fontSize: '0.8rem',
            display: 'flex',
            alignItems: 'center',
            gap: '4px'
          } }>
            <Clock size={ 12 } />
            Atualizado { lastUpdate.toLocaleTimeString( 'pt-BR', { hour: '2-digit', minute: '2-digit' } ) }
          </div>

          <ChevronRight
            size={ 20 }
            style={ {
              color: '#9ca3af',
              transform: isExpanded ? 'rotate(270deg)' : 'rotate(90deg)',
              transition: 'transform 0.3s ease'
            } }
          />
        </div>
      </div>

      {/* Expanded content */ }
      { isExpanded && (
        <div style={ { padding: '20px' } }>
          {/* Platform filters */ }
          <div style={ {
            display: 'flex',
            gap: '8px',
            marginBottom: '20px',
            alignItems: 'center'
          } }>
            <span style={ { color: '#9ca3af', fontSize: '0.9rem', marginRight: '8px' } }>
              Filtrar por fonte:
            </span>

            <button
              onClick={ () => setSelectedPlatform( 'all' ) }
              style={ {
                padding: '6px 12px',
                background: selectedPlatform === 'all' ? '#3b82f6' : '#374151',
                border: 'none',
                color: 'white',
                borderRadius: '6px',
                fontSize: '0.8rem',
                cursor: 'pointer'
              } }
            >
              Todas ({ trendingTopics.length })
            </button>

            { platformStats.map( ( platform ) => (
              <button
                key={ platform.platform }
                onClick={ () => setSelectedPlatform( platform.platform ) }
                style={ {
                  padding: '6px 12px',
                  background: selectedPlatform === platform.platform ? platform.color : '#374151',
                  border: 'none',
                  color: 'white',
                  borderRadius: '6px',
                  fontSize: '0.8rem',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  opacity: platform.trends === 0 ? 0.6 : 1
                } }
              >
                { platform.icon }
                { platform.platform } ({ platform.trends })
              </button>
            ) ) }
          </div>

          {/* Category filters */ }
          <div style={ {
            display: 'flex',
            gap: '8px',
            marginBottom: '20px',
            alignItems: 'center'
          } }>
            <span style={ { color: '#9ca3af', fontSize: '0.9rem', marginRight: '8px' } }>
              Filtrar por categoria:
            </span>

            <button
              onClick={ () => setSelectedCategory( 'all' ) }
              style={ {
                padding: '6px 12px',
                background: selectedCategory === 'all' ? '#10b981' : '#374151',
                border: 'none',
                color: 'white',
                borderRadius: '6px',
                fontSize: '0.8rem',
                cursor: 'pointer'
              } }
            >
              Todas ({ selectedPlatform === 'all' ? trendingTopics.length : trendingTopics.filter( t => t.platform === selectedPlatform ).length })
            </button>

            { categoryStats.map( ( catStat ) => (
              <button
                key={ catStat.category }
                onClick={ () => setSelectedCategory( catStat.category ) }
                style={ {
                  padding: '6px 12px',
                  background: selectedCategory === catStat.category ? '#10b981' : '#374151',
                  border: 'none',
                  color: 'white',
                  borderRadius: '6px',
                  fontSize: '0.8rem',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  opacity: catStat.trends === 0 ? 0.6 : 1
                } }
              >
                { catStat.category } ({ catStat.trends })
              </button>
            ) ) }
          </div>

          {/* Trending items */ }
          <div style={ {
            display: 'flex',
            gap: '12px',
            overflowX: 'auto',
            paddingBottom: '8px'
          } }>
            { filteredTrends.length > 0 ? (
              filteredTrends.map( ( item ) => (
                <TrendingCard key={ item.id } item={ item } />
              ) )
            ) : (
              <div style={ { color: '#9ca3af', width: '100%', textAlign: 'center', marginTop: '20px' } }>
                Nenhuma tendência encontrada para { selectedPlatform !== 'all' ? `fonte "${selectedPlatform}"` : '' }
                { selectedPlatform !== 'all' && selectedCategory !== 'all' ? ' e ' : '' }
                { selectedCategory !== 'all' ? `categoria "${selectedCategory}"` : '' }.
              </div>
            ) }
          </div>

          {/* Platform summary */ }
          <div style={ {
            marginTop: '16px',
            padding: '12px',
            background: '#0f172a',
            borderRadius: '8px',
            border: '1px solid #334155'
          } }>
            <div style={ {
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: '16px',
              fontSize: '0.8rem'
            } }>
              { currentPlatformStats.map( ( platform ) => (
                <div
                  key={ platform.platform }
                  style={ {
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px'
                  } }
                >
                  <div style={ { color: platform.color } }>
                    { platform.icon }
                  </div>
                  <div>
                    <div style={ { color: 'white', fontWeight: 'bold' } }>
                      { platform.platform }
                    </div>
                    <div style={ { color: '#9ca3af' } }>
                      { platform.trends } tendências • { formatNumber( platform.totalVolume ) } vol
                    </div>
                  </div>
                </div>
              ) ) }
            </div>
          </div>
        </div>
      ) }
    </div>
  );
};

export default TrendingPanel;