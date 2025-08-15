import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

// --- NOVOS IMPORTS DO MATERIAL-UI ---
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';

// --- NOSSO TEMA DARK CUSTOMIZADO ---
const darkTheme = createTheme( {
  palette: {
    mode: 'dark',
    primary: {
      main: '#667eea', // Um azul/roxo similar ao seu design
    },
    secondary: {
      main: '#f59e0b', // Um laranja para contraste, como no botão de batalha
    },
    background: {
      default: '#1a202c', // Fundo principal
      paper: '#2d3748',   // Fundo de "cartões" e "papéis"
    },
  },
  typography: {
    fontFamily: 'sans-serif', // Mantendo a fonte simples por enquanto
  },
} );


const root = ReactDOM.createRoot(
  document.getElementById( 'root' ) as HTMLElement
);

root.render(
  <React.StrictMode>
    {/* O ThemeProvider "envelopa" toda a aplicação */ }
    <ThemeProvider theme={ darkTheme }>
      {/* O CssBaseline normaliza os estilos e aplica o fundo escuro */ }
      <CssBaseline />
      <App />
    </ThemeProvider>
  </React.StrictMode>
);