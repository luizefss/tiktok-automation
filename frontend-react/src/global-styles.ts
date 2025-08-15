import { CSSProperties } from 'react';

// Estilos globais expandidos para a Dashboard Suprema
export const globalStyles: { [ key: string ]: CSSProperties } = {
    // === ESTILOS BASE (mantidos) ===
    page: {
        minHeight: '100vh',
        background: '#111827',
        color: 'white',
        padding: '24px',
        fontFamily: 'sans-serif',
        paddingBottom: '120px' // Espaço para o TrendingPanel
    },
    container: { maxWidth: '1280px', margin: '0 auto' },
    card: {
        background: '#1f2937',
        padding: '24px',
        borderRadius: '12px',
        border: '1px solid #334155',
        transition: 'all 0.3s ease'
    },
    headerTitle: {
        fontSize: '2.25rem',
        fontWeight: 'bold',
        marginBottom: '8px',
        margin: '0 0 8px 0'
    },
    statsGrid: {
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
        gap: '24px',
        marginBottom: '24px'
    },
    contentGrid: {
        display: 'grid',
        gridTemplateColumns: 'minmax(0, 2fr) minmax(0, 1fr)',
        gap: '24px'
    },
    cardTitle: {
        fontSize: '1.25rem',
        fontWeight: 'bold',
        marginBottom: '16px',
        borderBottom: '1px solid #4b5563',
        paddingBottom: '8px',
        color: '#cbd5e1',
        margin: '0 0 16px 0'
    },
    videoList: {
        display: 'flex',
        flexDirection: 'column',
        gap: '16px',
        maxHeight: '60vh',
        overflowY: 'auto',
        paddingRight: '8px'
    },
    videoItem: {
        background: '#334155',
        padding: '16px',
        borderRadius: '8px',
        display: 'flex',
        alignItems: 'center',
        gap: '16px'
    },
    iconButton: {
        background: '#475569',
        color: 'white',
        border: 'none',
        borderRadius: '8px',
        width: '36px',
        height: '36px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        cursor: 'pointer',
        transition: 'all 0.3s ease'
    },
    button: {
        color: 'white',
        padding: '10px 20px',
        borderRadius: '8px',
        fontWeight: '600',
        border: 'none',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '8px',
        cursor: 'pointer',
        transition: 'all 0.3s ease'
    },
    loadingContainer: {
        minHeight: '100vh',
        background: '#111827',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: 'white',
        fontSize: '1.25rem'
    },

    // === MODAL STYLES ===
    modalBackdrop: {
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: 'rgba(0,0,0,0.8)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000
    },
    modalContent: {
        background: '#1f293b',
        padding: '24px',
        borderRadius: '12px',
        width: '80%',
        maxWidth: '900px',
        position: 'relative'
    },
    modalCloseButton: {
        position: 'absolute',
        top: '16px',
        right: '16px',
        background: 'none',
        border: 'none',
        color: 'white',
        cursor: 'pointer'
    },
    modalTitle: {
        margin: '0 0 16px 0',
        fontSize: '1.5rem',
        fontWeight: 600,
        color: '#f1f5f9'
    },
    roteiroContainer: {
        flex: 1,
        overflowY: 'auto',
        background: '#111827',
        padding: '16px',
        borderRadius: '8px',
        fontSize: '0.875rem',
        whiteSpace: 'pre-wrap',
        color: '#d1d5db',
        lineHeight: 1.6
    },
    infoTitle: {
        fontWeight: 'bold',
        borderBottom: '1px solid #4b5563',
        paddingBottom: '8px',
        marginBottom: '8px',
        color: '#cbd5e1'
    },
    infoText: {
        fontSize: '0.875rem',
        whiteSpace: 'pre-wrap',
        color: '#d1d5db',
        lineHeight: 1.6
    },

    // === TAB SYSTEM ===
    tabContainer: {
        display: 'flex',
        gap: '8px',
        marginBottom: '24px',
        background: '#1e293b',
        padding: '4px',
        borderRadius: '12px'
    },
    tab: {
        flex: 1,
        padding: '12px 16px',
        background: 'transparent',
        border: 'none',
        color: '#94a3b8',
        borderRadius: '8px',
        cursor: 'pointer',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '8px',
        transition: 'all 0.3s ease',
        fontSize: '0.9rem',
        fontWeight: '500'
    },
    activeTab: {
        background: '#3b82f6',
        color: 'white',
        transform: 'translateY(-1px)',
        boxShadow: '0 4px 12px rgba(59, 130, 246, 0.3)'
    },

    // === SECTIONS ===
    section: {
        background: '#1e293b',
        padding: '24px',
        borderRadius: '12px',
        marginBottom: '24px',
        border: '1px solid #334155'
    },
    sectionTitle: {
        fontSize: '1.2rem',
        fontWeight: 'bold',
        marginBottom: '16px',
        color: '#f1f5f9'
    },

    // === FORM ELEMENTS ===
    radioGroup: {
        display: 'flex',
        flexDirection: 'column',
        gap: '12px',
        marginBottom: '24px'
    },
    radioLabel: {
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        cursor: 'pointer',
        padding: '12px',
        background: '#334155',
        borderRadius: '8px',
        border: '1px solid #475569',
        transition: 'all 0.3s ease'
    },
    radio: { width: '16px', height: '16px' },
    radioTitle: { fontWeight: 'bold', color: '#f1f5f9' },
    radioDesc: { fontSize: '0.9rem', color: '#cbd5e1' },

    // === CHIP/TAG SYSTEM ===
    chipContainer: {
        display: 'flex',
        flexWrap: 'wrap',
        gap: '8px',
        marginBottom: '24px'
    },
    chip: {
        padding: '8px 16px',
        background: '#334155',
        borderRadius: '20px',
        color: '#f1f5f9',
        cursor: 'pointer',
        fontSize: '0.85rem',
        fontWeight: '500',
        transition: 'all 0.3s ease',
        border: '1px solid #475569'
    },
    activeChip: {
        background: '#3b82f6',
        color: 'white',
        borderColor: '#60a5fa',
        transform: 'translateY(-1px)',
        boxShadow: '0 4px 8px rgba(59, 130, 246, 0.3)'
    },

    // === SELECT/INPUT ELEMENTS ===
    select: {
        width: '100%',
        padding: '12px',
        background: '#334155',
        border: '1px solid #475569',
        borderRadius: '8px',
        color: 'white',
        outline: 'none',
        fontSize: '0.9rem',
        transition: 'all 0.3s ease'
    },
    textarea: {
        width: 'calc(100% - 24px)',
        padding: '12px',
        background: '#334155',
        border: '1px solid #4b5563',
        borderRadius: '8px',
        color: 'white',
        fontSize: '1rem',
        resize: 'vertical',
        outline: 'none',
        transition: 'all 0.3s ease',
        lineHeight: '1.5'
    },
    checkbox: { width: '16px', height: '16px', marginRight: '8px' },

    // === VISUAL CARDS ===
    visualGrid: {
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '12px',
        marginBottom: '24px'
    },
    visualCard: {
        padding: '16px',
        background: '#334155',
        borderRadius: '8px',
        cursor: 'pointer',
        border: '2px solid transparent',
        transition: 'all 0.3s ease'
    },
    activeVisualCard: {
        border: '2px solid #3b82f6',
        background: 'linear-gradient(135deg, #334155 0%, #3b82f640 100%)',
        transform: 'translateY(-2px)',
        boxShadow: '0 8px 16px rgba(59, 130, 246, 0.2)'
    },
    visualTitle: { fontWeight: 'bold', marginBottom: '8px' },
    visualSample: { fontSize: '0.9rem', color: '#cbd5e1' },

    // === COLOR SYSTEM ===
    colorGrid: {
        display: 'flex',
        gap: '12px',
        flexWrap: 'wrap',
        marginBottom: '24px'
    },
    colorChip: {
        padding: '12px 20px',
        border: 'none',
        borderRadius: '8px',
        color: 'white',
        fontWeight: 'bold',
        cursor: 'pointer',
        transition: 'all 0.3s ease',
        fontSize: '0.85rem'
    },
    activeColorChip: {
        transform: 'scale(1.05) translateY(-2px)',
        boxShadow: '0 6px 12px rgba(0, 0, 0, 0.3)'
    },

    // === EMOTION/MOOD SYSTEM ===
    emotionGrid: {
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))',
        gap: '12px',
        marginBottom: '24px'
    },
    emotionButton: {
        padding: '16px',
        background: '#334155',
        borderRadius: '8px',
        color: 'white',
        cursor: 'pointer',
        textAlign: 'center',
        transition: 'all 0.3s ease',
        border: '1px solid #475569'
    },
    activeEmotion: {
        background: '#3b82f6',
        borderColor: '#60a5fa',
        transform: 'translateY(-2px)',
        boxShadow: '0 6px 12px rgba(59, 130, 246, 0.3)'
    },
    emoji: { fontSize: '2rem', marginBottom: '8px' },

    // === SLIDER SYSTEM ===
    sliderContainer: {
        display: 'flex',
        alignItems: 'center',
        gap: '16px'
    },
    slider: {
        flex: 1,
        height: '6px',
        background: '#334155',
        borderRadius: '3px',
        WebkitAppearance: 'none',
        appearance: 'none',
        cursor: 'pointer',
        outline: 'none',
        transition: 'all 0.3s ease'
    } as CSSProperties,
    sliderValue: {
        minWidth: '60px',
        textAlign: 'center',
        background: '#3b82f6',
        padding: '4px 12px',
        borderRadius: '4px',
        fontWeight: 'bold',
        fontSize: '0.85rem'
    },

    // === TOGGLE/SWITCH SYSTEM ===
    toggleGroup: { marginBottom: '24px' },

    // === PREVIEW SYSTEM ===
    settingsPreview: {
        marginTop: '24px',
        background: '#0f172a',
        padding: '16px',
        borderRadius: '8px',
        border: '1px solid #334155'
    },
    previewTitle: {
        fontSize: '1rem',
        fontWeight: 'bold',
        marginBottom: '12px',
        color: '#cbd5e1'
    },
    previewGrid: {
        display: 'flex',
        flexDirection: 'column',
        gap: '8px'
    },
    previewItem: {
        display: 'flex',
        justifyContent: 'space-between',
        padding: '4px 0'
    },
    previewLabel: {
        color: '#9ca3af',
        fontSize: '0.875rem'
    },
    previewValue: {
        color: '#3b82f6',
        fontSize: '0.875rem',
        fontWeight: 'bold'
    },

    // === NOVOS ESTILOS PARA DASHBOARD SUPREMA ===

    // System Status Cards
    statusCard: {
        background: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        border: '1px solid #475569',
        borderRadius: '12px',
        padding: '20px',
        position: 'relative',
        overflow: 'hidden',
        transition: 'all 0.3s ease'
    },

    // Metric Cards
    metricCard: {
        background: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        border: '1px solid #475569',
        borderRadius: '8px',
        padding: '16px',
        transition: 'all 0.3s ease'
    },

    // Revenue Cards
    revenueCard: {
        background: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        border: '1px solid #475569',
        borderRadius: '12px',
        padding: '20px',
        position: 'relative',
        overflow: 'hidden'
    },

    // AI Battle Cards
    aiBattleCard: {
        background: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        border: '1px solid #475569',
        borderRadius: '8px',
        padding: '16px',
        cursor: 'pointer',
        transition: 'all 0.3s ease',
        position: 'relative',
        overflow: 'hidden'
    },

    // Trending Cards
    trendingCard: {
        padding: '12px',
        background: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        borderRadius: '8px',
        border: '1px solid #475569',
        cursor: 'pointer',
        transition: 'all 0.3s ease',
        minWidth: '280px',
        position: 'relative',
        overflow: 'hidden'
    },

    // Production Studio Cards
    productionCard: {
        background: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        marginBottom: '20px',
        padding: '24px',
        borderRadius: '12px',
        border: '1px solid #475569'
    },

    // Platform Selection Cards
    platformCard: {
        padding: '20px',
        borderRadius: '12px',
        cursor: 'pointer',
        border: '1px solid #6b7280',
        transition: 'all 0.3s ease',
        position: 'relative'
    },

    // Voice Option Cards
    voiceCard: {
        padding: '16px',
        background: '#1e293b',
        borderRadius: '8px',
        border: '1px solid #475569',
        cursor: 'pointer'
    },

    // Effect Option Cards
    effectCard: {
        padding: '16px',
        background: '#1e293b',
        borderRadius: '8px',
        border: '1px solid #475569',
        cursor: 'pointer'
    },

    // Quick Action Buttons
    quickActionButton: {
        background: 'rgba(255, 255, 255, 0.1)',
        color: 'white',
        padding: '8px 16px',
        fontSize: '0.85rem',
        border: 'none',
        borderRadius: '8px',
        cursor: 'pointer',
        position: 'relative',
        overflow: 'hidden',
        transition: 'all 0.3s ease'
    },

    // Analytics Charts
    chartContainer: {
        height: '300px',
        background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
        borderRadius: '8px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        border: '1px solid #334155',
        position: 'relative'
    },

    // Prediction Cards
    predictionCard: {
        padding: '16px',
        borderRadius: '8px',
        border: '1px solid #475569',
        position: 'relative'
    },

    // Gradient Backgrounds
    gradientPrimary: {
        background: 'linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)'
    },
    gradientSuccess: {
        background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)'
    },
    gradientWarning: {
        background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)'
    },
    gradientDanger: {
        background: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)'
    },
    gradientPurple: {
        background: 'linear-gradient(135deg, #7c3aed 0%, #3b82f6 100%)'
    },
    gradientEmerald: {
        background: 'linear-gradient(135deg, #059669 0%, #10b981 100%)'
    },

    // Hover Effects
    hoverLift: {
        transition: 'all 0.3s ease',
        transform: 'translateY(-2px)',
        boxShadow: '0 8px 16px rgba(0, 0, 0, 0.2)'
    },

    // Pulse Animation
    pulseGreen: {
        animation: 'pulse-green 2s infinite'
    },
    pulseBlue: {
        animation: 'pulse-blue 2s infinite'
    },

    // Status Indicators
    statusIndicator: {
        width: '8px',
        height: '8px',
        borderRadius: '50%',
        display: 'inline-block'
    },

    // Badge Styles
    badge: {
        padding: '4px 8px',
        borderRadius: '12px',
        fontSize: '0.75rem',
        fontWeight: 'bold',
        display: 'inline-flex',
        alignItems: 'center',
        gap: '4px'
    },

    // Floating Panel
    floatingPanel: {
        position: 'fixed',
        background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
        borderRadius: '8px',
        border: '1px solid #334155',
        boxShadow: '0 10px 25px rgba(0, 0, 0, 0.5)',
        zIndex: 1000
    }
};

