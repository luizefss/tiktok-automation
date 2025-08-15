// /var/www/tiktok-automation/frontend-react/src/components/ActionButton.tsx
import React from 'react';
import { globalStyles as styles } from '../global-styles'; // Importa estilos globais

const ActionButton: React.FC<{ onClick: () => void; disabled?: boolean; Icon: React.ElementType; text: string; color: string }> =
    ( { onClick, disabled, Icon, text, color } ) => (
        <button onClick={ onClick } disabled={ disabled } style={ { ...styles.button, background: color, cursor: disabled ? 'not-allowed' : 'pointer', opacity: disabled ? 0.6 : 1 } }>
            <Icon size={ 20 } />
            { text }
        </button>
    );
export default ActionButton;