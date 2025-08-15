// /var/www/tiktok-automation/frontend-react/src/components/ProductionStudio.tsx

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { ContentSettings } from '../types';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import Stack from '@mui/material/Stack';
// Removidos imports não utilizados
import CircularProgress from '@mui/material/CircularProgress';
import LinearProgress from '@mui/material/LinearProgress';
import Alert from '@mui/material/Alert';
import AutoFixHighIcon from '@mui/icons-material/AutoFixHigh';
import GroupsIcon from '@mui/icons-material/Groups';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import MovieIcon from '@mui/icons-material/Movie';
// Ícones não usados removidos para evitar warnings

// Usar a mesma configuração do apiService
const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://topatudoeletrofacil.com.br/api';

// Configurações de rede seguras (evita sobrecarga e travamentos)
const DEFAULT_TIMEOUT_MS = 110_000; // Hostinger/Nginx costuma fechar > 120s
const DEFAULT_RETRIES = 2; // tenta novamente erros transitórios

// Pequena ajuda para aguardar com jitter (backoff exponencial)
const sleep = (ms: number) => new Promise(res => setTimeout(res, ms));

// Fetch com timeout, retry e abort (mitiga requests presos que derrubam o server)
async function safeFetch(
  url: string,
  options: RequestInit & { timeoutMs?: number } = {},
  retryCfg: { retries?: number; retryDelayBaseMs?: number } = {}
): Promise<Response> {
  const { timeoutMs = DEFAULT_TIMEOUT_MS, ...rest } = options;
  const { retries = DEFAULT_RETRIES, retryDelayBaseMs = 800 } = retryCfg;

  for (let attempt = 0; attempt <= retries; attempt++) {
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), timeoutMs);
    try {
      const resp = await fetch(url, { ...rest, signal: controller.signal, keepalive: true });
      clearTimeout(id);
      // Repetir em 502/503/504 ou 429
      if ([429, 502, 503, 504].includes(resp.status) && attempt < retries) {
        const wait = retryDelayBaseMs * Math.pow(2, attempt) + Math.floor(Math.random() * 250);
        await sleep(wait);
        continue;
      }
      return resp;
    } catch (err: any) {
      clearTimeout(id);
      const isAbort = err?.name === 'AbortError';
      if (attempt < retries) {
        const wait = retryDelayBaseMs * Math.pow(2, attempt) + Math.floor(Math.random() * 250);
        await sleep(wait);
        continue;
      }
      // Rejogar último erro
      throw isAbort ? new Error('Tempo limite atingido. Tente novamente.') : err;
    }
  }
  // Nunca deve chegar aqui
  throw new Error('Falha de rede inesperada');
}

// Limitador de concorrência removido (não utilizado no fluxo atual)

// Função para construir URLs da API corretamente
const buildApiUrl = (endpoint: string) => {
  const finalEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  // Se a URL já termina com /api, não adiciona /api extra
  const url = API_BASE_URL.endsWith('/api') 
    ? `${API_BASE_URL}${finalEndpoint}`
    : `${API_BASE_URL}/api${finalEndpoint}`;
  return url;
};

// Função para construir URLs de mídia corretamente
const buildMediaUrl = (mediaPath: string) => {
  if (!mediaPath) return '';
  // Se já for URL completa, retorna como está
  if (/^https?:\/\//i.test(mediaPath)) return mediaPath;
  // Normaliza caminhos como "/media/...", "media/..." ou com barras extras
  const cleanPath = mediaPath
    .replace(/^\/+/, '')            // remove barras iniciais
    .replace(/^media\//i, '')       // remove prefixo media/
    .replace(/^\/+media\//i, '')   // remove /media/ se ainda houver
    .replace(/^\/+/, '');           // normaliza novamente

  if (API_BASE_URL.includes('/api')) {
    // Produção: usa /media/ para servir arquivos diretamente
    return `https://topatudoeletrofacil.com.br/media/${cleanPath}`;
  } else {
    // Desenvolvimento: usa o backend local
    return `${API_BASE_URL}/media/${cleanPath}`;
  }
};

// Função para limpar tags de direção do script antes do TTS
const cleanScriptForTTS = (script: string): string => {
  // Remove tags como [GANCHO], [EXPLICAÇÃO CONTEXTO], etc.
  return script
    .replace(/\[([^\]]+)\]/g, '') // Remove tudo entre colchetes
    .replace(/\s+/g, ' ') // Remove espaços múltiplos
    .trim(); // Remove espaços no início e fim
};

// Componente simplificado do Step 2: 3 opções de voz com preview de 4s e geração completa
interface AudioSimpleStepProps {
  script: string;
  onSelectComplete: (result: { audio_url: string; model?: string; voice_profile?: string; duration?: number }) => void;
  buildApiUrl: (endpoint: string) => string;
  safeFetch: (
    url: string,
    options?: RequestInit & { timeoutMs?: number },
    retryCfg?: { retries?: number; retryDelayBaseMs?: number }
  ) => Promise<Response>;
  buildMediaUrl: (mediaPath: string) => string;
  cleanScriptForTTS: (script: string) => string;
}

const AudioSimpleStep: React.FC<AudioSimpleStepProps> = ({
  script,
  onSelectComplete,
  buildApiUrl,
  safeFetch,
  buildMediaUrl,
  cleanScriptForTTS
}) => {
  const [previewUrls, setPreviewUrls] = useState<Record<string, string>>({});
  const [loadingPreview, setLoadingPreview] = useState<Record<string, boolean>>({});
  const [loadingFull, setLoadingFull] = useState<Record<string, boolean>>({});
  const [err, setErr] = useState<string | null>(null);

  const options = [
    { id: 'google_m', title: 'Google (Masculina)', provider: 'google' as const, voice_profile: 'male-professional' },
    { id: 'google_f', title: 'Google (Feminina)', provider: 'google' as const, voice_profile: 'female-professional' },
    { id: 'eleven_victor', title: 'ElevenLabs (Victor)', provider: 'elevenlabs' as const, voice_profile: 'victor-power' },
  ];

  const getPreviewText = (full: string) => {
    const clean = cleanScriptForTTS(full);
    const maxChars = 70; // ~4s
    let text = clean.substring(0, maxChars);
    const lastEnd = Math.max(text.lastIndexOf('.'), text.lastIndexOf('!'), text.lastIndexOf('?'));
    if (lastEnd > 20) text = text.substring(0, lastEnd + 1);
    else {
      const lastSpace = text.lastIndexOf(' ');
      if (lastSpace > 20) text = text.substring(0, lastSpace) + '...';
    }
    return text;
  };

  const handlePreview = async (optId: string, provider: 'google' | 'elevenlabs', voice_profile: string) => {
    if (!script) return;
    setErr(null);
    setLoadingPreview(prev => ({ ...prev, [optId]: true }));
    try {
      const previewText = getPreviewText(script);
      let resp: Response;
      if (provider === 'google') {
        resp = await safeFetch(buildApiUrl('production/generate-google-tts'), {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: previewText, voice_profile, speed: 1.0 })
        });
      } else {
        resp = await safeFetch(buildApiUrl('production/generate-elevenlabs-audio'), {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: previewText, voice_profile })
        });
      }
      if (!resp.ok) throw new Error(`Erro ${provider} preview: ${resp.status}`);
      const data = await resp.json();
      const path = data.audio_url || data.audio_path;
      if (!data.success || !path) throw new Error(data.error || 'Falha ao gerar preview');
      setPreviewUrls(prev => ({ ...prev, [optId]: path }));
    } catch (e: any) {
      setErr(e?.message || 'Erro ao gerar preview');
    } finally {
      setLoadingPreview(prev => ({ ...prev, [optId]: false }));
    }
  };

  const handleFull = async (optId: string, provider: 'google' | 'elevenlabs', voice_profile: string) => {
    if (!script) return;
    setErr(null);
    setLoadingFull(prev => ({ ...prev, [optId]: true }));
    try {
      let resp: Response;
      if (provider === 'google') {
        resp = await safeFetch(buildApiUrl('production/generate-google-tts'), {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: cleanScriptForTTS(script), voice_profile, speed: 1.0 })
        });
      } else {
        resp = await safeFetch(buildApiUrl('production/generate-elevenlabs-audio'), {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: cleanScriptForTTS(script), voice_profile })
        });
      }
      if (!resp.ok) throw new Error(`Erro ${provider} completo: ${resp.status}`);
      const data = await resp.json();
      const path = data.audio_url || data.audio_path;
      if (!data.success || !path) throw new Error(data.error || 'Falha ao gerar áudio completo');
      onSelectComplete({ audio_url: path, model: provider === 'google' ? 'google' : 'elevenlabs', voice_profile, duration: data.duration });
    } catch (e: any) {
      setErr(e?.message || 'Erro ao gerar áudio completo');
    } finally {
      setLoadingFull(prev => ({ ...prev, [optId]: false }));
    }
  };

  return (
    <Box>
      {!script && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          ❌ Nenhum roteiro disponível. Gere o roteiro no Step 1 primeiro.
        </Alert>
      )}
      <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 2 }}>
        {options.map(opt => (
          <Box key={opt.id} sx={{ p: 2, border: '1px solid #444', borderRadius: 2, backgroundColor: '#0a0a0f' }}>
            <Typography variant="subtitle1" sx={{ color: '#ffd700', fontWeight: 'bold', mb: 1 }}>
              {opt.title}
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 1 }}>
              <Button
                variant="outlined"
                size="small"
                onClick={() => handlePreview(opt.id, opt.provider, opt.voice_profile)}
                disabled={!script || !!loadingPreview[opt.id]}
                sx={{ borderColor: '#ffd700', color: '#ffd700' }}
              >
                {loadingPreview[opt.id] ? <CircularProgress size={16} /> : 'Preview 4s'}
              </Button>
              <Button
                variant="contained"
                size="small"
                onClick={() => handleFull(opt.id, opt.provider, opt.voice_profile)}
                disabled={!script || !!loadingFull[opt.id]}
                sx={{ backgroundColor: '#ffd700', color: '#000', fontWeight: 'bold' }}
              >
                {loadingFull[opt.id] ? <CircularProgress size={16} /> : 'Gerar completo'}
              </Button>
            </Box>
            {previewUrls[opt.id] && (
              <audio controls style={{ width: '100%' }} key={`prev-${opt.id}-${previewUrls[opt.id]}`}>
                <source src={`${buildMediaUrl(previewUrls[opt.id])}?t=${Date.now()}`} type="audio/mp3" />
              </audio>
            )}
          </Box>
        ))}
      </Box>
      {err && <Alert severity="error" sx={{ mt: 2 }}>{err}</Alert>}
      <Alert severity="info" sx={{ mt: 2 }}>
        💡 Dica: Durante testes, prefira as vozes Google para economizar créditos. ElevenLabs fica disponível como opção premium.
      </Alert>
    </Box>
  );
};

interface ProductionStudioProps
{
  contentSettings: ContentSettings;
  onSettingsChange: ( settings: ContentSettings ) => void;
  onGenerateCustom: ( settings: ContentSettings ) => void;
}

