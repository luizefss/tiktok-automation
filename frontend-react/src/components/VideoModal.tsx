// /var/www/tiktok-automation/frontend-react/src/components/VideoModal.tsx
import React from 'react';
import { X } from 'lucide-react'; // Ícones necessários aqui
import { apiService } from '../services/api';
import { Video as VideoType } from '../types';

import { globalStyles as styles } from '../global-styles'; // Importa estilos globais

const VideoModal: React.FC<{ video: VideoType; onClose: () => void; }> = ( { video, onClose } ) => (
    <div style={ styles.modalBackdrop } onClick={ onClose }>
        <div style={ { ...styles.modalContent, display: 'flex', flexDirection: 'column' } } onClick={ ( e ) => e.stopPropagation() }>
            <button onClick={ onClose } style={ styles.modalCloseButton }><X size={ 20 } /></button>
            <h3 style={ styles.modalTitle }>{ video.metadata?.roteiro?.titulo }</h3>
            <div style={ { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', maxHeight: '70vh', flexGrow: 1 } }>
                { video.metadata?.roteiro?.hashtags?.map( ( tag, index ) => (
                    <span key={ index }>{ tag }</span>
                ) ) }
                <video src={ apiService.getVideoUrl( video.filename ) } controls />
                <div style={ { display: 'flex', flexDirection: 'column', minHeight: 0 } }>
                    <div style={ styles.roteiroContainer }>
                        <h4 style={ styles.infoTitle }>📝 Roteiro Completo</h4>
                        <p style={ styles.infoText }>{ video.metadata?.roteiro?.roteiro_completo }</p>
                    </div>
                    <div style={ { ...styles.roteiroContainer, marginTop: '16px' } }>
                        <h4 style={ styles.infoTitle }>🖼️ Prompts de Imagem Usados</h4>
                        <p style={ styles.infoText }>Informação de prompt não disponível.</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
);
export default VideoModal;