// CSS personalizado para animações e pseudo-elementos
export const customCSS = `
  @keyframes pulse-green {
    0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
    70% { box-shadow: 0 0 0 10px rgba(16, 185, 129, 0); }
    100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
  }

  @keyframes pulse-blue {
    0% { box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.7); }
    70% { box-shadow: 0 0 0 10px rgba(59, 130, 246, 0); }
    100% { box-shadow: 0 0 0 0 rgba(59, 130, 246, 0); }
  }

  @keyframes shimmer {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(100%); }
  }

  @keyframes slideIn {
    from { transform: translateX(-100%); opacity: 0; }
    to { transform: translateX(0); opacity: 1; }
  }

  @keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
  }

  @keyframes bounceIn {
    0% { transform: scale(0.3); opacity: 0; }
    50% { transform: scale(1.05); }
    70% { transform: scale(0.9); }
    100% { transform: scale(1); opacity: 1; }
  }

  /* Scrollbar personalizado */
  ::-webkit-scrollbar {
    width: 8px;
    height: 8px;
  }

  ::-webkit-scrollbar-track {
    background: #1f2937;
  }

  ::-webkit-scrollbar-thumb {
    background: #4b5563;
    border-radius: 4px;
  }

  ::-webkit-scrollbar-thumb:hover {
    background: #6b7280;
  }

  /* Slider personalizado */
  input[type="range"]::-webkit-slider-thumb {
    -webkit-appearance: none;
    appearance: none;
    width: 20px;
    height: 20px;
    border-radius: 50%;
    background: #3b82f6;
    cursor: pointer;
    border: 2px solid #1e293b;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  }

  input[type="range"]::-moz-range-thumb {
    width: 20px;
    height: 20px;
    border-radius: 50%;
    background: #3b82f6;
    cursor: pointer;
    border: 2px solid #1e293b;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  }

  /* Foco nos elementos */
  input:focus, select:focus, textarea:focus {
    border-color: #3b82f6;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
  }

  /* Hover effects */
  .hover-lift:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
  }

  .hover-glow:hover {
    box-shadow: 0 0 20px rgba(59, 130, 246, 0.3);
  }
`;
