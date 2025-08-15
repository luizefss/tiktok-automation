// /var/www/tiktok-automation/frontend-react/src/AdminPanel.tsx

import React, { useState } from 'react';
import { ContentSettings } from './types'; // Importa ContentSettings do arquivo de tipos centralizado
import { X, MessageSquare, Palette, Play, Wand2 } from 'lucide-react'; // Ícones necessários

// <<<<<<< NOVO: Importa os estilos globais >>>>>>>>>
import { globalStyles as styles } from './global-styles';

// Importa as seções (elas também precisarão ser atualizadas para usar global-styles)
import ContentSection from './sections/ContentSection';
import VisualSection from './sections/VisualSection';
import AudioSection from './sections/AudioSection';

const AdminPanel: React.FC<{
    settings: ContentSettings;
    onSettingsChange: ( settings: ContentSettings ) => void;
    onClose: () => void;
    onGenerateCustom: () => void;
}> = ( { settings, onSettingsChange, onClose, onGenerateCustom } ) =>
{
    const [ activeTab, setActiveTab ] = useState<'content' | 'visual' | 'audio'>( 'content' );

    // Função auxiliar para atualizar qualquer setting de forma genérica
    const updateSetting = <K extends keyof ContentSettings> ( key: K, value: ContentSettings[ K ] ) =>
    {
        onSettingsChange( { ...settings, [ key ]: value } );
    };

    return (
        <div style={ styles.modalBackdrop } onClick={ onClose }>
            <div style={ styles.adminPanel } onClick={ ( e ) => e.stopPropagation() }>
                <div style={ styles.adminHeader }>
                    <h2 style={ styles.adminTitle }>🎛️ Centro de Controle Criativo</h2>
                    <button onClick={ onClose } style={ styles.modalCloseButton }>
                        <X size={ 20 } />
                    </button>
                </div>

                {/* Aba de navegação do painel */ }
                <div style={ styles.tabContainer }>
                    { [
                        { id: 'content', label: '📝 Conteúdo', icon: MessageSquare },
                        { id: 'visual', label: '🎨 Visual', icon: Palette },
                        { id: 'audio', label: '🎵 Áudio', icon: Play }
                    ].map( tab => (
                        <button
                            key={ tab.id }
                            onClick={ () => setActiveTab( tab.id as any ) }
                            style={ {
                                ...styles.tab,
                                ...( activeTab === tab.id ? styles.activeTab : {} )
                            } }
                        >
                            <tab.icon size={ 16 } />
                            { tab.label }
                        </button>
                    ) ) }
                </div>

                {/* Conteúdo das abas */ }
                <div style={ styles.adminContent }>
                    { activeTab === 'content' && (
                        <ContentSection settings={ settings } updateSetting={ updateSetting } />
                    ) }
                    { activeTab === 'visual' && (
                        <VisualSection settings={ settings } updateSetting={ updateSetting } />
                    ) }
                    { activeTab === 'audio' && (
                        <AudioSection settings={ settings } updateSetting={ updateSetting } />
                    ) }
                </div>

                {/* Rodapé do painel com botão de gerar vídeo */ }
                <div style={ styles.adminFooter }>
                    <button onClick={ onGenerateCustom } style={ styles.generateCustomButton }>
                        <Wand2 size={ 20 } />
                        Gerar Vídeo Personalizado
                    </button>
                </div>
            </div>
        </div>
    );
};

// REMOVIDO: A definição de 'styles' foi movida para global-styles.ts
// const styles: { [key: string]: CSSProperties } = { ... };

export default AdminPanel;