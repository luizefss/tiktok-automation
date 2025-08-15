// /var/www/tiktok-automation/frontend-react/src/sections/ContentSection.tsx

import React, { useState } from 'react';
import { ContentSettings } from '../types';
import { globalStyles as styles } from '../global-styles';
import { apiService } from '../services/api';
import { Brain, Sword, Trophy, Clock, Zap, FileText, RefreshCw } from 'lucide-react';

interface BattleResult
{
    iaName: string;
    scriptData: {
        titulo: string;
        hook: string;
        desenvolvimento: string;
        cta: string;
        hashtags: string[];
        duracao_estimada: number;
    } | null;
    error?: string;
    generationTime?: number;
}

const ContentSection: React.FC<{ settings: ContentSettings, updateSetting: any }> = ( { settings, updateSetting } ) =>
{
    const [ isBattleMode, setIsBattleMode ] = useState( false );
    const [ battleInProgress, setBattleInProgress ] = useState( false );
    const [ battleResults, setBattleResults ] = useState<BattleResult[]>( [] );
    const [ selectedWinner, setSelectedWinner ] = useState<string>( '' );
    const [ customTopic, setCustomTopic ] = useState( '' );

    // Configuração das IAs para batalha
    const battleParticipants = [
        { id: 'claude-opus-4', name: 'Claude Opus 4', color: '#7c3aed', icon: '🎭' },
        { id: 'gemini-2.0-flash', name: 'Gemini 2.0 Flash', color: '#4285f4', icon: '🚀' },
        { id: 'gpt-4-turbo', name: 'GPT-4 Turbo', color: '#00a67e', icon: '🧠' }
    ];

    const startBattle = async () =>
    {
        if ( !customTopic.trim() )
        {
            alert( 'Digite um tema para a batalha!' );
            return;
        }

        setBattleInProgress( true );
        setBattleResults( [] );
        setSelectedWinner( '' );

        try
        {
            const battleSettings = {
                ...settings,
                custom_topics: [ customTopic ],
                participants: battleParticipants.map( p => p.id ),
                battle_mode: true,
                measure_time: true
            };

            const response = await apiService.post( 'production/ai-battle', {
                settings: battleSettings
            } );

            if ( response.success )
            {
                setBattleResults( response.results );
            } else
            {
                alert( 'Erro na batalha: ' + response.error );
            }
        } catch ( error )
        {
            console.error( 'Erro ao iniciar batalha:', error );
            alert( 'Erro ao conectar com o servidor' );
        } finally
        {
            setBattleInProgress( false );
        }
    };

    const saveWinner = async () =>
    {
        if ( !selectedWinner )
        {
            alert( 'Selecione um vencedor primeiro!' );
            return;
        }

        const winner = battleResults.find( r => r.iaName === selectedWinner );
        if ( !winner || !winner.scriptData ) return;

        // Salva o roteiro vencedor nas configurações
        updateSetting( 'script', winner.scriptData.desenvolvimento );
        updateSetting( 'content_ai_model', selectedWinner );

        // Registra a vitória no histórico
        try
        {
            // Endpoint save-result não implementado ainda no backend
            // await apiService.post( '/api/ai-battle/save-result', {
            //     winner: selectedWinner,
            //     topic: customTopic,
            //     results: battleResults,
            //     timestamp: new Date().toISOString()
            // } );

            alert( `✅ ${ selectedWinner } venceu! Roteiro selecionado.` );
            setIsBattleMode( false );
            setBattleResults( [] );
        } catch ( error )
        {
            console.error( 'Erro ao salvar resultado:', error );
        }
    };

    return (
        <div style={ styles.section }>
            {/* Toggle Modo Batalha */ }
            <div style={ {
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '24px',
                padding: '16px',
                background: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
                borderRadius: '12px'
            } }>
                <div>
                    <h3 style={ { ...styles.sectionTitle, margin: 0, color: 'white' } }>
                        🎬 Geração de Roteiro
                    </h3>
                    <p style={ { color: '#9ca3af', fontSize: '0.85rem', margin: '4px 0 0 0' } }>
                        Escolha entre modo direto ou batalha de IAs
                    </p>
                </div>
                <button
                    onClick={ () => setIsBattleMode( !isBattleMode ) }
                    style={ {
                        ...styles.button,
                        background: isBattleMode
                            ? 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)'
                            : 'linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)',
                        padding: '10px 20px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px'
                    } }
                >
                    { isBattleMode ? <Sword size={ 18 } /> : <Brain size={ 18 } /> }
                    { isBattleMode ? 'Modo Batalha ON' : 'Ativar Batalha' }
                </button>
            </div>

            { isBattleMode ? (
                // MODO BATALHA
                <div>
                    {/* Input do Tema */ }
                    <div style={ { marginBottom: '24px' } }>
                        <h4 style={ { ...styles.sectionTitle, fontSize: '1rem' } }>
                            💭 Tema da Batalha
                        </h4>
                        <input
                            type="text"
                            value={ customTopic }
                            onChange={ ( e ) => setCustomTopic( e.target.value ) }
                            placeholder="Ex: O poder da disciplina na era digital"
                            style={ {
                                ...styles.input,
                                width: '100%',
                                padding: '12px',
                                fontSize: '1rem'
                            } }
                            disabled={ battleInProgress }
                        />
                    </div>

                    {/* Participantes */ }
                    <div style={ { marginBottom: '24px' } }>
                        <h4 style={ { ...styles.sectionTitle, fontSize: '1rem' } }>
                            ⚔️ Participantes da Batalha
                        </h4>
                        <div style={ { display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px' } }>
                            { battleParticipants.map( ia => (
                                <div
                                    key={ ia.id }
                                    style={ {
                                        padding: '16px',
                                        background: `linear-gradient(135deg, ${ ia.color }20 0%, ${ ia.color }10 100%)`,
                                        border: `2px solid ${ ia.color }`,
                                        borderRadius: '8px',
                                        textAlign: 'center'
                                    } }
                                >
                                    <div style={ { fontSize: '2rem', marginBottom: '8px' } }>{ ia.icon }</div>
                                    <div style={ { color: 'white', fontWeight: 'bold' } }>{ ia.name }</div>
                                </div>
                            ) ) }
                        </div>
                    </div>

                    {/* Botão Iniciar Batalha */ }
                    { !battleResults.length && (
                        <button
                            onClick={ startBattle }
                            disabled={ battleInProgress || !customTopic.trim() }
                            style={ {
                                ...styles.button,
                                width: '100%',
                                padding: '16px',
                                background: battleInProgress
                                    ? '#6b7280'
                                    : 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
                                fontSize: '1.1rem',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                gap: '12px',
                                cursor: battleInProgress ? 'not-allowed' : 'pointer'
                            } }
                        >
                            { battleInProgress ? (
                                <>
                                    <RefreshCw size={ 20 } className="animate-spin" />
                                    Batalha em Progresso...
                                </>
                            ) : (
                                <>
                                    <Zap size={ 20 } />
                                    INICIAR BATALHA ÉPICA
                                </>
                            ) }
                        </button>
                    ) }

                    {/* Resultados da Batalha */ }
                    { battleResults.length > 0 && (
                        <div style={ { marginTop: '24px' } }>
                            <h4 style={ { ...styles.sectionTitle, fontSize: '1.1rem', marginBottom: '16px' } }>
                                📊 Resultados da Batalha
                            </h4>

                            <div style={ { display: 'grid', gap: '16px' } }>
                                { battleResults.map( ( result ) =>
                                {
                                    const ia = battleParticipants.find( p => p.id === result.iaName );
                                    const isSelected = selectedWinner === result.iaName;

                                    return (
                                        <div
                                            key={ result.iaName }
                                            onClick={ () => result.scriptData && setSelectedWinner( result.iaName ) }
                                            style={ {
                                                padding: '20px',
                                                background: isSelected
                                                    ? 'linear-gradient(135deg, #065f46 0%, #047857 100%)'
                                                    : '#1e293b',
                                                border: isSelected ? '2px solid #10b981' : '1px solid #475569',
                                                borderRadius: '12px',
                                                cursor: result.scriptData ? 'pointer' : 'not-allowed',
                                                opacity: result.error ? 0.6 : 1,
                                                transition: 'all 0.3s ease'
                                            } }
                                        >
                                            <div style={ {
                                                display: 'flex',
                                                justifyContent: 'space-between',
                                                alignItems: 'center',
                                                marginBottom: '16px'
                                            } }>
                                                <div style={ { display: 'flex', alignItems: 'center', gap: '12px' } }>
                                                    <span style={ { fontSize: '1.5rem' } }>{ ia?.icon }</span>
                                                    <div>
                                                        <h5 style={ { color: 'white', margin: 0, fontSize: '1.1rem' } }>
                                                            { ia?.name }
                                                        </h5>
                                                        { result.generationTime && (
                                                            <span style={ { color: '#9ca3af', fontSize: '0.8rem' } }>
                                                                <Clock size={ 12 } style={ { display: 'inline', marginRight: '4px' } } />
                                                                { result.generationTime.toFixed( 2 ) }s
                                                            </span>
                                                        ) }
                                                    </div>
                                                </div>
                                                { isSelected && (
                                                    <Trophy size={ 24 } color="#fbbf24" />
                                                ) }
                                            </div>

                                            { result.scriptData ? (
                                                <div>
                                                    <div style={ { marginBottom: '12px' } }>
                                                        <strong style={ { color: '#f59e0b' } }>🎯 Hook:</strong>
                                                        <p style={ {
                                                            color: '#cbd5e1',
                                                            margin: '8px 0',
                                                            fontStyle: 'italic',
                                                            fontSize: '0.95rem'
                                                        } }>
                                                            "{ result.scriptData.hook }"
                                                        </p>
                                                    </div>

                                                    <div style={ { marginBottom: '12px' } }>
                                                        <strong style={ { color: '#3b82f6' } }>📝 Título:</strong>
                                                        <p style={ { color: '#cbd5e1', margin: '8px 0' } }>
                                                            { result.scriptData.titulo }
                                                        </p>
                                                    </div>

                                                    <div style={ {
                                                        background: 'rgba(0,0,0,0.3)',
                                                        padding: '12px',
                                                        borderRadius: '8px',
                                                        maxHeight: '150px',
                                                        overflowY: 'auto'
                                                    } }>
                                                        <strong style={ { color: '#10b981' } }>Desenvolvimento:</strong>
                                                        <p style={ {
                                                            color: '#cbd5e1',
                                                            margin: '8px 0',
                                                            fontSize: '0.9rem',
                                                            lineHeight: '1.5'
                                                        } }>
                                                            { result.scriptData.desenvolvimento }
                                                        </p>
                                                    </div>

                                                    <div style={ { marginTop: '12px' } }>
                                                        <strong style={ { color: '#a78bfa' } }>🎬 CTA:</strong>
                                                        <p style={ { color: '#cbd5e1', margin: '8px 0' } }>
                                                            { result.scriptData.cta }
                                                        </p>
                                                    </div>

                                                    <div style={ {
                                                        marginTop: '12px',
                                                        display: 'flex',
                                                        gap: '8px',
                                                        flexWrap: 'wrap'
                                                    } }>
                                                        { result.scriptData.hashtags.map( tag => (
                                                            <span
                                                                key={ tag }
                                                                style={ {
                                                                    background: '#334155',
                                                                    padding: '4px 8px',
                                                                    borderRadius: '12px',
                                                                    fontSize: '0.8rem',
                                                                    color: '#60a5fa'
                                                                } }
                                                            >
                                                                { tag }
                                                            </span>
                                                        ) ) }
                                                    </div>
                                                </div>
                                            ) : (
                                                <div style={ { color: '#ef4444', textAlign: 'center', padding: '20px' } }>
                                                    <p>❌ Falha na geração</p>
                                                    <p style={ { fontSize: '0.85rem', marginTop: '8px' } }>
                                                        { result.error || 'Erro desconhecido' }
                                                    </p>
                                                </div>
                                            ) }
                                        </div>
                                    );
                                } ) }
                            </div>

                            {/* Botão Salvar Vencedor */ }
                            <button
                                onClick={ saveWinner }
                                disabled={ !selectedWinner }
                                style={ {
                                    ...styles.button,
                                    width: '100%',
                                    marginTop: '20px',
                                    padding: '14px',
                                    background: selectedWinner
                                        ? 'linear-gradient(135deg, #10b981 0%, #059669 100%)'
                                        : '#6b7280',
                                    fontSize: '1rem',
                                    cursor: selectedWinner ? 'pointer' : 'not-allowed'
                                } }
                            >
                                <Trophy size={ 18 } style={ { marginRight: '8px' } } />
                                { selectedWinner ? `Confirmar ${ selectedWinner } como Vencedor` : 'Selecione um Vencedor' }
                            </button>
                        </div>
                    ) }
                </div>
            ) : (
                // MODO NORMAL
                <div>
                    <h3 style={ styles.sectionTitle }>🧠 IA de Conteúdo</h3>
                    <div style={ styles.radioGroup }>
                        { [
                            { value: 'claude-opus-4', label: 'Claude Opus 4', desc: 'Narrativas profundas e complexas' },
                            { value: 'gemini-2.0-flash', label: 'Gemini 2.0 Flash', desc: 'Velocidade com qualidade excepcional' },
                            { value: 'gpt-4-turbo', label: 'GPT-4 Turbo', desc: 'Versatilidade e criatividade' }
                        ].map( option => (
                            <label key={ option.value } style={ styles.radioLabel }>
                                <input
                                    type="radio"
                                    checked={ settings.content_ai_model === option.value }
                                    onChange={ () => updateSetting( 'content_ai_model', option.value ) }
                                    style={ styles.radio }
                                />
                                <div>
                                    <div style={ styles.radioTitle }>{ option.label }</div>
                                    <div style={ styles.radioDesc }>{ option.desc }</div>
                                </div>
                            </label>
                        ) ) }
                    </div>

                    <h3 style={ styles.sectionTitle }>🎯 Tipo de Conteúdo</h3>
                    <div style={ styles.radioGroup }>
                        { [
                            { value: 'trending', label: 'Baseado em Trends', desc: 'Analisa topics em alta' },
                            { value: 'custom_message', label: 'Mensagem Personalizada', desc: 'Seu próprio tema/mensagem' },
                            { value: 'mixed', label: 'Híbrido', desc: 'Mistura trends com sua mensagem' }
                        ].map( option => (
                            <label key={ option.value } style={ styles.radioLabel }>
                                <input
                                    type="radio"
                                    checked={ settings.content_type === option.value }
                                    onChange={ () => updateSetting( 'content_type', option.value ) }
                                    style={ styles.radio }
                                />
                                <div>
                                    <div style={ styles.radioTitle }>{ option.label }</div>
                                    <div style={ styles.radioDesc }>{ option.desc }</div>
                                </div>
                            </label>
                        ) ) }
                    </div>

                    <h3 style={ styles.sectionTitle }>💭 Temas Personalizados</h3>
                    <div style={ styles.chipContainer }>
                        { [ 'Motivação', 'Tecnologia', 'Negócios', 'Mistérios', 'Ciência', 'História' ].map( topic => (
                            <button
                                key={ topic }
                                onClick={ () =>
                                {
                                    const isSelected = settings.custom_topics.includes( topic );
                                    const newTopics = isSelected
                                        ? settings.custom_topics.filter( t => t !== topic )
                                        : [ ...settings.custom_topics, topic ];
                                    updateSetting( 'custom_topics', newTopics );
                                } }
                                style={ {
                                    ...styles.chip,
                                    ...( settings.custom_topics.includes( topic ) ? styles.activeChip : {} )
                                } }
                            >
                                { topic }
                            </button>
                        ) ) }
                    </div>

                    <h3 style={ styles.sectionTitle }>🎭 Tom da Mensagem</h3>
                    <select
                        value={ settings.tone }
                        onChange={ ( e ) => updateSetting( 'tone', e.target.value ) }
                        style={ styles.select }
                    >
                        <option value="inspirational">Inspiracional</option>
                        <option value="educational">Educativo</option>
                        <option value="entertaining">Divertido</option>
                        <option value="motivational">Motivacional</option>
                        <option value="mysterious">Misterioso</option>
                        <option value="dramatic">Dramático</option>
                    </select>

                    <h3 style={ { ...styles.sectionTitle, marginTop: '24px' } }>📝 Prompt Personalizado</h3>
                    <textarea
                        value={ settings.custom_prompt_roteiro }
                        onChange={ ( e ) => updateSetting( 'custom_prompt_roteiro', e.target.value ) }
                        style={ styles.textarea }
                        rows={ 4 }
                        placeholder="Ex: Crie um roteiro sobre superação com uma linguagem poética..."
                    />
                </div>
            ) }
        </div>
    );
};

export default ContentSection;