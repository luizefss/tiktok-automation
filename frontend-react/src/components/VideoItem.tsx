// /var/www/tiktok-automation/frontend-react/src/components/VideoItem.tsx
import React from 'react';
import { RefreshCw, Eye, Check, X, Trash2 } from 'lucide-react'; // Ícones necessários aqui
import { Video as VideoType } from '../types'; // Importa VideoType

import { globalStyles as styles } from '../global-styles'; // Importa estilos globais

const VideoItem: React.FC<{ video: VideoType; onApprove: () => void; onReject: () => void; onDelete: () => void; onPreview: () => void; }> = ( { video, onApprove, onReject, onDelete, onPreview } ) =>
{
    if ( video.status === 'Gerando...' )
    {
        return (
            <div style={ { ...styles.videoItem, justifyContent: 'center', opacity: 0.6 } }>
                <RefreshCw size={ 16 } style={ { animation: 'spin 1s linear infinite' } } />
                <h4 style={ { fontWeight: '600' } }>{ video.metadata?.roteiro?.titulo }</h4>
            </div>
        )
    }

    const status = video.metadata?.status ?? 'Indefinido';
    const statusInfo = {
        'Aguardando Revisão': { color: '#f59e0b', label: 'Revisão' },
        'Aprovado': { color: '#10b981', label: 'Aprovado' },
        'Rejeitado': { color: '#ef4444', label: 'Rejeitado' },
        'Postado': { color: '#6366f1', label: 'Postado' },
        'default': { color: '#64748b', label: 'Indefinido' }
    };
    const currentStatus = statusInfo[ status as keyof typeof statusInfo ] || statusInfo.default;

    return (
        <div style={ styles.videoItem }>
            <div style={ { flex: 1, minWidth: 0 } }>
                <h4 style={ { fontWeight: '600', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' } }>{ video.metadata?.roteiro?.titulo ?? video.filename }</h4>
                <div style={ { display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.75rem', color: '#9ca3af', marginTop: '4px' } }>
                    <span>{ ( video.size_mb ).toFixed( 2 ) } MB</span>
                    <span style={ { background: currentStatus.color, color: 'white', padding: '2px 8px', borderRadius: '12px', fontSize: '0.7rem', fontWeight: 'bold' } }>{ currentStatus.label }</span>
                </div>
            </div>
            <div style={ { display: 'flex', gap: '8px' } }>
                <button onClick={ onPreview } style={ styles.iconButton } title="Visualizar"><Eye size={ 16 } /></button>
                { status === "Aguardando Revisão" && (
                    <>
                        <button onClick={ onApprove } style={ { ...styles.iconButton, background: '#10b981' } } title="Aprovar"><Check size={ 16 } /></button>
                        <button onClick={ onReject } style={ { ...styles.iconButton, background: '#ef4444' } } title="Rejeitar"><X size={ 16 } /></button>
                    </>
                ) }
                <button onClick={ onDelete } style={ { ...styles.iconButton, background: '#475569' } } title="Deletar"><Trash2 size={ 16 } /></button>
            </div>
        </div>
    );
};
export default VideoItem;