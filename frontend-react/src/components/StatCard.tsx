// Componentes auxiliares atualizados para Dashboard Suprema

import React from 'react';
import
{
    TrendingUp, ArrowUp, ArrowDown, Activity,
    AlertCircle, CheckCircle, Clock, Zap
} from 'lucide-react';
import { globalStyles as styles } from '../global-styles';

// === STAT CARD RENOVADO ===

interface StatCardProps
{
    icon: React.ReactNode;
    title: string;
    value: string | number;
    color?: string;
    trend?: number;
    subtitle?: string;
    status?: 'success' | 'warning' | 'error' | 'info';
    animated?: boolean;
}

export const StatCard: React.FC<StatCardProps> = ( {
    icon,
    title,
    value,
    color = '#3b82f6',
    trend,
    subtitle,
    status,
    animated = false
} ) =>
{
    const getStatusColor = () =>
    {
        switch ( status )
        {
            case 'success': return '#10b981';
            case 'warning': return '#f59e0b';
            case 'error': return '#ef4444';
            default: return color;
        }
    };

    const getStatusIcon = () =>
    {
        switch ( status )
        {
            case 'success': return <CheckCircle size={ 16 } />;
            case 'warning': return <AlertCircle size={ 16 } />;
            case 'error': return <AlertCircle size={ 16 } />;
            default: return <Activity size={ 16 } />;
        }
    };

    return (
        <div style={ {
            ...styles.card,
            background: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
            border: `1px solid ${ getStatusColor() }40`,
            position: 'relative',
            overflow: 'hidden',
            cursor: 'pointer',
            transition: 'all 0.3s ease',
            ...( animated && {
                animation: 'fadeIn 0.5s ease-in-out'
            } )
        } }>
            {/* Background decoration */ }
            <div style={ {
                position: 'absolute',
                top: 0,
                right: 0,
                width: '80px',
                height: '80px',
                background: `${ getStatusColor() }15`,
                borderRadius: '50%',
                transform: 'translate(25px, -25px)'
            } } />

            <div style={ {
                display: 'flex',
                alignItems: 'flex-start',
                gap: '16px',
                position: 'relative',
                zIndex: 1
            } }>
                <div style={ {
                    color: getStatusColor(),
                    background: `${ getStatusColor() }20`,
                    padding: '12px',
                    borderRadius: '8px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                } }>
                    { icon }
                </div>

                <div style={ { flex: 1 } }>
                    <div style={ {
                        color: '#9ca3af',
                        fontSize: '0.875rem',
                        marginBottom: '4px',
                        fontWeight: '500'
                    } }>
                        { title }
                    </div>

                    <div style={ {
                        color: 'white',
                        fontSize: '1.75rem',
                        fontWeight: 'bold',
                        lineHeight: '1',
                        marginBottom: '8px'
                    } }>
                        { value }
                    </div>

                    { subtitle && (
                        <div style={ {
                            color: '#cbd5e1',
                            fontSize: '0.8rem',
                            marginBottom: '8px'
                        } }>
                            { subtitle }
                        </div>
                    ) }

                    <div style={ {
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between'
                    } }>
                        { trend !== undefined && (
                            <div style={ {
                                display: 'flex',
                                alignItems: 'center',
                                gap: '4px',
                                color: trend > 0 ? '#10b981' : '#ef4444',
                                fontSize: '0.8rem',
                                fontWeight: 'bold'
                            } }>
                                { trend > 0 ? <ArrowUp size={ 14 } /> : <ArrowDown size={ 14 } /> }
                                { Math.abs( trend ).toFixed( 1 ) }%
                            </div>
                        ) }

                        { status && (
                            <div style={ {
                                display: 'flex',
                                alignItems: 'center',
                                gap: '4px',
                                color: getStatusColor(),
                                fontSize: '0.75rem'
                            } }>
                                { getStatusIcon() }
                            </div>
                        ) }
                    </div>
                </div>
            </div>
        </div>
    );
};

// === METRIC DISPLAY ===

interface MetricDisplayProps
{
    label: string;
    value: number;
    max: number;
    unit?: string;
    color?: string;
    size?: 'small' | 'medium' | 'large';
    showPercentage?: boolean;
}

export const MetricDisplay: React.FC<MetricDisplayProps> = ( {
    label,
    value,
    max,
    unit = '%',
    color = '#3b82f6',
    size = 'medium',
    showPercentage = true
} ) =>
{
    const percentage = ( value / max ) * 100;

    const getSizeStyles = () =>
    {
        switch ( size )
        {
            case 'small':
                return { fontSize: '0.8rem', height: '4px' };
            case 'large':
                return { fontSize: '1.2rem', height: '8px' };
            default:
                return { fontSize: '1rem', height: '6px' };
        }
    };

    const sizeStyles = getSizeStyles();

    return (
        <div style={ { marginBottom: '12px' } }>
            <div style={ {
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '6px',
                fontSize: sizeStyles.fontSize
            } }>
                <span style={ { color: '#cbd5e1', fontWeight: '500' } }>{ label }</span>
                <span style={ { color: 'white', fontWeight: 'bold' } }>
                    { value }{ unit } { showPercentage && `(${ percentage.toFixed( 1 ) }%)` }
                </span>
            </div>

            <div style={ {
                background: '#374151',
                borderRadius: '4px',
                overflow: 'hidden',
                height: sizeStyles.height
            } }>
                <div style={ {
                    width: `${ Math.min( percentage, 100 ) }%`,
                    height: '100%',
                    background: `linear-gradient(90deg, ${ color } 0%, ${ color }CC 100%)`,
                    borderRadius: '4px',
                    transition: 'width 0.8s ease-out'
                } } />
            </div>
        </div>
    );
};

// === STATUS INDICATOR ===

interface StatusIndicatorProps
{
    status: 'online' | 'offline' | 'processing' | 'error' | 'warning';
    label?: string;
    pulse?: boolean;
    size?: number;
}

export const StatusIndicator: React.FC<StatusIndicatorProps> = ( {
    status,
    label,
    pulse = false,
    size = 8
} ) =>
{
    const getStatusConfig = () =>
    {
        switch ( status )
        {
            case 'online':
                return { color: '#10b981', text: 'Online' };
            case 'offline':
                return { color: '#6b7280', text: 'Offline' };
            case 'processing':
                return { color: '#3b82f6', text: 'Processando' };
            case 'error':
                return { color: '#ef4444', text: 'Erro' };
            case 'warning':
                return { color: '#f59e0b', text: 'Atenção' };
            default:
                return { color: '#6b7280', text: 'Desconhecido' };
        }
    };

    const config = getStatusConfig();

    return (
        <div style={ {
            display: 'flex',
            alignItems: 'center',
            gap: '6px'
        } }>
            <div style={ {
                width: `${ size }px`,
                height: `${ size }px`,
                borderRadius: '50%',
                background: config.color,
                ...( pulse && {
                    animation: 'pulse 2s infinite'
                } )
            } } />

            { label && (
                <span style={ {
                    color: '#cbd5e1',
                    fontSize: '0.875rem',
                    fontWeight: '500'
                } }>
                    { label || config.text }
                </span>
            ) }
        </div>
    );
};

// === LOADING SPINNER ===

interface LoadingSpinnerProps
{
    size?: number;
    color?: string;
    text?: string;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ( {
    size = 24,
    color = '#3b82f6',
    text
} ) =>
{
    return (
        <div style={ {
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
        } }>
            <div style={ {
                width: `${ size }px`,
                height: `${ size }px`,
                border: `2px solid ${ color }30`,
                borderTop: `2px solid ${ color }`,
                borderRadius: '50%',
                animation: 'spin 1s linear infinite'
            } } />

            { text && (
                <span style={ {
                    color: '#9ca3af',
                    fontSize: '0.875rem'
                } }>
                    { text }
                </span>
            ) }
        </div>
    );
};

// === PROGRESS BAR ===

interface ProgressBarProps
{
    value: number;
    max: number;
    color?: string;
    showLabel?: boolean;
    animated?: boolean;
    height?: number;
}

export const ProgressBar: React.FC<ProgressBarProps> = ( {
    value,
    max,
    color = '#3b82f6',
    showLabel = true,
    animated = true,
    height = 8
} ) =>
{
    const percentage = Math.min( ( value / max ) * 100, 100 );

    return (
        <div>
            { showLabel && (
                <div style={ {
                    display: 'flex',
                    justifyContent: 'space-between',
                    marginBottom: '4px',
                    fontSize: '0.875rem'
                } }>
                    <span style={ { color: '#9ca3af' } }>Progresso</span>
                    <span style={ { color: 'white', fontWeight: 'bold' } }>
                        { percentage.toFixed( 1 ) }%
                    </span>
                </div>
            ) }

            <div style={ {
                background: '#374151',
                borderRadius: `${ height / 2 }px`,
                overflow: 'hidden',
                height: `${ height }px`
            } }>
                <div style={ {
                    width: `${ percentage }%`,
                    height: '100%',
                    background: `linear-gradient(90deg, ${ color } 0%, ${ color }CC 100%)`,
                    borderRadius: `${ height / 2 }px`,
                    transition: animated ? 'width 0.5s ease-out' : 'none',
                    position: 'relative',
                    overflow: 'hidden'
                } }>
                    { animated && (
                        <div style={ {
                            position: 'absolute',
                            top: 0,
                            left: 0,
                            right: 0,
                            bottom: 0,
                            background: 'linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.3) 50%, transparent 100%)',
                            animation: 'shimmer 2s infinite'
                        } } />
                    ) }
                </div>
            </div>
        </div>
    );
};

// === NOTIFICATION BADGE ===

interface NotificationBadgeProps
{
    count: number;
    max?: number;
    color?: string;
    size?: 'small' | 'medium' | 'large';
}

export const NotificationBadge: React.FC<NotificationBadgeProps> = ( {
    count,
    max = 99,
    color = '#ef4444',
    size = 'medium'
} ) =>
{
    const getSizeStyles = () =>
    {
        switch ( size )
        {
            case 'small':
                return {
                    minWidth: '16px',
                    height: '16px',
                    fontSize: '0.6rem',
                    padding: '0 4px'
                };
            case 'large':
                return {
                    minWidth: '24px',
                    height: '24px',
                    fontSize: '0.8rem',
                    padding: '0 8px'
                };
            default:
                return {
                    minWidth: '20px',
                    height: '20px',
                    fontSize: '0.7rem',
                    padding: '0 6px'
                };
        }
    };

    if ( count === 0 ) return null;

    const displayCount = count > max ? `${ max }+` : count.toString();
    const sizeStyles = getSizeStyles();

    return (
        <div style={ {
            ...sizeStyles,
            background: color,
            color: 'white',
            borderRadius: '10px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontWeight: 'bold',
            lineHeight: '1'
        } }>
            { displayCount }
        </div>
    );
};

// === TOOLTIP ===

interface TooltipProps
{
    content: string;
    children: React.ReactNode;
    position?: 'top' | 'bottom' | 'left' | 'right';
}

export const Tooltip: React.FC<TooltipProps> = ( {
    content,
    children,
    position = 'top'
} ) =>
{
    const [ isVisible, setIsVisible ] = React.useState( false );

    return (
        <div
            style={ { position: 'relative', display: 'inline-block' } }
            onMouseEnter={ () => setIsVisible( true ) }
            onMouseLeave={ () => setIsVisible( false ) }
        >
            { children }

            { isVisible && (
                <div style={ {
                    position: 'absolute',
                    zIndex: 1000,
                    background: '#1f2937',
                    color: 'white',
                    padding: '8px 12px',
                    borderRadius: '6px',
                    fontSize: '0.8rem',
                    whiteSpace: 'nowrap',
                    border: '1px solid #374151',
                    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.3)',
                    ...( position === 'top' && {
                        bottom: '100%',
                        left: '50%',
                        transform: 'translateX(-50%)',
                        marginBottom: '8px'
                    } ),
                    ...( position === 'bottom' && {
                        top: '100%',
                        left: '50%',
                        transform: 'translateX(-50%)',
                        marginTop: '8px'
                    } ),
                    ...( position === 'left' && {
                        right: '100%',
                        top: '50%',
                        transform: 'translateY(-50%)',
                        marginRight: '8px'
                    } ),
                    ...( position === 'right' && {
                        left: '100%',
                        top: '50%',
                        transform: 'translateY(-50%)',
                        marginLeft: '8px'
                    } )
                } }>
                    { content }
                </div>
            ) }
        </div>
    );
};

// === ANIMATED COUNTER ===

interface AnimatedCounterProps
{
    value: number;
    duration?: number;
    prefix?: string;
    suffix?: string;
    decimals?: number;
}

export const AnimatedCounter: React.FC<AnimatedCounterProps> = ( {
    value,
    duration = 2000,
    prefix = '',
    suffix = '',
    decimals = 0
} ) =>
{
    const [ currentValue, setCurrentValue ] = React.useState( 0 );

    React.useEffect( () =>
    {
        let startTime: number;
        let animationFrame: number;

        const animate = ( timestamp: number ) =>
        {
            if ( !startTime ) startTime = timestamp;
            const progress = Math.min( ( timestamp - startTime ) / duration, 1 );

            const easeOutQuart = 1 - Math.pow( 1 - progress, 4 );
            setCurrentValue( value * easeOutQuart );

            if ( progress < 1 )
            {
                animationFrame = requestAnimationFrame( animate );
            }
        };

        animationFrame = requestAnimationFrame( animate );

        return () =>
        {
            if ( animationFrame )
            {
                cancelAnimationFrame( animationFrame );
            }
        };
    }, [ value, duration ] );

    return (
        <span>
            { prefix }{ currentValue.toFixed( decimals ) }{ suffix }
        </span>
    );
};

// CSS adicional para animações
const additionalCSS = `
  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }

  @keyframes pulse {
    0% { opacity: 1; }
    50% { opacity: 0.5; }
    100% { opacity: 1; }
  }

  @keyframes shimmer {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(100%); }
  }

  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
  }
`;

// Injetar CSS adicional
if ( typeof document !== 'undefined' )
{
    const style = document.createElement( 'style' );
    style.textContent = additionalCSS;
    document.head.appendChild( style );
}