// /var/www/tiktok-automation/frontend-react/src/sections/VisualSection.tsx

import React, { CSSProperties } from 'react';
import { ContentSettings } from '../types'; // Importa ContentSettings do arquivo de tipos
import { globalStyles as styles } from '../global-styles'; // <<<<<<< NOVO: Importa estilos globais >>>>>>>>>

// Esta função representa a seção Visual do painel administrativo
const VisualSection: React.FC<{ settings: ContentSettings, updateSetting: any }> = ( { settings, updateSetting } ) => (
    <div style={ styles.section }>
        <h3 style={ styles.sectionTitle }>🎨 Estilo Visual</h3>
        <div style={ styles.visualGrid }>
            { [
                { value: 'realistic', label: 'Realista', sample: '📸 Fotográfico, detalhado' },
                { value: 'vectorized', label: 'Vetorizado', sample: '✨ Limpo, minimalista' },
                { value: 'cinematic', label: 'Cinematográfico', sample: '🎬 Dramático, épico' },
                { value: 'artistic', label: 'Artístico', sample: '🎨 Criativo, único' }
            ].map( style => (
                <div
                    key={ style.value }
                    onClick={ () => updateSetting( 'image_style', style.value ) }
                    style={ {
                        ...styles.visualCard,
                        ...( settings.image_style === style.value ? styles.activeVisualCard : {} )
                    } }
                >
                    <div style={ styles.visualTitle }>{ style.label }</div>
                    <div style={ styles.visualSample }>{ style.sample }</div>
                </div>
            ) ) }
        </div>

        <h3 style={ styles.sectionTitle }>🌈 Paleta de Cores</h3>
        <div style={ styles.colorGrid }>
            { [
                { value: 'vibrant', color: '#ff6b6b', label: 'Vibrante' },
                { value: 'muted', color: '#74b9ff', label: 'Suave' },
                { value: 'monochrome', color: '#636e72', label: 'Monocromático' },
                { value: 'sunset', color: '#fd79a8', label: 'Sunset' },
                { value: 'nature', color: '#00b894', label: 'Natureza' }
            ].map( palette => (
                <button
                    key={ palette.value }
                    onClick={ () => updateSetting( 'color_palette', palette.value ) }
                    style={ {
                        ...styles.colorChip,
                        backgroundColor: palette.color,
                        ...( settings.color_palette === palette.value ? styles.activeColorChip : {} )
                    } }
                >
                    { palette.label }
                </button>
            ) ) }
        </div>

        {/* NOVO: CAMPO PARA PROMPT PERSONALIZADO DA IMAGEM */ }
        <h3 style={ { ...styles.sectionTitle, marginTop: '24px' } }>🖼️ Prompt Personalizado da Imagem</h3>
        <textarea
            value={ settings.custom_prompt_imagem }
            onChange={ ( e ) => updateSetting( 'custom_prompt_imagem', e.target.value ) }
            style={ styles.textarea }
            rows={ 4 }
            placeholder="Ex: Objeto solitário em paisagem desolada, dramatic lighting..."
        />
    </div>
);

// REMOVIDO: A definição de 'styles' foi movida para global-styles.ts
// const styles: { [ keyof: string ]: CSSProperties } = { ... };

export default VisualSection;