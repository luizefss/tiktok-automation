// Tipos expandidos para a Dashboard Suprema

export interface ContentSettings
{
  // Configurações básicas (mantidas)
  topic: string,
  script: string,
  subtitle_mode?: string,
  audio_duration: number,
  content_ai_model: 'claude' | 'chatgpt' | 'gemini',
  // Categoria do conteúdo (usada no ProductionStudio)
  category?: string;
  content_type: 'custom_message' | 'trending' | 'trending_research' | 'auto_viral';
  custom_topics: string[];
  message_categories: string[];
  tone: 'inspirational' | 'mysterious' | 'dramatic' | 'motivational' | 'serious' | 'enthusiastic';
  image_style: 'cinematic' | 'realistic' | 'dramatic' | 'futuristic' | 'artistic';
  color_palette: 'vibrant' | 'dark' | 'neon' | 'gold' | 'blue' | 'warm' | 'cold';
  animation_type: 'parallax' | 'zoom' | 'slide' | 'fade' | 'dynamic';
  voice_emotion: 'neutral' | 'enthusiastic' | 'dramatic' | 'mysterious' | 'calm';
  speaking_speed: number;
  use_topmedia_ai: boolean;
  // Música de fundo: categoria e volume (compatível com render backend)
  background_music?: string; // ex.: 'upbeat' | 'chill' | 'energetic' | 'ambient'
  background_music_volume?: number;
  video_duration: number;
  transitions: 'smooth' | 'dynamic' | 'cut' | 'fade';
  text_overlay: boolean;
  custom_prompt_roteiro: string;
  custom_prompt_imagem: string;
  custom_prompt_audio: string;

  // Propriedades para ProductionStudio
  voice_id?: string;
  music_category?: string;
  background_music_category?: string;
  video_effects?: string[];
  visual_style?: string;
  visual_color_palette?: string;
  visual_lighting_mood?: string;
  visual_camera_angle?: string;
  visual_prompts?: any[];
  // Textos consolidados dos prompts, usados para manter no Step 1 e persistir
  visual_prompts_text?: string;
  leonardo_prompts?: any[];
  leonardo_prompts_text?: string;

  // Configurações de áudio TTS
  voice_style?: |'default'|'mulher_nova_carioca' | 'homem_maduro_paulista' | 'mulher_madura_mineira' | 'homem_jovem_nordestino';
  emotion_style?: 'neutro' | 'enthusiastic' | 'mysterious' | 'calm' | 'happy' | 'dramatic';
  audio_file?: string;
  preview_audio_file?: string;
  
  // Configurações de imagens geradas
  generated_images?: any[];
  // Seletor de provedor de imagens (frontend → backend)
  image_provider?: 'imagen' | 'openai' | 'leonardo' | 'hybrid'|'dalle';

  // Configurações de voz expandidas
  voice_profile?: string;
  voice_pitch?: number;
  voice_volume_gain?: number;
  voice_accent?: string;
  // Campos opcionais adicionais usados em renderização completa
  elevenlabs_voice?: string;
  voice_stability?: number;
  voice_clarity?: number;
  pause_duration?: 'short' | 'normal' | 'long' | 'very_long';
  emphasis_level?: 'reduced' | 'moderate' | 'strong';
  
  // Features avançadas de áudio
  auto_emotion_detection?: boolean;
  voice_cloning?: boolean;
  multi_speaker?: boolean;
  ai_voice_enhancement?: boolean;
  global_voice_sync?: boolean;
  
  // Configurações de equalizador
  voice_eq_bass?: number;
  voice_eq_mid?: number;
  voice_eq_treble?: number;
  voice_eq_presence?: number;
  
  // Efeitos de áudio
  voice_reverb?: 'none' | 'room' | 'hall' | 'cathedral' | 'cave' | 'underwater';
  voice_compression?: number;
  
  // Otimização automática
  auto_platform_optimization?: boolean;
  
  // Configurações de estúdio virtual
  real_time_monitoring?: boolean;
  virtual_microphone?: 'studio_condenser' | 'dynamic_vocal' | 'ribbon_vintage' | 'podcast_broadcast' | 'gaming_headset' | 'phone_quality';
  noise_suppression?: number;
  noise_gate?: number;
  studio_preset?: 'podcast' | 'audiobook' | 'commercial' | 'documentary';