const ProductionStudio: React.FC<ProductionStudioProps> = ( {
  contentSettings,
  onSettingsChange,
  onGenerateCustom
} ) =>
{
  // Estados do workflow sequencial
  const [ currentStep, setCurrentStep ] = useState( 1 );
  const [ stepCompleted, setStepCompleted ] = useState<boolean[]>( [false, false, false, false, false, false] );
  
  const [ isGenerating, setIsGenerating ] = useState( false );
  // Step 2 simplificado não usa os estados antigos de modo rápido
  const [ generationProgress, setGenerationProgress ] = useState( 0 );
  const [ error, setError ] = useState<string | null>( null );

  // Estados da batalha de IAs
  const [ battleResults, setBattleResults ] = useState<any[]>( [] );
  const [ showBattleResults, setShowBattleResults ] = useState( false );
  const [ selectedAI, setSelectedAI ] = useState<string>( '' );
  const [ videoDuration, setVideoDuration ] = useState<number>( 60 ); // segundos
  const [ expandedCard, setExpandedCard ] = useState<number | null>( null ); // Card expandido
  
  // Estados para imagens e vídeo
  const [ generatedImages, setGeneratedImages ] = useState<any[]>( [] );
  const [ replacingIndex, setReplacingIndex ] = useState<number | null>(null);
  const [ replacePrompt, setReplacePrompt ] = useState<string>("");
  const [ videoPreview, setVideoPreview ] = useState<string | null>( null );

  // Estados antigos de processamento local removidos do fluxo simplificado
  
  // Estados para animação (consolidados no render completo)
  const [optimizedPrompts, setOptimizedPrompts] = useState<any[]>([]);
  const optimizedPromptsRef = useRef<string[]>([]);
  const [isOptimizingPrompts, setIsOptimizingPrompts] = useState(false);
  
  // Estados para renderização completa de vídeo
  const [isRenderingVideo, setIsRenderingVideo] = useState(false);
  
  // Web Audio API não utilizada no modo simplificado

  // Workflow steps definition
  const workflowSteps = [
    { id: 1, title: 'Roteiro', icon: '📝', description: 'Gerar o roteiro do vídeo' },
    { id: 2, title: 'Áudio', icon: '🎤', description: 'Configurar narração e voz' },
    { id: 3, title: 'Visual', icon: '🎨', description: 'Escolher estilo visual e imagens' },
    { id: 4, title: 'Efeitos', icon: '✨', description: 'Adicionar efeitos e transições' },
    { id: 5, title: 'Multi-Plataforma', icon: '🎯', description: 'Configurar plataformas de destino' },
    { id: 6, title: 'Previsualização', icon: '👁️', description: 'Revisar e finalizar' }
  ];

  // Workflow control functions
  const completeStep = ( stepIndex: number ) =>
  {
    const newCompleted = [ ...stepCompleted ];
    newCompleted[ stepIndex - 1 ] = true;
    setStepCompleted( newCompleted );
    if ( stepIndex < 6 )
    {
      setCurrentStep( stepIndex + 1 );
    }
  };

  const markStepAsCompleted = ( stepIndex: number ) =>
  {
    const newCompleted = [ ...stepCompleted ];
    newCompleted[ stepIndex - 1 ] = true;
    setStepCompleted( newCompleted );
    // Não avança automaticamente o step
  };

  const goToStep = ( stepIndex: number ) =>
  {
    if ( stepIndex === 1 || stepCompleted[ stepIndex - 2 ] )
    {
      setCurrentStep( stepIndex );
    }
  };

  // Função para obter dados do script selecionado (para exibir prompts)
  const getSelectedScriptData = () => {
    if (battleResults.length > 0 && selectedAI) {
      const selected = battleResults.find(result => result.name === selectedAI);
      return selected?.script || null;
    }
    return null;
  };

  const isStepAccessible = ( stepIndex: number ) =>
  {
    return stepIndex === 1 || stepCompleted[ stepIndex - 2 ];
  };

  const canCompleteCurrentStep = () =>
  {
    switch ( currentStep )
    {
      case 1: 
        return contentSettings.script && contentSettings.script.trim().length > 50;
      case 2: 
  // Novo fluxo: Step 2 conclui quando houver áudio completo gerado
  return !!(contentSettings.script && contentSettings.audio_file);
      case 3: 
        return contentSettings.visual_style;
      case 4: 
        return contentSettings.subtitle_style && contentSettings.transitions;
      case 5: 
        return contentSettings.target_platforms && contentSettings.target_platforms.length > 0;
      case 6: 
        return true;
      default: 
        return false;
    }
  };

  // Reidratar estado a partir do localStorage para não perder o progresso
  useEffect(() => {
    try {
      const saved = localStorage.getItem('production_studio_state');
      if (saved) {
        const parsed = JSON.parse(saved);
        // Reaplicar apenas campos conhecidos
        onSettingsChange({ ...contentSettings, ...parsed.settings });
        if (Array.isArray(parsed.generatedImages)) setGeneratedImages(parsed.generatedImages);
        if (typeof parsed.videoPreview === 'string') setVideoPreview(parsed.videoPreview);
        if (Array.isArray(parsed.stepCompleted)) setStepCompleted(parsed.stepCompleted);
      }
    } catch (e) {
      console.warn('⚠️ Falha ao reidratar estado:', e);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Aviso ao usuário se tentar recarregar/fechar com progresso
  useEffect(() => {
    const handler = (e: BeforeUnloadEvent) => {
      const hasProgress = Boolean(
        contentSettings.script ||
        generatedImages.length ||
        contentSettings.audio_file ||
        videoPreview
      );
      if (hasProgress) {
        e.preventDefault();
        e.returnValue = '';
      }
    };
    window.addEventListener('beforeunload', handler);
    return () => window.removeEventListener('beforeunload', handler);
  }, [contentSettings.script, contentSettings.audio_file, generatedImages.length, videoPreview]);

  // Persistir estado chave para não perder após refresh/timeout
  useEffect(() => {
    const payload = {
      settings: {
        script: contentSettings.script,
        visual_style: contentSettings.visual_style,
        image_provider: contentSettings.image_provider,
        visual_prompts_text: contentSettings.visual_prompts_text,
        leonardo_prompts_text: contentSettings.leonardo_prompts_text,
        generated_images: contentSettings.generated_images,
        audio_file: contentSettings.audio_file,
        preview_audio_file: contentSettings.preview_audio_file,
        elevenlabs_voice: contentSettings.elevenlabs_voice,
        scene_duration: contentSettings.scene_duration,
        transitions: contentSettings.transitions,
        subtitle_style: contentSettings.subtitle_style,
        leonardo_motion: contentSettings.leonardo_motion,
        motion_strength: contentSettings.motion_strength
      },
      generatedImages,
      videoPreview,
      stepCompleted
    };
    try {
      localStorage.setItem('production_studio_state', JSON.stringify(payload));
    } catch (e) {
      // storage cheio ou privacidade
    }
  }, [contentSettings, generatedImages, videoPreview, stepCompleted]);

  const updateSettings = useCallback(( key: keyof ContentSettings, value: any ) =>
  {
    console.log(`🔄 Atualizando ${key}:`, value);
    console.log('📊 Valor atual antes da atualização:', contentSettings[key]);
    const newSettings = {
      ...contentSettings,
      [ key ]: value
    };
    console.log('📊 Novas configurações:', newSettings);
    console.log('🎯 Verificando se valor foi atualizado:', newSettings[key]);
    onSettingsChange( newSettings );
  }, [contentSettings, onSettingsChange]);

  // Configurar voice_profile padrão se não estiver definido
  useEffect(() => {
    if (!contentSettings.voice_profile) {
      updateSettings('voice_profile', 'male-professional');
    }
  }, [contentSettings.voice_profile, updateSettings]);

  // Áudio local não é utilizado no fluxo simplificado

  // Fluxo simplificado removeu preview/efeitos locais e sliders

  const setTopic = ( topic: string ) =>
  {
    updateSettings( 'topic', topic );
  };

  const setScript = ( script: string ) =>
  {
    console.log('📝 setScript chamado com:', script.substring(0, 100));
    updateSettings( 'script', script );
    console.log('✅ contentSettings.script atualizado');
    
    // Salvar roteiro automaticamente
    if (script && script.length > 50) {
      saveScriptToFile(script);
    }
  };

  // Extrai texto de roteiro e prompts a partir de diferentes formatos de resposta
  const extractFromScriptObject = (scriptObj: any) => {
    let scriptText = '';
    let visualPromptsText = '';
    let leonardoPromptsText = '';

    if (!scriptObj) {
      return { scriptText, visualPromptsText, leonardoPromptsText };
    }

    // 1) Texto do roteiro
    if (typeof scriptObj === 'string') {
      scriptText = scriptObj;
    } else if (typeof scriptObj === 'object') {
      scriptText = scriptObj.roteiro_completo || scriptObj.final_script_for_tts || scriptObj.script || scriptObj.content || '';

      // Se não houver texto contínuo, montar a partir das cenas (narration)
      if (!scriptText && Array.isArray(scriptObj.scenes)) {
        const parts: string[] = [];
        for (const s of scriptObj.scenes) {
          if (s && (s.narration || s.on_screen_text)) {
            const t = (s.t_start !== undefined && s.t_end !== undefined) ? `[TIMING: ${s.t_start}-${s.t_end}s] ` : '';
            parts.push(`${t}${s.narration || s.on_screen_text}`);
          }
        }
        scriptText = parts.join('\n');
      }
    }

    // 2) Prompts de imagem (Imagen/DALL·E)
    if (typeof scriptObj === 'object') {
      // Preferir campos diretos quando já fornecidos pelo backend
      if (typeof scriptObj.visual_prompts_text === 'string' && scriptObj.visual_prompts_text.trim().length > 0) {
        visualPromptsText = scriptObj.visual_prompts_text;
      }
      // Derivar de scenes se ainda vazio
      if (!visualPromptsText && Array.isArray(scriptObj.scenes)) {
        const lines: string[] = [];
        for (const s of scriptObj.scenes) {
          if (s && s.image_prompt) {
            const timing = (s.t_start !== undefined && s.t_end !== undefined) ? `[${s.t_start}-${s.t_end}s]` : '';
            lines.push(`${timing} ${s.image_prompt}`.trim());
          }
        }
        visualPromptsText = lines.join('\n');
      }
      // Derivar de visual_prompts array (compatibilidade)
      if (!visualPromptsText && Array.isArray(scriptObj.visual_prompts)) {
        const lines: string[] = [];
        for (const vp of scriptObj.visual_prompts) {
          if (!vp) continue;
          if (typeof vp === 'string') {
            lines.push(vp);
          } else if (typeof vp === 'object' && vp.image_prompt) {
            lines.push(String(vp.image_prompt));
          }
        }
        visualPromptsText = lines.join('\n');
      }
    }

    // 3) Prompts de animação (Leonardo Motion)
    if (typeof scriptObj === 'object') {
      // Preferir campo direto quando existir
      if (typeof scriptObj.leonardo_prompts_text === 'string' && scriptObj.leonardo_prompts_text.trim().length > 0) {
        leonardoPromptsText = scriptObj.leonardo_prompts_text;
      }
      // Derivar de scenes se ainda vazio
      if (!leonardoPromptsText && Array.isArray(scriptObj.scenes)) {
        const lines: string[] = [];
        for (const s of scriptObj.scenes) {
          if (s && s.motion_prompt) {
            const timing = (s.t_start !== undefined && s.t_end !== undefined) ? `[${s.t_start}-${s.t_end}s]` : '';
            lines.push(`${timing} ${s.motion_prompt}`.trim());
          }
        }
        leonardoPromptsText = lines.join('\n');
      }
      // Derivar de visual_prompts array (quando tiver motion_prompt)
      if (!leonardoPromptsText && Array.isArray(scriptObj.visual_prompts)) {
        const lines: string[] = [];
        for (const vp of scriptObj.visual_prompts) {
          if (!vp) continue;
          if (typeof vp === 'object' && vp.motion_prompt) {
            lines.push(String(vp.motion_prompt));
          }
        }
        leonardoPromptsText = lines.join('\n');
      }
    }

    return { scriptText, visualPromptsText, leonardoPromptsText };
  };

  const saveScriptToFile = async (script: string) => {
    try {
      // Criar nome do arquivo organizado
      const now = new Date();
      const dateStr = now.toISOString().split('T')[0]; // 2025-08-10
      const timeStr = now.toTimeString().split(' ')[0].replace(/:/g, '-'); // 14-30-45
      
      // Limpar tópico para nome de arquivo
      const cleanTopic = (contentSettings.topic || 'sem-topico')
        .toLowerCase()
        .replace(/[^a-z0-9\s]/g, '') // Remove caracteres especiais
        .replace(/\s+/g, '-') // Substitui espaços por hífens
        .substring(0, 30); // Limita tamanho
      
      const aiModel = contentSettings.content_ai_model || 'unknown';
      const duration = videoDuration || 60;
      
      // Nome: 2025-08-10_14-30-45_gemini_60s_historia-de-terror
      const fileName = `${dateStr}_${timeStr}_${aiModel}_${duration}s_${cleanTopic}`;
      
      // Metadados completos para facilitar busca e replicação
      const scriptData = {
        // Identificação
        fileName: fileName,
        timestamp: now.toISOString(),
        
        // Conteúdo
        script: script,
        topic: contentSettings.topic,
        
        // Configurações de geração
        ai_model: contentSettings.content_ai_model,
        video_duration: videoDuration,
        
        // Estatísticas
        script_length: script.length,
        estimated_audio_duration: Math.ceil(script.length / 10), // ~10 chars por segundo
        word_count: script.split(' ').length,
        
        // Para replicação
        generation_settings: {
          provider: contentSettings.content_ai_model,
          format: 'tiktok',
          duration: videoDuration,
          theme: contentSettings.topic
        },
        
        // Organização
        category: detectScriptCategory(script),
        tags: generateScriptTags(contentSettings.topic, script),
        
        // Status
        status: 'generated',
        version: '1.0'
      };

      const response = await fetch(buildApiUrl('scripts/save-organized'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(scriptData),
      });
      
      if (response.ok) {
        console.log(`✅ Script salvo: /media/scripts/${fileName}.json`);
        console.log('📊 Metadados:', scriptData);
        
        // Notificar usuário discretamente
        setError(null);
        setTimeout(() => {
          console.log(`💾 Script "${cleanTopic}" salvo automaticamente`);
        }, 1000);
      }
    } catch (error) {
      console.warn('⚠️ Não foi possível salvar script:', error);
    }
  };
  
  // Função auxiliar para detectar categoria do script
  const detectScriptCategory = (script: string): string => {
    const lowerScript = script.toLowerCase();
    
    if (lowerScript.includes('misterio') || lowerScript.includes('terror') || lowerScript.includes('assombr')) {
      return 'mystery-terror';
    } else if (lowerScript.includes('tecnologia') || lowerScript.includes('ia') || lowerScript.includes('artificial')) {
      return 'technology';
    } else if (lowerScript.includes('historia') || lowerScript.includes('era uma vez')) {
      return 'story';
    } else if (lowerScript.includes('como') || lowerScript.includes('tutorial') || lowerScript.includes('aprenda')) {
      return 'tutorial';
    } else if (lowerScript.includes('engraçad') || lowerScript.includes('piada') || lowerScript.includes('humor')) {
      return 'comedy';
    } else {
      return 'general';
    }
  };
  
  // Função auxiliar para gerar tags
  const generateScriptTags = (topic: string, script: string): string[] => {
    const tags = [];
    
    // Tags do tópico
    if (topic) {
      tags.push(...topic.toLowerCase().split(' ').filter(word => word.length > 2));
    }
    
    // Tags do conteúdo
    const keywords = ['historia', 'tecnologia', 'misterio', 'tutorial', 'dica', 'segredo', 'incrivel'];
    keywords.forEach(keyword => {
      if (script.toLowerCase().includes(keyword)) {
        tags.push(keyword);
      }
    });
    
    // Tags de duração
    if (videoDuration <= 30) tags.push('short');
    else if (videoDuration <= 60) tags.push('medium');
    else tags.push('long');
    
    return Array.from(new Set(tags)); // Remove duplicatas
  };

  const handleGenerateScript = async ( provider: string ) =>
  {
    if ( !contentSettings.topic )
    {
      setError( 'Por favor, digite um tema ou ideia.' );
      return;
    }
    setIsGenerating( true );
    setError( null );

    try {
      const response = await fetch(buildApiUrl('production/generate-script'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          theme: contentSettings.topic,
          provider: provider.toLowerCase(),
          format: 'tiktok',
          duration: videoDuration,
          story_type: contentSettings.category || 'curiosidade'
        }),
      });

      if (!response.ok) {
        throw new Error(`Erro na API: ${response.status}`);
      }

      const data = await response.json();
      console.log('Response data:', data); // Debug log

      if (data.success && data.data) {
        // Extrair roteiro e prompts de forma robusta
        const { scriptText, visualPromptsText, leonardoPromptsText } = extractFromScriptObject(data.data);
        const script = scriptText || data.data.roteiro_completo || data.data.final_script_for_tts || data.data.script || data.data.content || '';

        if (script && script.trim().length > 0) {
          setScript(script);
          // Preencher prompts quando presentes
          if (visualPromptsText && visualPromptsText.trim().length > 0) {
            updateSettings('visual_prompts_text', visualPromptsText);
          } else if (typeof data.data.visual_prompts_text === 'string' && data.data.visual_prompts_text.trim().length > 0) {
            updateSettings('visual_prompts_text', data.data.visual_prompts_text);
          }
          if (leonardoPromptsText && leonardoPromptsText.trim().length > 0) {
            updateSettings('leonardo_prompts_text', leonardoPromptsText);
          } else if (typeof data.data.leonardo_prompts_text === 'string' && data.data.leonardo_prompts_text.trim().length > 0) {
            updateSettings('leonardo_prompts_text', data.data.leonardo_prompts_text);
          }
        } else {
          console.error('Nenhum campo de script encontrado na resposta:', data.data);
          throw new Error('Script não encontrado na resposta da API');
        }
      } else {
        console.error('API response structure:', data); // Debug log
        throw new Error(data.error || 'Erro desconhecido na geração do roteiro');
      }
    } catch (error) {
      console.error('Erro ao gerar roteiro:', error);
      const errorMessage = error instanceof Error ? error.message : 'Erro desconhecido';
      setError(`Erro ao gerar roteiro: ${errorMessage}`);
    }
    
    setIsGenerating( false );
  };

  const handleBattleClick = async ( event: React.MouseEvent<HTMLButtonElement, MouseEvent> ): Promise<void> =>
  {
    if ( !contentSettings.topic )
    {
      setError( 'Por favor, digite um tema ou ideia antes de iniciar a batalha.' );
      return;
    }

    setIsGenerating( true );
    setError( null );
    setGenerationProgress( 25 );
    setBattleResults( [] );
    setShowBattleResults( false );

    try {
      console.log('🥊 Iniciando batalha de AIs para:', contentSettings.topic);
      
      const response = await fetch(buildApiUrl('production/ai-battle'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          theme: contentSettings.topic,
          providers: ['gemini', 'claude', 'gpt'],
          format: 'tiktok',
          duration: videoDuration
        }),
      });

      setGenerationProgress( 50 );
      console.log('📡 Resposta da API recebida, status:', response.status);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('❌ Erro na resposta:', errorText);
        throw new Error(`Erro na API: ${response.status} - ${errorText}`);
      }

      const data = await response.json();
      console.log('📊 DADOS COMPLETOS DA BATALHA:', JSON.stringify(data, null, 2));
      
      setGenerationProgress( 75 );
      
      // Processar resposta da batalha de AIs
      if (data.success && data.data && data.data.battle_results) {
        console.log('✅ Estrutura battle_results encontrada');
        const results = [];
        const battleResults = data.data.battle_results;
        console.log('🔍 Battle results:', JSON.stringify(battleResults, null, 2));
        
        // Processar cada AI participante
        for (const [aiName, aiData] of Object.entries(battleResults)) {
          console.log(`🤖 Processando ${aiName}:`, aiData);
          if (aiData && typeof aiData === 'object') {
            const aiResult = aiData as any;
            const processedResult = {
              name: aiName.charAt(0).toUpperCase() + aiName.slice(1),
              script: aiResult.script_data || aiResult.script || aiResult,
              score: aiResult.score || Math.random() * 100, // Fallback score
              analysis: aiResult.analysis || {}
            };
            console.log(`✅ Resultado processado para ${aiName}:`, processedResult);
            results.push(processedResult);
          }
        }

        console.log('🏆 TODOS OS RESULTADOS FINAIS:', results);
        
        if (results.length > 0) {
          // Ordenar por score (maior primeiro)
          results.sort((a, b) => b.score - a.score);
          setBattleResults(results);
          setShowBattleResults(true);
          setGenerationProgress(100);
          console.log('🎯 Estado atualizado - showBattleResults:', true, 'battleResults length:', results.length);
        } else {
          console.error('❌ Nenhum resultado válido encontrado');
          throw new Error('Nenhum resultado válido recebido da batalha');
        }
        
      } else if (data.success && data.data) {
        // Fallback: tentar processar estrutura alternativa
        console.log('🔄 Tentando estrutura alternativa de dados');
        const results = [];
        
        // Se tiver winner_script_data, usar como base
        if (data.data.winner_script_data) {
          results.push({
            name: data.data.winner || 'Vencedor',
            script: data.data.winner_script_data,
            score: 100,
            analysis: {}
          });
        }
        
        if (results.length > 0) {
          setBattleResults(results);
          setShowBattleResults(true);
          setGenerationProgress(100);
        } else {
          throw new Error('Estrutura de dados da batalha não reconhecida');
        }
      } else {
        console.error('❌ Resposta inválida da API:', data);
        throw new Error(data.error || 'Resposta inválida da API de batalha');
      }
      
    } catch (error) {
      console.error('💥 Erro completo na batalha:', error);
      const errorMessage = error instanceof Error ? error.message : 'Erro desconhecido';
      setError(`Erro na batalha de AIs: ${errorMessage}`);
      setGenerationProgress(0);
    } finally {
      setIsGenerating(false);
    }
  };


  const handleSelectAI = ( aiName: string, script: any ) => {
    console.log('🎯 Selecionando AI:', aiName);
    console.log('📄 Script recebido:', script);
    
  // Manter seleção ativa para possibilitar fallback nas textareas via getSelectedScriptData()
  setSelectedAI( aiName );
    
  // Extrair textos e prompts a partir do objeto flexível
  const { scriptText, visualPromptsText, leonardoPromptsText } = extractFromScriptObject(script);
  const scriptContent = (scriptText && scriptText.trim().length > 0)
    ? scriptText
    : 'Roteiro não encontrado no objeto';
  console.log('📝 Campos disponíveis no script:', typeof script === 'object' ? Object.keys(script) : '(string)');
  console.log('🔍 Roteiro extraído:', scriptContent.substring(0, 100));
    
    console.log('✅ Script final para textarea:', scriptContent.substring(0, 200));
    
    // Atualização única (atômica) para evitar sobrescrita por closures
    const newSettings = {
      ...contentSettings,
      script: scriptContent,
      visual_prompts_text: (typeof visualPromptsText === 'string' && visualPromptsText.trim().length > 0)
        ? visualPromptsText
        : contentSettings.visual_prompts_text,
      leonardo_prompts_text: (typeof leonardoPromptsText === 'string' && leonardoPromptsText.trim().length > 0)
        ? leonardoPromptsText
        : contentSettings.leonardo_prompts_text,
      content_ai_model: aiName.toLowerCase() as 'gemini' | 'claude' | 'chatgpt'
    } as ContentSettings;
    onSettingsChange(newSettings);
    // Atualizar textarea (mantém UX responsiva)
    setScript(scriptContent);
    if (scriptContent && scriptContent.length > 50) {
      saveScriptToFile(scriptContent);
    }
    
    // Salvar o voto no sistema principal (mas SEM avançar para próxima etapa)
    saveBattleVoteOnly( aiName, script );

  // Fechar a grade de batalha, mas manter seleção e resultados para leitura dos textareas
  setShowBattleResults(false);
  setExpandedCard(null);
  };

  const saveBattleVoteOnly = async ( winner: string, winnerScript: any ) => {
    try {
      // Salvar configuração vencedora para replicação futura
      const now = new Date();
      const dateStr = now.toISOString().split('T')[0];
      const timeStr = now.toTimeString().split(' ')[0].replace(/:/g, '-');
      
      const cleanTopic = (contentSettings.topic || 'batalha-ai')
        .toLowerCase()
        .replace(/[^a-z0-9\s]/g, '')
        .replace(/\s+/g, '-')
        .substring(0, 25);
      
      // Nome: 2025-08-10_14-30-45_WINNER-gemini_60s_historia-terror
      const fileName = `${dateStr}_${timeStr}_WINNER-${winner.toLowerCase()}_${videoDuration}s_${cleanTopic}`;
      
      // Extrair script content
      let scriptContent = '';
      if (typeof winnerScript === 'string') {
        scriptContent = winnerScript;
      } else if (winnerScript && typeof winnerScript === 'object') {
        scriptContent = winnerScript.roteiro_completo || 
                      winnerScript.final_script_for_tts || 
                      winnerScript.script || 
                      winnerScript.content || 
                      JSON.stringify(winnerScript);
      }
      
      const winnerConfigData = {
        // Identificação
        fileName: fileName,
        timestamp: now.toISOString(),
        type: 'battle_winner',
        
        // Configuração vencedora
        winner_ai: winner,
        topic: contentSettings.topic,
        script: scriptContent,
        
        // Configurações para replicar
        winning_settings: {
          ai_model: winner.toLowerCase(),
          video_duration: videoDuration,
          theme: contentSettings.topic,
          provider: winner.toLowerCase()
        },
        
        // Contexto da batalha
        battle_context: {
          participants: battleResults.map(r => r.name),
          total_participants: battleResults.length,
          winner_score: battleResults.find(r => r.name === winner)?.score || 0,
          battle_timestamp: now.toISOString()
        },
        
        // Análise para replicação
        success_factors: {
          script_length: scriptContent.length,
          estimated_engagement: 'high', // Baseado na escolha manual
          category: detectScriptCategory(scriptContent),
          tags: generateScriptTags(contentSettings.topic || '', scriptContent)
        },
        
        // Metadados
        status: 'battle_winner',
        confidence: 'user_selected',
        replication_ready: true
      };

      // Salvar configuração vencedora
      const saveWinnerData = {
        winner_script_data: winnerConfigData,
        winner: winner,
        theme: contentSettings.topic || 'Tópico Automático',
        battle_results: battleResults
      };

      const response = await fetch(buildApiUrl('scripts/save-winner'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(saveWinnerData),
      });

      if (response.ok) {
        console.log(`🏆 Configuração vencedora salva: /media/scripts/winners/${fileName}.json`);
        console.log('📊 Dados para replicação:', winnerConfigData);
        setError(null);
        
        // Também salvar no sistema de batalha tradicional
        const battleData = {
          winner: winner,
          topic: contentSettings.topic || 'Tópico Automático',
          winnerScript: winnerScript,
          battleResults: battleResults,
          timestamp: now.toISOString(),
          source: 'ProductionStudio'
        };

        await fetch(buildApiUrl('ai-battle/save-result'), {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(battleData),
        });
        
      } else {
        const errorText = await response.text();
        console.error('❌ Erro ao salvar configuração vencedora:', errorText);
        setError('Erro ao salvar configuração, mas o roteiro foi selecionado.');
      }
    } catch (error) {
      console.error('💥 Erro no sistema de configurações vencedoras:', error);
      setError('Sistema offline - configuração não foi salva, mas roteiro foi selecionado.');
    }
  };

  // Função antiga de geração de áudio substituída pelo AudioSimpleStep

  const handleOptimizeVisualPrompts = async () => {
    if (!contentSettings.script) {
      setError('É necessário ter um roteiro antes de otimizar prompts visuais.');
      return;
    }

    setIsGenerating(true);
    setError(null);
    
    try {
      // Obter dados do roteiro estruturado selecionado
      const selectedScript = getSelectedScriptData();
      
      let script_data;
      
      if (selectedScript && selectedScript.visual_prompts) {
        // Usar os visual_prompts estruturados do roteiro selecionado
        console.log('✅ Usando visual_prompts estruturados do roteiro selecionado');
        script_data = {
          title: contentSettings.topic || selectedScript.title || 'Vídeo Gerado',
          content: contentSettings.script,
          visual_prompts: selectedScript.visual_prompts
        };
      } else {
        // Fallback: criar visual cues básicos
        console.log('⚠️ Roteiro estruturado não disponível, criando visual_cues básicos');
        setGenerationProgress(10);
        const scriptSentences = contentSettings.script.split(/[.!?]+/).filter(s => s.trim().length > 0);
        
        const visual_cues = scriptSentences.slice(0, 6).map(sentence => {
          return sentence.trim()
            .replace(/você|vocês|nós/gi, '')
            .replace(/vamos|iremos/gi, '')
            .trim();
        });
        
        script_data = {
          title: contentSettings.topic || 'Vídeo Gerado',
          content: contentSettings.script,
          visual_cues: visual_cues
        };
      }
      
      console.log('🎨 Gerando imagens com Vertex AI Imagen 3:', script_data);
      setGenerationProgress(30);
      
      // Se houver prompts otimizados, incluir no payload como visual_prompts
      let scriptPayload = { ...script_data } as any;
      if (Array.isArray(optimizedPromptsRef.current) && optimizedPromptsRef.current.length > 0) {
        const prompts = optimizedPromptsRef.current as string[];
        scriptPayload.visual_prompts = prompts.map((p, idx) => ({ image_prompt: p, index: idx + 1 }));
      }

      // Usar o novo endpoint de geração com cache
      console.log('🎯 Chamando endpoint de geração com cache...');
  const imageResponse = await safeFetch(buildApiUrl('production/generate-images'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          script_data: scriptPayload,
          visual_style: contentSettings.visual_style || 'misterio',
          image_provider: contentSettings.image_provider || 'hybrid'
        }),
  });
      
      if (!imageResponse.ok) {
        const errorText = await imageResponse.text();
        console.error('❌ Erro na resposta da API:', errorText);
        throw new Error(`Erro na geração de imagens: ${imageResponse.status} - ${errorText}`);
      }
      
      const imageData = await imageResponse.json();
      console.log('✅ Resposta da geração de imagens:', imageData);
      
      setGenerationProgress(80);
      
  if (imageData.success && imageData.images) {
        // Converter caminhos para URLs de mídia
        const imageUrls = imageData.images.map((imagePath: string, index: number) => {
          // Se já é uma URL completa, usar diretamente
          if (imagePath.startsWith('http')) {
            return {
              url: imagePath,
              image_url: imagePath,
              prompt: `Cena ${index + 1} - Prompt otimizado automaticamente`,
              index: index + 1
            };
          }
          
          // Senão, construir a URL
          const fileName = imagePath.split('/').pop();
          const imageUrl = buildMediaUrl(`images/${fileName}`);
          
          return {
            url: imageUrl,
            image_url: imageUrl,
            prompt: `Cena ${index + 1} - Prompt otimizado automaticamente`,
            index: index + 1
          };
        });
        
        // Salvar as imagens geradas
        console.log('🖼️ Dados das imagens recebidos:', imageData.images);
        console.log('🔗 URLs das imagens processadas:', imageUrls);
        setGeneratedImages(imageUrls);
        updateSettings('generated_images', imageUrls);
        if (Array.isArray(imageData.used_prompts) && imageData.used_prompts.length > 0) {
          const vpText = imageData.used_prompts
            .map((p: string, i: number) => `Cena ${i + 1} - Prompt:\n${p}\n`)
            .join('\n');
          updateSettings('visual_prompts_text', vpText);
        }
        
        setGenerationProgress(100);
        
        // Marcar step 3 como completo SEM avançar automaticamente
        markStepAsCompleted(3);
        
        const cacheMessage = imageData.from_cache ? 
          `♻️ ${imageData.images.length} imagens recuperadas do cache instantaneamente!` :
          `✨ ${imageData.images.length} imagens geradas com alta qualidade!`;
          
        alert(`✅ ${cacheMessage}\n🎯 Cache Hash: ${imageData.cache_hash}`);
      } else {
        throw new Error(imageData.error || 'Erro na geração de imagens');
      }
      
    } catch (error) {
      console.error('Erro no processo de otimização visual:', error);
      const errorMessage = error instanceof Error ? error.message : 'Erro desconhecido';
      setError(`Erro na otimização visual: ${errorMessage}`);
    }
    
    setIsGenerating(false);
    setGenerationProgress(0);
  };

  // Substitui uma imagem específica via prompt customizado, atualizando apenas ela no grid
  const handleReplaceImage = async (index: number) => {
    const prompt = replacePrompt.trim();
    if (!prompt) {
      setError('Informe um prompt para substituir a imagem.');
      return;
    }
    setReplacingIndex(index);
    try {
      const resp = await safeFetch(buildApiUrl('production/replace-image'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt,
          visual_style: contentSettings.visual_style || 'misterio',
          image_provider: contentSettings.image_provider || 'hybrid',
          filename_prefix: `scene_${index+1}_repl`
        })
      });
      if (!resp.ok) throw new Error(`Falha ao substituir imagem: ${resp.status}`);
      const data = await resp.json();
      if (!data.success || !data.image_url) throw new Error(data.error || 'Substituição falhou');

      setGeneratedImages(prev => {
        const next = [...prev];
        next[index] = { ...next[index], url: data.image_url, image_url: data.image_url };
        updateSettings('generated_images', next);
        return next;
      });
      setReplacePrompt("");
    } catch (e: any) {
      console.error('Erro ao substituir imagem:', e);
      setError(e?.message || 'Erro ao substituir imagem');
    } finally {
      setReplacingIndex(null);
    }
  };

  // Função para regenerar áudio com ajustes pós-geração
  // Regeneração de áudio avançada removida no modo simplificado

  const handleGenerateCustom = async () => {
    if (!contentSettings.script) {
      setError('É necessário ter um roteiro antes de gerar o vídeo.');
      return;
    }

    if (generatedImages.length === 0) {
      setError('É necessário gerar as imagens antes de criar o vídeo. Volte ao Step 3.');
      return;
    }

    setIsGenerating(true);
    setError(null);
    setGenerationProgress(0);
    
    try {
      // Passo 1: Preparar execução
      setGenerationProgress(10);

      // Passo 2: Usar áudio já gerado (preferir), senão gerar agora respeitando provedor escolhido
      setGenerationProgress(20);
      let finalAudioUrl = contentSettings.audio_file || contentSettings.preview_audio_file || '';
      let finalAudioDuration = contentSettings.audio_duration;

  if (!finalAudioUrl) {
        // Escolher provedor de TTS conforme preferência do usuário; padrão: Google (para não gastar créditos)
  const preferEleven = (contentSettings.last_audio_model === 'elevenlabs') || !!contentSettings.elevenlabs_voice;

        if (!preferEleven) {
          // Google primeiro (padrão de testes); sem fallback automático para ElevenLabs para evitar custos
          const gr = await safeFetch(buildApiUrl('production/generate-google-tts'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              text: cleanScriptForTTS(contentSettings.script),
              speaking_rate: contentSettings.speaking_speed || 1.0,
              language_code: 'pt-BR'
            })
          });
          if (!gr.ok) throw new Error(`Erro na geração de áudio (Google TTS): ${gr.status}`);
          const gd = await gr.json();
          if (!gd.success || !gd.audio_url) throw new Error(gd.error || 'Falha na geração de áudio Google TTS');
          finalAudioUrl = gd.audio_url;
          finalAudioDuration = gd.duration;
          updateSettings('audio_file', gd.audio_url);
          updateSettings('last_audio_model', 'natural');
        } else {
          // ElevenLabs quando explicitamente escolhido; com fallback para Google
          try {
            const r = await safeFetch(buildApiUrl('production/generate-elevenlabs-audio'), {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                text: cleanScriptForTTS(contentSettings.script),
                voice_profile: contentSettings.elevenlabs_voice || 'victor-power'
              })
            });
            if (!r.ok) throw new Error(`Erro na geração de áudio (ElevenLabs): ${r.status}`);
            const d = await r.json();
            const path = d.audio_url || d.audio_path;
            if (!d.success || !path) throw new Error(d.error || 'Falha na geração de áudio ElevenLabs');
            finalAudioUrl = path;
            finalAudioDuration = d.duration;
            updateSettings('audio_file', path);
            updateSettings('last_audio_model', 'elevenlabs');
          } catch (err) {
            console.warn('⚠️ ElevenLabs falhou, aplicando fallback para Google TTS:', err);
            const gr2 = await safeFetch(buildApiUrl('production/generate-google-tts'), {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                text: cleanScriptForTTS(contentSettings.script),
                speaking_rate: contentSettings.speaking_speed || 1.0,
                language_code: 'pt-BR'
              })
            });
            if (!gr2.ok) throw new Error(`Erro na geração de áudio (Google TTS): ${gr2.status}`);
            const gd2 = await gr2.json();
            if (!gd2.success || !gd2.audio_url) throw new Error(gd2.error || 'Falha na geração de áudio Google TTS');
            finalAudioUrl = gd2.audio_url;
            finalAudioDuration = gd2.duration;
            updateSettings('audio_file', gd2.audio_url);
            updateSettings('last_audio_model', 'natural');
            alert('⚠️ Sem créditos no ElevenLabs ou erro momentâneo. Fallback para Google TTS aplicado.');
          }
        }
      }

      // Passo 3: Criar vídeo final
      setGenerationProgress(50);
      // Enviar somente URLs/strings para reduzir payload
      const imagesForRender = generatedImages.map((img: any) => img.url || img.image_url || img);
  const videoResponse = await safeFetch(buildApiUrl('production/create-video'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          audio_path: finalAudioUrl,
          images: imagesForRender,
          script: contentSettings.script,
          settings: {
            duration: videoDuration,
            visual_style: contentSettings.visual_style || 'realista',
            voice_profile: contentSettings.voice_profile || 'male-professional',
            voice_emotion: contentSettings.voice_emotion || 'neutral',
            speaking_speed: contentSettings.speaking_speed || 1.0,
            transitions: contentSettings.transitions || 'fade',
            subtitle_style: contentSettings.subtitle_style || 'tiktok',
    background_music: contentSettings.background_music || 'upbeat',
    subtitle_mode: contentSettings.subtitle_mode || 'script',
            target_platforms: contentSettings.target_platforms || ['tiktok'],
            audio_duration: finalAudioDuration,
    music_volume: contentSettings.music_volume ?? contentSettings.background_music_volume ?? 0.3,
    min_cut: contentSettings.min_cut ?? 1.5,
    max_cut: contentSettings.max_cut ?? 3.0,
            // Dica de preset leve para não derrubar o servidor
            render_preset: 'mobile_720p'
          }
        }),
      });

      if (!videoResponse.ok) {
        throw new Error(`Erro na criação do vídeo: ${videoResponse.status}`);
      }

      const videoData = await videoResponse.json();
      setGenerationProgress(90);

      if (videoData.success && videoData.video_url) {
        setVideoPreview(videoData.video_url);
        setGenerationProgress(100);
        
        alert('🎉 Vídeo gerado com sucesso! Confira a pré-visualização acima.');
      } else {
        throw new Error(videoData.error || 'Erro na geração do vídeo');
      }

    } catch (error) {
      console.error('Erro na geração do vídeo:', error);
      const errorMessage = error instanceof Error ? error.message : 'Erro desconhecido';
      setError(`Erro na geração do vídeo: ${errorMessage}`);
    }

    setIsGenerating(false);
    setGenerationProgress(0);
  };

  // Função para otimizar prompts automaticamente
  const handleOptimizePrompts = async () => {
    if (!contentSettings.script) {
      setError('Primeiro gere um roteiro para otimizar os prompts.');
      return;
    }

    setIsOptimizingPrompts(true);
    setError('');

    try {
      console.log('🎯 Iniciando otimização de prompts...');

      // Extrair prompts atuais das imagens geradas ou criar prompts básicos
      const currentPrompts = generatedImages.length > 0 
        ? generatedImages.map((img, index) => `scene ${index + 1}`)
        : Array.from({length: 7}, (_, i) => `historical scene ${i + 1}`);

      const response = await fetch(buildApiUrl('/production/optimize-prompts'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          script: cleanScriptForTTS(contentSettings.script),
          image_prompts: currentPrompts,
          style: contentSettings.visual_style || 'historia_documentario',
          duration: 60
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      if (data.success) {
        setOptimizedPrompts(data.optimized_scenes);

        // Aplicar automaticamente os prompts otimizados às imagens atuais
        // para que a próxima geração use prompts distintos por cena
        try {
          const prompts = (data.optimized_scenes || []).map((s: any) => s.image_prompt).filter(Boolean);
          if (prompts.length > 0) {
            optimizedPromptsRef.current = prompts;
          }
        } catch (e) {
          console.warn('Não foi possível aplicar prompts otimizados automaticamente:', e);
        }

        console.log('✅ Prompts otimizados:', data.optimized_scenes);
      } else {
        throw new Error(data.error || 'Falha na otimização de prompts');
      }

    } catch (error) {
      console.error('❌ Erro na otimização de prompts:', error);
      const errorMessage = error instanceof Error ? error.message : 'Erro desconhecido';
      setError(`Erro na otimização de prompts: ${errorMessage}`);
    } finally {
      setIsOptimizingPrompts(false);
    }
  };

  // Animação de imagens consolidada no backend durante a renderização completa

  // Função para renderização completa do vídeo
  const handleCompleteVideoRender = async () => {
    if (!contentSettings.leonardo_motion) {
      setError('Selecione um estilo de movimento para continuar.');
      return;
    }

    if (generatedImages.length === 0) {
      setError('Nenhuma imagem disponível para renderização.');
      return;
    }

    if (isRenderingVideo) return; // trava reentradas

    setIsRenderingVideo(true);
    setError(null);
    
    try {
      console.log('🎬 Iniciando renderização completa do vídeo...');
      setGenerationProgress(10);
      const imagesForRender = generatedImages.map((img: any) => img.url || img.image_url || img);
      const response = await safeFetch(buildApiUrl('production/render-complete-video'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          // Evita payloads gigantes: enviar apenas URLs das imagens
          storyboard: (contentSettings.script || '').slice(0, 12000),
          images: imagesForRender,
          settings: {
            leonardo_motion: contentSettings.leonardo_motion,
            motion_strength: contentSettings.motion_strength || 0.7,
            elevenlabs_voice: contentSettings.elevenlabs_voice || 'Rachel',
            voice_stability: contentSettings.voice_stability || 0.5,
            voice_clarity: contentSettings.voice_clarity || 0.5,
            transitions: contentSettings.transitions || 'fade',
            scene_duration: contentSettings.scene_duration || 4,
            music_volume: contentSettings.music_volume ?? contentSettings.background_music_volume ?? 0.3,
            background_music: contentSettings.background_music || 'upbeat',
            min_cut: contentSettings.min_cut || 1.5,
            max_cut: contentSettings.max_cut || 3.0,
            render_preset: 'mobile_720p'
          }
        }),
      });

      if (!response.ok) {
        throw new Error(`Erro na renderização: ${response.status}`);
      }

      const renderData = await response.json();
      if (!renderData.success) {
        throw new Error(renderData.error || 'Erro na renderização do vídeo');
      }

      // Se o backend retornar job_id, fazer polling para evitar request longa
      const jobId = renderData.job_id || renderData.jobId || renderData.task_id || renderData.id;
      if (jobId) {
        console.log('🧵 Job iniciado:', jobId);
        setGenerationProgress(20);
        let finished = false;
        const started = Date.now();
        while (!finished) {
          // Evita loop infinito (> 20 minutos)
          if (Date.now() - started > 20 * 60 * 1000) {
            throw new Error('Tempo máximo de renderização excedido. Tente novamente.');
          }
          await sleep(1500);
          const statusResp = await safeFetch(buildApiUrl(`production/job-status?job_id=${encodeURIComponent(jobId)}`), { method: 'GET' }, { retries: 1 });
          if (!statusResp.ok) continue;
          const statusData = await statusResp.json();
          if (statusData?.progress) {
            setGenerationProgress(Math.min(95, Number(statusData.progress) || 0));
          }
          if (statusData?.status === 'completed' && statusData?.video_url) {
            setVideoPreview(statusData.video_url);
            finished = true;
          } else if (statusData?.status === 'failed') {
            throw new Error(statusData?.error || 'Falha na renderização');
          }
        }
        setGenerationProgress(100);
        alert('🎉 Vídeo renderizado com sucesso! Seu vídeo completo está pronto.');
      } else {
        // Resposta direta
  setVideoPreview(renderData.video_path || renderData.video_url);
        alert('🎉 Vídeo renderizado com sucesso! Seu vídeo completo está pronto.');
      }
      
    } catch (error) {
      console.error('Erro na renderização do vídeo:', error);
      const errorMessage = error instanceof Error ? error.message : 'Erro desconhecido';
      setError(`Erro na renderização do vídeo: ${errorMessage}`);
    }
    
    setIsRenderingVideo(false);
  };

  // Geração direta: Texto → Vídeo (Leonardo em uma chamada encadeada)
  const handleLeonardoDirectVideo = async () => {
    if (!contentSettings.script) {
      setError('É necessário ter um roteiro para gerar o vídeo.');
      return;
    }
    if (!contentSettings.leonardo_motion) {
      setError('Selecione um estilo de movimento para continuar.');
      return;
    }
    if (isRenderingVideo) return;

    setIsRenderingVideo(true);
    setError(null);
    try {
      // Extrair uma frase curta do roteiro para o prompt de imagem
      const firstSentence = (contentSettings.script.split(/[.!?]+/).find(s => s.trim().length > 8) || contentSettings.topic || 'Cena cinematográfica').trim();

      // Mapear estilo visual para o otimizador do backend
      const styleMap: Record<string, string> = {
        misterio: 'misterio_suspense',
        tecnologia: 'tecnologia_moderna',
        historia: 'historia_documentario',
        educativo: 'historia_documentario',
        entretenimento: 'historia_documentario',
        ciencia: 'historia_documentario'
      };
      const styleKey = styleMap[(contentSettings.visual_style as string) || 'historia'] || 'historia_documentario';

      // Mapear o ID do movimento para um motion_prompt descritivo
      const motionMap: Record<string, string> = {
        subtle_movement: 'Subtle natural movement, gentle breathing, soft wind effects',
        dynamic_zoom: 'Dynamic camera zoom, cinematic movement, depth focus shift',
        floating_elements: 'Floating particles, magical atmosphere, ethereal movement',
        perspective_shift: 'Perspective transformation, 3D rotation, spatial movement',
        energy_pulse: 'Energy waves, pulsating light, rhythmic movement'
      };
      const motionPrompt = motionMap[contentSettings.leonardo_motion as string] || 'Subtle cinematic motion, slow zoom, gentle parallax';

      // Duração sugerida
      const duration = Number(contentSettings.scene_duration) || 6;

      const resp = await safeFetch(buildApiUrl('production/leonardo-text-to-video'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: firstSentence,
          motion_prompt: motionPrompt,
          duration,
          style: styleKey
        })
      }, { retries: 0 });

      if (!resp.ok) {
        const t = await resp.text();
        throw new Error(`Erro (${resp.status}): ${t}`);
      }
      const data = await resp.json();
      if (!data.success || !data.video) {
        throw new Error(data.error || 'Falha na geração de vídeo (Leonardo)');
      }
      const v = typeof data.video === 'string' ? data.video : (data.video_url || data.video_path);
      const finalUrl = v && v.startsWith('/media/') ? buildMediaUrl(v) : v;
      setVideoPreview(finalUrl);
      alert('🎉 Vídeo (Leonardo) gerado com sucesso!');
    } catch (e) {
      console.error('❌ Erro no Leonardo texto→vídeo:', e);
      const msg = e instanceof Error ? e.message : 'Erro desconhecido';
      setError(`Erro no Leonardo texto→vídeo: ${msg}`);
    }
    setIsRenderingVideo(false);
  };

  // Funções Veo AI para movimento sutil
  const handleVeoProcessImages = async () => {
    if (!contentSettings.veo_motion_preset) {
      alert('Selecione um preset de movimento primeiro!');
      return;
    }
    
    const prompt = contentSettings.veo_motion_preset === 'custom' 
      ? contentSettings.veo_custom_prompt 
      : (contentSettings.veo_custom_prompt || 'Movimento sutil e natural');
    
    if (!prompt?.trim()) {
      alert('Digite um prompt de movimento!');
      return;
    }

    setIsRenderingVideo(true);
    setError(null);

    try {
      const veoResults = [];
      
      // Processar cada imagem individualmente
      for (let i = 0; i < generatedImages.length; i++) {
        const image = generatedImages[i];
        console.log(`🎥 Processando imagem ${i + 1}/${generatedImages.length} com Veo...`);
        
        try {
          const resp = await safeFetch(buildApiUrl('production/veo-image-to-video'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              image_path: image.url,
              prompt: prompt,
              duration_seconds: 3,
              aspect_ratio: '9:16'
            })
          }, { retries: 1 });

          if (!resp.ok) {
            const errorText = await resp.text();
            console.warn(`⚠️ Veo falhou para imagem ${i + 1}: ${errorText}`);
            veoResults.push({ success: false, error: errorText, image_index: i });
            continue;
          }

          const data = await resp.json();
          if (data.success && data.video_url) {
            console.log(`✅ Veo sucesso para imagem ${i + 1}: ${data.video_url}`);
            veoResults.push({ 
              success: true, 
              video_url: data.video_url, 
              image_index: i,
              duration: 3 
            });
          } else {
            console.warn(`⚠️ Veo sem sucesso para imagem ${i + 1}: ${data.error || 'Erro desconhecido'}`);
            veoResults.push({ 
              success: false, 
              error: data.error || 'Erro desconhecido', 
              image_index: i 
            });
          }
        } catch (e) {
          console.error(`❌ Erro Veo imagem ${i + 1}:`, e);
          veoResults.push({ 
            success: false, 
            error: e instanceof Error ? e.message : 'Erro de rede', 
            image_index: i 
          });
        }
      }

      // Analisar resultados
      const successCount = veoResults.filter(r => r.success).length;
      const failCount = veoResults.filter(r => !r.success).length;
      
      if (successCount > 0) {
        alert(`🎉 Veo processou ${successCount}/${generatedImages.length} imagens com sucesso! ${failCount > 0 ? `(${failCount} falharam)` : ''}`);
        console.log('🎥 Resultados Veo:', veoResults);
      } else {
        alert(`❌ Veo falhou em todas as ${generatedImages.length} imagens. Verifique logs para detalhes.`);
      }
      
    } catch (e) {
      console.error('❌ Erro geral no processamento Veo:', e);
      const msg = e instanceof Error ? e.message : 'Erro desconhecido';
      setError(`Erro no processamento Veo: ${msg}`);
    }

    setIsRenderingVideo(false);
  };

  const handleVeoTestImage = async () => {
    if (!contentSettings.veo_motion_preset) {
      alert('Selecione um preset de movimento primeiro!');
      return;
    }
    
    const prompt = contentSettings.veo_motion_preset === 'custom' 
      ? contentSettings.veo_custom_prompt 
      : (contentSettings.veo_custom_prompt || 'Movimento sutil e natural');
    
    if (!prompt?.trim()) {
      alert('Digite um prompt de movimento!');
      return;
    }

    if (generatedImages.length === 0) {
      alert('Nenhuma imagem disponível para teste!');
      return;
    }

    setIsRenderingVideo(true);
    setError(null);

    try {
      const testImage = generatedImages[0];
      console.log('🧪 Testando Veo com primeira imagem:', testImage.url);
      
      const resp = await safeFetch(buildApiUrl('production/veo-image-to-video'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          image_path: testImage.url,
          prompt: prompt,
          duration_seconds: 3,
          aspect_ratio: '9:16'
        })
      }, { retries: 1 });

      if (!resp.ok) {
        const errorText = await resp.text();
        throw new Error(`Erro ${resp.status}: ${errorText}`);
      }

      const data = await resp.json();
      if (data.success && data.video_url) {
        const finalUrl = data.video_url.startsWith('/media/') ? buildMediaUrl(data.video_url) : data.video_url;
        setVideoPreview(finalUrl);
        alert(`🎉 Teste Veo concluído! Vídeo gerado: ${data.video_url}`);
        console.log('✅ Resultado do teste Veo:', data);
      } else {
        throw new Error(data.error || 'Veo retornou sem sucesso');
      }
      
    } catch (e) {
      console.error('❌ Erro no teste Veo:', e);
      const msg = e instanceof Error ? e.message : 'Erro desconhecido';
      setError(`Erro no teste Veo: ${msg}`);
      alert(`❌ Teste Veo falhou: ${msg}`);
    }

    setIsRenderingVideo(false);
  };

  return (
    <Box sx={ { p: 3, backgroundColor: 'background.paper', borderRadius: 2 } }>
      {/* Cabeçalho do Studio */ }
      <Typography variant="h5" component="h2" gutterBottom sx={ { display: 'flex', alignItems: 'center', gap: 1 } }>
        🎬 Production Studio - Workflow Sequencial
      </Typography>

      {/* Navegação dos Steps */ }
      <Box sx={ { mb: 4 } }>
        <Box sx={ { 
          display: 'flex', 
          flexWrap: 'wrap',
          gap: 1,
          mb: 2,
          justifyContent: 'space-between',
          borderBottom: '1px solid #374151',
          pb: 2
        } }>
          { workflowSteps.map( ( step ) => (
            <Button
              key={ step.id }
              variant={ currentStep === step.id ? 'contained' : 'outlined' }
              color={ stepCompleted[ step.id - 1 ] ? 'success' : 'primary' }
              onClick={ () => goToStep( step.id ) }
              disabled={ !isStepAccessible( step.id ) }
              sx={ { 
                minWidth: '140px',
                height: '60px',
                display: 'flex',
                flexDirection: 'column',
                fontSize: '0.8rem'
              } }
            >
              <Box sx={ { fontSize: '1.2rem' } }>{ step.icon }</Box>
              <Box>{ step.title }</Box>
              { stepCompleted[ step.id - 1 ] && <Box sx={ { fontSize: '0.8rem' } }>✅</Box> }
            </Button>
          ) ) }
        </Box>
        
        {/* Indicador do step atual */ }
        <Typography variant="h6" sx={ { color: 'primary.main', mb: 1 } }>
          Step { currentStep }: { workflowSteps[ currentStep - 1 ].title }
        </Typography>
        <Typography variant="body2" sx={ { color: 'text.secondary', mb: 2 } }>
          { workflowSteps[ currentStep - 1 ].description }
        </Typography>
        
        {/* Instruções específicas por step */}
        {currentStep === 1 && (
          <Alert severity="info" sx={{ mb: 2 }}>
            💡 <strong>Como usar:</strong> Ajuste a duração desejada, digite um tema interessante e escolha uma IA para gerar o roteiro. O "🥊 Batalha de AIs" compara todas as opções.
          </Alert>
        )}
        
        {currentStep === 2 && (
          <Alert severity="info" sx={{ mb: 2 }}>
            🎤 <strong>Como usar:</strong> Selecione voz e emoção, ajuste configurações avançadas (tom, velocidade, volume), teste com preview e gere o áudio completo.
          </Alert>
        )}
      </Box>

      {/* Conteúdo do Step Atual */ }
      { currentStep === 1 && (
        <Box sx={ { p: 3, border: '1px solid #374151', borderRadius: 2, mb: 2 } }>
          <Typography variant="h6" gutterBottom>
            📝 Geração do Roteiro
          </Typography>
          
          {/* Controle de Duração do Vídeo */}
          <Box sx={ { mb: 3, p: 2, backgroundColor: '#1a1a2e', borderRadius: 2 } }>
            <Typography variant="body1" sx={ { mb: 2, color: '#ffd700', fontWeight: 'bold' } }>
              ⏱️ Duração do Vídeo: {videoDuration} segundos
            </Typography>
            <Box sx={{ px: 2 }}>
              <input
                type="range"
                min="15"
                max="180"
                step="15"
                value={videoDuration}
                onChange={(e) => setVideoDuration(parseInt(e.target.value))}
                style={{
                  width: '100%',
                  height: '8px',
                  borderRadius: '4px',
                  background: `linear-gradient(to right, #ffd700 0%, #ffd700 ${((videoDuration-15)/(180-15))*100}%, #444 ${((videoDuration-15)/(180-15))*100}%, #444 100%)`,
                  outline: 'none',
                  cursor: 'pointer',
                  WebkitAppearance: 'none',
                  MozAppearance: 'none'
                }}
              />
              <style>{`
                input[type="range"]::-webkit-slider-thumb {
                  appearance: none;
                  width: 20px;
                  height: 20px;
                  border-radius: 50%;
                  background: #ffd700;
                  cursor: pointer;
                  border: 2px solid #333;
                  box-shadow: 0 2px 6px rgba(255, 215, 0, 0.4);
                }
                input[type="range"]::-moz-range-thumb {
                  width: 20px;
                  height: 20px;
                  border-radius: 50%;
                  background: #ffd700;
                  cursor: pointer;
                  border: 2px solid #333;
                  box-shadow: 0 2px 6px rgba(255, 215, 0, 0.4);
                }
              `}</style>
            </Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 1, fontSize: '0.8rem', color: '#888' }}>
              <span>15s</span>
              <span>30s</span>
              <span>1min</span>
              <span>1:30min</span>
              <span>2min</span>
              <span>3min</span>
            </Box>
            <Typography variant="caption" sx={{ color: '#aaa', display: 'block', textAlign: 'center', mt: 1 }}>
              💡 A IA adaptará o roteiro para a duração selecionada
            </Typography>
          </Box>
          
          {/* Categorias de Conteúdo */}
          <Box sx={{ mb: 3 }}>
            <Typography variant="body1" sx={{ mb: 2, color: '#ffd700', fontWeight: 'bold' }}>
              🎬 Categoria do Conteúdo
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1.5 }}>
              {[
                { key: 'historia', label: '📜 História', desc: 'Fatos históricos e biografias' },
                { key: 'ciencia', label: '🧬 Ciência', desc: 'Descobertas e experimentos' },
                { key: 'tecnologia', label: '⚡ Tecnologia', desc: 'Inovações e gadgets' },
                { key: 'misterio', label: '🌙 Mistério', desc: 'Enigmas e casos inexplicados' },
                { key: 'curiosidade', label: '🤔 Curiosidades', desc: 'Fatos surpreendentes' }
              ].map((category) => (
                <Button
                  key={category.key}
                  variant={contentSettings.category === category.key ? "contained" : "outlined"}
                  onClick={() => updateSettings('category', category.key)}
                  sx={{ 
                    minWidth: '140px',
                    backgroundColor: contentSettings.category === category.key ? '#ffd700' : 'transparent',
                    color: contentSettings.category === category.key ? '#000' : '#fff',
                    border: '1px solid #444',
                    '&:hover': {
                      backgroundColor: contentSettings.category === category.key ? '#ffed4e' : '#333'
                    }
                  }}
                  title={category.desc}
                >
                  {category.label}
                </Button>
              ))}
            </Box>
          </Box>
          
          <TextField
            fullWidth
            label="Seu tema ou ideia aqui..."
            variant="outlined"
            value={ contentSettings.topic || '' }
            onChange={ ( e ) => setTopic( e.target.value ) }
            disabled={ isGenerating }
            sx={ { mb: 2 } }
          />

          <Stack direction="row" spacing={ 2 } sx={ { mb: 2, flexWrap: 'wrap' } }>
            <Button
              variant="contained"
              color="primary"
              onClick={ () => handleGenerateScript( 'Gemini' ) }
              disabled={ isGenerating || !contentSettings.topic }
              startIcon={ <AutoFixHighIcon /> }
            >
              Gerar com Gemini
            </Button>
            <Button
              variant="outlined"
              color="primary"
              onClick={ () => handleGenerateScript( 'Claude' ) }
              disabled={ isGenerating || !contentSettings.topic }
            >
              Gerar com Claude
            </Button>
            <Button
              variant="outlined"
              color="primary"
              onClick={ () => handleGenerateScript( 'GPT-4' ) }
              disabled={ isGenerating || !contentSettings.topic }
            >
              Gerar com GPT-4
            </Button>
            <Button
              variant="contained"
              color="secondary"
              onClick={ handleBattleClick }
              disabled={ isGenerating || !contentSettings.topic }
              startIcon={ <GroupsIcon /> }
            >
              🥊 Batalha de AIs
            </Button>
          </Stack>

          { isGenerating && (
            <Box sx={ { display: 'flex', alignItems: 'center', gap: 2, my: 1 } }>
              <CircularProgress size={ 20 } />
              <Typography>{ generationProgress > 0 ? 'Batalha em progresso...' : 'Gerando roteiro...' }</Typography>
            </Box>
          ) }

          { generationProgress > 0 && (
            <Box sx={ { width: '100%', mt: 1 } }>
              <LinearProgress variant="determinate" value={ generationProgress } />
              <Typography variant="caption">{ generationProgress }% - Analisando respostas das IAs...</Typography>
            </Box>
          ) }

          { showBattleResults && battleResults.length > 0 && (
            <Box sx={ { 
              mt: 3, mb: 2, p: 4, 
              backgroundColor: 'linear-gradient(135deg, #0a0a0f 0%, #1a1a2e 100%)', 
              borderRadius: 3, 
              border: '2px solid #ffd700',
              boxShadow: '0 8px 32px rgba(255, 215, 0, 0.2)'
            } }>
              <Typography variant="h5" gutterBottom sx={ { 
                color: '#ffd700', 
                textAlign: 'center',
                fontWeight: 'bold',
                textShadow: '2px 2px 4px rgba(0,0,0,0.5)'
              } }>
                🥊 BATALHA DE AIs - RESULTADOS
              </Typography>
              <Typography variant="body1" sx={ { 
                color: '#fff', 
                textAlign: 'center', 
                mb: 3,
                backgroundColor: 'rgba(255, 215, 0, 0.1)',
                padding: '12px',
                borderRadius: 2,
                border: '1px solid rgba(255, 215, 0, 0.3)'
              } }>
                ⚡ <strong>Escolha a melhor IA</strong> • Seu voto conta para o ranking global • O roteiro selecionado seguirá para a próxima etapa
              </Typography>
              
              <Box sx={ { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 3 } }>
                { battleResults.map( ( result, index ) => {
                  const isExpanded = expandedCard === index;
                  const isSelected = selectedAI === result.name;
                  const aiEmojis: { [key: string]: string } = { 'Gemini': '🤖', 'Claude': '🧠', 'Gpt': '⚡', 'GPT': '⚡' };
                  const aiColors: { [key: string]: string } = { 'Gemini': '#4285F4', 'Claude': '#FF6B35', 'Gpt': '#10A37F', 'GPT': '#10A37F' };
                  
                  return (
                    <Box 
                      key={ index }
                      sx={ { 
                        p: 3, 
                        border: isSelected ? '2px solid #4caf50' : '2px solid #444',
                        borderRadius: 3, 
                        backgroundColor: 'linear-gradient(135deg, #1a1a2e 0%, #2d2d4e 100%)',
                        cursor: 'pointer',
                        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                        position: 'relative',
                        overflow: 'hidden',
                        transform: isSelected ? 'scale(1.02)' : 'none',
                        boxShadow: isSelected ? '0 8px 32px rgba(76, 175, 80, 0.3)' : 'none',
                        '&:hover': { 
                          borderColor: isSelected ? '#4caf50' : '#ffd700',
                          transform: 'translateY(-2px) scale(1.01)',
                          boxShadow: '0 8px 32px rgba(255, 215, 0, 0.25)'
                        },
                        '&::before': {
                          content: '""',
                          position: 'absolute',
                          top: 0,
                          left: 0,
                          right: 0,
                          height: '4px',
                          background: aiColors[result.name] || '#666',
                          borderRadius: '3px 3px 0 0'
                        }
                      } }
                      onClick={ () => setExpandedCard( isExpanded ? null : index ) }
                    >
                    <Box sx={ { display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 } }>
                      <Typography variant="h6" sx={ { 
                        color: '#fff',
                        display: 'flex',
                        alignItems: 'center',
                        gap: 1,
                        fontWeight: 'bold'
                      } }>
                        <span style={{fontSize: '1.2em'}}>{aiEmojis[result.name] || '🤖'}</span>
                        { result.name }
                      </Typography>
                      <Box sx={ { 
                        px: 2, py: 1, 
                        backgroundColor: result.score >= 80 ? '#4caf50' : result.score >= 60 ? '#ff9800' : '#f44336',
                        borderRadius: 2,
                        color: 'white',
                        fontSize: '0.85rem',
                        fontWeight: 'bold',
                        boxShadow: '0 2px 8px rgba(0,0,0,0.3)'
                      } }>
                        { typeof result.score === 'number' ? result.score.toFixed(1) : '85.0' }★
                      </Box>
                    </Box>
                    
                    <Typography variant="body2" sx={ { 
                      color: '#ccc', 
                      maxHeight: isExpanded ? 'none' : '120px', 
                      overflow: isExpanded ? 'visible' : 'auto',
                      fontSize: '0.9rem',
                      lineHeight: 1.5,
                      mb: 2,
                      padding: '12px',
                      backgroundColor: '#0a0a0f',
                      borderRadius: 1,
                      border: '1px solid #333',
                      whiteSpace: isExpanded ? 'pre-wrap' : 'normal'
                    } }>
                      { 
                        (() => {
                          const script = result.script;
                          let text = '';
                          if (typeof script === 'string') {
                            text = script;
                          } else if (script && typeof script === 'object') {
                            text = script.roteiro_completo || script.final_script_for_tts || script.script || script.content || 'Roteiro não disponível';
                          } else {
                            text = 'Roteiro não disponível';
                          }
                          
                          if (typeof text === 'string') {
                            return isExpanded ? text : text.substring(0, 200) + (text.length > 200 ? '...' : '');
                          }
                          return 'Roteiro não disponível';
                        })()
                      }
                    </Typography>
                    
                    {/* Indicador de expansão */}
                    <Box sx={{ textAlign: 'center', mb: 2 }}>
                      <Typography variant="caption" sx={{ color: '#888' }}>
                        {isExpanded ? '👆 Clique para recolher' : '👆 Clique para expandir e ler completo'}
                      </Typography>
                    </Box>
                    
                    <Button 
                      fullWidth
                      variant="contained"
                      size="large"
                      onClick={(e) => { e.stopPropagation(); handleSelectAI(result.name, result.script); }}
                      sx={ { 
                        backgroundColor: aiColors[result.name] || '#666',
                        color: '#fff',
                        fontWeight: 'bold',
                        py: 1.5,
                        mt: 2,
                        '&:hover': { 
                          backgroundColor: aiColors[result.name] ? `${aiColors[result.name]}dd` : '#888',
                          transform: 'scale(1.02)'
                        }
                      } }
                      startIcon={ <span>🗳️</span> }
                    >
                      ESCOLHER {result.name.toUpperCase()}
                    </Button>
                  </Box>
                  );
                })}
              </Box>
              
            </Box>
          ) }

          {/* Roteiro para Narração */}
          <TextField
            fullWidth
            multiline
            rows={ 8 }
            label="📝 Roteiro para Narração (texto limpo)"
            variant="outlined"
            value={ contentSettings.script || '' }
            onChange={ ( e ) => setScript( e.target.value ) }
            InputProps={ { style: { fontFamily: 'monospace' } } }
            sx={ { mt: 2 } }
          />

          {/* Prompts de Imagem */}
          { (battleResults.length > 0 || contentSettings.script) && (
            <TextField
              fullWidth
              multiline
              rows={ 10 }
              label="🎨 Prompts das Imagens (Imagen 3)"
              variant="outlined"
              value={ contentSettings.visual_prompts_text || getSelectedScriptData()?.visual_prompts_text || '' }
              onChange={(e) => updateSettings('visual_prompts_text', e.target.value)}
              InputProps={{ style: { fontFamily: 'monospace', fontSize: '0.9rem' } }}
              sx={{ mt: 2, '& .MuiInputBase-input': { color: '#4CAF50' } }}
            />
          )}

          {/* Prompts do Leonardo AI */}
          { (battleResults.length > 0 || contentSettings.script) && (
            <TextField
              fullWidth
              multiline
              rows={ 10 }
              label="🎬 Prompts de Animação (Leonardo AI)"
              variant="outlined"
              value={ contentSettings.leonardo_prompts_text || getSelectedScriptData()?.leonardo_prompts_text || '' }
              onChange={(e) => updateSettings('leonardo_prompts_text', e.target.value)}
              InputProps={{ style: { fontFamily: 'monospace', fontSize: '0.9rem' } }}
              sx={{ mt: 2, '& .MuiInputBase-input': { color: '#FF9800' } }}
            />
          )}

          <Alert severity="info" sx={ { mt: 2 } }>
            💡 <strong>Dica:</strong> O roteiro foi limpo para narração (sem tags). Os prompts de imagem e Leonardo AI são gerados automaticamente para o Step 3.
          </Alert>
          
          <Alert severity="warning" sx={ { mt: 1 } }>
            ⚠️ <strong>Importante:</strong> Esta seção é apenas para visualização dos prompts de imagem e animação. Para gerar as imagens reais, vá para o Step 3: Visual após configurar o áudio.
          </Alert>
        </Box>
      ) }

      { currentStep === 2 && (
        <Box sx={{ p: 3, backgroundColor: '#1a1a2e', borderRadius: 2, mb: 2 }}>
          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1, color: '#ffd700' }}>
            🎤 Áudio (Simplificado)
          </Typography>

          {/* Helper: preview snippet de ~4s */}
          {/* UI de três opções: Google 1, Google 2, ElevenLabs */}
          <AudioSimpleStep
            script={contentSettings.script || ''}
      onSelectComplete={(result) => {
              if (result?.audio_url) {
                updateSettings('audio_file', result.audio_url);
                updateSettings('preview_audio_file', undefined);
                updateSettings('last_audio_model', result.model || 'google');
                if (result.model === 'elevenlabs' && result.voice_profile) {
                  updateSettings('elevenlabs_voice', result.voice_profile);
                }
        // Concluir e avançar automaticamente para o Step 3
        completeStep(2);
              }
            }}
            buildApiUrl={buildApiUrl}
            safeFetch={safeFetch}
            buildMediaUrl={buildMediaUrl}
            cleanScriptForTTS={cleanScriptForTTS}
          />

          {/* Mostra status quando completo */}
          {contentSettings.audio_file && (
            <Box sx={{ mt: 3, p: 2, backgroundColor: 'rgba(76, 175, 80, 0.1)', borderRadius: 2, border: '1px solid #4CAF50' }}>
              <Typography variant="body2" sx={{ color: '#4CAF50', fontWeight: 'bold', mb: 1 }}>
                ✅ Áudio Completo Gerado
              </Typography>
              <audio controls style={{ width: '100%' }} key={`audio-${contentSettings.audio_file}-${Date.now()}`}>
                <source src={`${buildMediaUrl(contentSettings.audio_file)}?t=${Date.now()}`} type="audio/mp3" />
              </audio>
            </Box>
          )}
        </Box>
      ) }

      { currentStep === 3 && (
        <Box sx={ { p: 3, backgroundColor: '#1a1a2e', borderRadius: 2, mb: 2 } }>
          <Typography variant="h6" gutterBottom sx={ { display: 'flex', alignItems: 'center', gap: 1, color: '#ffd700' } }>
            🎨 Configuração Visual
          </Typography>
          
          <Typography variant="body2" sx={ { mb: 2, color: '#b0b0b0' } }>
            Otimize seu roteiro para gerar imagens perfeitas com IA:
          </Typography>
          
          <Box sx={ { display: 'flex', flexWrap: 'wrap', gap: 2, mb: 3 } }>
            {[
              { key: 'misterio', label: '🌙 Mistério', desc: 'Atmosfera escura e misteriosa' },
              { key: 'tecnologia', label: '⚡ Tecnologia', desc: 'Estilo futurista e tech' },
              { key: 'ciencia', label: '🧬 Ciência', desc: 'Visual científico e educativo' },
              { key: 'historia', label: '📜 História', desc: 'Épico e histórico' },
              { key: 'curiosidade', label: '🤔 Curiosidade', desc: 'Intrigante e colorido' }
            ].map((style) => (
              <Button
                key={style.key}
                variant={contentSettings.visual_style === style.key ? "contained" : "outlined"}
                onClick={() => updateSettings('visual_style', style.key)}
                sx={{ 
                  minWidth: '160px',
                  backgroundColor: contentSettings.visual_style === style.key ? '#ffd700' : 'transparent',
                  color: contentSettings.visual_style === style.key ? '#000' : '#fff',
                  border: '1px solid #444',
                  '&:hover': {
                    backgroundColor: contentSettings.visual_style === style.key ? '#ffed4e' : '#333'
                  }
                }}
                title={style.desc}
              >
                {style.label}
              </Button>
            ))}
          </Box>
          
          <Stack spacing={2} sx={{ mb: 2 }}>
            <Button
              variant="contained"
              size="large"
              onClick={handleOptimizePrompts}
              disabled={isGenerating || !contentSettings.script}
              sx={{
                backgroundColor: '#4a90e2',
                color: '#fff',
                fontWeight: 'bold',
                '&:hover': { backgroundColor: '#357abd' }
              }}
              startIcon={isGenerating ? <CircularProgress size={20} /> : <span>✨</span>}
            >
              {isGenerating ? 'Otimizando...' : '✨ Otimizar Prompts (Econômico)'}
            </Button>
            
            <Button
              variant="contained"
              size="large"
              onClick={handleOptimizeVisualPrompts}
              disabled={isGenerating || !contentSettings.script}
              sx={{
                backgroundColor: '#ff6b35',
                color: '#fff',
                fontWeight: 'bold',
                '&:hover': { backgroundColor: '#ff8555' }
              }}
              startIcon={isGenerating ? <CircularProgress size={20} /> : <span>🔥</span>}
            >
              {isGenerating ? 'Gerando Imagens...' : '🚀 Gerar Imagens'}
            </Button>
          </Stack>
          
          <Alert severity="info" sx={{ mt: 2 }}>
            💡 <strong>Dica:</strong> Use "Otimizar Prompts" primeiro para refinar e limpar os prompts sem gastar créditos, depois "Gerar Imagens" para criar as imagens finais.
          </Alert>
          
          {/* Prompts Otimizados */}
          {optimizedPrompts.length > 0 && (
            <Box sx={{ mt: 3 }}>
              <Typography variant="h6" sx={{ color: '#4a90e2', mb: 2 }}>
                ✨ Prompts Otimizados ({optimizedPrompts.length})
              </Typography>
              
              <Alert severity="success" sx={{ mb: 2 }}>
                🎯 Prompts otimizados com sucesso! Agora você pode gerar imagens com qualidade superior.
              </Alert>
              
              <Box sx={{ maxHeight: '300px', overflowY: 'auto', p: 2, backgroundColor: 'rgba(74, 144, 226, 0.1)', borderRadius: 2 }}>
                {optimizedPrompts.map((scene, index) => (
                  <Box key={index} sx={{ mb: 2, pb: 2, borderBottom: index < optimizedPrompts.length - 1 ? '1px solid #333' : 'none' }}>
                    <Typography variant="subtitle2" sx={{ color: '#4a90e2', mb: 1 }}>
                      🎬 Cena {index + 1}
                    </Typography>
                    <Typography variant="body2" sx={{ color: '#e0e0e0', mb: 1 }}>
                      <strong>Prompt:</strong> {scene.image_prompt || scene.prompt}
                    </Typography>
                    {scene.leonardo_motion && (
                      <Typography variant="body2" sx={{ color: '#ffd700' }}>
                        <strong>Movimento:</strong> {scene.leonardo_motion}
                      </Typography>
                    )}
                  </Box>
                ))}
              </Box>
            </Box>
          )}
          
          {/* Loading da otimização */}
          {isOptimizingPrompts && (
            <Box sx={{ mt: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                <CircularProgress size={20} />
                <Typography variant="body2" sx={{ color: '#4a90e2' }}>
                  ✨ Otimizando prompts para melhor qualidade...
                </Typography>
              </Box>
              <Alert severity="info">
                💡 A IA está limpando e melhorando seus prompts para garantir imagens de alta qualidade sem desperdiçar créditos.
              </Alert>
            </Box>
          )}
          
          {/* Progresso da geração */}
          {isGenerating && generationProgress > 0 && (
            <Box sx={{ mt: 3 }}>
              <Typography variant="body2" sx={{ mb: 1, color: '#ffd700' }}>
                {generationProgress <= 30 ? '⚙️ Otimizando prompts...' :
                 generationProgress <= 80 ? '🎨 Gerando imagens...' : 
                 '✅ Finalizando...'}
              </Typography>
              <LinearProgress 
                variant="determinate" 
                value={generationProgress} 
                sx={{ 
                  height: 8, 
                  borderRadius: 4,
                  backgroundColor: 'rgba(255, 215, 0, 0.2)',
                  '& .MuiLinearProgress-bar': { backgroundColor: '#ffd700' }
                }} 
              />
              <Typography variant="caption" sx={{ color: '#ccc', mt: 1, display: 'block' }}>
                {generationProgress}% concluído
              </Typography>
            </Box>
          )}
          
          {/* Galeria de Imagens Geradas */}
          {generatedImages.length > 0 && (
            <Box sx={{ mt: 4 }}>
              <Typography variant="h6" sx={{ color: '#ffd700', mb: 2 }}>
                🖼️ Imagens Geradas ({generatedImages.length})
              </Typography>
              
              {/* Debug info */}
              <Typography variant="caption" sx={{ color: '#666', display: 'block', mb: 2 }}>
                Debug: {JSON.stringify(generatedImages[0], null, 2)}
              </Typography>
              
              <Box sx={{ 
                display: 'grid', 
                gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
                gap: 2 
              }}>
                {generatedImages.map((image, index) => (
                  <Box 
                    key={index}
                    sx={{ 
                      border: '2px solid #444',
                      borderRadius: 2,
                      overflow: 'hidden',
                      backgroundColor: '#0a0a0f',
                      transition: 'all 0.3s ease',
                      '&:hover': {
                        borderColor: '#ffd700',
                        transform: 'scale(1.02)'
                      }
                    }}
                  >
                    <img 
                      src={buildMediaUrl(image.url || image.image_url)}
                      alt={`Cena ${index + 1}`}
                      style={{
                        width: '100%',
                        height: '150px',
                        objectFit: 'cover'
                      }}
                      onError={(e) => {
                        const target = e.target as HTMLImageElement;
                        target.style.display = 'none';
                        const nextSibling = target.nextElementSibling as HTMLElement;
                        if (nextSibling) {
                          nextSibling.style.display = 'flex';
                        }
                      }}
                    />
                    <Box sx={{ 
                      display: 'none',
                      height: '150px',
                      alignItems: 'center',
                      justifyContent: 'center',
                      backgroundColor: '#1a1a2e',
                      color: '#666'
                    }}>
                      🖼️ Erro ao carregar
                    </Box>
                    
                    <Box sx={{ p: 2 }}>
                      <Typography variant="caption" sx={{ 
                        color: '#ffd700', 
                        fontWeight: 'bold' 
                      }}>
                        Cena {index + 1}
                      </Typography>
                      <Typography variant="body2" sx={{ 
                        color: '#ccc',
                        fontSize: '0.8rem',
                        mt: 0.5,
                        display: '-webkit-box',
                        WebkitLineClamp: 2,
                        WebkitBoxOrient: 'vertical',
                        overflow: 'hidden'
                      }}>
                        {image.prompt || 'Prompt otimizado automaticamente'}
                      </Typography>

                      {/* Trocar imagem por prompt (inline) */}
                      <Box sx={{ mt: 1.5, display: 'flex', gap: 1 }}>
                        <TextField
                          size="small"
                          fullWidth
                          variant="outlined"
                          placeholder={`Novo prompt para a cena ${index + 1}`}
                          value={replacePrompt}
                          onChange={(e) => setReplacePrompt(e.target.value)}
                          InputProps={{
                            sx: { backgroundColor: '#111', color: '#ddd' }
                          }}
                        />
                        <Button
                          variant="contained"
                          size="small"
                          onClick={() => handleReplaceImage(index)}
                          disabled={!!replacingIndex || !replacePrompt.trim()}
                          sx={{
                            backgroundColor: '#ffd700',
                            color: '#000',
                            minWidth: 90,
                            '&:hover': { backgroundColor: '#ffed4e' }
                          }}
                        >
                          {replacingIndex === index ? <CircularProgress size={16} /> : 'Trocar'}
                        </Button>
                      </Box>
                    </Box>
                  </Box>
                ))}
              </Box>
              
              <Alert severity="success" sx={{ mt: 3 }}>
                ✅ <strong>Imagens prontas!</strong> Suas cenas foram geradas com qualidade profissional usando IA.
              </Alert>
            </Box>
          )}
        </Box>
      ) }

      {/* Step 4: Leonardo AI Animation */}
      { currentStep === 4 && (
        <Box>
          <Typography variant="h5" sx={{ color: '#ffd700', fontWeight: 'bold', mb: 3 }}>
            🎬 Step 4: Renderização Completa do Vídeo
          </Typography>
          
          <Alert severity="info" sx={{ mb: 3 }}>
            <Typography>
              🚀 <strong>Crie seu vídeo completo!</strong> Integrando imagens, animações Leonardo AI, narração ElevenLabs e música de fundo.
              Pipeline completo: Imagens → Animação → TTS → Montagem Final.
            </Typography>
          </Alert>
          
          {generatedImages.length > 0 ? (
            <Stack spacing={3}>
              {/* Preview das Imagens Geradas */}
              <Box sx={{ 
                p: 3, 
                backgroundColor: 'rgba(255, 215, 0, 0.05)', 
                borderRadius: 2, 
                border: '1px solid rgba(255, 215, 0, 0.2)' 
              }}>
                <Typography variant="h6" sx={{ color: '#ffd700', mb: 2 }}>
                  🖼️ Imagens Geradas para Animação
                </Typography>
                
                <Box sx={{ 
                  display: 'grid', 
                  gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', 
                  gap: 2 
                }}>
                  {generatedImages.map((image, index) => (
                    <Box key={index} sx={{ 
                      border: '2px solid #ffd700', 
                      borderRadius: 2, 
                      overflow: 'hidden',
                      backgroundColor: 'rgba(0,0,0,0.3)'
                    }}>
                      <img
                        src={buildMediaUrl(image.url)}
                        alt={`Cena ${index + 1}`}
                        style={{
                          width: '100%',
                          height: '120px',
                          objectFit: 'cover'
                        }}
                        onError={(e) => {
                          console.error(`Erro ao carregar imagem ${index + 1}:`, image.url);
                          e.currentTarget.style.display = 'none';
                        }}
                      />
                      <Box sx={{ p: 1, textAlign: 'center' }}>
                        <Typography variant="caption" sx={{ color: '#ffd700' }}>
                          Cena {index + 1}
                        </Typography>
                      </Box>
                    </Box>
                  ))}
                </Box>
              </Box>

              {/* Controles Veo - Movimento Sutil para cada Imagem */}
              <Box sx={{ 
                p: 3, 
                backgroundColor: 'rgba(138, 43, 226, 0.05)', 
                borderRadius: 2, 
                border: '1px solid rgba(138, 43, 226, 0.3)' 
              }}>
                <Typography variant="h6" sx={{ color: '#8A2BE2', mb: 2, display: 'flex', alignItems: 'center' }}>
                  🎥 Veo AI - Movimento Sutil (3s por imagem)
                  <Box sx={{ ml: 2, px: 1, py: 0.5, backgroundColor: 'rgba(138, 43, 226, 0.2)', borderRadius: 1, fontSize: '0.7rem' }}>
                    NOVO
                  </Box>
                </Typography>
                
                <Alert severity="info" sx={{ mb: 3, backgroundColor: 'rgba(138, 43, 226, 0.1)', border: '1px solid rgba(138, 43, 226, 0.3)' }}>
                  <Typography variant="body2">
                    🚀 <strong>Vertex AI Veo:</strong> Gera movimento cinematográfico sutil de 3 segundos para cada imagem. 
                    Ideal para criar micro-animações profissionais que mantêm o foco no conteúdo.
                  </Typography>
                </Alert>

                {/* Presets de Movimento */}
                <Box sx={{ mb: 3 }}>
                  <Typography variant="subtitle2" sx={{ color: '#8A2BE2', mb: 2 }}>
                    🎬 Presets de Movimento
                  </Typography>
                  <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 2 }}>
                    {[
                      { id: 'subtle_breath', name: 'Respiração Natural', prompt: 'Movimento sutil de respiração, iluminação suave oscilando, efeito natural orgânico' },
                      { id: 'gentle_sway', name: 'Balanço Suave', prompt: 'Movimento suave de balanço, câmera estável, movimento hipnótico lento' },
                      { id: 'soft_zoom', name: 'Zoom Suave', prompt: 'Zoom in muito lento e suave, foco progressivo, movimento cinematográfico' },
                      { id: 'light_shift', name: 'Mudança de Luz', prompt: 'Mudança sutil na iluminação, sombras dançando suavemente, atmosfera dinâmica' },
                      { id: 'floating_cam', name: 'Câmera Flutuante', prompt: 'Movimento flutuante da câmera, estabilizado, perspectiva etérea' },
                      { id: 'custom', name: 'Personalizado', prompt: '' }
                    ].map(preset => (
                      <Button
                        key={preset.id}
                        variant={contentSettings.veo_motion_preset === preset.id ? 'contained' : 'outlined'}
                        onClick={() => {
                          onSettingsChange({
                            ...contentSettings, 
                            veo_motion_preset: preset.id,
                            veo_custom_prompt: preset.id === 'custom' ? (contentSettings.veo_custom_prompt || '') : preset.prompt
                          });
                        }}
                        sx={{
                          p: 2,
                          height: 'auto',
                          flexDirection: 'column',
                          alignItems: 'flex-start',
                          backgroundColor: contentSettings.veo_motion_preset === preset.id ? '#8A2BE2' : 'transparent',
                          color: contentSettings.veo_motion_preset === preset.id ? '#fff' : '#8A2BE2',
                          borderColor: '#8A2BE2',
                          '&:hover': { 
                            backgroundColor: contentSettings.veo_motion_preset === preset.id ? '#9932CC' : 'rgba(138, 43, 226, 0.1)'
                          }
                        }}
                      >
                        <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 0.5 }}>
                          {preset.name}
                        </Typography>
                        <Typography variant="caption" sx={{ textAlign: 'left', opacity: 0.8, fontSize: '0.7rem' }}>
                          {preset.id === 'custom' ? 'Crie seu próprio prompt' : preset.prompt.substring(0, 50) + '...'}
                        </Typography>
                      </Button>
                    ))}
                  </Box>
                </Box>

                {/* Prompt Personalizado */}
                {contentSettings.veo_motion_preset === 'custom' && (
                  <Box sx={{ mb: 3 }}>
                    <Typography variant="subtitle2" sx={{ color: '#8A2BE2', mb: 1 }}>
                      ✍️ Prompt Personalizado
                    </Typography>
                    <TextField
                      fullWidth
                      multiline
                      rows={3}
                      placeholder="Ex: Movimento suave de câmera para a esquerda, zoom out lento, partículas de luz flutuando..."
                      value={contentSettings.veo_custom_prompt || ''}
                      onChange={(e) => onSettingsChange({
                        ...contentSettings, 
                        veo_custom_prompt: e.target.value
                      })}
                      sx={{
                        '& .MuiOutlinedInput-root': {
                          '& fieldset': { borderColor: '#8A2BE2' },
                          '&:hover fieldset': { borderColor: '#9932CC' },
                          '&.Mui-focused fieldset': { borderColor: '#8A2BE2' }
                        },
                        '& .MuiInputLabel-root': { color: '#8A2BE2' },
                        '& .MuiInputBase-input': { color: '#fff' }
                      }}
                    />
                  </Box>
                )}

                {/* Botões de Ação Veo */}
                <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                  <Button
                    variant="contained"
                    onClick={handleVeoProcessImages}
                    disabled={!contentSettings.veo_motion_preset || (contentSettings.veo_motion_preset === 'custom' && !contentSettings.veo_custom_prompt?.trim()) || isRenderingVideo}
                    startIcon={isRenderingVideo ? <CircularProgress size={16} /> : <MovieIcon />}
                    sx={{
                      backgroundColor: '#8A2BE2',
                      color: '#fff',
                      fontWeight: 'bold',
                      '&:hover': { backgroundColor: '#9932CC' },
                      '&:disabled': { backgroundColor: '#666', color: '#999' }
                    }}
                  >
                    {isRenderingVideo ? 'Processando...' : `🎬 Processar ${generatedImages.length} Imagens`}
                  </Button>
                  
                  <Button
                    variant="outlined"
                    onClick={handleVeoTestImage}
                    disabled={!contentSettings.veo_motion_preset || generatedImages.length === 0 || (contentSettings.veo_motion_preset === 'custom' && !contentSettings.veo_custom_prompt?.trim()) || isRenderingVideo}
                    sx={{
                      borderColor: '#8A2BE2',
                      color: '#8A2BE2',
                      '&:hover': { backgroundColor: 'rgba(138, 43, 226, 0.1)' },
                      '&:disabled': { borderColor: '#666', color: '#999' }
                    }}
                  >
                    🧪 Testar 1 Imagem
                  </Button>
                </Box>
              </Box>

              {/* Seleção de Prompt de Movimento */}
              <Box sx={{ 
                p: 3, 
                backgroundColor: 'rgba(255, 215, 0, 0.05)', 
                borderRadius: 2, 
                border: '1px solid rgba(255, 215, 0, 0.2)' 
              }}>
                <Typography variant="h6" sx={{ color: '#ffd700', mb: 2 }}>
                  🎞️ Leonardo AI - Estilo de Movimento
                </Typography>
                
                <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: 2 }}>
                  {[
                    { id: 'subtle_movement', name: 'Movimento Sutil', description: 'Respiração natural, efeitos suaves de vento', icon: '�' },
                    { id: 'dynamic_zoom', name: 'Zoom Dinâmico', description: 'Zoom cinematográfico, mudança de foco', icon: '🎯' },
                    { id: 'floating_elements', name: 'Elementos Flutuantes', description: 'Partículas mágicas, atmosfera etérea', icon: '✨' },
                    { id: 'perspective_shift', name: 'Mudança de Perspectiva', description: 'Rotação 3D, movimento espacial', icon: '�' },
                    { id: 'energy_pulse', name: 'Pulso de Energia', description: 'Ondas de energia, movimento rítmico', icon: '⚡' }
                  ].map(motion => (
                    <Button
                      key={motion.id}
                      variant={contentSettings.leonardo_motion === motion.id ? 'contained' : 'outlined'}
                      onClick={() => onSettingsChange({...contentSettings, leonardo_motion: motion.id})}
                      sx={{
                        p: 2,
                        height: 'auto',
                        flexDirection: 'column',
                        alignItems: 'flex-start',
                        backgroundColor: contentSettings.leonardo_motion === motion.id ? '#ffd700' : 'transparent',
                        color: contentSettings.leonardo_motion === motion.id ? '#000' : '#ffd700',
                        borderColor: '#ffd700',
                        '&:hover': { 
                          backgroundColor: contentSettings.leonardo_motion === motion.id ? '#ffed4e' : 'rgba(255, 215, 0, 0.1)'
                        }
                      }}
                    >
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                        <Typography variant="h6" sx={{ mr: 1 }}>{motion.icon}</Typography>
                        <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                          {motion.name}
                        </Typography>
                      </Box>
                      <Typography variant="caption" sx={{ textAlign: 'left', opacity: 0.8 }}>
                        {motion.description}
                      </Typography>
                    </Button>
                  ))}
                </Box>
              </Box>

              {/* Botão de Animação */}
              <Box sx={{ textAlign: 'center', mt: 3 }}>
                <Button
                  variant="contained"
                  size="large"
                  onClick={handleCompleteVideoRender}
                  disabled={isRenderingVideo || !contentSettings.leonardo_motion}
                  startIcon={isRenderingVideo ? <CircularProgress size={20} /> : <MovieIcon />}
                  sx={{
                    backgroundColor: '#ffd700',
                    color: '#000',
                    fontWeight: 'bold',
                    py: 2,
                    px: 4,
                    fontSize: '1.1rem',
                    '&:hover': { backgroundColor: '#ffed4e' },
                    '&:disabled': { backgroundColor: '#666', color: '#999' }
                  }}
                >
                  {isRenderingVideo ? 'Renderizando Vídeo Completo...' : '🎬 Criar Vídeo Completo'}
                </Button>
                <Box sx={{ mt: 2 }}>
                  <Button
                    variant="outlined"
                    size="medium"
                    onClick={handleLeonardoDirectVideo}
                    disabled={isRenderingVideo || !contentSettings.leonardo_motion}
                    sx={{
                      borderColor: '#ffd700',
                      color: '#ffd700',
                      fontWeight: 'bold',
                      '&:hover': { backgroundColor: 'rgba(255, 215, 0, 0.1)' },
                      '&:disabled': { borderColor: '#666', color: '#999' }
                    }}
                  >
                    🎞️ Gerar Vídeo (Leonardo Direto)
                  </Button>
                </Box>
                
                {!contentSettings.leonardo_motion && (
                  <Typography variant="caption" sx={{ display: 'block', mt: 1, color: '#ff6b6b' }}>
                    Selecione um estilo de movimento para continuar
                  </Typography>
                )}
              </Box>

              {/* Configurações Adicionais */}
              <Box sx={{ 
                p: 3, 
                backgroundColor: 'rgba(255, 215, 0, 0.05)', 
                borderRadius: 2, 
                border: '1px solid rgba(255, 215, 0, 0.2)' 
              }}>
                <Typography variant="h6" sx={{ color: '#ffd700', mb: 2 }}>
                  🎬 Configurações Finais
                </Typography>
                
                <Stack spacing={2}>
                  {/* Transições */}
                  <Box>
                    <Typography variant="subtitle2" sx={{ color: '#ffd700', mb: 1 }}>
                      Transições entre Cenas
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                      {[
                        { name: 'Fade Suave', value: 'fade', icon: '🌅' },
                        { name: 'Corte Rápido', value: 'cut', icon: '⚡' },
                        { name: 'Dinâmico', value: 'dynamic', icon: '🔍' },
                        { name: 'Suave', value: 'smooth', icon: '➡️' }
                      ].map(transition => (
                        <Button
                          key={transition.value}
                          variant={contentSettings.transitions === transition.value ? 'contained' : 'outlined'}
                          size="small"
                          onClick={() => onSettingsChange({...contentSettings, transitions: transition.value as any})}
                          startIcon={<span>{transition.icon}</span>}
                          sx={{
                            backgroundColor: contentSettings.transitions === transition.value ? '#ffd700' : 'transparent',
                            color: contentSettings.transitions === transition.value ? '#000' : '#ffd700',
                            borderColor: '#ffd700'
                          }}
                        >
                          {transition.name}
                        </Button>
                      ))}
                    </Box>
                  </Box>

                  {/* Legendas */}
                  <Box>
                    <Typography variant="subtitle2" sx={{ color: '#ffd700', mb: 1 }}>
                      Estilo das Legendas
                    </Typography>
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                      {[
            { name: 'Moderno', value: 'moderno', icon: '🔥' },
            { name: 'Neon', value: 'neon', icon: '💫' },
            { name: 'Neon Amarelo', value: 'neon_yellow', icon: '🟡' },
            { name: 'Elegante', value: 'elegante', icon: '✨' }
                      ].map(subtitle => (
                        <Button
                          key={subtitle.value}
                          variant={contentSettings.subtitle_style === subtitle.value ? 'contained' : 'outlined'}
                          size="small"
                          onClick={() => onSettingsChange({...contentSettings, subtitle_style: subtitle.value as any})}
                          startIcon={<span>{subtitle.icon}</span>}
                          sx={{
                            backgroundColor: contentSettings.subtitle_style === subtitle.value ? '#ffd700' : 'transparent',
                            color: contentSettings.subtitle_style === subtitle.value ? '#000' : '#ffd700',
                            borderColor: '#ffd700'
                          }}
                        >
                          {subtitle.name}
                        </Button>
                      ))}
                    </Box>
                  </Box>
                </Stack>

                {/* Música de Fundo */}
                <Box sx={{ mt: 3 }}>
                  <Typography variant="subtitle2" sx={{ color: '#ffd700', mb: 1 }}>
                    Música de Fundo
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 1 }}>
                    {['upbeat','chill','energetic','ambient','none'].map(cat => (
                      <Button
                        key={cat}
                        variant={(contentSettings.background_music || 'upbeat') === cat ? 'contained' : 'outlined'}
                        size="small"
                        onClick={() => onSettingsChange({...contentSettings, background_music: cat})}
                        sx={{
                          backgroundColor: (contentSettings.background_music || 'upbeat') === cat ? '#ffd700' : 'transparent',
                          color: (contentSettings.background_music || 'upbeat') === cat ? '#000' : '#ffd700',
                          borderColor: '#ffd700'
                        }}
                      >
                        {cat === 'none' ? 'Sem Música' : cat}
                      </Button>
                    ))}
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <Typography variant="caption" sx={{ color: '#ffd700' }}>Volume</Typography>
                    <input
                      type="range"
                      min={0}
                      max={0.8}
                      step={0.05}
                      value={contentSettings.music_volume ?? contentSettings.background_music_volume ?? 0.3}
                      onChange={(e) => onSettingsChange({...contentSettings, music_volume: Number(e.target.value), background_music_volume: Number(e.target.value)})}
                      style={{ width: 220 }}
                    />
                    <Typography variant="caption" sx={{ color: '#ffd700' }}>{(contentSettings.music_volume ?? 0.3).toFixed(2)}</Typography>
                  </Box>
                </Box>

                {/* Pacing (Cortes por imagem) */}
                <Box sx={{ mt: 3 }}>
                  <Typography variant="subtitle2" sx={{ color: '#ffd700', mb: 1 }}>
                    Pacing dos cortes (por imagem)
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center' }}>
                    <TextField
                      label="Min Cut (s)"
                      type="number"
                      size="small"
                      inputProps={{ step: 0.1, min: 0.5, max: 5 }}
                      value={contentSettings.min_cut ?? 1.5}
                      onChange={(e) => onSettingsChange({...contentSettings, min_cut: Number(e.target.value)})}
                      sx={{ width: 130 }}
                    />
                    <TextField
                      label="Max Cut (s)"
                      type="number"
                      size="small"
                      inputProps={{ step: 0.1, min: 1, max: 6 }}
                      value={contentSettings.max_cut ?? 3.0}
                      onChange={(e) => onSettingsChange({...contentSettings, max_cut: Number(e.target.value)})}
                      sx={{ width: 130 }}
                    />
                    <Typography variant="caption" sx={{ color: '#ffd700' }}>
                      Dica: mantenha ≤ 3.0s para dinamismo.
                    </Typography>
                  </Box>
                </Box>
              </Box>
            </Stack>
          ) : (
            <Alert severity="warning" sx={{ mt: 2 }}>
              <Typography>
                ⚠️ Nenhuma imagem foi gerada ainda. Volte ao Step 3 para gerar as imagens primeiro.
              </Typography>
            </Alert>
          )}
        </Box>
      )}

      {/* Step 5: Multi-Plataforma */}
      { currentStep === 5 && (
        <Box>
          <Typography variant="h5" sx={{ color: '#ffd700', fontWeight: 'bold', mb: 3 }}>
            🎯 Step 5: Multi-Plataforma
          </Typography>
          
          <Box sx={{ 
            p: 3, 
            backgroundColor: 'rgba(255, 215, 0, 0.05)', 
            borderRadius: 2, 
            border: '1px solid rgba(255, 215, 0, 0.2)' 
          }}>
            <Typography variant="h6" sx={{ color: '#ffd700', mb: 2 }}>
              📱 Selecione as Plataformas de Destino
            </Typography>
            
            <Typography variant="body2" sx={{ color: '#ccc', mb: 3 }}>
              Escolha as plataformas onde você quer publicar. O vídeo será otimizado para cada proporção específica.
            </Typography>
            
            <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: 3 }}>
              {[
                { 
                  name: 'TikTok', 
                  value: 'tiktok', 
                  icon: '🎵', 
                  ratio: '9:16 (Vertical)',
                  desc: 'Perfeito para viralizar no TikTok',
                  color: '#000'
                },
                { 
                  name: 'Instagram Reels', 
                  value: 'instagram', 
                  icon: '📸', 
                  ratio: '9:16 (Vertical)',
                  desc: 'Stories e Reels do Instagram',
                  color: '#E4405F'
                },
                { 
                  name: 'YouTube Shorts', 
                  value: 'youtube_shorts', 
                  icon: '🩳', 
                  ratio: '9:16 (Vertical)',
                  desc: 'Shorts do YouTube para crescer rápido',
                  color: '#FF0000'
                },
                { 
                  name: 'YouTube', 
                  value: 'youtube', 
                  icon: '📺', 
                  ratio: '16:9 (Horizontal)',
                  desc: 'Vídeos tradicionais do YouTube',
                  color: '#FF0000'
                },
                { 
                  name: 'Kwai', 
                  value: 'kwai', 
                  icon: '🌟', 
                  ratio: '9:16 (Vertical)',
                  desc: 'Rede social em crescimento',
                  color: '#FF6B35'
                }
              ].map(platform => {
                const isSelected = contentSettings.target_platforms?.includes(platform.value) || false;
                
                return (
                  <Box
                    key={platform.value}
                    onClick={() => {
                      const currentPlatforms = contentSettings.target_platforms || [];
                      const newPlatforms = isSelected 
                        ? currentPlatforms.filter(p => p !== platform.value)
                        : [...currentPlatforms, platform.value];
                      onSettingsChange({...contentSettings, target_platforms: newPlatforms});
                    }}
                    sx={{
                      p: 3,
                      borderRadius: 3,
                      cursor: 'pointer',
                      border: isSelected ? `2px solid ${platform.color}` : '2px solid #444',
                      backgroundColor: isSelected ? `${platform.color}15` : 'rgba(255, 255, 255, 0.02)',
                      transition: 'all 0.3s ease',
                      '&:hover': {
                        transform: 'translateY(-2px)',
                        borderColor: platform.color,
                        backgroundColor: `${platform.color}10`
                      }
                    }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                        <span style={{ fontSize: '1.5em' }}>{platform.icon}</span>
                        <Typography variant="h6" sx={{ color: '#fff', fontWeight: 'bold' }}>
                          {platform.name}
                        </Typography>
                      </Box>
                      <Box sx={{
                        width: 24,
                        height: 24,
                        borderRadius: '50%',
                        border: `2px solid ${isSelected ? platform.color : '#666'}`,
                        backgroundColor: isSelected ? platform.color : 'transparent',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center'
                      }}>
                        {isSelected && <span style={{ color: 'white', fontSize: '14px' }}>✓</span>}
                      </Box>
                    </Box>
                    
                    <Typography variant="body2" sx={{ color: '#ccc', mb: 1 }}>
                      {platform.desc}
                    </Typography>
                    
                    <Typography variant="caption" sx={{ 
                      color: platform.color, 
                      fontWeight: 'bold',
                      backgroundColor: `${platform.color}20`,
                      px: 1,
                      py: 0.5,
                      borderRadius: 1,
                      display: 'inline-block'
                    }}>
                      {platform.ratio}
                    </Typography>
                  </Box>
                );
              })}
            </Box>
            
            {contentSettings.target_platforms && contentSettings.target_platforms.length > 0 && (
              <Alert severity="success" sx={{ mt: 3 }}>
                ✅ {contentSettings.target_platforms.length} plataforma(s) selecionada(s): {contentSettings.target_platforms.join(', ')}
              </Alert>
            )}
          </Box>
        </Box>
      ) }

      {/* Step 6: Pré-visualização */}
      { currentStep === 6 && (
        <Box>
          <Typography variant="h5" sx={{ color: '#ffd700', fontWeight: 'bold', mb: 3 }}>
            👁️ Step 6: Pré-visualização e Finalização
          </Typography>
          
          <Box sx={{ 
            p: 3, 
            backgroundColor: 'rgba(255, 215, 0, 0.05)', 
            borderRadius: 2, 
            border: '1px solid rgba(255, 215, 0, 0.2)' 
          }}>
            <Typography variant="h6" sx={{ color: '#ffd700', mb: 2 }}>
              📋 Resumo da Configuração
            </Typography>
            
            <Stack spacing={2}>
              {/* Roteiro */}
              <Box sx={{ p: 2, backgroundColor: '#0a0a0f', borderRadius: 1 }}>
                <Typography variant="subtitle1" sx={{ color: '#4caf50', fontWeight: 'bold', mb: 1 }}>
                  📝 Roteiro ({videoDuration}s)
                </Typography>
                <Typography variant="body2" sx={{ color: '#ccc' }}>
                  {contentSettings.script ? 
                    `${contentSettings.script.substring(0, 100)}...` : 
                    'Nenhum roteiro selecionado'}
                </Typography>
              </Box>
              
              {/* Áudio */}
              <Box sx={{ p: 2, backgroundColor: '#0a0a0f', borderRadius: 1 }}>
                <Typography variant="subtitle1" sx={{ color: '#4caf50', fontWeight: 'bold', mb: 1 }}>
                  🎤 Configuração de Áudio
                </Typography>
                <Typography variant="body2" sx={{ color: '#ccc' }}>
                  Perfil: {contentSettings.voice_profile || 'male-professional'} | 
                  Emoção: {contentSettings.voice_emotion || 'neutral'} | 
                  Velocidade: {contentSettings.speaking_speed || 1.0}x
                </Typography>
              </Box>
              
              {/* Visual */}
              <Box sx={{ p: 2, backgroundColor: '#0a0a0f', borderRadius: 1 }}>
                <Typography variant="subtitle1" sx={{ color: '#4caf50', fontWeight: 'bold', mb: 1 }}>
                  🎨 Estilo Visual
                </Typography>
                <Typography variant="body2" sx={{ color: '#ccc' }}>
                  Estilo: {contentSettings.visual_style || 'realista'} | 
                  Imagens geradas: {generatedImages.length || 0}
                </Typography>
              </Box>
              
              {/* Efeitos */}
              <Box sx={{ p: 2, backgroundColor: '#0a0a0f', borderRadius: 1 }}>
                <Typography variant="subtitle1" sx={{ color: '#4caf50', fontWeight: 'bold', mb: 1 }}>
                  ✨ Efeitos e Transições
                </Typography>
                <Typography variant="body2" sx={{ color: '#ccc' }}>
                  Transições: {contentSettings.transitions || 'fade'} | 
                  Legendas: {contentSettings.subtitle_style || 'tiktok'} | 
                  Música: {contentSettings.background_music || 'upbeat'}
                </Typography>
              </Box>
              
              {/* Plataformas */}
              <Box sx={{ p: 2, backgroundColor: '#0a0a0f', borderRadius: 1 }}>
                <Typography variant="subtitle1" sx={{ color: '#4caf50', fontWeight: 'bold', mb: 1 }}>
                  🎯 Plataformas de Destino
                </Typography>
                <Typography variant="body2" sx={{ color: '#ccc' }}>
                  {contentSettings.target_platforms && contentSettings.target_platforms.length > 0 ? 
                    contentSettings.target_platforms.join(', ') : 
                    'Nenhuma plataforma selecionada'}
                </Typography>
              </Box>
            </Stack>
          </Box>
          
          {/* Pré-visualização do vídeo */}
          {videoPreview && (
            <Box sx={{ mt: 4 }}>
              <Typography variant="h6" sx={{ color: '#ffd700', mb: 2 }}>
                🎬 Pré-visualização do Vídeo
              </Typography>
              
              <Box sx={{ 
                display: 'flex',
                justifyContent: 'center',
                p: 3,
                backgroundColor: '#0a0a0f',
                borderRadius: 2,
                border: '2px solid #444'
              }}>
                <video 
                  src={videoPreview}
                  controls
                  style={{
                    maxWidth: '400px',
                    width: '100%',
                    borderRadius: '8px'
                  }}
                />
              </Box>
              
              <Alert severity="success" sx={{ mt: 2 }}>
                ✅ <strong>Pré-visualização pronta!</strong> Revise o vídeo e clique em "Gerar Vídeo Final" para finalizar.
              </Alert>
            </Box>
          )}
          
          {/* Validações antes de gerar */}
          <Box sx={{ mt: 4 }}>
            <Typography variant="h6" sx={{ color: '#ffd700', mb: 2 }}>
              ✅ Validações
            </Typography>
            
            <Stack spacing={1}>
              {[
                { check: !!contentSettings.script, label: 'Roteiro definido' },
                { check: generatedImages.length > 0, label: 'Imagens geradas' },
                { check: !!(contentSettings.voice_profile || contentSettings.audio_file || contentSettings.preview_audio_file), label: 'Voz configurada' },
                { check: !!contentSettings.transitions, label: 'Efeitos configurados' },
                { check: (contentSettings.target_platforms?.length ?? 0) > 0, label: 'Plataformas selecionadas' }
              ].map((validation, index) => (
                <Box key={index} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <span style={{ color: validation.check ? '#4caf50' : '#f44336' }}>
                    {validation.check ? '✅' : '❌'}
                  </span>
                  <Typography variant="body2" sx={{ 
                    color: validation.check ? '#4caf50' : '#f44336' 
                  }}>
                    {validation.label}
                  </Typography>
                </Box>
              ))}
            </Stack>
            
            {!videoPreview && (
              <Alert severity="info" sx={{ mt: 2 }}>
                💡 Clique em "Gerar Vídeo Final" para criar seu vídeo personalizado com todas as configurações escolhidas.
              </Alert>
            )}
          </Box>
        </Box>
      ) }

      {/* Exibir erros se existirem */ }
      { error && <Alert severity="error" sx={ { mb: 2 } }>{ error }</Alert> }

      {/* Navegação dos botões */ }
      <Box sx={ { mt: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' } }>
        <Button 
          variant="outlined" 
          onClick={ () => setCurrentStep( Math.max( 1, currentStep - 1 ) ) }
          disabled={ currentStep === 1 }
          sx={{
            borderColor: '#666',
            color: '#ccc',
            '&:hover': { 
              borderColor: '#888', 
              backgroundColor: 'rgba(255, 255, 255, 0.05)' 
            }
          }}
        >
          ← Voltar
        </Button>
        
        { currentStep < 6 && (
          <Button 
            variant="contained" 
            size="large"
            onClick={ () => completeStep( currentStep ) }
            disabled={ !canCompleteCurrentStep() }
            sx={{
              background: 'linear-gradient(45deg, #FFD700 30%, #FFA000 90%)',
              color: '#000',
              fontWeight: 'bold',
              px: 3,
              py: 1.5,
              boxShadow: '0 3px 15px rgba(255, 215, 0, 0.4)',
              '&:hover': { 
                background: 'linear-gradient(45deg, #FFE55C 30%, #FFB300 90%)',
                transform: 'translateY(-2px)',
                boxShadow: '0 6px 20px rgba(255, 215, 0, 0.6)'
              },
              '&:disabled': { 
                background: '#666', 
                color: '#999',
                boxShadow: 'none'
              },
              transition: 'all 0.3s ease'
            }}
            startIcon={currentStep === 2 ? <span>🎨</span> : <span>➡️</span>}
          >
            {currentStep === 1 && 'Próximo: Configurar Áudio'}
            {currentStep === 2 && 'Próximo: Configurar Imagens'}
            {currentStep === 3 && 'Próximo: Efeitos Visuais'}
            {currentStep === 4 && 'Próximo: Música e Som'}
            {currentStep === 5 && 'Próximo: Pré-visualização'}
          </Button>
        ) }
        
        { currentStep === 6 && (
          <Button 
            variant="contained" 
            color="success"
            size="large"
            onClick={ handleGenerateCustom }
            disabled={ isGenerating }
            startIcon={ <PlayArrowIcon /> }
            sx={{
              background: 'linear-gradient(45deg, #4CAF50 30%, #2E7D32 90%)',
              color: '#fff',
              fontWeight: 'bold',
              px: 3,
              py: 1.5,
              boxShadow: '0 3px 15px rgba(76, 175, 80, 0.4)',
              '&:hover': { 
                background: 'linear-gradient(45deg, #66BB6A 30%, #388E3C 90%)',
                transform: 'translateY(-2px)',
                boxShadow: '0 6px 20px rgba(76, 175, 80, 0.6)'
              }
            }}
          >
            🚀 Gerar Vídeo Final
          </Button>
        ) }
      </Box>

      {/* Progresso de geração */ }
      { isGenerating && currentStep === 6 && (
        <Box sx={ { mt: 3 } }>
          <Box sx={ { display: 'flex', alignItems: 'center', gap: 2, mb: 1 } }>
            <CircularProgress size={ 20 } />
            <Typography>Gerando vídeo personalizado...</Typography>
          </Box>
          { generationProgress > 0 && (
            <Box sx={ { width: '100%' } }>
              <LinearProgress variant="determinate" value={ generationProgress } />
              <Typography variant="caption">{ generationProgress }% concluído</Typography>
            </Box>
          ) }
        </Box>
      ) }

    </Box>
  );
};

export default ProductionStudio
