import React, { useState, useEffect } from 'react';
import { 
  DollarSign, TrendingUp, BarChart3, Target, Globe, Eye,
  Users, Clock, Award, Zap, ArrowUp, ArrowDown, Calendar,
  PieChart, LineChart, Activity, Rocket, Star, AlertCircle
} from 'lucide-react';
import { globalStyles as styles } from '../global-styles';
import { Stats, Video as VideoType } from '../services/api';
import { ContentSettings } from '../types';

interface EmpireAnalyticsProps {
  videos: VideoType[];
  status: Partial<Stats>;
  contentSettings: ContentSettings;
}

interface RevenueData {
  platform: string;
  monthly: number;
  growth: number;
  cpm: number;
  videos: number;
  flag: string;
}

interface PerformanceMetric {
  metric: string;
  current: number;
  target: number;
  trend: number;
  status: 'excellent' | 'good' | 'warning' | 'critical';
}

interface ViralPrediction {
  topic: string;
  platform: string;
  probability: number;
  expectedViews: number;
  revenue: number;
  timeframe: string;
}

const EmpireAnalytics: React.FC<EmpireAnalyticsProps> = ({
  videos,
  status,
  contentSettings
}) => {
  const [timeRange, setTimeRange] = useState<'7d' | '30d' | '90d' | '1y'>('30d');
  const [selectedMetric, setSelectedMetric] = useState<'revenue' | 'performance' | 'predictions'>('revenue');

  const [revenueData, setRevenueData] = useState<RevenueData[]>([
    { platform: 'YouTube US', monthly: 23847, growth: 34.2, cpm: 4.50, videos: 45, flag: '🇺🇸' },
    { platform: 'TikTok US', monthly: 15623, growth: 67.8, cpm: 2.30, videos: 120, flag: '🇺🇸' },
    { platform: 'YouTube BR', monthly: 8934, growth: 12.5, cpm: 1.20, videos: 67, flag: '🇧🇷' },
    { platform: 'TikTok BR', monthly: 6745, growth: 45.3, cpm: 0.80, videos: 156, flag: '🇧🇷' },
    { platform: 'Shorts US', monthly: 12456, growth: 89.4, cpm: 3.20, videos: 89, flag: '🇺🇸' },
    { platform: 'Kwai BR', monthly: 4532, growth: 23.7, cpm: 0.60, videos: 78, flag: '🇧🇷' }
  ]);

  const [performanceMetrics, setPerformanceMetrics] = useState<PerformanceMetric[]>([
    { metric: 'Taxa de Viral', current: 28, target: 35, trend: 15.3, status: 'good' },
    { metric: 'Retenção Média', current: 87, target: 90, trend: 8.7, status: 'good' },
    { metric: 'Engajamento', current: 94, target: 85, trend: 12.4, status: 'excellent' },
    { metric: 'CTR Thumbnails', current: 76, target: 80, trend: -2.1, status: 'warning' },
    { metric: 'Qualidade IA', current: 91, target: 95, trend: 5.8, status: 'good' },
    { metric: 'Conversão Subs', current: 23, target: 30, trend: 18.9, status: 'warning' }
  ]);

  const [viralPredictions, setViralPredictions] = useState<ViralPrediction[]>([
    { topic: 'Hacker NASA 2025', platform: 'TikTok US', probability: 94, expectedViews: 2300000, revenue: 5290, timeframe: '24-48h' },
    { topic: 'IA Consciente Google', platform: 'YouTube US', probability: 87, expectedViews: 850000, revenue: 3825, timeframe: '3-5 dias' },
    { topic: 'Alien Signals Brazil', platform: 'YouTube BR', probability: 76, expectedViews: 420000, revenue: 504, timeframe: '2-3 dias' },
    { topic: 'Mistério Mariana MG', platform: 'Kwai BR', probability: 83, expectedViews: 650000, revenue: 390, timeframe: '1-2 dias' }
  ]);

  const totalRevenue = revenueData.reduce((sum, item) => sum + item.monthly, 0);
  const avgGrowth = revenueData.reduce((sum, item) => sum + item.growth, 0) / revenueData.length;
  const totalVideos = revenueData.reduce((sum, item) => sum + item.videos, 0);

  // Simulação de dados em tempo real
  useEffect(() => {
    const interval = setInterval(() => {
      setRevenueData(prev => prev.map(item => ({
        ...item,
        growth: Math.max(0, Math.min(100, item.growth + (Math.random() - 0.5) * 2))
      })));
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status: PerformanceMetric['status']) => {
    switch (status) {
      case 'excellent': return '#10b981';
      case 'good': return '#3b82f6';
      case 'warning': return '#f59e0b';
      case 'critical': return '#ef4444';
      default: return '#6b7280';
    }
  };

  const getStatusIcon = (status: PerformanceMetric['status']) => {
    switch (status) {
      case 'excellent': return <Star size={16} />;
      case 'good': return <TrendingUp size={16} />;
      case 'warning': return <AlertCircle size={16} />;
      case 'critical': return <ArrowDown size={16} />;
      default: return <Activity size={16} />;
    }
  };

  const RevenueCard = ({ data }: { data: RevenueData }) => (
    <div style={{
      ...styles.card,
      background: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
      border: '1px solid #475569',
      position: 'relative',
      overflow: 'hidden'
    }}>
      <div style={{
        position: 'absolute',
        top: 0,
        right: 0,
        width: '60px',
        height: '60px',
        background: `${data.growth > 50 ? '#10b981' : data.growth > 20 ? '#3b82f6' : '#f59e0b'}20`,
        borderRadius: '50%',
        transform: 'translate(20px, -20px)'
      }} />
      
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        marginBottom: '12px'
      }}>
        <div>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            marginBottom: '4px'
          }}>
            <span style={{ fontSize: '1.2rem' }}>{data.flag}</span>
            <div style={{ color: 'white', fontWeight: 'bold', fontSize: '1rem' }}>
              {data.platform}
            </div>
          </div>
          <div style={{ color: '#9ca3af', fontSize: '0.8rem' }}>
            {data.videos} vídeos • CPM ${data.cpm}
          </div>
        </div>
        
        <div style={{
          textAlign: 'right'
        }}>
          <div style={{
            color: 'white',
            fontSize: '1.3rem',
            fontWeight: 'bold'
          }}>
            ${data.monthly.toLocaleString()}
          </div>
          <div style={{
            color: data.growth > 20 ? '#10b981' : '#f59e0b',
            fontSize: '0.8rem',
            display: 'flex',
            alignItems: 'center',
            gap: '2px'
          }}>
            {data.growth > 0 ? <ArrowUp size={12} /> : <ArrowDown size={12} />}
            +{data.growth.toFixed(1)}%
          </div>
        </div>
      </div>
      
      <div style={{
        background: '#0f172a',
        padding: '8px',
        borderRadius: '4px',
        fontSize: '0.75rem',
        color: '#cbd5e1'
      }}>
        Revenue/vídeo: ${(data.monthly / data.videos).toFixed(0)}
      </div>
    </div>
  );

  const MetricCard = ({ metric }: { metric: PerformanceMetric }) => (
    <div style={{
      padding: '16px',
      background: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
      borderRadius: '8px',
      border: `1px solid ${getStatusColor(metric.status)}40`,
      position: 'relative'
    }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        marginBottom: '12px'
      }}>
        <div>
          <div style={{ color: '#cbd5e1', fontSize: '0.9rem', marginBottom: '4px' }}>
            {metric.metric}
          </div>
          <div style={{
            color: 'white',
            fontSize: '1.5rem',
            fontWeight: 'bold',
            display: 'flex',
            alignItems: 'baseline',
            gap: '4px'
          }}>
            {metric.current}
            <span style={{ fontSize: '0.8rem', color: '#9ca3af' }}>
              /{metric.target}
            </span>
          </div>
        </div>
        
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '4px',
          color: getStatusColor(metric.status)
        }}>
          {getStatusIcon(metric.status)}
        </div>
      </div>
      
      <div style={{
        background: '#0f172a',
        borderRadius: '4px',
        padding: '2px'
      }}>
        <div style={{
          width: `${(metric.current / metric.target) * 100}%`,
          height: '4px',
          background: getStatusColor(metric.status),
          borderRadius: '2px'
        }} />
      </div>
      
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginTop: '8px',
        fontSize: '0.75rem'
      }}>
        <span style={{ color: '#9ca3af' }}>Meta: {metric.target}</span>
        <span style={{
          color: metric.trend > 0 ? '#10b981' : '#ef4444',
          display: 'flex',
          alignItems: 'center',
          gap: '2px'
        }}>
          {metric.trend > 0 ? <ArrowUp size={10} /> : <ArrowDown size={10} />}
          {Math.abs(metric.trend).toFixed(1)}%
        </span>
      </div>
    </div>
  );

  const PredictionCard = ({ prediction }: { prediction: ViralPrediction }) => (
    <div style={{
      padding: '16px',
      background: `linear-gradient(135deg, rgba(16, 185, 129, ${prediction.probability / 1000}) 0%, rgba(59, 130, 246, ${prediction.probability / 1000}) 100%)`,
      borderRadius: '8px',
      border: '1px solid #475569',
      position: 'relative'
    }}>
      <div style={{
        position: 'absolute',
        top: '8px',
        right: '8px',
        background: prediction.probability > 90 
          ? 'linear-gradient(135deg, #10b981 0%, #059669 100%)'
          : prediction.probability > 75
          ? 'linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)'
          : 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
        color: 'white',
        padding: '4px 8px',
        borderRadius: '12px',
        fontSize: '0.75rem',
        fontWeight: 'bold'
      }}>
        {prediction.probability}%
      </div>
      
      <div style={{ marginBottom: '12px' }}>
        <div style={{
          color: 'white',
          fontWeight: 'bold',
          fontSize: '1rem',
          marginBottom: '4px'
        }}>
          {prediction.topic}
        </div>
        <div style={{
          color: '#cbd5e1',
          fontSize: '0.85rem',
          display: 'flex',
          alignItems: 'center',
          gap: '8px'
        }}>
          <span>📱 {prediction.platform}</span>
          <span>⏱️ {prediction.timeframe}</span>
        </div>
      </div>
      
      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: '12px',
        fontSize: '0.8rem'
      }}>
        <div>
          <div style={{ color: '#9ca3af' }}>Views Esperadas</div>
          <div style={{ color: 'white', fontWeight: 'bold' }}>
            {(prediction.expectedViews / 1000000).toFixed(1)}M
          </div>
        </div>
        <div>
          <div style={{ color: '#9ca3af' }}>Revenue Est.</div>
          <div style={{ color: '#10b981', fontWeight: 'bold' }}>
            ${prediction.revenue.toLocaleString()}
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div>
      {/* Header Analytics */}
      <div style={{
        ...styles.card,
        background: 'linear-gradient(135deg, #059669 0%, #10b981 100%)',
        marginBottom: '24px',
        border: 'none'
      }}>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <div>
            <h2 style={{
              fontSize: '1.5rem',
              fontWeight: 'bold',
              color: 'white',
              margin: '0 0 8px 0',
              display: 'flex',
              alignItems: 'center',
              gap: '12px'
            }}>
              <BarChart3 size={32} />
              Empire Analytics
              <div style={{
                padding: '4px 12px',
                background: 'rgba(255, 255, 255, 0.2)',
                borderRadius: '12px',
                fontSize: '0.75rem'
              }}>
                💰 ${totalRevenue.toLocaleString()}/mês
              </div>
            </h2>
            <div style={{ color: 'rgba(255, 255, 255, 0.8)', fontSize: '0.95rem' }}>
              📊 Crescimento médio: +{avgGrowth.toFixed(1)}% • {totalVideos} vídeos ativos
            </div>
          </div>
          
          <div style={{ display: 'flex', gap: '8px' }}>
            {['7d', '30d', '90d', '1y'].map((range) => (
              <button
                key={range}
                onClick={() => setTimeRange(range as any)}
                style={{
                  padding: '6px 12px',
                  background: timeRange === range 
                    ? 'rgba(255, 255, 255, 0.3)' 
                    : 'rgba(255, 255, 255, 0.1)',
                  border: 'none',
                  borderRadius: '6px',
                  color: 'white',
                  fontSize: '0.8rem',
                  cursor: 'pointer'
                }}
              >
                {range}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Navigation Metrics */}
      <div style={{
        display: 'flex',
        gap: '8px',
        marginBottom: '24px',
        background: '#1e293b',
        padding: '4px',
        borderRadius: '12px'
      }}>
        {[
          { id: 'revenue', label: 'Revenue', icon: <DollarSign size={16} /> },
          { id: 'performance', label: 'Performance', icon: <Target size={16} /> },
          { id: 'predictions', label: 'Previsões', icon: <Rocket size={16} /> }
        ].map((metric) => (
          <button
            key={metric.id}
            onClick={() => setSelectedMetric(metric.id as any)}
            style={{
              flex: 1,
              padding: '12px 16px',
              background: selectedMetric === metric.id ? '#3b82f6' : 'transparent',
              border: 'none',
              color: selectedMetric === metric.id ? 'white' : '#9ca3af',
              borderRadius: '8px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              transition: 'all 0.3s ease'
            }}
          >
            {metric.icon}
            {metric.label}
          </button>
        ))}
      </div>

      {/* Revenue Section */}
      {selectedMetric === 'revenue' && (
        <>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
            gap: '16px',
            marginBottom: '24px'
          }}>
            {revenueData.map((revenue, index) => (
              <RevenueCard key={index} data={revenue} />
            ))}
          </div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: '2fr 1fr',
            gap: '24px'
          }}>
            {/* Revenue Chart Placeholder */}
            <div style={styles.card}>
              <h3 style={{
                ...styles.cardTitle,
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}>
                <LineChart size={20} />
                📈 Evolução Revenue (30 dias)
              </h3>
              
              <div style={{
                height: '300px',
                background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
                borderRadius: '8px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                border: '1px solid #334155',
                position: 'relative'
              }}>
                <div style={{ textAlign: 'center', color: '#9ca3af' }}>
                  <TrendingUp size={48} style={{ marginBottom: '12px' }} />
                  <div style={{ fontSize: '1.1rem', marginBottom: '8px' }}>
                    Gráfico de Revenue
                  </div>
                  <div style={{ fontSize: '0.9rem' }}>
                    Crescimento consistente em todas as plataformas
                  </div>
                  
                  {/* Simulated trend line */}
                  <div style={{
                    position: 'absolute',
                    bottom: '20px',
                    left: '20px',
                    right: '20px',
                    height: '2px',
                    background: 'linear-gradient(90deg, #3b82f6 0%, #10b981 100%)',
                    borderRadius: '1px'
                  }} />
                </div>
              </div>
            </div>

            {/* Top Performers */}
            <div style={styles.card}>
              <h3 style={{
                ...styles.cardTitle,
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}>
                <Award size={20} />
                🏆 Top Performers
              </h3>
              
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {revenueData
                  .sort((a, b) => b.growth - a.growth)
                  .slice(0, 4)
                  .map((platform, index) => (
                    <div
                      key={index}
                      style={{
                        padding: '12px',
                        background: '#1e293b',
                        borderRadius: '8px',
                        border: '1px solid #475569',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center'
                      }}
                    >
                      <div>
                        <div style={{
                          color: 'white',
                          fontWeight: 'bold',
                          fontSize: '0.9rem',
                          marginBottom: '4px'
                        }}>
                          {platform.flag} {platform.platform}
                        </div>
                        <div style={{
                          color: '#9ca3af',
                          fontSize: '0.8rem'
                        }}>
                          ${platform.monthly.toLocaleString()}/mês
                        </div>
                      </div>
                      
                      <div style={{
                        background: '#10b981',
                        color: 'white',
                        padding: '4px 8px',
                        borderRadius: '6px',
                        fontSize: '0.8rem',
                        fontWeight: 'bold'
                      }}>
                        +{platform.growth.toFixed(1)}%
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          </div>
        </>
      )}

      {/* Performance Section */}
      {selectedMetric === 'performance' && (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
          gap: '16px'
        }}>
          {performanceMetrics.map((metric, index) => (
            <MetricCard key={index} metric={metric} />
          ))}
        </div>
      )}

      {/* Predictions Section */}
      {selectedMetric === 'predictions' && (
        <>
          <div style={{
            ...styles.card,
            background: 'linear-gradient(135deg, #7c3aed 0%, #3b82f6 100%)',
            marginBottom: '24px',
            border: 'none'
          }}>
            <h3 style={{
              color: 'white',
              fontSize: '1.2rem',
              fontWeight: 'bold',
              margin: '0 0 8px 0',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}>
              <Rocket size={24} />
              🔮 Previsões de Viral - Próximas 48h
            </h3>
            <div style={{ color: 'rgba(255, 255, 255, 0.8)', fontSize: '0.9rem' }}>
              IA analisou trends e prevê estes conteúdos com alto potencial viral
            </div>
          </div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
            gap: '16px',
            marginBottom: '24px'
          }}>
            {viralPredictions.map((prediction, index) => (
              <PredictionCard key={index} prediction={prediction} />
            ))}
          </div>

          <div style={{
            ...styles.card,
            background: '#0f172a',
            border: '1px solid #334155'
          }}>
            <h4 style={{
              color: '#cbd5e1',
              fontSize: '1rem',
              marginBottom: '16px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}>
              <Eye size={20} />
              📊 Análise de Mercado
            </h4>
            
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: '16px',
              fontSize: '0.9rem'
            }}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ color: '#3b82f6', fontSize: '1.5rem', fontWeight: 'bold' }}>
                  2.3M
                </div>
                <div style={{ color: '#9ca3af' }}>Views Potenciais</div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ color: '#10b981', fontSize: '1.5rem', fontWeight: 'bold' }}>
                  $10,009
                </div>
                <div style={{ color: '#9ca3af' }}>Revenue Estimado</div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ color: '#f59e0b', fontSize: '1.5rem', fontWeight: 'bold' }}>
                  85%
                </div>
                <div style={{ color: '#9ca3af' }}>Confiança IA</div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ color: '#8b5cf6', fontSize: '1.5rem', fontWeight: 'bold' }}>
                  24h
                </div>
                <div style={{ color: '#9ca3af' }}>Timeframe Médio</div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default EmpireAnalytics;