  // Novas configurações globais
  target_platforms?: string[];
  target_languages?: string[];
  ai_competition_mode?: boolean;
  auto_research_trending?: boolean;
  generate_micro_videos?: boolean;
  video_effects_enabled?: boolean;
  // Estilos de legenda suportados no compositor
  subtitle_style?: 'moderno' | 'neon' | 'neon_yellow' | 'elegante' | 'tiktok' | 'neon_glow' | 'bold_impact' | 'retro_gaming' | 'minimalist';
  revenue_optimization?: boolean;
  
  // Campos para controle de interface
  last_audio_model?: string;
  selected_audio_model?: string;
  
  // Configurações Leonardo AI
  leonardo_motion?: string;
  motion_strength?: number;

  // Configurações Veo AI
  veo_motion_preset?: string;
  veo_custom_prompt?: string;
  veo_duration_seconds?: number;
  veo_aspect_ratio?: string;

  // Renderização de cenas
  scene_duration?: number;
  music_volume?: number;
  // Pacing de cortes por imagem (suportado no backend)
  min_cut?: number;
  max_cut?: number;
}

// Configurações globais do sistema
export interface GlobalSettings
{
  autoMode: boolean;
  multiPlatform: boolean;
  multiLanguage: boolean;
  aiCompetition: boolean;
  revenueTracking: boolean;
}

// Configuração de plataforma
export interface PlatformConfig
{
  id: string;
  name: string;
  aspectRatio: string;
  maxDuration: number;
  recommended: {
    duration: number;
    style: string;
    pace: string;
  };
}

// Estatísticas de IA
export interface AIStats
{
  name: string;
  model: 'chatgpt' | 'claude' | 'gemini';
  wins: number;
  totalBattles: number;
  avgRetention: number;
  specialty: string;
  strengthEmoji: string;
  color: string;
  performance: {
    hooks: number;
    storytelling: number;
    viral_potential: number;
    cultural_adaptation: number;
  };
}

// Histórico de batalhas entre IAs
export interface BattleHistory
{
  timestamp: string;
  winner: string;
  topic: string;
  votes: number;
  retention: number;
}

// Dados de revenue por plataforma
export interface RevenueData
{
  platform: string;
  monthly: number;
  growth: number;
  cpm: number;
  videos: number;
  flag: string;
}

// Métricas de performance
export interface PerformanceMetric
{
  metric: string;
  current: number;
  target: number;
  trend: number;
  status: 'excellent' | 'good' | 'warning' | 'critical';
}

// Previsões de viral
export interface ViralPrediction
{
  topic: string;
  platform: string;
  probability: number;
  expectedViews: number;
  revenue: number;
  timeframe: string;
}

// Métricas do sistema em tempo real
export interface SystemMetrics
{
  aiAccuracy: number;
  viralRate: number;
  platformReach: number;
  revenueGrowth: number;
  contentQuality: number;
}

// Item trending
export interface TrendingTopic
{
  topic: string;
  platform: string;
  growth: number;
  potential: number;
  category: string;
}

// Item trending detalhado
export interface TrendingItem
{
  id: string;
  topic: string;
  platform: string;
  category: string;
  growth: number;
  volume: number;
  viralPotential: number;
  hashtags: string[];
  timeframe: string;
  region: string;
  status: 'hot' | 'rising' | 'stable' | 'declining';
}

// Estatísticas de plataforma
export interface PlatformStats
{
  platform: string;
  icon: React.ReactNode;
  color: string;
  trends: number;
  totalVolume: number;
}

// Próximas ações do sistema
export interface NextAction
{
  action: string;
  eta: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
}

// Opções de voz
export interface VoiceOption
{
  id: string;
  name: string;
  language: string;
  style: string;
  gender: string;
  sample: string;
}

// Opções de efeito
export interface EffectOption
{
  id: string;
  name: string;
  description: string;
  preview: string;
  intensity: number;
}

// Configuração de aba
export interface TabConfig
{
  id: 'command' | 'ai-battle' | 'studio' | 'analytics';
  name: string;
  icon: React.ReactNode;
  description: string;
}

// Prompts customizados por IA
export interface CustomPrompts
{
  roteiro: {
    chatgpt: string;
    claude: string;
    gemini: string;
  };
  imagem: {
    chatgpt: string;
    claude: string;
    gemini: string;
  };
  audio: {
    chatgpt: string;
    claude: string;
    gemini: string;
  };
}

