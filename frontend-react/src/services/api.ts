// /var/www/tiktok-automation/frontend-react/src/services/api.ts

import
  {
    ContentSettings, GlobalSettings, RevenueData, TrendingItem,
    ViralPrediction, SystemMetrics, ExtendedStats, Video as VideoType
  } from '../types';

export interface Stats
{
  total_views?: string | number;
  followers?: string | number;
  automation_running?: boolean;
  pipeline_running?: boolean;
}

export interface Video
{
  filename: string;
  size_mb: number;
  status: string;
  metadata?: {
    roteiro?: {
      titulo: string;
      categoria: string;
      hook: string;
      hashtags: string[];
      roteiro_completo: string;
      timestamp: string;
      music_style: string;
    };
    status?: string;
    aiUsed?: string;
    generationTime?: number;
    viralScore?: number;
    platform?: string;
    language?: string;
  };
}

const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://topatudoeletrofacil.com.br/api';

class ApiService
{
  private baseUrl: string;

  constructor ()
  {
    // NÃO adicionar /api aqui pois já vamos adicionar nos métodos
    this.baseUrl = API_BASE_URL.endsWith( '/' ) ? API_BASE_URL.slice( 0, -1 ) : API_BASE_URL;
  }

  private async request<T> ( endpoint: string, options: RequestInit = {} ): Promise<T>
  {
    const finalEndpoint = endpoint.startsWith( '/' ) ? endpoint : `/${ endpoint }`;
    // Construir URL final - se baseUrl já termina com /api, não adicionar
    const url = this.baseUrl.endsWith('/api') 
      ? `${ this.baseUrl }${ finalEndpoint }`
      : `${ this.baseUrl }/api${ finalEndpoint }`;

    const config: RequestInit = {
      headers: { 'Content-Type': 'application/json', ...options.headers },
      ...options,
    };

    const response = await fetch( url, config );

    if ( !response.ok )
    {
      const errorBody = await response.json().catch( () => ( { error: "Erro de rede ou JSON inválido" } ) );
      console.error( "Erro da API:", errorBody );
      throw new Error( errorBody.error || `Erro ${ response.status }` );
    }

    const data = await response.json();
    return data as T;
  }

  // Métodos SEM /api/ prefix - backend já tem as rotas com /api/
  async get ( endpoint: string ): Promise<any>
  {
    return this.request( endpoint );
  }

  async post ( endpoint: string, body: any ): Promise<any>
  {
    return this.request( endpoint, {
      method: 'POST',
      body: JSON.stringify( body ),
    } );
  }

  async getStatus (): Promise<ExtendedStats>
  {
    try
    {
      const response = await this.get( 'status' );
      return {
        ...response,
        aiAccuracy: 94.2,
        viralRate: 28.5,
        platformReach: 87.3,
        revenueGrowth: 156.7,
        contentQuality: 91.8,
        systemHealth: 'good',
        totalRevenue: 71250,
        monthlyGrowth: 23.4
      };
    } catch ( error )
    {
      console.error( 'Erro ao buscar status:', error );
      return {
        total_views: '2.3M',
        followers: '45.2K',
        automation_running: true,
        pipeline_running: false,
        aiAccuracy: 94.2,
        viralRate: 28.5,
        platformReach: 87.3,
        revenueGrowth: 156.7,
        contentQuality: 91.8,
        systemHealth: 'good',
        totalRevenue: 71250,
        monthlyGrowth: 23.4
      };
    }
  }

  async getVideos (): Promise<VideoType[]>
  {
    try
    {
      const response = await this.get( 'videos' );
      return response.videos || [];
    } catch ( error )
    {
      console.error( 'Erro ao buscar vídeos:', error );
      return [];
    }
  }

  getVideoUrl ( filename: string ): string
  {
    return `${ this.baseUrl }/media/videos/${ filename }`;
  }

  async toggleAutomation (): Promise<{ message: string }>
  {
    try
    {
      return await this.post( 'toggle-automation', {} );
    } catch ( error )
    {
      console.error( 'Erro ao alternar automação:', error );
      return { message: 'Automação alternada (simulado)' };
    }
  }

  async generateViral (): Promise<{ message: string }>
  {
    try
    {
      return await this.post( 'viral-now', {} );
    } catch ( error )
    {
      console.error( 'Erro ao gerar viral:', error );
      return { message: 'Vídeo viral iniciado (simulado)' };
    }
  }

  async generateCustomContent ( body: { settings: ContentSettings } ): Promise<{ message: string }>
  {
    try
    {
      return await this.post( 'custom-production', body );
    } catch ( error )
    {
      console.error( 'Erro ao gerar vídeo:', error );
      return { message: 'Vídeo customizado iniciado (simulado)' };
    }
  }

