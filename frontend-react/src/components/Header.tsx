// /var/www/tiktok-automation/frontend-react/src/components/Header.tsx
import React from 'react';
import { globalStyles as styles } from '../global-styles'; // Importa estilos globais

const Header: React.FC = () => (
    <header style={ { padding: '0 0 24px 0' } }>
        <h1 style={ styles.headerTitle }>🚀 TikTok Automation Dashboard</h1>
        <p style={ { color: '#d1d5db' } }>Pipeline de geração e postagem de conteúdo com IA</p>
    </header>
);
export default Header;