import React, { useState } from 'react';
import { 
  Rocket, Play, Pause, Zap, AlertTriangle, Shield,
  RefreshCw, Settings, Power, Activity, Target
} from 'lucide-react';
import { globalStyles as styles } from '../global-styles';

interface QuickActionsProps {
  onEmergencyGenerate: () => void;
  isSystemActive: boolean;
  onToggleSystem: () => void;
}

const QuickActions: React.FC<QuickActionsProps> = ({
  onEmergencyGenerate,
  isSystemActive,
  onToggleSystem
}) => {
  const [emergencyMode, setEmergencyMode] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);

  const handleEmergencyGenerate = () => {
    setIsGenerating(true);
    setEmergencyMode(true);
    onEmergencyGenerate();
    
    // Reset após 5 segundos
    setTimeout(() => {
      setIsGenerating(false);
      setEmergencyMode(false);
    }, 5000);
  };

  const ActionButton = ({ 
    onClick, 
    icon, 
    label, 
    variant = 'default',
    disabled = false,
    pulse = false 
  }: {
    onClick: () => void;
    icon: React.ReactNode;
    label: string;
    variant?: 'default' | 'primary' | 'success' | 'warning' | 'danger';
    disabled?: boolean;
    pulse?: boolean;
  }) => {
    const getVariantStyles = () => {
      switch (variant) {
        case 'primary':
          return {
            background: 'linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)',
            color: 'white'
          };
        case 'success':
          return {
            background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
            color: 'white'
          };
        case 'warning':
          return {
            background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
            color: 'white'
          };
        case 'danger':
          return {
            background: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
            color: 'white'
          };
        default:
          return {
            background: 'rgba(255, 255, 255, 0.1)',
            color: 'white'
          };
      }
    };

    return (
      <button
        onClick={onClick}
        disabled={disabled}
        style={{
          ...styles.button,
          ...getVariantStyles(),
          padding: '8px 16px',
          fontSize: '0.85rem',
          border: 'none',
          borderRadius: '8px',
          cursor: disabled ? 'not-allowed' : 'pointer',
          opacity: disabled ? 0.5 : 1,
          position: 'relative',
          overflow: 'hidden',
          ...(pulse && {
            animation: 'pulse 2s infinite'
          })
        }}
        title={label}
      >
        {pulse && (
          <div style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(255, 255, 255, 0.1)',
            animation: 'shimmer 2s infinite'
          }} />
        )}
        
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          position: 'relative',
          zIndex: 1
        }}>
          {icon}
          <span>{label}</span>
        </div>
      </button>
    );
  };

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: '8px'
    }}>
      {/* Emergency Generate Button */}
      <ActionButton
        onClick={handleEmergencyGenerate}
        icon={
          isGenerating ? (
            <RefreshCw size={16} style={{ animation: 'spin 1s linear infinite' }} />
          ) : (
            <Rocket size={16} />
          )
        }
        label={
          isGenerating 
            ? 'Gerando...' 
            : emergencyMode 
            ? 'VIRAL MODE' 
            : 'Viral AGORA'
        }
        variant={emergencyMode ? 'danger' : 'primary'}
        disabled={isGenerating}
        pulse={emergencyMode}
      />

      {/* System Toggle */}
      <ActionButton
        onClick={onToggleSystem}
        icon={isSystemActive ? <Pause size={16} /> : <Play size={16} />}
        label={isSystemActive ? 'Pausar' : 'Ativar'}
        variant={isSystemActive ? 'warning' : 'success'}
      />

      {/* System Status Indicator */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '6px',
        padding: '8px 12px',
        background: 'rgba(255, 255, 255, 0.05)',
        borderRadius: '8px',
        border: '1px solid rgba(255, 255, 255, 0.1)'
      }}>
        <div style={{
          width: '8px',
          height: '8px',
          borderRadius: '50%',
          background: isSystemActive ? '#10b981' : '#ef4444',
          animation: isSystemActive ? 'pulse 2s infinite' : 'none'
        }} />
        <div style={{
          color: 'rgba(255, 255, 255, 0.8)',
          fontSize: '0.8rem',
          fontWeight: 'bold'
        }}>
          {isSystemActive ? 'SISTEMA ATIVO' : 'PAUSADO'}
        </div>
      </div>

      {/* Quick Stats */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        padding: '8px 12px',
        background: 'rgba(255, 255, 255, 0.05)',
        borderRadius: '8px',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        fontSize: '0.75rem',
        color: 'rgba(255, 255, 255, 0.7)'
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '4px'
        }}>
          <Activity size={12} style={{ color: '#3b82f6' }} />
          <span>94% IA</span>
        </div>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '4px'
        }}>
          <Target size={12} style={{ color: '#10b981' }} />
          <span>28% Viral</span>
        </div>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '4px'
        }}>
          <Zap size={12} style={{ color: '#f59e0b' }} />
          <span>12 Queue</span>
        </div>
      </div>

      {/* Emergency Actions Menu */}
      {emergencyMode && (
        <div style={{
          position: 'absolute',
          top: '100%',
          right: 0,
          marginTop: '8px',
          background: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
          border: '1px solid #ef4444',
          borderRadius: '8px',
          padding: '12px',
          minWidth: '200px',
          zIndex: 1000,
          boxShadow: '0 10px 25px rgba(0, 0, 0, 0.5)'
        }}>
          <div style={{
            color: '#ef4444',
            fontWeight: 'bold',
            fontSize: '0.9rem',
            marginBottom: '8px',
            display: 'flex',
            alignItems: 'center',
            gap: '6px'
          }}>
            <AlertTriangle size={16} />
            MODO EMERGÊNCIA ATIVO
          </div>
          
          <div style={{
            color: 'rgba(255, 255, 255, 0.8)',
            fontSize: '0.8rem',
            lineHeight: '1.4'
          }}>
            • Prioridade máxima na fila<br />
            • Trending analysis acelerado<br />
            • Multi-plataforma simultâneo<br />
            • IA competition mode ativo
          </div>

          <div style={{
            marginTop: '8px',
            padding: '6px',
            background: 'rgba(239, 68, 68, 0.1)',
            borderRadius: '4px',
            fontSize: '0.7rem',
            color: '#ef4444',
            textAlign: 'center'
          }}>
            Auto-reset em 5 segundos
          </div>
        </div>
      )}

      {/* CSS for animations */}
      <style>
        {`
          @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
          }
          
          @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
          }
          
          @keyframes shimmer {
            0% { transform: translateX(-100%); }
            100% { transform: translateX(100%); }
          }
        `}
      </style>
    </div>
  );
};

export default QuickActions;