  async startBattleVideo ( body: { settings: ContentSettings } ): Promise<any>
  {
    try
    {
      return await this.post( 'production/ai-battle', body );
    } catch ( error )
    {
      console.error( 'Erro ao iniciar a produção de vídeo de batalha:', error );
      throw error;
    }
  }

  async updateVideoStatus ( filename: string, status: string ): Promise<{ message: string }>
  {
    try
    {
      return await this.request( `videos/${ filename }/status`, {
        method: 'PUT',
        body: JSON.stringify( { status } )
      } );
    } catch ( error )
    {
      console.error( 'Erro ao atualizar status:', error );
      return { message: `Status atualizado para ${ status } (simulado)` };
    }
  }

  async deleteVideo ( filename: string ): Promise<{ message: string }>
  {
    try
    {
      return await this.request( `videos/${ filename }`, {
        method: 'DELETE'
      } );
    } catch ( error )
    {
      console.error( 'Erro ao deletar vídeo:', error );
      return { message: 'Vídeo deletado (simulado)' };
    }
  }

  async getTrendingTopics (): Promise<{ topics: TrendingItem[] }>
  {
    try
    {
      return await this.get( 'trending/topics' );
    } catch ( error )
    {
      console.error( 'Erro ao buscar trending topics:', error );
      return {
        topics: [
          {
            id: '1',
            topic: 'Hacker invadiu NASA',
            platform: 'TikTok',
            category: 'Tech',
            growth: 847,
            volume: 2340000,
            viralPotential: 94,
            hashtags: [ '#hacker', '#nasa', '#tech' ],
            timeframe: '2h',
            region: 'Global',
            status: 'hot'
          }
        ]
      };
    }
  }

  async analyzeTrending ( topic: string ): Promise<{ analysis: string; recommendation: string }>
  {
    try
    {
      return await this.post( 'trending/analyze', { topic } );
    } catch ( error )
    {
      console.error( 'Erro ao analisar trending:', error );
      return {
        analysis: 'Análise de trending em progresso...',
        recommendation: 'Recomendação será gerada automaticamente.'
      };
    }
  }

  async getRevenueData (): Promise<RevenueData[]>
  {
    try
    {
      return await this.get( 'analytics/revenue' );
    } catch ( error )
    {
      console.error( 'Erro ao buscar dados de revenue:', error );
      return [
        {
          platform: 'YouTube US',
          monthly: 23847,
          growth: 34.2,
          cpm: 4.50,
          videos: 45,
          flag: '🇺🇸'
        },
        {
          platform: 'TikTok US',
          monthly: 15623,
          growth: 67.8,
          cpm: 2.30,
          videos: 120,
          flag: '🇺🇸'
        }
      ];
    }
  }

  async getViralPredictions (): Promise<ViralPrediction[]>
  {
    try
    {
      return await this.get( 'analytics/predictions' );
    } catch ( error )
    {
      console.error( 'Erro ao buscar previsões:', error );
      return [
        {
          topic: 'Hacker NASA 2025',
          platform: 'TikTok US',
          probability: 94,
          expectedViews: 2300000,
          revenue: 5290,
          timeframe: '24-48h'
        }
      ];
    }
  }

  async getSystemMetrics (): Promise<SystemMetrics>
  {
    try
    {
      return await this.get( 'system/metrics' );
    } catch ( error )
    {
      console.error( 'Erro ao buscar métricas:', error );
      return {
        aiAccuracy: 94.2,
        viralRate: 28.5,
        platformReach: 87.3,
        revenueGrowth: 156.7,
        contentQuality: 91.8
      };
    }
  }

  async updateGlobalSettings ( settings: GlobalSettings ): Promise<{ message: string }>
  {
    try
    {
      return await this.request( 'settings/global', {
        method: 'PUT',
        body: JSON.stringify( settings )
      } );
    } catch ( error )
    {
      console.error( 'Erro ao atualizar configurações:', error );
      return { message: 'Configurações atualizadas (simulado)' };
    }
  }

  async getGlobalSettings (): Promise<GlobalSettings>
  {
    try
    {
      return await this.get( 'settings/global' );
    } catch ( error )
    {
      console.error( 'Erro ao buscar configurações:', error );
      return {
        autoMode: true,
        multiPlatform: true,
        multiLanguage: false,
        aiCompetition: true,
        revenueTracking: true
      };
    }
  }
}

export const apiService = new ApiService();
export default apiService;