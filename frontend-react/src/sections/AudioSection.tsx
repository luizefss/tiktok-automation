// /var/www/tiktok-automation/frontend-react/src/sections/AudioSection.tsx

import React, { useState } from 'react';
import { ContentSettings } from '../types';
import
    {
        Mic, Volume2, VolumeX, Sliders, Play,
        Music, User, Users, Globe, Zap
    } from 'lucide-react';
import { globalStyles as styles } from '../global-styles';
import { apiService } from '../services/api';

interface VoiceProfile
{
    id: string;
    name: string;
    gender: 'male' | 'female';
    style: string;
    description: string;
    icon: string;
}

interface AudioPreset
{
    id: string;
    name: string;
    icon: string;
    emotion: string;
    pitch: number;
    speed: number;
    volumeGain: number;
    description: string;
}

const AudioSection: React.FC<{ settings: ContentSettings, updateSetting: any }> = ( { settings, updateSetting } ) =>
{
    const [ isTestingVoice, setIsTestingVoice ] = useState( false );
    const [ selectedPreset, setSelectedPreset ] = useState<string>( 'neutral' );
    const [ advancedMode, setAdvancedMode ] = useState( false );

    // Perfis de voz disponíveis
    const voiceProfiles: VoiceProfile[] = [
        // Vozes Masculinas
        { id: 'male-professional', name: 'Profissional', gender: 'male', style: 'professional', description: 'Tom autoritativo e confiante', icon: '👔' },
        { id: 'male-youthful', name: 'Jovem', gender: 'male', style: 'youthful', description: 'Tom energético e moderno', icon: '🎮' },
        { id: 'male-mature', name: 'Maduro', gender: 'male', style: 'mature', description: 'Tom experiente e sábio', icon: '🎓' },
        { id: 'male-casual', name: 'Casual', gender: 'male', style: 'casual', description: 'Tom amigável e descontraído', icon: '😊' },
        { id: 'male-dramatic', name: 'Dramático', gender: 'male', style: 'dramatic', description: 'Tom intenso e emocional', icon: '🎭' },

        // Vozes Femininas
        { id: 'female-warm', name: 'Calorosa', gender: 'female', style: 'warm', description: 'Tom acolhedor e maternal', icon: '🤗' },
        { id: 'female-professional', name: 'Profissional', gender: 'female', style: 'professional', description: 'Tom executivo e direto', icon: '💼' },
        { id: 'female-energetic', name: 'Energética', gender: 'female', style: 'energetic', description: 'Tom vibrante e motivador', icon: '⚡' },
        { id: 'female-storyteller', name: 'Narradora', gender: 'female', style: 'storyteller', description: 'Tom envolvente para histórias', icon: '📚' },
        { id: 'female-youthful', name: 'Jovem', gender: 'female', style: 'youthful', description: 'Tom fresco e moderno', icon: '✨' }
    ];

    // Presets de emoção com configurações otimizadas
    const audioPresets: AudioPreset[] = [
        {
            id: 'neutral',
            name: 'Neutro',
            icon: '😐',
            emotion: 'neutral',
            pitch: 0,
            speed: 1.0,
            volumeGain: 0,
            description: 'Tom equilibrado e natural'
        },
        {
            id: 'dramatic',
            name: 'Dramático',
            icon: '🎭',
            emotion: 'dramatic',
            pitch: -3,
            speed: 0.85,
            volumeGain: 2,
            description: 'Intenso e impactante, com pausas dramáticas'
        },
        {
            id: 'mysterious',
            name: 'Misterioso',
            icon: '🕵️',
            emotion: 'mysterious',
            pitch: -5,
            speed: 0.80,
            volumeGain: -1,
            description: 'Sussurrante e enigmático'
        },
        {
            id: 'enthusiastic',
            name: 'Entusiasmado',
            icon: '🎉',
            emotion: 'enthusiastic',
            pitch: 2,
            speed: 1.15,
            volumeGain: 3,
            description: 'Animado e cheio de energia'
        },
        {
            id: 'calm',
            name: 'Calmo',
            icon: '😌',
            emotion: 'calm',
            pitch: -1,
            speed: 0.90,
            volumeGain: 0,
            description: 'Tranquilo e relaxante'
        },
        {
            id: 'suspenseful',
            name: 'Suspense',
            icon: '😰',
            emotion: 'suspenseful',
            pitch: -2,
            speed: 0.75,
            volumeGain: 1,
            description: 'Tenso com pausas longas'
        },
        {
            id: 'happy',
            name: 'Feliz',
            icon: '😄',
            emotion: 'happy',
            pitch: 3,
            speed: 1.1,
            volumeGain: 2,
            description: 'Alegre e otimista'
        },
        {
            id: 'sad',
            name: 'Triste',
            icon: '😢',
            emotion: 'sad',
            pitch: -4,
            speed: 0.85,
            volumeGain: -2,
            description: 'Melancólico e emotivo'
        },
        {
            id: 'angry',
            name: 'Raivoso',
            icon: '😠',
            emotion: 'angry',
            pitch: 1,
            speed: 1.2,
            volumeGain: 4,
            description: 'Intenso e agressivo'
        }
    ];

    // Sotaques disponíveis
    const accents = [
        { id: 'pt-BR', name: 'Português BR', flag: '🇧🇷' },
        { id: 'pt-PT', name: 'Português PT', flag: '🇵🇹' },
        { id: 'en-US', name: 'Inglês US', flag: '🇺🇸' },
        { id: 'es-ES', name: 'Espanhol', flag: '🇪🇸' }
    ];

    const handlePresetSelect = ( preset: AudioPreset ) =>
    {
        setSelectedPreset( preset.id );
        updateSetting( 'voice_emotion', preset.emotion );
        updateSetting( 'voice_pitch', preset.pitch );
        updateSetting( 'speaking_speed', preset.speed );
        updateSetting( 'voice_volume_gain', preset.volumeGain );
    };

    const testVoice = async () =>
    {
        setIsTestingVoice( true );
        try
        {
            const testText = "Esta é uma demonstração da voz selecionada com as configurações atuais.";
            const response = await apiService.post( 'production/generate-audio', {
                text: testText,
                voice_profile: settings.voice_profile,
                emotion: settings.voice_emotion,
                pitch: settings.voice_pitch || 0,
                speed: settings.speaking_speed,
                volume_gain: settings.voice_volume_gain || 0,
                accent: settings.voice_accent || 'pt-BR'
            } );

            if ( response.audio_url )
            {
                const audio = new Audio( response.audio_url );
                await audio.play();
            }
        } catch ( error )
        {
            console.error( 'Erro ao testar voz:', error );
        } finally
        {
            setIsTestingVoice( false );
        }
    };

    return (
        <div style={ styles.section }>
            {/* Header com toggle de modo avançado */ }
            <div style={ {
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '24px'
            } }>
                <h3 style={ styles.sectionTitle }>🎤 Configuração de Áudio</h3>
                <button
                    onClick={ () => setAdvancedMode( !advancedMode ) }
                    style={ {
                        ...styles.button,
                        padding: '8px 16px',
                        fontSize: '0.9rem',
                        background: advancedMode ? '#3b82f6' : '#475569'
                    } }
                >
                    <Sliders size={ 16 } style={ { marginRight: '6px' } } />
                    { advancedMode ? 'Modo Avançado' : 'Modo Simples' }
                </button>
            </div>

            {/* Seleção de Perfil de Voz */ }
            <div style={ { marginBottom: '24px' } }>
                <h4 style={ { ...styles.sectionTitle, fontSize: '1rem' } }>
                    👤 Perfil de Voz
                </h4>
                <div style={ {
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
                    gap: '8px'
                } }>
                    { voiceProfiles.map( profile => (
                        <button
                            key={ profile.id }
                            onClick={ () => updateSetting( 'voice_profile', profile.id ) }
                            style={ {
                                padding: '12px',
                                background: settings.voice_profile === profile.id
                                    ? 'linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)'
                                    : '#1e293b',
                                border: settings.voice_profile === profile.id
                                    ? '2px solid #60a5fa'
                                    : '1px solid #475569',
                                borderRadius: '8px',
                                cursor: 'pointer',
                                transition: 'all 0.2s ease',
                                textAlign: 'center'
                            } }
                            title={ profile.description }
                        >
                            <div style={ { fontSize: '1.5rem', marginBottom: '4px' } }>
                                { profile.icon }
                            </div>
                            <div style={ {
                                color: 'white',
                                fontSize: '0.85rem',
                                fontWeight: settings.voice_profile === profile.id ? 'bold' : 'normal'
                            } }>
                                { profile.name }
                            </div>
                            <div style={ {
                                color: profile.gender === 'male' ? '#60a5fa' : '#f472b6',
                                fontSize: '0.7rem',
                                marginTop: '2px'
                            } }>
                                { profile.gender === 'male' ? '♂️' : '♀️' }
                            </div>
                        </button>
                    ) ) }
                </div>
            </div>

            {/* Presets de Emoção */ }
            <div style={ { marginBottom: '24px' } }>
                <h4 style={ { ...styles.sectionTitle, fontSize: '1rem' } }>
                    🎭 Preset de Emoção
                </h4>
                <div style={ {
                    display: 'grid',
                    gridTemplateColumns: 'repeat(3, 1fr)',
                    gap: '8px'
                } }>
                    { audioPresets.map( preset => (
                        <button
                            key={ preset.id }
                            onClick={ () => handlePresetSelect( preset ) }
                            style={ {
                                padding: '16px',
                                background: selectedPreset === preset.id
                                    ? 'linear-gradient(135deg, #10b981 0%, #059669 100%)'
                                    : '#1e293b',
                                border: selectedPreset === preset.id
                                    ? '2px solid #34d399'
                                    : '1px solid #475569',
                                borderRadius: '8px',
                                cursor: 'pointer',
                                transition: 'all 0.2s ease'
                            } }
                            title={ preset.description }
                        >
                            <div style={ { fontSize: '2rem', marginBottom: '4px' } }>
                                { preset.icon }
                            </div>
                            <div style={ { color: 'white', fontSize: '0.85rem' } }>
                                { preset.name }
                            </div>
                        </button>
                    ) ) }
                </div>
            </div>

            {/* Controles Avançados */ }
            { advancedMode && (
                <div style={ {
                    padding: '20px',
                    background: '#0f172a',
                    borderRadius: '12px',
                    marginBottom: '24px'
                } }>
                    <h4 style={ { color: '#cbd5e1', marginBottom: '16px' } }>
                        ⚙️ Ajustes Finos
                    </h4>

                    {/* Tom (Pitch) */ }
                    <div style={ { marginBottom: '20px' } }>
                        <label style={ { color: '#9ca3af', fontSize: '0.9rem', marginBottom: '8px', display: 'block' } }>
                            🎵 Tom de Voz (Pitch): { settings.voice_pitch || 0 } st
                        </label>
                        <div style={ { display: 'flex', alignItems: 'center', gap: '12px' } }>
                            <span style={ { color: '#6b7280', fontSize: '0.8rem' } }>Grave</span>
                            <input
                                type="range"
                                min="-10"
                                max="10"
                                step="0.5"
                                value={ settings.voice_pitch || 0 }
                                onChange={ ( e ) => updateSetting( 'voice_pitch', parseFloat( e.target.value ) ) }
                                style={ { ...styles.slider, flex: 1 } }
                            />
                            <span style={ { color: '#6b7280', fontSize: '0.8rem' } }>Agudo</span>
                        </div>
                    </div>

                    {/* Velocidade */ }
                    <div style={ { marginBottom: '20px' } }>
                        <label style={ { color: '#9ca3af', fontSize: '0.9rem', marginBottom: '8px', display: 'block' } }>
                            ⚡ Velocidade: { settings.speaking_speed }x
                        </label>
                        <div style={ { display: 'flex', alignItems: 'center', gap: '12px' } }>
                            <span style={ { color: '#6b7280', fontSize: '0.8rem' } }>Lento</span>
                            <input
                                type="range"
                                min="0.5"
                                max="1.5"
                                step="0.05"
                                value={ settings.speaking_speed }
                                onChange={ ( e ) => updateSetting( 'speaking_speed', parseFloat( e.target.value ) ) }
                                style={ { ...styles.slider, flex: 1 } }
                            />
                            <span style={ { color: '#6b7280', fontSize: '0.8rem' } }>Rápido</span>
                        </div>
                    </div>

                    {/* Volume/Ganho */ }
                    <div style={ { marginBottom: '20px' } }>
                        <label style={ { color: '#9ca3af', fontSize: '0.9rem', marginBottom: '8px', display: 'block' } }>
                            🔊 Ganho de Volume: { settings.voice_volume_gain || 0 } dB
                        </label>
                        <div style={ { display: 'flex', alignItems: 'center', gap: '12px' } }>
                            <VolumeX size={ 16 } color="#6b7280" />
                            <input
                                type="range"
                                min="-10"
                                max="10"
                                step="0.5"
                                value={ settings.voice_volume_gain || 0 }
                                onChange={ ( e ) => updateSetting( 'voice_volume_gain', parseFloat( e.target.value ) ) }
                                style={ { ...styles.slider, flex: 1 } }
                            />
                            <Volume2 size={ 16 } color="#6b7280" />
                        </div>
                    </div>

                    {/* Pausas */ }
                    <div style={ { marginBottom: '20px' } }>
                        <label style={ { color: '#9ca3af', fontSize: '0.9rem', marginBottom: '8px', display: 'block' } }>
                            ⏸️ Duração das Pausas
                        </label>
                        <select
                            value={ settings.pause_duration || 'normal' }
                            onChange={ ( e ) => updateSetting( 'pause_duration', e.target.value ) }
                            style={ {
                                ...styles.select,
                                width: '100%',
                                background: '#1e293b'
                            } }
                        >
                            <option value="short">Curtas (dinâmico)</option>
                            <option value="normal">Normais (natural)</option>
                            <option value="long">Longas (dramático)</option>
                            <option value="very_long">Muito Longas (suspense)</option>
                        </select>
                    </div>

                    {/* Ênfase */ }
                    <div style={ { marginBottom: '20px' } }>
                        <label style={ { color: '#9ca3af', fontSize: '0.9rem', marginBottom: '8px', display: 'block' } }>
                            💪 Nível de Ênfase
                        </label>
                        <select
                            value={ settings.emphasis_level || 'moderate' }
                            onChange={ ( e ) => updateSetting( 'emphasis_level', e.target.value ) }
                            style={ {
                                ...styles.select,
                                width: '100%',
                                background: '#1e293b'
                            } }
                        >
                            <option value="reduced">Reduzida (suave)</option>
                            <option value="moderate">Moderada (natural)</option>
                            <option value="strong">Forte (impactante)</option>
                        </select>
                    </div>
                </div>
            ) }

            {/* Sotaque/Idioma */ }
            <div style={ { marginBottom: '24px' } }>
                <h4 style={ { ...styles.sectionTitle, fontSize: '1rem' } }>
                    🌍 Sotaque/Idioma
                </h4>
                <div style={ { display: 'flex', gap: '8px' } }>
                    { accents.map( accent => (
                        <button
                            key={ accent.id }
                            onClick={ () => updateSetting( 'voice_accent', accent.id ) }
                            style={ {
                                padding: '12px 20px',
                                background: settings.voice_accent === accent.id
                                    ? '#3b82f6'
                                    : '#1e293b',
                                border: settings.voice_accent === accent.id
                                    ? '2px solid #60a5fa'
                                    : '1px solid #475569',
                                borderRadius: '8px',
                                cursor: 'pointer',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '8px'
                            } }
                        >
                            <span style={ { fontSize: '1.2rem' } }>{ accent.flag }</span>
                            <span style={ { color: 'white', fontSize: '0.9rem' } }>
                                { accent.name }
                            </span>
                        </button>
                    ) ) }
                </div>
            </div>

            {/* Música de Fundo */ }
            <div style={ {
                padding: '20px',
                background: '#1e293b',
                borderRadius: '12px',
                marginBottom: '24px'
            } }>
                <div style={ { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' } }>
                    <h4 style={ { color: '#cbd5e1', margin: 0 } }>
                        <Music size={ 20 } style={ { display: 'inline', marginRight: '8px' } } />
                        Música de Fundo
                    </h4>
                    <label style={ { display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' } }>
                        <input
                            type="checkbox"
                            checked={ !!settings.background_music }
                            onChange={ ( e ) => updateSetting( 'background_music', e.target.checked ) }
                            style={ { width: '20px', height: '20px' } }
                        />
                        <span style={ { color: '#cbd5e1' } }>Ativar</span>
                    </label>
                </div>

                { settings.background_music && (
                    <>
                        <div style={ { marginBottom: '16px' } }>
                            <label style={ { color: '#9ca3af', fontSize: '0.9rem', marginBottom: '8px', display: 'block' } }>
                                Volume da Música: { Math.round( ( settings.background_music_volume || 0.15 ) * 100 ) }%
                            </label>
                            <div style={ { display: 'flex', alignItems: 'center', gap: '12px' } }>
                                <VolumeX size={ 16 } color="#6b7280" />
                                <input
                                    type="range"
                                    min="0"
                                    max="0.5"
                                    step="0.01"
                                    value={ settings.background_music_volume || 0.15 }
                                    onChange={ ( e ) => updateSetting( 'background_music_volume', parseFloat( e.target.value ) ) }
                                    style={ { ...styles.slider, flex: 1 } }
                                />
                                <Volume2 size={ 16 } color="#6b7280" />
                            </div>
                        </div>

                        <div>
                            <label style={ { color: '#9ca3af', fontSize: '0.9rem', marginBottom: '8px', display: 'block' } }>
                                Categoria da Música
                            </label>
                            <select
                                value={ settings.music_category || 'epic' }
                                onChange={ ( e ) => updateSetting( 'music_category', e.target.value ) }
                                style={ {
                                    ...styles.select,
                                    width: '100%',
                                    background: '#0f172a'
                                } }
                            >
                                <option value="epic">🎼 Épica</option>
                                <option value="suspense">🕵️ Suspense</option>
                                <option value="emotional">💔 Emocional</option>
                                <option value="upbeat">🎉 Animada</option>
                                <option value="ambient">🌌 Ambiente</option>
                            </select>
                        </div>
                    </>
                ) }
            </div>

            {/* Features Avançadas */ }
            <div style={ { marginBottom: '24px' } }>
                <h4 style={ { ...styles.sectionTitle, fontSize: '1rem' } }>
                    ✨ Features Avançadas
                </h4>
                <div style={ { display: 'flex', flexDirection: 'column', gap: '12px' } }>
                    <label style={ { display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', color: '#cbd5e1' } }>
                        <input
                            type="checkbox"
                            checked={ settings.auto_emotion_detection || false }
                            onChange={ ( e ) => updateSetting( 'auto_emotion_detection', e.target.checked ) }
                            style={ { width: '18px', height: '18px' } }
                        />
                        <span>🎭 Detecção Automática de Emoção (IA analisa texto)</span>
                    </label>

                    <label style={ { display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', color: '#cbd5e1' } }>
                        <input
                            type="checkbox"
                            checked={ settings.voice_cloning || false }
                            onChange={ ( e ) => updateSetting( 'voice_cloning', e.target.checked ) }
                            style={ { width: '18px', height: '18px' } }
                        />
                        <User size={ 16 } style={ { marginRight: '4px' } } />
                        <span>Voice Cloning (usar voz personalizada)</span>
                    </label>

                    <label style={ { display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', color: '#cbd5e1' } }>
                        <input
                            type="checkbox"
                            checked={ settings.multi_speaker || false }
                            onChange={ ( e ) => updateSetting( 'multi_speaker', e.target.checked ) }
                            style={ { width: '18px', height: '18px' } }
                        />
                        <Users size={ 16 } style={ { marginRight: '4px' } } />
                        <span>Multi-Speaker (diálogos com vozes diferentes)</span>
                    </label>

                    <label style={ { display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', color: '#cbd5e1' } }>
                        <input
                            type="checkbox"
                            checked={ settings.ai_voice_enhancement || false }
                            onChange={ ( e ) => updateSetting( 'ai_voice_enhancement', e.target.checked ) }
                            style={ { width: '18px', height: '18px' } }
                        />
                        <Zap size={ 16 } style={ { marginRight: '4px' } } />
                        <span>Aprimoramento IA (melhora qualidade da voz)</span>
                    </label>

                    <label style={ { display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', color: '#cbd5e1' } }>
                        <input
                            type="checkbox"
                            checked={ settings.global_voice_sync || false }
                            onChange={ ( e ) => updateSetting( 'global_voice_sync', e.target.checked ) }
                            style={ { width: '18px', height: '18px' } }
                        />
                        <Globe size={ 16 } style={ { marginRight: '4px' } } />
                        <span>Sincronização Global (voz consistente multi-idiomas)</span>
                    </label>
                </div>
            </div>

            {/* Configurações de Dublagem */ }
            <div style={ {
                padding: '20px',
                background: '#1e293b',
                borderRadius: '12px',
                marginBottom: '24px'
            } }>
                <h4 style={ { color: '#cbd5e1', marginBottom: '16px' } }>
                    <Mic size={ 20 } style={ { display: 'inline', marginRight: '8px' } } />
                    Configurações de Dublagem
                </h4>

                {/* Equalizador de Voz */ }
                <div style={ { marginBottom: '16px' } }>
                    <label style={ { color: '#9ca3af', fontSize: '0.9rem', marginBottom: '8px', display: 'block' } }>
                        🎚️ Equalizador de Voz
                    </label>
                    <div style={ { display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '8px' } }>
                        <div style={ { textAlign: 'center' } }>
                            <label style={ { color: '#6b7280', fontSize: '0.7rem', display: 'block', marginBottom: '4px' } }>
                                Graves
                            </label>
                            <input
                                type="range"
                                min="-5"
                                max="5"
                                step="0.5"
                                value={ settings.voice_eq_bass || 0 }
                                onChange={ ( e ) => updateSetting( 'voice_eq_bass', parseFloat( e.target.value ) ) }
                                style={ { ...styles.slider, width: '100%' } }
                            />
                            <span style={ { color: '#6b7280', fontSize: '0.7rem' } }>
                                { settings.voice_eq_bass || 0 }
                            </span>
                        </div>
                        <div style={ { textAlign: 'center' } }>
                            <label style={ { color: '#6b7280', fontSize: '0.7rem', display: 'block', marginBottom: '4px' } }>
                                Médios
                            </label>
                            <input
                                type="range"
                                min="-5"
                                max="5"
                                step="0.5"
                                value={ settings.voice_eq_mid || 0 }
                                onChange={ ( e ) => updateSetting( 'voice_eq_mid', parseFloat( e.target.value ) ) }
                                style={ { ...styles.slider, width: '100%' } }
                            />
                            <span style={ { color: '#6b7280', fontSize: '0.7rem' } }>
                                { settings.voice_eq_mid || 0 }
                            </span>
                        </div>
                        <div style={ { textAlign: 'center' } }>
                            <label style={ { color: '#6b7280', fontSize: '0.7rem', display: 'block', marginBottom: '4px' } }>
                                Agudos
                            </label>
                            <input
                                type="range"
                                min="-5"
                                max="5"
                                step="0.5"
                                value={ settings.voice_eq_treble || 0 }
                                onChange={ ( e ) => updateSetting( 'voice_eq_treble', parseFloat( e.target.value ) ) }
                                style={ { ...styles.slider, width: '100%' } }
                            />
                            <span style={ { color: '#6b7280', fontSize: '0.7rem' } }>
                                { settings.voice_eq_treble || 0 }
                            </span>
                        </div>
                        <div style={ { textAlign: 'center' } }>
                            <label style={ { color: '#6b7280', fontSize: '0.7rem', display: 'block', marginBottom: '4px' } }>
                                Presença
                            </label>
                            <input
                                type="range"
                                min="-5"
                                max="5"
                                step="0.5"
                                value={ settings.voice_eq_presence || 0 }
                                onChange={ ( e ) => updateSetting( 'voice_eq_presence', parseFloat( e.target.value ) ) }
                                style={ { ...styles.slider, width: '100%' } }
                            />
                            <span style={ { color: '#6b7280', fontSize: '0.7rem' } }>
                                { settings.voice_eq_presence || 0 }
                            </span>
                        </div>
                    </div>
                </div>

                {/* Reverb e Efeitos */ }
                <div style={ { marginBottom: '16px' } }>
                    <label style={ { color: '#9ca3af', fontSize: '0.9rem', marginBottom: '8px', display: 'block' } }>
                        🎭 Ambiente Acústico
                    </label>
                    <select
                        value={ settings.voice_reverb || 'none' }
                        onChange={ ( e ) => updateSetting( 'voice_reverb', e.target.value ) }
                        style={ {
                            ...styles.select,
                            width: '100%',
                            background: '#0f172a'
                        } }
                    >
                        <option value="none">🏠 Sem Reverb (Estúdio)</option>
                        <option value="room">🏢 Sala</option>
                        <option value="hall">🏛️ Salão</option>
                        <option value="cathedral">⛪ Catedral</option>
                        <option value="cave">🕳️ Caverna</option>
                        <option value="underwater">🌊 Subaquático</option>
                    </select>
                </div>

                {/* Compressão de Áudio */ }
                <div style={ { marginBottom: '16px' } }>
                    <label style={ { color: '#9ca3af', fontSize: '0.9rem', marginBottom: '8px', display: 'block' } }>
                        🎚️ Compressão: { Math.round( ( settings.voice_compression || 0.3 ) * 100 ) }%
                    </label>
                    <div style={ { display: 'flex', alignItems: 'center', gap: '12px' } }>
                        <span style={ { color: '#6b7280', fontSize: '0.8rem' } }>Natural</span>
                        <input
                            type="range"
                            min="0"
                            max="1"
                            step="0.1"
                            value={ settings.voice_compression || 0.3 }
                            onChange={ ( e ) => updateSetting( 'voice_compression', parseFloat( e.target.value ) ) }
                            style={ { ...styles.slider, flex: 1 } }
                        />
                        <span style={ { color: '#6b7280', fontSize: '0.8rem' } }>Rádio</span>
                    </div>
                </div>
            </div>

            {/* Configurações Multi-Plataforma */ }
            <div style={ {
                padding: '20px',
                background: '#1e293b',
                borderRadius: '12px',
                marginBottom: '24px'
            } }>
                <div style={ { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' } }>
                    <h4 style={ { color: '#cbd5e1', margin: 0 } }>
                        <Globe size={ 20 } style={ { display: 'inline', marginRight: '8px' } } />
                        Otimização Multi-Plataforma
                    </h4>
                </div>

                {/* Plataformas Alvo */ }
                <div style={ { marginBottom: '16px' } }>
                    <label style={ { color: '#9ca3af', fontSize: '0.9rem', marginBottom: '8px', display: 'block' } }>
                        📱 Plataformas de Destino
                    </label>
                    <div style={ { display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px' } }>
                        { [
                            { id: 'tiktok', name: 'TikTok', icon: '📱' },
                            { id: 'youtube_shorts', name: 'YouTube Shorts', icon: '🎬' },
                            { id: 'instagram_reels', name: 'Instagram Reels', icon: '📸' },
                            { id: 'facebook_reels', name: 'Facebook Reels', icon: '📘' },
                            { id: 'twitter_videos', name: 'Twitter Videos', icon: '🐦' },
                            { id: 'snapchat_spotlight', name: 'Snapchat Spotlight', icon: '👻' }
                        ].map( platform => (
                            <label key={ platform.id } style={ { display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', color: '#cbd5e1' } }>
                                <input
                                    type="checkbox"
                                    checked={ ( settings.target_platforms || [] ).includes( platform.id ) }
                                    onChange={ ( e ) =>
                                    {
                                        const currentPlatforms = settings.target_platforms || [];
                                        if ( e.target.checked )
                                        {
                                            updateSetting( 'target_platforms', [ ...currentPlatforms, platform.id ] );
                                        } else
                                        {
                                            updateSetting( 'target_platforms', currentPlatforms.filter( p => p !== platform.id ) );
                                        }
                                    } }
                                    style={ { width: '16px', height: '16px' } }
                                />
                                <span style={ { fontSize: '0.8rem' } }>{ platform.icon } { platform.name }</span>
                            </label>
                        ) ) }
                    </div>
                </div>

                {/* Idiomas Alvo */ }
                <div style={ { marginBottom: '16px' } }>
                    <label style={ { color: '#9ca3af', fontSize: '0.9rem', marginBottom: '8px', display: 'block' } }>
                        🌍 Idiomas de Destino
                    </label>
                    <div style={ { display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '8px' } }>
                        { [
                            { id: 'pt-BR', name: 'Português BR', flag: '🇧🇷' },
                            { id: 'en-US', name: 'Inglês US', flag: '🇺🇸' },
                            { id: 'es-ES', name: 'Espanhol', flag: '🇪🇸' },
                            { id: 'fr-FR', name: 'Francês', flag: '🇫🇷' },
                            { id: 'de-DE', name: 'Alemão', flag: '🇩🇪' },
                            { id: 'it-IT', name: 'Italiano', flag: '🇮🇹' },
                            { id: 'ja-JP', name: 'Japonês', flag: '🇯🇵' },
                            { id: 'ko-KR', name: 'Coreano', flag: '🇰🇷' }
                        ].map( language => (
                            <label key={ language.id } style={ { display: 'flex', alignItems: 'center', gap: '4px', cursor: 'pointer', color: '#cbd5e1' } }>
                                <input
                                    type="checkbox"
                                    checked={ ( settings.target_languages || [] ).includes( language.id ) }
                                    onChange={ ( e ) =>
                                    {
                                        const currentLanguages = settings.target_languages || [];
                                        if ( e.target.checked )
                                        {
                                            updateSetting( 'target_languages', [ ...currentLanguages, language.id ] );
                                        } else
                                        {
                                            updateSetting( 'target_languages', currentLanguages.filter( l => l !== language.id ) );
                                        }
                                    } }
                                    style={ { width: '14px', height: '14px' } }
                                />
                                <span style={ { fontSize: '0.7rem' } }>{ language.flag }</span>
                            </label>
                        ) ) }
                    </div>
                </div>

                {/* Otimização Automática */ }
                <label style={ { display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', color: '#cbd5e1' } }>
                    <input
                        type="checkbox"
                        checked={ settings.auto_platform_optimization || false }
                        onChange={ ( e ) => updateSetting( 'auto_platform_optimization', e.target.checked ) }
                        style={ { width: '18px', height: '18px' } }
                    />
                    <Zap size={ 16 } style={ { marginRight: '4px' } } />
                    <span>Otimização Automática de Áudio por Plataforma</span>
                </label>
            </div>

            {/* Configurações de Estúdio Virtual */ }
            <div style={ {
                padding: '20px',
                background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
                borderRadius: '12px',
                marginBottom: '24px',
                border: '1px solid #3b82f6'
            } }>
                <div style={ { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' } }>
                    <h4 style={ { color: '#60a5fa', margin: 0, fontSize: '1.1rem' } }>
                        <Mic size={ 22 } style={ { display: 'inline', marginRight: '8px' } } />
                        Estúdio Virtual Pro
                    </h4>
                    <div style={ {
                        background: '#3b82f6',
                        color: 'white',
                        padding: '4px 8px',
                        borderRadius: '12px',
                        fontSize: '0.7rem',
                        fontWeight: 'bold'
                    } }>
                        PRO
                    </div>
                </div>

                {/* Monitoramento em Tempo Real */ }
                <div style={ { marginBottom: '16px' } }>
                    <label style={ { display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', color: '#cbd5e1', marginBottom: '8px' } }>
                        <input
                            type="checkbox"
                            checked={ settings.real_time_monitoring || false }
                            onChange={ ( e ) => updateSetting( 'real_time_monitoring', e.target.checked ) }
                            style={ { width: '18px', height: '18px' } }
                        />
                        <Volume2 size={ 16 } style={ { marginRight: '4px' } } />
                        <span>Monitoramento em Tempo Real</span>
                    </label>
                </div>

                {/* Configurações de Microfone Virtual */ }
                <div style={ { marginBottom: '16px' } }>
                    <label style={ { color: '#9ca3af', fontSize: '0.9rem', marginBottom: '8px', display: 'block' } }>
                        🎙️ Tipo de Microfone Virtual
                    </label>
                    <select
                        value={ settings.virtual_microphone || 'studio_condenser' }
                        onChange={ ( e ) => updateSetting( 'virtual_microphone', e.target.value ) }
                        style={ {
                            ...styles.select,
                            width: '100%',
                            background: '#0f172a'
                        } }
                    >
                        <option value="studio_condenser">🎙️ Condensador de Estúdio</option>
                        <option value="dynamic_vocal">🎤 Dinâmico Vocal</option>
                        <option value="ribbon_vintage">📻 Ribbon Vintage</option>
                        <option value="podcast_broadcast">📡 Broadcast Podcast</option>
                        <option value="gaming_headset">🎮 Gaming Headset</option>
                        <option value="phone_quality">📱 Qualidade Telefone</option>
                    </select>
                </div>

                {/* Filtros de Ruído */ }
                <div style={ { marginBottom: '16px' } }>
                    <label style={ { color: '#9ca3af', fontSize: '0.9rem', marginBottom: '8px', display: 'block' } }>
                        🔇 Supressão de Ruído: { Math.round( ( settings.noise_suppression || 0.7 ) * 100 ) }%
                    </label>
                    <div style={ { display: 'flex', alignItems: 'center', gap: '12px' } }>
                        <span style={ { color: '#6b7280', fontSize: '0.8rem' } }>Desligado</span>
                        <input
                            type="range"
                            min="0"
                            max="1"
                            step="0.1"
                            value={ settings.noise_suppression || 0.7 }
                            onChange={ ( e ) => updateSetting( 'noise_suppression', parseFloat( e.target.value ) ) }
                            style={ { ...styles.slider, flex: 1 } }
                        />
                        <span style={ { color: '#6b7280', fontSize: '0.8rem' } }>Máximo</span>
                    </div>
                </div>

                {/* Gate de Ruído */ }
                <div style={ { marginBottom: '16px' } }>
                    <label style={ { color: '#9ca3af', fontSize: '0.9rem', marginBottom: '8px', display: 'block' } }>
                        🚪 Noise Gate: { settings.noise_gate || -30 } dB
                    </label>
                    <input
                        type="range"
                        min="-60"
                        max="-10"
                        step="1"
                        value={ settings.noise_gate || -30 }
                        onChange={ ( e ) => updateSetting( 'noise_gate', parseInt( e.target.value ) ) }
                        style={ { ...styles.slider, width: '100%' } }
                    />
                </div>

                {/* Presets de Estúdio */ }
                <div style={ { marginBottom: '16px' } }>
                    <label style={ { color: '#9ca3af', fontSize: '0.9rem', marginBottom: '8px', display: 'block' } }>
                        🎚️ Preset de Estúdio
                    </label>
                    <div style={ { display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '8px' } }>
                        { [
                            { id: 'podcast', name: '🎙️ Podcast', description: 'Voz clara e presente' },
                            { id: 'audiobook', name: '📚 Audiobook', description: 'Narrativa suave' },
                            { id: 'commercial', name: '📺 Comercial', description: 'Impacto e energia' },
                            { id: 'documentary', name: '🎬 Documentário', description: 'Autoridade e credibilidade' }
                        ].map( preset => (
                            <button
                                key={ preset.id }
                                onClick={ () => updateSetting( 'studio_preset', preset.id ) }
                                style={ {
                                    padding: '12px',
                                    background: settings.studio_preset === preset.id
                                        ? 'linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)'
                                        : '#1e293b',
                                    border: settings.studio_preset === preset.id
                                        ? '2px solid #60a5fa'
                                        : '1px solid #475569',
                                    borderRadius: '8px',
                                    cursor: 'pointer',
                                    textAlign: 'left'
                                } }
                                title={ preset.description }
                            >
                                <div style={ { color: 'white', fontSize: '0.85rem', fontWeight: 'bold' } }>
                                    { preset.name }
                                </div>
                                <div style={ { color: '#9ca3af', fontSize: '0.7rem', marginTop: '2px' } }>
                                    { preset.description }
                                </div>
                            </button>
                        ) ) }
                    </div>
                </div>
            </div>

            {/* Botão de Teste */ }
            <button
                onClick={ testVoice }
                disabled={ isTestingVoice }
                style={ {
                    ...styles.button,
                    width: '100%',
                    padding: '14px',
                    background: isTestingVoice
                        ? '#6b7280'
                        : 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)',
                    fontSize: '1rem',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '8px',
                    cursor: isTestingVoice ? 'not-allowed' : 'pointer'
                } }
            >
                <Play size={ 20 } />
                { isTestingVoice ? 'Testando...' : 'Testar Configurações de Voz' }
            </button>

            {/* Player de Áudio Preview */ }
            { settings.preview_audio_file && (
                <div style={ {
                    marginTop: '16px',
                    padding: '16px',
                    background: 'linear-gradient(135deg, #059669 0%, #047857 100%)',
                    borderRadius: '12px',
                    border: '2px solid #10b981'
                } }>
                    <div style={ { 
                        display: 'flex', 
                        alignItems: 'center', 
                        gap: '12px',
                        marginBottom: '8px'
                    } }>
                        <Volume2 size={ 20 } color="white" />
                        <span style={ { color: 'white', fontWeight: 'bold' } }>
                            🎵 Preview de Áudio Gerado
                        </span>
                    </div>
                    <audio 
                        controls 
                        style={ { 
                            width: '100%',
                            height: '40px',
                            borderRadius: '8px'
                        } }
                        src={ settings.preview_audio_file }
                        preload="metadata"
                    >
                        Seu navegador não suporta o elemento de áudio.
                    </audio>
                </div>
            ) }

            {/* Player de Áudio Completo */ }
            { settings.audio_file && (
                <div style={ {
                    marginTop: '16px',
                    padding: '16px',
                    background: 'linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)',
                    borderRadius: '12px',
                    border: '2px solid #60a5fa'
                } }>
                    <div style={ { 
                        display: 'flex', 
                        alignItems: 'center', 
                        gap: '12px',
                        marginBottom: '8px'
                    } }>
                        <Music size={ 20 } color="white" />
                        <span style={ { color: 'white', fontWeight: 'bold' } }>
                            🎤 Áudio Final Gerado
                        </span>
                        { settings.audio_duration && (
                            <span style={ { 
                                color: '#bfdbfe', 
                                fontSize: '0.9rem',
                                background: 'rgba(255,255,255,0.1)',
                                padding: '4px 8px',
                                borderRadius: '6px'
                            } }>
                                { Math.round( settings.audio_duration ) }s
                            </span>
                        ) }
                    </div>
                    <audio 
                        controls 
                        style={ { 
                            width: '100%',
                            height: '40px',
                            borderRadius: '8px'
                        } }
                        src={ settings.audio_file }
                        preload="metadata"
                    >
                        Seu navegador não suporta o elemento de áudio.
                    </audio>
                </div>
            ) }

            {/* Campo de Prompt Customizado */ }
            <div style={ { marginTop: '24px' } }>
                <h4 style={ { ...styles.sectionTitle, fontSize: '1rem' } }>
                    📝 Instruções Especiais (Opcional)
                </h4>
                <textarea
                    value={ settings.custom_prompt_audio || '' }
                    onChange={ ( e ) => updateSetting( 'custom_prompt_audio', e.target.value ) }
                    style={ {
                        ...styles.textarea,
                        minHeight: '80px'
                    } }
                    placeholder="Ex: Adicionar risada no início, fazer pausa longa antes da revelação, sussurrar a última frase..."
                />
            </div>
        </div>
    );
};

export default AudioSection;