// Configuração de música
export interface MusicCategory
{
  id: string;
  name: string;
  description: string;
}

// Estilo de legenda
export interface SubtitleStyle
{
  id: string;
  name: string;
  preview: string;
  color: string;
}

// Estado do vídeo expandido
export interface VideoState
{
  status: 'queue' | 'generating' | 'processing' | 'ready' | 'uploaded' | 'failed';
  progress?: number;
  platform?: string;
  estimatedCompletion?: string;
  metadata?: {
    aiUsed?: string;
    generationTime?: number;
    viralScore?: number;
    targetAudience?: string;
  };
}

// Análise de trending expandida
export interface TrendingAnalysis
{
  topic: string;
  platforms: string[];
  totalVolume: number;
  growthRate: number;
  sentimentScore: number;
  demographicTargets: string[];
  competitionLevel: number;
  monetizationPotential: number;
  recommendations: string[];
}

// Configuração de nicho
export interface NicheConfig
{
  id: string;
  name: string;
  description: string;
  emoji: string;
  targetAudience: string[];
  avgPerformance: number;
  competitionLevel: 'low' | 'medium' | 'high';
  monetizationRate: number;
  platforms: string[];
}

// Analytics de canal
export interface ChannelAnalytics
{
  channelId: string;
  platform: string;
  subscribers: number;
  totalViews: number;
  avgViewsPerVideo: number;
  engagementRate: number;
  monthlyRevenue: number;
  topVideos: Array<{
    title: string;
    views: number;
    revenue: number;
    viralScore: number;
  }>;
}

// Configuração de automação
export interface AutomationConfig
{
  enabled: boolean;
  frequency: number; // horas entre gerações
  platforms: string[];
  contentTypes: string[];
  qualityThreshold: number;
  autoPost: boolean;
  timeSlots: string[];
}

// Status expandido do sistema
export interface ExtendedStats
{
  // Stats básicas (mantidas da interface original)
  total_views?: string | number;
  followers?: string | number;
  automation_running?: boolean;
  pipeline_running?: boolean;

  // Novas stats
  aiAccuracy?: number;
  viralRate?: number;
  platformReach?: number;
  revenueGrowth?: number;
  contentQuality?: number;
  systemHealth?: 'excellent' | 'good' | 'warning' | 'critical';
  lastGeneration?: string;
  nextScheduled?: string;
  totalRevenue?: number;
  monthlyGrowth?: number;
}


export interface GlobalSettings
{
  autoMode: boolean;
  multiPlatform: boolean;
  multiLanguage: boolean;
  aiCompetition: boolean;
  revenueTracking: boolean;
}

export interface AIStats
{
  name: string;
  model: 'chatgpt' | 'claude' | 'gemini';
  wins: number;
  totalBattles: number;
  avgRetention: number;
  specialty: string;
  strengthEmoji: string;
  color: string;
  performance: {
    hooks: number;
    storytelling: number;
    viral_potential: number;
    cultural_adaptation: number;
  };
}

export interface RevenueData
{
  platform: string;
  monthly: number;
  growth: number;
  cpm: number;
  videos: number;
  flag: string;
}

export interface TrendingItem
{
  id: string;
  topic: string;
  platform: string;
  category: string;
  growth: number;
  volume: number;
  viralPotential: number;
  hashtags: string[];
  timeframe: string;
  region: string;
  status: 'hot' | 'rising' | 'stable' | 'declining';
}

export interface ViralPrediction
{
  topic: string;
  platform: string;
  probability: number;
  expectedViews: number;
  revenue: number;
  timeframe: string;
}

export interface SystemMetrics
{
  aiAccuracy: number;
  viralRate: number;
  platformReach: number;
  revenueGrowth: number;
  contentQuality: number;
}

export interface ExtendedStats
{
  total_views?: string | number;
  followers?: string | number;
  automation_running?: boolean;
  pipeline_running?: boolean;
  aiAccuracy?: number;
  viralRate?: number;
  platformReach?: number;
  revenueGrowth?: number;
  contentQuality?: number;
  systemHealth?: 'excellent' | 'good' | 'warning' | 'critical';
  lastGeneration?: string;
  nextScheduled?: string;
  totalRevenue?: number;
  monthlyGrowth?: number;
}

// Exportações para compatibilidade (mantidas)
export * from '../services/api';